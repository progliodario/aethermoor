#pragma once

// Plays the sounds of the pack: renders them once (spec 14), mixes the sound effects (up to 16 voices) and the looping
// ambience, and feeds an SDL audio stream. The only audio code that links SDL3. If there is no audio device the board
// stays silent.

#include <SDL3/SDL.h>

#include <cstdint>
#include <future>
#include <map>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include "audio/events.hpp"
#include "audio/music.hpp"
#include "data/pack.hpp"

namespace aether {

class SoundBoard {
public:
    SoundBoard() = default;
    ~SoundBoard();
    SoundBoard(const SoundBoard&) = delete;
    SoundBoard& operator=(const SoundBoard&) = delete;

    // Reads the event table of the pack, renders its sounds and opens the default playback device. Returns false when
    // there is no table or no device.
    bool open(const Pack& pack);
    // Plays the sound of an event (`swing`, `step.grass`, `enemy.wolf.hit`...), `volume_pm` loud. Does nothing when
    // muted.
    void play_event(const std::string& event, int volume_pm = 1000);
    // The loops that should be heard, with their gain in permille; the others fade out.
    void set_ambience(const std::map<std::string, int>& gains);
    // The rules of the ambience of the pack.
    const AmbienceRules& ambience_rules() const { return m_table_.ambience; }
    // The music: the piece that should play and the layers that are on. A new piece is rendered in the background and
    // then takes over with a crossfade; the layers fade in and out.
    void set_music(const std::string& piece, const std::vector<std::string>& layers);
    // The rules that choose the piece, or nullptr when the pack has none.
    const MusicRules* music_rules() const { return m_music_rules_ ? &*m_music_rules_ : nullptr; }
    // Call once per frame: counts down the cooldowns and keeps the audio stream filled.
    void frame();
    void set_muted(bool muted);
    bool muted() const { return m_muted_; }
    bool ready() const { return m_stream_ != nullptr; }

private:
    struct Voice {
        const std::vector<std::int16_t>* samples = nullptr;
        std::size_t position = 0;
        float gain = 1.0F;
        std::uint64_t started = 0;
    };
    struct Loop {
        const std::vector<std::int16_t>* samples = nullptr;
        std::size_t position = 0;
        float gain = 0.0F;
        float target = 0.0F;
    };

    using Layers = std::map<std::string, std::vector<std::int16_t>>;
    struct MusicLoop {
        std::string piece;
        std::shared_ptr<Layers> layers;
        std::size_t position = 0;
        float gain = 0.0F;
        float target = 1.0F;
        std::map<std::string, float> layer_gain;
    };

    void pump();
    void update_music();

    static constexpr std::size_t kMaxVoices = 16;
    SDL_AudioStream* m_stream_ = nullptr;
    EventTable m_table_;
    std::map<std::string, std::vector<std::int16_t>, std::less<>> m_sounds_;
    std::map<std::string, int, std::less<>> m_played_;    // how many times each event played (to rotate its variants)
    std::map<std::string, int, std::less<>> m_cooldown_;  // frames left before an event may play again
    std::vector<Voice> m_voices_;
    std::map<std::string, Loop, std::less<>> m_loops_;
    std::uint64_t m_counter_ = 0;
    const Pack* m_pack_ = nullptr;
    std::optional<MusicRules> m_music_rules_;
    std::vector<MusicLoop> m_music_;  // the pieces that are heard, the newest last
    std::string m_music_wanted_;      // the piece asked for
    std::string m_music_rendering_;   // the piece being rendered
    std::future<std::shared_ptr<Layers>> m_music_job_;
    std::vector<std::string> m_music_layers_;
    bool m_muted_ = false;
};

}  // namespace aether
