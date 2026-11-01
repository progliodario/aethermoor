#include "sim/world.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <utility>

namespace aether {

namespace {

constexpr int kPlayerHitIframes = 45;
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
    m_player_.position = {m_map_.spawn_x, m_map_.spawn_y};
    if (m_store_) {
        m_world_ticks_ = m_store_->params().time.start_tick;
        m_store_->keep_around(chunk_of(static_cast<int>(std::floor(m_player_.position.x))),
                              chunk_of(static_cast<int>(std::floor(m_player_.position.y))));
    }
    m_collision_.resolve(m_player_.position.x, m_player_.position.y);
    m_spawn_ = m_player_.position;
    for (const NpcDef& npc : m_setup_.story.npcs) {
        m_collision_.add_prop({npc.x, npc.y, kNpcRadius});
    }
    if (m_setup_.enabled) {
        m_player_.level = m_setup_.start_level;
        recompute_derived();
        m_player_.hp = m_derived_.max_hp;
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

void WorldSim::add_chunk_enemies(int cx, int cy) {
    if (!m_setup_.stream_enemy) {
        return;
    }
    const Chunk* chunk = m_store_->find(cx, cy);
    if (chunk == nullptr) {
        return;
    }
    for (const auto& [sx, sy] : chunk->spawners) {
        const auto died = m_cleared_.find({sx, sy});
        if (died != m_cleared_.end()) {
            // A spawner whose enemy has been dead long enough is ready again when its chunk enters the window (spec 08).
            if (m_world_ticks_ - died->second < m_store_->params().spawner_respawn_ticks) {
                continue;
            }
            m_cleared_.erase(died);
        }
        Enemy enemy;
        enemy.def = *m_setup_.stream_enemy;
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
    m_window_valid_ = true;
    m_window_x_ = cx;
    m_window_y_ = cy;
}

void WorldSim::recompute_derived() {
    Equipment equipment;
    equipment.weapon_atk = m_setup_.player.weapon_atk;
    equipment.weapon_matk = m_setup_.player.weapon_matk;
    m_derived_ = derived_stats(m_player_.level, primary_at_level(m_setup_.player, m_player_.level), equipment);
}

std::vector<DamageEvent> WorldSim::take_events() { return std::exchange(m_events_, {}); }

void WorldSim::tick(float raw_x, float raw_y, bool attack) {
    Player& p = m_player_;
    const bool combat = m_setup_.enabled;
    ++m_world_ticks_;
    sync_window();
    mark_explored();
    if (m_story_.dialogue_active()) {
        raw_x = 0.0F;
        raw_y = 0.0F;
        attack = false;
    }
    if (p.iframes > 0) {
        --p.iframes;
    }
    if (p.cooldown > 0) {
        --p.cooldown;
    }

    const Vec2 direction = normalize_input(raw_x, raw_y);
    const bool moving = direction.x != 0.0F || direction.y != 0.0F;
    if (combat && moving && (p.phase == AttackPhase::None || p.phase == AttackPhase::Startup)) {
        const float length = std::sqrt(direction.x * direction.x + direction.y * direction.y);
        p.facing = {direction.x / length, direction.y / length};
    }
    float speed = combat ? static_cast<float>(m_derived_.move_speed_x100) / 100.0F : m_speed_;
    if (combat && p.phase != AttackPhase::None) {
        speed *= kAttackMoveMult;
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
    if (attack && p.phase == AttackPhase::None && p.cooldown == 0) {
        p.phase = AttackPhase::Startup;
        p.phase_tick = 0;
        p.cooldown = m_setup_.skill.cooldown;
        std::fill(m_hit_set_.begin(), m_hit_set_.end(), false);
    }
    advance_attack();
    for (Enemy& enemy : m_enemies_) {
        update_enemy(enemy);
        if (enemy.hit_flash > 0) {
            --enemy.hit_flash;
        }
    }
}

void WorldSim::advance_attack() {
    Player& p = m_player_;
    const SkillDef& s = m_setup_.skill;
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
    const SkillDef& s = m_setup_.skill;
    const auto cos_half =
        static_cast<float>(std::cos(static_cast<double>(s.angle_deg) / 2.0 * kPi / 180.0));
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
        const std::int64_t variance = 950 + static_cast<std::int64_t>(m_combat_rng_.next_bounded(101));
        const bool crit = static_cast<std::int64_t>(m_combat_rng_.next_bounded(1000)) < m_derived_.crit_chance_pm;
        DamageInput in;
        in.atk = m_derived_.atk;
        in.power_pct = s.power_pct;
        in.def_target = enemy.def.def;
        in.lvl_attacker = p.level;
        in.lvl_target = enemy.def.level;
        in.variance_pm = variance;
        in.crit = crit;
        in.crit_mult_pm = m_derived_.crit_mult_pm;
        const std::int64_t amount = damage(in);
        enemy.hp -= amount;
        enemy.hit_flash = kHitFlashTicks;
        m_events_.push_back({enemy.position, amount, crit, false});
        if (enemy.hp <= 0) {
            enemy.hp = 0;
            enemy.state = EnemyState::Dead;
            on_kill(enemy);
        }
    }
}

void WorldSim::on_kill(Enemy& enemy) {
    Player& p = m_player_;
    ++p.kills;
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
    grant_xp(xp_gain(enemy.def.xp, enemy.def.level, p.level));
    m_story_.on_kill(enemy.def.id);
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

void WorldSim::update_enemy(Enemy& enemy) {
    if (enemy.state == EnemyState::Dead) {
        return;
    }
    const BehaviorDef& b = enemy.def.behavior;
    const Player& p = m_player_;
    const float dist = distance(enemy.position.x, enemy.position.y, p.position.x, p.position.y);
    switch (enemy.state) {
        case EnemyState::Idle:
            if (dist <= static_cast<float>(b.aggro_x100) / 100.0F) {
                enemy.state = EnemyState::Chase;
                enemy.state_tick = 0;
            }
            break;
        case EnemyState::Chase:
            if (dist > static_cast<float>(b.leash_x100) / 100.0F) {
                enemy.state = EnemyState::Return;
            } else if (dist <= static_cast<float>(b.attack_range_x100) / 100.0F) {
                enemy.state = EnemyState::Attack;
                enemy.state_tick = 0;
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
    const float step = (static_cast<float>(enemy.def.speed_x100) / 100.0F) * kTickDt;
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

void WorldSim::hurt_player(const Enemy& enemy) {
    Player& p = m_player_;
    const std::int64_t variance = 950 + static_cast<std::int64_t>(m_combat_rng_.next_bounded(101));
    DamageInput in;
    in.atk = enemy.def.atk;
    in.power_pct = 100;
    in.def_target = m_derived_.def;
    in.lvl_attacker = enemy.def.level;
    in.lvl_target = p.level;
    in.variance_pm = variance;
    const std::int64_t amount = damage(in);
    p.hp -= amount;
    p.iframes = kPlayerHitIframes;
    m_events_.push_back({p.position, amount, false, true});
    if (p.hp <= 0) {
        ++p.deaths;
        p.hp = m_derived_.max_hp;
        p.position = m_spawn_;
        p.phase = AttackPhase::None;
        p.phase_tick = 0;
        p.iframes = kRespawnIframes;
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
        s.enemies.push_back({enemy.position, enemy.hp, enemy.state, enemy.state_tick, m_store_ != nullptr, enemy.spawner_x,
                             enemy.spawner_y});
    }
    for (const auto& [spawner, died] : m_cleared_) {
        s.cleared.push_back({spawner.first, spawner.second, died});
    }
    s.explored.assign(m_explored_.begin(), m_explored_.end());
    std::sort(s.explored.begin(), s.explored.end(), [](const auto& a, const auto& b) {  // rows first (spec 12)
        return a.second != b.second ? a.second < b.second : a.first < b.first;
    });
    s.world_ticks = m_world_ticks_;
    s.inventory = m_inventory_;
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
    m_combat_rng_.set_state(s.combat_state, s.combat_inc);
    m_loot_rng_.set_state(s.loot_state, s.loot_inc);
    if (m_store_) {
        m_enemies_.clear();
        for (const SaveEnemy& e : s.enemies) {
            Enemy enemy;
            enemy.def = *m_setup_.stream_enemy;
            enemy.home = {static_cast<float>(e.spawner_x) + 0.5F, static_cast<float>(e.spawner_y) + 0.5F};
            enemy.spawner_x = e.spawner_x;
            enemy.spawner_y = e.spawner_y;
            m_enemies_.push_back(std::move(enemy));
        }
        m_cleared_.clear();
        for (const ClearedSpawner& c : s.cleared) {
            m_cleared_[{c.x, c.y}] = c.died;
        }
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
    m_explored_ = std::set<std::pair<int, int>>(s.explored.begin(), s.explored.end());
    mark_explored();
    m_world_ticks_ = s.world_ticks >= 0 ? s.world_ticks : (m_store_ ? m_store_->params().time.start_tick : 0);
    m_events_.clear();
    return true;
}

Camera WorldSim::camera(float view_w, float view_h) const {
    return {axis_origin(m_player_.position.x, view_w, static_cast<float>(m_map_.width)),
            axis_origin(m_player_.position.y, view_h, static_cast<float>(m_map_.height))};
}

}  // namespace aether
