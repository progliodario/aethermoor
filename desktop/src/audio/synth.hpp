#pragma once

// Sound effect synthesizer. Spec: docs/spec/14-audio.md (normative algorithm). Schema: schemas/sfx_recipe.schema.json.
// Headless: it produces 16 bit samples; playing them is the job of the app.

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace aether {

constexpr int kSampleRate = 22050;

enum class Wave { Sine, Square, Saw, Triangle, Noise };

struct SfxLayer {
    Wave wave = Wave::Sine;
    int freq_start = 440;
    int freq_end = 440;
    int volume_pm = 1000;
    int duty_pm = 500;
    int attack_ms = 0;
    int decay_ms = 1;
    int am_dhz = 0;       // amplitude modulation rate in tenths of a hertz
    int am_depth_pm = 0;  // and its depth
};

struct SfxRecipe {
    std::string id;
    int duration_ms = 0;
    int volume_pm = 1000;
    bool loop = false;  // an ambience: no envelope, meant to repeat
    std::vector<SfxLayer> layers;
};

// Parses a sound effect recipe from JSON text. On failure returns nullopt and sets `error`.
std::optional<SfxRecipe> parse_sfx(std::string_view json_text, std::string& error);

// Renders a recipe to mono samples at kSampleRate.
std::vector<std::int16_t> synthesize(const SfxRecipe& recipe);

}  // namespace aether
