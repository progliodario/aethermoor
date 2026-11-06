// Aethermoor desktop client (M3): a vector-art character exploring a tile map and fighting slimes.
// Flags: --version prints the version line; --smoke-test runs a short scripted session and exits (CI).

#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <map>
#include <optional>
#include <string>
#include <vector>

#include "app/texture_cache.hpp"
#include "core/numerics.hpp"
#include "core/rules.hpp"
#include "core/version.hpp"
#include "data/pack.hpp"
#include "data/protagonist.hpp"
#include "sim/combat_loader.hpp"
#include "sim/chunk_store.hpp"
#include "app/sound_board.hpp"
#include "data/world_data.hpp"
#include "sim/save.hpp"
#include "sim/world_map.hpp"
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
// Who is played in this run (spec 18), chosen for a new game and kept in the folder of the slot.
std::string g_protagonist_id = kProtagonistId;
aether::SoundBoard g_sound;  // the sound effects (spec 14); silent in the smoke tests
std::string g_art_variant;   // palette variant of the player's art
bool g_has_analyze = true;   // the protagonist has Ren's Analyze
constexpr const char* kMapPath = "maps/demo.tmj";
constexpr int kFloatingTextFrames = 50;
constexpr double kAutosaveSeconds = 30.0;
constexpr const char* kWorldId = "base:world/overworld";

struct Assets {
    aether::Pack pack;
    aether::Rig rig;
    aether::Clip idle;
    aether::Clip walk;
    aether::TileMap map;
    aether::Tileset tileset;
};

struct Ui {
    std::string lang = "en";
    int choice_index = 0;
    std::string last_speaker;  // last line spoken in the open dialogue, kept while choices are shown
    std::string last_text;
    std::map<std::string, std::string> last_args;  // arguments of the last spoken line
    std::string message;                           // short notice ("Game saved"), shown for a moment
    int message_frames = 0;
    bool show_inventory = false;
    int bag_cursor = 0;  // index of the selected item in the bag
    int shop_cursor = 0;
    int board_cursor = 0;
    int travel_cursor = 0;
    bool shop_sell = false;  // the shop shows what the player sells instead of what it sells
    bool show_map = false;
    bool show_journal = false;
    int journal_scroll = 0;  // first visible line of the journal
    mutable std::map<std::pair<int, int>, std::optional<aether::Settlement>> map_markers;  // settlement shown on a cell
    mutable std::map<std::pair<int, int>, int>
        map_codes;  // biome code of the explored cells, filled when the map is drawn
    // The view of the world map (spec 09, "The map view"): zoom level, the cell at its center, and what was drawn last.
    // The biome codes of the sampled tiles of a cell {x, y, n}: n x n of them, row by row (see draw_world_map).
    mutable std::map<std::array<int, 3>, std::vector<std::uint8_t>> map_detail;
    // The goal: a place of the world the player marked on the map (not saved); the HUD shows its direction and
    // distance.
    mutable bool has_goal = false;
    mutable float goal_x = 0.0F;  // in tiles
    mutable float goal_y = 0.0F;
    mutable float map_view_x =
        0.0F;  // where the square view of the map was drawn, in pixels (to place a goal with the mouse)
    mutable float map_view_y = 0.0F;
    mutable float map_view_side = 1.0F;
    mutable int analyze_frames = 0;  // frames left of the Analyze panel (Z), 0: hidden
    bool show_minimap = true;        // N shows or hides the small map in the corner
    mutable std::vector<std::uint8_t>
        mini_codes;           // biome codes of the sampled tiles around the player, 255 where unexplored
    mutable int mini_ox = 0;  // the tile of the top left sample
    mutable int mini_oy = 0;
    mutable int map_pick = -1;   // the place the view last jumped to (Tab), in order of distance
    int last_region = -1;        // the region the player was in, to say the name when it changes
    mutable int map_level = -1;  // -1: frame what was explored when the map is drawn next
    mutable float map_cx = 0.0F;
    mutable float map_cy = 0.0F;
    mutable float map_cell_px = 1.0F;     // pixels per cell, as drawn (to turn a mouse drag into cells)
    mutable float map_view_cells = 1.0F;  // cells across the view, as drawn (the size of a key step)
};

std::string detect_language() {
    int count = 0;
    SDL_Locale** locales = SDL_GetPreferredLocales(&count);
    std::string lang = "en";
    if (locales != nullptr && count > 0 && locales[0] != nullptr && locales[0]->language != nullptr &&
        std::strcmp(locales[0]->language, "it") == 0) {
        lang = "it";
    }
    SDL_free(locales);
    return lang;
}

std::vector<std::string> wrap_text(const std::string& text, std::size_t width) {
    std::vector<std::string> lines;
    std::string line;
    std::size_t pos = 0;
    while (pos < text.size()) {
        std::size_t end = text.find(' ', pos);
        if (end == std::string::npos) {
            end = text.size();
        }
        const std::string word = text.substr(pos, end - pos);
        if (!line.empty() && line.size() + 1 + word.size() > width) {
            lines.push_back(line);
            line.clear();
        }
        line += (line.empty() ? "" : " ") + word;
        pos = end + 1;
    }
    if (!line.empty()) {
        lines.push_back(line);
    }
    return lines;
}

// What the sounds were last frame, to hear what changed (see the sound block of the main loop).
struct SoundWatch {
    bool valid = false;
    bool attacking = false;
    int dodge_ticks = 0;
    std::int64_t level = 0;
    std::int64_t items = 0;
    std::int64_t gold = 0;
    bool panel = false;
    std::int64_t hp = 0;
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
    bool dodge = false;   // the dodge roll (spec 05): L, Left Shift or the east button of the gamepad
    bool strike = false;  // the power strike (spec 05, "Mana"): K or the right shoulder button of the gamepad
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
        in.dodge = keys[SDL_SCANCODE_L] || keys[SDL_SCANCODE_LSHIFT];
        in.strike = keys[SDL_SCANCODE_K];
        if (gamepad != nullptr) {
            in.dodge = in.dodge || SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_EAST);
            in.strike = in.strike || SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER);
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
    int kind = 0;  // 0 prop, 1 enemy, 2 player, 3 npc
    const aether::Prop* prop = nullptr;
    const aether::Enemy* enemy = nullptr;
    const aether::NpcDef* npc = nullptr;
};

// The number of characters of a UTF-8 text (the debug font draws one character in 8 units, whatever its length in
// bytes).
float text_columns(const std::string& text) {
    std::size_t columns = 0;
    for (const char c : text) {
        if ((static_cast<unsigned char>(c) & 0xC0) != 0x80) {
            ++columns;
        }
    }
    return static_cast<float>(columns);
}

// The debug font of SDL has the ASCII characters only (anything else is drawn as a block). The accented letters of the
// Italian texts are drawn as the letter with a small accent, the quotation marks as ASCII ones, anything else as a
// question mark. `text` is UTF-8.
void debug_text(SDL_Renderer* renderer, float x, float y, const char* text) {
    struct Accent {
        int code;
        char base;
        bool acute;
        bool upper;
    };
    static const Accent kAccents[] = {
        {0xE0, 'a', false, false}, {0xE8, 'e', false, false}, {0xE9, 'e', true, false}, {0xEC, 'i', false, false},
        {0xF2, 'o', false, false}, {0xF9, 'u', false, false}, {0xC0, 'A', false, true}, {0xC8, 'E', false, true},
        {0xC9, 'E', true, true},   {0xCC, 'I', false, true},  {0xD2, 'O', false, true}, {0xD9, 'U', false, true},
    };
    std::string run;  // a stretch of ASCII characters, drawn in one call
    float run_x = x;
    float pen = x;
    const auto flush = [&]() {
        if (!run.empty()) {
            SDL_RenderDebugText(renderer, run_x, y, run.c_str());
            run.clear();
        }
    };
    const auto* p = reinterpret_cast<const unsigned char*>(text);
    while (*p != 0) {
        int code = *p;
        int length = 1;
        if (code >= 0xC0 && code < 0xE0 && (p[1] & 0xC0) == 0x80) {
            code = ((code & 0x1F) << 6) | (p[1] & 0x3F);
            length = 2;
        } else if (code >= 0xE0 && code < 0xF0 && (p[1] & 0xC0) == 0x80 && (p[2] & 0xC0) == 0x80) {
            code = ((code & 0x0F) << 12) | ((p[1] & 0x3F) << 6) | (p[2] & 0x3F);
            length = 3;
        } else if (code >= 0x80 && code < 0xC0) {  // the rest of a character that is not drawn
            ++p;
            continue;
        } else if (code >= 0x80) {
            code = '?';
        }
        p += length;
        if (code < 0x80) {
            if (run.empty()) {
                run_x = pen;
            }
            run.push_back(static_cast<char>(code));
            pen += 8.0F;
            continue;
        }
        flush();
        const Accent* accent = nullptr;
        for (const Accent& candidate : kAccents) {
            if (candidate.code == code) {
                accent = &candidate;
            }
        }
        char glyph[2] = {'?', 0};
        if (accent != nullptr) {
            glyph[0] = accent->base;
            const float top = y + (accent->upper ? -1.0F : 0.0F);
            SDL_RenderPoint(renderer, pen + (accent->acute ? 4.0F : 2.0F), top);
            SDL_RenderPoint(renderer, pen + 3.0F, top + 1.0F);
        } else if (code == 0xAB || code == 0xBB || code == 0x201C || code == 0x201D) {
            glyph[0] = '"';
        } else if (code == 0x2018 || code == 0x2019) {
            glyph[0] = '\'';
        }
        SDL_RenderDebugText(renderer, pen, y, glyph);
        pen += 8.0F;
    }
    flush();
}

void fill_rect(SDL_Renderer* renderer, float x, float y, float w, float h, Uint8 r, Uint8 g, Uint8 b, Uint8 a) {
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    SDL_SetRenderDrawColor(renderer, r, g, b, a);
    const SDL_FRect rect{x, y, w, h};
    SDL_RenderFillRect(renderer, &rect);
}

// A panel with a soft shadow, a border in the accent color, a body that fades from lighter to darker, a thin light line
// under the top edge and a stripe of the accent color on the top.
void draw_panel(SDL_Renderer* renderer, float x, float y, float w, float h, Uint8 ar, Uint8 ag, Uint8 ab, Uint8 alpha) {
    fill_rect(renderer, x + 3.0F, y + 4.0F, w, h, 0, 0, 0, 90);
    fill_rect(renderer, x - 2.0F, y - 2.0F, w + 4.0F, h + 4.0F, 4, 10, 24, 255);
    fill_rect(renderer, x - 1.0F, y - 1.0F, w + 2.0F, h + 2.0F, static_cast<Uint8>(ar / 2), static_cast<Uint8>(ag / 2),
              static_cast<Uint8>(ab / 2), 255);
    const int strips = std::max(1, static_cast<int>(h / 4.0F));
    for (int i = 0; i < strips; ++i) {
        const float t = static_cast<float>(i) / static_cast<float>(strips);
        const auto shade = [&](int top, int bottom) { return static_cast<Uint8>(top + (bottom - top) * t); };
        const float sy = y + h * t;
        fill_rect(renderer, x, sy, w, h / static_cast<float>(strips) + 0.5F, shade(22, 8), shade(48, 20), shade(88, 44),
                  alpha);
    }
    fill_rect(renderer, x, y + 3.0F, w, 1.0F, 255, 255, 255, 40);
    fill_rect(renderer, x, y, w, 3.0F, ar, ag, ab, 255);
    // little studs in the corners
    for (const float cx : {x + 5.0F, x + w - 8.0F}) {
        for (const float cy : {y + 6.0F, y + h - 9.0F}) {
            fill_rect(renderer, cx, cy, 3.0F, 3.0F, static_cast<Uint8>(ar / 2 + 40), static_cast<Uint8>(ag / 2 + 40),
                      static_cast<Uint8>(ab / 2 + 40), 200);
        }
    }
}

// A bar with a dark frame, a fill that is lighter on the top half and darker on the bottom, a gloss line and ticks.
void draw_bar(SDL_Renderer* renderer, float x, float y, float w, float h, float ratio, Uint8 r, Uint8 g, Uint8 b) {
    fill_rect(renderer, x - 2.0F, y - 2.0F, w + 4.0F, h + 4.0F, 4, 10, 24, 235);
    fill_rect(renderer, x - 1.0F, y - 1.0F, w + 2.0F, h + 2.0F, 70, 90, 120, 200);
    fill_rect(renderer, x, y, w, h, 12, 22, 40, 255);
    const float fw = w * std::clamp(ratio, 0.0F, 1.0F);
    if (fw > 0.0F) {
        const auto lighter = [](Uint8 c, int k) { return static_cast<Uint8>(std::min(255, c + k)); };
        const auto darker = [](Uint8 c, int k) { return static_cast<Uint8>(std::max(0, c - k)); };
        fill_rect(renderer, x, y, fw, h * 0.55F, lighter(r, 40), lighter(g, 40), lighter(b, 40), 255);
        fill_rect(renderer, x, y + h * 0.55F, fw, h * 0.45F, darker(r, 45), darker(g, 45), darker(b, 45), 255);
        fill_rect(renderer, x, y + 1.0F, fw, std::max(1.0F, h * 0.14F), 255, 255, 255, 70);
        fill_rect(renderer, x + fw - 1.0F, y, 1.0F, h, 255, 255, 255, 90);
    }
    for (int i = 1; i < 10; ++i) {
        fill_rect(renderer, x + w * static_cast<float>(i) / 10.0F, y + h * 0.7F, 1.0F, h * 0.3F, 0, 0, 0, 70);
    }
}

void draw_sprite(SDL_Renderer* renderer, const aether::Sprite& sprite, float feet_x, float feet_y, float k,
                 float squash = 1.0F) {
    const float w = sprite.width * k * (2.0F - squash);
    const float h = sprite.height * k * squash;
    const SDL_FRect dst{feet_x - sprite.origin_x * k * (2.0F - squash), feet_y - sprite.origin_y * k * squash, w, h};
    SDL_RenderTexture(renderer, sprite.texture, nullptr, &dst);
}

void draw_character(SDL_Renderer* renderer, aether::TextureCache& cache, const Assets& assets, bool moving,
                    bool facing_left, int clip_tick, bool blink, std::string_view variant, float feet_x, float feet_y,
                    float k, int tile_px) {
    const aether::Clip& clip = moving ? assets.walk : assets.idle;
    std::vector<aether::PosedPart> pose =
        aether::evaluate_pose(assets.rig, clip, static_cast<float>(clip_tick), facing_left);
    std::stable_sort(pose.begin(), pose.end(),
                     [](const aether::PosedPart& a, const aether::PosedPart& b) { return a.z < b.z; });
    for (const aether::PosedPart& posed : pose) {
        const aether::RigPart& part = assets.rig.parts[posed.part_index];
        const aether::Sprite* sprite = cache.get(part.art, tile_px, variant);
        if (sprite == nullptr) {
            continue;
        }
        const float px = feet_x + posed.x * k;
        const float py = feet_y + posed.y * k;
        const float w = sprite->width * k;
        const float h = sprite->height * k;
        const float pivot_x = facing_left ? (sprite->width - sprite->origin_x) * k : sprite->origin_x * k;
        const float pivot_y = sprite->origin_y * k;
        const SDL_FRect dst{px - pivot_x, py - pivot_y, w, h};
        const SDL_FPoint center{pivot_x, pivot_y};
        SDL_SetTextureAlphaMod(sprite->texture, blink ? 120 : 255);
        SDL_RenderTextureRotated(renderer, sprite->texture, nullptr, &dst, static_cast<double>(posed.rotation_deg),
                                 &center, facing_left ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);
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
        fill_rect(renderer, feet_x - bar_w / 2.0F, feet_y - sprite->height * k - 6.0F * k * 0.5F, bar_w,
                  4.0F * k * 0.5F, 20, 20, 20, 200);
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

// Text with a dark edge, for what is drawn over the world (the HUD): it reads on grass and snow alike. Uses the current
// color.
void outlined_text(SDL_Renderer* renderer, float x, float y, const char* text) {
    Uint8 r = 255;
    Uint8 g = 255;
    Uint8 b = 255;
    Uint8 a = 255;
    SDL_GetRenderDrawColor(renderer, &r, &g, &b, &a);
    SDL_SetRenderDrawColor(renderer, 0, 0, 0, 230);
    debug_text(renderer, x + 0.5F, y + 0.5F, text);
    SDL_SetRenderDrawColor(renderer, r, g, b, a);
    debug_text(renderer, x, y, text);
}

void draw_hud(SDL_Renderer* renderer, const Assets& assets, const aether::WorldSim& sim, const Ui& ui, float density) {
    const aether::Player& p = sim.player();
    const float bar_w = 220.0F * density;
    const float bar_h = 16.0F * density;
    const float x = 12.0F * density;
    const float y = 12.0F * density;
    const float hp_ratio = std::clamp(static_cast<float>(p.hp) / static_cast<float>(sim.derived().max_hp), 0.0F, 1.0F);
    const float below = 10.0F * density;  // the mana bar, between the health bar and the experience bar
    const float mp_ratio = std::clamp(
        static_cast<float>(sim.mp()) / static_cast<float>(std::max<std::int64_t>(sim.derived().max_mp, 1)), 0.0F, 1.0F);
    draw_bar(renderer, x, y + bar_h + 4.0F, bar_w, 7.0F * density, mp_ratio, 80, 140, 255);
    draw_bar(renderer, x, y, bar_w, bar_h, hp_ratio, 210, 60, 60);
    const std::int64_t need =
        sim.combat().xp_table.empty() || p.level - 1 >= static_cast<std::int64_t>(sim.combat().xp_table.size())
            ? 0
            : sim.combat().xp_table[static_cast<std::size_t>(p.level - 1)];
    const float xp_ratio =
        need > 0 ? std::clamp(static_cast<float>(p.xp) / static_cast<float>(need), 0.0F, 1.0F) : 0.0F;
    draw_bar(renderer, x, y + bar_h + 6.0F + below, bar_w, 6.0F * density, xp_ratio, 90, 200, 120);

    // The two abilities next to the bars: a square that fills while the cooldown runs and is lit when the ability is
    // ready (green: the dodge roll, `L`; blue: the power strike, `K`, and enough mana for it).
    const aether::CombatSetup& setup = sim.combat();
    const float pip = 15.0F * density;
    float pip_x = x + bar_w + 8.0F * density;
    const auto draw_pip = [&](float ready, bool lit, Uint8 r, Uint8 g, Uint8 b, const char* key) {
        fill_rect(renderer, pip_x - 1.0F, y - 1.0F, pip + 2.0F, pip + 2.0F, 10, 20, 40, 220);
        const float filled = std::clamp(ready, 0.0F, 1.0F);
        fill_rect(renderer, pip_x, y + pip * (1.0F - filled), pip, pip * filled, lit ? r : 90, lit ? g : 100,
                  lit ? b : 120, 255);
        SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
        outlined_text(renderer, pip_x + (pip - 8.0F) / 2.0F, y + (pip - 8.0F) / 2.0F, key);
        pip_x += pip + 6.0F * density;
    };
    if (setup.dodge.enabled) {
        const float ready =
            1.0F - static_cast<float>(p.dodge_cooldown) / static_cast<float>(std::max(setup.dodge.cooldown, 1));
        draw_pip(ready, p.dodge_cooldown == 0, 90, 220, 120, "L");
    }
    if (setup.gift.death_save_ticks > 0) {  // the Eternal Aegis: lit when the death save is ready
        const float ready =
            1.0F - static_cast<float>(p.death_save_cd) / static_cast<float>(setup.gift.death_save_ticks);
        draw_pip(ready, p.death_save_cd == 0, 255, 215, 90, "A");
    }
    if (setup.strike.enabled) {
        const float ready = 1.0F - static_cast<float>(std::min(p.cooldown, setup.strike.skill.cooldown)) /
                                       static_cast<float>(std::max(setup.strike.skill.cooldown, 1));
        draw_pip(ready, p.cooldown == 0 && sim.mp() >= setup.strike.mp, 100, 160, 255, "K");
    }

    char line[96];
    std::snprintf(line, sizeof(line), "%s %lld/%lld", assets.pack.text(ui.lang, "$i18n:ui.hp").c_str(),
                  static_cast<long long>(p.hp), static_cast<long long>(sim.derived().max_hp));
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_SetRenderScale(renderer, 2.0F, 2.0F);
    outlined_text(renderer, (x + 6.0F) / 2.0F, (y + 3.0F * density) / 2.0F, line);
    const std::string level =
        assets.pack.text(ui.lang, "$i18n:ui.level", {{"level", static_cast<std::int64_t>(p.level)}});
    outlined_text(renderer, x / 2.0F, (y + bar_h + 16.0F * density + below) / 2.0F, level.c_str());
    const std::string bag_hint = assets.pack.text(ui.lang, "$i18n:ui.bag_hint");
    const float hint_x = (x + 110.0F * density) / 2.0F;
    outlined_text(renderer, hint_x, (y + bar_h + 16.0F * density + below) / 2.0F, bag_hint.c_str());
    if (sim.streamed()) {
        // The map hint follows the bag hint whatever the language: 8 units per character, two characters of gap.
        outlined_text(renderer, hint_x + 8.0F * (text_columns(bag_hint) + 2.0F),
                      (y + bar_h + 16.0F * density + below) / 2.0F,
                      assets.pack.text(ui.lang, "$i18n:ui.map_hint").c_str());
    }
    SDL_SetRenderScale(renderer, 1.0F, 1.0F);
}

// A small map of the land around the player in a corner of the screen (spec 09, "The map view"): 40 x 40 samples 16
// tiles apart (640 tiles across), only where the land was explored, with the player in the middle, the woken stones and
// the goal.
// Ren's Analyze, the eye of the system (key Z): the nearest living creature within 10 tiles, with its level, health,
// attack, defense and what it can drop (with the chance), in a panel at the top center for a few seconds. Presentation
// only.
void draw_analyze(SDL_Renderer* renderer, const Assets& assets, const aether::WorldSim& sim, const Ui& ui, int out_w,
                  float density) {
    if (ui.analyze_frames <= 0 || sim.story().dialogue_active() || ui.show_map) {
        return;
    }
    --ui.analyze_frames;
    const aether::Enemy* target = nullptr;
    float best = 100.0F;  // 10 tiles, squared
    for (const aether::Enemy& e : sim.enemies()) {
        if (e.state == aether::EnemyState::Dead) {
            continue;
        }
        const float dx = e.position.x - sim.player().position.x;
        const float dy = e.position.y - sim.player().position.y;
        if (dx * dx + dy * dy < best) {
            best = dx * dx + dy * dy;
            target = &e;
        }
    }
    const auto last_segment = [](const std::string& id) { return id.substr(id.rfind('/') + 1); };
    std::vector<std::string> lines;
    if (target == nullptr) {
        lines.push_back(assets.pack.text(ui.lang, "$i18n:ui.analyze_none"));
    } else {
        const aether::EnemyDef& def = target->def;
        lines.push_back(
            assets.pack.text(ui.lang, "$i18n:ui.analyze_title",
                             {{"name", assets.pack.text(ui.lang, "$i18n:enemy." + last_segment(def.id) + ".name")},
                              {"level", static_cast<std::int64_t>(def.level)}}));
        lines.push_back(assets.pack.text(ui.lang, "$i18n:ui.analyze_stats",
                                         {{"hp", static_cast<std::int64_t>(target->hp)},
                                          {"max", static_cast<std::int64_t>(def.hp)},
                                          {"atk", static_cast<std::int64_t>(def.atk)},
                                          {"def", static_cast<std::int64_t>(def.def)}}));
        std::string items;
        for (const aether::DropDef& drop : def.drops) {
            items += (items.empty() ? "" : ", ") +
                     assets.pack.text(ui.lang, "$i18n:item." + last_segment(drop.item) + ".name",
                                      {{"count", static_cast<std::int64_t>(1)}}) +
                     " " + std::to_string(drop.weight_pm / 10) + "%";
        }
        if (!items.empty()) {
            lines.push_back(assets.pack.text(ui.lang, "$i18n:ui.analyze_drops", {{"items", items}}));
        }
    }
    float columns = 0.0F;
    for (const std::string& line : lines) {
        columns = std::max(columns, text_columns(line));
    }
    constexpr float kScale = 2.0F;
    const float width = (columns * 8.0F + 12.0F) * kScale;
    const float height = (static_cast<float>(lines.size()) * 12.0F + 8.0F) * kScale;
    const float x = (static_cast<float>(out_w) - width) / 2.0F;
    const float y = 12.0F * density;
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    draw_panel(renderer, x, y, width, height, 111, 227, 255, 235);
    SDL_SetRenderScale(renderer, kScale, kScale);
    float ty = y / kScale + 4.0F;
    for (std::size_t i = 0; i < lines.size(); ++i) {
        SDL_SetRenderDrawColor(renderer, i == 0 ? 255 : 235, i == 0 ? 215 : 245, i == 0 ? 120 : 255, 255);
        debug_text(renderer, x / kScale + 6.0F, ty, lines[i].c_str());
        ty += 12.0F;
    }
    SDL_SetRenderScale(renderer, 1.0F, 1.0F);
}

void draw_minimap(SDL_Renderer* renderer, const aether::WorldSim& sim, const Ui& ui, float density) {
    const aether::ChunkStore* store = sim.chunks();
    if (store == nullptr || !ui.show_minimap || ui.show_map || sim.story().dialogue_active()) {
        return;
    }
    constexpr int kN = 40;
    constexpr int kStep = 16;
    const aether::WorldParams& params = store->params();
    const int player_x = static_cast<int>(std::floor(sim.player().position.x));
    const int player_y = static_cast<int>(std::floor(sim.player().position.y));
    const int ox = (player_x / kStep) * kStep - kN / 2 * kStep;
    const int oy = (player_y / kStep) * kStep - kN / 2 * kStep;
    if (ui.mini_codes.empty() || ui.mini_ox != ox || ui.mini_oy != oy) {  // sampled again every 16 tiles walked
        ui.mini_codes.assign(static_cast<std::size_t>(kN * kN), 255);
        for (int j = 0; j < kN; ++j) {
            for (int i = 0; i < kN; ++i) {
                const int tx = ox + i * kStep + kStep / 2;
                const int ty = oy + j * kStep + kStep / 2;
                if (tx < 0 || ty < 0 || tx >= params.width || ty >= params.height ||
                    sim.explored().count({tx / aether::kMapCell, ty / aether::kMapCell}) == 0) {
                    continue;
                }
                ui.mini_codes[static_cast<std::size_t>(j * kN + i)] =
                    static_cast<std::uint8_t>(aether::biome_code_at(store->seed(), params, tx, ty));
            }
        }
        ui.mini_ox = ox;
        ui.mini_oy = oy;
    }
    static const Uint8 kColors[7][3] = {{60, 110, 190},  {222, 206, 150}, {130, 130, 140}, {235, 240, 245},
                                        {222, 206, 150}, {60, 130, 70},   {110, 180, 90}};
    const float cell = 3.0F * density;
    const float side = cell * static_cast<float>(kN);
    const float x0 = 10.0F * density;
    const float y0 = 84.0F * density;
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    fill_rect(renderer, x0 - 2.0F, y0 - 2.0F, side + 4.0F, side + 4.0F, 20, 36, 66, 230);
    fill_rect(renderer, x0, y0, side, side, 8, 16, 34, 200);
    for (int j = 0; j < kN; ++j) {
        for (int i = 0; i < kN; ++i) {
            const std::uint8_t code = ui.mini_codes[static_cast<std::size_t>(j * kN + i)];
            if (code < 7) {
                fill_rect(renderer, x0 + cell * static_cast<float>(i), y0 + cell * static_cast<float>(j),
                          std::ceil(cell), std::ceil(cell), kColors[code][0], kColors[code][1], kColors[code][2], 235);
            }
        }
    }
    const auto place = [&](float tile_x, float tile_y, bool clamp, float size, Uint8 r, Uint8 g, Uint8 b) {
        float sx = x0 + (tile_x - static_cast<float>(ox)) / static_cast<float>(kStep) * cell;
        float sy = y0 + (tile_y - static_cast<float>(oy)) / static_cast<float>(kStep) * cell;
        const bool inside = sx >= x0 && sy >= y0 && sx <= x0 + side && sy <= y0 + side;
        if (!inside && !clamp) {
            return;
        }
        sx = std::clamp(sx, x0 + size, x0 + side - size);
        sy = std::clamp(sy, y0 + size, y0 + side - size);
        fill_rect(renderer, sx - size / 2.0F - 1.0F, sy - size / 2.0F - 1.0F, size + 2.0F, size + 2.0F, 20, 20, 30,
                  255);
        fill_rect(renderer, sx - size / 2.0F, sy - size / 2.0F, size, size, r, g, b, 255);
    };
    for (const auto& [stone_x, stone_y] : sim.stones()) {
        place(static_cast<float>(stone_x), static_cast<float>(stone_y), false, 4.0F * density, 140, 255, 235);
    }
    if (ui.has_goal) {
        place(ui.goal_x, ui.goal_y, true, 5.0F * density, 90, 255, 120);
    }
    place(sim.player().position.x, sim.player().position.y, false, 5.0F * density, 255, 50, 50);
}

// The world map (spec 09, "The map view"): explored cells by biome, the places that were found, and the player. The
// view is a square window onto the map with a zoom level (0 shows the whole world, each level doubles the size of a
// cell) and a center that can be moved; opening the map frames everything explored so far.
constexpr int kMapMaxLevel = 4;

struct MapGeometry {
    float x = 0.0F;  // the square viewport, in pixels
    float y = 0.0F;
    float side = 0.0F;
    float cell = 0.0F;  // pixels per map cell at this zoom
    float cx = 0.0F;    // the map cell (fractional) at the center of the viewport
    float cy = 0.0F;
    float to_x(float cell_x) const { return x + side / 2.0F + (cell_x - cx) * cell; }
    float to_y(float cell_y) const { return y + side / 2.0F + (cell_y - cy) * cell; }
};

int map_columns(const aether::WorldParams& params) { return (params.width + aether::kMapCell - 1) / aether::kMapCell; }
int map_rows(const aether::WorldParams& params) { return (params.height + aether::kMapCell - 1) / aether::kMapCell; }

// Frames the explored cells (with a margin of one cell around): the biggest zoom at which they all fit, centered on
// them.
void map_fit(const aether::WorldSim& sim, const aether::WorldParams& params, const Ui& ui, float side) {
    int min_x = map_columns(params);
    int min_y = map_rows(params);
    int max_x = 0;
    int max_y = 0;
    for (const auto& [x, y] : sim.explored()) {
        min_x = std::min(min_x, x);
        min_y = std::min(min_y, y);
        max_x = std::max(max_x, x);
        max_y = std::max(max_y, y);
    }
    if (min_x > max_x) {  // nothing explored: the player's cell
        min_x = max_x = static_cast<int>(sim.player().position.x) / aether::kMapCell;
        min_y = max_y = static_cast<int>(sim.player().position.y) / aether::kMapCell;
    }
    const float span = static_cast<float>(std::max(max_x - min_x, max_y - min_y) + 3);
    const float base = side / static_cast<float>(std::max(map_columns(params), map_rows(params)));
    int level = 0;
    while (level < kMapMaxLevel && span * base * static_cast<float>(1 << (level + 1)) <= side) {
        ++level;
    }
    ui.map_level = level;
    ui.map_cx = static_cast<float>(min_x + max_x + 1) / 2.0F;
    ui.map_cy = static_cast<float>(min_y + max_y + 1) / 2.0F;
}

// Moves the center of the view by a number of view widths, keeping it inside the world.
void map_pan(const aether::WorldSim& sim, const Ui& ui, float dx_cells, float dy_cells) {
    if (sim.chunks() == nullptr) {
        return;
    }
    const aether::WorldParams& params = sim.chunks()->params();
    ui.map_cx = std::clamp(ui.map_cx + dx_cells, 0.0F, static_cast<float>(map_columns(params)));
    ui.map_cy = std::clamp(ui.map_cy + dy_cells, 0.0F, static_cast<float>(map_rows(params)));
}

void map_zoom(const Ui& ui, int delta) {
    if (ui.map_level >= 0) {
        ui.map_level = std::clamp(ui.map_level + delta, 0, kMapMaxLevel);
    }
}

void map_center_on_player(const aether::WorldSim& sim, const Ui& ui) {
    ui.map_cx = sim.player().position.x / static_cast<float>(aether::kMapCell);
    ui.map_cy = sim.player().position.y / static_cast<float>(aether::kMapCell);
}

// A rectangle cut to the viewport of the map.
void fill_map_rect(SDL_Renderer* renderer, const MapGeometry& g, float x, float y, float w, float h, Uint8 r, Uint8 gr,
                   Uint8 b, Uint8 a) {
    const float x0 = std::max(x, g.x);
    const float y0 = std::max(y, g.y);
    const float x1 = std::min(x + w, g.x + g.side);
    const float y1 = std::min(y + h, g.y + g.side);
    if (x1 > x0 && y1 > y0) {
        fill_rect(renderer, x0, y0, x1 - x0, y1 - y0, r, gr, b, a);
    }
}

void draw_world_map(SDL_Renderer* renderer, const Assets& assets, const aether::WorldSim& sim, const Ui& ui, int out_w,
                    int out_h, float density) {
    const aether::ChunkStore* store = sim.chunks();
    if (!ui.show_map || store == nullptr) {
        return;
    }
    const aether::WorldParams& params = store->params();
    const int columns = map_columns(params);
    const int rows = map_rows(params);
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    fill_rect(renderer, 0.0F, 0.0F, static_cast<float>(out_w), static_cast<float>(out_h), 4, 10, 24, 235);

    MapGeometry g;
    g.side = std::min(static_cast<float>(out_w), static_cast<float>(out_h)) * 0.8F;
    g.x = (static_cast<float>(out_w) - g.side) / 2.0F;
    g.y = (static_cast<float>(out_h) - g.side) / 2.0F + 10.0F * density;
    if (ui.map_level < 0) {
        map_fit(sim, params, ui, g.side);
    }
    g.cell = g.side / static_cast<float>(std::max(columns, rows)) * static_cast<float>(1 << ui.map_level);
    g.cx = ui.map_cx;
    g.cy = ui.map_cy;
    ui.map_cell_px = g.cell;
    ui.map_view_x = g.x;
    ui.map_view_y = g.y;
    ui.map_view_side = g.side;
    ui.map_view_cells = g.side / g.cell;

    const float ts = std::max(1.0F, std::floor(density));  // scale of the text: the debug font is 8 pixels
    const auto text = [&](float x, float y, const std::string& line, Uint8 r, Uint8 gr, Uint8 b) {
        SDL_SetRenderScale(renderer, ts, ts);
        SDL_SetRenderDrawColor(renderer, 0, 0, 0, 230);  // a dark edge, so that the text reads on pale cells too
        debug_text(renderer, (x + 1.0F) / ts, (y + 1.0F) / ts, line.c_str());
        SDL_SetRenderDrawColor(renderer, r, gr, b, 255);
        debug_text(renderer, x / ts, y / ts, line.c_str());
        SDL_SetRenderScale(renderer, 1.0F, 1.0F);
    };

    fill_rect(renderer, g.x - 3.0F, g.y - 3.0F, g.side + 6.0F, g.side + 6.0F, 40, 70, 110, 255);
    fill_rect(renderer, g.x, g.y, g.side, g.side, 6, 12, 28, 255);  // beyond the edge of the world
    fill_map_rect(renderer, g, g.to_x(0.0F), g.to_y(0.0F), g.cell * static_cast<float>(columns),
                  g.cell * static_cast<float>(rows), 20, 36, 66, 255);  // the world, still unexplored
    static const Uint8 kColors[7][3] = {{60, 110, 190},  {222, 206, 150}, {130, 130, 140}, {235, 240, 245},
                                        {222, 206, 150}, {60, 130, 70},   {110, 180, 90}};
    // A cell is drawn as a grid of n x n sampled tiles (n = 1, 2, 4, 8, 16 from level 1), so that the squares stay
    // about 4 or 5 pixels whatever the zoom: the shape of coasts, mountains and deserts shows when the map is zoomed
    // in.
    const int n = ui.map_level <= 0 ? 1 : 1 << ui.map_level;
    if (ui.map_detail.size() > 6000) {
        ui.map_detail.clear();
    }
    for (const auto& [x, y] : sim.explored()) {
        const float sx = g.to_x(static_cast<float>(x));
        const float sy = g.to_y(static_cast<float>(y));
        if (sx > g.x + g.side || sy > g.y + g.side || sx + g.cell < g.x || sy + g.cell < g.y) {
            continue;
        }
        if (n == 1) {
            auto code = ui.map_codes.find({x, y});
            if (code == ui.map_codes.end()) {
                code =
                    ui.map_codes.emplace(std::make_pair(x, y), aether::biome_code(store->seed(), params, x, y)).first;
            }
            const Uint8* color = kColors[code->second];
            fill_map_rect(renderer, g, sx, sy, std::ceil(g.cell), std::ceil(g.cell), color[0], color[1], color[2], 255);
            continue;
        }
        auto detail = ui.map_detail.find({x, y, n});
        if (detail == ui.map_detail.end()) {
            std::vector<std::uint8_t> codes(static_cast<std::size_t>(n) * static_cast<std::size_t>(n));
            for (int j = 0; j < n; ++j) {
                for (int i = 0; i < n; ++i) {
                    codes[static_cast<std::size_t>(j * n + i)] = static_cast<std::uint8_t>(aether::biome_code_at(
                        store->seed(), params, x * aether::kMapCell + (2 * i + 1) * aether::kMapCell / (2 * n),
                        y * aether::kMapCell + (2 * j + 1) * aether::kMapCell / (2 * n)));
                }
            }
            detail = ui.map_detail.emplace(std::array<int, 3>{x, y, n}, std::move(codes)).first;
        }
        const float sub = g.cell / static_cast<float>(n);
        for (int j = 0; j < n; ++j) {
            for (int i = 0; i < n; ++i) {
                const Uint8* color = kColors[detail->second[static_cast<std::size_t>(j * n + i)]];
                fill_map_rect(renderer, g, sx + sub * static_cast<float>(i), sy + sub * static_cast<float>(j),
                              std::ceil(sub), std::ceil(sub), color[0], color[1], color[2], 255);
            }
        }
    }

    // The places found: settlements in yellow, dungeons and other sites in violet; their names when they fit.
    struct Box {
        float x;
        float y;
        float w;
        float h;
    };
    struct MapLabel {
        Box marker;    // the marker the name belongs to
        int priority;  // towns first, then villages, then the other sites, then hamlets
        const std::string* text;
    };
    std::vector<MapLabel> labels;
    std::vector<Box> obstacles;  // every marker drawn, and then every name placed
    const float boost = 1.0F + 0.4F * static_cast<float>(ui.map_level);
    for (const auto& [x, y] : sim.explored()) {
        const float mx = g.to_x(static_cast<float>(x) + 0.5F);
        const float my = g.to_y(static_cast<float>(y) + 0.5F);
        if (mx < g.x || my < g.y || mx > g.x + g.side || my > g.y + g.side) {
            continue;
        }
        auto marker = ui.map_markers.find({x, y});
        if (marker == ui.map_markers.end()) {
            marker =
                ui.map_markers.emplace(std::make_pair(x, y), aether::settlement_marker(store->seed(), params, x, y))
                    .first;
        }
        if (!marker->second) {
            continue;
        }
        const std::string& kind = marker->second->kind;
        const bool place = kind == "town" || kind == "village" || kind == "hamlet";
        const float size = (kind == "town" ? 7.0F : (kind == "village" ? 5.0F : 4.0F)) * density * boost;
        fill_map_rect(renderer, g, mx - size / 2.0F - 1.0F, my - size / 2.0F - 1.0F, size + 2.0F, size + 2.0F, 20, 20,
                      30, 255);
        if (place) {
            fill_map_rect(renderer, g, mx - size / 2.0F, my - size / 2.0F, size, size, 255, 235, 150, 255);
        } else {
            fill_map_rect(renderer, g, mx - size / 2.0F, my - size / 2.0F, size, size, 205, 120, 255, 255);
        }
        const Box box{mx - size / 2.0F - 1.0F, my - size / 2.0F - 1.0F, size + 2.0F, size + 2.0F};
        obstacles.push_back(box);
        if (kind != "hamlet" || ui.map_level >= 3) {
            const int priority = kind == "town" ? 0 : (kind == "village" ? 1 : (kind == "hamlet" ? 3 : 2));
            labels.push_back({box, priority, &marker->second->name});
        }
    }
    const float line_h = 10.0F * ts;
    const auto overlaps = [](const Box& a, const Box& b) {
        return a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
    };
    const auto inside = [&](const Box& a) {
        return a.x >= g.x && a.x + a.w <= g.x + g.side && a.y >= g.y && a.y + a.h <= g.y + g.side;
    };
    // Tries a box in turn at each candidate place and keeps the first that is in the view and over nothing; the
    // marker of the name itself does not count.
    const auto place_text = [&](const std::vector<Box>& candidates, const Box* own, const std::string& name) {
        for (const Box& c : candidates) {
            const bool free = inside(c) && std::none_of(obstacles.begin(), obstacles.end(), [&](const Box& o) {
                                  return (own == nullptr || &o != own) && overlaps(c, o);
                              });
            if (free) {
                obstacles.push_back(c);
                text(c.x, c.y, name, 255, 255, 255);
                return true;
            }
        }
        return false;
    };
    std::stable_sort(labels.begin(), labels.end(),
                     [](const MapLabel& a, const MapLabel& b) { return a.priority < b.priority; });
    for (const MapLabel& label : labels) {
        const float w = text_columns(*label.text) * 8.0F * ts;
        const Box& m = label.marker;
        const Box* own = nullptr;
        for (const Box& o : obstacles) {  // the marker of this name, found again in the list
            if (o.x == m.x && o.y == m.y && o.w == m.w) {
                own = &o;
                break;
            }
        }
        const float cx = m.x + m.w / 2.0F;
        place_text({{m.x + m.w + 3.0F, m.y + m.h / 2.0F - line_h / 2.0F, w, line_h},
                    {m.x - 3.0F - w, m.y + m.h / 2.0F - line_h / 2.0F, w, line_h},
                    {cx - w / 2.0F, m.y + m.h + 2.0F, w, line_h},
                    {cx - w / 2.0F, m.y - 2.0F - line_h, w, line_h}},
                   own, *label.text);
    }
    for (const aether::Region& region : params.regions) {
        const int rx =
            static_cast<int>(static_cast<std::int64_t>(region.x_pm) * params.width / 1000) / aether::kMapCell;
        const int ry =
            static_cast<int>(static_cast<std::int64_t>(region.y_pm) * params.height / 1000) / aether::kMapCell;
        if (sim.explored().count({rx, ry}) == 0) {
            continue;
        }
        const std::string name = assets.pack.text(ui.lang, region.name);
        const float width = text_columns(name) * 8.0F * ts;
        const float cx = g.to_x(static_cast<float>(rx));
        const float cy = g.to_y(static_cast<float>(ry));
        // In gold, below the center of the region, or above it, or on it.
        const Box candidates[] = {{cx - width / 2.0F, cy + 14.0F * density, width, line_h},
                                  {cx - width / 2.0F, cy - 14.0F * density - line_h, width, line_h},
                                  {cx - width / 2.0F, cy - line_h / 2.0F, width, line_h}};
        for (const Box& c : candidates) {
            const bool free = inside(c) && std::none_of(obstacles.begin(), obstacles.end(),
                                                        [&](const Box& o) { return overlaps(c, o); });
            if (free) {
                obstacles.push_back(c);
                text(c.x, c.y, name, 255, 215, 120);
                break;
            }
        }
    }

    // The Threshold Stones that were woken: small pale squares.
    for (const auto& [stone_x, stone_y] : sim.stones()) {
        const float sx = g.to_x(static_cast<float>(stone_x) / static_cast<float>(aether::kMapCell));
        const float sy = g.to_y(static_cast<float>(stone_y) / static_cast<float>(aether::kMapCell));
        const float ss = 5.0F * density;
        fill_map_rect(renderer, g, sx - ss / 2.0F - 1.0F, sy - ss / 2.0F - 1.0F, ss + 2.0F, ss + 2.0F, 20, 20, 30, 255);
        fill_map_rect(renderer, g, sx - ss / 2.0F, sy - ss / 2.0F, ss, ss, 140, 255, 235, 255);
    }
    // The player: a red square with a white edge, kept on the edge of the view when it is out of it.
    const float px = g.to_x(sim.player().position.x / static_cast<float>(aether::kMapCell));
    const float py = g.to_y(sim.player().position.y / static_cast<float>(aether::kMapCell));
    const float margin = 8.0F * density;
    const bool off = px < g.x || py < g.y || px > g.x + g.side || py > g.y + g.side;
    const float dx = std::clamp(px, g.x + margin, g.x + g.side - margin);
    const float dy = std::clamp(py, g.y + margin, g.y + g.side - margin);
    const float pulse = 1.0F + 0.25F * std::sin(static_cast<float>(SDL_GetTicks()) / 180.0F);
    const float ps = 7.0F * density * pulse;
    fill_rect(renderer, dx - ps / 2.0F - 2.0F, dy - ps / 2.0F - 2.0F, ps + 4.0F, ps + 4.0F, 255, 255, 255, 255);
    fill_rect(renderer, dx - ps / 2.0F, dy - ps / 2.0F, ps, ps, 255, off ? 150 : 50, off ? 40 : 50, 255);

    if (ui.has_goal) {  // the goal: a green square, and a line from the player, both kept inside the view
        const float gx =
            std::clamp(g.to_x(ui.goal_x / static_cast<float>(aether::kMapCell)), g.x + margin, g.x + g.side - margin);
        const float gy =
            std::clamp(g.to_y(ui.goal_y / static_cast<float>(aether::kMapCell)), g.y + margin, g.y + g.side - margin);
        SDL_SetRenderDrawColor(renderer, 90, 255, 120, 200);
        SDL_RenderLine(renderer, dx, dy, gx, gy);
        fill_rect(renderer, gx - 5.0F * density - 2.0F, gy - 5.0F * density - 2.0F, 10.0F * density + 4.0F,
                  10.0F * density + 4.0F, 20, 20, 30, 255);
        fill_rect(renderer, gx - 5.0F * density, gy - 5.0F * density, 10.0F * density, 10.0F * density, 90, 255, 120,
                  255);
    }

    // The title, then the keys, the position and what the colors mean, under the view.
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_SetRenderScale(renderer, 2.0F, 2.0F);
    debug_text(renderer, g.x / 2.0F, (g.y - 28.0F * density) / 2.0F, assets.pack.text(ui.lang, "$i18n:ui.map").c_str());
    SDL_SetRenderScale(renderer, 1.0F, 1.0F);
    const float row = 12.0F * ts;
    float ty = g.y + g.side + 8.0F * density;
    text(g.x, ty, assets.pack.text(ui.lang, "$i18n:ui.map_help"), 150, 200, 255);
    ty += row;
    text(g.x, ty, assets.pack.text(ui.lang, "$i18n:ui.map_help2"), 150, 200, 255);
    ty += row;
    const std::string where = assets.pack.text(ui.lang, "$i18n:ui.map_pos",
                                               {{"x", static_cast<std::int64_t>(std::floor(sim.player().position.x))},
                                                {"y", static_cast<std::int64_t>(std::floor(sim.player().position.y))},
                                                {"zoom", std::int64_t{1} << ui.map_level}});
    text(g.x, ty, where, 255, 255, 255);
    ty += row;
    float pen = g.x;
    const auto key = [&](Uint8 r, Uint8 gr, Uint8 b, const char* id) {
        fill_rect(renderer, pen, ty + 1.0F, 8.0F * ts, 8.0F * ts, r, gr, b, 255);
        const std::string label = assets.pack.text(ui.lang, id);
        text(pen + 12.0F * ts, ty, label, 220, 220, 230);
        pen += (12.0F + 8.0F + text_columns(label) * 8.0F) * ts;
    };
    key(255, 50, 50, "$i18n:ui.map_key_you");
    key(255, 235, 150, "$i18n:ui.map_key_place");
    key(205, 120, 255, "$i18n:ui.map_key_site");
    key(140, 255, 235, "$i18n:ui.map_key_stone");
    key(90, 255, 120, "$i18n:ui.map_key_goal");
}

// Night and weather over the world, and the clock (spec 08). Presentation only.
void draw_atmosphere(SDL_Renderer* renderer, const Assets& assets, const aether::WorldSim& sim, const Ui& ui, int out_w,
                     int out_h, float density, Uint64 now_ms) {
    const auto time = sim.time();
    if (!time) {
        return;
    }
    const int dark = 1000 - time->effective_light_pm;  // 0 = full daylight
    if (dark > 0) {
        SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
        SDL_SetRenderDrawColor(renderer, 8, 14, 44, static_cast<Uint8>(dark * 175 / 1000));
        const SDL_FRect all{0.0F, 0.0F, static_cast<float>(out_w), static_cast<float>(out_h)};
        SDL_RenderFillRect(renderer, &all);
    }
    if (time->season_index >= 0 && sim.chunks() != nullptr) {  // the tint of the season (spec 08)
        const aether::Season& season =
            sim.chunks()->params().time.seasons[static_cast<std::size_t>(time->season_index)];
        if (season.tint[3] > 0) {
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
            SDL_SetRenderDrawColor(renderer, static_cast<Uint8>(season.tint[0]), static_cast<Uint8>(season.tint[1]),
                                   static_cast<Uint8>(season.tint[2]), static_cast<Uint8>(season.tint[3]));
            const SDL_FRect all{0.0F, 0.0F, static_cast<float>(out_w), static_cast<float>(out_h)};
            SDL_RenderFillRect(renderer, &all);
        }
    }
    if (time->rain_pm > 0) {
        const int drops = 160 * time->rain_pm / 1000;
        SDL_SetRenderDrawColor(renderer, 170, 190, 230, 150);
        for (int i = 0; i < drops; ++i) {
            const Uint64 fall = now_ms / 2 + static_cast<Uint64>(i) * 977;
            const float x =
                static_cast<float>((static_cast<Uint64>(i) * 7919 + now_ms / 5) % static_cast<Uint64>(out_w));
            const float y = static_cast<float>(fall % static_cast<Uint64>(out_h));
            SDL_RenderLine(renderer, x, y, x - 3.0F * density, y + 12.0F * density);
        }
    }
    const int hour = time->tod_pm * 24 / 1000;
    const int minute = (time->tod_pm * 1440 / 1000) % 60;
    char clock[16];
    std::snprintf(clock, sizeof(clock), "%02d:%02d", hour, minute);
    std::string season_name;
    if (time->season_index >= 0 && sim.chunks() != nullptr) {
        season_name = assets.pack.text(
            ui.lang,
            "$i18n:season." + sim.chunks()->params().time.seasons[static_cast<std::size_t>(time->season_index)].id);
    }
    const std::string line = assets.pack.text(
        ui.lang, "$i18n:ui.clock",
        {{"day", static_cast<std::int64_t>(time->day)}, {"time", std::string(clock)}, {"season", season_name}});
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_SetRenderScale(renderer, 2.0F, 2.0F);
    outlined_text(renderer, (static_cast<float>(out_w) - 12.0F * density) / 2.0F - text_columns(line) * 8.0F,
                  12.0F * density / 2.0F, line.c_str());
    if (const aether::ChunkStore* store = sim.chunks()) {
        const aether::WorldParams& params = store->params();
        const aether::Region& region = params.regions[static_cast<std::size_t>(
            aether::region_at(params, static_cast<int>(std::floor(sim.player().position.x)),
                              static_cast<int>(std::floor(sim.player().position.y))))];
        const std::string name = assets.pack.text(ui.lang, region.name);
        SDL_SetRenderDrawColor(renderer, 255, 215, 120, 255);
        outlined_text(renderer, (static_cast<float>(out_w) - 12.0F * density) / 2.0F - text_columns(name) * 8.0F,
                      12.0F * density / 2.0F + 12.0F, name.c_str());
    }
    SDL_SetRenderScale(renderer, 1.0F, 1.0F);
}

// "world" or "demo": which map this run plays on (stored in the saves).
std::string g_map_name = "world";

fs::path save_dir() {
    fs::path dir;
    if (char* pref = SDL_GetPrefPath("progliodario", "Aethermoor")) {
        dir = fs::path(pref) / "saves";
        SDL_free(pref);
    } else {
        dir = fs::temp_directory_path() / "aethermoor_saves";
    }
    std::error_code ec;
    fs::create_directories(dir, ec);
    return dir;
}

// Writes `<slot>.json` atomically: a temporary file first, then a rename over the old save.
bool write_text_atomic(const fs::path& file, const std::string& text) {
    const fs::path temp = fs::path(file).concat(".tmp");
    {
        std::ofstream out(temp, std::ios::binary | std::ios::trunc);
        out << text;
        if (!out) {
            return false;
        }
    }
    std::error_code ec;
    fs::rename(temp, file, ec);
    return !ec;
}

std::optional<std::string> read_text_file(const fs::path& file) {
    std::ifstream in(file, std::ios::binary);
    if (!in) {
        return std::nullopt;
    }
    return std::string(std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>());
}

constexpr int kSlotCount = 3;  // the games a player can keep (spec 12, "Slots")

// The folder of the saves of a game (1..kSlotCount).
fs::path slot_dir(int slot) {
    const fs::path dir = save_dir() / ("slot" + std::to_string(slot));
    std::error_code ec;
    fs::create_directories(dir, ec);
    return dir;
}

// The folder of the saves of this run, set once the game is chosen.
fs::path g_slot_dir;

// Saves written before slots existed become the first game.
void migrate_legacy_saves() {
    std::error_code ec;
    if (!fs::exists(save_dir() / "auto.json", ec) || fs::exists(slot_dir(1) / "auto.json", ec)) {
        return;
    }
    for (const char* name : {"auto.json", "quick.json"}) {
        if (fs::exists(save_dir() / name, ec)) {
            fs::rename(save_dir() / name, slot_dir(1) / name, ec);
        }
    }
}

struct SlotInfo {
    bool used = false;
    int level = 1;
    std::int64_t gold = 0;
};

SlotInfo read_slot(int slot) {
    SlotInfo info;
    if (const auto text = read_text_file(slot_dir(slot) / "auto.json")) {
        if (const auto peek = aether::save_peek(*text)) {
            info.used = true;
            info.level = peek->level;
            info.gold = peek->gold;
        }
    }
    return info;
}

void delete_slot(int slot) {
    std::error_code ec;
    for (const char* name : {"auto.json", "auto.json.tmp", "quick.json", "quick.json.tmp"}) {
        fs::remove(slot_dir(slot) / name, ec);
    }
}

// The settings file (spec 16): the language chosen by the player; without it the language of the system is used.
fs::path settings_file() { return save_dir().parent_path() / "settings.json"; }

void save_language(const std::string& lang) {
    write_text_atomic(settings_file(), "{\n  \"language\": \"" + lang + "\"\n}\n");
}

std::optional<std::string> saved_language() {
    const auto text = read_text_file(settings_file());
    if (!text || text->find("\"language\"") == std::string::npos) {
        return std::nullopt;
    }
    if (text->find("\"it\"") != std::string::npos) {
        return "it";
    }
    if (text->find("\"en\"") != std::string::npos) {
        return "en";
    }
    return std::nullopt;
}

aether::SaveMeta save_meta(const aether::WorldSim& sim) {
    aether::SaveMeta meta;
    meta.map = g_map_name;
    meta.game_version = std::string(aether::game_version());
    meta.protagonist = g_protagonist_id;
    meta.seed = sim.combat().seed;
    return meta;
}

bool save_game(const aether::WorldSim& sim, const fs::path& file) {
    return write_text_atomic(file, aether::save_to_json(sim.capture(), save_meta(sim)));
}

bool load_game(aether::WorldSim& sim, const fs::path& file, std::string& error) {
    const auto text = read_text_file(file);
    if (!text) {
        error = "no save file";
        return false;
    }
    const auto state = aether::save_from_json(*text, error);
    return state.has_value() && sim.restore(*state, error);
}

std::string dialogue_text(const aether::Pack& pack, const std::string& lang, const std::string& reference,
                          const std::map<std::string, std::string>& args);

void notify(Ui& ui, const std::string& text) {
    ui.message = text;
    ui.message_frames = 150;
}

// Confirms the current dialogue line or choice.
void activate_dialogue(aether::WorldSim& sim, Ui& ui) {
    aether::Story& story = sim.story();
    const aether::DialogueView view = story.dialogue_view();
    if (!view.active) {
        if (story.npc_in_range() == nullptr && sim.use_stone()) {  // a Threshold Stone (spec 09)
            const aether::WorldSim::Travel* travel = sim.travel();
            ui.travel_cursor = travel->here == 0 && travel->stops.size() > 1 ? 1 : 0;
        } else {
            story.interact();
        }
        ui.choice_index = 0;
    } else if (view.is_choice) {
        story.choose(ui.choice_index);
        ui.choice_index = 0;
    } else {
        story.advance();
        ui.choice_index = 0;
    }
}

void move_choice(aether::WorldSim& sim, Ui& ui, int delta) {
    const aether::DialogueView view = sim.story().dialogue_view();
    if (view.active && view.is_choice && !view.choices.empty()) {
        const int count = static_cast<int>(view.choices.size());
        ui.choice_index = (ui.choice_index + delta + count) % count;
    }
}

// "base:item/slime_gel" -> text key "item.slime_gel"
std::string item_key(const std::string& item_id) {
    std::string key = item_id.substr(item_id.find(':') + 1);
    std::replace(key.begin(), key.end(), '/', '.');
    return key;
}

// The bag: move the cursor and use the selected item (spec 06).
void bag_move(const aether::WorldSim& sim, Ui& ui, int delta) {
    const int count = static_cast<int>(sim.inventory().size());
    ui.bag_cursor = count > 0 ? (std::clamp(ui.bag_cursor, 0, count - 1) + delta + count) % count : 0;
}

void bag_use(aether::WorldSim& sim, const Assets& assets, Ui& ui) {
    const auto& items = sim.inventory();
    if (items.empty()) {
        return;
    }
    auto it = items.begin();
    std::advance(it, std::clamp(ui.bag_cursor, 0, static_cast<int>(items.size()) - 1));
    const std::string item_id = it->first;
    const std::string name =
        assets.pack.text(ui.lang, "$i18n:" + item_key(item_id) + ".name", {{"count", std::int64_t{1}}});
    const auto def = sim.combat().items.find(item_id);
    const bool wearable =
        def != sim.combat().items.end() && (def->second.kind == "weapon" || def->second.kind == "armor");
    if (wearable && sim.equip(item_id)) {
        notify(ui, assets.pack.text(ui.lang, "$i18n:ui.item_equipped", {{"item", name}}));
    } else if (!wearable && sim.use_item(item_id)) {
        notify(ui, assets.pack.text(ui.lang, "$i18n:ui.item_used", {{"item", name}}));
        bag_move(sim, ui, 0);
    } else {
        notify(ui, assets.pack.text(ui.lang, "$i18n:ui.item_unchanged"));
    }
}

// The shop (spec 06): what is listed now, with the price of each entry.
std::vector<std::pair<std::string, std::int64_t>> shop_entries(const aether::WorldSim& sim, const Ui& ui) {
    std::vector<std::pair<std::string, std::int64_t>> entries;
    if (sim.shop() == nullptr) {
        return entries;
    }
    if (!ui.shop_sell) {
        for (const std::string& id : sim.shop()->stock) {
            entries.emplace_back(id, sim.buy_price(id));
        }
    } else {
        for (const auto& [id, quantity] : sim.inventory()) {
            if (quantity > 0 && sim.sell_price(id) > 0) {
                entries.emplace_back(id, sim.sell_price(id));
            }
        }
    }
    return entries;
}

void shop_move(const aether::WorldSim& sim, Ui& ui, int delta) {
    const int count = static_cast<int>(shop_entries(sim, ui).size());
    ui.shop_cursor = count > 0 ? (std::clamp(ui.shop_cursor, 0, count - 1) + delta + count) % count : 0;
}

void shop_confirm(aether::WorldSim& sim, const Assets& assets, Ui& ui) {
    const auto entries = shop_entries(sim, ui);
    if (entries.empty()) {
        return;
    }
    const std::string id =
        entries[static_cast<std::size_t>(std::clamp(ui.shop_cursor, 0, static_cast<int>(entries.size()) - 1))].first;
    const std::string name = assets.pack.text(ui.lang, "$i18n:" + item_key(id) + ".name", {{"count", std::int64_t{1}}});
    const bool done = ui.shop_sell ? sim.sell(id) : sim.buy(id);
    if (done) {
        notify(ui, assets.pack.text(ui.lang, ui.shop_sell ? "$i18n:ui.sold" : "$i18n:ui.bought", {{"item", name}}));
        shop_move(sim, ui, 0);
    } else {
        notify(ui, assets.pack.text(ui.lang, "$i18n:ui.cannot_do"));
    }
}

void handle_shop_key(aether::WorldSim& sim, const Assets& assets, Ui& ui, SDL_Keycode key) {
    if (key == SDLK_UP || key == SDLK_W) {
        shop_move(sim, ui, -1);
    } else if (key == SDLK_DOWN || key == SDLK_S) {
        shop_move(sim, ui, 1);
    } else if (key == SDLK_TAB) {
        ui.shop_sell = !ui.shop_sell;
        ui.shop_cursor = 0;
    } else if (key == SDLK_E || key == SDLK_RETURN || key == SDLK_SPACE) {
        shop_confirm(sim, assets, ui);
    }
}

// The guild board (spec 07, "Guild").
void board_move(const aether::WorldSim& sim, Ui& ui, int delta) {
    const int count = sim.board() == nullptr ? 0 : static_cast<int>(sim.board()->offers.size());
    ui.board_cursor = count > 0 ? (std::clamp(ui.board_cursor, 0, count - 1) + delta + count) % count : 0;
}

void board_accept(aether::WorldSim& sim, const Assets& assets, Ui& ui) {
    if (sim.board() == nullptr || sim.board()->offers.empty()) {
        return;
    }
    const int slot = std::clamp(ui.board_cursor, 0, static_cast<int>(sim.board()->offers.size()) - 1);
    const aether::Offer offer = sim.board()->offers[static_cast<std::size_t>(slot)];
    if (sim.accept_offer(slot)) {
        const aether::QuestDef quest = aether::quest_from_offer(offer);
        notify(ui, assets.pack.text(ui.lang, "$i18n:ui.quest_accepted",
                                    {{"quest", dialogue_text(assets.pack, ui.lang, quest.name, quest.args)}}));
    } else {
        notify(ui, assets.pack.text(ui.lang, "$i18n:ui.cannot_do"));
    }
}

void handle_board_key(aether::WorldSim& sim, const Assets& assets, Ui& ui, SDL_Keycode key) {
    if (key == SDLK_UP || key == SDLK_W) {
        board_move(sim, ui, -1);
    } else if (key == SDLK_DOWN || key == SDLK_S) {
        board_move(sim, ui, 1);
    } else if (key == SDLK_E || key == SDLK_RETURN || key == SDLK_SPACE) {
        board_accept(sim, assets, ui);
    }
}

// The Threshold Stones (spec 09).
void travel_move(const aether::WorldSim& sim, Ui& ui, int delta) {
    const int count = sim.travel() == nullptr ? 0 : static_cast<int>(sim.travel()->stops.size());
    ui.travel_cursor = count > 0 ? (std::clamp(ui.travel_cursor, 0, count - 1) + delta + count) % count : 0;
}

void travel_go(aether::WorldSim& sim, const Assets& assets, Ui& ui) {
    if (sim.travel() == nullptr) {
        return;
    }
    const aether::WorldSim::StoneStop stop = sim.travel()->stops[static_cast<std::size_t>(
        std::clamp(ui.travel_cursor, 0, static_cast<int>(sim.travel()->stops.size()) - 1))];
    if (sim.travel_to(ui.travel_cursor)) {
        notify(ui, assets.pack.text(ui.lang, "$i18n:ui.traveled", {{"place", stop.place}}));
    } else {
        notify(ui, assets.pack.text(ui.lang, "$i18n:ui.cannot_do"));
    }
}

void handle_travel_key(aether::WorldSim& sim, const Assets& assets, Ui& ui, SDL_Keycode key) {
    if (key == SDLK_UP || key == SDLK_W) {
        travel_move(sim, ui, -1);
    } else if (key == SDLK_DOWN || key == SDLK_S) {
        travel_move(sim, ui, 1);
    } else if (key == SDLK_E || key == SDLK_RETURN || key == SDLK_SPACE) {
        travel_go(sim, assets, ui);
    }
}

// The goal is kept with the game: a file `goal.txt` ("x y" in tiles) in the folder of the slot, removed when the goal
// is.
void save_goal(const Ui& ui) {
    const fs::path file = g_slot_dir / "goal.txt";
    std::error_code ec;
    if (!ui.has_goal) {
        fs::remove(file, ec);
        return;
    }
    std::ofstream out(file, std::ios::trunc);
    out << static_cast<long long>(ui.goal_x) << " " << static_cast<long long>(ui.goal_y) << "\n";
}

void load_goal(Ui& ui) {
    ui.has_goal = false;
    if (const auto text = read_text_file(g_slot_dir / "goal.txt")) {
        char* end = nullptr;
        const long long gx = std::strtoll(text->c_str(), &end, 10);
        char* end_y = nullptr;
        const long long gy = std::strtoll(end, &end_y, 10);
        if (end != text->c_str() && end_y != end) {
            ui.goal_x = static_cast<float>(gx);
            ui.goal_y = static_cast<float>(gy);
            ui.has_goal = true;
        }
    }
}

// Marks the goal at a map position given in cells (fractional), inside the world.
void set_goal(const aether::WorldSim& sim, const Assets& assets, Ui& ui, float cell_x, float cell_y) {
    if (sim.chunks() == nullptr) {
        return;
    }
    const aether::WorldParams& params = sim.chunks()->params();
    ui.goal_x = std::clamp(cell_x * static_cast<float>(aether::kMapCell), 0.0F, static_cast<float>(params.width - 1));
    ui.goal_y = std::clamp(cell_y * static_cast<float>(aether::kMapCell), 0.0F, static_cast<float>(params.height - 1));
    ui.has_goal = true;
    save_goal(ui);
    notify(ui, assets.pack.text(ui.lang, "$i18n:ui.goal_set"));
}

// Moves the view to the next place found (settlements, dungeons, lairs), nearest to the player first, and says its
// name.
void map_next_place(const aether::WorldSim& sim, Ui& ui) {
    const aether::ChunkStore* store = sim.chunks();
    if (store == nullptr) {
        return;
    }
    struct Place {
        float x;
        float y;
        float distance;
        const std::string* name;
    };
    std::vector<Place> places;
    for (const auto& [cx, cy] : sim.explored()) {
        auto marker = ui.map_markers.find({cx, cy});
        if (marker == ui.map_markers.end()) {
            marker =
                ui.map_markers
                    .emplace(std::make_pair(cx, cy), aether::settlement_marker(store->seed(), store->params(), cx, cy))
                    .first;
        }
        if (marker->second) {
            const float mx = static_cast<float>(marker->second->px);
            const float my = static_cast<float>(marker->second->py);
            const float dx = mx - sim.player().position.x;
            const float dy = my - sim.player().position.y;
            places.push_back({mx, my, dx * dx + dy * dy, &marker->second->name});
        }
    }
    if (places.empty()) {
        return;
    }
    std::stable_sort(places.begin(), places.end(), [](const Place& a, const Place& b) {
        return a.distance != b.distance ? a.distance < b.distance : *a.name < *b.name;
    });
    ui.map_pick = (ui.map_pick + 1) % static_cast<int>(places.size());
    const Place& place = places[static_cast<std::size_t>(ui.map_pick)];
    ui.map_cx = place.x / static_cast<float>(aether::kMapCell);
    ui.map_cy = place.y / static_cast<float>(aether::kMapCell);
    notify(ui, *place.name);
}

// The keys of the world map (spec 16): zoom, move the view, back to the player, frame everything explored.
void handle_map_key(const aether::WorldSim& sim, const Assets& assets, Ui& ui, SDL_Keycode key) {
    const float step = ui.map_view_cells / 6.0F;
    if (key == SDLK_PLUS || key == SDLK_EQUALS || key == SDLK_KP_PLUS) {
        map_zoom(ui, 1);
    } else if (key == SDLK_MINUS || key == SDLK_KP_MINUS) {
        map_zoom(ui, -1);
    } else if (key == SDLK_UP || key == SDLK_W) {
        map_pan(sim, ui, 0.0F, -step);
    } else if (key == SDLK_DOWN || key == SDLK_S) {
        map_pan(sim, ui, 0.0F, step);
    } else if (key == SDLK_LEFT || key == SDLK_A) {
        map_pan(sim, ui, -step, 0.0F);
    } else if (key == SDLK_RIGHT || key == SDLK_D) {
        map_pan(sim, ui, step, 0.0F);
    } else if (key == SDLK_TAB) {
        map_next_place(sim, ui);
    } else if (key == SDLK_P) {
        set_goal(sim, assets, ui, ui.map_cx, ui.map_cy);
    } else if (key == SDLK_X) {
        ui.has_goal = false;
        save_goal(ui);
        notify(ui, assets.pack.text(ui.lang, "$i18n:ui.goal_cleared"));
    } else if (key == SDLK_C) {
        map_center_on_player(sim, ui);
    } else if (key == SDLK_0 || key == SDLK_KP_0 || key == SDLK_HOME) {
        ui.map_level = -1;
    }
}

void handle_dialogue_key(aether::WorldSim& sim, Ui& ui, SDL_Keycode key) {
    const bool active = sim.story().dialogue_active();
    if (key == SDLK_E || key == SDLK_RETURN || (active && key == SDLK_SPACE)) {
        activate_dialogue(sim, ui);
    } else if (active && (key == SDLK_UP || key == SDLK_W)) {
        move_choice(sim, ui, -1);
    } else if (active && (key == SDLK_DOWN || key == SDLK_S)) {
        move_choice(sim, ui, 1);
    } else if (active && key >= SDLK_1 && key <= SDLK_9) {
        const aether::DialogueView view = sim.story().dialogue_view();
        const int index = static_cast<int>(key - SDLK_1);
        if (view.is_choice && index < static_cast<int>(view.choices.size())) {
            ui.choice_index = index;
            activate_dialogue(sim, ui);
        }
    }
}

void handle_dialogue_button(aether::WorldSim& sim, Ui& ui, Uint8 button) {
    const bool active = sim.story().dialogue_active();
    if (button == SDL_GAMEPAD_BUTTON_WEST || (active && button == SDL_GAMEPAD_BUTTON_SOUTH)) {
        activate_dialogue(sim, ui);
    } else if (active && button == SDL_GAMEPAD_BUTTON_DPAD_UP) {
        move_choice(sim, ui, -1);
    } else if (active && button == SDL_GAMEPAD_BUTTON_DPAD_DOWN) {
        move_choice(sim, ui, 1);
    }
}

// A dialogue text with its arguments (spec 07): values that start with "$i18n:" are text keys resolved with the plain
// ones.
std::string dialogue_text(const aether::Pack& pack, const std::string& lang, const std::string& reference,
                          const std::map<std::string, std::string>& args) {
    aether::FormatArgs plain;
    for (const auto& [key, value] : args) {
        if (value.rfind("$i18n:", 0) != 0) {
            plain[key] = value;
        }
    }
    aether::FormatArgs all = plain;
    for (const auto& [key, value] : args) {
        if (value.rfind("$i18n:", 0) == 0) {
            all[key] = pack.text(lang, value, plain);
        }
    }
    return pack.text(lang, reference, all);
}

// The name shown for a speaker: "npc" is the NPC being talked to, any other one has a text.
std::string speaker_name(const aether::Pack& pack, const std::string& lang, const std::string& speaker,
                         const std::map<std::string, std::string>& args) {
    if (speaker == "npc") {
        const auto name = args.find("npc");
        return name == args.end() ? std::string() : name->second;
    }
    return pack.text(lang, "$i18n:speaker." + speaker);
}

void draw_dialogue(SDL_Renderer* renderer, const Assets& assets, const aether::WorldSim& sim, const Ui& ui, int out_w,
                   int out_h, float density) {
    const aether::DialogueView view = sim.story().dialogue_view();
    if (!view.active) {
        return;
    }
    constexpr float kScale = 2.0F;
    const float char_w = 8.0F * kScale;
    const float margin = 24.0F * density;
    const auto columns =
        static_cast<std::size_t>(std::max(20.0F, (static_cast<float>(out_w) - 2.0F * margin - 16.0F) / char_w));
    std::vector<std::string> lines;
    std::string heading;
    if (view.is_choice) {
        if (!ui.last_text.empty()) {
            heading = speaker_name(assets.pack, ui.lang, ui.last_speaker, ui.last_args);
            lines = wrap_text(dialogue_text(assets.pack, ui.lang, ui.last_text, ui.last_args), columns);
            lines.emplace_back();
        }
        for (std::size_t i = 0; i < view.choices.size(); ++i) {
            const std::string text = dialogue_text(assets.pack, ui.lang, view.choices[i], view.args);
            const std::vector<std::string> wrapped = wrap_text(text, columns > 6 ? columns - 6 : columns);
            lines.push_back((static_cast<int>(i) == ui.choice_index ? "> " : "  ") + std::to_string(i + 1) + ". " +
                            (wrapped.empty() ? std::string() : wrapped.front()));
        }
    } else {
        heading = speaker_name(assets.pack, ui.lang, view.speaker, view.args);
        lines = wrap_text(dialogue_text(assets.pack, ui.lang, view.text, view.args), columns);
    }
    const float line_h = 8.0F * kScale + 6.0F;
    const float box_h = (static_cast<float>(lines.size()) + (heading.empty() ? 0.0F : 1.0F)) * line_h + 24.0F;
    const float box_y = static_cast<float>(out_h) - box_h - margin;
    draw_panel(renderer, margin, box_y, static_cast<float>(out_w) - 2.0F * margin, box_h, 111, 227, 255, 235);
    SDL_SetRenderScale(renderer, kScale, kScale);
    float y = (box_y + 12.0F) / kScale;
    if (!heading.empty()) {
        SDL_SetRenderDrawColor(renderer, 255, 215, 120, 255);
        debug_text(renderer, (margin + 12.0F) / kScale, y, heading.c_str());
        y += line_h / kScale;
    }
    SDL_SetRenderDrawColor(renderer, 235, 245, 255, 255);
    for (const std::string& line : lines) {
        debug_text(renderer, (margin + 12.0F) / kScale, y, line.c_str());
        y += line_h / kScale;
    }
    SDL_SetRenderScale(renderer, 1.0F, 1.0F);
}

void draw_quest_tracker(SDL_Renderer* renderer, const Assets& assets, const aether::WorldSim& sim, const Ui& ui,
                        int out_w, float density) {
    const aether::Story& story = sim.story();
    constexpr float kScale = 2.0F;
    const float x = (static_cast<float>(out_w) - 410.0F * density) / kScale;
    float y = 12.0F * density / kScale +
              32.0F;  // below the clock and the name of the region, which are right-aligned in the corner
    SDL_SetRenderScale(renderer, kScale, kScale);
    char line[96];
    std::snprintf(line, sizeof(line), "%s",
                  assets.pack.text(ui.lang, "$i18n:ui.gold", {{"gold", story.gold()}}).c_str());
    SDL_SetRenderDrawColor(renderer, 255, 215, 120, 255);
    outlined_text(renderer, x, y, line);
    if (sim.streamed()) {
        if (const aether::ChunkStore* store = sim.chunks()) {
            std::string letter = store->params().guild.ranks[static_cast<std::size_t>(sim.guild_rank())].id;
            for (char& c : letter) {
                c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
            }
            const std::string text = assets.pack.text(ui.lang, "$i18n:ui.rank", {{"rank", letter}});
            outlined_text(renderer, x - text_columns(text) * 8.0F - 8.0F, y, text.c_str());
        }
    }
    y += 14.0F;
    if (sim.streamed()) {
        const float px = sim.player().position.x;
        const float py = sim.player().position.y;
        SDL_SetRenderDrawColor(renderer, 170, 190, 210, 255);
        outlined_text(renderer, x, y,
                      assets.pack
                          .text(ui.lang, "$i18n:ui.coords",
                                {{"x", static_cast<std::int64_t>(std::floor(px))},
                                 {"y", static_cast<std::int64_t>(std::floor(py))}})
                          .c_str());
        y += 12.0F;
        if (ui.has_goal) {
            const float dx = ui.goal_x - px;
            const float dy = ui.goal_y - py;
            const int distance = static_cast<int>(std::lround(std::sqrt(dx * dx + dy * dy)));
            std::string goal;
            if (distance < 6) {
                goal = assets.pack.text(ui.lang, "$i18n:ui.goal_here");
            } else {
                static const char* kDirections[8] = {"e", "se", "s", "sw", "w", "nw", "n", "ne"};
                const float sector = std::atan2(dy, dx) / (3.14159265F / 4.0F);  // 0 east, 2 south: y points down
                const int index = (static_cast<int>(std::lround(sector)) + 8) % 8;
                goal = assets.pack.text(
                    ui.lang, "$i18n:ui.goal",
                    {{"dir", assets.pack.text(ui.lang, std::string("$i18n:ui.dir_") + kDirections[index])},
                     {"dist", static_cast<std::int64_t>(distance)}});
            }
            SDL_SetRenderDrawColor(renderer, 90, 255, 120, 255);
            outlined_text(renderer, x, y, goal.c_str());
            y += 12.0F;
        }
        y += 4.0F;
    }
    for (const auto& [quest_id, progress] : story.quests()) {
        if (progress.done) {
            continue;
        }
        const aether::QuestDef& def = story.setup().quests.at(quest_id);
        const aether::QuestStage* stage = nullptr;
        for (const aether::QuestStage& s : def.stages) {
            if (s.id == progress.stage) {
                stage = &s;
            }
        }
        if (stage == nullptr) {
            continue;
        }
        SDL_SetRenderDrawColor(renderer, 111, 227, 255, 255);
        outlined_text(renderer, x, y, dialogue_text(assets.pack, ui.lang, def.name, def.args).c_str());
        y += 14.0F;
        SDL_SetRenderDrawColor(renderer, 235, 245, 255, 255);
        for (const std::string& wrapped :
             wrap_text(dialogue_text(assets.pack, ui.lang, stage->journal, def.args), 24)) {
            outlined_text(renderer, x, y, wrapped.c_str());
            y += 12.0F;
        }
        for (std::size_t i = 0; i < stage->objectives.size(); ++i) {
            if (stage->objectives[i].kind == aether::Objective::Kind::Talk) {
                continue;
            }
            std::snprintf(line, sizeof(line), "  %lld/%lld", static_cast<long long>(progress.progress[i]),
                          static_cast<long long>(stage->objectives[i].count));
            outlined_text(renderer, x, y, line);
            y += 12.0F;
        }
        y += 6.0F;
    }
    SDL_SetRenderScale(renderer, 1.0F, 1.0F);
}

// The first row to draw of a long list: the rows that fit on the screen, with the cursor kept near the middle.
int list_first(int total, int cursor, int max_rows) {
    return total <= max_rows ? 0 : std::clamp(cursor - max_rows / 2, 0, total - max_rows);
}

void draw_shop(SDL_Renderer* renderer, const Assets& assets, const aether::WorldSim& sim, const Ui& ui, int out_w,
               int out_h, float density) {
    if (sim.shop() == nullptr) {
        return;
    }
    constexpr float kScale = 2.0F;
    const auto entries = shop_entries(sim, ui);
    const float row = 8.0F * kScale + 8.0F;
    const float w = std::min(static_cast<float>(out_w) - 40.0F, 560.0F * density);
    const int cursor = std::clamp(ui.shop_cursor, 0, std::max(static_cast<int>(entries.size()) - 1, 0));
    const int max_rows = std::max(
        3, static_cast<int>((static_cast<float>(out_h) - 150.0F) / row));  // a long list scrolls with the cursor
    const int visible = std::min(static_cast<int>(entries.size()), max_rows);
    const int first = list_first(static_cast<int>(entries.size()), cursor, max_rows);
    const float h = 100.0F + row * static_cast<float>(std::max(visible, 1));
    const float x = (static_cast<float>(out_w) - w) / 2.0F;
    const float y = (static_cast<float>(out_h) - h) / 2.0F;
    draw_panel(renderer, x, y, w, h, 255, 215, 120, 245);
    SDL_SetRenderScale(renderer, kScale, kScale);
    SDL_SetRenderDrawColor(renderer, 255, 215, 120, 255);
    const std::string title = assets.pack.text(ui.lang, "$i18n:ui.shop") + " - " +
                              assets.pack.text(ui.lang, ui.shop_sell ? "$i18n:ui.shop_sell" : "$i18n:ui.shop_buy");
    debug_text(renderer, (x + 16.0F) / kScale, (y + 12.0F) / kScale, title.c_str());
    const std::string gold =
        assets.pack.text(ui.lang, "$i18n:ui.gold", {{"gold", static_cast<std::int64_t>(sim.story().gold())}});
    debug_text(renderer, (x + w - 16.0F) / kScale - text_columns(gold) * 8.0F, (y + 12.0F) / kScale, gold.c_str());
    float ty = y + 12.0F + row + 8.0F;
    if (entries.empty()) {
        SDL_SetRenderDrawColor(renderer, 235, 245, 255, 255);
        debug_text(renderer, (x + 16.0F) / kScale, ty / kScale,
                   assets.pack.text(ui.lang, "$i18n:ui.shop_empty").c_str());
    }
    for (std::size_t i = static_cast<std::size_t>(first); i < static_cast<std::size_t>(first + visible); ++i) {
        const std::string name =
            assets.pack.text(ui.lang, "$i18n:" + item_key(entries[i].first) + ".name", {{"count", std::int64_t{1}}});
        const std::string price = std::to_string(entries[i].second);
        if (static_cast<int>(i) == cursor) {
            SDL_SetRenderScale(renderer, 1.0F, 1.0F);
            fill_rect(renderer, x + 8.0F, ty - 3.0F, w - 16.0F, row, 40, 90, 140, 255);
            SDL_SetRenderScale(renderer, kScale, kScale);
        }
        SDL_SetRenderDrawColor(renderer, 235, 245, 255, 255);
        debug_text(renderer, (x + 16.0F) / kScale, ty / kScale,
                   ((static_cast<int>(i) == cursor ? ">" : " ") + name).c_str());
        SDL_SetRenderDrawColor(renderer, 255, 215, 120, 255);
        debug_text(renderer, (x + w - 16.0F) / kScale - text_columns(price) * 8.0F, ty / kScale, price.c_str());
        ty += row;
    }
    SDL_SetRenderDrawColor(renderer, 170, 200, 230, 255);
    debug_text(renderer, (x + 16.0F) / kScale, (y + h - 28.0F) / kScale,
               assets.pack.text(ui.lang, "$i18n:ui.shop_hint").c_str());
    SDL_SetRenderScale(renderer, 1.0F, 1.0F);
}

void draw_board(SDL_Renderer* renderer, const Assets& assets, const aether::WorldSim& sim, const Ui& ui, int out_w,
                int out_h, float density) {
    const aether::WorldSim::Board* board = sim.board();
    const aether::ChunkStore* store = sim.chunks();
    if (board == nullptr || store == nullptr) {
        return;
    }
    constexpr float kScale = 2.0F;
    const float row = 8.0F * kScale + 8.0F;
    const float w = std::min(static_cast<float>(out_w) - 40.0F, 760.0F * density);
    const float h = 110.0F + row * 3.0F * static_cast<float>(std::max<std::size_t>(board->offers.size(), 1));
    const float x = (static_cast<float>(out_w) - w) / 2.0F;
    const float y = (static_cast<float>(out_h) - h) / 2.0F;
    const aether::GuildParams& guild = store->params().guild;
    const auto rank_letter = [&guild](int index) {
        std::string letter = guild.ranks[static_cast<std::size_t>(index)].id;
        for (char& c : letter) {
            c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
        }
        return letter;
    };
    draw_panel(renderer, x, y, w, h, 111, 227, 255, 245);
    SDL_SetRenderScale(renderer, kScale, kScale);
    SDL_SetRenderDrawColor(renderer, 111, 227, 255, 255);
    const std::string title = assets.pack.text(ui.lang, "$i18n:ui.board") + " - " + board->settlement.name;
    debug_text(renderer, (x + 16.0F) / kScale, (y + 12.0F) / kScale, title.c_str());
    const std::string status = assets.pack.text(ui.lang, "$i18n:ui.rank", {{"rank", rank_letter(sim.guild_rank())}}) +
                               "  " +
                               assets.pack.text(ui.lang, "$i18n:ui.guild_points",
                                                {{"points", static_cast<std::int64_t>(sim.story().guild_points())}});
    SDL_SetRenderDrawColor(renderer, 255, 215, 120, 255);
    debug_text(renderer, (x + 16.0F) / kScale, (y + 12.0F + row) / kScale, status.c_str());
    float ty = y + 12.0F + row * 2.0F + 6.0F;
    const int cursor = std::clamp(ui.board_cursor, 0, std::max(static_cast<int>(board->offers.size()) - 1, 0));
    for (std::size_t i = 0; i < board->offers.size(); ++i) {
        const aether::Offer& offer = board->offers[i];
        const aether::QuestDef quest = aether::quest_from_offer(offer);
        const bool locked = sim.guild_rank() < offer.min_rank;
        const bool taken = sim.story().quests().count(offer.id) != 0;
        if (static_cast<int>(i) == cursor) {
            SDL_SetRenderScale(renderer, 1.0F, 1.0F);
            fill_rect(renderer, x + 8.0F, ty - 3.0F, w - 16.0F, row * 3.0F, 40, 90, 140, 255);
            SDL_SetRenderScale(renderer, kScale, kScale);
        }
        const std::string name = dialogue_text(assets.pack, ui.lang, quest.name, quest.args);
        std::string tag;
        if (taken) {
            tag = "  (" + assets.pack.text(ui.lang, "$i18n:ui.board_taken") + ")";
        } else if (locked) {
            tag = "  (" + assets.pack.text(ui.lang, "$i18n:ui.board_locked", {{"rank", rank_letter(offer.min_rank)}}) +
                  ")";
        }
        SDL_SetRenderDrawColor(renderer, locked ? 130 : 255, locked ? 140 : 255, locked ? 160 : 255, 255);
        debug_text(renderer, (x + 16.0F) / kScale, ty / kScale,
                   ((static_cast<int>(i) == cursor ? ">" : " ") + name + tag).c_str());
        SDL_SetRenderDrawColor(renderer, 170, 200, 230, 255);
        const std::string journal = dialogue_text(assets.pack, ui.lang, quest.stages.front().journal, quest.args);
        debug_text(renderer, (x + 16.0F + 8.0F * kScale) / kScale, (ty + row) / kScale, journal.substr(0, 80).c_str());
        SDL_SetRenderDrawColor(renderer, 255, 215, 120, 255);
        const std::string reward = assets.pack.text(ui.lang, "$i18n:ui.board_reward",
                                                    {{"gold", static_cast<std::int64_t>(offer.gold)},
                                                     {"xp", static_cast<std::int64_t>(offer.xp)},
                                                     {"points", static_cast<std::int64_t>(offer.points)}});
        debug_text(renderer, (x + 16.0F + 8.0F * kScale) / kScale, (ty + row * 2.0F) / kScale, reward.c_str());
        ty += row * 3.0F;
    }
    SDL_SetRenderDrawColor(renderer, 170, 200, 230, 255);
    debug_text(renderer, (x + 16.0F) / kScale, (y + h - 28.0F) / kScale,
               assets.pack.text(ui.lang, "$i18n:ui.board_hint").c_str());
    SDL_SetRenderScale(renderer, 1.0F, 1.0F);
}

// The journal (spec 07, "Journal"): the quests in progress with their text and counts, then the finished ones.
struct JournalLine {
    std::string text;
    int kind = 0;  // 0 section title, 1 quest name, 2 text, 3 finished quest
};

std::vector<JournalLine> journal_lines(const Assets& assets, const aether::WorldSim& sim, const Ui& ui,
                                       std::size_t columns) {
    std::vector<JournalLine> lines;
    const auto& quests = sim.story().quests();
    bool any_active = false;
    bool any_done = false;
    for (const auto& entry : quests) {
        (entry.second.done ? any_done : any_active) = true;
    }
    if (!any_active && !any_done) {
        lines.push_back({assets.pack.text(ui.lang, "$i18n:ui.journal_empty"), 2});
        return lines;
    }
    if (any_active) {
        lines.push_back({assets.pack.text(ui.lang, "$i18n:ui.journal_active"), 0});
        for (const auto& [quest_id, progress] : quests) {
            if (progress.done) {
                continue;
            }
            const aether::QuestDef& def = sim.story().setup().quests.at(quest_id);
            const aether::QuestStage* stage = nullptr;
            for (const aether::QuestStage& s : def.stages) {
                if (s.id == progress.stage) {
                    stage = &s;
                }
            }
            if (stage == nullptr) {
                continue;
            }
            lines.push_back({dialogue_text(assets.pack, ui.lang, def.name, def.args), 1});
            for (const std::string& wrapped :
                 wrap_text(dialogue_text(assets.pack, ui.lang, stage->journal, def.args), columns)) {
                lines.push_back({"  " + wrapped, 2});
            }
            for (std::size_t i = 0; i < stage->objectives.size(); ++i) {
                if (stage->objectives[i].kind != aether::Objective::Kind::Talk) {
                    lines.push_back(
                        {"  " + std::to_string(progress.progress[i]) + "/" + std::to_string(stage->objectives[i].count),
                         2});
                }
            }
            lines.push_back({"", 2});
        }
    }
    if (any_done) {
        lines.push_back({assets.pack.text(ui.lang, "$i18n:ui.journal_done"), 0});
        for (const auto& [quest_id, progress] : quests) {
            if (progress.done) {
                const aether::QuestDef& def = sim.story().setup().quests.at(quest_id);
                lines.push_back({dialogue_text(assets.pack, ui.lang, def.name, def.args), 3});
            }
        }
    }
    return lines;
}

void draw_journal(SDL_Renderer* renderer, const Assets& assets, const aether::WorldSim& sim, const Ui& ui, int out_w,
                  int out_h, float density) {
    if (!ui.show_journal) {
        return;
    }
    constexpr float kScale = 1.5F;
    const float row = 8.0F * kScale + 6.0F;
    const float w = std::min(static_cast<float>(out_w) - 40.0F, 640.0F * density);
    const float h = std::min(static_cast<float>(out_h) - 40.0F, 520.0F * density);
    const float x = (static_cast<float>(out_w) - w) / 2.0F;
    const float y = (static_cast<float>(out_h) - h) / 2.0F;
    const std::size_t columns = static_cast<std::size_t>(std::max((w - 32.0F) / (8.0F * kScale), 20.0F));
    const std::vector<JournalLine> lines = journal_lines(assets, sim, ui, columns);
    const int visible = std::max(static_cast<int>((h - 90.0F) / row), 1);
    const int first = std::clamp(ui.journal_scroll, 0, std::max(static_cast<int>(lines.size()) - visible, 0));
    draw_panel(renderer, x, y, w, h, 255, 215, 120, 245);
    SDL_SetRenderScale(renderer, kScale, kScale);
    SDL_SetRenderDrawColor(renderer, 255, 215, 120, 255);
    debug_text(renderer, (x + 16.0F) / kScale, (y + 14.0F) / kScale,
               assets.pack.text(ui.lang, "$i18n:ui.journal").c_str());
    float ty = y + 14.0F + row * 1.5F;
    for (int i = first; i < std::min(first + visible, static_cast<int>(lines.size())); ++i) {
        const JournalLine& line = lines[static_cast<std::size_t>(i)];
        switch (line.kind) {
            case 0:
                SDL_SetRenderDrawColor(renderer, 255, 215, 120, 255);
                break;
            case 1:
                SDL_SetRenderDrawColor(renderer, 111, 227, 255, 255);
                break;
            case 3:
                SDL_SetRenderDrawColor(renderer, 130, 140, 160, 255);
                break;
            default:
                SDL_SetRenderDrawColor(renderer, 235, 245, 255, 255);
                break;
        }
        debug_text(renderer, (x + 16.0F) / kScale, ty / kScale, line.text.c_str());
        ty += row;
    }
    SDL_SetRenderDrawColor(renderer, 170, 200, 230, 255);
    debug_text(renderer, (x + 16.0F) / kScale, (y + h - 28.0F) / kScale,
               assets.pack.text(ui.lang, "$i18n:ui.journal_hint").c_str());
    SDL_SetRenderScale(renderer, 1.0F, 1.0F);
}

void draw_travel(SDL_Renderer* renderer, const Assets& assets, const aether::WorldSim& sim, const Ui& ui, int out_w,
                 int out_h, float density) {
    const aether::WorldSim::Travel* travel = sim.travel();
    if (travel == nullptr) {
        return;
    }
    constexpr float kScale = 2.0F;
    const float row = 8.0F * kScale + 8.0F;
    const float w = std::min(static_cast<float>(out_w) - 40.0F, 640.0F * density);
    const int cursor = std::clamp(ui.travel_cursor, 0, std::max(static_cast<int>(travel->stops.size()) - 1, 0));
    const int max_rows = std::max(2, static_cast<int>((static_cast<float>(out_h) - 170.0F) /
                                                      (row * 2.0F)));  // a long list scrolls with the cursor
    const int visible = std::min(static_cast<int>(travel->stops.size()), max_rows);
    const int first = list_first(static_cast<int>(travel->stops.size()), cursor, max_rows);
    const float h = 120.0F + row * 2.0F * static_cast<float>(std::max(visible, 1));
    const float x = (static_cast<float>(out_w) - w) / 2.0F;
    const float y = (static_cast<float>(out_h) - h) / 2.0F;
    draw_panel(renderer, x, y, w, h, 111, 227, 255, 245);
    SDL_SetRenderScale(renderer, kScale, kScale);
    SDL_SetRenderDrawColor(renderer, 111, 227, 255, 255);
    debug_text(renderer, (x + 16.0F) / kScale, (y + 12.0F) / kScale,
               assets.pack.text(ui.lang, "$i18n:ui.travel").c_str());
    SDL_SetRenderDrawColor(renderer, 255, 215, 120, 255);
    debug_text(renderer, (x + 16.0F) / kScale, (y + 12.0F + row) / kScale,
               assets.pack.text(ui.lang, travel->fresh ? "$i18n:ui.stone_awake" : "$i18n:ui.stone_rest").c_str());
    float ty = y + 12.0F + row * 2.0F + 6.0F;
    for (std::size_t i = static_cast<std::size_t>(first); i < static_cast<std::size_t>(first + visible); ++i) {
        const aether::WorldSim::StoneStop& stop = travel->stops[i];
        const bool here = static_cast<int>(i) == travel->here;
        if (static_cast<int>(i) == cursor) {
            SDL_SetRenderScale(renderer, 1.0F, 1.0F);
            fill_rect(renderer, x + 8.0F, ty - 3.0F, w - 16.0F, row * 2.0F, 40, 90, 140, 255);
            SDL_SetRenderScale(renderer, kScale, kScale);
        }
        SDL_SetRenderDrawColor(renderer, here ? 130 : 255, here ? 140 : 255, here ? 160 : 255, 255);
        std::string line = (static_cast<int>(i) == cursor ? ">" : " ") + stop.place;
        if (here) {
            line += "  (" + assets.pack.text(ui.lang, "$i18n:ui.travel_here") + ")";
        }
        debug_text(renderer, (x + 16.0F) / kScale, ty / kScale, line.c_str());
        SDL_SetRenderDrawColor(renderer, 170, 200, 230, 255);
        debug_text(renderer, (x + 16.0F + 8.0F * kScale) / kScale, (ty + row) / kScale,
                   assets.pack.text(ui.lang, stop.region).c_str());
        ty += row * 2.0F;
    }
    SDL_SetRenderDrawColor(renderer, 170, 200, 230, 255);
    debug_text(renderer, (x + 16.0F) / kScale, (y + h - 28.0F) / kScale,
               assets.pack.text(ui.lang, "$i18n:ui.travel_hint").c_str());
    SDL_SetRenderScale(renderer, 1.0F, 1.0F);
}

void draw_inventory_and_notice(SDL_Renderer* renderer, const Assets& assets, const aether::WorldSim& sim, const Ui& ui,
                               int out_w, int out_h, float density) {
    constexpr float kScale = 2.0F;
    if (ui.show_inventory) {
        const float w = std::min(static_cast<float>(out_w) - 40.0F, 520.0F * density);
        const float x = (static_cast<float>(out_w) - w) / 2.0F;
        const float row = 8.0F * kScale + 8.0F;
        const auto& items = sim.inventory();
        const int bag_cursor = std::clamp(ui.bag_cursor, 0, std::max(static_cast<int>(items.size()) - 1, 0));
        const int max_rows = std::max(3, static_cast<int>((static_cast<float>(out_h) - 140.0F) / row) -
                                             2);  // a long list scrolls with the cursor
        const int visible = std::min(static_cast<int>(items.size()), max_rows);
        const int first = list_first(static_cast<int>(items.size()), bag_cursor, max_rows);
        const float h = 56.0F + row * static_cast<float>(std::max(visible, 1)) + row * 2.0F;
        const float y = (static_cast<float>(out_h) - h) / 2.0F;
        draw_panel(renderer, x, y, w, h, 111, 227, 255, 240);
        SDL_SetRenderScale(renderer, kScale, kScale);
        SDL_SetRenderDrawColor(renderer, 255, 215, 120, 255);
        debug_text(renderer, (x + 16.0F) / kScale, (y + 14.0F) / kScale,
                   assets.pack.text(ui.lang, "$i18n:ui.inventory").c_str());
        float ty = y + 14.0F + row + 6.0F;
        SDL_SetRenderDrawColor(renderer, 235, 245, 255, 255);
        if (items.empty()) {
            debug_text(renderer, (x + 16.0F) / kScale, ty / kScale,
                       assets.pack.text(ui.lang, "$i18n:ui.empty_bag").c_str());
        }
        const int cursor = std::clamp(ui.bag_cursor, 0, std::max(static_cast<int>(items.size()) - 1, 0));
        int index = 0;
        std::string selected;
        for (const auto& [item_id, quantity] : items) {
            if (index < first || index >= first + visible) {
                ++index;
                continue;
            }
            const std::string key = item_key(item_id);
            const std::string name =
                assets.pack.text(ui.lang, "$i18n:" + key + ".name", {{"count", static_cast<std::int64_t>(quantity)}});
            std::string line = name + "  x" + std::to_string(quantity);
            if (item_id == sim.equipped_weapon() || item_id == sim.equipped_armor()) {
                line += "  " + assets.pack.text(ui.lang, "$i18n:ui.worn");
            }
            if (index == cursor) {
                selected = key;
                SDL_SetRenderScale(renderer, 1.0F, 1.0F);
                fill_rect(renderer, x + 8.0F, ty - 3.0F, w - 16.0F, row, 40, 90, 140, 255);
                SDL_SetRenderScale(renderer, kScale, kScale);
                SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
                debug_text(renderer, (x + 16.0F) / kScale, ty / kScale, (">" + line).c_str());
                SDL_SetRenderDrawColor(renderer, 235, 245, 255, 255);
            } else {
                debug_text(renderer, (x + 16.0F + 8.0F * kScale) / kScale, ty / kScale, line.c_str());
            }
            ty += row;
            ++index;
        }
        if (!selected.empty()) {
            SDL_SetRenderDrawColor(renderer, 170, 200, 230, 255);
            debug_text(renderer, (x + 16.0F) / kScale, (ty + 6.0F) / kScale,
                       assets.pack.text(ui.lang, "$i18n:" + selected + ".desc").c_str());
            debug_text(renderer, (x + 16.0F) / kScale, (ty + 6.0F + row) / kScale,
                       assets.pack.text(ui.lang, "$i18n:ui.bag_use_hint").c_str());
        }
        SDL_SetRenderScale(renderer, 1.0F, 1.0F);
    }
    if (ui.message_frames > 0 && !ui.message.empty()) {
        SDL_SetRenderScale(renderer, kScale, kScale);
        SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
        debug_text(renderer, 12.0F * density / kScale, (static_cast<float>(out_h) - 40.0F * density) / kScale,
                   ui.message.c_str());
        SDL_SetRenderScale(renderer, 1.0F, 1.0F);
    }
}

void render(SDL_Renderer* renderer, aether::TextureCache& cache, const Assets& assets, const aether::WorldSim& sim,
            const Ui& ui, std::vector<FloatingText>& floating, int tile_px, float density, bool debug, double fps,
            const std::string& capture_path = {}) {
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
            const auto def = assets.tileset.tiles.find(sim.gid_at(tx, ty));
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
    sim.for_each_prop(cam.x - 2.0F, cam.y - 1.0F, cam.x + view_w + 2.0F, cam.y + view_h + 4.0F,
                      [&items](const aether::Prop& prop) { items.push_back({prop.y, 0, &prop, nullptr, nullptr}); });
    for (const aether::Enemy& enemy : sim.enemies()) {
        if (enemy.state != aether::EnemyState::Dead) {
            items.push_back({enemy.position.y, 1, nullptr, &enemy, nullptr});
        }
    }
    for (const aether::NpcDef& npc : sim.story().setup().npcs) {
        items.push_back({npc.y, 3, nullptr, nullptr, &npc});
    }
    for (const aether::NpcDef& npc : sim.story().dynamic_npcs()) {
        items.push_back({npc.y, 3, nullptr, nullptr, &npc});
    }
    items.push_back({sim.player().position.y, 2, nullptr, nullptr, nullptr});
    std::stable_sort(items.begin(), items.end(),
                     [](const DrawItem& a, const DrawItem& b) { return a.feet_y < b.feet_y; });
    for (const DrawItem& item : items) {
        if (item.kind == 2) {
            const float fx = (sim.player().position.x - cam.x) * tile;
            const float fy = (sim.player().position.y - cam.y) * tile;
            const aether::Player& player = sim.player();
            const bool blink = player.iframes > 0 && (player.iframes / 4) % 2 == 0;
            draw_character(renderer, cache, assets, player.moving, player.facing_left, player.clip_tick, blink,
                           g_art_variant, fx, fy, k, tile_px);
            draw_swing(renderer, sim, fx, fy, tile);
        } else if (item.kind == 3) {
            const float fx = (item.npc->x - cam.x) * tile;
            const float fy = (item.npc->y - cam.y) * tile;
            draw_character(renderer, cache, assets, false, sim.player().position.x < item.npc->x,
                           static_cast<int>(now_ms / 16), false, item.npc->variant, fx, fy, k, tile_px);
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
        debug_text(renderer, sx, sy, f.text.c_str());
    }

    draw_atmosphere(renderer, assets, sim, ui, out_w, out_h, density, now_ms);
    draw_hud(renderer, assets, sim, ui, density);
    draw_quest_tracker(renderer, assets, sim, ui, out_w, density);
    draw_minimap(renderer, sim, ui, density);
    draw_analyze(renderer, assets, sim, ui, out_w, density);
    if (ui.has_goal && sim.streamed() && !ui.show_map) {  // an arrow around the player, toward the goal, when it is far
        const float ddx = ui.goal_x - sim.player().position.x;
        const float ddy = ui.goal_y - sim.player().position.y;
        const float dist = std::sqrt(ddx * ddx + ddy * ddy);
        if (dist > 12.0F) {
            const float ux = ddx / dist;
            const float uy = ddy / dist;
            const float ox = (sim.player().position.x - cam.x) * tile;
            const float oy = (sim.player().position.y - cam.y) * tile - 0.6F * tile;
            const float tip_x = ox + ux * 2.7F * tile;
            const float tip_y = oy + uy * 2.7F * tile;
            const float base_x = ox + ux * 1.9F * tile;
            const float base_y = oy + uy * 1.9F * tile;
            const float barb = 0.4F * tile;
            SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
            for (int pass = 0; pass < 2; ++pass) {  // a dark edge first, then the arrow
                const float shift = pass == 0 ? 1.5F : 0.0F;
                SDL_SetRenderDrawColor(renderer, pass == 0 ? 0 : 90, pass == 0 ? 0 : 255, pass == 0 ? 0 : 120, 230);
                for (int thick = 0; thick < 3; ++thick) {
                    const float o = static_cast<float>(thick) - 1.0F + shift;
                    SDL_RenderLine(renderer, base_x + o, base_y + o, tip_x + o, tip_y + o);
                    for (const float angle : {2.6F, -2.6F}) {
                        const float bx = (ux * std::cos(angle) - uy * std::sin(angle)) * barb;
                        const float by = (ux * std::sin(angle) + uy * std::cos(angle)) * barb;
                        SDL_RenderLine(renderer, tip_x + o, tip_y + o, tip_x + bx + o, tip_y + by + o);
                    }
                }
            }
        }
    }

    if (!sim.story().dialogue_active() && sim.story().npc_in_range() == nullptr) {
        if (const auto stone = sim.stone_near()) {
            const std::string hint = assets.pack.text(ui.lang, "$i18n:ui.interact");
            SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
            debug_text(renderer, (stone->first - cam.x) * tile - static_cast<float>(hint.size()) * 4.0F,
                       (stone->second - cam.y) * tile - 2.4F * tile, hint.c_str());
        }
    }
    if (!sim.story().dialogue_active()) {
        if (const aether::NpcDef* npc = sim.story().npc_in_range()) {
            const std::string hint = assets.pack.text(ui.lang, "$i18n:ui.interact");
            const float hx = (npc->x - cam.x) * tile - static_cast<float>(hint.size()) * 4.0F;
            const float hy = (npc->y - cam.y) * tile - 2.2F * tile;
            SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
            debug_text(renderer, hx, hy, hint.c_str());
            if (!npc->name.empty()) {
                SDL_SetRenderDrawColor(renderer, 255, 215, 120, 255);
                debug_text(renderer, (npc->x - cam.x) * tile - static_cast<float>(npc->name.size()) * 4.0F, hy - 12.0F,
                           npc->name.c_str());
            }
        }
    }
    draw_dialogue(renderer, assets, sim, ui, out_w, out_h, density);
    draw_inventory_and_notice(renderer, assets, sim, ui, out_w, out_h, density);
    draw_world_map(renderer, assets, sim, ui, out_w, out_h, density);
    draw_shop(renderer, assets, sim, ui, out_w, out_h, density);
    draw_board(renderer, assets, sim, ui, out_w, out_h, density);
    draw_travel(renderer, assets, sim, ui, out_w, out_h, density);
    draw_journal(renderer, assets, sim, ui, out_w, out_h, density);

    if (debug) {
        char line[160];
        std::snprintf(line, sizeof(line), "%s  %.0f fps  pos %.2f,%.2f  tile %dpx  textures %zu",
                      aether::version_line().c_str(), fps, static_cast<double>(sim.player().position.x),
                      static_cast<double>(sim.player().position.y), tile_px, cache.size());
        SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
        debug_text(renderer, 8.0F, static_cast<float>(out_h) - 16.0F, line);
    }
    if (!capture_path.empty()) {
        if (SDL_Surface* surface = SDL_RenderReadPixels(renderer, nullptr)) {
            if (!SDL_SavePNG(surface, capture_path.c_str())) {
                SDL_Log("cannot save %s: %s", capture_path.c_str(), SDL_GetError());
            }
            SDL_DestroySurface(surface);
        }
    }
    SDL_RenderPresent(renderer);
}

// Saves what is on the renderer as a PNG (the smoke test looks at the screens this way).
void save_frame(SDL_Renderer* renderer, const std::string& path) {
    if (SDL_Surface* surface = SDL_RenderReadPixels(renderer, nullptr)) {
        if (!SDL_SavePNG(surface, path.c_str())) {
            SDL_Log("cannot save %s: %s", path.c_str(), SDL_GetError());
        }
        SDL_DestroySurface(surface);
    }
}

// The title screen (spec 12, "Slots"): the games to pick from. Returns the game (1..kSlotCount), or 0 when the player
// quits.
int run_title(SDL_Window* window, SDL_Renderer* renderer, const Assets& assets, const std::string& lang, int first_slot,
              const std::string& capture_path = {}) {
    std::vector<SlotInfo> slots;
    for (int slot = 1; slot <= kSlotCount; ++slot) {
        slots.push_back(read_slot(slot));
    }
    int cursor = std::clamp(first_slot - 1, 0, kSlotCount - 1);
    int pending_delete = -1;
    std::string notice;
    for (;;) {
        float density = SDL_GetWindowPixelDensity(window);
        if (density <= 0.0F) {
            density = 1.0F;
        }
        int out_w = 0;
        int out_h = 0;
        SDL_GetCurrentRenderOutputSize(renderer, &out_w, &out_h);
        const float panel_w = std::min(static_cast<float>(out_w) - 40.0F, 600.0F * density);
        const float panel_x = (static_cast<float>(out_w) - panel_w) / 2.0F;
        const float row_h = 56.0F * density;
        const float top = static_cast<float>(out_h) * 0.32F;
        const auto row_at = [&](float px, float py) {
            for (int i = 0; i < kSlotCount; ++i) {
                const float ry = top + static_cast<float>(i) * (row_h + 8.0F * density);
                if (px >= panel_x && px <= panel_x + panel_w && py >= ry && py <= ry + row_h) {
                    return i;
                }
            }
            return -1;
        };

        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_EVENT_QUIT) {
                return 0;
            }
            if (event.type == SDL_EVENT_KEY_DOWN) {
                const SDL_Keycode key = event.key.key;
                const int digit = static_cast<int>(key) - static_cast<int>(SDLK_1);
                if (key == SDLK_ESCAPE) {
                    if (!event.key.repeat) {  // the Esc that left a game may still be held
                        return 0;
                    }
                    continue;
                }
                if (key == SDLK_UP || key == SDLK_W) {
                    cursor = (cursor + kSlotCount - 1) % kSlotCount;
                    pending_delete = -1;
                    notice.clear();
                } else if (key == SDLK_DOWN || key == SDLK_S) {
                    cursor = (cursor + 1) % kSlotCount;
                    pending_delete = -1;
                    notice.clear();
                } else if (key == SDLK_E || key == SDLK_RETURN || key == SDLK_KP_ENTER || key == SDLK_SPACE) {
                    return cursor + 1;
                } else if (digit >= 0 && digit < kSlotCount) {
                    return digit + 1;
                } else if ((key == SDLK_D || key == SDLK_DELETE) && slots[static_cast<std::size_t>(cursor)].used) {
                    const aether::FormatArgs args{{"slot", static_cast<std::int64_t>(cursor + 1)}};
                    if (pending_delete == cursor) {
                        delete_slot(cursor + 1);
                        slots[static_cast<std::size_t>(cursor)] = SlotInfo{};
                        pending_delete = -1;
                        notice = assets.pack.text(lang, "$i18n:ui.slot_deleted", args);
                    } else {
                        pending_delete = cursor;
                        notice = assets.pack.text(lang, "$i18n:ui.slot_delete", args);
                    }
                }
            } else if (event.type == SDL_EVENT_MOUSE_MOTION) {
                SDL_ConvertEventToRenderCoordinates(renderer, &event);
                const int hovered = row_at(event.motion.x, event.motion.y);
                if (hovered >= 0 && hovered != cursor) {
                    cursor = hovered;
                    pending_delete = -1;
                    notice.clear();
                }
            } else if (event.type == SDL_EVENT_MOUSE_BUTTON_DOWN && event.button.button == SDL_BUTTON_LEFT) {
                SDL_ConvertEventToRenderCoordinates(renderer, &event);
                const int clicked = row_at(event.button.x, event.button.y);
                if (clicked >= 0) {
                    return clicked + 1;
                }
            }
        }

        const auto draw_text = [&](float scale, float px, float py, const std::string& line, Uint8 r, Uint8 g,
                                   Uint8 b) {
            SDL_SetRenderScale(renderer, scale, scale);
            SDL_SetRenderDrawColor(renderer, r, g, b, 255);
            debug_text(renderer, px / scale, py / scale, line.c_str());
            SDL_SetRenderScale(renderer, 1.0F, 1.0F);
        };
        SDL_SetRenderDrawColor(renderer, 11, 31, 58, 255);
        SDL_RenderClear(renderer);
        const std::string game_title = assets.pack.text(lang, "$i18n:game.title");
        const float title_scale = 3.0F * density;
        draw_text(title_scale, (static_cast<float>(out_w) - text_columns(game_title) * 8.0F * title_scale) / 2.0F,
                  static_cast<float>(out_h) * 0.12F, game_title, 255, 215, 120);
        const std::string choose = assets.pack.text(lang, "$i18n:ui.title_choose");
        const float choose_scale = 1.5F * density;
        draw_text(choose_scale, (static_cast<float>(out_w) - text_columns(choose) * 8.0F * choose_scale) / 2.0F,
                  static_cast<float>(out_h) * 0.12F + 40.0F * density, choose, 170, 200, 230);
        for (int i = 0; i < kSlotCount; ++i) {
            const SlotInfo& info = slots[static_cast<std::size_t>(i)];
            const float ry = top + static_cast<float>(i) * (row_h + 8.0F * density);
            const bool selected = i == cursor;
            const Uint8 fill_r = selected ? Uint8{30} : Uint8{20};
            const Uint8 fill_g = selected ? Uint8{70} : Uint8{50};
            const Uint8 fill_b = selected ? Uint8{120} : Uint8{90};
            fill_rect(renderer, panel_x, ry, panel_w, row_h, fill_r, fill_g, fill_b, 255);
            if (selected) {
                fill_rect(renderer, panel_x, ry, panel_w, 3.0F, 255, 215, 120, 255);
            }
            const aether::FormatArgs args{{"slot", static_cast<std::int64_t>(i + 1)},
                                          {"level", static_cast<std::int64_t>(info.level)},
                                          {"gold", info.gold}};
            const std::string line =
                assets.pack.text(lang, info.used ? "$i18n:ui.slot_used" : "$i18n:ui.slot_empty", args);
            const Uint8 text_r = info.used ? Uint8{235} : Uint8{150};
            const Uint8 text_g = info.used ? Uint8{245} : Uint8{170};
            const Uint8 text_b = info.used ? Uint8{255} : Uint8{200};
            draw_text(choose_scale, panel_x + 16.0F * density, ry + (row_h - 8.0F * choose_scale) / 2.0F, line, text_r,
                      text_g, text_b);
        }
        const float hint_scale = 1.25F * density;
        if (!notice.empty()) {
            draw_text(hint_scale, panel_x, top + 3.0F * (row_h + 8.0F * density) + 12.0F * density, notice, 255, 215,
                      120);
        }
        draw_text(hint_scale, panel_x, static_cast<float>(out_h) - 36.0F * density,
                  assets.pack.text(lang, "$i18n:ui.title_hint"), 170, 200, 230);
        if (!capture_path.empty()) {
            save_frame(renderer, capture_path);
            return 0;
        }
        SDL_RenderPresent(renderer);
    }
}

// Choosing who to be (spec 18), for a new game: the protagonists that are available, with their story and gift. Returns
// the ID of the one chosen, or "" when the player goes back to the title screen (Esc) or closes the window.
std::string choose_protagonist(SDL_Window* window, SDL_Renderer* renderer, const Assets& assets,
                               const std::string& lang, const std::string& capture_path = {}, int capture_cursor = 0) {
    std::vector<std::string> ids;
    for (const auto& entry : assets.pack.document_paths) {
        const std::string& id = entry.first;
        if (id.rfind("base:protagonist/", 0) != 0) {
            continue;
        }
        std::string error;
        const auto text = assets.pack.read_document(id);
        const auto def = text ? aether::parse_protagonist(*text, error) : std::nullopt;
        if (def && def->initially_available) {
            ids.push_back(id);
        }
    }
    std::stable_sort(ids.begin(), ids.end(), [](const std::string& a, const std::string& b) {
        const bool ren_a = a == kProtagonistId;
        const bool ren_b = b == kProtagonistId;
        return ren_a != ren_b ? ren_a : a < b;  // Ren first, the others in the order of their IDs
    });
    if (ids.empty()) {
        return kProtagonistId;
    }
    const auto key_of = [](const std::string& id, const char* what) {
        return std::string("$i18n:protagonist.") + id.substr(id.rfind('/') + 1) + "." + what;
    };
    aether::TextureCache preview_cache(renderer, assets.pack);  // for the preview of the character
    int cursor = std::clamp(capture_cursor, 0, static_cast<int>(ids.size()) - 1);
    for (;;) {
        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_EVENT_QUIT) {
                return "";
            }
            if (event.type == SDL_EVENT_KEY_DOWN && !event.key.repeat) {
                const SDL_Keycode key = event.key.key;
                const int digit = static_cast<int>(key) - static_cast<int>(SDLK_1);
                if (key == SDLK_ESCAPE) {
                    return "";
                }
                if (key == SDLK_UP || key == SDLK_W) {
                    cursor = (cursor + static_cast<int>(ids.size()) - 1) % static_cast<int>(ids.size());
                } else if (key == SDLK_DOWN || key == SDLK_S) {
                    cursor = (cursor + 1) % static_cast<int>(ids.size());
                } else if (key == SDLK_E || key == SDLK_RETURN || key == SDLK_KP_ENTER || key == SDLK_SPACE) {
                    return ids[static_cast<std::size_t>(cursor)];
                } else if (digit >= 0 && digit < static_cast<int>(ids.size())) {
                    return ids[static_cast<std::size_t>(digit)];
                }
            } else if (event.type == SDL_EVENT_MOUSE_BUTTON_DOWN && event.button.button == SDL_BUTTON_LEFT) {
                SDL_ConvertEventToRenderCoordinates(renderer, &event);
                float density = SDL_GetWindowPixelDensity(window);
                density = density <= 0.0F ? 1.0F : density;
                const float row_h = 40.0F * density;
                for (std::size_t i = 0; i < ids.size(); ++i) {
                    const float ry = 120.0F * density + static_cast<float>(i) * (row_h + 6.0F * density);
                    if (event.button.x >= 30.0F * density && event.button.x <= 330.0F * density &&
                        event.button.y >= ry && event.button.y <= ry + row_h) {
                        return ids[i];
                    }
                }
            }
        }
        float density = SDL_GetWindowPixelDensity(window);
        density = density <= 0.0F ? 1.0F : density;
        int out_w = 0;
        int out_h = 0;
        SDL_GetCurrentRenderOutputSize(renderer, &out_w, &out_h);
        const auto draw_text = [&](float scale, float px, float py, const std::string& line, Uint8 r, Uint8 g,
                                   Uint8 b) {
            SDL_SetRenderScale(renderer, scale, scale);
            SDL_SetRenderDrawColor(renderer, r, g, b, 255);
            debug_text(renderer, px / scale, py / scale, line.c_str());
            SDL_SetRenderScale(renderer, 1.0F, 1.0F);
        };
        SDL_SetRenderDrawColor(renderer, 11, 31, 58, 255);
        SDL_RenderClear(renderer);
        draw_text(2.0F * density, 30.0F * density, 30.0F * density,
                  assets.pack.text(lang, "$i18n:ui.protagonist_choose"), 255, 215, 120);
        const float row_h = 40.0F * density;
        for (std::size_t i = 0; i < ids.size(); ++i) {
            const float ry = 120.0F * density + static_cast<float>(i) * (row_h + 6.0F * density);
            const bool selected = static_cast<int>(i) == cursor;
            fill_rect(renderer, 30.0F * density, ry, 300.0F * density, row_h, selected ? 30 : 20, selected ? 70 : 50,
                      selected ? 120 : 90, 255);
            if (selected) {
                fill_rect(renderer, 30.0F * density, ry, 300.0F * density, 3.0F, 255, 215, 120, 255);
            }
            draw_text(1.5F * density, 42.0F * density, ry + (row_h - 12.0F * density) / 2.0F,
                      std::to_string(i + 1) + ". " + assets.pack.text(lang, key_of(ids[i], "name")),
                      selected ? 255 : 200, selected ? 255 : 215, selected ? 255 : 230);
        }
        const std::string& id = ids[static_cast<std::size_t>(cursor)];
        std::string stats_line;
        std::string stats_line2;
        {  // the character, as it will look, under the list
            std::string variant;
            std::string parse_error;
            if (const auto document = assets.pack.read_document(id)) {
                if (const auto def = aether::parse_protagonist(*document, parse_error)) {
                    variant = def->art_variant;
                    const aether::Primary& p = def->base_stats;
                    const aether::DerivedStats stats = aether::derived_stats(1, p, aether::Equipment{});
                    stats_line = "STR " + std::to_string(p.str) + "  VIT " + std::to_string(p.vit) + "  DEX " +
                                 std::to_string(p.dex) + "  AGI " + std::to_string(p.agi) + "  INT " +
                                 std::to_string(p.int_) + "  WIS " + std::to_string(p.wis) + "  LUK " +
                                 std::to_string(p.luk);
                    stats_line2 = assets.pack.text(lang, "$i18n:ui.hp") + " " + std::to_string(stats.max_hp) + "   " +
                                  assets.pack.text(lang, "$i18n:ui.mp") + " " + std::to_string(stats.max_mp) + "   " +
                                  assets.pack.text(lang, "$i18n:ui.mp_regen") + " " +
                                  std::to_string(stats.mp_regen_x100 / 100) + "." +
                                  std::to_string(stats.mp_regen_x100 % 100 / 10);
                }
            }
            const int preview_px = static_cast<int>(116.0F * density);
            draw_character(renderer, preview_cache, assets, false, false, static_cast<int>(SDL_GetTicks() / 16), false,
                           variant, static_cast<float>(out_w) - 140.0F * density, 640.0F * density,
                           static_cast<float>(preview_px) / 32.0F, preview_px);
        }
        const float text_x = 360.0F * density;
        const float text_w = static_cast<float>(out_w) - text_x - 30.0F * density;
        const float scale = 1.25F * density;
        const std::size_t columns = std::max<std::size_t>(20, static_cast<std::size_t>(text_w / (8.0F * scale)));
        float ty = 120.0F * density;
        draw_text(1.75F * density, text_x, ty, assets.pack.text(lang, key_of(id, "name")), 255, 255, 255);
        ty += 24.0F * density;
        draw_text(scale, text_x, ty, assets.pack.text(lang, key_of(id, "tagline")), 170, 200, 230);
        ty += 24.0F * density;
        draw_text(scale, text_x, ty, assets.pack.text(lang, "$i18n:ui.protagonist_gift"), 255, 215, 120);
        ty += 14.0F * density;
        for (const std::string& line : wrap_text(assets.pack.text(lang, key_of(id, "gift")), columns)) {
            draw_text(scale, text_x, ty, line, 235, 245, 255);
            ty += 14.0F * density;
        }
        ty += 12.0F * density;
        draw_text(scale, text_x, ty, assets.pack.text(lang, "$i18n:ui.protagonist_story"), 255, 215, 120);
        ty += 14.0F * density;
        for (const std::string& line : wrap_text(assets.pack.text(lang, key_of(id, "story")), columns)) {
            draw_text(scale, text_x, ty, line, 235, 245, 255);
            ty += 14.0F * density;
        }
        ty += 16.0F * density;
        draw_text(scale, text_x, ty, stats_line, 150, 200, 255);
        ty += 14.0F * density;
        draw_text(scale, text_x, ty, stats_line2, 150, 200, 255);
        draw_text(1.25F * density, 30.0F * density, static_cast<float>(out_h) - 36.0F * density,
                  assets.pack.text(lang, "$i18n:ui.protagonist_hint"), 170, 200, 230);
        if (!capture_path.empty()) {
            save_frame(renderer, capture_path);
            return ids[static_cast<std::size_t>(cursor)];
        }
        SDL_RenderPresent(renderer);
        SDL_Delay(16);
    }
}

}  // namespace

int main(int argc, char** argv) {
    bool smoke_test = false;
    int forced_slot = 0;     // developer option: --slot=N skips the title screen
    std::string map_choice;  // "demo" or "world"; the default depends on the mode
    std::string
        forced_protagonist;  // developer option: --protagonist=sakura plays that one (a new game, the smoke test)
    std::optional<std::uint64_t> forced_seed;
    std::optional<std::pair<float, float>> start_at;  // developer option: --start=X,Y in tiles
    fs::path screenshot_dir;
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--version") == 0) {
            std::printf("%s\n", aether::version_line().c_str());
            return 0;
        }
        if (std::strcmp(argv[i], "--smoke-test") == 0) {
            smoke_test = true;
        }
        if (std::strncmp(argv[i], "--screenshot-dir=", 17) == 0) {
            screenshot_dir = argv[i] + 17;
        }
        if (std::strncmp(argv[i], "--map=", 6) == 0) {
            map_choice = argv[i] + 6;
        }
        if (std::strncmp(argv[i], "--start=", 8) == 0) {
            char* end = nullptr;
            const float sx = std::strtof(argv[i] + 8, &end);
            if (end != nullptr && *end == ',') {
                start_at = std::make_pair(sx, std::strtof(end + 1, nullptr));
            }
        }
        if (std::strncmp(argv[i], "--seed=", 7) == 0) {
            forced_seed = std::strtoull(argv[i] + 7, nullptr, 0);
        }
        if (std::strncmp(argv[i], "--protagonist=", 14) == 0) {
            forced_protagonist = argv[i] + 14;
        }
        if (std::strncmp(argv[i], "--slot=", 7) == 0) {
            forced_slot = std::atoi(argv[i] + 7);
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
    if (map_choice.empty()) {
        map_choice = smoke_test ? "demo" : "world";
    }
    g_map_name = map_choice;
    if (!smoke_test) {
        g_sound.open(assets.pack, {"swing", "hit", "crit", "hurt", "dodge", "level_up", "pickup", "coin", "open",
                                   "close", "confirm", "power", "death", "enemy_die"});
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

    if (smoke_test && !screenshot_dir.empty()) {  // the screens before the game, saved for a look
        std::error_code folder_error;
        fs::create_directories(screenshot_dir, folder_error);
        const std::string shots_lang = saved_language().value_or(detect_language());
        run_title(window, renderer, assets, shots_lang, 1, (screenshot_dir / "title.png").string());
        for (int i = 0; i < 8; ++i) {
            choose_protagonist(window, renderer, assets, shots_lang,
                               (screenshot_dir / ("chooser_" + std::to_string(i) + ".png")).string(), i);
        }
    }

    // One game after another: Esc in a game comes back to the title screen, where another slot can be chosen.
    int exit_code = 0;
    int last_slot = 0;
    for (;;) {
        bool back_to_title = false;
        // The game (spec 12, "Slots"): chosen on the title screen; the smoke test has a folder of its own.
        if (smoke_test) {
            g_slot_dir = save_dir() / "smoke";
            std::error_code folder_error;
            fs::create_directories(g_slot_dir, folder_error);
        } else {
            migrate_legacy_saves();
            const int slot =
                forced_slot >= 1 && forced_slot <= kSlotCount
                    ? forced_slot
                    : run_title(window, renderer, assets, saved_language().value_or(detect_language()), last_slot);
            if (slot == 0) {
                SDL_DestroyRenderer(renderer);
                SDL_DestroyWindow(window);
                SDL_Quit();
                return 0;
            }
            last_slot = slot;
            g_slot_dir = slot_dir(slot);
        }

        // Who is played: forced, else the one kept in the folder of the slot, else (a new game) the one the player
        // chooses (spec 18).
        g_protagonist_id = kProtagonistId;
        if (!forced_protagonist.empty()) {
            g_protagonist_id = "base:protagonist/" + forced_protagonist;
        } else if (!smoke_test) {
            const fs::path kept = g_slot_dir / "protagonist.txt";
            if (const auto text = read_text_file(kept)) {
                std::string id = *text;
                while (!id.empty() && (id.back() == '\n' || id.back() == '\r' || id.back() == ' ')) {
                    id.pop_back();
                }
                if (!id.empty() && assets.pack.document_paths.count(id) != 0) {
                    g_protagonist_id = id;
                }
            } else if (!fs::exists(g_slot_dir / "auto.json")) {  // a new game: choose
                const std::string chosen =
                    choose_protagonist(window, renderer, assets, saved_language().value_or(detect_language()));
                if (chosen.empty()) {
                    if (forced_slot != 0) {
                        break;  // no title screen to go back to
                    }
                    continue;  // back to the title screen
                }
                g_protagonist_id = chosen;
                std::error_code folder_error;
                fs::create_directories(g_slot_dir, folder_error);
                std::ofstream out(kept, std::ios::trunc);
                out << g_protagonist_id << "\n";
            }
        }
        g_art_variant.clear();
        g_has_analyze = true;
        {
            std::string protagonist_error;
            if (const auto document = assets.pack.read_document(g_protagonist_id)) {
                if (const auto def = aether::parse_protagonist(*document, protagonist_error)) {
                    g_art_variant = def->art_variant;
                    g_has_analyze = std::find(def->starting_skills.begin(), def->starting_skills.end(),
                                              "base:skill/ren/analyze") != def->starting_skills.end();
                }
            }
        }

        // The seed: forced, else the one of the last session on this map (so the same world comes back), else a new
        // one.
        std::uint64_t seed = smoke_test ? 1234U : SDL_GetTicksNS();
        if (forced_seed) {
            seed = *forced_seed;
        } else if (!smoke_test) {
            if (const auto text = read_text_file(g_slot_dir / "auto.json")) {
                if (const auto peek = aether::save_peek(*text); peek && peek->map == g_map_name) {
                    seed = peek->seed;
                }
            }
        }
        std::optional<aether::StreamConfig> stream;
        if (g_map_name == "world") {
            std::string world_error;
            const auto params = aether::load_world_params(assets.pack, kWorldId, world_error);
            if (!params) {
                SDL_Log("cannot read the world parameters: %s", world_error.c_str());
                SDL_Quit();
                return 1;
            }
            assets.map = aether::make_stream_map(*params);
            stream = aether::StreamConfig{*params, seed};
        }
        std::string combat_error;
        auto combat = aether::load_combat_setup(assets.pack, assets.map, g_protagonist_id, seed, combat_error);
        if (combat && stream) {
            for (const std::string& enemy : aether::world_enemy_ids(stream->params)) {
                if (combat && combat->stream_enemies.count(enemy) == 0) {
                    if (auto def = aether::load_enemy_def(assets.pack, enemy, combat_error)) {
                        def->hp = std::max<std::int64_t>(
                            1, def->hp * stream->params.enemy_hp_pct / 100);  // the difficulty of the world (spec 04)
                        def->atk = def->atk * stream->params.enemy_atk_pct / 100;
                        combat->stream_enemies.emplace(enemy, std::move(*def));
                    } else {
                        combat.reset();
                    }
                }
            }
        }
        if (!combat) {
            SDL_Log("cannot build the combat setup: %s", combat_error.c_str());
            SDL_Quit();
            return 1;
        }

        {
            aether::TextureCache cache(renderer, assets.pack);
            aether::WorldSim sim(assets.map, assets.tileset, 0.0F, std::move(*combat), stream);
            if (start_at && g_map_name == "world") {
                sim.teleport(start_at->first, start_at->second);
            }
            const float spawn_x = sim.player().position.x;
            const aether::SaveState initial_state = sim.capture();
            double since_autosave = 0.0;
            InputDevices devices;
            devices.open_first_gamepad();
            std::vector<FloatingText> floating;
            Ui ui;
            ui.lang = saved_language().value_or(detect_language());
            if (!smoke_test) {
                load_goal(ui);  // the goal marked in this game
            }

            if (!smoke_test) {  // continue the last session, if there is one
                std::string ignored;
                const auto previous = read_text_file(g_slot_dir / "auto.json");
                const auto peek = previous ? aether::save_peek(*previous) : std::nullopt;
                if (peek && peek->map == g_map_name && peek->seed == seed &&
                    load_game(sim, g_slot_dir / "auto.json", ignored)) {
                    notify(ui, assets.pack.text(ui.lang, "$i18n:ui.loaded"));
                }
            }

            bool running = true;
            bool debug = false;
            int frames = 0;
            bool captured_choice = false;
            bool smoke_save_ok = false;
            int talk_step = 0;  // smoke test: scripted conversation with the guild clerk
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
                    if (event.type == SDL_EVENT_KEY_DOWN && event.key.key == SDLK_ESCAPE &&
                        (ui.show_map || ui.show_inventory || ui.show_journal || sim.shop() != nullptr ||
                         sim.board() != nullptr || sim.travel() != nullptr)) {
                        ui.show_map = false;  // Esc closes the open panel first
                        ui.show_inventory = false;
                        ui.show_journal = false;
                        sim.close_shop();
                        sim.close_board();
                        sim.close_travel();
                    } else if (event.type == SDL_EVENT_QUIT) {
                        running = false;
                    } else if (event.type == SDL_EVENT_KEY_DOWN && event.key.key == SDLK_ESCAPE) {
                        running = false;
                        back_to_title =
                            !smoke_test &&
                            forced_slot == 0;  // Esc leaves the game for the title screen (spec 12, "Slots")
                    } else if (event.type == SDL_EVENT_KEY_DOWN && event.key.key == SDLK_F3) {
                        debug = !debug;
                    } else if (event.type == SDL_EVENT_KEY_DOWN && event.key.key == SDLK_F8 && !smoke_test) {
                        g_sound.set_muted(!g_sound.muted());
                        notify(ui,
                               assets.pack.text(ui.lang, g_sound.muted() ? "$i18n:ui.sound_off" : "$i18n:ui.sound_on"));
                    } else if (event.type == SDL_EVENT_KEY_DOWN && event.key.key == SDLK_Z && !smoke_test &&
                               g_has_analyze && !ui.show_map && !sim.story().dialogue_active()) {
                        ui.analyze_frames = ui.analyze_frames > 0 ? 0 : 360;  // Analyze: six seconds, or again to hide
                    } else if (event.type == SDL_EVENT_KEY_DOWN && event.key.key == SDLK_N && !smoke_test &&
                               !ui.show_map) {
                        ui.show_minimap = !ui.show_minimap;
                    } else if (event.type == SDL_EVENT_KEY_DOWN && !smoke_test &&
                               (event.key.key == SDLK_F5 || event.key.key == SDLK_F9 || event.key.key == SDLK_F7 ||
                                event.key.key == SDLK_I || event.key.key == SDLK_M || event.key.key == SDLK_Q ||
                                event.key.key == SDLK_F2)) {
                        if (event.key.key == SDLK_I) {
                            ui.show_inventory = !ui.show_inventory;
                            ui.show_map = false;
                            ui.show_journal = false;
                        } else if (event.key.key == SDLK_M) {
                            ui.show_map = !ui.show_map && sim.streamed();
                            ui.map_level = -1;  // framed on what was explored, when it is drawn
                            ui.map_pick = -1;
                            ui.show_inventory = false;
                            ui.show_journal = false;
                        } else if (event.key.key == SDLK_Q) {
                            ui.show_journal = !ui.show_journal && sim.shop() == nullptr && sim.board() == nullptr;
                            ui.journal_scroll = 0;
                            ui.show_inventory = false;
                            ui.show_map = false;
                        } else if (event.key.key == SDLK_F2) {
                            ui.lang = ui.lang == "it" ? "en" : "it";
                            save_language(ui.lang);
                            notify(ui, assets.pack.text(ui.lang, "$i18n:ui.language_set"));
                        } else if (event.key.key == SDLK_F5) {
                            notify(ui, save_game(sim, g_slot_dir / "quick.json")
                                           ? assets.pack.text(ui.lang, "$i18n:ui.saved")
                                           : "save failed");
                        } else if (event.key.key == SDLK_F9) {
                            std::string load_error;
                            notify(ui, load_game(sim, g_slot_dir / "quick.json", load_error)
                                           ? assets.pack.text(ui.lang, "$i18n:ui.loaded")
                                           : assets.pack.text(ui.lang, "$i18n:ui.load_failed"));
                        } else {
                            std::string ignored;
                            sim.restore(initial_state, ignored);
                            notify(ui, assets.pack.text(ui.lang, "$i18n:ui.new_game"));
                        }
                    } else if (event.type == SDL_EVENT_KEY_DOWN && !smoke_test) {
                        if (sim.travel() != nullptr) {
                            handle_travel_key(sim, assets, ui, event.key.key);
                        } else if (sim.board() != nullptr) {
                            handle_board_key(sim, assets, ui, event.key.key);
                        } else if (sim.shop() != nullptr) {
                            handle_shop_key(sim, assets, ui, event.key.key);
                        } else if (ui.show_map) {
                            handle_map_key(sim, assets, ui, event.key.key);
                        } else if (ui.show_journal) {
                            if (event.key.key == SDLK_UP || event.key.key == SDLK_W) {
                                ui.journal_scroll = std::max(ui.journal_scroll - 1, 0);
                            } else if (event.key.key == SDLK_DOWN || event.key.key == SDLK_S) {
                                ++ui.journal_scroll;  // clamped when drawn
                            }
                        } else if (ui.show_inventory) {
                            if (event.key.key == SDLK_UP || event.key.key == SDLK_W) {
                                bag_move(sim, ui, -1);
                            } else if (event.key.key == SDLK_DOWN || event.key.key == SDLK_S) {
                                bag_move(sim, ui, 1);
                            } else if (event.key.key == SDLK_E || event.key.key == SDLK_RETURN ||
                                       event.key.key == SDLK_SPACE) {
                                bag_use(sim, assets, ui);
                            }
                        } else {
                            handle_dialogue_key(sim, ui, event.key.key);
                        }
                    } else if (event.type == SDL_EVENT_MOUSE_WHEEL && ui.show_map && !smoke_test) {
                        map_zoom(ui, event.wheel.y > 0 ? 1 : (event.wheel.y < 0 ? -1 : 0));
                    } else if (event.type == SDL_EVENT_MOUSE_MOTION && ui.show_map && !smoke_test &&
                               (event.motion.state & SDL_BUTTON_LMASK) != 0) {
                        const float pixels = std::max(SDL_GetWindowPixelDensity(window), 1.0F) / ui.map_cell_px;
                        map_pan(sim, ui, -event.motion.xrel * pixels, -event.motion.yrel * pixels);  // drag the map
                    } else if (event.type == SDL_EVENT_MOUSE_BUTTON_DOWN && ui.show_map && !smoke_test &&
                               event.button.button == SDL_BUTTON_RIGHT) {
                        const float density_now = std::max(SDL_GetWindowPixelDensity(window), 1.0F);
                        const float cell_x =
                            ui.map_cx +
                            (event.button.x * density_now - (ui.map_view_x + ui.map_view_side / 2.0F)) / ui.map_cell_px;
                        const float cell_y =
                            ui.map_cy +
                            (event.button.y * density_now - (ui.map_view_y + ui.map_view_side / 2.0F)) / ui.map_cell_px;
                        set_goal(sim, assets, ui, cell_x, cell_y);
                    } else if (event.type == SDL_EVENT_MOUSE_BUTTON_DOWN && !smoke_test &&
                               sim.story().dialogue_active()) {
                        activate_dialogue(sim, ui);
                    } else if (event.type == SDL_EVENT_GAMEPAD_BUTTON_DOWN && !smoke_test) {
                        if (sim.travel() != nullptr) {
                            if (event.gbutton.button == SDL_GAMEPAD_BUTTON_DPAD_UP) {
                                travel_move(sim, ui, -1);
                            } else if (event.gbutton.button == SDL_GAMEPAD_BUTTON_DPAD_DOWN) {
                                travel_move(sim, ui, 1);
                            } else if (event.gbutton.button == SDL_GAMEPAD_BUTTON_WEST ||
                                       event.gbutton.button == SDL_GAMEPAD_BUTTON_SOUTH) {
                                travel_go(sim, assets, ui);
                            } else if (event.gbutton.button == SDL_GAMEPAD_BUTTON_EAST) {
                                sim.close_travel();
                            }
                        } else if (sim.board() != nullptr) {
                            if (event.gbutton.button == SDL_GAMEPAD_BUTTON_DPAD_UP) {
                                board_move(sim, ui, -1);
                            } else if (event.gbutton.button == SDL_GAMEPAD_BUTTON_DPAD_DOWN) {
                                board_move(sim, ui, 1);
                            } else if (event.gbutton.button == SDL_GAMEPAD_BUTTON_WEST ||
                                       event.gbutton.button == SDL_GAMEPAD_BUTTON_SOUTH) {
                                board_accept(sim, assets, ui);
                            } else if (event.gbutton.button == SDL_GAMEPAD_BUTTON_EAST) {
                                sim.close_board();
                            }
                        } else if (sim.shop() != nullptr) {
                            if (event.gbutton.button == SDL_GAMEPAD_BUTTON_DPAD_UP) {
                                shop_move(sim, ui, -1);
                            } else if (event.gbutton.button == SDL_GAMEPAD_BUTTON_DPAD_DOWN) {
                                shop_move(sim, ui, 1);
                            } else if (event.gbutton.button == SDL_GAMEPAD_BUTTON_NORTH) {
                                ui.shop_sell = !ui.shop_sell;
                                ui.shop_cursor = 0;
                            } else if (event.gbutton.button == SDL_GAMEPAD_BUTTON_WEST ||
                                       event.gbutton.button == SDL_GAMEPAD_BUTTON_SOUTH) {
                                shop_confirm(sim, assets, ui);
                            } else if (event.gbutton.button == SDL_GAMEPAD_BUTTON_EAST) {
                                sim.close_shop();
                            }
                        } else if (ui.show_inventory) {
                            if (event.gbutton.button == SDL_GAMEPAD_BUTTON_DPAD_UP) {
                                bag_move(sim, ui, -1);
                            } else if (event.gbutton.button == SDL_GAMEPAD_BUTTON_DPAD_DOWN) {
                                bag_move(sim, ui, 1);
                            } else if (event.gbutton.button == SDL_GAMEPAD_BUTTON_WEST ||
                                       event.gbutton.button == SDL_GAMEPAD_BUTTON_SOUTH) {
                                bag_use(sim, assets, ui);
                            } else if (event.gbutton.button == SDL_GAMEPAD_BUTTON_EAST) {
                                ui.show_inventory = false;
                            }
                        } else {
                            handle_dialogue_button(sim, ui, event.gbutton.button);
                        }
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
                    // Talk to the guild clerk and accept her quest while passing by (real dialogue data).
                    if (talk_step == 0 && g_map_name == "demo") {
                        if (sim.story().npc_in_range() != nullptr) {
                            sim.story().interact();
                            talk_step = 1;
                        }
                    } else if (talk_step == 1 && g_map_name == "demo") {
                        sim.story().advance();
                        talk_step = 2;
                    } else if (talk_step == 2 && g_map_name == "demo") {
                        sim.story().choose(0);
                        talk_step = 3;
                    } else if (talk_step == 3 && g_map_name == "demo") {
                        sim.story().advance();
                        talk_step = 4;
                    }
                    // At frame 60 write a save file, load it back into the running world and keep playing.
                    if (frames == 60) {
                        const fs::path file = fs::temp_directory_path() / "aethermoor_smoke_save.json";
                        std::string load_error;
                        smoke_save_ok = save_game(sim, file) && load_game(sim, file, load_error);
                        std::error_code ec;
                        fs::remove(file, ec);
                        if (!smoke_save_ok) {
                            SDL_Log("smoke: save/load failed: %s", load_error.c_str());
                        }
                    }
                    if (frames == 30) {
                        ui.analyze_frames = 12;  // frames 30 to 41 show the Analyze panel
                    }
                    if (frames == 80) {
                        ui.show_inventory = true;  // frames 80 to 83 show the bag
                    }
                    if (frames == 84) {
                        ui.show_inventory = false;
                        ui.show_map = sim.streamed();  // the last frames show the world map
                    }
                    if (frames == kSmokeTestFrames - 1) {
                        ui.map_level = 0;  // the very last frame shows the whole world
                        ui.map_cx = ui.map_cy = 64.0F;
                    }
                    sim.tick(input.x, input.y, input.attack, input.dodge, input.strike);
                } else if (ui.show_inventory || ui.show_map || ui.show_journal || sim.shop() != nullptr ||
                           sim.board() != nullptr || sim.travel() != nullptr) {
                    accumulator = 0.0;  // the bag, the map, the journal, the shop and the board pause the game
                } else {
                    accumulator += frame_seconds;
                    int ticks = 0;
                    while (accumulator >= static_cast<double>(aether::kTickDt) && ticks < kMaxTicksPerFrame) {
                        sim.tick(input.x, input.y, input.attack, input.dodge, input.strike);
                        accumulator -= static_cast<double>(aether::kTickDt);
                        ++ticks;
                    }
                    if (ticks == kMaxTicksPerFrame) {
                        accumulator = 0.0;  // drop the backlog instead of spiralling
                    }
                }

                if (sim.chunks() != nullptr) {  // entering a region: its name, for a moment
                    const aether::WorldParams& world_params = sim.chunks()->params();
                    const int region =
                        aether::region_at(world_params, static_cast<int>(std::floor(sim.player().position.x)),
                                          static_cast<int>(std::floor(sim.player().position.y)));
                    if (ui.last_region >= 0 && region != ui.last_region && !smoke_test) {
                        notify(ui, assets.pack.text(
                                       ui.lang, "$i18n:ui.region_enter",
                                       {{"region",
                                         assets.pack.text(
                                             ui.lang, world_params.regions[static_cast<std::size_t>(region)].name)}}));
                    }
                    ui.last_region = region;
                }
                {
                    const aether::DialogueView spoken = sim.story().dialogue_view();
                    if (spoken.active && !spoken.is_choice) {
                        ui.last_speaker = spoken.speaker;
                        ui.last_text = spoken.text;
                        ui.last_args = spoken.args;
                    } else if (!spoken.active) {
                        ui.last_text.clear();
                    }
                }
                for (const aether::DamageEvent& e : sim.take_events()) {
                    floating.push_back({e.position.x, e.position.y, 0, std::to_string(e.amount) + (e.weak ? "!" : ""),
                                        e.on_player, e.crit});
                    g_sound.play(e.on_player ? "hurt" : (e.crit ? "crit" : "hit"));
                }
                {  // the sounds that follow from what changed: an attack, a roll, a level, something in the bag...
                    static SoundWatch watch;
                    const aether::Player& hero = sim.player();
                    std::int64_t items = 0;
                    for (const auto& entry : sim.inventory()) {
                        items += entry.second;
                    }
                    const std::int64_t gold = static_cast<std::int64_t>(sim.story().gold());
                    const bool panel = ui.show_inventory || ui.show_map || ui.show_journal;
                    if (watch.valid) {
                        if (hero.phase != aether::AttackPhase::None && !watch.attacking) {
                            g_sound.play(hero.using_strike ? "power" : "swing");
                        }
                        if (hero.dodge_ticks > 0 && watch.dodge_ticks == 0) {
                            g_sound.play("dodge");
                        }
                        if (hero.level > watch.level) {
                            g_sound.play("level_up");
                        }
                        if (items > watch.items) {
                            g_sound.play("pickup");
                        }
                        if (gold > watch.gold) {
                            g_sound.play("coin");
                        }
                        if (panel != watch.panel) {
                            g_sound.play(panel ? "open" : "close");
                        }
                        if (hero.hp <= 0 && watch.hp > 0) {
                            g_sound.play("death");
                        }
                    }
                    watch = {true,
                             hero.phase != aether::AttackPhase::None,
                             hero.dodge_ticks,
                             hero.level,
                             items,
                             gold,
                             panel,
                             hero.hp};
                    g_sound.pump();
                }
                for (FloatingText& f : floating) {
                    ++f.age;
                }
                floating.erase(std::remove_if(floating.begin(), floating.end(),
                                              [](const FloatingText& f) { return f.age > kFloatingTextFrames; }),
                               floating.end());

                if (ui.message_frames > 0) {
                    --ui.message_frames;
                }
                since_autosave += frame_seconds;
                if (!smoke_test && since_autosave >= kAutosaveSeconds) {
                    since_autosave = 0.0;
                    save_game(sim, g_slot_dir / "auto.json");
                }

                float density = SDL_GetWindowPixelDensity(window);
                if (density <= 0.0F) {
                    density = 1.0F;
                }
                const int tile_px = std::max(16, static_cast<int>(std::lround(kBaseTilePx * density)));
                cache.release_other_buckets(tile_px);
                std::string capture;
                if (!screenshot_dir.empty() && smoke_test) {
                    std::error_code ec;
                    fs::create_directories(screenshot_dir, ec);
                    const aether::DialogueView view = sim.story().dialogue_view();
                    if (view.active && view.is_choice && !captured_choice) {
                        capture = (screenshot_dir / "dialogue_choice.png").string();
                        captured_choice = true;
                    } else if (frames == 20) {
                        capture = (screenshot_dir / "walking.png").string();
                    } else if (frames == 35) {
                        capture = (screenshot_dir / "analyze.png").string();
                    } else if (frames == 82) {
                        capture = (screenshot_dir / "bag.png").string();
                    } else if (frames == kSmokeTestFrames - 2 && ui.show_map) {
                        capture = (screenshot_dir / "map.png").string();
                    } else if (frames == kSmokeTestFrames - 1 && ui.show_map) {
                        capture = (screenshot_dir / "map_world.png").string();
                    }
                }
                render(renderer, cache, assets, sim, ui, floating, tile_px, density, debug, fps, capture);

                if (smoke_test && ++frames >= kSmokeTestFrames) {
                    running = false;
                    const bool moved = g_map_name == "world" || sim.player().position.x > spawn_x + 1.0F;
                    const bool baked = cache.size() > 10;
                    const bool enemies =
                        g_map_name == "world"
                            ? (sim.chunks() != nullptr && sim.chunks()->loaded() >= 25 && smoke_save_ok)
                            : (sim.enemies().size() == 12 && sim.story().quests().size() == 1 &&
                               !sim.story().dialogue_active() && smoke_save_ok &&
                               sim.inventory().count("base:item/bread") == 1);
                    std::printf("smoke: x %.2f -> %.2f, textures %zu, enemies %zu, %s\n", static_cast<double>(spawn_x),
                                static_cast<double>(sim.player().position.x), cache.size(), sim.enemies().size(),
                                (moved && baked && enemies) ? "ok" : "FAILED");
                    if (!moved || !baked || !enemies) {
                        exit_code = 2;
                    }
                }
            }
            if (!smoke_test) {
                save_game(sim, g_slot_dir / "auto.json");
            }
            if (devices.gamepad != nullptr) {
                SDL_CloseGamepad(devices.gamepad);
            }
        }
        if (!back_to_title) {
            break;
        }
    }

    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    return exit_code;
}
