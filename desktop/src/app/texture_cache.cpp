#include "app/texture_cache.hpp"

#include <array>

#include "vector/raster.hpp"
#include "vector/recipe.hpp"

namespace aether {

namespace {

constexpr std::array<int, 7> kBuckets = {32, 48, 64, 96, 128, 192, 256};

}  // namespace

TextureCache::TextureCache(SDL_Renderer* renderer, const Pack& pack) : m_renderer_(renderer), m_pack_(pack) {}

TextureCache::~TextureCache() {
    for (auto& [key, entry] : m_entries_) {
        if (entry.sprite.texture != nullptr) {
            SDL_DestroyTexture(entry.sprite.texture);
        }
    }
}

int TextureCache::bucket_for(int tile_px) {
    for (const int bucket : kBuckets) {
        if (tile_px <= bucket) {
            return bucket;
        }
    }
    return kBuckets.back();
}

const Sprite* TextureCache::get(const std::string& recipe_id, int tile_px, std::string_view variant) {
    const int bucket = bucket_for(tile_px);
    const std::string key = recipe_id + "|" + std::string(variant) + "|" + std::to_string(bucket);
    const auto found = m_entries_.find(key);
    if (found != m_entries_.end()) {
        return found->second.failed ? nullptr : &found->second.sprite;
    }

    Entry entry;
    entry.bucket = bucket;
    entry.failed = true;
    const auto text = m_pack_.read_document(recipe_id);
    std::string error;
    if (text) {
        if (const auto recipe = parse_recipe(*text, error)) {
            const Bitmap bitmap = rasterize(*recipe, static_cast<float>(bucket) / 32.0F, variant);
            SDL_Surface* surface =
                SDL_CreateSurfaceFrom(bitmap.width, bitmap.height, SDL_PIXELFORMAT_RGBA32,
                                      const_cast<std::uint8_t*>(bitmap.rgba.data()), bitmap.width * 4);
            if (surface != nullptr) {
                SDL_Texture* texture = SDL_CreateTextureFromSurface(m_renderer_, surface);
                SDL_DestroySurface(surface);
                if (texture != nullptr) {
                    SDL_SetTextureScaleMode(texture, SDL_SCALEMODE_LINEAR);
                    SDL_SetTextureBlendMode(texture, SDL_BLENDMODE_BLEND);
                    entry.sprite.texture = texture;
                    entry.sprite.width = recipe->width;
                    entry.sprite.height = recipe->height;
                    entry.sprite.origin_x = recipe->origin_x;
                    entry.sprite.origin_y = recipe->origin_y;
                    entry.sprite.faces_left = recipe->faces_left;
                    entry.sprite.px_w = bitmap.width;
                    entry.sprite.px_h = bitmap.height;
                    entry.sprite.sway = recipe->sway;
                    entry.failed = false;
                }
            }
        }
    }
    if (entry.failed) {
        SDL_Log("Cannot bake art recipe '%s' %s", recipe_id.c_str(), error.c_str());
    }
    const auto inserted = m_entries_.emplace(key, entry);
    return entry.failed ? nullptr : &inserted.first->second.sprite;
}

void TextureCache::release_other_buckets(int tile_px) {
    const int bucket = bucket_for(tile_px);
    for (auto it = m_entries_.begin(); it != m_entries_.end();) {
        if (it->second.bucket != bucket) {
            if (it->second.sprite.texture != nullptr) {
                SDL_DestroyTexture(it->second.sprite.texture);
            }
            it = m_entries_.erase(it);
        } else {
            ++it;
        }
    }
}

}  // namespace aether
