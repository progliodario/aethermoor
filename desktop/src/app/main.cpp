// Aethermoor desktop client (M3): a vector-art character exploring a tile map and fighting slimes.
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
#include "sim/combat_loader.hpp"
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
constexpr int kFloatingTextFrames = 50;

struct Assets {
    aether::Pack pack;
    aether::Rig rig;
    aether::Clip idle;
    aether::Clip walk;
    aether::TileMap map;
    aether::Tileset tileset;
};

struct FloatingText {
    float x = 0.0F;  // world position in tiles
    float y = 0.0F;
    int age = 0;
    std::string text;
    bool on_player = false;
    bool crit = false;
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
    const auto rig_text = read("base:art/rig/humanoid");
    const auto idle_text = read("base:art/clip/humanoid_idle");
    const auto walk_text = read("base:art/clip/humanoid_walk");
    const auto tileset_text = read("base:tileset/overworld");
    const auto map_text = out.pack.read_file(kMapPath);
    if (!rig_text || !idle_text || !walk_text || !tileset_text || !map_text) {
        SDL_Log("a required data document is missing");
        return false;
    }
    auto rig = aether::parse_rig(*rig_text, error);
    auto idle = aether::parse_clip(*idle_text, error);
    auto walk = aether::parse_clip(*walk_text, error);
    auto tileset = aether::parse_tileset(*tileset_text, error);
    auto map = aether::parse_tilemap(*map_text, error);
    if (!rig || !idle || !walk || !tileset || !map) {
        SDL_Log("cannot parse game data: %s", error.c_str());
        return false;
    }
    out.rig = std::move(*rig);
    out.idle = std::move(*idle);
    out.walk = std::move(*walk);
    out.tileset = std::move(*tileset);
    out.map = std::move(*map);
    return true;
}

struct InputState {
    float x = 0.0F;
    float y = 0.0F;
    bool attack = false;
};

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

    // Raw movement vector and attack button from keyboard, mouse and gamepad; the simulation normalizes movement.
    InputState read() const {
        const bool* keys = SDL_GetKeyboardState(nullptr);
        InputState in;
        if (keys[SDL_SCANCODE_A] || keys[SDL_SCANCODE_LEFT]) {
            in.x -= 1.0F;
        }
        if (keys[SDL_SCANCODE_D] || keys[SDL_SCANCODE_RIGHT]) {
            in.x += 1.0F;
        }
        if (keys[SDL_SCANCODE_W] || keys[SDL_SCANCODE_UP]) {
            in.y -= 1.0F;
        }
        if (keys[SDL_SCANCODE_S] || keys[SDL_SCANCODE_DOWN]) {
            in.y += 1.0F;
        }
        in.attack = keys[SDL_SCANCODE_J] || keys[SDL_SCANCODE_SPACE] ||
                    (SDL_GetMouseState(nullptr, nullptr) & SDL_BUTTON_LMASK) != 0;
        if (gamepad != nullptr) {
            if (in.x == 0.0F && in.y == 0.0F) {
                in.x = static_cast<float>(SDL_GetGamepadAxis(gamepad, SDL_GAMEPAD_AXIS_LEFTX)) / 32767.0F;
                in.y = static_cast<float>(SDL_GetGamepadAxis(gamepad, SDL_GAMEPAD_AXIS_LEFTY)) / 32767.0F;
            }
            in.attack = in.attack || SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_SOUTH);
        }
        return in;
    }
};

struct DrawItem {
    float feet_y = 0.0F;
    int kind = 0;  // 0 prop, 1 enemy, 2 player
    const aether::Prop* prop = nullptr;
    const aether::Enemy* enemy = nullptr;
};

void fill_rect(SDL_Renderer* renderer, float x, float y, float w, float h, Uint8 r, Uint8 g, Uint8 b, Uint8 a) {
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    SDL_SetRenderDrawColor(renderer, r, g, b, a);
    const SDL_FRect rect{x, y, w, h};
    SDL_RenderFillRect(renderer, &rect);
}

void draw_sprite(SDL_Renderer* renderer, const aether::Sprite& sprite, float feet_x, float feet_y, float k,
                 float squash = 1.0F) {
    const float w = sprite.width * k * (2.0F - squash);
    const float h = sprite.height * k * squash;
    const SDL_FRect dst{feet_x - sprite.origin_x * k * (2.0F - squash), feet_y - sprite.origin_y * k * squash, w, h};
    SDL_RenderTexture(renderer, sprite.texture, nullptr, &dst);
}

void draw_player(SDL_Renderer* renderer, aether::TextureCache& cache, const Assets& assets,
                 const aether::Player& player, float feet_x, float feet_y, float k, int tile_px) {
    const aether::Clip& clip = player.moving ? assets.walk : assets.idle;
    std::vector<aether::PosedPart> pose =
        aether::evaluate_pose(assets.rig, clip, static_cast<float>(player.clip_tick), player.facing_left);
    std::stable_sort(pose.begin(), pose.end(),
                     [](const aether::PosedPart& a, const aether::PosedPart& b) { return a.z < b.z; });
    const bool blink = player.iframes > 0 && (player.iframes / 4) % 2 == 0;
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
        SDL_SetTextureAlphaMod(sprite->texture, blink ? 120 : 255);
        SDL_RenderTextureRotated(renderer, sprite->texture, nullptr, &dst, static_cast<double>(posed.rotation_deg),
                                 &center, player.facing_left ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);
        SDL_SetTextureAlphaMod(sprite->texture, 255);
    }
}

void draw_enemy(SDL_Renderer* renderer, aether::TextureCache& cache, const aether::Enemy& enemy, float feet_x,
                float feet_y, float k, int tile_px, Uint64 now_ms) {
    const aether::Sprite* sprite = cache.get(enemy.def.art, tile_px);
    if (sprite == nullptr) {
        return;
    }
    const float phase = static_cast<float>((now_ms / 16 + static_cast<Uint64>(enemy.home.x * 37.0F)) % 60);
    const float wave = phase < 30.0F ? phase / 30.0F : (60.0F - phase) / 30.0F;
    const float squash = 0.95F + 0.1F * wave;
    if (enemy.hit_flash > 0) {
        SDL_SetTextureColorMod(sprite->texture, 255, 120, 120);
    }
    draw_sprite(renderer, *sprite, feet_x, feet_y, k, squash);
    SDL_SetTextureColorMod(sprite->texture, 255, 255, 255);
    if (enemy.hp < enemy.def.hp) {
        const float bar_w = 28.0F * k;
        const float ratio = static_cast<float>(enemy.hp) / static_cast<float>(enemy.def.hp);
        fill_rect(renderer, feet_x - bar_w / 2.0F, feet_y - sprite->height * k - 6.0F * k * 0.5F, bar_w, 4.0F * k * 0.5F,
                  20, 20, 20, 200);
        fill_rect(renderer, feet_x - bar_w / 2.0F, feet_y - sprite->height * k - 6.0F * k * 0.5F, bar_w * ratio,
                  4.0F * k * 0.5F, 220, 70, 70, 255);
    }
}

void draw_swing(SDL_Renderer* renderer, const aether::WorldSim& sim, float feet_x, float feet_y, float tile) {
    const aether::Player& p = sim.player();
    if (p.phase != aether::AttackPhase::Active && p.phase != aether::AttackPhase::Recovery) {
        return;
    }
    const aether::SkillDef& skill = sim.combat().skill;
    const float radius = static_cast<float>(skill.radius_x100) / 100.0F * tile;
    const float center_angle = std::atan2(p.facing.y, p.facing.x);
    const float half = static_cast<float>(skill.angle_deg) / 2.0F * 3.14159265F / 180.0F;
    const float alpha = p.phase == aether::AttackPhase::Active ? 0.45F : 0.15F;
    constexpr int kSegments = 12;
    std::vector<SDL_Vertex> vertices;
    vertices.push_back({{feet_x, feet_y - 0.5F * tile}, {1.0F, 1.0F, 1.0F, alpha}, {0.0F, 0.0F}});
    for (int i = 0; i <= kSegments; ++i) {
        const float a = center_angle - half + (2.0F * half) * static_cast<float>(i) / static_cast<float>(kSegments);
        vertices.push_back({{feet_x + std::cos(a) * radius, feet_y - 0.5F * tile + std::sin(a) * radius},
                            {1.0F, 1.0F, 1.0F, 0.0F},
                            {0.0F, 0.0F}});
    }
    std::vector<int> indices;
    for (int i = 1; i <= kSegments; ++i) {
        indices.push_back(0);
        indices.push_back(i);
        indices.push_back(i + 1);
    }
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    SDL_RenderGeometry(renderer, nullptr, vertices.data(), static_cast<int>(vertices.size()), indices.data(),
                       static_cast<int>(indices.size()));
}

void draw_hud(SDL_Renderer* renderer, const Assets& assets, const aether::WorldSim& sim, float density) {
    const aether::Player& p = sim.player();
    const float bar_w = 220.0F * density;
    const float bar_h = 16.0F * density;
    const float x = 12.0F * density;
    const float y = 12.0F * density;
    const float hp_ratio = std::clamp(static_cast<float>(p.hp) / static_cast<float>(sim.derived().max_hp), 0.0F, 1.0F);
    fill_rect(renderer, x - 2.0F, y - 2.0F, bar_w + 4.0F, bar_h + 4.0F, 10, 20, 40, 200);
    fill_rect(renderer, x, y, bar_w * hp_ratio, bar_h, 210, 60, 60, 255);
    const std::int64_t need = sim.combat().xp_table.empty() || p.level - 1 >= static_cast<std::int64_t>(sim.combat().xp_table.size())
                                  ? 0
                                  : sim.combat().xp_table[static_cast<std::size_t>(p.level - 1)];
    const float xp_ratio = need > 0 ? std::clamp(static_cast<float>(p.xp) / static_cast<float>(need), 0.0F, 1.0F) : 0.0F;
    fill_rect(renderer, x, y + bar_h + 6.0F, bar_w, 6.0F * density, 10, 20, 40, 200);
    fill_rect(renderer, x, y + bar_h + 6.0F, bar_w * xp_ratio, 6.0F * density, 90, 200, 120, 255);

    char line[96];
    std::snprintf(line, sizeof(line), "%s %lld/%lld", assets.pack.text("en", "$i18n:ui.hp").c_str(),
                  static_cast<long long>(p.hp), static_cast<long long>(sim.derived().max_hp));
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_RenderDebugText(renderer, x + 4.0F, y + 4.0F, line);
    const std::string level =
        assets.pack.text("en", "$i18n:ui.level", {{"level", static_cast<std::int64_t>(p.level)}});
    SDL_RenderDebugText(renderer, x, y + bar_h + 20.0F * density, level.c_str());
}

void render(SDL_Renderer* renderer, aether::TextureCache& cache, const Assets& assets, const aether::WorldSim& sim,
            std::vector<FloatingText>& floating, int tile_px, float density, bool debug, double fps) {
    int out_w = 0;
    int out_h = 0;
    SDL_GetCurrentRenderOutputSize(renderer, &out_w, &out_h);
    const float tile = static_cast<float>(tile_px);
    const float k = tile / 32.0F;
    const float view_w = static_cast<float>(out_w) / tile;
    const float view_h = static_cast<float>(out_h) / tile;
    const aether::Camera cam = sim.camera(view_w, view_h);
    const Uint64 now_ms = SDL_GetTicks();

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
            items.push_back({prop.y, 0, &prop, nullptr});
        }
    }
    for (const aether::Enemy& enemy : sim.enemies()) {
        if (enemy.state != aether::EnemyState::Dead) {
            items.push_back({enemy.position.y, 1, nullptr, &enemy});
        }
    }
    items.push_back({sim.player().position.y, 2, nullptr, nullptr});
    std::stable_sort(items.begin(), items.end(),
                     [](const DrawItem& a, const DrawItem& b) { return a.feet_y < b.feet_y; });
    for (const DrawItem& item : items) {
        if (item.kind == 2) {
            const float fx = (sim.player().position.x - cam.x) * tile;
            const float fy = (sim.player().position.y - cam.y) * tile;
            draw_player(renderer, cache, assets, sim.player(), fx, fy, k, tile_px);
            draw_swing(renderer, sim, fx, fy, tile);
        } else if (item.kind == 1) {
            draw_enemy(renderer, cache, *item.enemy, (item.enemy->position.x - cam.x) * tile,
                       (item.enemy->position.y - cam.y) * tile, k, tile_px, now_ms);
        } else if (const aether::Sprite* sprite = cache.get(item.prop->art, tile_px)) {
            draw_sprite(renderer, *sprite, (item.prop->x - cam.x) * tile, (item.prop->y - cam.y) * tile, k);
        }
    }

    for (const FloatingText& f : floating) {
        const float rise = static_cast<float>(f.age) * 0.6F * density;
        const float sx = (f.x - cam.x) * tile - static_cast<float>(f.text.size()) * 4.0F;
        const float sy = (f.y - cam.y) * tile - tile - rise;
        if (f.on_player) {
            SDL_SetRenderDrawColor(renderer, 255, 90, 90, 255);
        } else if (f.crit) {
            SDL_SetRenderDrawColor(renderer, 255, 220, 80, 255);
        } else {
            SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
        }
        SDL_RenderDebugText(renderer, sx, sy, f.text.c_str());
    }

    draw_hud(renderer, assets, sim, density);

    if (debug) {
        char line[160];
        std::snprintf(line, sizeof(line), "%s  %.0f fps  pos %.2f,%.2f  tile %dpx  textures %zu",
                      aether::version_line().c_str(), fps, static_cast<double>(sim.player().position.x),
                      static_cast<double>(sim.player().position.y), tile_px, cache.size());
        SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
        SDL_RenderDebugText(renderer, 8.0F, static_cast<float>(out_h) - 16.0F, line);
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
    std::string combat_error;
    const std::uint64_t seed = smoke_test ? 1234U : SDL_GetTicksNS();
    auto combat = aether::load_combat_setup(assets.pack, assets.map, kProtagonistId, seed, combat_error);
    if (!combat) {
        SDL_Log("cannot build the combat setup: %s", combat_error.c_str());
        SDL_Quit();
        return 1;
    }

    const std::string title(aether::game_name());
    SDL_Window* window = nullptr;
    SDL_Renderer* renderer = nullptr;
    if (!SDL_CreateWindowAndRenderer(title.c_str(), kWindowWidth, kWindowHeight,
                                     SDL_WINDOW_RESIZABLE | SDL_WINDOW_HIGH_PIXEL_DENSITY, &window, &renderer)) {
        SDL_Log("Window creation failed: %s", SDL_GetError());
        SDL_Quit();
        return 1;
    }
    SDL_SetRenderVSync(renderer, 1);

    int exit_code = 0;
    {
        aether::TextureCache cache(renderer, assets.pack);
        aether::WorldSim sim(assets.map, assets.tileset, 0.0F, std::move(*combat));
        const float spawn_x = sim.player().position.x;
        InputDevices devices;
        devices.open_first_gamepad();
        std::vector<FloatingText> floating;

        bool running = true;
        bool debug = false;
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

            InputState input = devices.read();
            if (smoke_test) {
                input = {1.0F, 0.0F, frames % 2 == 0};  // scripted: walk right, swinging now and then
                sim.tick(input.x, input.y, input.attack);
            } else {
                accumulator += frame_seconds;
                int ticks = 0;
                while (accumulator >= static_cast<double>(aether::kTickDt) && ticks < kMaxTicksPerFrame) {
                    sim.tick(input.x, input.y, input.attack);
                    accumulator -= static_cast<double>(aether::kTickDt);
                    ++ticks;
                }
                if (ticks == kMaxTicksPerFrame) {
                    accumulator = 0.0;  // drop the backlog instead of spiralling
                }
            }

            for (const aether::DamageEvent& e : sim.take_events()) {
                floating.push_back({e.position.x, e.position.y, 0, std::to_string(e.amount), e.on_player, e.crit});
            }
            for (FloatingText& f : floating) {
                ++f.age;
            }
            floating.erase(std::remove_if(floating.begin(), floating.end(),
                                          [](const FloatingText& f) { return f.age > kFloatingTextFrames; }),
                           floating.end());

            float density = SDL_GetWindowPixelDensity(window);
            if (density <= 0.0F) {
                density = 1.0F;
            }
            const int tile_px = std::max(16, static_cast<int>(std::lround(kBaseTilePx * density)));
            cache.release_other_buckets(tile_px);
            render(renderer, cache, assets, sim, floating, tile_px, density, debug, fps);

            if (smoke_test && ++frames >= kSmokeTestFrames) {
                running = false;
                const bool moved = sim.player().position.x > spawn_x + 1.0F;
                const bool baked = cache.size() > 10;
                const bool enemies = sim.enemies().size() == 12;
                std::printf("smoke: x %.2f -> %.2f, textures %zu, enemies %zu, %s\n", static_cast<double>(spawn_x),
                            static_cast<double>(sim.player().position.x), cache.size(), sim.enemies().size(),
                            (moved && baked && enemies) ? "ok" : "FAILED");
                if (!moved || !baked || !enemies) {
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
