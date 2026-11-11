#pragma once

// The font of the interface (spec 13, "Font"): data/base/fonts/aether.json. Presentation only.

#include <map>
#include <string>

namespace aether {

class Pack;

struct FontGlyph {
    float width = 0.0F;  // what the glyph takes in a line of text, in font units
    std::string path;    // its strokes, in the cell (empty: nothing to draw, a space)
};

struct FontDef {
    float cell_w = 8.0F;  // the cell every glyph is drawn in
    float cell_h = 11.0F;
    float top = 1.5F;  // the room above the top of the caps
    float stroke = 0.95F;
    std::map<int, FontGlyph> glyphs;  // by Unicode code point

    bool loaded() const { return !glyphs.empty(); }
};

// The font of the pack; empty (not loaded) when the pack has none or it is broken.
FontDef load_font(const Pack& pack);

// The first code point of a UTF-8 text and how many bytes it takes (1 for a broken sequence, with the code of '?').
int utf8_code_point(const char* text, int& length);

}  // namespace aether
