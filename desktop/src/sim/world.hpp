#pragma once

// The M2 world: map, player, animation state and camera. Spec: docs/spec/02 and docs/spec/03.

#include "sim/movement.hpp"
#include "sim/tilemap.hpp"

namespace aether {

struct Player {
    Vec2 position;
    bool moving = false;
    bool facing_left = false;
    int clip_tick = 0;  // ticks since the current clip started
};

struct Camera {
    float x = 0.0F;  // top-left of the view, in tiles
    float y = 0.0F;
};

class WorldSim {
public:
    WorldSim(TileMap map, Tileset tileset, float speed_tiles_per_s);

    // One fixed tick (1/60 s) with the raw movement input of this tick.
    void tick(float raw_x, float raw_y);

    const Player& player() const { return m_player_; }
    const TileMap& map() const { return m_map_; }
    const Tileset& tileset() const { return m_tileset_; }
    const CollisionWorld& collision() const { return m_collision_; }

    // View of `view_w` x `view_h` tiles centered on the player and clamped to the map.
    Camera camera(float view_w, float view_h) const;

private:
    TileMap m_map_;
    Tileset m_tileset_;
    CollisionWorld m_collision_;
    float m_speed_;
    Player m_player_;
};

}  // namespace aether
