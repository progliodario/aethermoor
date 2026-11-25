#pragma once

// The levels of the graphics quality (spec 13, "Quality"): presentation only, the game is the same at every level.
// Keep in step with android/core/.../core/vector/Quality.kt and the table of the spec.

#include <array>
#include <cstddef>
#include <string_view>

namespace aether {

struct QualityLevel {
    std::string_view id;     // the value of "quality" in the settings file; the text is ui.quality_<id>
    int bucket_cap;          // the largest scale bucket the textures are baked at (spec 13, "Scale buckets")
    bool water;              // the moving water (spec 13, "Water")
    bool corners;            // the rounded corners of the ground blending (spec 13, "Ground blending")
    bool long_shadows;       // the long shadows of dawn and dusk (spec 08, "The colour of the hour")
    int texture_budget_mib;  // all the art of the pack baked once at bucket_cap fits in this (tested)
};

inline constexpr std::array<QualityLevel, 3> kQualityLevels = {{
    {"low", 64, false, false, false, 32},
    {"normal", 128, true, true, true, 128},
    {"high", 256, true, true, true, 512},
}};

// The index of the level `id`, or `fallback` when there is none.
inline int quality_index(std::string_view id, int fallback) {
    for (std::size_t i = 0; i < kQualityLevels.size(); ++i) {
        if (kQualityLevels[i].id == id) {
            return static_cast<int>(i);
        }
    }
    return fallback;
}

}  // namespace aether
