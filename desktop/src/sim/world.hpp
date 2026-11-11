#pragma once

// The world: map, player, enemies, combat and camera. Spec: docs/spec/02, 03 and 05.

#include <functional>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "core/numerics.hpp"
#include "core/rules.hpp"
#include "core/worldgen.hpp"
#include "sim/chunk_store.hpp"
#include "sim/combat.hpp"
#include "sim/movement.hpp"
#include "sim/tilemap.hpp"

namespace aether {

struct Player {
    Vec2 position;
    bool moving = false;
    bool facing_left = false;
    int clip_tick = 0;  // ticks since the current clip started

    // Combat (only meaningful when combat is enabled).
    Vec2 facing{1.0F, 0.0F};
    std::int64_t hp = 1;
    std::int64_t level = 1;
    std::int64_t xp = 0;
    int deaths = 0;
    int kills = 0;
    int iframes = 0;
    int cooldown = 0;
    AttackPhase phase = AttackPhase::None;
    int phase_tick = 0;
    std::int64_t mp_u = 0;      // mana in units of 1/6000 of a point (spec 05, "Mana"); not saved
    bool using_strike = false;  // the swing in progress is the power strike; not saved
    int death_save_cd = 0;      // ticks until the death save is ready again (spec 18); not saved
    int dodge_ticks = 0;        // ticks of the dodge roll left (spec 05); not saved
    int dodge_cooldown = 0;     // ticks until the next roll; not saved
    int parry_ticks = 0;        // ticks of the parry window left (spec 05, "Parry"); not saved
    int parry_cooldown = 0;     // ticks until the next parry; not saved
    int burn = 0;               // status effects on the player (spec 05), ticks left; not saved
    int burn_clock = 0;
    int chill = 0;
    int stun = 0;
    int weaken = 0;
    int fortify = 0;  // a meal that fortifies (spec 06): ticks left, and the attack it adds; not saved
    std::int64_t fortify_pct = 0;
    int ward = 0;  // a brew that wards (spec 06): ticks left, and the defense it adds; not saved
    std::int64_t ward_pct = 0;
    int regen = 0;  // a dish that heals over time (spec 06): ticks left, and the health every second; not saved
    std::int64_t regen_amount = 0;
    int haste = 0;  // a brew of haste (spec 06): ticks left, and the speed of walking it adds; not saved
    std::int64_t haste_pct = 0;
    Vec2 dodge_dir{1.0F, 0.0F};
};

struct Enemy {
    EnemyDef def;
    Vec2 position;
    Vec2 home;
    std::int64_t hp = 0;
    EnemyState state = EnemyState::Idle;
    int state_tick = 0;
    int hit_flash = 0;  // presentation only
    // Status effects (spec 05): ticks left; not saved.
    int burn = 0;
    int burn_clock = 0;
    int chill = 0;
    int weaken = 0;
    int stun = 0;
    std::int64_t stagger = 0;  // the stagger bar (spec 05, "Stagger"); not saved
    bool marked = false;       // the last creature the player hit: the companion goes for it first (spec 10)
    int broken = 0;            // ticks left of being broken: stunned, and hits do more; not saved
    int spawner_x = 0;         // streamed worlds: the spawner tile this enemy belongs to
    int spawner_y = 0;
    float radius() const { return static_cast<float>(def.radius_x100) / 100.0F; }
};

// Something a client may want to show (numbers floating up from a hit); not part of the contract.
struct DamageEvent {
    Vec2 position;
    std::int64_t amount = 0;
    bool crit = false;
    bool on_player = false;
    bool weak = false;  // the element multiplier of the hit was above 1000 (spec 05, "Elements")
};

// Something that made a sound (presentation only, like DamageEvent): `kind` is aggro, attack, hit, hurt or die,
// `family` the voices of the creature (spec 14).
struct SimCue {
    std::string kind;
    std::string family;
    Vec2 position;
    bool crit = false;
    bool weak = false;
};

// Everything that changes while playing; see docs/spec/12-save-format.md.
struct SaveEnemy {
    Vec2 position;
    std::int64_t hp = 0;
    EnemyState state = EnemyState::Idle;
    int state_tick = 0;
    bool has_spawner = false;  // streamed worlds only
    int spawner_x = 0;
    int spawner_y = 0;
};

struct ClearedSpawner {
    int x = 0;
    int y = 0;
    std::int64_t died = 0;  // world tick of the death
};

struct SaveState {
    Vec2 position;
    Vec2 facing{1.0F, 0.0F};
    bool facing_left = false;
    bool moving = false;
    int clip_tick = 0;
    std::int64_t hp = 1;
    std::int64_t level = 1;
    std::int64_t xp = 0;
    int deaths = 0;
    int kills = 0;
    int iframes = 0;
    int cooldown = 0;
    AttackPhase phase = AttackPhase::None;
    int phase_tick = 0;
    std::vector<bool> hit_set;
    std::uint64_t combat_state = 0;
    std::uint64_t combat_inc = 0;
    std::uint64_t loot_state = 0;
    std::uint64_t loot_inc = 0;
    std::vector<SaveEnemy> enemies;
    std::vector<ClearedSpawner> cleared;        // streamed worlds: spawners whose enemy was killed
    std::vector<std::pair<int, int>> explored;  // streamed worlds: explored world map cells
    std::vector<std::pair<int, int>>
        stones;                     // streamed worlds: tiles of the Threshold Stones that were used, in order (spec 09)
    std::int64_t world_ticks = -1;  // -1: not in the save (a new game starts at the world's start tick)
    bool has_companion = false;     // the companion of the protagonist (spec 10): where it is and its cooldown
    float companion_x = 0.0F;
    float companion_y = 0.0F;
    int companion_cooldown = 0;
    bool companion_stay = false;          // told to stay (spec 10, "Commands")
    int companion_bond = 0;               // the creatures it has killed (spec 10, "Bond")
    std::map<std::string, int> bestiary;  // creature ID -> how many were killed (spec 11)
    std::map<std::string, int> counters;  // gathered, crafted, parried (spec 11)
    std::map<std::string, int> talents;   // talent ID -> rank (spec 11, "Talents")
    std::map<std::string, std::int64_t> inventory;
    std::string equipped_weapon;  // spec 06
    std::string equipped_armor;
    StoryState story;
};

// A streamed world: its parameters and seed (spec 09, "Streaming").
struct StreamConfig {
    WorldParams params;
    std::uint64_t seed = 0;
};

struct Camera {
    float x = 0.0F;  // top-left of the view, in tiles
    float y = 0.0F;
};

class WorldSim : private StoryHost {
public:
    // `speed_tiles_per_s` is used while combat is disabled; with combat the speed comes from the derived stats.
    // With `stream` the map only gives the size, the spawn and the NPCs; tiles, props and enemies come from the chunks.
    WorldSim(TileMap map, Tileset tileset, float speed_tiles_per_s, CombatSetup combat = {},
             std::optional<StreamConfig> stream = std::nullopt);

    // One fixed tick (1/60 s) with the raw movement input and the attack input of this tick.
    void tick(float raw_x, float raw_y, bool attack = false, bool dodge = false, bool strike = false,
              bool parry = false);
    // The mana in points (the floor of mp_u / 6000), and whether the protagonist has a power strike.
    std::int64_t mp() const { return m_player_.mp_u / 6000; }
    bool has_strike() const { return m_setup_.strike.enabled; }

    const Player& player() const { return m_player_; }
    const TileMap& map() const { return m_map_; }
    const Tileset& tileset() const { return m_tileset_; }
    const CollisionWorld& collision() const { return m_collision_; }
    const std::vector<Enemy>& enemies() const { return m_enemies_; }
    const std::map<std::string, std::int64_t>& inventory() const { return m_inventory_; }
    // The bestiary (spec 11): creature ID -> kills, and the IDs of the titles earned, in the order of the data.
    const std::map<std::string, int>& bestiary() const { return m_bestiary_; }
    std::vector<std::string> earned_titles() const;
    // How far the player is toward a title: the number its kind counts (spec 11, "Titles").
    std::int64_t title_progress(const TitleDef& title) const;
    // The percent that the earned titles add to the attack of the player's hits (spec 11, "Titles with effects").
    std::int64_t title_attack_pct() const;
    // What the earned titles add (spec 11): "gather", "craft", "parry" (window ticks) or "xp" (percent).
    std::int64_t title_bonus(const std::string& what) const;
    const std::map<std::string, int>& counters() const { return m_counters_; }
    // Talents (spec 11): the ranks learned, the points left, and spending one point on a rank (false when refused).
    const std::map<std::string, int>& talents() const { return m_talents_; }
    int talent_points() const;
    bool learn_talent(const std::string& talent_id);
    const std::vector<TitleDef>& titles() const { return m_setup_.titles; }
    const DerivedStats& derived() const { return m_derived_; }
    bool streamed() const { return m_store_ != nullptr; }
    std::int64_t world_ticks() const { return m_world_ticks_; }
    // Explored world map cells (spec 09); empty on a fixed map.
    const std::set<std::pair<int, int>>& explored() const { return m_explored_; }
    // Day, light and weather of the streamed world now (spec 08); nullopt on a fixed map.
    std::optional<TimeSample> time() const;
    const ChunkStore* chunks() const { return m_store_.get(); }
    // The gid at the tile on whichever map is played, 0 when unknown.
    int gid_at(int x, int y) const;
    // Calls `fn` for every prop inside the rectangle (in tiles).
    void for_each_prop(float x0, float y0, float x1, float y1, const std::function<void(const Prop&)>& fn) const;
    const CombatSetup& combat() const { return m_setup_; }
    Story& story() { return m_story_; }
    // Puts the player at (x, y) in tiles, loading the chunks around (developer option --start, later the Threshold
    // Stones).
    void teleport(float x, float y);
    // The guild board (spec 07, "Guild"): open from a clerk's dialogue; each call returns false, changing nothing, when
    // refused.
    struct Board {
        Settlement settlement;
        std::int64_t day = 1;
        std::vector<Offer> offers;
    };
    const Board* board() const { return m_board_ ? &*m_board_ : nullptr; }
    void close_board() { m_board_.reset(); }
    bool accept_offer(int slot);
    int guild_rank() const;
    // Threshold Stones (spec 09): `stone_near` is the position of the stone prop the player can use, `use_stone` wakes
    // it, restores health and opens the list of the stones that were used; `travel_to` goes to one of them.
    struct StoneStop {
        int x = 0;
        int y = 0;
        std::string place;   // name of the settlement
        std::string region;  // $i18n: key of the region
    };
    struct Travel {
        std::vector<StoneStop> stops;
        int here = -1;       // index of the stone being used
        bool fresh = false;  // the stone was woken just now
    };
    std::optional<std::pair<float, float>> stone_near() const;
    bool use_stone();
    bool travel_to(int index);
    const Travel* travel() const { return m_travel_ ? &*m_travel_ : nullptr; }
    void close_travel() { m_travel_.reset(); }
    const std::vector<std::pair<int, int>>& stones() const { return m_stones_; }
    // Equipment and shops (spec 06): each returns false, changing nothing, when refused.
    bool equip(const std::string& item_id);
    // Puts items into the bag (the heirloom of a past life, spec 11); a quantity below 1 does nothing.
    void give_item(const std::string& item_id, std::int64_t qty) {
        if (qty > 0 && !item_id.empty()) {
            m_inventory_[item_id] += qty;
        }
    }
    bool buy(const std::string& item_id);
    bool sell(const std::string& item_id);
    void close_shop() { m_shop_.reset(); }
    // The `open_shop` dialogue effect, callable on its own (scenarios).
    void open_shop_for_test() { open_shop(); }
    // The shop that is open now, or nullptr.
    const ShopDef* shop() const { return m_shop_ ? &*m_shop_ : nullptr; }
    const std::string& equipped_weapon() const { return m_equipped_weapon_; }
    const std::string& equipped_armor() const { return m_equipped_armor_; }
    // Price of buying / selling an item in the open shop.
    std::int64_t buy_price(const std::string& item_id) const;
    std::int64_t sell_price(const std::string& item_id) const;
    // Uses one item of the inventory (spec 06). Returns false, changing nothing, when it is refused.
    bool use_item(const std::string& item_id);
    // Gathering (spec 06, "Gathering"): the items found at the nearest prop in reach that can be gathered from, which
    // are added to the bag.
    struct GatherResult {
        bool node = false;  // there was something to gather from
        std::string sound;  // plant, wood, stone or water
        std::vector<std::pair<std::string, std::int64_t>> items;
    };
    GatherResult gather();
    // Whether a prop of that art is within 2 tiles (plus its radius); an empty art is everywhere (spec 06, "Stations").
    bool near_station(const std::string& art) const;
    // Where the prop that `gather` would gather from is, if there is one (for the hint of the interface).
    std::optional<std::pair<float, float>> gather_near() const;
    // Makes a recipe from the bag (spec 06, "Crafting"). Returns false, changing nothing, when it is refused.
    bool craft(const std::string& recipe_id);
    // The companion (spec 10): where it is, or nullptr when the protagonist has none.
    const Vec2* companion_position() const { return m_setup_.companion ? &m_companion_pos_ : nullptr; }
    // Tells the companion to stay where it is, or to follow again (spec 10, "Commands"); false when there is none.
    bool companion_stay();
    bool companion_staying() const { return m_companion_stay_; }
    int companion_bond() const { return m_companion_bond_; }
    const Story& story() const { return m_story_; }

    SaveState capture() const;
    // Overwrites the mutable state. On a mismatch with the loaded data returns false, sets `error` and changes nothing.
    bool restore(const SaveState& state, std::string& error);

    // Events produced since the last call (damage numbers).
    std::vector<DamageEvent> take_events();
    std::vector<SimCue> take_cues();

    // View of `view_w` x `view_h` tiles centered on the player and clamped to the map.
    Camera camera(float view_w, float view_h) const;

private:
    void advance_attack();
    void do_hits();
    void on_kill(Enemy& enemy);
    // The element multiplier of a hit of the equipped weapon against `target` (spec 05, "Elements").
    std::int64_t element_multiplier(const EnemyDef& target) const;
    std::string hit_element() const;  // the element of the hit in progress: the skill's, or the weapon's
    // The roll for the status effect of the equipped weapon after a hit that left `enemy` alive (spec 05, "Status
    // effects").
    void apply_status(Enemy& enemy);
    // The behavior of a creature that is not stunned.
    void behave_enemy(Enemy& enemy);
    void update_enemy(Enemy& enemy);
    void move_enemy(Enemy& enemy, float target_x, float target_y);
    void hurt_player(Enemy& enemy);
    void recompute_derived();
    void sync_window();
    void mark_explored();
    void add_chunk_enemies(int cx, int cy);
    void add_chunk_people(int cx, int cy);
    // Rebuilds the dynamic NPCs of the 5 x 5 chunks around chunk (cx, cy) for the time of day (spec 08, Routines).
    void refresh_people(int cx, int cy);
    int time_of_day_pm() const;
    void rebuild_npc_circles();

    // StoryHost
    void grant_xp(std::int64_t amount) override;
    std::map<std::string, std::int64_t>& host_inventory() override { return m_inventory_; }
    std::int64_t level() const override { return m_player_.level; }
    float player_x() const override { return m_player_.position.x; }
    float player_y() const override { return m_player_.position.y; }
    void open_shop() override;
    void open_board() override;
    void heal_full() override { m_player_.hp = m_derived_.max_hp; }
    std::string season_id() const override;
    int tod_pm() const override { return m_store_ ? time_of_day_pm() : 0; }
    // The enemy the spawner on a tile makes (spec 09, "Fauna").
    const EnemyDef& stream_enemy_at(int x, int y) const;

    TileMap m_map_;
    Tileset m_tileset_;
    std::unique_ptr<ChunkStore> m_store_;
    CollisionWorld m_collision_;
    float m_speed_;
    CombatSetup m_setup_;
    Pcg32 m_combat_rng_;
    Pcg32 m_loot_rng_;
    Player m_player_;
    Vec2 m_spawn_;
    DerivedStats m_derived_;
    std::vector<Enemy> m_enemies_;
    std::vector<bool> m_hit_set_;
    std::map<std::string, std::int64_t> m_inventory_;
    std::vector<DamageEvent> m_events_;
    std::vector<SimCue> m_cues_;
    Vec2 m_companion_pos_;
    int m_companion_cooldown_ = 0;
    bool m_companion_stay_ = false;
    int m_companion_bond_ = 0;
    int m_companion_care_ = 0;  // ticks since it last tended the player (spec 10, "Care"); not saved
    void update_companion();
    std::map<std::pair<int, int>, std::pair<std::int64_t, int>>
        m_gathered_;  // (x100, y100) -> (tick it grows back, times); not saved
    Story m_story_;
    bool m_window_valid_ = false;
    int m_window_x_ = 0;  // chunk of the player the enemies were synchronized for
    int m_window_y_ = 0;
    std::map<std::pair<int, int>, std::int64_t> m_cleared_;  // spawner tile -> world tick of the death
    std::int64_t m_world_ticks_ = 0;
    std::string m_equipped_weapon_;
    std::string m_equipped_armor_;
    std::optional<ShopDef> m_shop_;
    std::optional<Board> m_board_;
    std::vector<std::pair<int, int>> m_stones_;
    std::map<std::string, int> m_bestiary_;
    std::map<std::string, int> m_counters_;
    std::map<std::string, int> m_talents_;
    std::optional<Travel> m_travel_;
    int m_routine_tod_ = -1;             // time of day (permille) the dynamic NPCs were built for
    std::vector<NpcDef> m_npcs_;         // settlement people of the active window (spec 09)
    std::vector<Circle> m_npc_circles_;  // their collision circles
    std::set<std::pair<int, int>> m_explored_;
};

}  // namespace aether
