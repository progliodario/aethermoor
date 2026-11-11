#include "data/font.hpp"

#include <nlohmann/json.hpp>

#include "data/pack.hpp"

namespace aether {

int utf8_code_point(const char* text, int& length) {
    const auto* p = reinterpret_cast<const unsigned char*>(text);
    const int lead = p[0];
    length = 1;
    if (lead < 0x80) {
        return lead;
    }
    if (lead >= 0xC0 && lead < 0xE0 && (p[1] & 0xC0) == 0x80) {
        length = 2;
        return ((lead & 0x1F) << 6) | (p[1] & 0x3F);
    }
    if (lead >= 0xE0 && lead < 0xF0 && (p[1] & 0xC0) == 0x80 && (p[2] & 0xC0) == 0x80) {
        length = 3;
        return ((lead & 0x0F) << 12) | ((p[1] & 0x3F) << 6) | (p[2] & 0x3F);
    }
    if (lead >= 0xF0 && lead < 0xF8 && (p[1] & 0xC0) == 0x80 && (p[2] & 0xC0) == 0x80 && (p[3] & 0xC0) == 0x80) {
        length = 4;
        return ((lead & 0x07) << 18) | ((p[1] & 0x3F) << 12) | ((p[2] & 0x3F) << 6) | (p[3] & 0x3F);
    }
    return '?';
}

FontDef load_font(const Pack& pack) {
    FontDef font;
    const auto text = pack.read_document("base:font/aether");
    if (!text) {
        return font;
    }
    const nlohmann::json doc = nlohmann::json::parse(*text, nullptr, /*allow_exceptions=*/false);
    if (doc.is_discarded() || !doc.contains("glyphs") || !doc.at("glyphs").is_object()) {
        return font;
    }
    if (doc.contains("cell") && doc.at("cell").is_object()) {
        font.cell_w = doc.at("cell").value("w", 8.0F);
        font.cell_h = doc.at("cell").value("h", 11.0F);
        font.top = doc.at("cell").value("top", 1.5F);
    }
    font.stroke = doc.value("stroke", 0.95F);
    for (const auto& [key, value] : doc.at("glyphs").items()) {
        if (key.empty() || !value.is_object()) {
            continue;
        }
        int length = 1;
        const int code = utf8_code_point(key.c_str(), length);
        FontGlyph glyph;
        glyph.width = value.value("w", font.cell_w);
        glyph.path = value.value("d", "");
        font.glyphs[code] = std::move(glyph);
    }
    return font;
}

}  // namespace aether
