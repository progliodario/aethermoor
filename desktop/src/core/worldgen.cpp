#include "core/worldgen.hpp"

#include <algorithm>
#include <utility>

#include "core/numerics.hpp"

namespace aether {

namespace {

enum class Biome { Water, Beach, Mountain, Snow, Desert, Forest, Plains };

const char* biome_name(Biome biome) {
    switch (biome) {
        case Biome::Water:
            return "water";
        case Biome::Beach:
            return "beach";
        case Biome::Mountain:
            return "mountain";
        case Biome::Snow:
            return "snow";
        case Biome::Desert:
            return "desert";
        case Biome::Forest:
            return "forest";
        case Biome::Plains:
            return "plains";
    }
    return "plains";
}

std::int64_t coord(std::int64_t tile, int scale) { return (tile << 16) / scale; }

std::int64_t field(std::uint64_t seed, const NoiseSpec& spec, int x, int y) {
    const std::uint64_t salted = hash64(seed, spec.salt);
    return fbm2(salted, coord(x, spec.scale), coord(y, spec.scale), spec.octaves);
}

bool in_clearing(const WorldParams& p, int x, int y) {
    const std::int64_t dx = x - p.width / 2;
    const std::int64_t dy = y - p.height / 2;
    return dx * dx + dy * dy < static_cast<std::int64_t>(p.spawn_clear_radius) * p.spawn_clear_radius;
}

Biome biome_at(std::uint64_t seed, const WorldParams& p, int x, int y) {
    if (x < p.border || y < p.border || x >= p.width - p.border || y >= p.height - p.border) {
        return Biome::Water;
    }
    if (in_clearing(p, x, y)) {
        return Biome::Plains;
    }
    const std::int64_t e = field(seed, p.elevation, x, y);
    if (e < p.water) {
        return Biome::Water;
    }
    if (e < p.beach) {
        return Biome::Beach;
    }
    if (e >= p.mountain) {
        return Biome::Mountain;
    }
    const std::int64_t temperature = field(seed, p.temperature, x, y);
    if (temperature < p.snow) {
        return Biome::Snow;
    }
    const std::int64_t moisture = field(seed, p.moisture, x, y);
    if (temperature >= p.desert_heat && moisture < p.desert_dry) {
        return Biome::Desert;
    }
    if (moisture >= p.forest_wet) {
        return Biome::Forest;
    }
    return Biome::Plains;
}

enum class Overlay { None, River, Ford, Road, Bridge };

// Spec 09, "Rivers and roads": only on land tiles outside the spawn clearing.
Overlay overlay_at(std::uint64_t seed, const WorldParams& p, Biome biome, int x, int y) {
    if (biome == Biome::Water || biome == Biome::Mountain || in_clearing(p, x, y)) {
        return Overlay::None;
    }
    constexpr std::int64_t kMid = 32768;
    const auto distance = [](std::int64_t value) { return value < kMid ? kMid - value : value - kMid; };
    const bool is_river = distance(field(seed, p.river, x, y)) < p.river_half_width;
    const bool is_road = distance(field(seed, p.road, x, y)) < p.road_half_width;
    if (is_river) {
        if (is_road) {
            return Overlay::Bridge;
        }
        const std::int64_t scale = p.ford_scale;
        const bool ford = noise2(hash64(seed, p.ford_salt), (static_cast<std::int64_t>(x) << 16) / scale,
                                 (static_cast<std::int64_t>(y) << 16) / scale) >= p.ford_min;
        return ford ? Overlay::Ford : Overlay::River;
    }
    return is_road ? Overlay::Road : Overlay::None;
}

int gid_for(std::uint64_t seed, const WorldParams& p, Biome biome, int x, int y, Overlay overlay) {
    switch (overlay) {
        case Overlay::River:
            return p.tile_river;
        case Overlay::Ford:
            return p.tile_ford;
        case Overlay::Road:
            return p.tile_road;
        case Overlay::Bridge:
            return p.tile_bridge;
        case Overlay::None:
            break;
    }
    switch (biome) {
        case Biome::Water:
            return p.tile_water;
        case Biome::Beach:
            return p.tile_beach;
        case Biome::Mountain:
            return p.tile_mountain;
        case Biome::Snow:
            return p.tile_snow;
        case Biome::Desert:
            return p.tile_desert;
        case Biome::Forest:
            return p.tile_forest;
        case Biome::Plains:
            return p.tiles_plains[(hash64(seed, x, y, 5) >> 40) % p.tiles_plains.size()];
    }
    return p.tile_water;
}

bool prop_at(std::uint64_t seed, const WorldParams& p, Biome biome, int x, int y, GenProp& out) {
    const auto options = p.props.find(biome_name(biome));
    if (options == p.props.end() || options->second.empty()) {
        return false;
    }
    const std::uint64_t h = hash64(seed, x, y, 7);
    const std::uint64_t roll = (h >> 20) % 1000;
    std::uint64_t total = 0;
    for (const PropOption& option : options->second) {
        total += static_cast<std::uint64_t>(option.per_mille);
        if (roll < total) {
            out.art = option.art;
            out.radius_x100 = option.radius_x100;
            out.x256 = x * 256 + 48 + static_cast<int>((h >> 8) & 0x7F);
            out.y256 = y * 256 + 128 + static_cast<int>((h >> 16) & 0x7F);
            return true;
        }
    }
    return false;
}

bool spawner_at(std::uint64_t seed, const WorldParams& p, Biome biome, int x, int y) {
    const auto& biomes = p.spawner_biomes;
    if (std::find(biomes.begin(), biomes.end(), biome_name(biome)) == biomes.end()) {
        return false;
    }
    const std::int64_t dx = x - p.width / 2;
    const std::int64_t dy = y - p.height / 2;
    if (dx * dx + dy * dy < static_cast<std::int64_t>(p.spawner_min_distance) * p.spawner_min_distance) {
        return false;
    }
    return (hash64(seed, x, y, 11) >> 20) % 10000 < static_cast<std::uint64_t>(p.spawner_per_10000);
}

}  // namespace

GeneratedWorld generate_world(std::uint64_t seed, const WorldParams& p) {
    GeneratedWorld world;
    world.width = p.width;
    world.height = p.height;
    world.tiles.reserve(static_cast<std::size_t>(p.width) * static_cast<std::size_t>(p.height));
    for (int y = 0; y < p.height; ++y) {
        for (int x = 0; x < p.width; ++x) {
            const Biome biome = biome_at(seed, p, x, y);
            const Overlay overlay = overlay_at(seed, p, biome, x, y);
            world.tiles.push_back(gid_for(seed, p, biome, x, y, overlay));
            if (overlay == Overlay::None && !in_clearing(p, x, y)) {
                GenProp prop;
                if (prop_at(seed, p, biome, x, y, prop)) {
                    world.props.push_back(std::move(prop));
                }
                if (spawner_at(seed, p, biome, x, y)) {
                    world.spawners.emplace_back(x, y);
                }
            }
        }
    }
    const int cx = p.width / 2;
    const int cy = p.height / 2;
    world.spawn_x256 = cx * 256 + 128;
    world.spawn_y256 = cy * 256 + 128;
    for (const WorldNpc& npc : p.npcs) {
        world.npcs.push_back({npc.key, npc.dialogue, npc.variant, (cx + npc.dx) * 256 + 128, (cy + npc.dy) * 256 + 128});
    }
    return world;
}

GeneratedChunk generate_chunk(std::uint64_t seed, const WorldParams& p, int chunk_x, int chunk_y) {
    GeneratedChunk chunk;
    chunk.tiles.reserve(static_cast<std::size_t>(kChunkSize) * static_cast<std::size_t>(kChunkSize));
    for (int y = chunk_y * kChunkSize; y < (chunk_y + 1) * kChunkSize; ++y) {
        for (int x = chunk_x * kChunkSize; x < (chunk_x + 1) * kChunkSize; ++x) {
            const Biome biome = biome_at(seed, p, x, y);
            const Overlay overlay = overlay_at(seed, p, biome, x, y);
            chunk.tiles.push_back(gid_for(seed, p, biome, x, y, overlay));
            if (overlay == Overlay::None && !in_clearing(p, x, y)) {
                GenProp prop;
                if (prop_at(seed, p, biome, x, y, prop)) {
                    chunk.props.push_back(std::move(prop));
                }
                if (spawner_at(seed, p, biome, x, y)) {
                    chunk.spawners.emplace_back(x, y);
                }
            }
        }
    }
    return chunk;
}

int biome_code(std::uint64_t seed, const WorldParams& p, int cell_x, int cell_y) {
    return static_cast<int>(biome_at(seed, p, cell_x * kMapCell + kMapCell / 2, cell_y * kMapCell + kMapCell / 2));
}

void explore(std::set<std::pair<int, int>>& cells, const WorldParams& p, int tile_x, int tile_y) {
    const int columns = (p.width + kMapCell - 1) / kMapCell;
    const int rows = (p.height + kMapCell - 1) / kMapCell;
    const int cx = tile_x / kMapCell;
    const int cy = tile_y / kMapCell;
    for (int y = cy - 1; y <= cy + 1; ++y) {
        for (int x = cx - 1; x <= cx + 1; ++x) {
            if (x >= 0 && x < columns && y >= 0 && y < rows) {
                cells.insert({x, y});
            }
        }
    }
}

std::uint64_t digest_cells(const std::set<std::pair<int, int>>& cells) {
    std::vector<std::pair<int, int>> ordered(cells.begin(), cells.end());
    std::sort(ordered.begin(), ordered.end(), [](const auto& a, const auto& b) {
        return a.second != b.second ? a.second < b.second : a.first < b.first;
    });
    std::uint64_t h = 0;
    for (const auto& [x, y] : ordered) {
        h = hash64(h, x, y);
    }
    return h;
}

std::uint64_t digest_tiles(const std::vector<int>& tiles) {
    std::uint64_t h = 0;
    for (const int gid : tiles) {
        h = hash64(h, gid);
    }
    return h;
}

std::uint64_t digest_tile_row(const std::vector<int>& tiles, int width, int row) {
    std::uint64_t h = 0;
    for (int x = 0; x < width; ++x) {
        h = hash64(h, tiles[static_cast<std::size_t>(row) * static_cast<std::size_t>(width) + static_cast<std::size_t>(x)]);
    }
    return h;
}

std::uint64_t digest_props(const std::vector<GenProp>& props) {
    std::uint64_t h = 0;
    for (const GenProp& p : props) {
        const std::int64_t packed =
            static_cast<std::int64_t>(p.radius_x100) * 4294967296LL + static_cast<std::int64_t>(fnv1a64(p.art) >> 32);
        h = hash64(h, p.x256, p.y256, packed);
    }
    return h;
}

std::uint64_t digest_spawners(const std::vector<std::pair<int, int>>& spawners) {
    std::uint64_t h = 0;
    for (const auto& s : spawners) {
        h = hash64(h, s.first, s.second);
    }
    return h;
}

}  // namespace aether
