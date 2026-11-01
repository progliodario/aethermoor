#pragma once

// Turns a generated world into the tile map the simulation plays on.

#include "core/worldgen.hpp"
#include "sim/tilemap.hpp"

namespace aether {

TileMap make_tilemap(const GeneratedWorld& world, const WorldParams& params);

// The map of a streamed world: only its size, the spawn and the NPCs (tiles, props and enemies come from the chunks).
TileMap make_stream_map(const WorldParams& params);

}  // namespace aether
