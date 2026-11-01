#include "sim/world.hpp"

#include <utility>

namespace aether {

namespace {

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

}  // namespace

WorldSim::WorldSim(TileMap map, Tileset tileset, float speed_tiles_per_s)
    : m_map_(std::move(map)),
      m_tileset_(std::move(tileset)),
      m_collision_(build_collision(m_map_, m_tileset_)),
      m_speed_(speed_tiles_per_s) {
    m_player_.position = {m_map_.spawn_x, m_map_.spawn_y};
    m_collision_.resolve(m_player_.position.x, m_player_.position.y);
}

void WorldSim::tick(float raw_x, float raw_y) {
    const Vec2 direction = normalize_input(raw_x, raw_y);
    const bool moving = direction.x != 0.0F || direction.y != 0.0F;
    m_collision_.step(m_player_.position, direction, m_speed_);
    if (direction.x != 0.0F) {
        m_player_.facing_left = direction.x < 0.0F;
    }
    if (moving != m_player_.moving) {
        m_player_.moving = moving;
        m_player_.clip_tick = 0;
    } else {
        ++m_player_.clip_tick;
    }
}

Camera WorldSim::camera(float view_w, float view_h) const {
    return {axis_origin(m_player_.position.x, view_w, static_cast<float>(m_map_.width)),
            axis_origin(m_player_.position.y, view_h, static_cast<float>(m_map_.height))};
}

}  // namespace aether
