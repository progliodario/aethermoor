#pragma once

// Turns a generated world into the tile map the simulation plays on.

#include "core/worldgen.hpp"
#include "sim/tilemap.hpp"

namespace aether {

TileMap make_tilemap(const GeneratedWorld& world, const WorldParams& params);

}  // namespace aether
