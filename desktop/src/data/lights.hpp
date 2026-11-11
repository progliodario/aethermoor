#pragma once

// The props that shine at night (spec 08, "Lights"): data/base/lights.json. Presentation only.

#include <array>
#include <string>
#include <vector>

namespace aether {

class Pack;

struct LightDef {
    std::string art;      // the prop that shines
    float radius = 3.5F;  // in tiles
    int r = 255;
    int g = 200;
    int b = 112;
    int strength_pm = 600;  // how bright, at full night
    int flicker_pm = 0;     // how much it wavers
};

// The lights of the pack; none when it has no table or the table is broken.
std::vector<LightDef> load_lights(const Pack& pack);

// The colour of the hour (spec 08): what the world is multiplied by at night and at twilight, the vignette and the
// motes.
struct Grading {
    std::array<int, 3> night{0x57, 0x66, 0xC7};
    std::array<int, 3> twilight{0xFF, 0xCC, 0x9E};
    int vignette_pm = 280;
    int motes = 26;
    std::array<int, 3> mote_day{0xFF, 0xF6, 0xC8};
    std::array<int, 3> mote_night{0xC8, 0xFF, 0x8A};
};

// The grading of the pack (`grading` of base:lights/all); the defaults for what it does not say.
Grading load_grading(const Pack& pack);

}  // namespace aether
