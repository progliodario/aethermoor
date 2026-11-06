#pragma once

// Music: pieces of a few tracks on layers, rendered to seamless loops, and the director that chooses the piece and the
// layers. Spec: docs/spec/14-audio.md ("Music", normative). Headless.

#include <cstdint>
#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include "audio/director.hpp"
#include "audio/synth.hpp"

namespace aether {

struct MusicPatch {
    Wave wave = Wave::Sine;
    int attack_ms = 0;
    int decay_ms = 0;
    int sustain_pm = 1000;
    int release_ms = 0;
    int duty_pm = 500;
    int detune_cents = 0;
    int glide_pm = 1000;
    int am_dhz = 0;
    int am_depth_pm = 0;
};

struct MusicTrack {
    std::string layer;  // base, tension, combat or boss
    MusicPatch patch;
    int volume_pm = 1000;
    std::vector<std::string> bars;  // one string of 16 steps per bar; repeats when shorter than the piece
};

struct MusicPiece {
    std::string id;
    int tempo_bpm = 100;
    int bars = 1;
    int volume_pm = 1000;
    std::vector<MusicTrack> tracks;
};

std::optional<MusicPiece> parse_music(std::string_view json_text, std::string& error);

// Renders every layer of a piece to mono samples at kSampleRate. All layers have the same length: the loop.
std::map<std::string, std::vector<std::int16_t>> render_music(const MusicPiece& piece);

// What the music director is told each frame.
struct MusicContext {
    std::int64_t frame = 0;
    std::string screen = "game";  // title, game or dead
    std::string region;
    int tod_pm = 500;
    std::string place = "wild";       // wild, settlement or dungeon
    std::vector<std::string> quests;  // the IDs of the quests under way
    bool low_hp = false;
    std::vector<SoundCue> cues;
    double x = 0.0;
    double y = 0.0;
};

struct MusicRules {
    struct Choice {
        std::string day;
        std::string night;  // empty: the same as day
    };
    std::string title;
    std::string dead;
    std::string default_region;
    std::vector<std::pair<std::string, std::string>> quests;  // quest ID, piece; the first active one wins
    std::map<std::string, Choice> places;
    std::map<std::string, Choice> regions;
};

std::optional<MusicRules> parse_music_rules(std::string_view json_text, std::string& error);

struct MusicChoice {
    std::string piece;
    std::vector<std::string> layers;  // in the order base, tension, combat, boss
};

class MusicDirector {
public:
    explicit MusicDirector(MusicRules rules) : m_rules_(std::move(rules)) {}
    MusicChoice update(const MusicContext& ctx);

private:
    std::string piece_for(const MusicContext& ctx) const;

    MusicRules m_rules_;
    std::int64_t m_last_fight_ = -1000000000;
    std::int64_t m_last_boss_ = -1000000000;
};

}  // namespace aether
