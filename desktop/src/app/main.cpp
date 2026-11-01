// Aethermoor desktop client (M2): a vector-art character walking around a tile map.
// Flags: --version prints the version line; --smoke-test runs a short scripted session and exits (CI).

#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <string>
#include <vector>

#include "app/texture_cache.hpp"
#include "core/numerics.hpp"
#include "core/rules.hpp"
#include "core/version.hpp"
#include "data/pack.hpp"
#include "data/protagonist.hpp"
#include "sim/world.hpp"
#include "vector/rig.hpp"

namespace {

namespace fs = std::filesystem;

constexpr int kWindowWidth = 1280;
constexpr int kWindowHeight = 720;
constexpr int kSmokeTestFrames = 90;
constexpr int kMaxTicksPerFrame = 5;
constexpr double kMaxFrameSeconds = 0.25;
constexpr float kBaseTilePx = 48.0F;
constexpr const char* kProtagonistId = "base:protagonist/ren";
constexpr const char* kMapPath = "maps/demo.tmj";

struct Assets {
    aether::Pack pack;
    aether::Rig rig;
    aether::Clip idle;
    aether::Clip walk;
    aether::TileMap map;
    aether::Tileset tileset;
    float speed_tiles_per_s = 0.0F;
};

fs::path find_data_dir() {
    if (const char* base = SDL_GetBasePath()) {
        const fs::path candidate = fs::path(base) / "data" / "base";
        if (fs::exists(candidate / "pack.json")) {
            return candidate;
        }
    }
    return fs::path(AETHER_REPO_ROOT) / "data" / "base";
}

bool load_assets(const fs::path& dir, Assets& out) {
    std::vector<std::string> errors;
    auto pack = aether::load_pack(dir, errors);
    for (const std::string& e : errors) {
        SDL_Log("pack: %s", e.c_str());
    }
    if (!pack) {
        return false;
    }
    out.pack = std::move(*pack);

    std::string error;
    const auto read = [&](std::string_view id) { return out.pack.read_document(id); };

    const auto protagonist_text = read(kProtagonistId);
    const auto rig_text = read("base:art/rig/humanoid");
    const auto idle_text = read("base:art/clip/humanoid_idle");
    const auto walk_text = read("base:art/clip/humanoid_walk");
    const auto tileset_text = read("base:tileset/overworld");
    const auto map_text = out.pack.read_file(kMapPath);
    if (!protagonist_text || !rig_text || !idle_text || !walk_text || !tileset_text || !map_text) {
        SDL_Log("a required data document is missing");
        return false;
    }
    const auto protagonist = aether::parse_protagonist(*protagonist_text, error);
    auto rig = aether::parse_rig(*rig_text, error);
    auto idle = aether::parse_clip(*idle_text, error);
    auto walk = aether::parse_clip(*walk_text, error);
    auto tileset = aether::parse_tileset(*tileset_text, error);
    auto map = aether::parse_tilemap(*map_text, error);
    if (!protagonist || !rig || !idle || !walk || !tileset || !map) {
        SDL_Log("cannot parse game data: %s", error.c_str());
        return false;
    }
    out.rig = std::move(*rig);
    out.idle = std::move(*idle);
    out.walk = std::move(*walk);
    out.tileset = std::move(*tileset);
    out.map = std::move(*map);
    const aether::DerivedStats stats =
        aether::derived_stats(1, protagonist->base_stats, aether::Equipment{});
    out.speed_tiles_per_s = static_cast<float>(stats.move_speed_x100) / 100.0F;
    return true;
}

struct InputDevices {
    SDL_Gamepad* gamepad = nullptr;

    void open_first_gamepad() {
        if (gamepad != nullptr) {
            return;
        }
        int count = 0;
        SDL_JoystickID* ids = SDL_GetGamepads(&count);
        if (ids != nullptr && count > 0) {
            gamepad = SDL_OpenGamepad(ids[0]);
        }
        SDL_free(ids);
    }

    // Raw movement vector from keyboard and the left stick; the simulation normalizes it.
    void read(float& x, float& y) const {
        const bool* keys = SDL_GetKeyboardState(nullptr);
        x = 0.0F;
        y = 0.0F;
        if (keys[SDL_SCANCODE_A] || keys[SDL_SCANCODE_LEFT]) {
            x -= 1.0F;
        }
        if (keys[SDL_SCANCODE_D] || keys[SDL_SCANCODE_RIGHT]) {
            x += 1.0F;
        }
        if (keys[SDL_SCANCODE_W] || keys[SDL_SCANCODE_UP]) {
            y -= 1.0F;
        }
        if (keys[SDL_SCANCODE_S] || keys[SDL_SCANCODE_DOWN]) {
            y += 1.0F;
        }
        if (gamepad != nullptr && x == 0.0F && y == 0.0F) {
            x = static_cast<float>(SDL_GetGamepadAxis(gamepad, SDL_GAMEPAD_AXIS_LEFTX)) / 32767.0F;
            y = static_cast<float>(SDL_GetGamepadAxis(gamepad, SDL_GAMEPAD_AXIS_LEFTY)) / 32767.0F;
        }
    }
};

struct DrawItem {
    float feet_y = 0.0F;
    bool is_player = false;
    const aether::Prop* prop = nullptr;
};

void draw_sprite(SDL_Renderer* renderer, const aether::Sprite& sprite, float feet_x, float feet_y, float k) {
    const SDL_FRect dst{feet_x - sprite.origin_x * k, feet_y - sprite.origin_y * k, sprite.width * k,
                        sprite.height * k};
    SDL_RenderTexture(renderer, sprite.texture, nullptr, &dst);
}

void draw_player(SDL_Renderer* renderer, aether::TextureCache& cache, const Assets& assets,
                 const aether::Player& player, float feet_x, float feet_y, float k, int tile_px) {
    const aether::Clip& clip = player.moving ? assets.walk : assets.idle;
    std::vector<aether::PosedPart> pose =
        aether::evaluate_pose(assets.rig, clip, static_cast<float>(player.clip_tick), player.facing_left);
    std::stable_sort(pose.begin(), pose.end(),
                     [](const aether::PosedPart& a, const aether::PosedPart& b) { return a.z < b.z; });
    for (const aether::PosedPart& posed : pose) {
        const aether::RigPart& part = assets.rig.parts[posed.part_index];
        const aether::Sprite* sprite = cache.get(part.art, tile_px);
        if (sprite == nullptr) {
            continue;
        }
        const float px = feet_x + posed.x * k;
        const float py = feet_y + posed.y * k;
        const float w = sprite->width * k;
        const float h = sprite->height * k;
        const float pivot_x = player.facing_left ? (sprite->width - sprite->origin_x) * k : sprite->origin_x * k;
        const float pivot_y = sprite->origin_y * k;
        const SDL_FRect dst{px - pivot_x, py - pivot_y, w, h};
        const SDL_FPoint center{pivot_x, pivot_y};
        SDL_RenderTextureRotated(renderer, sprite->texture, nullptr, &dst,
                                 static_cast<double>(posed.rotation_deg), &center,
                                 player.facing_left ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);
    }
}

void render(SDL_Renderer* renderer, aether::TextureCache& cache, const Assets& assets,
            const aether::WorldSim& sim, int tile_px, bool debug, double fps) {
    int out_w = 0;
    int out_h = 0;
    SDL_GetCurrentRenderOutputSize(renderer, &out_w, &out_h);
    const float tile = static_cast<float>(tile_px);
    const float k = tile / 32.0F;
    const float view_w = static_cast<float>(out_w) / tile;
    const float view_h = static_cast<float>(out_h) / tile;
    const aether::Camera cam = sim.camera(view_w, view_h);

    SDL_SetRenderDrawColor(renderer, 11, 31, 58, 255);
    SDL_RenderClear(renderer);

    const aether::TileMap& map = sim.map();
    const int x0 = std::max(0, static_cast<int>(std::floor(cam.x)));
    const int x1 = std::min(map.width, static_cast<int>(std::ceil(cam.x + view_w)));
    const int y0 = std::max(0, static_cast<int>(std::floor(cam.y)));
    const int y1 = std::min(map.height, static_cast<int>(std::ceil(cam.y + view_h)));
    for (int ty = y0; ty < y1; ++ty) {
        for (int tx = x0; tx < x1; ++tx) {
            const auto def = assets.tileset.tiles.find(map.gid_at(tx, ty));
            if (def == assets.tileset.tiles.end()) {
                continue;
            }
            const aether::Sprite* sprite = cache.get(def->second.art, tile_px);
            if (sprite == nullptr) {
                continue;
            }
            const float sx0 = std::round((static_cast<float>(tx) - cam.x) * tile);
            const float sy0 = std::round((static_cast<float>(ty) - cam.y) * tile);
            const float sx1 = std::round((static_cast<float>(tx + 1) - cam.x) * tile);
            const float sy1 = std::round((static_cast<float>(ty + 1) - cam.y) * tile);
            const SDL_FRect dst{sx0, sy0, sx1 - sx0, sy1 - sy0};
            SDL_RenderTexture(renderer, sprite->texture, nullptr, &dst);
        }
    }

    std::vector<DrawItem> items;
    for (const aether::Prop& prop : map.props) {
        if (prop.x >= cam.x - 2.0F && prop.x <= cam.x + view_w + 2.0F && prop.y >= cam.y - 1.0F &&
            prop.y <= cam.y + view_h + 4.0F) {
            items.push_back({prop.y, false, &prop});
        }
    }
    items.push_back({sim.player().position.y, true, nullptr});
    std::stable_sort(items.begin(), items.end(),
                     [](const DrawItem& a, const DrawItem& b) { return a.feet_y < b.feet_y; });
    for (const DrawItem& item : items) {
        if (item.is_player) {
            const float fx = (sim.player().position.x - cam.x) * tile;
            const float fy = (sim.player().position.y - cam.y) * tile;
            draw_player(renderer, cache, assets, sim.player(), fx, fy, k, tile_px);
        } else if (const aether::Sprite* sprite = cache.get(item.prop->art, tile_px)) {
            draw_sprite(renderer, *sprite, (item.prop->x - cam.x) * tile, (item.prop->y - cam.y) * tile, k);
        }
    }

    if (debug) {
        char line[160];
        std::snprintf(line, sizeof(line), "%s  %.0f fps  pos %.2f,%.2f  tile %dpx  textures %zu",
                      aether::version_line().c_str(), fps, static_cast<double>(sim.player().position.x),
                      static_cast<double>(sim.player().position.y), tile_px, cache.size());
        SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
        SDL_RenderDebugText(renderer, 8.0F, 8.0F, line);
    }
    SDL_RenderPresent(renderer);
}

}  // namespace

int main(int argc, char** argv) {
    bool smoke_test = false;
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--version") == 0) {
            std::printf("%s\n", aether::version_line().c_str());
            return 0;
        }
        if (std::strcmp(argv[i], "--smoke-test") == 0) {
            smoke_test = true;
        }
    }

    if (!SDL_Init(SDL_INIT_VIDEO | SDL_INIT_GAMEPAD)) {
        SDL_Log("SDL_Init failed: %s", SDL_GetError());
        return 1;
    }

    Assets assets;
    if (!load_assets(find_data_dir(), assets)) {
        SDL_Quit();
        return 1;
    }

    const std::string title(aether::game_name());
    SDL_Window* window = nullptr;
    SDL_Renderer* renderer = nullptr;
    if (!SDL_CreateWindowAndRenderer(title.c_str(), kWindowWidth, kWindowHeight,
                                     SDL_WINDOW_RESIZABLE | SDL_WINDOW_HIGH_PIXEL_DENSITY, &window,
                                     &renderer)) {
        SDL_Log("Window creation failed: %s", SDL_GetError());
        SDL_Quit();
        return 1;
    }
    SDL_SetRenderVSync(renderer, 1);

    int exit_code = 0;
    {
        aether::TextureCache cache(renderer, assets.pack);
        aether::WorldSim sim(assets.map, assets.tileset, assets.speed_tiles_per_s);
        const float spawn_x = sim.player().position.x;
        InputDevices devices;
        devices.open_first_gamepad();

        bool running = true;
        bool debug = true;
        int frames = 0;
        double accumulator = 0.0;
        double fps = 0.0;
        Uint64 last = SDL_GetTicksNS();
        while (running) {
            const Uint64 now = SDL_GetTicksNS();
            const double frame_seconds = std::min(static_cast<double>(now - last) / 1.0e9, kMaxFrameSeconds);
            last = now;
            if (frame_seconds > 0.0) {
                fps = fps * 0.9 + (1.0 / frame_seconds) * 0.1;
            }

            SDL_Event event;
            while (SDL_PollEvent(&event)) {
                if (event.type == SDL_EVENT_QUIT ||
                    (event.type == SDL_EVENT_KEY_DOWN && event.key.key == SDLK_ESCAPE)) {
                    running = false;
                } else if (event.type == SDL_EVENT_KEY_DOWN && event.key.key == SDLK_F3) {
                    debug = !debug;
                } else if (event.type == SDL_EVENT_GAMEPAD_ADDED) {
                    devices.open_first_gamepad();
                } else if (event.type == SDL_EVENT_GAMEPAD_REMOVED && devices.gamepad != nullptr &&
                           !SDL_GamepadConnected(devices.gamepad)) {
                    SDL_CloseGamepad(devices.gamepad);
                    devices.gamepad = nullptr;
                    devices.open_first_gamepad();
                }
            }

            float in_x = 0.0F;
            float in_y = 0.0F;
            devices.read(in_x, in_y);
            if (smoke_test) {
                in_x = 1.0F;  // scripted: walk right
                in_y = 0.0F;
                sim.tick(in_x, in_y);
            } else {
                accumulator += frame_seconds;
                int ticks = 0;
                while (accumulator >= static_cast<double>(aether::kTickDt) && ticks < kMaxTicksPerFrame) {
                    sim.tick(in_x, in_y);
                    accumulator -= static_cast<double>(aether::kTickDt);
                    ++ticks;
                }
                if (ticks == kMaxTicksPerFrame) {
                    accumulator = 0.0;  // drop the backlog instead of spiralling
                }
            }

            float density = SDL_GetWindowPixelDensity(window);
            if (density <= 0.0F) {
                density = 1.0F;
            }
            const int tile_px = std::max(16, static_cast<int>(std::lround(kBaseTilePx * density)));
            cache.release_other_buckets(tile_px);
            render(renderer, cache, assets, sim, tile_px, debug, fps);

            if (smoke_test && ++frames >= kSmokeTestFrames) {
                running = false;
                const bool moved = sim.player().position.x > spawn_x + 1.0F;
                const bool baked = cache.size() > 10;
                std::printf("smoke: x %.2f -> %.2f, textures %zu, %s\n", static_cast<double>(spawn_x),
                            static_cast<double>(sim.player().position.x), cache.size(),
                            (moved && baked) ? "ok" : "FAILED");
                if (!moved || !baked) {
                    exit_code = 2;
                }
            }
        }
        if (devices.gamepad != nullptr) {
            SDL_CloseGamepad(devices.gamepad);
        }
    }

    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    return exit_code;
}
