#include "audio/synth.hpp"

#include <algorithm>
#include <cmath>

#include <nlohmann/json.hpp>

namespace aether {

namespace {

using Json = nlohmann::json;

std::optional<Wave> parse_wave(const std::string& name) {
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

}  // namespace

std::optional<SfxRecipe> parse_sfx(std::string_view json_text, std::string& error) {
    try {
        const Json j = Json::parse(json_text);
        SfxRecipe recipe;
        recipe.id = j.value("id", "");
        recipe.duration_ms = j.at("duration_ms").get<int>();
        recipe.volume_pm = j.at("volume_pm").get<int>();
        for (const Json& l : j.at("layers")) {
            SfxLayer layer;
            const auto wave = parse_wave(l.at("wave").get<std::string>());
            if (!wave) {
                error = "unknown wave";
                return std::nullopt;
            }
            layer.wave = *wave;
            layer.freq_start = l.at("freq_start").get<int>();
            layer.freq_end = l.at("freq_end").get<int>();
            layer.volume_pm = l.at("volume_pm").get<int>();
            layer.duty_pm = l.value("duty_pm", 500);
            layer.attack_ms = l.at("attack_ms").get<int>();
            layer.decay_ms = std::max(1, l.at("decay_ms").get<int>());
            recipe.layers.push_back(layer);
        }
        return recipe;
    } catch (const Json::exception& e) {
        error = e.what();
        return std::nullopt;
    }
}

std::vector<std::int16_t> synthesize(const SfxRecipe& recipe) {
    const int n = recipe.duration_ms * kSampleRate / 1000;
    const double master = static_cast<double>(recipe.volume_pm) / 1000.0;
    std::vector<double> mix(static_cast<std::size_t>(std::max(0, n)), 0.0);
    constexpr double kPi = 3.14159265358979323846;
    for (const SfxLayer& layer : recipe.layers) {
        const double fs = static_cast<double>(layer.freq_start);
        const double fe = static_cast<double>(layer.freq_end);
        const double ratio_log = std::log(fe / fs);
        const double attack = static_cast<double>(layer.attack_ms);
        const double decay = static_cast<double>(layer.decay_ms);
        const double volume = static_cast<double>(layer.volume_pm) / 1000.0;
        double phase = 0.0;
        std::uint32_t state = 2463534242U;
        double held = 0.0;
        bool wrapped = true;
        for (int i = 0; i < n; ++i) {
            const double t = static_cast<double>(i) / static_cast<double>(n);
            const double freq = layer.freq_start == layer.freq_end ? fs : fs * std::exp(t * ratio_log);
            double w = 0.0;
            switch (layer.wave) {
                case Wave::Sine:
                    w = std::sin(2.0 * kPi * phase);
                    break;
                case Wave::Square:
                    w = phase * 1000.0 < static_cast<double>(layer.duty_pm) ? 1.0 : -1.0;
                    break;
                case Wave::Saw:
                    w = 2.0 * phase - 1.0;
                    break;
                case Wave::Triangle:
                    w = 4.0 * std::fabs(phase - 0.5) - 1.0;
                    break;
                case Wave::Noise:
                    if (wrapped) {
                        state = xorshift(state);
                        held = static_cast<double>(static_cast<std::int32_t>(state)) / 2147483648.0;
                    }
                    w = held;
                    break;
            }
            phase += freq / static_cast<double>(kSampleRate);
            wrapped = phase >= 1.0;
            if (wrapped) {
                phase -= 1.0;
            }
            const double ms = static_cast<double>(i) * 1000.0 / static_cast<double>(kSampleRate);
            const double env = ms < attack ? ms / attack : std::max(0.0, 1.0 - (ms - attack) / decay);
            mix[static_cast<std::size_t>(i)] += w * env * volume;
        }
    }
    std::vector<std::int16_t> out(mix.size());
    for (std::size_t i = 0; i < mix.size(); ++i) {
        const double x = std::clamp(mix[i] * master, -1.0, 1.0);
        out[i] = static_cast<std::int16_t>(std::floor(x * 32767.0 + 0.5));
    }
    return out;
}

}  // namespace aether
