#pragma once

// Bakes vector recipes into SDL textures at the current scale bucket (spec 13: scale buckets and caching).

#include <SDL3/SDL.h>

#include <algorithm>
#include <deque>
#include <string>
#include <string_view>
#include <unordered_map>

#include "data/pack.hpp"

namespace aether {

struct Sprite {
    SDL_Texture* texture = nullptr;
    float width = 0.0F;  // art units
    float height = 0.0F;
    float origin_x = 0.0F;
    float origin_y = 0.0F;
    bool faces_left = false;  // the picture looks to the left (spec 13, "Facing")
    int px_w = 0;             // the size of the picture, in pixels
    int px_h = 0;
    float sway = 0.0F;  // how far the top moves in the wind, in art units (spec 13, "Sway")
    // Where the picture begins inside `texture`, which is an atlas shared with the other recipes of the bucket: the
    // whole picture is `px_w` by `px_h` pixels from there (spec 13, "Atlas of the textures").
    float sx = 0.0F;
    float sy = 0.0F;
    int tex_w = 0;  // the size of the texture
    int tex_h = 0;

    // The part of the texture that holds the picture, for the calls that take a source rectangle.
    SDL_FRect source() const {
        return SDL_FRect{sx, sy, static_cast<float>(px_w), static_cast<float>(px_h)};
    }
    float u0() const { return tex_w > 0 ? sx / static_cast<float>(tex_w) : 0.0F; }
    float v0() const { return tex_h > 0 ? sy / static_cast<float>(tex_h) : 0.0F; }
    float u1() const { return tex_w > 0 ? (sx + static_cast<float>(px_w)) / static_cast<float>(tex_w) : 1.0F; }
    float v1() const { return tex_h > 0 ? (sy + static_cast<float>(px_h)) / static_cast<float>(tex_h) : 1.0F; }
};

class TextureCache {
public:
    TextureCache(SDL_Renderer* renderer, const Pack& pack);
    ~TextureCache();
    TextureCache(const TextureCache&) = delete;
    TextureCache& operator=(const TextureCache&) = delete;

    // Sprite for `recipe_id` baked for `tile_px` pixels per tile; nullptr if the recipe is unusable.
    // The lookup builds no string: the frame asks for the same recipes thousands of times (spec 13).
    // `atlas` false bakes the picture into a texture of its own, for the callers that set a colour or an opacity on the
    // texture: a modulation would touch the whole atlas (spec 13, "Atlas of the textures").
    const Sprite* get(std::string_view recipe_id, int tile_px, std::string_view variant = {}, bool atlas = true);

    // How long `get` may still spend baking before the next call, in milliseconds: once it is spent, a recipe that is
    // not baked yet is not drawn (nullptr) and appears in one of the next frames, so that a frame never waits for many
    // pictures at once. A negative budget is no limit (the default).
    void set_budget(int milliseconds) {
        m_budget_ns_ = milliseconds < 0 ? -1 : static_cast<Sint64>(milliseconds) * 1000000;
        m_spent_ns_ = 0;
    }

    // Destroys textures baked for other scale buckets than the one used by `tile_px`.
    void release_other_buckets(int tile_px);

    // The largest bucket the textures are baked at, from the quality of the graphics (spec 13, "Quality"); a larger
    // tile is drawn from it, scaled.
    void set_bucket_cap(int cap) { m_bucket_cap_ = cap; }

    std::size_t size() const;

    static int bucket_for(int tile_px);

    // The bucket `get` uses for `tile_px`: a caller that resolves many pictures at once asks for it once.
    int bucket_for_tile(int tile_px) const { return std::min(bucket_for(tile_px), m_bucket_cap_); }

private:
    struct Entry {
        Sprite sprite;
        std::string variant;
        int bucket = 0;
        bool failed = false;
        bool in_atlas = false;
    };

    // One texture of pictures laid side by side, packed in shelves: the frame then sends them all with one call.
    struct Atlas {
        SDL_Texture* texture = nullptr;
        int bucket = 0;
        int size = 0;
        int x = 0;      // the next free pixel of the shelf
        int y = 0;      // the top of the shelf
        int shelf = 0;  // the height of the shelf
    };

    // A hash that reads a string_view as it is: `find` asks with the id of the recipe, without copying it.
    struct StringHash {
        using is_transparent = void;
        std::size_t operator()(std::string_view text) const noexcept { return std::hash<std::string_view>{}(text); }
    };

    int capped_bucket(int tile_px) const { return std::min(bucket_for(tile_px), m_bucket_cap_); }

    // The atlas of `bucket` with room for a picture `w` by `h`, a new one if none has it; nullptr if the textures
    // cannot be made. The slot is taken.
    Atlas* room_for(int bucket, int w, int h);

    int m_bucket_cap_ = 256;
    Sint64 m_budget_ns_ = -1;
    Sint64 m_spent_ns_ = 0;
    SDL_Renderer* m_renderer_;
    const Pack& m_pack_;
    std::deque<Atlas> m_atlases_;  // a deque keeps the addresses stable as atlases are added
    // By recipe id; a deque keeps the addresses of the sprites stable as entries are added, and an id has one entry
    // for each variant and bucket that was asked.
    std::unordered_map<std::string, std::deque<Entry>, StringHash, std::equal_to<>> m_entries_;
};

}  // namespace aether
