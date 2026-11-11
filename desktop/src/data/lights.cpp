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

}  // namespace aether
