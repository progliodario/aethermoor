#pragma once

// Software rasterizer for vector art recipes. Spec: docs/spec/13-vector-art.md (normative algorithm).

#include <cstdint>
#include <string_view>
#include <vector>

#include "vector/recipe.hpp"

namespace aether {

struct Bitmap {
    int width = 0;
    int height = 0;
    std::vector<std::uint8_t> rgba;  // width * height * 4, straight (non-premultiplied) alpha
};

// Renders `recipe` at `scale` pixels per art unit, using the palette of `variant` when it exists.
Bitmap rasterize(const Recipe& recipe, float scale, std::string_view variant = {});

}  // namespace aether
