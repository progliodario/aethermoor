#pragma once

// The chunks of a streamed world that are loaded right now. Spec: docs/spec/09-worldgen.md ("Streaming").

#include <cstdint>
#include <functional>
#include <map>
#include <utility>
#include <vector>

#include "core/worldgen.hpp"
#include "sim/tilemap.hpp"

namespace aether {

// Chunks around the player's chunk (Chebyshev distance) that are active: a 5 x 5 window.
constexpr int kActiveRadius = 2;
// Loaded chunks farther than this are dropped (the extra ring avoids regenerating at a border).
constexpr int kKeepRadius = 3;

// Chunk of a tile coordinate (floor division, also for negative tiles).
inline int chunk_of(int tile) { return tile >> 5; }
static_assert(kChunkSize == 32, "chunk_of assumes 32 tiles per chunk");

struct Chunk {
    int cx = 0;
    int cy = 0;
    std::vector<int> tiles;                     // kChunkSize * kChunkSize gids
    std::vector<bool> solid;                    // same layout
    std::vector<Prop> props;                    // feet positions in tiles
    std::vector<std::pair<int, int>> spawners;  // absolute tile coordinates, scan order
};

class ChunkStore {
public:
    ChunkStore(WorldParams params, std::uint64_t seed, const Tileset& tileset);

    // Loads the chunks within kActiveRadius of (cx, cy) and drops those beyond kKeepRadius.
    void keep_around(int cx, int cy);

    const Chunk* find(int cx, int cy) const;
    // The gid at the tile, 0 when its chunk is not loaded.
    int gid_at(int x, int y) const;
    // Tiles of chunks that are not loaded are solid.
    bool solid(int x, int y) const;

    // Calls `fn` for every prop of the chunk of (x, y) and its eight neighbours.
    void for_each_prop_near(float x, float y, const std::function<void(const Prop&)>& fn) const;
    // Calls `fn` for every prop of the loaded chunks inside the rectangle (in tiles).
    void for_each_prop_in(float x0, float y0, float x1, float y1, const std::function<void(const Prop&)>& fn) const;

    std::size_t loaded() const { return m_chunks_.size(); }
    const WorldParams& params() const { return m_params_; }
    std::uint64_t seed() const { return m_seed_; }

private:
    const Chunk& load(int cx, int cy);

    WorldParams m_params_;
    std::uint64_t m_seed_;
    const Tileset* m_tileset_;
    std::map<std::pair<int, int>, Chunk> m_chunks_;
};

}  // namespace aether
