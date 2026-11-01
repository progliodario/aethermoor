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
};

struct Enemy {
    EnemyDef def;
    Vec2 position;
    Vec2 home;
    std::int64_t hp = 0;
    EnemyState state = EnemyState::Idle;
    int state_tick = 0;
    int hit_flash = 0;  // presentation only
    int spawner_x = 0;  // streamed worlds: the spawner tile this enemy belongs to
    int spawner_y = 0;
    float radius() const { return static_cast<float>(def.radius_x100) / 100.0F; }
};

// Something a client may want to show (numbers floating up from a hit); not part of the contract.
struct DamageEvent {
    Vec2 position;
    std::int64_t amount = 0;
    bool crit = false;
    bool on_player = false;
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
    std::vector<ClearedSpawner> cleared;  // streamed worlds: spawners whose enemy was killed
    std::vector<std::pair<int, int>> explored;  // streamed worlds: explored world map cells
    std::int64_t world_ticks = -1;  // -1: not in the save (a new game starts at the world's start tick)
    std::map<std::string, std::int64_t> inventory;
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
    void tick(float raw_x, float raw_y, bool attack = false);

    const Player& player() const { return m_player_; }
    const TileMap& map() const { return m_map_; }
    const Tileset& tileset() const { return m_tileset_; }
    const CollisionWorld& collision() const { return m_collision_; }
    const std::vector<Enemy>& enemies() const { return m_enemies_; }
    const std::map<std::string, std::int64_t>& inventory() const { return m_inventory_; }
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
    // Uses one item of the inventory (spec 06). Returns false, changing nothing, when it is refused.
    bool use_item(const std::string& item_id);
    const Story& story() const { return m_story_; }

    SaveState capture() const;
    // Overwrites the mutable state. On a mismatch with the loaded data returns false, sets `error` and changes nothing.
    bool restore(const SaveState& state, std::string& error);

    // Events produced since the last call (damage numbers).
    std::vector<DamageEvent> take_events();

    // View of `view_w` x `view_h` tiles centered on the player and clamped to the map.
    Camera camera(float view_w, float view_h) const;

private:
    void advance_attack();
    void do_hits();
    void on_kill(Enemy& enemy);
    void update_enemy(Enemy& enemy);
    void move_enemy(Enemy& enemy, float target_x, float target_y);
    void hurt_player(const Enemy& enemy);
    void recompute_derived();
    void sync_window();
    void mark_explored();
    void add_chunk_enemies(int cx, int cy);

    // StoryHost
    void grant_xp(std::int64_t amount) override;
    std::map<std::string, std::int64_t>& host_inventory() override { return m_inventory_; }
    std::int64_t level() const override { return m_player_.level; }
    float player_x() const override { return m_player_.position.x; }
    float player_y() const override { return m_player_.position.y; }

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
    Story m_story_;
    bool m_window_valid_ = false;
    int m_window_x_ = 0;  // chunk of the player the enemies were synchronized for
    int m_window_y_ = 0;
    std::map<std::pair<int, int>, std::int64_t> m_cleared_;  // spawner tile -> world tick of the death
    std::int64_t m_world_ticks_ = 0;
    std::set<std::pair<int, int>> m_explored_;
};

}  // namespace aether
