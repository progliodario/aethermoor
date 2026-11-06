#pragma once

// Vector art recipes. Spec: docs/spec/13-vector-art.md. Schema: schemas/art_recipe.schema.json.

#include <array>
#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace aether {

struct Color {
    float r = 0.0F;
    float g = 0.0F;
    float b = 0.0F;
    float a = 0.0F;
};

// "#RRGGBB" or "#RRGGBBAA". Returns false (and leaves `out` untouched) for anything else.
bool parse_hex_color(std::string_view text, Color& out);

struct GradientStop {
    float t = 0.0F;
    std::string color;  // "#..." or "$p.name"
};

struct Paint {
    enum class Kind { None, Solid, Linear, Radial };
    Kind kind = Kind::None;
    std::string color;                                 // Solid
    float x0 = 0.0F, y0 = 0.0F, x1 = 0.0F, y1 = 0.0F;  // Linear
    float cx = 0.0F, cy = 0.0F, r = 0.0F;              // Radial
    std::vector<GradientStop> stops;                   // Linear and Radial
};

struct Shape {
    enum class Kind { Rect, Ellipse, Polygon, Path };
    Kind kind = Kind::Rect;
    std::array<float, 4> v{};                     // Rect: x y w h. Ellipse: cx cy rx ry
    std::vector<std::pair<float, float>> points;  // Polygon
    std::string path;                             // Path
};

struct StrokeStyle {
    bool present = false;
    std::string color;
    float width = 0.0F;
};

struct Layer {
    Shape shape;
    Paint fill;
    StrokeStyle stroke;
    float alpha = 1.0F;
    std::vector<std::string> only;    // drawn only with one of these variants (empty: always)
    std::vector<std::string> except;  // not drawn with one of these variants
};

using Palette = std::map<std::string, std::string, std::less<>>;

struct Recipe {
    std::string id;
    float width = 0.0F;
    float height = 0.0F;
    float origin_x = 0.0F;
    float origin_y = 0.0F;
    Palette palette;
    std::map<std::string, Palette, std::less<>> variants;
    std::vector<Layer> layers;
};

// Parses a recipe from JSON text. On failure returns nullopt and sets `error`.
std::optional<Recipe> parse_recipe(std::string_view json_text, std::string& error);

}  // namespace aether
