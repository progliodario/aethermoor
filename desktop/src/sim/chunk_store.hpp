#pragma once

// The chunks of a streamed world that are loaded right now. Spec: docs/spec/09-worldgen.md ("Streaming").

#include <condition_variable>
#include <cstdint>
#include <deque>
#include <functional>
#include <map>
#include <memory>
#include <mutex>
#include <set>
#include <thread>
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
    std::vector<GenPerson> people;              // settlement NPCs, scan order
};

class ChunkStore {
public:
    ChunkStore(WorldParams params, std::uint64_t seed, const Tileset& tileset);
    ~ChunkStore();
    ChunkStore(const ChunkStore&) = delete;
    ChunkStore& operator=(const ChunkStore&) = delete;

    // Starts a thread that generates ahead of time the ring of chunks just outside the window (spec 09, "Streaming";
    // item C4.1). keep_around takes a chunk from it when it is ready and generates it at once when it is not: the
    // chunks the simulation sees, and the tick in which it sees them, are the same with or without the thread.
    void start_prefetch();
    // Waits until the thread has generated every chunk asked of it (for the tests).
    void wait_prefetched();
    // How many chunks keep_around took from the thread (for the tests).
    std::size_t prefetched_taken() const { return m_taken_; }

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
    // What the thread of start_prefetch shares with the simulation, behind its mutex: the chunks asked, the one being
    // generated and those that are ready.
    struct Prefetch {
        std::mutex mutex;
        std::condition_variable wake;  // a chunk is asked, or the thread must stop
        std::condition_variable idle;  // nothing is asked or being generated
        std::deque<std::pair<int, int>> wanted;
        std::set<std::pair<int, int>> busy;
        std::map<std::pair<int, int>, GeneratedChunk> ready;
        bool stop = false;
        std::thread thread;
    };

    const Chunk& load(int cx, int cy);
    bool take_prefetched(int cx, int cy, GeneratedChunk& out);
    void ask_ring(int cx, int cy);
    static void run_prefetch(Prefetch& prefetch, WorldParams params, std::uint64_t seed);

    std::unique_ptr<Prefetch> m_prefetch_;
    std::size_t m_taken_ = 0;
    WorldParams m_params_;
    std::uint64_t m_seed_;
    const Tileset* m_tileset_;
    std::map<std::pair<int, int>, Chunk> m_chunks_;
};

}  // namespace aether
