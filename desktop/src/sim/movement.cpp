#include "sim/movement.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <utility>

namespace aether {

namespace {

float clampf(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }

}  // namespace

Vec2 normalize_input(float x, float y) {
    const float length = std::sqrt(x * x + y * y);
    if (length < kInputDeadzone) {
        return {0.0F, 0.0F};
    }
    if (length > 1.0F) {
        return {x / length, y / length};
    }
    return {x, y};
}

CollisionWorld::CollisionWorld(int width, int height, std::vector<bool> solid, std::vector<Circle> props)
    : m_width_(width), m_height_(height), m_solid_(std::move(solid)), m_props_(std::move(props)) {}

bool CollisionWorld::solid(int tx, int ty) const {
    if (tx < 0 || ty < 0 || tx >= m_width_ || ty >= m_height_) {
        return true;
    }
    return m_solid_[static_cast<std::size_t>(ty) * static_cast<std::size_t>(m_width_) +
                    static_cast<std::size_t>(tx)];
}

void CollisionWorld::resolve(float& x, float& y, float radius) const {
    const float r = radius;
    for (int iteration = 0; iteration < 4; ++iteration) {
        bool moved = false;
        const int ty0 = static_cast<int>(std::floor(y - r));
        const int ty1 = static_cast<int>(std::floor(y + r));
        const int tx0 = static_cast<int>(std::floor(x - r));
        const int tx1 = static_cast<int>(std::floor(x + r));
        for (int ty = ty0; ty <= ty1; ++ty) {
            for (int tx = tx0; tx <= tx1; ++tx) {
                if (!solid(tx, ty)) {
                    continue;
                }
                const float cx = clampf(x, static_cast<float>(tx), static_cast<float>(tx + 1));
                const float cy = clampf(y, static_cast<float>(ty), static_cast<float>(ty + 1));
                const float dx = x - cx;
                const float dy = y - cy;
                const float d2 = dx * dx + dy * dy;
                if (d2 < r * r) {
                    if (d2 > 0.0F) {
                        const float d = std::sqrt(d2);
                        const float k = (r - d) / d;
                        x += dx * k;
                        y += dy * k;
                    } else {
                        const float left = x - static_cast<float>(tx);
                        const float right = static_cast<float>(tx + 1) - x;
                        const float top = y - static_cast<float>(ty);
                        const float bottom = static_cast<float>(ty + 1) - y;
                        const float m = std::min(std::min(left, right), std::min(top, bottom));
                        if (m == left) {
                            x = static_cast<float>(tx) - r;
                        } else if (m == right) {
                            x = static_cast<float>(tx + 1) + r;
                        } else if (m == top) {
                            y = static_cast<float>(ty) - r;
                        } else {
                            y = static_cast<float>(ty + 1) + r;
                        }
                    }
                    moved = true;
                }
            }
        }
        for (const Circle& prop : m_props_) {
            const float dx = x - prop.x;
            const float dy = y - prop.y;
            const float d2 = dx * dx + dy * dy;
            const float md = r + prop.radius;
            if (d2 < md * md) {
                if (d2 > 0.0F) {
                    const float d = std::sqrt(d2);
                    const float k = (md - d) / d;
                    x += dx * k;
                    y += dy * k;
                } else {
                    x = prop.x + md;
                }
                moved = true;
            }
        }
        if (!moved) {
            break;
        }
    }
}

void CollisionWorld::step(Vec2& position, Vec2 direction, float speed_tiles_per_s, float radius) const {
    position.x += direction.x * speed_tiles_per_s * kTickDt;
    resolve(position.x, position.y, radius);
    position.y += direction.y * speed_tiles_per_s * kTickDt;
    resolve(position.x, position.y, radius);
}

}  // namespace aether
