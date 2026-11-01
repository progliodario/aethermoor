#pragma once

// Tile maps (Tiled TMJ subset) and tilesets. Spec: docs/spec/02-entities-and-movement.md.

#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace aether {

struct TileDef {
    std::string art;
    bool solid = false;
};

struct Tileset {
    std::string id;
    std::map<int, TileDef> tiles;  // by gid
};

struct Prop {
    std::string art;
    float x = 0.0F;  // feet position, in tiles
    float y = 0.0F;
    float radius = 0.3F;
};

struct TileMap {
    int width = 0;
    int height = 0;
    std::string tileset_id;
    std::vector<int> ground;  // width * height gids, row-major
    float spawn_x = 0.0F;
    float spawn_y = 0.0F;
    std::vector<Prop> props;

    // gid at the cell, 0 when out of range.
    int gid_at(int x, int y) const;
};

std::optional<Tileset> parse_tileset(std::string_view json_text, std::string& error);
std::optional<TileMap> parse_tilemap(std::string_view tmj_text, std::string& error);

}  // namespace aether
