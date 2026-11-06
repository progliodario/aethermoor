#pragma once

// The sound director: from a snapshot of the game each frame, the sound events to play, and the gain of the looping
// ambience of a place. Spec: docs/spec/14-audio.md ("What plays when"). Headless and free of randomness.

#include <cstdint>
#include <map>
#include <optional>
#include <string>
#include <vector>

namespace aether {

// Something a creature did this frame (the simulation reports it): `kind` is hit, hurt, die, aggro or attack.
struct SoundCue {
    std::string kind;
    std::string family;
    double x = 0.0;
    double y = 0.0;
    bool crit = false;
    bool weak = false;
};

struct PlayerSound {
    std::int64_t hp = 1;
    std::int64_t max_hp = 1;
    std::int64_t level = 1;
    int phase = 0;  // 0 none, otherwise startup, active or recovery of an attack
    bool strike = false;
    bool dodge = false;
    bool moving = false;
    double x = 0.0;
    double y = 0.0;
    std::string surface = "grass";
    std::int64_t save_cd = 0;
};

struct PanelsOpen {
    bool bag = false;
    bool map = false;
    bool journal = false;
    bool shop = false;
    bool board = false;
    bool travel = false;
    bool any() const { return bag || map || journal || shop || board || travel; }
};

struct SoundSnapshot {
    std::int64_t frame = 0;
    PlayerSound player;
    std::vector<SoundCue> cues;
    std::int64_t items = 0;  // how many things are in the bag
    std::int64_t gold = 0;
    std::int64_t mp = 0;
    std::string weapon;
    std::string armor;
    PanelsOpen panels;
    bool dialogue = false;
    std::int64_t line = 0;    // grows with every line of dialogue
    std::int64_t cursor = 0;  // the sum of the cursors of the menus
    std::int64_t quests_started = 0;
    std::int64_t quests_done = 0;
    std::int64_t stones = 0;
    std::string region;
    int tod_pm = 0;
    int rain_pm = 0;
};

struct SoundEvent {
    std::string event;
    int volume_pm = 1000;
};

class SoundDirector {
public:
    // One frame: the events to play.
    std::vector<SoundEvent> update(const SoundSnapshot& s);

private:
    std::optional<SoundSnapshot> m_prev_;
    double m_walked_ = 0.0;
    int m_since_heartbeat_ = 70;
};

struct AmbienceEntry {
    std::string sound;
    std::string when = "always";  // always, day or night
    int gain_pm = 0;
};

struct AmbienceRules {
    std::string rain_light;
    std::string rain_heavy;
    std::vector<std::string> silences;  // loops that stop when it rains
    std::map<std::string, std::vector<AmbienceEntry>> regions;
};

// The gain (permille) of every looping sound for a place and a moment; silent loops are left out.
std::map<std::string, int> ambience_gains(const std::string& region, int tod_pm, int rain_pm,
                                          const AmbienceRules& rules);

}  // namespace aether
