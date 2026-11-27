#include "app/texture_cache.hpp"

#include <array>

#include "vector/raster.hpp"
#include "vector/recipe.hpp"

namespace aether {

namespace {

constexpr std::array<int, 8> kBuckets = {32, 48, 64, 80, 96, 128, 192, 256};
constexpr int kGap = 1;  // the pixels kept free around a picture, so that a scaled sampling does not read its neighbour

// The side of the atlas of a bucket: big enough for the whole art of a level at that bucket (spec 13, "Quality").
int atlas_size(int bucket) { return bucket <= 64 ? 2048 : 4096; }

}  // namespace

TextureCache::TextureCache(SDL_Renderer* renderer, const Pack& pack) : m_renderer_(renderer), m_pack_(pack) {}

TextureCache::~TextureCache() {
    for (const Atlas& atlas : m_atlases_) {
        SDL_DestroyTexture(atlas.texture);
    }
    for (auto& [id, entries] : m_entries_) {
        for (const Entry& entry : entries) {
            if (!entry.in_atlas && entry.sprite.texture != nullptr) {
                SDL_DestroyTexture(entry.sprite.texture);
            }
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

std::size_t TextureCache::size() const {
    std::size_t count = 0;
    for (const auto& [id, entries] : m_entries_) {
        count += entries.size();
    }
    return count;
}

TextureCache::Atlas* TextureCache::room_for(int bucket, int w, int h) {
    for (Atlas& atlas : m_atlases_) {
        if (atlas.bucket != bucket) {
            continue;
        }
        int x = atlas.x;
        int y = atlas.y;
        int shelf = atlas.shelf;
        if (x + w > atlas.size) {  // the shelf is full: the next one
            x = 0;
            y += shelf + kGap;
            shelf = 0;
        }
        if (y + h > atlas.size) {
            continue;
        }
        atlas.x = x + w + kGap;
        atlas.y = y;
        atlas.shelf = std::max(shelf, h);
        return &atlas;
    }
    Atlas atlas;
    atlas.bucket = bucket;
    atlas.size = atlas_size(bucket);
    if (w > atlas.size || h > atlas.size) {
        return nullptr;
    }
    atlas.texture = SDL_CreateTexture(m_renderer_, SDL_PIXELFORMAT_RGBA32, SDL_TEXTUREACCESS_STREAMING, atlas.size,
                                      atlas.size);
    if (atlas.texture == nullptr) {
        return nullptr;
    }
    SDL_SetTextureScaleMode(atlas.texture, SDL_SCALEMODE_LINEAR);
    SDL_SetTextureBlendMode(atlas.texture, SDL_BLENDMODE_BLEND);
    atlas.x = w + kGap;
    atlas.y = 0;
    atlas.shelf = h;
    m_atlases_.push_back(atlas);
    return &m_atlases_.back();
}

const Sprite* TextureCache::get(std::string_view recipe_id, int tile_px, std::string_view variant, bool atlas) {
    const int bucket = capped_bucket(tile_px);
    const auto found = m_entries_.find(recipe_id);  // no string built: the key is read as it is
    if (found != m_entries_.end()) {
        for (const Entry& entry : found->second) {
            if (entry.bucket == bucket && entry.variant == variant) {
                return entry.failed ? nullptr : &entry.sprite;
            }
        }
    }

    if (m_budget_ns_ >= 0 && m_spent_ns_ > m_budget_ns_) {  // not this frame: the picture appears in one of the next
        return nullptr;
    }
    const Uint64 bake_start = SDL_GetTicksNS();
    Entry entry;
    entry.bucket = bucket;
    entry.variant = std::string(variant);
    entry.failed = true;
    const auto text = m_pack_.read_document(recipe_id);
    std::string error;
    if (text) {
        if (const auto recipe = parse_recipe(*text, error)) {
            const Bitmap bitmap = rasterize(*recipe, static_cast<float>(bucket) / 32.0F, variant);
            SDL_Texture* texture = nullptr;
            bool in_atlas = false;
            if (atlas) {
                if (Atlas* target = room_for(bucket, bitmap.width, bitmap.height)) {
                    const SDL_Rect slot{target->x, target->y, bitmap.width, bitmap.height};
                    if (SDL_UpdateTexture(target->texture, &slot, bitmap.rgba.data(), bitmap.width * 4)) {
                        texture = target->texture;
                        entry.sprite.sx = static_cast<float>(slot.x);
                        entry.sprite.sy = static_cast<float>(slot.y);
                        entry.sprite.tex_w = target->size;
                        entry.sprite.tex_h = target->size;
                        in_atlas = true;
                    }
                }
            }
            if (texture == nullptr) {  // an atlas of its own, or the caller modulates the texture
                SDL_Surface* surface =
                    SDL_CreateSurfaceFrom(bitmap.width, bitmap.height, SDL_PIXELFORMAT_RGBA32,
                                          const_cast<std::uint8_t*>(bitmap.rgba.data()), bitmap.width * 4);
                if (surface != nullptr) {
                    texture = SDL_CreateTextureFromSurface(m_renderer_, surface);
                    SDL_DestroySurface(surface);
                    if (texture != nullptr) {
                        SDL_SetTextureScaleMode(texture, SDL_SCALEMODE_LINEAR);
                        SDL_SetTextureBlendMode(texture, SDL_BLENDMODE_BLEND);
                        entry.sprite.tex_w = bitmap.width;
                        entry.sprite.tex_h = bitmap.height;
                    }
                }
            }
            if (texture != nullptr) {
                entry.sprite.texture = texture;
                entry.sprite.width = recipe->width;
                entry.sprite.height = recipe->height;
                entry.sprite.origin_x = recipe->origin_x;
                entry.sprite.origin_y = recipe->origin_y;
                entry.sprite.faces_left = recipe->faces_left;
                entry.sprite.px_w = bitmap.width;
                entry.sprite.px_h = bitmap.height;
                entry.sprite.sway = recipe->sway;
                entry.in_atlas = in_atlas;
                entry.failed = false;
            }
        }
    }
    if (entry.failed) {
        SDL_Log("Cannot bake art recipe '%.*s' %s", static_cast<int>(recipe_id.size()), recipe_id.data(), error.c_str());
    }
    m_spent_ns_ += static_cast<Sint64>(SDL_GetTicksNS() - bake_start);
    // The id is copied only the first time a recipe is baked; a deque keeps the sprites already handed out valid.
    auto& entries = m_entries_[std::string(recipe_id)];
    entries.push_back(std::move(entry));
    const Entry& inserted = entries.back();
    return inserted.failed ? nullptr : &inserted.sprite;
}

void TextureCache::release_other_buckets(int tile_px) {
    const int bucket = capped_bucket(tile_px);
    for (auto it = m_entries_.begin(); it != m_entries_.end();) {
        std::deque<Entry>& entries = it->second;
        for (auto entry = entries.begin(); entry != entries.end();) {
            if (entry->bucket != bucket) {
                if (!entry->in_atlas && entry->sprite.texture != nullptr) {
                    SDL_DestroyTexture(entry->sprite.texture);
                }
                entry = entries.erase(entry);
            } else {
                ++entry;
            }
        }
        if (entries.empty()) {
            it = m_entries_.erase(it);
        } else {
            ++it;
        }
    }
    for (auto atlas = m_atlases_.begin(); atlas != m_atlases_.end();) {
        if (atlas->bucket != bucket) {
            SDL_DestroyTexture(atlas->texture);
            atlas = m_atlases_.erase(atlas);
        } else {
            ++atlas;
        }
    }
}

}  // namespace aether
