#include "sim/world.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <utility>

namespace aether {

namespace {

constexpr int kPlayerHitIframes = 45;
// The parry (spec 05, "Parry"): the window, the wait before the next one, what it does to the attacker, the safety it
// gives.
constexpr int kParryTicks = 14;
// The companion (spec 10): it never comes farther than this from the player, and its body is this big.
constexpr float kCompanionLeash = 8.0F;
constexpr float kCompanionRadius = 0.25F;
constexpr int kParryCooldown = 70;
constexpr int kParryStun = 60;
constexpr int kStaggerTicks = 120;  // spec 05, "Stagger"
constexpr std::int64_t kStaggerDamagePct = 125;
constexpr int kPlayerBurnPeriod = 30;  // spec 05, "Status effects on the player"
constexpr int kPlayerBurnPct = 2;
constexpr int kParryIframes = 20;
constexpr int kRespawnIframes = 90;
constexpr float kAttackMoveMult = 0.5F;
constexpr std::int64_t kMaxLevel = 99;
constexpr float kReturnArrival = 0.1F;
constexpr int kHitFlashTicks = 6;
constexpr float kNpcRadius = 0.3F;
constexpr double kPi = 3.14159265358979323846;

CollisionWorld build_collision(const TileMap& map, const Tileset& tileset) {
    std::vector<bool> solid(map.ground.size(), false);
    for (std::size_t i = 0; i < map.ground.size(); ++i) {
        const auto tile = tileset.tiles.find(map.ground[i]);
        solid[i] = tile != tileset.tiles.end() && tile->second.solid;
    }
    std::vector<Circle> props;
    props.reserve(map.props.size());
    for (const Prop& prop : map.props) {
        props.push_back({prop.x, prop.y, prop.radius});
    }
    return CollisionWorld(map.width, map.height, std::move(solid), std::move(props));
}

float axis_origin(float player, float view, float map_size) {
    if (map_size <= view) {
        return (map_size - view) / 2.0F;
    }
    const float origin = player - view / 2.0F;
    if (origin < 0.0F) {
        return 0.0F;
    }
    const float max_origin = map_size - view;
    return origin > max_origin ? max_origin : origin;
}

float distance(float ax, float ay, float bx, float by) {
    const float dx = bx - ax;
    const float dy = by - ay;
    return std::sqrt(dx * dx + dy * dy);
}

}  // namespace

WorldSim::WorldSim(TileMap map, Tileset tileset, float speed_tiles_per_s, CombatSetup combat,
                   std::optional<StreamConfig> stream)
    : m_map_(std::move(map)),
      m_tileset_(std::move(tileset)),
      m_store_(stream ? std::make_unique<ChunkStore>(std::move(stream->params), stream->seed, m_tileset_) : nullptr),
      m_collision_(m_store_ ? CollisionWorld(m_store_.get()) : build_collision(m_map_, m_tileset_)),
      m_speed_(speed_tiles_per_s),
      m_setup_(std::move(combat)),
      m_combat_rng_(derive_stream(m_setup_.seed, "combat")),
      m_loot_rng_(derive_stream(m_setup_.seed, "loot")),
      m_story_(m_setup_.story, *this) {
    m_story_.set_dynamic_npcs(&m_npcs_);
    if (m_store_) {
        const ChunkStore* store = m_store_.get();
        m_story_.set_quest_resolver([store](const std::string& id) -> std::optional<QuestDef> {
            const auto offer = resolve_offer(store->seed(), store->params(), id);
            if (!offer) {
                return std::nullopt;
            }
            return quest_from_offer(*offer);
        });
    }
    m_collision_.set_dynamic_props(&m_npc_circles_);
    m_player_.position = {m_map_.spawn_x, m_map_.spawn_y};
    if (m_store_) {
        m_world_ticks_ = m_store_->params().time.start_tick;
        m_store_->keep_around(chunk_of(static_cast<int>(std::floor(m_player_.position.x))),
                              chunk_of(static_cast<int>(std::floor(m_player_.position.y))));
    }
    m_collision_.resolve(m_player_.position.x, m_player_.position.y);
    m_spawn_ = m_player_.position;
    m_companion_pos_ = m_player_.position;
    m_companion_cooldown_ = m_setup_.companion ? m_setup_.companion->cooldown_ticks : 0;
    for (const NpcDef& npc : m_setup_.story.npcs) {
        m_collision_.add_prop({npc.x, npc.y, kNpcRadius});
    }
    if (m_setup_.enabled) {
        m_player_.level = m_setup_.start_level;
        m_equipped_weapon_ = m_setup_.start_weapon;
        m_equipped_armor_ = m_setup_.start_armor;
        recompute_derived();
        m_player_.hp = m_derived_.max_hp;
        m_player_.mp_u = m_derived_.max_mp * 6000;
        for (const EnemySpawn& spawn : m_setup_.spawns) {
            Enemy enemy;
            enemy.def = spawn.def;
            enemy.position = {spawn.x, spawn.y};
            enemy.home = enemy.position;
            enemy.hp = spawn.def.hp;
            m_enemies_.push_back(std::move(enemy));
        }
        m_hit_set_.assign(m_enemies_.size(), false);
        m_inventory_ = m_setup_.start_inventory;
        sync_window();
        mark_explored();
    }
}

std::optional<TimeSample> WorldSim::time() const {
    if (!m_store_) {
        return std::nullopt;
    }
    return sample_time(m_store_->seed(), m_store_->params().time, m_world_ticks_);
}

int WorldSim::gid_at(int x, int y) const { return m_store_ ? m_store_->gid_at(x, y) : m_map_.gid_at(x, y); }

void WorldSim::for_each_prop(float x0, float y0, float x1, float y1, const std::function<void(const Prop&)>& fn) const {
    if (m_store_) {
        m_store_->for_each_prop_in(x0, y0, x1, y1, fn);
        return;
    }
    for (const Prop& prop : m_map_.props) {
        if (prop.x >= x0 && prop.x <= x1 && prop.y >= y0 && prop.y <= y1) {
            fn(prop);
        }
    }
}

void WorldSim::rebuild_npc_circles() {
    m_npc_circles_.clear();
    for (const NpcDef& npc : m_npcs_) {
        m_npc_circles_.push_back({npc.x, npc.y, kNpcRadius});
    }
}

std::string WorldSim::season_id() const {
    if (!m_store_) {
        return {};
    }
    const TimeParams& time = m_store_->params().time;
    const int index = season_index_of(time, m_world_ticks_ / time.day_ticks + 1);
    return index >= 0 ? time.seasons[static_cast<std::size_t>(index)].id : std::string();
}

int WorldSim::time_of_day_pm() const {
    const std::int64_t day_ticks = m_store_->params().time.day_ticks;
    return static_cast<int>((m_world_ticks_ % day_ticks) * 1000 / day_ticks);
}

void WorldSim::refresh_people(int cx, int cy) {
    m_npcs_.clear();
    for (int j = cy - kActiveRadius; j <= cy + kActiveRadius; ++j) {
        for (int i = cx - kActiveRadius; i <= cx + kActiveRadius; ++i) {
            add_chunk_people(i, j);
        }
    }
    m_routine_tod_ = time_of_day_pm();
    rebuild_npc_circles();
}

void WorldSim::add_chunk_people(int cx, int cy) {
    const Chunk* chunk = m_store_->find(cx, cy);
    if (chunk == nullptr) {
        return;
    }
    const int tod = time_of_day_pm();
    for (const GenPerson& person : chunk->people) {
        const auto placement = person_placement(m_store_->params(), person, tod);
        if (!placement) {
            continue;  // indoors (spec 08)
        }
        NpcDef npc;
        npc.key = person.key;
        npc.dialogue = person.dialogue;
        npc.variant = person.variant;
        npc.x = static_cast<float>(placement->x256) / 256.0F;
        npc.y = static_cast<float>(placement->y256) / 256.0F;
        npc.name = person.name;
        npc.args = {{"npc", person.name},
                    {"place", person.place},
                    {"region", person.region},
                    {"quirk", "$i18n:" + person.quirk}};
        m_npcs_.push_back(std::move(npc));
    }
}

const EnemyDef& WorldSim::stream_enemy_at(int x, int y) const {
    return m_setup_.stream_enemies.at(spawner_enemy_at(m_store_->seed(), m_store_->params(), x, y));
}

void WorldSim::add_chunk_enemies(int cx, int cy) {
    if (m_setup_.stream_enemies.empty()) {
        return;
    }
    const Chunk* chunk = m_store_->find(cx, cy);
    if (chunk == nullptr) {
        return;
    }
    for (const auto& [sx, sy] : chunk->spawners) {
        const auto died = m_cleared_.find({sx, sy});
        if (died != m_cleared_.end()) {
            // A spawner whose enemy has been dead long enough is ready again when its chunk enters the window (spec
            // 08).
            if (m_world_ticks_ - died->second < m_store_->params().spawner_respawn_ticks) {
                continue;
            }
            m_cleared_.erase(died);
        }
        Enemy enemy;
        enemy.def = stream_enemy_at(sx, sy);
        enemy.position = {static_cast<float>(sx) + 0.5F, static_cast<float>(sy) + 0.5F};
        enemy.home = enemy.position;
        enemy.hp = enemy.def.hp;
        enemy.spawner_x = sx;
        enemy.spawner_y = sy;
        m_enemies_.push_back(std::move(enemy));
        m_hit_set_.push_back(false);
    }
}

// Spec 09, "Streaming": keeps the enemies in step with the 5 x 5 window around the player's chunk.
void WorldSim::mark_explored() {
    if (m_store_) {
        explore(m_explored_, m_store_->params(), static_cast<int>(std::floor(m_player_.position.x)),
                static_cast<int>(std::floor(m_player_.position.y)));
    }
}

void WorldSim::sync_window() {
    if (!m_store_) {
        return;
    }
    const int cx = chunk_of(static_cast<int>(std::floor(m_player_.position.x)));
    const int cy = chunk_of(static_cast<int>(std::floor(m_player_.position.y)));
    if (m_window_valid_ && cx == m_window_x_ && cy == m_window_y_) {
        return;
    }
    m_store_->keep_around(cx, cy);
    const auto inside = [](int i, int j, int wx, int wy) {
        return std::max(std::abs(i - wx), std::abs(j - wy)) <= kActiveRadius;
    };
    if (m_window_valid_) {
        std::size_t kept = 0;
        for (std::size_t i = 0; i < m_enemies_.size(); ++i) {
            if (!inside(chunk_of(m_enemies_[i].spawner_x), chunk_of(m_enemies_[i].spawner_y), cx, cy)) {
                continue;
            }
            if (kept != i) {
                m_enemies_[kept] = std::move(m_enemies_[i]);
                m_hit_set_[kept] = m_hit_set_[i];
            }
            ++kept;
        }
        m_enemies_.resize(kept);
        m_hit_set_.resize(kept);
    }
    for (int j = cy - kActiveRadius; j <= cy + kActiveRadius; ++j) {
        for (int i = cx - kActiveRadius; i <= cx + kActiveRadius; ++i) {
            if (!m_window_valid_ || !inside(i, j, m_window_x_, m_window_y_)) {
                add_chunk_enemies(i, j);
            }
        }
    }
    refresh_people(cx, cy);
    m_window_valid_ = true;
    m_window_x_ = cx;
    m_window_y_ = cy;
}

void WorldSim::recompute_derived() {
    Equipment equipment;
    equipment.weapon_atk = m_setup_.player.weapon_atk;
    equipment.weapon_matk = m_setup_.player.weapon_matk;
    const auto weapon = m_setup_.items.find(m_equipped_weapon_);
    if (weapon != m_setup_.items.end() && weapon->second.is_weapon) {
        equipment.weapon_atk = weapon->second.weapon_atk;
        equipment.weapon_matk = weapon->second.weapon_matk;
    }
    const auto armor = m_setup_.items.find(m_equipped_armor_);
    if (armor != m_setup_.items.end() && armor->second.is_armor) {
        equipment.armor_def = armor->second.armor_def;
        equipment.armor_mdef = armor->second.armor_mdef;
    }
    m_derived_ = derived_stats(m_player_.level, primary_at_level(m_setup_.player, m_player_.level), equipment);
    m_derived_.max_hp = m_derived_.max_hp * (100 + m_setup_.echo_pct) / 100;  // the echoes of past games (spec 11)
    for (const TalentDef& talent : m_setup_.talents) {  // the talents, in the order of the data (spec 11)
        const auto learned = m_talents_.find(talent.id);
        if (learned == m_talents_.end() || learned->second <= 0) {
            continue;
        }
        const std::int64_t pct = 100 + talent.pct_per_rank * learned->second;
        if (talent.stat == "attack") {
            m_derived_.atk = m_derived_.atk * pct / 100;
            m_derived_.matk = m_derived_.matk * pct / 100;
        } else if (talent.stat == "health") {
            m_derived_.max_hp = m_derived_.max_hp * pct / 100;
        } else if (talent.stat == "mana") {
            m_derived_.max_mp = m_derived_.max_mp * pct / 100;
        } else if (talent.stat == "defense") {
            m_derived_.def = m_derived_.def * pct / 100;
            m_derived_.mdef = m_derived_.mdef * pct / 100;
        } else if (talent.stat == "magic") {
            m_derived_.matk = m_derived_.matk * pct / 100;
        } else if (talent.stat == "critical") {
            m_derived_.crit_chance_pm = m_derived_.crit_chance_pm * pct / 100;
        } else if (talent.stat == "speed") {
            m_derived_.move_speed_x100 = m_derived_.move_speed_x100 * pct / 100;
        }
    }
    const auto accessory = m_setup_.items.find(m_equipped_accessory_);  // its flat bonuses come last (spec 06)
    if (accessory != m_setup_.items.end() && accessory->second.is_accessory) {
        m_derived_.atk += accessory->second.acc_atk;
        m_derived_.matk += accessory->second.acc_matk;
        m_derived_.def += accessory->second.acc_def;
        m_derived_.mdef += accessory->second.acc_mdef;
        m_derived_.max_hp += accessory->second.acc_max_hp;
        m_derived_.crit_chance_pm += accessory->second.acc_crit_pm;
    }
}

int WorldSim::talent_points() const {
    int spent = 0;
    for (const auto& entry : m_talents_) {
        spent += entry.second;
    }
    return static_cast<int>(m_player_.level - 1) * m_setup_.talent_points_per_level - spent;
}

bool WorldSim::learn_talent(const std::string& talent_id) {
    if (m_story_.dialogue_active()) {
        return false;
    }
    const auto talent = std::find_if(m_setup_.talents.begin(), m_setup_.talents.end(),
                                     [&](const TalentDef& t) { return t.id == talent_id; });
    if (talent == m_setup_.talents.end() || talent_points() < 1) {
        return false;
    }
    const auto learned = m_talents_.find(talent_id);
    if (learned != m_talents_.end() && learned->second >= talent->max_rank) {
        return false;
    }
    if (!talent->requires_talent.empty()) {  // a branch of the tree opens when the talent before it has the rank asked
        const auto before = m_talents_.find(talent->requires_talent);
        if (before == m_talents_.end() || before->second < talent->requires_rank) {
            return false;
        }
    }
    ++m_talents_[talent_id];
    recompute_derived();
    m_player_.hp = std::min(m_player_.hp, m_derived_.max_hp);
    return true;
}

void WorldSim::teleport(float x, float y) {
    m_player_.position = {x, y};
    if (m_store_) {
        m_store_->keep_around(chunk_of(static_cast<int>(std::floor(x))), chunk_of(static_cast<int>(std::floor(y))));
    }
    m_collision_.resolve(m_player_.position.x, m_player_.position.y);
    sync_window();
    mark_explored();
}

std::optional<std::pair<float, float>> WorldSim::stone_near() const {
    if (!m_store_ || m_store_->params().stone_art.empty()) {
        return std::nullopt;
    }
    const WorldParams& params = m_store_->params();
    const float range = static_cast<float>(params.stone_range_x100) / 100.0F;
    const float px = m_player_.position.x;
    const float py = m_player_.position.y;
    std::optional<std::pair<float, float>> best;
    float best_d = range * range;
    for_each_prop(px - range, py - range, px + range, py + range, [&](const Prop& prop) {
        if (prop.art != params.stone_art) {
            return;
        }
        const float d = (prop.x - px) * (prop.x - px) + (prop.y - py) * (prop.y - py);
        if (d <= best_d) {
            best_d = d;
            best = std::make_pair(prop.x, prop.y);
        }
    });
    return best;
}

bool WorldSim::use_stone() {
    const auto stone = stone_near();
    if (!stone) {
        return false;
    }
    const WorldParams& params = m_store_->params();
    const std::pair<int, int> tile{static_cast<int>(std::floor(stone->first)),
                                   static_cast<int>(std::floor(stone->second))};
    Travel travel;
    if (std::find(m_stones_.begin(), m_stones_.end(), tile) == m_stones_.end()) {
        m_stones_.push_back(tile);
        travel.fresh = true;
    }
    m_player_.hp = m_derived_.max_hp;
    m_player_.mp_u = m_derived_.max_mp * 6000;  // a stone restores the mana too
    for (std::size_t i = 0; i < m_stones_.size(); ++i) {
        StoneStop stop;
        stop.x = m_stones_[i].first;
        stop.y = m_stones_[i].second;
        if (const auto settlement = settlement_containing(m_store_->seed(), params, stop.x, stop.y)) {
            stop.place = settlement->name;
            stop.region = params.regions[static_cast<std::size_t>(settlement->region)].name;
        }
        if (m_stones_[i] == tile) {
            travel.here = static_cast<int>(i);
        }
        travel.stops.push_back(std::move(stop));
    }
    m_travel_ = std::move(travel);
    return true;
}

bool WorldSim::travel_to(int index) {
    if (!m_travel_ || index < 0 || index >= static_cast<int>(m_travel_->stops.size()) || index == m_travel_->here) {
        return false;
    }
    const WorldSim::StoneStop stop = m_travel_->stops[static_cast<std::size_t>(index)];
    m_travel_.reset();
    teleport(static_cast<float>(stop.x) + 0.5F, static_cast<float>(stop.y) + 1.75F);  // one tile in front of the stone
    return true;
}

void WorldSim::open_shop() {
    if (m_store_) {
        const Region& region = m_store_->params().regions[static_cast<std::size_t>(
            region_at(m_store_->params(), static_cast<int>(std::floor(m_player_.position.x)),
                      static_cast<int>(std::floor(m_player_.position.y))))];
        m_shop_ = ShopDef{region.shop_price_pm, region.shop_stock};
    } else if (m_setup_.shop) {
        m_shop_ = m_setup_.shop;
    }
}

namespace {

int stack_limit(const ItemDef& item) {
    if (item.stack_max > 0) {
        return item.stack_max;
    }
    return item.kind == "weapon" || item.kind == "armor" || item.kind == "accessory" ? 1 : 99;
}

}  // namespace

void WorldSim::open_board() {
    if (!m_store_) {
        return;
    }
    const WorldParams& params = m_store_->params();
    const auto settlement =
        settlement_containing(m_store_->seed(), params, static_cast<int>(std::floor(m_player_.position.x)),
                              static_cast<int>(std::floor(m_player_.position.y)));
    if (!settlement) {
        return;
    }
    Board board;
    board.settlement = *settlement;
    board.day = m_world_ticks_ / params.time.day_ticks + 1;
    board.offers = offers_for(m_store_->seed(), params, *settlement, board.day);
    m_board_ = std::move(board);
}

int WorldSim::guild_rank() const {
    return m_store_ ? rank_index(m_store_->params().guild, m_story_.guild_points()) : 0;
}

bool WorldSim::accept_offer(int slot) {
    if (!m_board_ || slot < 0 || slot >= static_cast<int>(m_board_->offers.size())) {
        return false;
    }
    const Offer& offer = m_board_->offers[static_cast<std::size_t>(slot)];
    if (guild_rank() < offer.min_rank || m_story_.quests().count(offer.id) != 0) {
        return false;
    }
    m_story_.add_generated_quest(quest_from_offer(offer));
    m_story_.start_quest(offer.id);
    return true;
}

bool WorldSim::equip(const std::string& item_id) {
    const auto item = m_setup_.items.find(item_id);
    const auto owned = m_inventory_.find(item_id);
    if (item == m_setup_.items.end() || owned == m_inventory_.end() || owned->second < 1) {
        return false;
    }
    if (item->second.is_weapon && item->second.kind == "weapon" && m_equipped_weapon_ != item_id) {
        m_equipped_weapon_ = item_id;
    } else if (item->second.is_armor && item->second.kind == "armor" && m_equipped_armor_ != item_id) {
        m_equipped_armor_ = item_id;
    } else if (item->second.is_accessory && item->second.kind == "accessory" && m_equipped_accessory_ != item_id) {
        m_equipped_accessory_ = item_id;
    } else {
        return false;
    }
    recompute_derived();
    m_player_.hp = std::min(m_player_.hp, m_derived_.max_hp);
    return true;
}

std::int64_t WorldSim::buy_price(const std::string& item_id) const {
    const auto item = m_setup_.items.find(item_id);
    if (!m_shop_ || item == m_setup_.items.end() || item->second.price <= 0) {
        return 0;
    }
    return std::max<std::int64_t>(1, item->second.price * m_shop_->price_pm / 1000);
}

std::int64_t WorldSim::sell_price(const std::string& item_id) const {
    const auto item = m_setup_.items.find(item_id);
    if (item == m_setup_.items.end() || item->second.price <= 0) {
        return 0;
    }
    return std::max<std::int64_t>(1, item->second.price / 2);
}

bool WorldSim::buy(const std::string& item_id) {
    if (!m_shop_ || std::find(m_shop_->stock.begin(), m_shop_->stock.end(), item_id) == m_shop_->stock.end()) {
        return false;
    }
    const auto item = m_setup_.items.find(item_id);
    const std::int64_t price = buy_price(item_id);
    if (item == m_setup_.items.end() || price <= 0 || m_story_.gold() < price) {
        return false;
    }
    const auto owned = m_inventory_.find(item_id);
    const std::int64_t have = owned == m_inventory_.end() ? 0 : owned->second;
    if (have >= stack_limit(item->second)) {
        return false;
    }
    m_story_.set_gold(m_story_.gold() - price);
    m_inventory_[item_id] = have + 1;
    return true;
}

bool WorldSim::sell(const std::string& item_id) {
    const auto item = m_setup_.items.find(item_id);
    const auto owned = m_inventory_.find(item_id);
    if (!m_shop_ || item == m_setup_.items.end() || owned == m_inventory_.end() || owned->second < 1 ||
        sell_price(item_id) <= 0) {
        return false;
    }
    if (owned->second == 1 &&
        (item_id == m_equipped_weapon_ || item_id == m_equipped_armor_ || item_id == m_equipped_accessory_)) {
        return false;
    }
    m_story_.set_gold(m_story_.gold() + sell_price(item_id));
    if (--owned->second == 0) {
        m_inventory_.erase(owned);
    }
    return true;
}

bool WorldSim::use_item(const std::string& item_id) {
    if (m_story_.dialogue_active()) {
        return false;
    }
    const auto item = m_setup_.items.find(item_id);
    const auto owned = m_inventory_.find(item_id);
    if (item == m_setup_.items.end() || owned == m_inventory_.end() || owned->second < 1) {
        return false;
    }
    std::int64_t heal = 0;
    for (const ItemEffect& effect : item->second.effects) {
        if (effect.effect == "heal") {
            heal += effect.amount;
        }
    }
    std::int64_t mana = 0;
    for (const ItemEffect& effect : item->second.effects) {
        if (effect.effect == "restore_mp") {
            mana += effect.amount;
        }
    }
    heal = heal * m_setup_.gift.heal_pct / 100;
    const ItemEffect* fortify = nullptr;  // spec 06, "Fortify": attack up for a while
    const ItemEffect* ward = nullptr;     // spec 06, "Ward": defense up for a while
    const ItemEffect* regen = nullptr;    // spec 06, "Regen": health back over time
    const ItemEffect* haste = nullptr;    // spec 06, "Haste": faster on foot for a while
    bool cleanse = false;                 // spec 06, "Cleanse": the statuses go, when there is one
    for (const ItemEffect& effect : item->second.effects) {
        if (effect.effect == "fortify") {
            fortify = &effect;
        } else if (effect.effect == "ward") {
            ward = &effect;
        } else if (effect.effect == "regen") {
            regen = &effect;
        } else if (effect.effect == "haste") {
            haste = &effect;
        } else if (effect.effect == "cleanse") {
            cleanse = true;
        }
    }
    cleanse = cleanse && (m_player_.burn > 0 || m_player_.chill > 0 || m_player_.stun > 0 || m_player_.weaken > 0);
    const std::int64_t full_mp = m_derived_.max_mp * 6000;
    if (!((heal > 0 && m_player_.hp < m_derived_.max_hp) || (mana > 0 && m_player_.mp_u < full_mp) ||
          fortify != nullptr || ward != nullptr || regen != nullptr || haste != nullptr || cleanse)) {
        return false;
    }
    if (fortify != nullptr) {
        m_player_.fortify_pct = fortify->amount;
        m_player_.fortify = fortify->ticks;
    }
    if (ward != nullptr) {
        m_player_.ward_pct = ward->amount;
        m_player_.ward = ward->ticks;
    }
    if (regen != nullptr) {
        m_player_.regen_amount = regen->amount;
        m_player_.regen = regen->ticks;
    }
    if (haste != nullptr) {
        m_player_.haste_pct = haste->amount;
        m_player_.haste = haste->ticks;
    }
    if (cleanse) {
        m_player_.burn = m_player_.burn_clock = m_player_.chill = m_player_.stun = m_player_.weaken = 0;
    }
    if (heal > 0) {
        m_player_.hp = std::min(m_derived_.max_hp, m_player_.hp + heal);
    }
    if (mana > 0) {
        m_player_.mp_u = std::min(full_mp, m_player_.mp_u + mana * 6000);
    }
    if (--owned->second == 0) {
        m_inventory_.erase(owned);
    }
    return true;
}

std::vector<DamageEvent> WorldSim::take_events() { return std::exchange(m_events_, {}); }

// The companion follows the player and hits the nearest creature in range now and then (spec 10).
void WorldSim::update_companion() {
    const CompanionDef& c = *m_setup_.companion;
    const Player& p = m_player_;
    const float dx = p.position.x - m_companion_pos_.x;
    const float dy = p.position.y - m_companion_pos_.y;
    const float dist = std::sqrt(dx * dx + dy * dy);
    const float follow = static_cast<float>(c.follow_x100) / 100.0F;
    if (dist > kCompanionLeash) {
        m_companion_pos_ = p.position;
        m_companion_stay_ = false;  // too far: it comes back and follows again
    } else if (!m_companion_stay_ && dist > follow) {
        const float step = std::min(static_cast<float>(c.speed_x100) / 100.0F * kTickDt, dist - follow);
        m_companion_pos_.x += dx / dist * step;
        m_companion_pos_.y += dy / dist * step;
        m_collision_.resolve(m_companion_pos_.x, m_companion_pos_.y, kCompanionRadius);
    }
    if (c.care_ticks > 0 && m_companion_bond_ >= c.care_bond) {  // care (spec 10): it tends the player now and then
        ++m_companion_care_;
        if (m_companion_care_ >= c.care_ticks) {
            m_companion_care_ = 0;
            const std::int64_t full = m_derived_.max_hp;
            if (m_player_.hp > 0 && m_player_.hp < full) {
                m_player_.hp = std::min(full, m_player_.hp + std::max<std::int64_t>(1, full * c.care_pct / 100));
            }
        }
    }
    if (m_companion_cooldown_ > 0) {
        --m_companion_cooldown_;
    }
    if (m_companion_cooldown_ > 0) {
        return;
    }
    Enemy* target = nullptr;
    float best = 0.0F;
    for (Enemy& enemy : m_enemies_) {
        if (enemy.state == EnemyState::Dead) {
            continue;
        }
        const float d = std::sqrt((enemy.position.x - m_companion_pos_.x) * (enemy.position.x - m_companion_pos_.x) +
                                  (enemy.position.y - m_companion_pos_.y) * (enemy.position.y - m_companion_pos_.y));
        if (d > static_cast<float>(c.range_x100) / 100.0F + enemy.radius()) {
            continue;
        }
        if (enemy.marked) {  // the creature the player hit last, when it is in reach, before any other
            target = &enemy;
            break;
        }
        if (target == nullptr || d < best) {
            target = &enemy;
            best = d;
        }
    }
    if (target == nullptr) {
        return;
    }
    DamageInput in;
    in.atk = c.atk_base + c.atk_per_level * (p.level - 1) + std::min(m_companion_bond_ / 5, 10);  // the bond (spec 10)
    in.power_pct = 100;
    in.def_target = target->def.def;
    in.lvl_attacker = p.level;
    in.lvl_target = target->def.level;
    in.variance_pm = 1000;
    in.crit = false;
    in.crit_mult_pm = 1500;
    const std::int64_t amount = damage(in);
    target->hp -= amount;
    target->hit_flash = kHitFlashTicks;
    m_events_.push_back({target->position, amount, false, false});
    m_cues_.push_back({"hit", target->def.sound, target->position});
    m_companion_cooldown_ = c.cooldown_ticks;
    if (target->hp <= 0) {
        target->hp = 0;
        target->state = EnemyState::Dead;
        m_cues_.push_back({"die", target->def.sound, target->position});
        ++m_companion_bond_;
        on_kill(*target);
    }
}

bool WorldSim::companion_stay() {
    if (!m_setup_.companion) {
        return false;
    }
    m_companion_stay_ = !m_companion_stay_;
    return true;
}

bool WorldSim::near_station(const std::string& art) const {
    if (art.empty()) {
        return true;
    }
    const Vec2 at = m_player_.position;
    bool found = false;
    for_each_prop(at.x - 3.0F, at.y - 3.0F, at.x + 3.0F, at.y + 3.0F, [&](const Prop& prop) {
        if (prop.art == art &&
            std::sqrt((prop.x - at.x) * (prop.x - at.x) + (prop.y - at.y) * (prop.y - at.y)) <= 2.0F + prop.radius) {
            found = true;
        }
    });
    return found;
}

bool WorldSim::craft(const std::string& recipe_id) {
    if (m_story_.dialogue_active()) {
        return false;
    }
    const auto recipe = std::find_if(m_setup_.recipes.begin(), m_setup_.recipes.end(),
                                     [&](const RecipeDef& r) { return r.id == recipe_id; });
    if (recipe == m_setup_.recipes.end()) {
        return false;
    }
    if (!near_station(recipe->station)) {  // cooking needs a fire (spec 06, "Stations")
        return false;
    }
    for (const auto& [item, qty] : recipe->inputs) {
        const auto owned = m_inventory_.find(item);
        if (owned == m_inventory_.end() || owned->second < qty) {
            return false;
        }
    }
    for (const auto& [item, qty] : recipe->inputs) {
        auto owned = m_inventory_.find(item);
        owned->second -= qty;
        if (owned->second == 0) {
            m_inventory_.erase(owned);
        }
    }
    m_inventory_[recipe->output] += recipe->output_qty + title_bonus("craft");  // the titles of an artisan (spec 11)
    ++m_counters_["crafted"];
    m_cues_.push_back({"craft", "", m_player_.position});
    return true;
}

std::optional<std::pair<float, float>> WorldSim::gather_near() const {
    if (m_story_.dialogue_active() || m_setup_.gather_nodes.empty()) {
        return std::nullopt;
    }
    const Player& p = m_player_;
    bool found = false;
    float best_d = 0.0F;
    float best_x = 0.0F;
    float best_y = 0.0F;
    const float far = 4.5F;  // the largest reach plus a prop's radius
    for_each_prop(
        p.position.x - far, p.position.y - far, p.position.x + far, p.position.y + far, [&](const Prop& prop) {
            const auto node = m_setup_.gather_nodes.find(prop.art);
            if (node == m_setup_.gather_nodes.end()) {
                return;
            }
            const float d = std::sqrt((prop.x - p.position.x) * (prop.x - p.position.x) +
                                      (prop.y - p.position.y) * (prop.y - p.position.y));
            if (d > static_cast<float>(node->second.reach_x100) / 100.0F + prop.radius) {
                return;
            }
            const std::pair<int, int> key{static_cast<int>(std::floor(prop.x * 100.0F + 0.5F)),
                                          static_cast<int>(std::floor(prop.y * 100.0F + 0.5F))};
            const auto grown = m_gathered_.find(key);
            if (grown != m_gathered_.end() && m_world_ticks_ < grown->second.first) {
                return;
            }
            if (!found || d < best_d || (d == best_d && (prop.x < best_x || (prop.x == best_x && prop.y < best_y)))) {
                found = true;
                best_d = d;
                best_x = prop.x;
                best_y = prop.y;
            }
        });
    if (!found) {
        return std::nullopt;
    }
    return std::make_pair(best_x, best_y);
}

WorldSim::GatherResult WorldSim::gather() {
    GatherResult result;
    if (m_story_.dialogue_active() || m_setup_.gather_nodes.empty()) {
        return result;
    }
    const Player& p = m_player_;
    const GatherNode* best_node = nullptr;
    float best_d = 0.0F;
    float best_x = 0.0F;
    float best_y = 0.0F;
    const float far = 4.5F;  // the largest reach plus a prop's radius
    for_each_prop(p.position.x - far, p.position.y - far, p.position.x + far, p.position.y + far,
                  [&](const Prop& prop) {
                      const auto node = m_setup_.gather_nodes.find(prop.art);
                      if (node == m_setup_.gather_nodes.end()) {
                          return;
                      }
                      const float d = std::sqrt((prop.x - p.position.x) * (prop.x - p.position.x) +
                                                (prop.y - p.position.y) * (prop.y - p.position.y));
                      if (d > static_cast<float>(node->second.reach_x100) / 100.0F + prop.radius) {
                          return;
                      }
                      const std::pair<int, int> key{static_cast<int>(std::floor(prop.x * 100.0F + 0.5F)),
                                                    static_cast<int>(std::floor(prop.y * 100.0F + 0.5F))};
                      const auto grown = m_gathered_.find(key);
                      if (grown != m_gathered_.end() && m_world_ticks_ < grown->second.first) {
                          return;
                      }
                      if (best_node == nullptr || d < best_d ||
                          (d == best_d && (prop.x < best_x || (prop.x == best_x && prop.y < best_y)))) {
                          best_node = &node->second;
                          best_d = d;
                          best_x = prop.x;
                          best_y = prop.y;
                      }
                  });
    if (best_node == nullptr) {
        return result;
    }
    const std::pair<int, int> key{static_cast<int>(std::floor(best_x * 100.0F + 0.5F)),
                                  static_cast<int>(std::floor(best_y * 100.0F + 0.5F))};
    const auto before = m_gathered_.find(key);
    const int times = before == m_gathered_.end() ? 0 : before->second.second;
    const std::uint64_t h = hash64(fnv1a64("gather") ^ m_setup_.seed, key.first, key.second, times);
    result.node = true;
    result.sound = best_node->sound;
    for (std::size_t i = 0; i < best_node->drops.size(); ++i) {
        const GatherDrop& drop = best_node->drops[i];
        if (static_cast<std::int64_t>(mix64(h + 2 * i) % 1000U) < drop.weight_pm) {
            const std::int64_t qty =
                drop.qty_min +
                static_cast<std::int64_t>(mix64(h + 2 * i + 1) %
                                          static_cast<std::uint64_t>(drop.qty_max - drop.qty_min + 1)) +
                title_bonus("gather");  // the titles of a forager (spec 11)
            m_inventory_[drop.item] += qty;
            result.items.emplace_back(drop.item, qty);
        }
    }
    m_gathered_[key] = {m_world_ticks_ + best_node->cooldown_ticks, times + 1};
    ++m_counters_["gathered"];
    m_cues_.push_back({"gather", result.sound, p.position});
    return result;
}

std::vector<SimCue> WorldSim::take_cues() { return std::exchange(m_cues_, {}); }

void WorldSim::tick(float raw_x, float raw_y, bool attack, bool dodge, bool strike, bool parry) {
    Player& p = m_player_;
    const bool combat = m_setup_.enabled;
    ++m_world_ticks_;
    sync_window();
    if (m_store_ && m_window_valid_ && time_of_day_pm() != m_routine_tod_) {
        refresh_people(m_window_x_, m_window_y_);  // somebody goes home or comes out (spec 08)
    }
    mark_explored();
    if (m_story_.dialogue_active()) {
        raw_x = 0.0F;
        raw_y = 0.0F;
        attack = false;
        dodge = false;
        strike = false;
        parry = false;
    }
    if (p.iframes > 0) {
        --p.iframes;
    }
    if (p.cooldown > 0) {
        --p.cooldown;
    }
    if (p.dodge_cooldown > 0) {
        --p.dodge_cooldown;
    }
    if (p.parry_cooldown > 0) {
        --p.parry_cooldown;
    }
    if (p.death_save_cd > 0) {
        --p.death_save_cd;
    }
    p.mp_u = std::min(m_derived_.max_mp * 6000, p.mp_u + m_derived_.mp_regen_x100 * m_setup_.gift.mp_regen_pct / 100);

    if (p.burn > 0) {  // status effects on the player (spec 05)
        --p.burn;
        if (++p.burn_clock % kPlayerBurnPeriod == 0) {
            const std::int64_t amount = std::max<std::int64_t>(1, m_derived_.max_hp * kPlayerBurnPct / 100);
            p.hp = std::max<std::int64_t>(1, p.hp - amount);
        }
    }
    if (p.stun > 0) {
        --p.stun;
        attack = false;
        dodge = false;
        strike = false;
        parry = false;
    }

    if (combat && parry && p.parry_ticks == 0 && p.parry_cooldown == 0 && p.phase == AttackPhase::None &&
        p.dodge_ticks == 0) {
        p.parry_ticks =
            kParryTicks +
            static_cast<int>(title_bonus("parry"));  // the window opens (spec 05); a guard's titles widen it
        p.parry_cooldown = kParryCooldown;
    }
    if (p.parry_ticks > 0) {  // a parry in progress allows no attack and no roll
        attack = false;
        dodge = false;
        strike = false;
    }

    const Vec2 direction = normalize_input(raw_x, raw_y);
    const bool moving = direction.x != 0.0F || direction.y != 0.0F;
    if (combat && dodge && m_setup_.dodge.enabled && p.dodge_ticks == 0 && p.dodge_cooldown == 0 &&
        p.phase == AttackPhase::None) {  // the dodge roll starts (spec 05, "Dodge roll")
        const Vec2 way = moving ? direction : p.facing;
        const float length = std::sqrt(way.x * way.x + way.y * way.y);
        p.dodge_dir = {way.x / length, way.y / length};
        p.facing = p.dodge_dir;
        if (p.dodge_dir.x != 0.0F) {
            p.facing_left = p.dodge_dir.x < 0.0F;
        }
        p.dodge_ticks = m_setup_.dodge.ticks;
        p.dodge_cooldown = m_setup_.dodge.cooldown * m_setup_.gift.dodge_cooldown_pct / 100;
        p.iframes = std::max(p.iframes, m_setup_.dodge.iframes);
    }
    if (p.dodge_ticks > 0) {
        --p.dodge_ticks;
        if (!p.moving) {
            p.moving = true;
            p.clip_tick = 0;
        } else {
            ++p.clip_tick;
        }
        const float roll_speed = static_cast<float>(m_derived_.move_speed_x100) / 100.0F *
                                 static_cast<float>(m_setup_.dodge.speed_mult_x100) / 100.0F;
        m_collision_.step(p.position, p.dodge_dir, roll_speed);
    } else {
        if (combat && moving && (p.phase == AttackPhase::None || p.phase == AttackPhase::Startup)) {
            const float length = std::sqrt(direction.x * direction.x + direction.y * direction.y);
            p.facing = {direction.x / length, direction.y / length};
        }
        const std::int64_t walk_x100 = p.haste > 0 ? m_derived_.move_speed_x100 * (100 + p.haste_pct) / 100
                                                   : m_derived_.move_speed_x100;  // a brew of haste (spec 06)
        float speed = combat ? static_cast<float>(walk_x100) / 100.0F : m_speed_;
        if (combat && p.phase != AttackPhase::None) {
            speed *= kAttackMoveMult;
        }
        if (p.chill > 0) {
            speed *= 0.5F;
        }
        m_collision_.step(p.position, direction, speed);

        if (direction.x != 0.0F) {
            p.facing_left = direction.x < 0.0F;
        }
        if (moving != p.moving) {
            p.moving = moving;
            p.clip_tick = 0;
        } else {
            ++p.clip_tick;
        }

        if (!combat) {
            return;
        }
        if (p.phase == AttackPhase::None && p.cooldown == 0) {
            if (strike && m_setup_.strike.enabled && p.mp_u >= m_setup_.strike.mp * 6000) {
                p.mp_u -= m_setup_.strike.mp * 6000;
                p.using_strike = true;
                p.phase = AttackPhase::Startup;
                p.phase_tick = 0;
                p.cooldown = m_setup_.strike.skill.cooldown;
                std::fill(m_hit_set_.begin(), m_hit_set_.end(), false);
            } else if (attack) {
                p.using_strike = false;
                p.phase = AttackPhase::Startup;
                p.phase_tick = 0;
                p.cooldown = m_setup_.skill.cooldown;
                std::fill(m_hit_set_.begin(), m_hit_set_.end(), false);
            }
        }
    }
    advance_attack();
    if (m_setup_.companion) {
        update_companion();
    }
    for (Enemy& enemy : m_enemies_) {
        update_enemy(enemy);
        if (enemy.hit_flash > 0) {
            --enemy.hit_flash;
        }
    }
    if (p.parry_ticks > 0) {
        --p.parry_ticks;
    }
    if (p.chill > 0) {
        --p.chill;
    }
    if (p.weaken > 0) {
        --p.weaken;
    }
    if (p.fortify > 0) {  // a meal that fortifies (spec 06, "Fortify") wears off
        --p.fortify;
    }
    if (p.ward > 0) {  // and a brew that wards (spec 06, "Ward")
        --p.ward;
    }
    if (p.haste > 0) {  // a brew of haste (spec 06, "Haste") wears off
        --p.haste;
    }
    if (p.regen > 0) {  // a dish that heals over time (spec 06, "Regen"): `amount` every second
        --p.regen;
        if (p.regen % 60 == 0 && p.hp > 0 && p.hp < m_derived_.max_hp) {
            p.hp = std::min(m_derived_.max_hp, p.hp + p.regen_amount);
        }
    }
}

void WorldSim::advance_attack() {
    Player& p = m_player_;
    const SkillDef& s = m_player_.using_strike ? m_setup_.strike.skill : m_setup_.skill;
    switch (p.phase) {
        case AttackPhase::Startup:
            if (++p.phase_tick >= s.startup) {
                p.phase = AttackPhase::Active;
                p.phase_tick = 0;
            }
            break;
        case AttackPhase::Active:
            do_hits();
            if (++p.phase_tick >= s.active) {
                p.phase = AttackPhase::Recovery;
                p.phase_tick = 0;
            }
            break;
        case AttackPhase::Recovery:
            if (++p.phase_tick >= s.recovery) {
                p.phase = AttackPhase::None;
            }
            break;
        case AttackPhase::None:
            break;
    }
}

void WorldSim::do_hits() {
    Player& p = m_player_;
    const SkillDef& s = m_player_.using_strike ? m_setup_.strike.skill : m_setup_.skill;
    const auto cos_half = static_cast<float>(std::cos(static_cast<double>(s.angle_deg) / 2.0 * kPi / 180.0));
    for (std::size_t index = 0; index < m_enemies_.size(); ++index) {
        Enemy& enemy = m_enemies_[index];
        if (enemy.state == EnemyState::Dead || m_hit_set_[index]) {
            continue;
        }
        const float dx = enemy.position.x - p.position.x;
        const float dy = enemy.position.y - p.position.y;
        const float dist = std::sqrt(dx * dx + dy * dy);
        if (dist > static_cast<float>(s.radius_x100) / 100.0F + enemy.radius()) {
            continue;
        }
        if (dist > 0.0F) {
            const float dot = (dx * p.facing.x + dy * p.facing.y) / dist;
            if (dot < cos_half) {
                continue;
            }
        }
        m_hit_set_[index] = true;
        for (Enemy& other : m_enemies_) {  // the companion's next target (spec 10, "Teamwork")
            other.marked = &other == &enemy;
        }
        const std::int64_t variance = 950 + static_cast<std::int64_t>(m_combat_rng_.next_bounded(101));
        const bool crit = static_cast<std::int64_t>(m_combat_rng_.next_bounded(1000)) < m_derived_.crit_chance_pm;
        DamageInput in;
        in.atk = s.magical ? m_derived_.matk : m_derived_.atk;
        const std::int64_t fortify = p.fortify > 0 ? p.fortify_pct : 0;  // a meal that fortifies (spec 06)
        in.atk =
            in.atk * (100 + title_attack_pct() + fortify) / 100;  // the titles earned make the hits stronger (spec 11)
        if (p.weaken > 0) {
            in.atk = in.atk * 75 / 100;
        }
        in.power_pct = s.power_pct;
        in.def_target = enemy.def.def;
        in.elem_mult_pm = element_multiplier(enemy.def);
        in.lvl_attacker = p.level;
        in.lvl_target = enemy.def.level;
        in.variance_pm = variance;
        in.crit = crit;
        in.crit_mult_pm = m_derived_.crit_mult_pm;
        std::int64_t amount = damage(in);
        if (enemy.broken > 0) {
            amount = amount * kStaggerDamagePct / 100;
        }
        enemy.hp -= amount;
        if (const auto charm = m_setup_.items.find(m_equipped_accessory_);  // an accessory that drains (spec 06)
            charm != m_setup_.items.end() && charm->second.acc_drain_pm > 0 && p.hp > 0 && p.hp < m_derived_.max_hp) {
            p.hp = std::min(m_derived_.max_hp,
                            p.hp + std::max<std::int64_t>(1, amount * charm->second.acc_drain_pm / 1000));
        }
        enemy.hit_flash = kHitFlashTicks;
        m_events_.push_back({enemy.position, amount, crit, false, in.elem_mult_pm > 1000});
        m_cues_.push_back({"hit", enemy.def.sound, enemy.position, crit, in.elem_mult_pm > 1000});
        if (enemy.hp > 0) {
            apply_status(enemy);
            if (enemy.def.stagger_pct > 0 && enemy.broken == 0) {  // the stagger bar (spec 05, "Stagger")
                enemy.stagger += amount * (p.using_strike ? 2 : 1);
                if (enemy.stagger >= std::max<std::int64_t>(1, enemy.def.hp * enemy.def.stagger_pct / 100)) {
                    enemy.stagger = 0;
                    enemy.broken = kStaggerTicks;
                    enemy.stun = std::max(enemy.stun, kStaggerTicks);
                    m_cues_.push_back({"parry", enemy.def.sound, enemy.position});  // the same clang as a parry
                }
            }
        }
        if (enemy.hp <= 0) {
            enemy.hp = 0;
            enemy.state = EnemyState::Dead;
            m_cues_.push_back({"die", enemy.def.sound, enemy.position});
            on_kill(enemy);
        }
    }
}

std::string WorldSim::hit_element() const {
    const SkillDef& s = m_player_.using_strike ? m_setup_.strike.skill : m_setup_.skill;
    if (s.element != "none") {
        return s.element;
    }
    const auto weapon = m_setup_.items.find(m_equipped_weapon_);
    if (weapon == m_setup_.items.end() || !weapon->second.is_weapon) {
        return "none";
    }
    return weapon->second.weapon_element;
}

std::int64_t WorldSim::element_multiplier(const EnemyDef& target) const {
    const std::string element = hit_element();
    if (element == "none") {
        return 1000;
    }
    const auto weakness = target.weaknesses_pm.find(element);
    if (weakness != target.weaknesses_pm.end()) {
        return weakness->second;
    }
    return target.element == element ? 500 : 1000;
}

void WorldSim::on_kill(Enemy& enemy) {
    Player& p = m_player_;
    ++p.kills;
    if (!enemy.def.id.empty()) {
        ++m_bestiary_[enemy.def.id];
    }
    if (m_store_) {
        m_cleared_[{enemy.spawner_x, enemy.spawner_y}] = m_world_ticks_;
    }
    for (const DropDef& drop : enemy.def.drops) {
        if (static_cast<std::int64_t>(m_loot_rng_.next_bounded(1000)) < drop.weight_pm) {
            std::int64_t quantity = drop.qty_min;
            if (drop.qty_max > drop.qty_min) {
                quantity += static_cast<std::int64_t>(
                    m_loot_rng_.next_bounded(static_cast<std::uint32_t>(drop.qty_max - drop.qty_min + 1)));
            }
            m_inventory_[drop.item] += quantity;
        }
    }
    grant_xp(xp_gain(enemy.def.xp, enemy.def.level, p.level) * (100 + title_bonus("xp")) /
             100);  // a veteran's titles (spec 11)
    m_story_.on_kill(enemy.def.id);
}

std::int64_t WorldSim::title_progress(const TitleDef& t) const {
    if (t.kind == "kills") {
        return m_player_.kills;
    }
    if (t.kind == "kills_of") {
        const auto it = m_bestiary_.find(t.enemy);
        return it == m_bestiary_.end() ? 0 : it->second;
    }
    if (t.kind == "level") {
        return m_player_.level;
    }
    if (t.kind == "species") {
        return static_cast<std::int64_t>(m_bestiary_.size());
    }
    if (t.kind == "quests") {
        std::int64_t quests_done = 0;
        for (const auto& entry : m_story_.quests()) {
            quests_done += entry.second.done ? 1 : 0;
        }
        return quests_done;
    }
    const auto counter = m_counters_.find(t.kind);
    return counter == m_counters_.end() ? 0 : counter->second;
}

std::vector<std::string> WorldSim::earned_titles() const {
    std::vector<std::string> earned;
    for (const TitleDef& t : m_setup_.titles) {
        if (title_progress(t) >= t.count) {
            earned.push_back(t.id);
        }
    }
    return earned;
}

std::int64_t WorldSim::title_bonus(const std::string& what) const {
    const std::vector<std::string> earned = earned_titles();
    std::int64_t bonus = 0;
    for (const TitleDef& t : m_setup_.titles) {
        if (std::find(earned.begin(), earned.end(), t.id) != earned.end()) {
            bonus += what == "gather"  ? t.gather_bonus
                     : what == "craft" ? t.craft_bonus
                     : what == "parry" ? t.parry_bonus
                                       : t.xp_pct;
        }
    }
    return bonus;
}

std::int64_t WorldSim::title_attack_pct() const {
    const std::vector<std::string> earned = earned_titles();
    std::int64_t pct = 0;
    for (const TitleDef& t : m_setup_.titles) {
        if (t.atk_pct != 0 && std::find(earned.begin(), earned.end(), t.id) != earned.end()) {
            pct += t.atk_pct;
        }
    }
    return pct;
}

void WorldSim::grant_xp(std::int64_t amount) {
    Player& p = m_player_;
    p.xp += amount;
    while (p.level < kMaxLevel && p.level - 1 < static_cast<std::int64_t>(m_setup_.xp_table.size()) &&
           p.xp >= m_setup_.xp_table[static_cast<std::size_t>(p.level - 1)]) {
        p.xp -= m_setup_.xp_table[static_cast<std::size_t>(p.level - 1)];
        ++p.level;
        recompute_derived();
        p.hp = m_derived_.max_hp;
    }
}

void WorldSim::apply_status(Enemy& enemy) {
    const std::string element = hit_element();
    if (element == "none" || element_multiplier(enemy.def) == 0) {
        return;
    }
    int chance = 0;
    int ticks = 0;
    if (element == "fire") {
        chance = 350;
        ticks = 150;
    } else if (element == "water") {
        chance = 400;
        ticks = 180;
    } else if (element == "wind") {
        chance = 300;
        ticks = 45;
    } else if (element == "earth") {
        chance = 300;
        ticks = 75;
    } else {  // light, dark
        chance = 350;
        ticks = 240;
    }
    if (static_cast<int>(m_combat_rng_.next_bounded(1000)) >= chance) {
        return;
    }
    if (element == "fire") {
        enemy.burn = ticks;
        enemy.burn_clock = 0;
    } else if (element == "water") {
        enemy.chill = ticks;
    } else if (element == "wind" || element == "earth") {
        enemy.stun = ticks;
    } else {
        enemy.weaken = ticks;
    }
}

void WorldSim::update_enemy(Enemy& enemy) {
    if (enemy.state == EnemyState::Dead) {
        return;
    }
    if (enemy.broken > 0) {
        --enemy.broken;
    }
    if (enemy.burn > 0) {  // a burn hurts every 30 ticks, whatever the defense
        --enemy.burn;
        ++enemy.burn_clock;
        if (enemy.burn_clock % 30 == 0) {
            const std::int64_t amount = std::max<std::int64_t>(1, enemy.def.hp * 3 / 100);
            enemy.hp -= amount;
            m_events_.push_back({enemy.position, amount, false, false});
            if (enemy.hp <= 0) {
                enemy.hp = 0;
                enemy.state = EnemyState::Dead;
                m_cues_.push_back({"die", enemy.def.sound, enemy.position});
                on_kill(enemy);
                return;
            }
        }
    }
    if (enemy.stun > 0) {  // a stunned creature does nothing
        --enemy.stun;
        return;
    }
    behave_enemy(enemy);
    if (enemy.chill > 0) {
        --enemy.chill;
    }
    if (enemy.weaken > 0) {
        --enemy.weaken;
    }
}

void WorldSim::behave_enemy(Enemy& enemy) {
    const BehaviorDef& b = enemy.def.behavior;
    const Player& p = m_player_;
    const float dist = distance(enemy.position.x, enemy.position.y, p.position.x, p.position.y);
    switch (enemy.state) {
        case EnemyState::Idle:
            if (dist <= static_cast<float>(b.aggro_x100 * m_setup_.gift.aggro_pct / 100) / 100.0F) {
                enemy.state = EnemyState::Chase;
                enemy.state_tick = 0;
                m_cues_.push_back({"aggro", enemy.def.sound, enemy.position});
            }
            break;
        case EnemyState::Chase:
            if (dist > static_cast<float>(b.leash_x100) / 100.0F) {
                enemy.state = EnemyState::Return;
            } else if (dist <= static_cast<float>(b.attack_range_x100) / 100.0F) {
                enemy.state = EnemyState::Attack;
                enemy.state_tick = 0;
                m_cues_.push_back({"attack", enemy.def.sound, enemy.position});
            } else {
                move_enemy(enemy, p.position.x, p.position.y);
            }
            break;
        case EnemyState::Attack:
            ++enemy.state_tick;
            if (enemy.state_tick == b.windup_ticks && dist <= static_cast<float>(b.hit_range_x100) / 100.0F &&
                p.iframes == 0) {
                hurt_player(enemy);
            }
            if (enemy.state_tick >= b.windup_ticks + b.recovery_ticks) {
                enemy.state = EnemyState::Chase;
                enemy.state_tick = 0;
            }
            break;
        case EnemyState::Return:
            if (distance(enemy.position.x, enemy.position.y, enemy.home.x, enemy.home.y) <= kReturnArrival) {
                enemy.state = EnemyState::Idle;
                enemy.hp = enemy.def.hp;
                enemy.stagger = 0;
            } else {
                move_enemy(enemy, enemy.home.x, enemy.home.y);
            }
            break;
        case EnemyState::Dead:
            break;
    }
}

void WorldSim::move_enemy(Enemy& enemy, float target_x, float target_y) {
    const float dx = target_x - enemy.position.x;
    const float dy = target_y - enemy.position.y;
    const float dist = std::sqrt(dx * dx + dy * dy);
    const float speed = static_cast<float>(enemy.def.speed_x100) / 100.0F;
    const float step = (enemy.chill > 0 ? speed / 2.0F : speed) * kTickDt;
    if (dist > 0.0F) {
        if (dist <= step) {
            enemy.position = {target_x, target_y};
        } else {
            enemy.position.x += dx / dist * step;
            enemy.position.y += dy / dist * step;
        }
    }
    m_collision_.resolve(enemy.position.x, enemy.position.y, enemy.radius());
}

void WorldSim::hurt_player(Enemy& enemy) {
    if (m_player_.parry_ticks > 0) {  // parried: no damage, the attacker is stunned and the player is safe for a moment
        enemy.stun = kParryStun;
        ++m_counters_["parried"];
        m_player_.iframes = std::max(m_player_.iframes, kParryIframes);
        m_cues_.push_back({"parry", enemy.def.sound, enemy.position});
        return;
    }
    Player& p = m_player_;
    const std::int64_t variance = 950 + static_cast<std::int64_t>(m_combat_rng_.next_bounded(101));
    DamageInput in;
    in.atk = enemy.weaken > 0 ? enemy.def.atk * 75 / 100 : enemy.def.atk;
    in.power_pct = 100;
    in.def_target =
        p.ward > 0 ? m_derived_.def * (100 + p.ward_pct) / 100 : m_derived_.def;  // a brew that wards (spec 06)
    in.lvl_attacker = enemy.def.level;
    in.lvl_target = p.level;
    in.variance_pm = variance;
    const std::int64_t amount = damage(in);
    p.hp -= amount;
    p.iframes = kPlayerHitIframes;
    m_events_.push_back({p.position, amount, false, true});
    m_cues_.push_back({"hurt", enemy.def.sound, p.position});
    if (p.hp <= 0 && m_setup_.gift.death_save_ticks > 0 && p.death_save_cd == 0) {  // the death save (spec 18)
        p.hp = 1;
        p.death_save_cd = m_setup_.gift.death_save_ticks;
    }
    if (p.hp <= 0) {
        ++p.deaths;
        p.hp = m_derived_.max_hp;
        p.position = m_spawn_;
        p.phase = AttackPhase::None;
        p.phase_tick = 0;
        p.dodge_ticks = 0;
        p.dodge_cooldown = 0;
        p.parry_ticks = 0;
        p.parry_cooldown = 0;
        p.burn = p.burn_clock = p.chill = p.stun = p.weaken = p.fortify = p.ward = p.regen = p.haste = 0;
        p.mp_u = m_derived_.max_mp * 6000;
        p.iframes = kRespawnIframes;
        return;
    }
    const std::string& element = enemy.def.element;  // the status of the creature's element (spec 05)
    if (element == "none" || element.empty()) {
        return;
    }
    int chance = 350;  // light, dark: weaken
    int ticks = 240;
    if (element == "fire") {
        chance = 350;
        ticks = 150;
    } else if (element == "water") {
        chance = 400;
        ticks = 180;
    } else if (element == "wind") {
        chance = 300;
        ticks = 45;
    } else if (element == "earth") {
        chance = 300;
        ticks = 75;
    }
    if (static_cast<int>(m_combat_rng_.next_bounded(1000)) >= chance) {
        return;
    }
    if (element == "fire") {
        p.burn = ticks;
        p.burn_clock = 0;
    } else if (element == "water") {
        p.chill = ticks;
    } else if (element == "wind" || element == "earth") {
        p.stun = ticks;
    } else {
        p.weaken = ticks;
    }
}

SaveState WorldSim::capture() const {
    SaveState s;
    const Player& p = m_player_;
    s.position = p.position;
    s.facing = p.facing;
    s.facing_left = p.facing_left;
    s.moving = p.moving;
    s.clip_tick = p.clip_tick;
    s.hp = p.hp;
    s.level = p.level;
    s.xp = p.xp;
    s.deaths = p.deaths;
    s.kills = p.kills;
    s.iframes = p.iframes;
    s.cooldown = p.cooldown;
    s.phase = p.phase;
    s.phase_tick = p.phase_tick;
    s.hit_set = m_hit_set_;
    s.combat_state = m_combat_rng_.state();
    s.combat_inc = m_combat_rng_.inc();
    s.loot_state = m_loot_rng_.state();
    s.loot_inc = m_loot_rng_.inc();
    for (const Enemy& enemy : m_enemies_) {
        s.enemies.push_back({enemy.position, enemy.hp, enemy.state, enemy.state_tick, m_store_ != nullptr,
                             enemy.spawner_x, enemy.spawner_y});
    }
    for (const auto& [spawner, died] : m_cleared_) {
        s.cleared.push_back({spawner.first, spawner.second, died});
    }
    s.stones = m_stones_;
    s.bestiary = m_bestiary_;
    s.counters = m_counters_;
    s.talents = m_talents_;
    if (m_setup_.companion) {
        s.has_companion = true;
        s.companion_x = m_companion_pos_.x;
        s.companion_y = m_companion_pos_.y;
        s.companion_cooldown = m_companion_cooldown_;
        s.companion_stay = m_companion_stay_;
        s.companion_bond = m_companion_bond_;
    }
    s.explored.assign(m_explored_.begin(), m_explored_.end());
    std::sort(s.explored.begin(), s.explored.end(), [](const auto& a, const auto& b) {  // rows first (spec 12)
        return a.second != b.second ? a.second < b.second : a.first < b.first;
    });
    s.world_ticks = m_world_ticks_;
    s.inventory = m_inventory_;
    s.equipped_weapon = m_equipped_weapon_;
    s.equipped_armor = m_equipped_armor_;
    s.equipped_accessory = m_equipped_accessory_;
    s.story = m_story_.capture();
    return s;
}

bool WorldSim::restore(const SaveState& s, std::string& error) {
    if (m_store_) {
        // The saved enemies must be exactly those of the window around the saved position (spec 12).
        const int cx = chunk_of(static_cast<int>(std::floor(s.position.x)));
        const int cy = chunk_of(static_cast<int>(std::floor(s.position.y)));
        m_store_->keep_around(cx, cy);
        std::set<std::pair<int, int>> cleared;
        for (const ClearedSpawner& c : s.cleared) {
            cleared.insert({c.x, c.y});
        }
        std::set<std::pair<int, int>> in_window;
        for (int j = cy - kActiveRadius; j <= cy + kActiveRadius; ++j) {
            for (int i = cx - kActiveRadius; i <= cx + kActiveRadius; ++i) {
                for (const auto& spawner : m_store_->find(i, j)->spawners) {
                    in_window.insert(spawner);
                }
            }
        }
        std::set<std::pair<int, int>> found;
        bool valid = s.hit_set.size() == s.enemies.size();
        for (const SaveEnemy& e : s.enemies) {
            const std::pair<int, int> spawner{e.spawner_x, e.spawner_y};
            // Every enemy belongs to a spawner of the window; the enemy of a cleared spawner is dead.
            valid = valid && e.has_spawner && in_window.count(spawner) != 0 && found.insert(spawner).second &&
                    (cleared.count(spawner) == 0 || e.state == EnemyState::Dead);
        }
        for (const auto& spawner : in_window) {
            valid = valid && (cleared.count(spawner) != 0 || found.count(spawner) != 0);
        }
        if (!valid) {
            error = "the save has different enemies than the generated world";
            return false;
        }
    } else if (s.enemies.size() != m_enemies_.size() || s.hit_set.size() != m_hit_set_.size()) {
        error = "the save has a different number of enemies than the loaded map";
        return false;
    }
    if (s.level < 1 || s.level > kMaxLevel) {
        error = "invalid level in the save";
        return false;
    }
    if (!m_story_.restore(s.story)) {
        error = "the save refers to a quest or dialogue that does not exist";
        return false;
    }
    Player& p = m_player_;
    p.position = s.position;
    p.facing = s.facing;
    p.facing_left = s.facing_left;
    p.moving = s.moving;
    p.clip_tick = s.clip_tick;
    p.level = s.level;
    recompute_derived();
    p.hp = s.hp;
    p.xp = s.xp;
    p.deaths = s.deaths;
    p.kills = s.kills;
    p.iframes = s.iframes;
    p.cooldown = s.cooldown;
    p.phase = s.phase;
    p.phase_tick = s.phase_tick;
    m_hit_set_ = s.hit_set;
    m_player_.death_save_cd = 0;
    m_player_.dodge_ticks = 0;  // a roll in progress is not saved (spec 05)
    m_player_.dodge_cooldown = 0;
    m_player_.parry_ticks = 0;
    m_player_.parry_cooldown = 0;
    m_player_.burn = m_player_.burn_clock = m_player_.chill = m_player_.stun = m_player_.weaken = m_player_.fortify =
        m_player_.ward = m_player_.regen = m_player_.haste = 0;
    m_player_.mp_u = m_derived_.max_mp * 6000;  // nor is the mana: a loaded game starts full
    m_player_.using_strike = false;
    m_combat_rng_.set_state(s.combat_state, s.combat_inc);
    m_loot_rng_.set_state(s.loot_state, s.loot_inc);
    if (m_store_) {
        m_enemies_.clear();
        for (const SaveEnemy& e : s.enemies) {
            Enemy enemy;
            enemy.def = stream_enemy_at(e.spawner_x, e.spawner_y);
            enemy.home = {static_cast<float>(e.spawner_x) + 0.5F, static_cast<float>(e.spawner_y) + 0.5F};
            enemy.spawner_x = e.spawner_x;
            enemy.spawner_y = e.spawner_y;
            m_enemies_.push_back(std::move(enemy));
        }
        m_cleared_.clear();
        for (const ClearedSpawner& c : s.cleared) {
            m_cleared_[{c.x, c.y}] = c.died;
        }
        m_npcs_.clear();
        const int wcx = chunk_of(static_cast<int>(std::floor(s.position.x)));
        const int wcy = chunk_of(static_cast<int>(std::floor(s.position.y)));
        for (int j = wcy - kActiveRadius; j <= wcy + kActiveRadius; ++j) {
            for (int i = wcx - kActiveRadius; i <= wcx + kActiveRadius; ++i) {
                add_chunk_people(i, j);
            }
        }
        rebuild_npc_circles();
        m_window_valid_ = true;
        m_window_x_ = chunk_of(static_cast<int>(std::floor(s.position.x)));
        m_window_y_ = chunk_of(static_cast<int>(std::floor(s.position.y)));
    }
    for (std::size_t i = 0; i < m_enemies_.size(); ++i) {
        m_enemies_[i].position = s.enemies[i].position;
        m_enemies_[i].hp = s.enemies[i].hp;
        m_enemies_[i].state = s.enemies[i].state;
        m_enemies_[i].state_tick = s.enemies[i].state_tick;
        m_enemies_[i].hit_flash = 0;
    }
    m_inventory_ = s.inventory;
    m_equipped_weapon_ = s.equipped_weapon == "<start>" ? m_setup_.start_weapon : s.equipped_weapon;
    m_equipped_armor_ = s.equipped_armor;
    m_equipped_accessory_ = s.equipped_accessory;
    m_shop_.reset();
    m_board_.reset();
    m_travel_.reset();
    m_stones_ = s.stones;
    m_bestiary_ = s.bestiary;
    m_counters_ = s.counters;
    m_talents_ = s.talents;
    recompute_derived();       // the talents change the derived stats
    if (m_setup_.companion) {  // a save without a companion (an older one) puts it next to the player
        m_companion_pos_ = s.has_companion ? Vec2{s.companion_x, s.companion_y} : s.position;
        m_companion_cooldown_ = s.has_companion ? s.companion_cooldown : m_setup_.companion->cooldown_ticks;
        m_companion_stay_ = s.has_companion && s.companion_stay;
        m_companion_bond_ = s.has_companion ? s.companion_bond : 0;
    }
    recompute_derived();
    m_player_.hp = std::min(s.hp, m_derived_.max_hp);
    m_explored_ = std::set<std::pair<int, int>>(s.explored.begin(), s.explored.end());
    mark_explored();
    m_world_ticks_ = s.world_ticks >= 0 ? s.world_ticks : (m_store_ ? m_store_->params().time.start_tick : 0);
    if (m_store_ && m_window_valid_) {
        refresh_people(m_window_x_, m_window_y_);  // the people of the saved time of day
    }
    m_events_.clear();
    return true;
}

Camera WorldSim::camera(float view_w, float view_h) const {
    return {axis_origin(m_player_.position.x, view_w, static_cast<float>(m_map_.width)),
            axis_origin(m_player_.position.y, view_h, static_cast<float>(m_map_.height))};
}

}  // namespace aether
