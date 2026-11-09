#include "audio/music.hpp"

#include <algorithm>
#include <cmath>
#include <sstream>

#include <nlohmann/json.hpp>

namespace aether {

namespace {

using Json = nlohmann::json;

constexpr int kStepsPerBar = 16;
constexpr std::int64_t kFightFrames = 420;
constexpr std::int64_t kBossFrames = 600;
constexpr double kFightRangeTiles = 10.0;
constexpr double kPi = 3.14159265358979323846;

std::optional<Wave> wave_of(const std::string& name) {
    if (name == "sine") {
        return Wave::Sine;
    }
    if (name == "square") {
        return Wave::Square;
    }
    if (name == "saw") {
        return Wave::Saw;
    }
    if (name == "triangle") {
        return Wave::Triangle;
    }
    if (name == "noise") {
        return Wave::Noise;
    }
    return std::nullopt;
}

std::uint32_t xorshift(std::uint32_t state) {
    state ^= state << 13;
    state ^= state >> 17;
    state ^= state << 5;
    return state;
}

// `C4`, `F#3`, `Bb2`: the pitch in Hz (A4 = 440).
double note_frequency(const std::string& name) {
    int semitone = 0;
    switch (name[0]) {
        case 'C':
            semitone = 0;
            break;
        case 'D':
            semitone = 2;
            break;
        case 'E':
            semitone = 4;
            break;
        case 'F':
            semitone = 5;
            break;
        case 'G':
            semitone = 7;
            break;
        case 'A':
            semitone = 9;
            break;
        default:
            semitone = 11;
            break;
    }
    std::size_t i = 1;
    while (i < name.size() && (name[i] == '#' || name[i] == 'b')) {
        semitone += name[i] == '#' ? 1 : -1;
        ++i;
    }
    const int octave = std::stoi(name.substr(i));
    const int midi = 12 * (octave + 1) + semitone;
    return 440.0 * std::pow(2.0, static_cast<double>(midi - 69) / 12.0);
}

struct NoteEvent {
    int first = 0;
    int length = 0;
    std::vector<std::string> chord;
};

std::vector<NoteEvent> events_of(const MusicTrack& track, int bars) {
    std::vector<std::string> tokens;
    for (int bar = 0; bar < bars; ++bar) {
        std::istringstream in(track.bars[static_cast<std::size_t>(bar) % track.bars.size()]);
        std::string token;
        while (in >> token) {
            tokens.push_back(token);
        }
    }
    std::vector<NoteEvent> notes;
    for (std::size_t step = 0; step < tokens.size(); ++step) {
        const std::string& token = tokens[step];
        if (token == "-" && !notes.empty() &&
            static_cast<std::size_t>(notes.back().first + notes.back().length) == step) {
            ++notes.back().length;
        } else if (token != "." && token != "-") {
            NoteEvent note;
            note.first = static_cast<int>(step);
            note.length = 1;
            std::istringstream chord(token);
            std::string name;
            while (std::getline(chord, name, '+')) {
                note.chord.push_back(name);
            }
            notes.push_back(std::move(note));
        }
    }
    return notes;
}

// One note of a patch: `length` samples held, then the release; `total` samples in all.
std::vector<double> voice(const MusicPatch& patch, double freq, int length, int total, std::uint32_t state_seed) {
    const double attack = std::max(1.0, static_cast<double>(patch.attack_ms));
    const double decay = std::max(1.0, static_cast<double>(patch.decay_ms));
    const double sustain = static_cast<double>(patch.sustain_pm) / 1000.0;
    const double release = std::max(1.0, static_cast<double>(patch.release_ms));
    const double am_hz = static_cast<double>(patch.am_dhz) / 10.0;
    const double am_depth = static_cast<double>(patch.am_depth_pm) / 1000.0;
    const double length_ms = static_cast<double>(length) * 1000.0 / static_cast<double>(kSampleRate);
    std::vector<double> out(static_cast<std::size_t>(total), 0.0);
    std::vector<double> ratios;
    if (patch.detune_cents == 0) {
        ratios.push_back(1.0);
    } else {
        ratios.push_back(std::pow(2.0, static_cast<double>(patch.detune_cents) / 1200.0));
        ratios.push_back(std::pow(2.0, -static_cast<double>(patch.detune_cents) / 1200.0));
    }
    const double g = static_cast<double>(patch.glide_pm) / 1000.0;
    const double lg = patch.glide_pm != 1000 ? std::log(g) : 0.0;
    const double note_seconds = static_cast<double>(length) / static_cast<double>(kSampleRate);
    for (const double ratio : ratios) {
        const double f = freq * ratio;
        std::uint32_t state = state_seed != 0 ? state_seed : 1U;
        double held = 0.0;
        double prev_cycle = -1.0;
        for (int i = 0; i < total; ++i) {
            const double t = static_cast<double>(i) / static_cast<double>(kSampleRate);
            double phase_total = 0.0;
            if (patch.glide_pm != 1000 && length > 0) {
                if (i <= length) {
                    phase_total =
                        f * note_seconds / lg *
                        (std::pow(g, static_cast<double>(std::min(i, length)) / static_cast<double>(length)) - 1.0);
                } else {
                    phase_total = f * note_seconds / lg * (g - 1.0) + f * g * (t - note_seconds);
                }
            } else {
                phase_total = f * t;
            }
            const double phase = phase_total - std::floor(phase_total);
            double w = 0.0;
            switch (patch.wave) {
                case Wave::Sine:
                    w = std::sin(2.0 * kPi * phase);
                    break;
                case Wave::Square:
                    w = phase * 1000.0 < static_cast<double>(patch.duty_pm) ? 1.0 : -1.0;
                    break;
                case Wave::Saw:
                    w = 2.0 * phase - 1.0;
                    break;
                case Wave::Triangle:
                    w = 4.0 * std::fabs(phase - 0.5) - 1.0;
                    break;
                case Wave::Noise: {
                    const double cycle = std::floor(phase_total);
                    if (cycle != prev_cycle) {
                        state = xorshift(state);
                        held = static_cast<double>(static_cast<std::int32_t>(state)) / 2147483648.0;
                        prev_cycle = cycle;
                    }
                    w = held;
                    break;
                }
            }
            const double ms = static_cast<double>(i) * 1000.0 / static_cast<double>(kSampleRate);
            const double held_ms = std::min(ms, length_ms);
            double level = 0.0;
            if (held_ms < attack) {
                level = held_ms / attack;
            } else if (held_ms < attack + decay) {
                level = 1.0 - (1.0 - sustain) * (held_ms - attack) / decay;
            } else {
                level = sustain;
            }
            if (i >= length) {
                level = level * std::max(0.0, 1.0 - (ms - length_ms) / release);
            }
            const double gain = am_depth > 0.0 ? 1.0 - am_depth * (0.5 - 0.5 * std::cos(2.0 * kPi * am_hz * t)) : 1.0;
            out[static_cast<std::size_t>(i)] += w * level * gain / static_cast<double>(ratios.size());
        }
    }
    return out;
}

MusicRules::Choice choice_of(const Json& j) {
    MusicRules::Choice c;
    c.day = j.at("day").get<std::string>();
    c.night = j.value("night", "");
    return c;
}

}  // namespace

std::optional<MusicPiece> parse_music(std::string_view json_text, std::string& error) {
    try {
        const Json j = Json::parse(json_text);
        MusicPiece piece;
        piece.id = j.value("id", "");
        piece.tempo_bpm = j.at("tempo_bpm").get<int>();
        piece.bars = j.at("bars").get<int>();
        piece.volume_pm = j.at("volume_pm").get<int>();
        for (const Json& t : j.at("tracks")) {
            MusicTrack track;
            track.layer = t.at("layer").get<std::string>();
            track.volume_pm = t.at("volume_pm").get<int>();
            const Json& p = t.at("patch");
            const auto wave = wave_of(p.at("wave").get<std::string>());
            if (!wave) {
                error = "unknown wave";
                return std::nullopt;
            }
            track.patch.wave = *wave;
            track.patch.attack_ms = p.at("attack_ms").get<int>();
            track.patch.decay_ms = p.at("decay_ms").get<int>();
            track.patch.sustain_pm = p.at("sustain_pm").get<int>();
            track.patch.release_ms = p.at("release_ms").get<int>();
            track.patch.duty_pm = p.value("duty_pm", 500);
            track.patch.detune_cents = p.value("detune_cents", 0);
            track.patch.glide_pm = p.value("glide_pm", 1000);
            track.patch.am_dhz = p.value("am_dhz", 0);
            track.patch.am_depth_pm = p.value("am_depth_pm", 0);
            for (const Json& bar : t.at("bars")) {
                track.bars.push_back(bar.get<std::string>());
            }
            if (track.bars.empty()) {
                error = "a track without bars";
                return std::nullopt;
            }
            piece.tracks.push_back(std::move(track));
        }
        return piece;
    } catch (const Json::exception& e) {
        error = e.what();
        return std::nullopt;
    }
}

std::map<std::string, std::vector<std::int16_t>> render_music(const MusicPiece& piece) {
    const double step_samples = static_cast<double>(kSampleRate) * 60.0 / (static_cast<double>(piece.tempo_bpm) * 4.0);
    const int n = static_cast<int>(std::floor(static_cast<double>(piece.bars * kStepsPerBar) * step_samples));
    const double master = static_cast<double>(piece.volume_pm) / 1000.0;
    std::map<std::string, std::vector<double>> mixes;
    for (const MusicTrack& track : piece.tracks) {
        std::vector<double>& buf = mixes.try_emplace(track.layer, static_cast<std::size_t>(n), 0.0).first->second;
        const double volume = static_cast<double>(track.volume_pm) / 1000.0;
        const int release_samples =
            static_cast<int>(static_cast<double>(track.patch.release_ms) * kSampleRate / 1000.0);
        std::uint64_t index = 0;
        for (const NoteEvent& note : events_of(track, piece.bars)) {
            const int start = static_cast<int>(std::floor(static_cast<double>(note.first) * step_samples));
            const int held =
                static_cast<int>(std::floor(static_cast<double>(note.first + note.length) * step_samples)) - start;
            const int total = held + release_samples;
            const auto seed = static_cast<std::uint32_t>((2463534242ULL + 2654435761ULL * index) & 0xFFFFFFFFULL);
            const double scale = volume / std::sqrt(static_cast<double>(note.chord.size()));
            for (const std::string& name : note.chord) {
                const std::vector<double> samples = voice(track.patch, note_frequency(name), held, total, seed);
                for (int i = 0; i < total; ++i) {
                    buf[static_cast<std::size_t>((start + i) % n)] += samples[static_cast<std::size_t>(i)] * scale;
                }
            }
            ++index;
        }
    }
    std::map<std::string, std::vector<std::int16_t>> out;
    for (const auto& [layer, buf] : mixes) {
        std::vector<std::int16_t> samples(buf.size());
        for (std::size_t i = 0; i < buf.size(); ++i) {
            const double x = std::clamp(buf[i] * master, -1.0, 1.0);
            samples[i] = static_cast<std::int16_t>(std::floor(x * 32767.0 + 0.5));
        }
        out[layer] = std::move(samples);
    }
    return out;
}

std::optional<MusicRules> parse_music_rules(std::string_view json_text, std::string& error) {
    try {
        const Json j = Json::parse(json_text);
        MusicRules rules;
        rules.title = j.at("title").get<std::string>();
        rules.dead = j.at("dead").get<std::string>();
        rules.default_region = j.at("default_region").get<std::string>();
        for (const Json& q : j.at("quests")) {
            rules.quests.emplace_back(q.at("quest").get<std::string>(), q.at("piece").get<std::string>());
        }
        for (const auto& [name, entry] : j.at("places").items()) {
            rules.places[name] = choice_of(entry);
        }
        for (const auto& [name, entry] : j.at("regions").items()) {
            rules.regions[name] = choice_of(entry);
        }
        return rules;
    } catch (const Json::exception& e) {
        error = e.what();
        return std::nullopt;
    }
}

MusicChoice MusicDirector::update(const MusicContext& ctx) {
    for (const SoundCue& cue : ctx.cues) {
        if (cue.kind == "gather") {
            continue;
        }
        const bool near = std::hypot(cue.x - ctx.x, cue.y - ctx.y) <= kFightRangeTiles;
        if (cue.kind == "hit" || cue.kind == "hurt" || near) {
            m_last_fight_ = ctx.frame;
            const bool big =
                cue.family == "king" || cue.family == "matron" || cue.family == "alpha" || cue.family == "knight";
            if (big && cue.kind != "die") {
                m_last_boss_ = ctx.frame;
            }
        }
    }
    const bool fight = ctx.frame - m_last_fight_ < kFightFrames;
    const bool boss = ctx.frame - m_last_boss_ < kBossFrames;
    MusicChoice choice;
    choice.piece = piece_for(ctx);
    choice.layers.push_back("base");
    if (ctx.low_hp) {
        choice.layers.push_back("tension");
    }
    if (fight || boss) {
        choice.layers.push_back("combat");
    }
    if (boss) {
        choice.layers.push_back("boss");
    }
    return choice;
}

std::string MusicDirector::piece_for(const MusicContext& ctx) const {
    if (ctx.screen == "title") {
        return m_rules_.title;
    }
    if (ctx.screen == "dead") {
        return m_rules_.dead;
    }
    for (const auto& [quest, piece] : m_rules_.quests) {
        if (std::find(ctx.quests.begin(), ctx.quests.end(), quest) != ctx.quests.end() && ctx.place != "dungeon") {
            return piece;
        }
    }
    const bool day = ctx.tod_pm >= 250 && ctx.tod_pm <= 750;
    const auto place = m_rules_.places.find(ctx.place);
    if (place != m_rules_.places.end()) {
        return day || place->second.night.empty() ? place->second.day : place->second.night;
    }
    auto region = m_rules_.regions.find(ctx.region);
    if (region == m_rules_.regions.end()) {
        region = m_rules_.regions.find(m_rules_.default_region);
    }
    if (region == m_rules_.regions.end()) {
        return std::string();
    }
    return day ? region->second.day : region->second.night;
}

}  // namespace aether
