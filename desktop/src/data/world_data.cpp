#include "data/world_data.hpp"

#include "data/pack.hpp"

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

        if (j.contains("routines")) {
            for (const auto& [role, frames] : j.at("routines").at("roles").items()) {
                auto& list = p.routines[role];
                for (const Json& frame : frames) {
                    list.emplace_back(frame.at(0).get<int>(), frame.at(1).get<std::string>());
                }
            }
        }
        p.stone_art = j.at("stones").at("art").get<std::string>();
        p.stone_range_x100 = j.at("stones").at("range_x100").get<int>();

        const Json& s = j.at("spawners");
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
        if (time.contains("seasons")) {
            for (const Json& entry : time.at("seasons")) {
                Season season;
                season.id = entry.at("id").get<std::string>();
                season.days = entry.at("days").get<int>();
                for (int i = 0; i < 4; ++i) {
                    season.tint[i] = entry.at("tint").at(static_cast<std::size_t>(i)).get<int>();
                }
                if (entry.contains("weights")) {
                    for (const auto& [kind, weight] : entry.at("weights").items()) {
                        season.weights[kind] = weight.get<int>();
                    }
                }
                if (entry.contains("light")) {
                    for (const Json& key : entry.at("light")) {
                        season.light.emplace_back(key.at(0).get<int>(), key.at(1).get<int>());
                    }
                }
                if (season.days < 1) {
                    error = "invalid season length";
                    return std::nullopt;
                }
                p.time.seasons.push_back(std::move(season));
            }
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

        const Json& guild = j.at("guild");
        p.guild.offers_per_day = guild.at("offers_per_day").get<int>();
        for (const Json& rank : guild.at("ranks")) {
            p.guild.ranks.push_back({rank.at("id").get<std::string>(), rank.at("points").get<int>()});
        }
        for (const Json& entry : guild.at("templates")) {
            GuildTemplate tpl;
            tpl.id = entry.at("id").get<std::string>();
            tpl.type = entry.at("type").get<std::string>();
            tpl.target = entry.at("target").get<std::string>();
            tpl.count_min = entry.at("count_min").get<int>();
            tpl.count_max = entry.at("count_max").get<int>();
            tpl.gold_base = entry.at("gold_base").get<int>();
            tpl.gold_per = entry.at("gold_per").get<int>();
            tpl.xp_base = entry.at("xp_base").get<int>();
            tpl.xp_per = entry.at("xp_per").get<int>();
            tpl.points_base = entry.at("points_base").get<int>();
            tpl.points_per = entry.at("points_per").get<int>();
            p.guild.templates.push_back(std::move(tpl));
        }
        if (p.guild.ranks.empty() || p.guild.templates.empty() || p.guild.offers_per_day < 1) {
            error = "invalid guild parameters";
            return std::nullopt;
        }
        if (j.contains("home")) {
            p.home_radius = j.at("home").at("radius").get<int>();
            p.home_stamp = j.at("home").at("stamp").get<std::string>();
            p.home_dx = j.at("home").at("dx").get<int>();
            p.home_dy = j.at("home").at("dy").get<int>();
        }
        for (const Json& r : j.at("regions")) {
            Region region;
            region.id = r.at("id").get<std::string>();
            region.name = r.at("name").get<std::string>();
            region.x_pm = r.at("x_pm").get<int>();
            region.y_pm = r.at("y_pm").get<int>();
            region.danger = r.at("danger").get<int>();
            region.tone = r.at("tone").get<std::string>();
            region.shop_price_pm = r.at("shop").at("price_pm").get<int>();
            for (const Json& item : r.at("shop").at("stock")) {
                region.shop_stock.push_back(item.get<std::string>());
            }
            for (const Json& entry : r.at("fauna")) {
                FaunaEntry fauna;
                fauna.enemy = entry.at("enemy").get<std::string>();
                fauna.drop = entry.at("drop").get<std::string>();
                fauna.weight = entry.at("weight").get<int>();
                if (fauna.weight < 1) {
                    error = "invalid fauna weight";
                    return std::nullopt;
                }
                region.fauna.push_back(std::move(fauna));
            }
            if (region.fauna.empty()) {
                error = "a region needs fauna";
                return std::nullopt;
            }
            p.regions.push_back(std::move(region));
        }
        const Json& settlements = j.at("settlements");
        p.settlement_per_mille = settlements.at("per_mille").get<int>();
        for (const Json& kind : settlements.at("kinds")) {
            SettlementKind parsed{kind.at("id").get<std::string>(), kind.at("weight").get<int>(), {}};
            for (const Json& stamp : kind.at("stamps")) {
                parsed.stamps.push_back(stamp.get<std::string>());
            }
            p.settlement_kinds.push_back(std::move(parsed));
        }
        for (const Json& syllable : settlements.at("names").at("start")) {
            p.names_start.push_back(syllable.get<std::string>());
        }
        for (const Json& syllable : settlements.at("names").at("mid")) {
            p.names_mid.push_back(syllable.get<std::string>());
        }
        for (const Json& syllable : settlements.at("names").at("end")) {
            p.names_end.push_back(syllable.get<std::string>());
        }
        p.settlement_dialogue = settlements.at("dialogue").get<std::string>();
        for (const Json& variant : settlements.at("variants")) {
            p.variants.push_back(variant.get<std::string>());
        }
        for (const Json& quirk : settlements.at("quirks")) {
            p.quirks.push_back(quirk.get<std::string>());
        }
        for (const Json& syllable : settlements.at("people").at("start")) {
            p.people_start.push_back(syllable.get<std::string>());
        }
        for (const Json& syllable : settlements.at("people").at("end")) {
            p.people_end.push_back(syllable.get<std::string>());
        }
        if (j.contains("stamp_defs")) {
            for (const auto& [id, def] : j.at("stamp_defs").items()) {
                Stamp stamp;
                stamp.w = def.at("w").get<int>();
                stamp.h = def.at("h").get<int>();
                stamp.anchor_x = def.at("anchor").at(0).get<int>();
                stamp.anchor_y = def.at("anchor").at(1).get<int>();
                for (const Json& row : def.at("rows")) {
                    stamp.rows.push_back(row.get<std::string>());
                }
                if (static_cast<int>(stamp.rows.size()) != stamp.h) {
                    error = id + ": the number of rows does not match h";
                    return std::nullopt;
                }
                for (const std::string& row : stamp.rows) {
                    if (static_cast<int>(row.size()) != stamp.w) {
                        error = id + ": a row does not have w characters";
                        return std::nullopt;
                    }
                }
                if (def.contains("spots")) {
                    for (const Json& spot : def.at("spots")) {
                        stamp.spots.emplace_back(spot.at(0).get<int>(), spot.at(1).get<int>());
                    }
                }
                for (const auto& [key, entry] : def.at("legend").items()) {
                    StampEntry parsed;
                    parsed.tile = entry.value("tile", 0);
                    parsed.prop = entry.value("prop", "");
                    parsed.radius_x100 = entry.value("radius_x100", 0);
                    parsed.npc = entry.value("npc", "");
                    stamp.legend[key.at(0)] = parsed;
                }
                p.stamps[id] = std::move(stamp);
            }
        }
        if (p.home_radius > 0 && p.stamps.find(p.home_stamp) == p.stamps.end()) {
            error = "unknown home stamp " + p.home_stamp;
            return std::nullopt;
        }
        for (const SettlementKind& kind : p.settlement_kinds) {
            for (const std::string& stamp : kind.stamps) {
                if (p.stamps.find(stamp) == p.stamps.end() && p.settlement_per_mille > 0) {
                    error = "unknown stamp " + stamp;
                    return std::nullopt;
                }
            }
        }
        if (p.variants.empty() || p.quirks.empty() || p.people_start.empty() || p.people_end.empty()) {
            error = "invalid settlement people";
            return std::nullopt;
        }
        if (p.regions.empty() || p.names_start.empty() || p.names_mid.empty() || p.names_end.empty() || p.settlement_kinds.empty()) {
            error = "invalid regions or settlements";
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

std::optional<WorldParams> load_world_params(const Pack& pack, std::string_view world_id, std::string& error) {
    const auto text = pack.read_document(world_id);
    if (!text) {
        error = "missing world " + std::string(world_id);
        return std::nullopt;
    }
    Json j = Json::parse(*text, nullptr, /*allow_exceptions=*/false);
    if (j.is_discarded()) {
        error = "invalid JSON in " + std::string(world_id);
        return std::nullopt;
    }
    try {
        Json defs = Json::object();
        if (j.contains("home")) {
            const std::string home_id = j.at("home").at("stamp").get<std::string>();
            const auto home_text = pack.read_document(home_id);
            if (!home_text) {
                error = "missing stamp " + home_id;
                return std::nullopt;
            }
            defs[home_id] = Json::parse(*home_text);
        }
        for (const Json& kind : j.at("settlements").at("kinds")) {
            for (const Json& stamp : kind.at("stamps")) {
                const auto stamp_text = pack.read_document(stamp.get<std::string>());
                if (!stamp_text) {
                    error = "missing stamp " + stamp.get<std::string>();
                    return std::nullopt;
                }
                defs[stamp.get<std::string>()] = Json::parse(*stamp_text);
            }
        }
        j["stamp_defs"] = defs;
    } catch (const std::exception& e) {
        error = e.what();
        return std::nullopt;
    }
    return parse_world_params(j.dump(), error);
}

}  // namespace aether
