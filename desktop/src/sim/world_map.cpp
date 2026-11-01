#include "sim/world_map.hpp"

namespace aether {

TileMap make_tilemap(const GeneratedWorld& world, const WorldParams& params) {
    TileMap map;
    map.width = world.width;
    map.height = world.height;
    map.tileset_id = "base:tileset/overworld";
    map.ground = world.tiles;
    map.spawn_x = static_cast<float>(world.spawn_x256) / 256.0F;
    map.spawn_y = static_cast<float>(world.spawn_y256) / 256.0F;
    map.props.reserve(world.props.size());
    for (const GenProp& p : world.props) {
        map.props.push_back({p.art, static_cast<float>(p.x256) / 256.0F, static_cast<float>(p.y256) / 256.0F,
                             static_cast<float>(p.radius_x100) / 100.0F});
    }
    for (const auto& s : world.spawners) {
        map.spawners.push_back({params.spawner_enemy, static_cast<float>(s.first) + 0.5F, static_cast<float>(s.second) + 0.5F});
    }
    for (const GenNpc& n : world.npcs) {
        map.npcs.push_back({n.key, n.dialogue, n.variant, static_cast<float>(n.x256) / 256.0F, static_cast<float>(n.y256) / 256.0F});
    }
    return map;
}

}  // namespace aether
