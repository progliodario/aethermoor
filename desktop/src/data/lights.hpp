#pragma once

// The props that shine at night (spec 08, "Lights"): data/base/lights.json. Presentation only.

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

}  // namespace aether
