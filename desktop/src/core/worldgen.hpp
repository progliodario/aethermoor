#pragma once

// World generation. Spec: docs/spec/09-worldgen.md. Reference: tools/reference/worldgen.py.
// Integer arithmetic only: no floating point in this module.

#include <cstdint>
#include <map>
#include <string>
#include <utility>
#include <vector>

namespace aether {

struct NoiseSpec {
    int salt = 0;
    int scale = 64;
    int octaves = 4;
};

struct PropOption {
    std::string art;
    int radius_x100 = 30;
    int per_mille = 0;
};

struct WorldNpc {
    std::string key;
    std::string dialogue;
    std::string variant;
    int dx = 0;
    int dy = 0;
};

struct WorldParams {
    std::string id;
    int width = 0;
    int height = 0;
    int border = 0;
    int spawn_clear_radius = 0;
    NoiseSpec elevation;
    NoiseSpec moisture;
    NoiseSpec temperature;

    int water = 0;
    int beach = 0;
    int mountain = 0;
    int snow = 0;
    int desert_heat = 0;
    int desert_dry = 0;
    int forest_wet = 0;

    int tile_water = 0;
    int tile_beach = 0;
    int tile_desert = 0;
    int tile_snow = 0;
    int tile_mountain = 0;
    int tile_forest = 0;
    std::vector<int> tiles_plains;

    std::map<std::string, std::vector<PropOption>> props;  // by biome name

    std::string spawner_enemy;
    std::vector<std::string> spawner_biomes;
    int spawner_min_distance = 0;
    int spawner_per_10000 = 0;

    std::vector<WorldNpc> npcs;
};

struct GenProp {
    std::string art;
    int radius_x100 = 30;
    int x256 = 0;  // feet position in 1/256 tile
    int y256 = 0;
};

struct GenNpc {
    std::string key;
    std::string dialogue;
    std::string variant;
    int x256 = 0;
    int y256 = 0;
};

struct GeneratedWorld {
    int width = 0;
    int height = 0;
    std::vector<int> tiles;  // row-major gids
    std::vector<GenProp> props;
    std::vector<std::pair<int, int>> spawners;
    int spawn_x256 = 0;
    int spawn_y256 = 0;
    std::vector<GenNpc> npcs;
};

GeneratedWorld generate_world(std::uint64_t seed, const WorldParams& params);

// Digests used by the conformance vectors.
std::uint64_t digest_tile_row(const std::vector<int>& tiles, int width, int row);
std::uint64_t digest_props(const std::vector<GenProp>& props);
std::uint64_t digest_spawners(const std::vector<std::pair<int, int>>& spawners);

}  // namespace aether
