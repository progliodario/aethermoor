#include "app/sound_board.hpp"

#include <algorithm>
#include <chrono>

#include "audio/synth.hpp"

namespace aether {

namespace {
constexpr int kChunk = 512;          // samples mixed per step
constexpr int kTargetQueued = 2048;  // samples we try to keep queued (about 90 ms)
constexpr float kFadeStep = 1.0F / (1.5F * static_cast<float>(kSampleRate));       // a loop fades in or out in 1.5 s
constexpr float kMusicFadeStep = 1.0F / (2.5F * static_cast<float>(kSampleRate));  // a piece takes over in 2.5 s
constexpr float kMusicBus = 0.5F;  // the music is quieter than the effects
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
    m_pack_ = &pack;
    if (const auto rules_text = pack.read_document("base:audio/music_rules")) {
        m_music_rules_ = parse_music_rules(*rules_text, error);
    }
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
        for (MusicLoop& music : m_music_) {
            music.target = 0.0F;
        }
        m_music_wanted_.clear();
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

void SoundBoard::set_music(const std::string& piece, const std::vector<std::string>& layers) {
    m_music_layers_ = layers;
    if (m_stream_ == nullptr || m_pack_ == nullptr) {
        return;
    }
    if (m_muted_) {
        m_music_wanted_.clear();
        for (MusicLoop& loop : m_music_) {
            loop.target = 0.0F;
        }
        return;
    }
    if (piece == m_music_wanted_ || piece.empty()) {
        return;
    }
    m_music_wanted_ = piece;
}

void SoundBoard::update_music() {
    // A finished render becomes the newest piece; the others fade out.
    if (m_music_job_.valid() && m_music_job_.wait_for(std::chrono::seconds(0)) == std::future_status::ready) {
        const std::shared_ptr<Layers> layers = m_music_job_.get();
        if (layers && !layers->empty()) {
            for (MusicLoop& loop : m_music_) {
                loop.target = 0.0F;
            }
            MusicLoop loop;
            loop.piece = m_music_rendering_;
            loop.layers = layers;
            m_music_.push_back(std::move(loop));
        }
        m_music_rendering_.clear();
    }
    // Start rendering the piece that is wanted, when it is not the one being heard or rendered.
    const std::string newest = m_music_.empty() ? std::string() : m_music_.back().piece;
    if (!m_music_wanted_.empty() && m_music_wanted_ != newest && m_music_wanted_ != m_music_rendering_ &&
        !m_music_job_.valid()) {
        const auto text = m_pack_->read_document("base:audio/music/" + m_music_wanted_);
        if (text) {
            m_music_rendering_ = m_music_wanted_;
            m_music_job_ = std::async(std::launch::async, [json = *text]() -> std::shared_ptr<Layers> {
                std::string error;
                const auto piece = parse_music(json, error);
                if (!piece) {
                    return nullptr;
                }
                return std::make_shared<Layers>(render_music(*piece));
            });
        } else {
            m_music_wanted_.clear();
        }
    }
    // The old pieces are gone when they are silent.
    m_music_.erase(std::remove_if(m_music_.begin(), m_music_.end(),
                                  [](const MusicLoop& l) { return l.target == 0.0F && l.gain <= 0.0F; }),
                   m_music_.end());
}

void SoundBoard::frame() {
    update_music();
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
            for (MusicLoop& music : m_music_) {
                music.gain += std::clamp(music.target - music.gain, -kMusicFadeStep, kMusicFadeStep);
                for (const auto& [layer, samples] : *music.layers) {
                    float& layer_gain = music.layer_gain[layer];
                    const bool on =
                        &music == &m_music_.back() &&
                        std::find(m_music_layers_.begin(), m_music_layers_.end(), layer) != m_music_layers_.end();
                    layer_gain += std::clamp((on ? 1.0F : 0.0F) - layer_gain, -kFadeStep, kFadeStep);
                    if (layer_gain > 0.0F && music.gain > 0.0F) {
                        sum += static_cast<float>(samples[music.position % samples.size()]) * music.gain * layer_gain *
                               kMusicBus;
                    }
                }
                ++music.position;
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
