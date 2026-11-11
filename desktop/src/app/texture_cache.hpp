#pragma once

// Bakes vector recipes into SDL textures at the current scale bucket (spec 13: scale buckets and caching).

#include <SDL3/SDL.h>

#include <map>
#include <string>
#include <string_view>

#include "data/pack.hpp"

namespace aether {

struct Sprite {
    SDL_Texture* texture = nullptr;
    float width = 0.0F;  // art units
    float height = 0.0F;
    float origin_x = 0.0F;
    float origin_y = 0.0F;
    bool faces_left = false;  // the picture looks to the left (spec 13, "Facing")
    int px_w = 0;             // the size of the texture, in pixels
    int px_h = 0;
};

class TextureCache {
public:
    TextureCache(SDL_Renderer* renderer, const Pack& pack);
    ~TextureCache();
    TextureCache(const TextureCache&) = delete;
    TextureCache& operator=(const TextureCache&) = delete;

    // Sprite for `recipe_id` baked for `tile_px` pixels per tile; nullptr if the recipe is unusable.
    const Sprite* get(const std::string& recipe_id, int tile_px, std::string_view variant = {});

    // Destroys textures baked for other scale buckets than the one used by `tile_px`.
    void release_other_buckets(int tile_px);

    std::size_t size() const { return m_entries_.size(); }

    static int bucket_for(int tile_px);

private:
    struct Entry {
        Sprite sprite;
        int bucket = 0;
        bool failed = false;
    };

    SDL_Renderer* m_renderer_;
    const Pack& m_pack_;
    std::map<std::string, Entry, std::less<>> m_entries_;
};

}  // namespace aether
