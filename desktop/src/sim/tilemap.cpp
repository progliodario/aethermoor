#include "sim/tilemap.hpp"

#include <nlohmann/json.hpp>

namespace aether {

namespace {

using Json = nlohmann::json;

const Json* find_property(const Json& object, const char* name) {
    if (!object.contains("properties")) {
        return nullptr;
    }
    for (const Json& property : object.at("properties")) {
        if (property.value("name", "") == name) {
            return &property.at("value");
        }
    }
    return nullptr;
}

}  // namespace

int TileMap::gid_at(int x, int y) const {
    if (x < 0 || y < 0 || x >= width || y >= height) {
        return 0;
    }
    return ground[static_cast<std::size_t>(y) * static_cast<std::size_t>(width) + static_cast<std::size_t>(x)];
}

std::optional<Tileset> parse_tileset(std::string_view json_text, std::string& error) {
    try {
        const Json j = Json::parse(json_text);
        Tileset tileset;
        tileset.id = j.value("id", "");
        for (const Json& tile : j.at("tiles")) {
            TileDef def;
            def.art = tile.at("art").get<std::string>();
            def.solid = tile.at("solid").get<bool>();
            tileset.tiles[tile.at("gid").get<int>()] = std::move(def);
        }
        return tileset;
    } catch (const Json::exception& e) {
        error = e.what();
        return std::nullopt;
    }
}

std::optional<TileMap> parse_tilemap(std::string_view tmj_text, std::string& error) {
    try {
        const Json j = Json::parse(tmj_text);
        TileMap map;
        map.width = j.at("width").get<int>();
        map.height = j.at("height").get<int>();
        const auto tile_size = j.at("tilewidth").get<float>();
        if (const Json* tileset = find_property(j, "tileset")) {
            map.tileset_id = tileset->get<std::string>();
        }
        bool has_spawn = false;
        for (const Json& layer : j.at("layers")) {
            const std::string type = layer.value("type", "");
            const std::string name = layer.value("name", "");
            if (type == "tilelayer" && name == "ground") {
                for (const Json& gid : layer.at("data")) {
                    map.ground.push_back(gid.get<int>());
                }
            } else if (type == "objectgroup" && name == "objects") {
                for (const Json& object : layer.at("objects")) {
                    const std::string kind = object.value("type", "");
                    const float x = object.at("x").get<float>() / tile_size;
                    const float y = object.at("y").get<float>() / tile_size;
                    if (kind == "spawn_player") {
                        map.spawn_x = x;
                        map.spawn_y = y;
                        has_spawn = true;
                    } else if (kind == "prop") {
                        Prop prop;
                        prop.x = x;
                        prop.y = y;
                        if (const Json* art = find_property(object, "art")) {
                            prop.art = art->get<std::string>();
                        }
                        if (const Json* radius = find_property(object, "radius")) {
                            prop.radius = radius->get<float>();
                        }
                        map.props.push_back(std::move(prop));
                    }
                }
            }
        }
        if (map.width <= 0 || map.height <= 0 ||
            map.ground.size() != static_cast<std::size_t>(map.width) * static_cast<std::size_t>(map.height)) {
            error = "ground layer missing or its size does not match width * height";
            return std::nullopt;
        }
        if (!has_spawn) {
            error = "map has no spawn_player object";
            return std::nullopt;
        }
        return map;
    } catch (const Json::exception& e) {
        error = e.what();
        return std::nullopt;
    }
}

}  // namespace aether
