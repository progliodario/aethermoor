#include "vector/recipe.hpp"

#include <cstdint>

#include <nlohmann/json.hpp>

namespace aether {

namespace {

using Json = nlohmann::json;

int hex_digit(char c) {
    if (c >= '0' && c <= '9') {
        return c - '0';
    }
    if (c >= 'a' && c <= 'f') {
        return c - 'a' + 10;
    }
    if (c >= 'A' && c <= 'F') {
        return c - 'A' + 10;
    }
    return -1;
}

Paint parse_paint(const Json& fill) {
    Paint paint;
    if (fill.contains("color")) {
        paint.kind = Paint::Kind::Solid;
        paint.color = fill.at("color").get<std::string>();
        return paint;
    }
    if (fill.contains("noise")) {
        const Json& n = fill.at("noise");
        paint.kind = Paint::Kind::Noise;
        paint.noise_scale = n.at("scale").get<float>();
        paint.noise_seed = n.value("seed", 0);
        paint.noise_octaves = n.value("octaves", 3);
        paint.noise_period = n.value("period", 0);
        for (const Json& stop : n.at("stops")) {
            paint.stops.push_back({stop.at(0).get<float>(), stop.at(1).get<std::string>()});
        }
        return paint;
    }
    const bool linear = fill.contains("linear");
    const Json& g = linear ? fill.at("linear") : fill.at("radial");
    paint.kind = linear ? Paint::Kind::Linear : Paint::Kind::Radial;
    if (linear) {
        paint.x0 = g.at("x0").get<float>();
        paint.y0 = g.at("y0").get<float>();
        paint.x1 = g.at("x1").get<float>();
        paint.y1 = g.at("y1").get<float>();
    } else {
        paint.cx = g.at("cx").get<float>();
        paint.cy = g.at("cy").get<float>();
        paint.r = g.at("r").get<float>();
    }
    for (const Json& stop : g.at("stops")) {
        paint.stops.push_back({stop.at(0).get<float>(), stop.at(1).get<std::string>()});
    }
    return paint;
}

Shape parse_shape(const Json& shape) {
    Shape out;
    if (shape.contains("rect") || shape.contains("ellipse")) {
        const bool rect = shape.contains("rect");
        out.kind = rect ? Shape::Kind::Rect : Shape::Kind::Ellipse;
        const Json& values = rect ? shape.at("rect") : shape.at("ellipse");
        for (std::size_t i = 0; i < 4; ++i) {
            out.v[i] = values.at(i).get<float>();
        }
    } else if (shape.contains("polygon")) {
        out.kind = Shape::Kind::Polygon;
        for (const Json& p : shape.at("polygon")) {
            out.points.emplace_back(p.at(0).get<float>(), p.at(1).get<float>());
        }
    } else {
        out.kind = Shape::Kind::Path;
        out.path = shape.at("path").get<std::string>();
    }
    return out;
}

Palette parse_palette(const Json& object) {
    Palette palette;
    for (const auto& [key, value] : object.items()) {
        palette[key] = value.get<std::string>();
    }
    return palette;
}

}  // namespace

bool parse_hex_color(std::string_view text, Color& out) {
    if ((text.size() != 7 && text.size() != 9) || text.front() != '#') {
        return false;
    }
    int channel[4] = {0, 0, 0, 255};
    const std::size_t count = (text.size() - 1) / 2;
    for (std::size_t i = 0; i < count; ++i) {
        const int hi = hex_digit(text[1 + 2 * i]);
        const int lo = hex_digit(text[2 + 2 * i]);
        if (hi < 0 || lo < 0) {
            return false;
        }
        channel[i] = hi * 16 + lo;
    }
    out.r = static_cast<float>(channel[0]) / 255.0F;
    out.g = static_cast<float>(channel[1]) / 255.0F;
    out.b = static_cast<float>(channel[2]) / 255.0F;
    out.a = static_cast<float>(channel[3]) / 255.0F;
    return true;
}

std::optional<Recipe> parse_recipe(std::string_view json_text, std::string& error) {
    try {
        const Json j = Json::parse(json_text);
        Recipe recipe;
        recipe.id = j.value("id", "");
        const Json& canvas = j.at("canvas");
        recipe.width = canvas.at("w").get<float>();
        recipe.height = canvas.at("h").get<float>();
        recipe.origin_x = canvas.at("origin").at(0).get<float>();
        recipe.origin_y = canvas.at("origin").at(1).get<float>();
        recipe.faces_left = j.value("faces", "") == "left";
        recipe.sway = j.value("sway", 0.0F);
        if (j.contains("palette")) {
            recipe.palette = parse_palette(j.at("palette"));
        }
        if (j.contains("variants")) {
            for (const auto& [name, palette] : j.at("variants").items()) {
                recipe.variants[name] = parse_palette(palette);
            }
        }
        for (const Json& l : j.at("layers")) {
            Layer layer;
            layer.shape = parse_shape(l.at("shape"));
            if (l.contains("fill")) {
                layer.fill = parse_paint(l.at("fill"));
            }
            if (l.contains("stroke")) {
                layer.stroke.present = true;
                layer.stroke.color = l.at("stroke").at("color").get<std::string>();
                layer.stroke.width = l.at("stroke").at("width").get<float>();
            }
            layer.alpha = l.value("alpha", 1.0F);
            layer.blur = l.value("blur", 0.0F);
            layer.clip = l.value("clip", false);
            const std::string blend = l.value("blend", "normal");
            layer.blend = blend == "multiply" ? Layer::Blend::Multiply
                                              : (blend == "add" ? Layer::Blend::Add : Layer::Blend::Normal);
            if (l.contains("only")) {
                layer.only = l.at("only").get<std::vector<std::string>>();
            }
            if (l.contains("except")) {
                layer.except = l.at("except").get<std::vector<std::string>>();
            }
            recipe.layers.push_back(std::move(layer));
        }
        return recipe;
    } catch (const Json::exception& e) {
        error = e.what();
        return std::nullopt;
    }
}

}  // namespace aether
