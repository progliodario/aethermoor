#pragma once

// Player movement and collision. Spec: docs/spec/02-entities-and-movement.md.
// Reference: tools/reference/movement.py. Floating point (float32), compared with a tolerance.

#include <vector>

namespace aether {

inline constexpr float kTickDt = 1.0F / 60.0F;
inline constexpr float kInputDeadzone = 0.15F;
inline constexpr float kPlayerRadius = 0.3F;

struct Vec2 {
    float x = 0.0F;
    float y = 0.0F;
};

struct Circle {
    float x = 0.0F;
    float y = 0.0F;
    float radius = 0.0F;
};

// Dead zone, then clamp to the unit circle.
Vec2 normalize_input(float x, float y);

class CollisionWorld {
public:
    CollisionWorld(int width, int height, std::vector<bool> solid, std::vector<Circle> props);

    bool solid(int tx, int ty) const;  // cells outside the map are solid
    int width() const { return m_width_; }
    int height() const { return m_height_; }

    // Pushes (x, y) out of solid tiles and prop circles (spec: resolve).
    void resolve(float& x, float& y) const;

    // One tick of movement: X axis, resolve, Y axis, resolve.
    void step(Vec2& position, Vec2 direction, float speed_tiles_per_s) const;

private:
    int m_width_;
    int m_height_;
    std::vector<bool> m_solid_;
    std::vector<Circle> m_props_;
};

}  // namespace aether
