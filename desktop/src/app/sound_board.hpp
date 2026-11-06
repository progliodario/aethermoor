#pragma once

// Plays the sound effects of the pack: synthesizes them once (spec 14), mixes up to 16 voices and feeds an SDL audio
// stream. The only audio code that links SDL3. If there is no audio device the board stays silent.

#include <SDL3/SDL.h>

#include <cstdint>
#include <map>
#include <string>
#include <string_view>
#include <vector>

#include "data/pack.hpp"

namespace aether {

class SoundBoard {
public:
    SoundBoard() = default;
    ~SoundBoard();
    SoundBoard(const SoundBoard&) = delete;
    SoundBoard& operator=(const SoundBoard&) = delete;

    // Opens the default playback device and renders the sounds of the pack. Returns false when there is no device.
    bool open(const Pack& pack, const std::vector<std::string>& names);
    // Starts a sound by its short name (`hit` is `base:audio/sfx/hit`). Does nothing when muted or unknown.
    void play(std::string_view name);
    // Keeps the audio stream filled; call it once per frame.
    void pump();
    void set_muted(bool muted);
    bool muted() const { return m_muted_; }

private:
    struct Voice {
        const std::vector<std::int16_t>* samples = nullptr;
        std::size_t position = 0;
        std::uint64_t started = 0;
    };

    static constexpr std::size_t kMaxVoices = 16;
    SDL_AudioStream* m_stream_ = nullptr;
    std::map<std::string, std::vector<std::int16_t>, std::less<>> m_sounds_;
    std::vector<Voice> m_voices_;
    std::uint64_t m_counter_ = 0;
    bool m_muted_ = false;
};

}  // namespace aether
