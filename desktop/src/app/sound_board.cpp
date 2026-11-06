#include "app/sound_board.hpp"

#include <algorithm>

#include "audio/synth.hpp"

namespace aether {

namespace {
constexpr int kChunk = 512;          // samples mixed per step
constexpr int kTargetQueued = 2048;  // samples we try to keep queued (about 90 ms)
constexpr float kFadeStep = 1.0F / (1.5F * static_cast<float>(kSampleRate));  // a loop fades in or out in 1.5 s
}  // namespace

SoundBoard::~SoundBoard() {
    if (m_stream_ != nullptr) {
        SDL_DestroyAudioStream(m_stream_);
    }
}

bool SoundBoard::open(const Pack& pack) {
    const auto text = pack.read_document("base:audio/events");
    if (!text) {
        return false;
    }
    std::string error;
    auto table = parse_event_table(*text, error);
    if (!table) {
        return false;
    }
    m_table_ = std::move(*table);
    for (const std::string& name : m_table_.all_sounds()) {
        const auto sound = pack.read_document("base:audio/sfx/" + name);
        if (!sound) {
            continue;
        }
        const auto recipe = parse_sfx(*sound, error);
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
        for (auto& [name, loop] : m_loops_) {
            loop.target = 0.0F;
        }
    }
}

void SoundBoard::play_event(const std::string& event, int volume_pm) {
    if (m_stream_ == nullptr || m_muted_) {
        return;
    }
    const auto entry = m_table_.events.find(event);
    if (entry == m_table_.events.end() || entry->second.sounds.empty()) {
        return;
    }
    int& cooldown = m_cooldown_[event];
    if (cooldown > 0) {
        return;
    }
    cooldown = entry->second.cooldown;
    int& played = m_played_[event];
    const std::string& name = entry->second.sounds[static_cast<std::size_t>(played) % entry->second.sounds.size()];
    ++played;
    const auto sound = m_sounds_.find(name);
    if (sound == m_sounds_.end() || sound->second.empty()) {
        return;
    }
    if (m_voices_.size() >= kMaxVoices) {  // cut the oldest voice
        const auto oldest = std::min_element(m_voices_.begin(), m_voices_.end(),
                                             [](const Voice& a, const Voice& b) { return a.started < b.started; });
        m_voices_.erase(oldest);
    }
    const float gain = static_cast<float>(entry->second.volume_pm) * static_cast<float>(volume_pm) / 1.0e6F;
    Voice voice;
    voice.samples = &sound->second;
    voice.gain = gain;
    voice.started = ++m_counter_;
    m_voices_.push_back(voice);
}

void SoundBoard::set_ambience(const std::map<std::string, int>& gains) {
    for (auto& [name, loop] : m_loops_) {
        loop.target = 0.0F;
    }
    if (m_muted_) {
        return;
    }
    for (const auto& [name, gain] : gains) {
        const auto sound = m_sounds_.find(name);
        if (sound == m_sounds_.end() || sound->second.empty()) {
            continue;
        }
        Loop& loop = m_loops_[name];
        loop.samples = &sound->second;
        loop.target = static_cast<float>(gain) / 1000.0F;
    }
}

void SoundBoard::frame() {
    for (auto& [event, frames] : m_cooldown_) {
        frames = std::max(0, frames - 1);
    }
    pump();
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
            float sum = 0.0F;
            for (Voice& voice : m_voices_) {
                if (voice.position < voice.samples->size()) {
                    sum += static_cast<float>((*voice.samples)[voice.position++]) * voice.gain;
                }
            }
            for (auto& [name, loop] : m_loops_) {
                if (loop.gain == 0.0F && loop.target == 0.0F) {
                    continue;
                }
                loop.gain += std::clamp(loop.target - loop.gain, -kFadeStep, kFadeStep);
                sum += static_cast<float>((*loop.samples)[loop.position]) * loop.gain;
                loop.position = (loop.position + 1) % loop.samples->size();
            }
            chunk[i] = static_cast<std::int16_t>(std::clamp(sum, -32767.0F, 32767.0F));
        }
        m_voices_.erase(std::remove_if(m_voices_.begin(), m_voices_.end(),
                                       [](const Voice& v) { return v.position >= v.samples->size(); }),
                        m_voices_.end());
        SDL_PutAudioStreamData(m_stream_, chunk, kChunk * bytes_per_sample);
    }
}

}  // namespace aether
