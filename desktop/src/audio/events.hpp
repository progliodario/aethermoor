#pragma once

// The table that says which sounds play for an event, and what loops where (data/base/audio/events.json, spec 14).

#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include "audio/director.hpp"

namespace aether {

struct EventSounds {
    std::vector<std::string> sounds;  // short names (`swing_a` is `base:audio/sfx/swing_a`); played in turn
    int volume_pm = 1000;
    int cooldown = 0;  // frames during which the event does not play again
};

struct EventTable {
    std::map<std::string, EventSounds, std::less<>> events;
    AmbienceRules ambience;
    // Every sound name the table mentions.
    std::vector<std::string> all_sounds() const;
};

std::optional<EventTable> parse_event_table(std::string_view json_text, std::string& error);

}  // namespace aether
