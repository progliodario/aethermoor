#include "sim/chunk_store.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>

namespace aether {

ChunkStore::ChunkStore(WorldParams params, std::uint64_t seed, const Tileset& tileset)
    : m_params_(std::move(params)), m_seed_(seed), m_tileset_(&tileset) {}

const Chunk& ChunkStore::load(int cx, int cy) {
    const auto found = m_chunks_.find({cx, cy});
    if (found != m_chunks_.end()) {
        return found->second;
    }
    GeneratedChunk generated = generate_chunk(m_seed_, m_params_, cx, cy);
    Chunk chunk;
    chunk.cx = cx;
    chunk.cy = cy;
    chunk.solid.reserve(generated.tiles.size());
    for (const int gid : generated.tiles) {
        const auto tile = m_tileset_->tiles.find(gid);
        chunk.solid.push_back(tile != m_tileset_->tiles.end() && tile->second.solid);
    }
    chunk.tiles = std::move(generated.tiles);
    chunk.props.reserve(generated.props.size());
    for (const GenProp& p : generated.props) {
        chunk.props.push_back({p.art, static_cast<float>(p.x256) / 256.0F, static_cast<float>(p.y256) / 256.0F,
                               static_cast<float>(p.radius_x100) / 100.0F});
    }
    chunk.spawners = std::move(generated.spawners);
    chunk.people = std::move(generated.people);
    return m_chunks_.emplace(std::make_pair(cx, cy), std::move(chunk)).first->second;
}

void ChunkStore::keep_around(int cx, int cy) {
    for (int j = cy - kActiveRadius; j <= cy + kActiveRadius; ++j) {
        for (int i = cx - kActiveRadius; i <= cx + kActiveRadius; ++i) {
            load(i, j);
        }
    }
    for (auto it = m_chunks_.begin(); it != m_chunks_.end();) {
        if (std::max(std::abs(it->first.first - cx), std::abs(it->first.second - cy)) > kKeepRadius) {
            it = m_chunks_.erase(it);
        } else {
            ++it;
        }
    }
}

const Chunk* ChunkStore::find(int cx, int cy) const {
    const auto found = m_chunks_.find({cx, cy});
    return found == m_chunks_.end() ? nullptr : &found->second;
}

int ChunkStore::gid_at(int x, int y) const {
    const Chunk* chunk = find(chunk_of(x), chunk_of(y));
    if (chunk == nullptr) {
        return 0;
    }
    return chunk->tiles[static_cast<std::size_t>((y & 31) * kChunkSize + (x & 31))];
}

bool ChunkStore::solid(int x, int y) const {
    const Chunk* chunk = find(chunk_of(x), chunk_of(y));
    if (chunk == nullptr) {
        return true;
    }
    return chunk->solid[static_cast<std::size_t>((y & 31) * kChunkSize + (x & 31))];
}

void ChunkStore::for_each_prop_near(float x, float y, const std::function<void(const Prop&)>& fn) const {
    const int cx = chunk_of(static_cast<int>(std::floor(x)));
    const int cy = chunk_of(static_cast<int>(std::floor(y)));
    for (int j = cy - 1; j <= cy + 1; ++j) {
        for (int i = cx - 1; i <= cx + 1; ++i) {
            if (const Chunk* chunk = find(i, j)) {
                for (const Prop& prop : chunk->props) {
                    fn(prop);
                }
            }
        }
    }
}

void ChunkStore::for_each_prop_in(float x0, float y0, float x1, float y1,
                                  const std::function<void(const Prop&)>& fn) const {
    const int cx0 = chunk_of(static_cast<int>(std::floor(x0)));
    const int cx1 = chunk_of(static_cast<int>(std::floor(x1)));
    const int cy0 = chunk_of(static_cast<int>(std::floor(y0)));
    const int cy1 = chunk_of(static_cast<int>(std::floor(y1)));
    for (int j = cy0; j <= cy1; ++j) {
        for (int i = cx0; i <= cx1; ++i) {
            if (const Chunk* chunk = find(i, j)) {
                for (const Prop& prop : chunk->props) {
                    if (prop.x >= x0 && prop.x <= x1 && prop.y >= y0 && prop.y <= y1) {
                        fn(prop);
                    }
                }
            }
        }
    }
}

}  // namespace aether
