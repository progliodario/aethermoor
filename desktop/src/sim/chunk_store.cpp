#include "sim/chunk_store.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iterator>

namespace aether {

ChunkStore::ChunkStore(WorldParams params, std::uint64_t seed, const Tileset& tileset)
    : m_params_(std::move(params)), m_seed_(seed), m_tileset_(&tileset) {}

ChunkStore::~ChunkStore() {
    if (m_prefetch_) {
        {
            const std::lock_guard<std::mutex> lock(m_prefetch_->mutex);
            m_prefetch_->stop = true;
        }
        m_prefetch_->wake.notify_all();
        m_prefetch_->thread.join();
    }
}

void ChunkStore::start_prefetch() {
    if (m_prefetch_) {
        return;
    }
    m_prefetch_ = std::make_unique<Prefetch>();
    // the thread has its own copy of the parameters: it shares nothing with the simulation but the queues
    m_prefetch_->thread = std::thread(run_prefetch, std::ref(*m_prefetch_), m_params_, m_seed_);
}

void ChunkStore::run_prefetch(Prefetch& prefetch, WorldParams params, std::uint64_t seed) {
    for (;;) {
        std::pair<int, int> at;
        {
            std::unique_lock<std::mutex> lock(prefetch.mutex);
            prefetch.wake.wait(lock, [&prefetch] { return prefetch.stop || !prefetch.wanted.empty(); });
            if (prefetch.stop) {
                return;
            }
            at = prefetch.wanted.front();
            prefetch.wanted.pop_front();
            prefetch.busy.insert(at);
        }
        GeneratedChunk generated = generate_chunk(seed, params, at.first, at.second);
        bool idle = false;
        {
            const std::lock_guard<std::mutex> lock(prefetch.mutex);
            prefetch.busy.erase(at);
            prefetch.ready.insert_or_assign(at, std::move(generated));
            idle = prefetch.wanted.empty() && prefetch.busy.empty();
        }
        if (idle) {
            prefetch.idle.notify_all();
        }
    }
}

void ChunkStore::wait_prefetched() {
    if (!m_prefetch_) {
        return;
    }
    std::unique_lock<std::mutex> lock(m_prefetch_->mutex);
    m_prefetch_->idle.wait(lock, [this] { return m_prefetch_->wanted.empty() && m_prefetch_->busy.empty(); });
}

bool ChunkStore::take_prefetched(int cx, int cy, GeneratedChunk& out) {
    if (!m_prefetch_) {
        return false;
    }
    const std::lock_guard<std::mutex> lock(m_prefetch_->mutex);
    const auto found = m_prefetch_->ready.find({cx, cy});
    if (found == m_prefetch_->ready.end()) {
        return false;  // not asked, or not done yet: keep_around generates it at once
    }
    out = std::move(found->second);
    m_prefetch_->ready.erase(found);
    ++m_taken_;
    return true;
}

// Asks the thread for the ring just outside the window around (cx, cy), the chunks the next step of the player brings
// into it, and forgets what is asked or ready farther away.
void ChunkStore::ask_ring(int cx, int cy) {
    if (!m_prefetch_) {
        return;
    }
    const auto far = [cx, cy](const std::pair<int, int>& c) {
        return std::max(std::abs(c.first - cx), std::abs(c.second - cy)) > kKeepRadius;
    };
    {
        const std::lock_guard<std::mutex> lock(m_prefetch_->mutex);
        std::deque<std::pair<int, int>>& wanted = m_prefetch_->wanted;
        wanted.erase(std::remove_if(wanted.begin(), wanted.end(), far), wanted.end());
        for (auto it = m_prefetch_->ready.begin(); it != m_prefetch_->ready.end();) {
            it = far(it->first) ? m_prefetch_->ready.erase(it) : std::next(it);
        }
        constexpr int kRing = kActiveRadius + 1;
        for (int j = cy - kRing; j <= cy + kRing; ++j) {
            for (int i = cx - kRing; i <= cx + kRing; ++i) {
                const std::pair<int, int> at{i, j};
                if (std::max(std::abs(i - cx), std::abs(j - cy)) != kRing || m_chunks_.count(at) != 0 ||
                    m_prefetch_->ready.count(at) != 0 || m_prefetch_->busy.count(at) != 0 ||
                    std::find(wanted.begin(), wanted.end(), at) != wanted.end()) {
                    continue;
                }
                wanted.push_back(at);
            }
        }
    }
    m_prefetch_->wake.notify_one();
}

const Chunk& ChunkStore::load(int cx, int cy) {
    const auto found = m_chunks_.find({cx, cy});
    if (found != m_chunks_.end()) {
        return found->second;
    }
    GeneratedChunk generated;
    if (!take_prefetched(cx, cy, generated)) {
        generated = generate_chunk(m_seed_, m_params_, cx, cy);
    }
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
    ask_ring(cx, cy);
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
