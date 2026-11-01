#include "data/world_data.hpp"

#include <nlohmann/json.hpp>

namespace aether {

namespace {

using Json = nlohmann::json;

NoiseSpec noise_spec(const Json& j) {
    return NoiseSpec{j.at("salt").get<int>(), j.at("scale").get<int>(), j.at("octaves").get<int>()};
}

}  // namespace

std::optional<WorldParams> parse_world_params(std::string_view json_text, std::string& error) {
    try {
        const Json j = Json::parse(json_text);
        WorldParams p;
        p.id = j.value("id", "");
        p.width = j.at("width").get<int>();
        p.height = j.at("height").get<int>();
        p.border = j.at("border").get<int>();
        p.spawn_clear_radius = j.at("spawn_clear_radius").get<int>();
        p.elevation = noise_spec(j.at("elevation"));
        p.moisture = noise_spec(j.at("moisture"));
        p.temperature = noise_spec(j.at("temperature"));
        p.river = noise_spec(j.at("river"));
        p.river_half_width = j.at("river").at("half_width").get<int>();
        p.ford_salt = j.at("river").at("ford_salt").get<int>();
        p.ford_scale = j.at("river").at("ford_scale").get<int>();
        p.ford_min = j.at("river").at("ford_min").get<int>();
        p.road = noise_spec(j.at("road"));
        p.road_half_width = j.at("road").at("half_width").get<int>();

        const Json& t = j.at("thresholds");
        p.water = t.at("water").get<int>();
        p.beach = t.at("beach").get<int>();
        p.mountain = t.at("mountain").get<int>();
        p.snow = t.at("snow").get<int>();
        p.desert_heat = t.at("desert_heat").get<int>();
        p.desert_dry = t.at("desert_dry").get<int>();
        p.forest_wet = t.at("forest_wet").get<int>();

        const Json& tiles = j.at("tiles");
        p.tile_water = tiles.at("water").get<int>();
        p.tile_beach = tiles.at("beach").get<int>();
        p.tile_desert = tiles.at("desert").get<int>();
        p.tile_snow = tiles.at("snow").get<int>();
        p.tile_mountain = tiles.at("mountain").get<int>();
        p.tile_forest = tiles.at("forest").get<int>();
        p.tile_river = tiles.at("river").get<int>();
        p.tile_ford = tiles.at("ford").get<int>();
        p.tile_road = tiles.at("road").get<int>();
        p.tile_bridge = tiles.at("bridge").get<int>();
        for (const Json& gid : tiles.at("plains")) {
            p.tiles_plains.push_back(gid.get<int>());
        }
        if (p.tiles_plains.empty() || p.width < 1 || p.height < 1 || p.ford_scale < 1) {
            error = "invalid world parameters";
            return std::nullopt;
        }

        for (const auto& [biome, options] : j.at("props").items()) {
            for (const Json& o : options) {
                p.props[biome].push_back({o.at("art").get<std::string>(), o.at("radius_x100").get<int>(),
                                          o.at("per_mille").get<int>()});
            }
        }

        const Json& s = j.at("spawners");
        p.spawner_enemy = s.at("enemy").get<std::string>();
        for (const Json& biome : s.at("biomes")) {
            p.spawner_biomes.push_back(biome.get<std::string>());
        }
        p.spawner_min_distance = s.at("min_distance").get<int>();
        p.spawner_per_10000 = s.at("per_10000").get<int>();
        p.spawner_respawn_ticks = s.at("respawn_ticks").get<int>();

        const Json& time = j.at("time");
        p.time.day_ticks = time.at("day_ticks").get<int>();
        p.time.start_tick = time.at("start_tick").get<std::int64_t>();
        for (const Json& key : time.at("light")) {
            p.time.light.emplace_back(key.at(0).get<int>(), key.at(1).get<int>());
        }
        const Json& weather = time.at("weather");
        p.time.period_ticks = weather.at("period_ticks").get<int>();
        p.time.fade_ticks = weather.at("fade_ticks").get<int>();
        for (const Json& kind : weather.at("kinds")) {
            p.time.kinds.push_back({kind.at("id").get<std::string>(), kind.at("weight").get<int>(),
                                    kind.at("rain_pm").get<int>(), kind.at("dim_pm").get<int>()});
        }
        if (p.time.light.size() < 2 || p.time.kinds.empty() || p.time.day_ticks < 1 || p.time.period_ticks < 1 ||
            p.time.fade_ticks < 1) {
            error = "invalid world time parameters";
            return std::nullopt;
        }

        for (const Json& n : j.at("npcs")) {
            p.npcs.push_back({n.at("key").get<std::string>(), n.at("dialogue").get<std::string>(),
                              n.at("variant").get<std::string>(), n.at("dx").get<int>(), n.at("dy").get<int>()});
        }
        return p;
    } catch (const std::exception& e) {
        error = e.what();
        return std::nullopt;
    }
}

}  // namespace aether
