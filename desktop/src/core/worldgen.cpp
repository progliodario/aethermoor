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
    if (p.home_radius > 0) {
        const std::int64_t dx = x - p.width / 2;
        const std::int64_t dy = y - p.height / 2;
        if (dx * dx + dy * dy < static_cast<std::int64_t>(p.home_radius) * p.home_radius) {
            return Biome::Plains;  // the home meadow
        }
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

// The settlement of each site cell, computed on demand (spec 09, "Settlements").
class Sites {
public:
    Sites(std::uint64_t seed, const WorldParams& p) : m_seed_(seed), m_params_(p) {}

    const std::optional<Settlement>& site(int sx, int sy) {
        const auto key = std::make_pair(sx, sy);
        auto found = m_cells_.find(key);
        if (found == m_cells_.end()) {
            found = m_cells_.emplace(key, compute(sx, sy)).first;
        }
        return found->second;
    }

    // True when the tile lies in a footprint; `entry` is then the legend entry of its character, or null.
    bool at(int x, int y, const StampEntry*& entry, const Settlement** settlement = nullptr) {
        entry = nullptr;
        const auto& s = site(x >> 8, y >> 8);
        if (!s) {
            return false;
        }
        const int lx = x - s->x;
        const int ly = y - s->y;
        if (lx < 0 || ly < 0 || lx >= s->w || ly >= s->h) {
            return false;
        }
        if (settlement != nullptr) {
            *settlement = &*s;
        }
        const Stamp& stamp = m_params_.stamps.at(s->stamp);
        const auto legend = stamp.legend.find(stamp.rows[static_cast<std::size_t>(ly)][static_cast<std::size_t>(lx)]);
        if (legend != stamp.legend.end()) {
            entry = &legend->second;
        }
        return true;
    }

private:
    std::optional<Settlement> compute(int sx, int sy) const {
        const WorldParams& p = m_params_;
        if (p.home_radius > 0) {
            const int hx = p.width / 2 + p.home_dx;
            const int hy = p.height / 2 + p.home_dy;
            if ((hx >> 8) == sx && (hy >> 8) == sy) {
                return home(sx, sy, hx, hy);
            }
        }
        const std::uint64_t h = hash64(m_seed_, sx, sy, 41);
        if ((h >> 40) % 1000 >= static_cast<std::uint64_t>(p.settlement_per_mille)) {
            return std::nullopt;
        }
        const int px = sx * kSiteCell + 40 + static_cast<int>((h >> 8) % 176);
        const int py = sy * kSiteCell + 40 + static_cast<int>((h >> 24) % 176);
        const std::uint64_t k = hash64(m_seed_, sx, sy, 42);
        std::uint64_t total = 0;
        for (const SettlementKind& kind : p.settlement_kinds) {
            total += static_cast<std::uint64_t>(kind.weight);
        }
        const std::uint64_t roll = (k >> 20) % total;
        std::uint64_t acc = 0;
        const SettlementKind* chosen = &p.settlement_kinds.back();
        for (const SettlementKind& kind : p.settlement_kinds) {
            acc += static_cast<std::uint64_t>(kind.weight);
            if (roll < acc) {
                chosen = &kind;
                break;
            }
        }
        const std::string& stamp_id = chosen->stamps[(k >> 40) % chosen->stamps.size()];
        const Stamp& stamp = p.stamps.at(stamp_id);
        const int ox = px - stamp.anchor_x;
        const int oy = py - stamp.anchor_y;
        const std::int64_t keep_out = p.spawn_clear_radius + 48;
        const std::int64_t dx = px - p.width / 2;
        const std::int64_t dy = py - p.height / 2;
        if (dx * dx + dy * dy < keep_out * keep_out) {
            return std::nullopt;
        }
        const int points[5][2] = {{px, py},
                                  {ox, oy},
                                  {ox + stamp.w - 1, oy},
                                  {ox, oy + stamp.h - 1},
                                  {ox + stamp.w - 1, oy + stamp.h - 1}};
        for (const auto& point : points) {
            const Biome biome = biome_at(m_seed_, p, point[0], point[1]);
            if (biome != Biome::Plains && biome != Biome::Forest) {
                return std::nullopt;
            }
        }
        const std::uint64_t n = hash64(m_seed_, sx, sy, 43);
        Settlement s;
        s.x = ox;
        s.y = oy;
        s.px = px;
        s.py = py;
        s.w = stamp.w;
        s.h = stamp.h;
        s.stamp = stamp_id;
        s.kind = chosen->id;
        s.name = p.names_start[n % p.names_start.size()] + p.names_mid[(n >> 16) % p.names_mid.size()] +
                 p.names_end[(n >> 32) % p.names_end.size()];
        s.region = region_at(p, px, py);
        add_slots(s, sx, sy);
        return s;
    }

    // The home village: fixed position, stamp and kind near the spawn (spec 09, "The home village").
    Settlement home(int sx, int sy, int px, int py) const {
        const WorldParams& p = m_params_;
        const Stamp& stamp = p.stamps.at(p.home_stamp);
        const std::uint64_t n = hash64(m_seed_, sx, sy, 43);
        Settlement s;
        s.x = px - stamp.anchor_x;
        s.y = py - stamp.anchor_y;
        s.px = px;
        s.py = py;
        s.w = stamp.w;
        s.h = stamp.h;
        s.stamp = p.home_stamp;
        s.kind = "village";
        for (const SettlementKind& kind : p.settlement_kinds) {
            if (std::find(kind.stamps.begin(), kind.stamps.end(), p.home_stamp) != kind.stamps.end()) {
                s.kind = kind.id;
                break;
            }
        }
        s.name = p.names_start[n % p.names_start.size()] + p.names_mid[(n >> 16) % p.names_mid.size()] +
                 p.names_end[(n >> 32) % p.names_end.size()];
        s.region = region_at(p, px, py);
        add_slots(s, sx, sy);
        return s;
    }

    // The cell and the NPC slots of the stamp (its characters with an npc role, in scan order).
    void add_slots(Settlement& s, int sx, int sy) const {
        s.sx = sx;
        s.sy = sy;
        const Stamp& stamp = m_params_.stamps.at(s.stamp);
        for (int ly = 0; ly < stamp.h; ++ly) {
            for (int lx = 0; lx < stamp.w; ++lx) {
                const auto entry = stamp.legend.find(stamp.rows[static_cast<std::size_t>(ly)][static_cast<std::size_t>(lx)]);
                if (entry != stamp.legend.end() && !entry->second.npc.empty()) {
                    const int index = static_cast<int>(s.slots.size());
                    s.slots[{s.x + lx, s.y + ly}] = {index, entry->second.npc};
                }
            }
        }
    }

    std::uint64_t m_seed_;
    const WorldParams& m_params_;
    std::map<std::pair<int, int>, std::optional<Settlement>> m_cells_;
};

// Appends tile (x, y): its gid, and its prop or spawner. Settlements replace everything under their footprint.
void emit_tile(std::uint64_t seed, const WorldParams& p, Sites& sites, int x, int y, std::vector<int>& tiles,
               std::vector<GenProp>& props, std::vector<std::pair<int, int>>& spawners, std::vector<GenPerson>& people) {
    const Biome biome = biome_at(seed, p, x, y);
    const StampEntry* entry = nullptr;
    const Settlement* settlement = nullptr;
    if (sites.at(x, y, entry, &settlement)) {
        tiles.push_back(entry != nullptr && entry->tile != 0 ? entry->tile : gid_for(seed, p, biome, x, y, Overlay::None));
        if (entry != nullptr && !entry->prop.empty()) {
            props.push_back({entry->prop, entry->radius_x100, x * 256 + 128, y * 256 + 192});
        }
        if (entry != nullptr && !entry->npc.empty()) {
            people.push_back(person_at(seed, p, *settlement, x, y));
        }
        return;
    }
    const Overlay overlay = overlay_at(seed, p, biome, x, y);
    tiles.push_back(gid_for(seed, p, biome, x, y, overlay));
    if (overlay == Overlay::None && !in_clearing(p, x, y)) {
        GenProp prop;
        if (prop_at(seed, p, biome, x, y, prop)) {
            props.push_back(std::move(prop));
        }
        if (spawner_at(seed, p, biome, x, y)) {
            spawners.emplace_back(x, y);
        }
    }
}

}  // namespace

GenPerson person_at(std::uint64_t seed, const WorldParams& p, const Settlement& s, int x, int y) {
    const auto& [index, role] = s.slots.at({x, y});
    const std::uint64_t h = hash64(seed, s.sx, s.sy, 100 + index);
    const Region& region = p.regions[static_cast<std::size_t>(s.region)];
    GenPerson person;
    person.key = "settle:" + std::to_string(s.sx) + ":" + std::to_string(s.sy) + ":" + std::to_string(index);
    person.role = role;
    person.x256 = x * 256 + 128;
    person.y256 = y * 256 + 160;
    person.name = p.people_start[h % p.people_start.size()] + p.people_end[(h >> 16) % p.people_end.size()];
    person.variant = p.variants[(h >> 32) % p.variants.size()];
    person.tone = region.tone;
    person.dialogue = p.settlement_dialogue;
    const auto replace_all = [&person](const std::string& token, const std::string& value) {
        for (std::size_t at = person.dialogue.find(token); at != std::string::npos; at = person.dialogue.find(token, at + value.size())) {
            person.dialogue.replace(at, token.size(), value);
        }
    };
    replace_all("{role}", role);
    replace_all("{tone}", region.tone);
    person.place = s.name;
    person.region = region.name;
    person.quirk = p.quirks[hash64(seed, s.sx, s.sy, 44) % p.quirks.size()];
    return person;
}

int rank_index(const GuildParams& guild, std::int64_t points) {
    int index = 0;
    for (std::size_t i = 0; i < guild.ranks.size(); ++i) {
        if (points >= guild.ranks[i].points) {
            index = static_cast<int>(i);
        }
    }
    return index;
}

std::vector<Offer> offers_for(std::uint64_t seed, const WorldParams& p, const Settlement& settlement, std::int64_t day) {
    std::vector<Offer> offers;
    for (int slot = 0; slot < p.guild.offers_per_day; ++slot) {
        const std::uint64_t h = hash64(hash64(seed, settlement.sx, settlement.sy, 200 + slot), day, slot);
        const GuildTemplate& t = p.guild.templates[(h >> 16) % p.guild.templates.size()];
        const std::uint64_t span = static_cast<std::uint64_t>(t.count_max - t.count_min + 1);
        Offer offer;
        offer.slot = slot;
        offer.id = "board:" + std::to_string(settlement.sx) + ":" + std::to_string(settlement.sy) + ":" + std::to_string(day) + ":" +
                   std::to_string(slot);
        offer.min_rank = std::min(slot, static_cast<int>(p.guild.ranks.size()) - 1);
        offer.template_id = t.id;
        offer.type = t.type;
        offer.target = t.target;
        offer.count = t.count_min + static_cast<int>((h >> 32) % span);
        const std::int64_t tier = slot + 1;
        offer.gold = (t.gold_base + static_cast<std::int64_t>(offer.count) * t.gold_per) * tier;
        offer.xp = (t.xp_base + static_cast<std::int64_t>(offer.count) * t.xp_per) * tier;
        offer.points = (t.points_base + static_cast<std::int64_t>(offer.count) * t.points_per) * tier;
        offer.place = settlement.name;
        offer.tone = p.regions[static_cast<std::size_t>(settlement.region)].tone;
        offers.push_back(std::move(offer));
    }
    return offers;
}

std::optional<Offer> resolve_offer(std::uint64_t seed, const WorldParams& p, const std::string& quest_id) {
    std::vector<std::string> parts;
    for (std::size_t start = 0; start <= quest_id.size();) {
        const std::size_t end = quest_id.find(':', start);
        parts.push_back(quest_id.substr(start, end == std::string::npos ? std::string::npos : end - start));
        if (end == std::string::npos) {
            break;
        }
        start = end + 1;
    }
    if (parts.size() != 5 || parts[0] != "board") {
        return std::nullopt;
    }
    int sx = 0;
    int sy = 0;
    int slot = 0;
    std::int64_t day = 0;
    try {
        sx = std::stoi(parts[1]);
        sy = std::stoi(parts[2]);
        day = std::stoll(parts[3]);
        slot = std::stoi(parts[4]);
    } catch (const std::exception&) {
        return std::nullopt;
    }
    const auto settlement = settlement_site(seed, p, sx, sy);
    if (!settlement) {
        return std::nullopt;
    }
    for (Offer& offer : offers_for(seed, p, *settlement, day)) {
        if (offer.slot == slot) {
            return std::move(offer);
        }
    }
    return std::nullopt;
}

int region_at(const WorldParams& p, int x, int y) {
    int best = 0;
    std::int64_t best_distance = -1;
    for (std::size_t i = 0; i < p.regions.size(); ++i) {
        const std::int64_t dx = x - static_cast<std::int64_t>(p.regions[i].x_pm) * p.width / 1000;
        const std::int64_t dy = y - static_cast<std::int64_t>(p.regions[i].y_pm) * p.height / 1000;
        const std::int64_t d = dx * dx + dy * dy;
        if (best_distance < 0 || d < best_distance) {
            best = static_cast<int>(i);
            best_distance = d;
        }
    }
    return best;
}

std::optional<Settlement> settlement_site(std::uint64_t seed, const WorldParams& p, int site_x, int site_y) {
    Sites sites(seed, p);
    return sites.site(site_x, site_y);
}

std::vector<Settlement> settlements_in(std::uint64_t seed, const WorldParams& p, int sx0, int sy0, int sx1, int sy1) {
    Sites sites(seed, p);
    std::vector<Settlement> found;
    for (int sy = sy0; sy <= sy1; ++sy) {
        for (int sx = sx0; sx <= sx1; ++sx) {
            if (const auto& s = sites.site(sx, sy)) {
                found.push_back(*s);
            }
        }
    }
    return found;
}

std::optional<Settlement> settlement_marker(std::uint64_t seed, const WorldParams& p, int cell_x, int cell_y) {
    constexpr int kPerSite = kSiteCell / kMapCell;
    Sites sites(seed, p);
    const auto& s = sites.site(cell_x / kPerSite, cell_y / kPerSite);
    if (s && s->px / kMapCell == cell_x && s->py / kMapCell == cell_y) {
        return s;
    }
    return std::nullopt;
}

GeneratedWorld generate_world(std::uint64_t seed, const WorldParams& p) {
    GeneratedWorld world;
    world.width = p.width;
    world.height = p.height;
    world.tiles.reserve(static_cast<std::size_t>(p.width) * static_cast<std::size_t>(p.height));
    Sites sites(seed, p);
    for (int y = 0; y < p.height; ++y) {
        for (int x = 0; x < p.width; ++x) {
            emit_tile(seed, p, sites, x, y, world.tiles, world.props, world.spawners, world.people);
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
    Sites sites(seed, p);
    for (int y = chunk_y * kChunkSize; y < (chunk_y + 1) * kChunkSize; ++y) {
        for (int x = chunk_x * kChunkSize; x < (chunk_x + 1) * kChunkSize; ++x) {
            emit_tile(seed, p, sites, x, y, chunk.tiles, chunk.props, chunk.spawners, chunk.people);
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
