#pragma once

// The hints of the first minutes (spec 16, "Hints"): data/base/hints.json. Presentation only.

#include <string>
#include <vector>

namespace aether {

class Pack;

struct HintDef {
    std::string id;          // the hint is shown once a game: the story flag `hint_<id>` remembers it
    std::string when;        // what must be true: start, quest, enemy_near, gather, hurt, stone, talent_points, night,
                             // companion, renown
    std::string text;        // an $i18n: key, for a keyboard
    std::string text_touch;  // an $i18n: key, for a touch screen; empty: `text`
};

// The hints of the pack in the order of the data; none when it has no table or the table is broken.
std::vector<HintDef> load_hints(const Pack& pack);

// The credits (spec 16, "Credits"): data/base/credits.json, the lines to show in order. A heading is marked; a line is
// an $i18n: key or a text shown as it is.
struct CreditLine {
    std::string text;
    bool heading = false;
};
std::vector<CreditLine> load_credits(const Pack& pack);

}  // namespace aether
