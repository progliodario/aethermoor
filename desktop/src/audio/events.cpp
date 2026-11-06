#include "audio/events.hpp"

#include <algorithm>

#include <nlohmann/json.hpp>

namespace aether {

using Json = nlohmann::json;

std::vector<std::string> EventTable::all_sounds() const {
    std::vector<std::string> names;
    const auto add = [&names](const std::string& name) {
        if (std::find(names.begin(), names.end(), name) == names.end()) {
            names.push_back(name);
        }
    };
    for (const auto& [event, entry] : events) {
        for (const std::string& sound : entry.sounds) {
            add(sound);
        }
    }
    add(ambience.rain_light);
    add(ambience.rain_heavy);
    for (const auto& [region, entries] : ambience.regions) {
        for (const AmbienceEntry& entry : entries) {
            add(entry.sound);
        }
    }
    return names;
}

std::optional<EventTable> parse_event_table(std::string_view json_text, std::string& error) {
    try {
        const Json j = Json::parse(json_text);
        EventTable table;
        for (const auto& [name, entry] : j.at("events").items()) {
            EventSounds sounds;
            for (const Json& s : entry.at("sounds")) {
                sounds.sounds.push_back(s.get<std::string>());
            }
            sounds.volume_pm = entry.at("volume_pm").get<int>();
            sounds.cooldown = entry.value("cooldown", 0);
            table.events[name] = std::move(sounds);
        }
        const Json& amb = j.at("ambience");
        table.ambience.rain_light = amb.at("rain").at("light").get<std::string>();
        table.ambience.rain_heavy = amb.at("rain").at("heavy").get<std::string>();
        if (amb.at("rain").contains("silences")) {
            for (const Json& s : amb.at("rain").at("silences")) {
                table.ambience.silences.push_back(s.get<std::string>());
            }
        }
        for (const auto& [region, entries] : amb.at("regions").items()) {
            for (const Json& e : entries) {
                table.ambience.regions[region].push_back(
                    {e.at("sound").get<std::string>(), e.value("when", "always"), e.at("gain_pm").get<int>()});
            }
        }
        return table;
    } catch (const Json::exception& e) {
        error = e.what();
        return std::nullopt;
    }
}

}  // namespace aether
