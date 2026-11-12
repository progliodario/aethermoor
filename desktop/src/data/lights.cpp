#include "data/lights.hpp"

#include <nlohmann/json.hpp>

#include "data/pack.hpp"

namespace aether {

std::vector<LightDef> load_lights(const Pack& pack) {
    std::vector<LightDef> out;
    const auto text = pack.read_document("base:lights/all");
    if (!text) {
        return out;
    }
    const nlohmann::json doc = nlohmann::json::parse(*text, nullptr, /*allow_exceptions=*/false);
    if (doc.is_discarded() || !doc.contains("lights") || !doc.at("lights").is_array()) {
        return out;
    }
    for (const nlohmann::json& l : doc.at("lights")) {
        LightDef light;
        light.art = l.value("art", "");
        light.radius = static_cast<float>(l.value("radius_x100", 350)) / 100.0F;
        const std::string color = l.value("color", "#FFC870");
        if (color.size() == 7) {
            light.r = std::stoi(color.substr(1, 2), nullptr, 16);
            light.g = std::stoi(color.substr(3, 2), nullptr, 16);
            light.b = std::stoi(color.substr(5, 2), nullptr, 16);
        }
        light.strength_pm = l.value("strength_pm", 600);
        light.flicker_pm = l.value("flicker_pm", 0);
        out.push_back(std::move(light));
    }
    return out;
}

Grading load_grading(const Pack& pack) {
    Grading out;
    const auto text = pack.read_document("base:lights/all");
    if (!text) {
        return out;
    }
    const nlohmann::json doc = nlohmann::json::parse(*text, nullptr, /*allow_exceptions=*/false);
    if (doc.is_discarded() || !doc.contains("grading") || !doc.at("grading").is_object()) {
        return out;
    }
    const nlohmann::json& g = doc.at("grading");
    const auto color = [&g](const char* key, std::array<int, 3>& into) {
        const std::string value = g.value(key, "");
        if (value.size() == 7 && value[0] == '#') {
            into = {std::stoi(value.substr(1, 2), nullptr, 16), std::stoi(value.substr(3, 2), nullptr, 16),
                    std::stoi(value.substr(5, 2), nullptr, 16)};
        }
    };
    color("night", out.night);
    color("twilight", out.twilight);
    color("mote_day", out.mote_day);
    color("mote_night", out.mote_night);
    out.vignette_pm = g.value("vignette_pm", out.vignette_pm);
    out.motes = g.value("motes", out.motes);
    out.shadow_pm = g.value("shadow_pm", out.shadow_pm);
    if (g.contains("snow_regions") && g.at("snow_regions").is_array()) {
        for (const nlohmann::json& region : g.at("snow_regions")) {
            if (region.is_string()) {
                out.snow_regions.push_back(region.get<std::string>());
            }
        }
    }
    return out;
}

}  // namespace aether
