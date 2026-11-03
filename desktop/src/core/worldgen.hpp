#pragma once

// World generation. Spec: docs/spec/09-worldgen.md. Reference: tools/reference/worldgen.py.
// Integer arithmetic only: no floating point in this module.

#include <cstdint>
#include <map>
#include <optional>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "core/worldtime.hpp"

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

// An enemy of the fauna of a region (spec 09, "Fauna"): what a spawner makes and what it drops.
struct FaunaEntry {
    std::string enemy;
    std::string drop;
    int weight = 1;
};

struct Region {
    std::string id;
    std::string name;  // an $i18n: key
    int x_pm = 0;
    int y_pm = 0;
    int danger = 1;
    std::string tone;  // the voice of the people of the region
    int shop_price_pm = 1000;  // what the shops of the region sell (spec 06)
    std::vector<std::string> shop_stock;
    std::vector<FaunaEntry> fauna;  // the enemies of the spawners of the region, by weight
};

struct SettlementKind {
    std::string id;
    int weight = 1;
    std::vector<std::string> stamps;  // stamp ids
};

// What a character of a stamp means (spec 09, "Settlements").
struct StampEntry {
    int tile = 0;  // 0: keep the terrain
    std::string prop;
    int radius_x100 = 0;
    std::string npc;
    std::string spawner;  // an enemy ID: an enemy spawner stands on this tile (dungeons)
};

// The guild (spec 07, "Guild"): ranks and the templates of the board offers.
struct GuildRank {
    std::string id;
    int points = 0;
};

struct GuildTemplate {
    std::string id;
    std::string type;    // "kill" or "collect"
    std::string target;  // enemy or item ID
    int count_min = 1;
    int count_max = 1;
    int gold_base = 0;
    int gold_per = 0;
    int xp_base = 0;
    int xp_per = 0;
    int points_base = 0;
    int points_per = 0;
};

struct GuildParams {
    int offers_per_day = 0;
    std::vector<GuildRank> ranks;
    std::vector<GuildTemplate> templates;
};

struct Stamp {
    int w = 0;
    int h = 0;
    int anchor_x = 0;
    int anchor_y = 0;
    std::vector<std::string> rows;
    std::map<char, StampEntry> legend;
    std::vector<std::pair<int, int>> spots;  // gathering tiles relative to the stamp (spec 08, Routines)
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

    NoiseSpec river;  // rivers and roads: places where a field is near its middle value (spec 09)
    int river_half_width = 0;
    int ford_salt = 0;
    int ford_scale = 1;
    int ford_min = 0;
    NoiseSpec road;
    int road_half_width = 0;

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
    int tile_river = 0;
    int tile_ford = 0;
    int tile_road = 0;
    int tile_bridge = 0;
    std::vector<int> tiles_plains;

    std::map<std::string, std::vector<PropOption>> props;  // by biome name

    std::vector<std::string> spawner_biomes;
    int spawner_min_distance = 0;
    int spawner_per_10000 = 0;
    int spawner_respawn_ticks = 0;

    TimeParams time;

    int landmark_clearing = 0;  // tiles of plains around the footprint of a landmark (spec 09); 0: none
    int home_radius = 0;  // the home meadow and village (spec 09); 0: none
    std::string home_stamp;
    int home_dx = 0;
    int home_dy = 0;

    GuildParams guild;

    // Hand-placed sites with a fixed stamp, such as dungeons (spec 09, "Landmarks").
    struct Landmark {
        std::string id;
        std::string name;
        std::string stamp;
        std::string kind;
        int dx = 0;
        int dy = 0;
    };
    std::vector<Landmark> landmarks;

    // Daily routines by role: keyframes (from_pm, state) with state work, plaza or away (spec 08).
    std::map<std::string, std::vector<std::pair<int, std::string>>> routines;

    std::string stone_art;  // the prop that is a Threshold Stone (spec 09)
    int stone_range_x100 = 0;  // how near the player must be to use it, in 1/100 tile

    std::vector<Region> regions;
    int settlement_per_mille = 0;
    std::vector<SettlementKind> settlement_kinds;
    std::vector<std::string> names_start;
    std::vector<std::string> names_mid;
    std::vector<std::string> names_end;
    std::string settlement_dialogue;  // dialogue id of a settlement NPC with {role} and {tone}
    std::vector<std::string> variants;
    std::vector<std::string> quirks;
    std::vector<std::string> people_start;
    std::vector<std::string> people_end;
    std::map<std::string, Stamp> stamps;  // by id, resolved by the loader

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

// An NPC of a settlement (spec 09, "Settlement people").
struct GenPerson {
    std::string key;
    std::string role;
    int x256 = 0;
    int y256 = 0;
    std::string name;
    std::string variant;
    std::string tone;
    std::string dialogue;
    std::string place;
    std::string region;  // a text key
    std::string quirk;   // a text key
    int plaza_x256 = -1;  // gathering spot (spec 08), -1 when the stamp has none
    int plaza_y256 = -1;
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
    std::vector<GenPerson> people;
};

GeneratedWorld generate_world(std::uint64_t seed, const WorldParams& params);

// A chunk is a kChunkSize x kChunkSize window of the world; chunk (cx, cy) starts at tile (cx * kChunkSize, cy * kChunkSize).
constexpr int kChunkSize = 32;

struct GeneratedChunk {
    std::vector<int> tiles;  // kChunkSize * kChunkSize gids, row-major
    std::vector<GenProp> props;  // scan order inside the chunk
    std::vector<std::pair<int, int>> spawners;  // absolute tile coordinates, scan order
    std::vector<GenPerson> people;  // scan order
};

// Exactly the restriction of generate_world to the window. Any chunk coordinates are valid: tiles outside the world are water.
GeneratedChunk generate_chunk(std::uint64_t seed, const WorldParams& params, int chunk_x, int chunk_y);

// Regions and settlements (spec 09). Site cells are kSiteCell x kSiteCell tiles.
constexpr int kSiteCell = 256;

struct Settlement {
    int x = 0;  // top-left tile of the footprint
    int y = 0;
    int px = 0;  // site point (the anchor of the stamp)
    int py = 0;
    int w = 0;
    int h = 0;
    std::string stamp;
    std::string kind;
    std::string name;
    int region = 0;
    int sx = 0;  // site cell
    int sy = 0;
    // NPC slots by tile: (index in scan order of the stamp, role).
    std::map<std::pair<int, int>, std::pair<int, std::string>> slots;
    // Gathering tiles of the stamp, in the world.
    std::vector<std::pair<int, int>> spots;
};

// The NPC standing on the slot tile (x, y) of the settlement.
GenPerson person_at(std::uint64_t seed, const WorldParams& params, const Settlement& settlement, int x, int y);

// Where a person is at a time of day (spec 08, "Routines"): state work or plaza, nothing while away.
struct Placement {
    std::string state;
    int x256 = 0;
    int y256 = 0;
};
std::optional<Placement> person_placement(const WorldParams& params, const GenPerson& person, int tod_pm);

// An offer of the board of a settlement (spec 07, "Guild").
struct Offer {
    std::string id;  // board:<sx>:<sy>:<day>:<slot>
    int slot = 0;
    int min_rank = 0;
    std::string template_id;
    std::string type;
    std::string target;
    int count = 0;
    std::int64_t gold = 0;
    std::int64_t xp = 0;
    std::int64_t points = 0;
    std::string place;
    std::string tone;
};

// Index of the rank of a member with that many guild points.
int rank_index(const GuildParams& guild, std::int64_t points);
std::vector<Offer> offers_for(std::uint64_t seed, const WorldParams& params, const Settlement& settlement, std::int64_t day);
// The offer a generated quest id names, or nothing when the world cannot rebuild it.
std::optional<Offer> resolve_offer(std::uint64_t seed, const WorldParams& params, const std::string& quest_id);

// The enemy that the stamp under the tile names for a spawner there (dungeons), if any.
std::optional<std::string> stamp_spawner_at(std::uint64_t seed, const WorldParams& params, int x, int y);
// The enemy of the spawner on the tile: the one of its stamp, else a pick of the fauna of its region (spec 09).
std::string spawner_enemy_at(std::uint64_t seed, const WorldParams& params, int x, int y);
// Every enemy a spawner of the world can make (fauna of the regions and spawners of the stamps), sorted.
std::vector<std::string> world_enemy_ids(const WorldParams& params);

// The settlement whose footprint contains the tile, if any (looks at the site cell of the tile and its neighbours).
std::optional<Settlement> settlement_containing(std::uint64_t seed, const WorldParams& params, int x, int y);

// Index of the region of the tile: the nearest center.
int region_at(const WorldParams& params, int x, int y);
// The entry that r falls on when the entries share sum(weight) slots in order (entries must not be empty).
const FaunaEntry& pick_fauna(const std::vector<FaunaEntry>& entries, std::uint64_t r);
// The fauna entry of the spawner on tile (x, y): a weighted pick among the fauna of its region.
const FaunaEntry& fauna_at(std::uint64_t seed, const WorldParams& params, int x, int y);
std::optional<Settlement> settlement_site(std::uint64_t seed, const WorldParams& params, int site_x, int site_y);
// The settlements of the site cells sx0..sx1, sy0..sy1 (inclusive), row-major.
std::vector<Settlement> settlements_in(std::uint64_t seed, const WorldParams& params, int sx0, int sy0, int sx1, int sy1);
// The settlement shown on the world map cell: the one whose site point lies in the cell.
std::optional<Settlement> settlement_marker(std::uint64_t seed, const WorldParams& params, int cell_x, int cell_y);

// The world map (spec 09, "Exploration and the world map"): cells of kMapCell x kMapCell tiles.
constexpr int kMapCell = 128;
// Biome code of a cell: 0 water, 1 beach, 2 mountain, 3 snow, 4 desert, 5 forest, 6 plains.
int biome_code(std::uint64_t seed, const WorldParams& params, int cell_x, int cell_y);
// Marks the cell of the tile and its eight neighbours inside the world as explored.
void explore(std::set<std::pair<int, int>>& cells, const WorldParams& params, int tile_x, int tile_y);
std::uint64_t digest_cells(const std::set<std::pair<int, int>>& cells);

// Digests used by the conformance vectors.
std::uint64_t digest_tiles(const std::vector<int>& tiles);
std::uint64_t digest_tile_row(const std::vector<int>& tiles, int width, int row);
std::uint64_t digest_props(const std::vector<GenProp>& props);
std::uint64_t digest_spawners(const std::vector<std::pair<int, int>>& spawners);

}  // namespace aether
