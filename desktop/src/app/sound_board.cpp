#include "app/sound_board.hpp"

#include <algorithm>

#include "audio/synth.hpp"

namespace aether {

namespace {
constexpr int kChunk = 512;          // samples mixed per step
constexpr int kTargetQueued = 2048;  // samples we try to keep queued (about 90 ms)
}  // namespace

SoundBoard::~SoundBoard() {
    if (m_stream_ != nullptr) {
        SDL_DestroyAudioStream(m_stream_);
    }
}

bool SoundBoard::open(const Pack& pack, const std::vector<std::string>& names) {
    for (const std::string& name : names) {
        const auto text = pack.read_document("base:audio/sfx/" + name);
        if (!text) {
            continue;
        }
        std::string error;
        const auto recipe = parse_sfx(*text, error);
        if (recipe) {
            m_sounds_[name] = synthesize(*recipe);
        }
    }
    if (!SDL_InitSubSystem(SDL_INIT_AUDIO)) {
        return false;
    }
    SDL_AudioSpec spec{};
    spec.format = SDL_AUDIO_S16;
    spec.channels = 1;
    spec.freq = kSampleRate;
    m_stream_ = SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK, &spec, nullptr, nullptr);
    if (m_stream_ == nullptr) {
        return false;
    }
    SDL_ResumeAudioStreamDevice(m_stream_);
    return true;
}

void SoundBoard::set_muted(bool muted) {
    m_muted_ = muted;
    if (muted) {
        m_voices_.clear();
    }
}

void SoundBoard::play(std::string_view name) {
    if (m_stream_ == nullptr || m_muted_) {
        return;
    }
    const auto found = m_sounds_.find(name);
    if (found == m_sounds_.end() || found->second.empty()) {
        return;
    }
    if (m_voices_.size() >= kMaxVoices) {  // cut the oldest voice
        const auto oldest = std::min_element(m_voices_.begin(), m_voices_.end(),
                                             [](const Voice& a, const Voice& b) { return a.started < b.started; });
        m_voices_.erase(oldest);
    }
    m_voices_.push_back({&found->second, 0, ++m_counter_});
}

void SoundBoard::pump() {
    if (m_stream_ == nullptr) {
        return;
    }
    const int bytes_per_sample = static_cast<int>(sizeof(std::int16_t));
    for (int round = 0; round < 4; ++round) {
        if (SDL_GetAudioStreamQueued(m_stream_) / bytes_per_sample >= kTargetQueued) {
            return;
        }
        std::int16_t chunk[kChunk];
        for (int i = 0; i < kChunk; ++i) {
            int sum = 0;
            for (Voice& voice : m_voices_) {
                if (voice.position < voice.samples->size()) {
                    sum += (*voice.samples)[voice.position++];
                }
            }
            chunk[i] = static_cast<std::int16_t>(std::clamp(sum, -32767, 32767));
        }
        m_voices_.erase(std::remove_if(m_voices_.begin(), m_voices_.end(),
                                       [](const Voice& v) { return v.position >= v.samples->size(); }),
                        m_voices_.end());
        SDL_PutAudioStreamData(m_stream_, chunk, kChunk * bytes_per_sample);
    }
}

}  // namespace aether
