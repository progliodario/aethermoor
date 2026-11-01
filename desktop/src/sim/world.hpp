#pragma once

// The world: map, player, enemies, combat and camera. Spec: docs/spec/02, 03 and 05.

#include <map>
#include <string>
#include <vector>

#include "core/numerics.hpp"
#include "core/rules.hpp"
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
    float radius() const { return static_cast<float>(def.radius_x100) / 100.0F; }
};

// Something a client may want to show (numbers floating up from a hit); not part of the contract.
struct DamageEvent {
    Vec2 position;
    std::int64_t amount = 0;
    bool crit = false;
    bool on_player = false;
};

struct Camera {
    float x = 0.0F;  // top-left of the view, in tiles
    float y = 0.0F;
};

class WorldSim : private StoryHost {
public:
    // `speed_tiles_per_s` is used while combat is disabled; with combat the speed comes from the derived stats.
    WorldSim(TileMap map, Tileset tileset, float speed_tiles_per_s, CombatSetup combat = {});

    // One fixed tick (1/60 s) with the raw movement input and the attack input of this tick.
    void tick(float raw_x, float raw_y, bool attack = false);

    const Player& player() const { return m_player_; }
    const TileMap& map() const { return m_map_; }
    const Tileset& tileset() const { return m_tileset_; }
    const CollisionWorld& collision() const { return m_collision_; }
    const std::vector<Enemy>& enemies() const { return m_enemies_; }
    const std::map<std::string, std::int64_t>& inventory() const { return m_inventory_; }
    const DerivedStats& derived() const { return m_derived_; }
    const CombatSetup& combat() const { return m_setup_; }
    Story& story() { return m_story_; }
    const Story& story() const { return m_story_; }

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

    // StoryHost
    void grant_xp(std::int64_t amount) override;
    std::map<std::string, std::int64_t>& host_inventory() override { return m_inventory_; }
    std::int64_t level() const override { return m_player_.level; }
    float player_x() const override { return m_player_.position.x; }
    float player_y() const override { return m_player_.position.y; }

    TileMap m_map_;
    Tileset m_tileset_;
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
};

}  // namespace aether
