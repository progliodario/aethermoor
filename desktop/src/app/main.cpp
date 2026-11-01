// Aethermoor desktop client (M3): a vector-art character exploring a tile map and fighting slimes.
// Flags: --version prints the version line; --smoke-test runs a short scripted session and exits (CI).

#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

#include "app/texture_cache.hpp"
#include "core/numerics.hpp"
#include "core/rules.hpp"
#include "core/version.hpp"
#include "data/pack.hpp"
#include "data/protagonist.hpp"
#include "sim/combat_loader.hpp"
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
    std::string message;  // short notice ("Game saved"), shown for a moment
    int message_frames = 0;
    bool show_inventory = false;
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
    int kind = 0;  // 0 prop, 1 enemy, 2 player, 3 npc
    const aether::Prop* prop = nullptr;
    const aether::Enemy* enemy = nullptr;
    const aether::NpcDef* npc = nullptr;
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

void draw_hud(SDL_Renderer* renderer, const Assets& assets, const aether::WorldSim& sim, const Ui& ui, float density) {
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
    std::snprintf(line, sizeof(line), "%s %lld/%lld", assets.pack.text(ui.lang, "$i18n:ui.hp").c_str(),
                  static_cast<long long>(p.hp), static_cast<long long>(sim.derived().max_hp));
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_SetRenderScale(renderer, 2.0F, 2.0F);
    SDL_RenderDebugText(renderer, (x + 6.0F) / 2.0F, (y + 3.0F * density) / 2.0F, line);
    const std::string level =
        assets.pack.text(ui.lang, "$i18n:ui.level", {{"level", static_cast<std::int64_t>(p.level)}});
    SDL_RenderDebugText(renderer, x / 2.0F, (y + bar_h + 16.0F * density) / 2.0F, level.c_str());
    SDL_RenderDebugText(renderer, (x + 110.0F * density) / 2.0F, (y + bar_h + 16.0F * density) / 2.0F,
                        assets.pack.text(ui.lang, "$i18n:ui.bag_hint").c_str());
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

aether::SaveMeta save_meta(const aether::WorldSim& sim) {
    aether::SaveMeta meta;
    meta.map = g_map_name;
    meta.game_version = std::string(aether::game_version());
    meta.protagonist = kProtagonistId;
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

void notify(Ui& ui, const std::string& text) {
    ui.message = text;
    ui.message_frames = 150;
}

// Confirms the current dialogue line or choice.
void activate_dialogue(aether::WorldSim& sim, Ui& ui) {
    aether::Story& story = sim.story();
    const aether::DialogueView view = story.dialogue_view();
    if (!view.active) {
        story.interact();
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

void draw_dialogue(SDL_Renderer* renderer, const Assets& assets, const aether::WorldSim& sim, const Ui& ui,
                   int out_w, int out_h, float density) {
    const aether::DialogueView view = sim.story().dialogue_view();
    if (!view.active) {
        return;
    }
    constexpr float kScale = 2.0F;
    const float char_w = 8.0F * kScale;
    const float margin = 24.0F * density;
    const auto columns = static_cast<std::size_t>(std::max(20.0F, (static_cast<float>(out_w) - 2.0F * margin - 16.0F) / char_w));
    std::vector<std::string> lines;
    std::string heading;
    if (view.is_choice) {
        if (!ui.last_text.empty()) {
            heading = assets.pack.text(ui.lang, "$i18n:speaker." + ui.last_speaker);
            lines = wrap_text(assets.pack.text(ui.lang, ui.last_text), columns);
            lines.emplace_back();
        }
        for (std::size_t i = 0; i < view.choices.size(); ++i) {
            const std::string text = assets.pack.text(ui.lang, view.choices[i]);
            const std::vector<std::string> wrapped = wrap_text(text, columns > 6 ? columns - 6 : columns);
            lines.push_back((static_cast<int>(i) == ui.choice_index ? "> " : "  ") + std::to_string(i + 1) + ". " +
                            (wrapped.empty() ? std::string() : wrapped.front()));
        }
    } else {
        heading = assets.pack.text(ui.lang, "$i18n:speaker." + view.speaker);
        lines = wrap_text(assets.pack.text(ui.lang, view.text), columns);
    }
    const float line_h = 8.0F * kScale + 6.0F;
    const float box_h = (static_cast<float>(lines.size()) + (heading.empty() ? 0.0F : 1.0F)) * line_h + 24.0F;
    const float box_y = static_cast<float>(out_h) - box_h - margin;
    fill_rect(renderer, margin, box_y, static_cast<float>(out_w) - 2.0F * margin, box_h, 11, 31, 58, 235);
    fill_rect(renderer, margin, box_y, static_cast<float>(out_w) - 2.0F * margin, 3.0F, 111, 227, 255, 255);
    SDL_SetRenderScale(renderer, kScale, kScale);
    float y = (box_y + 12.0F) / kScale;
    if (!heading.empty()) {
        SDL_SetRenderDrawColor(renderer, 255, 215, 120, 255);
        SDL_RenderDebugText(renderer, (margin + 12.0F) / kScale, y, heading.c_str());
        y += line_h / kScale;
    }
    SDL_SetRenderDrawColor(renderer, 235, 245, 255, 255);
    for (const std::string& line : lines) {
        SDL_RenderDebugText(renderer, (margin + 12.0F) / kScale, y, line.c_str());
        y += line_h / kScale;
    }
    SDL_SetRenderScale(renderer, 1.0F, 1.0F);
}

void draw_quest_tracker(SDL_Renderer* renderer, const Assets& assets, const aether::WorldSim& sim, const Ui& ui,
                        int out_w, float density) {
    const aether::Story& story = sim.story();
    constexpr float kScale = 2.0F;
    const float x = (static_cast<float>(out_w) - 410.0F * density) / kScale;
    float y = 12.0F * density / kScale;
    SDL_SetRenderScale(renderer, kScale, kScale);
    char line[96];
    std::snprintf(line, sizeof(line), "%s", assets.pack.text(ui.lang, "$i18n:ui.gold", {{"gold", story.gold()}}).c_str());
    SDL_SetRenderDrawColor(renderer, 255, 215, 120, 255);
    SDL_RenderDebugText(renderer, x, y, line);
    y += 16.0F;
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
        SDL_RenderDebugText(renderer, x, y, assets.pack.text(ui.lang, def.name).c_str());
        y += 14.0F;
        SDL_SetRenderDrawColor(renderer, 235, 245, 255, 255);
        for (const std::string& wrapped : wrap_text(assets.pack.text(ui.lang, stage->journal), 24)) {
            SDL_RenderDebugText(renderer, x, y, wrapped.c_str());
            y += 12.0F;
        }
        for (std::size_t i = 0; i < stage->objectives.size(); ++i) {
            if (stage->objectives[i].kind == aether::Objective::Kind::Talk) {
                continue;
            }
            std::snprintf(line, sizeof(line), "  %lld/%lld", static_cast<long long>(progress.progress[i]),
                          static_cast<long long>(stage->objectives[i].count));
            SDL_RenderDebugText(renderer, x, y, line);
            y += 12.0F;
        }
        y += 6.0F;
    }
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
        const float h = 56.0F + row * static_cast<float>(std::max<std::size_t>(items.size(), 1));
        const float y = (static_cast<float>(out_h) - h) / 2.0F;
        fill_rect(renderer, x, y, w, h, 11, 31, 58, 240);
        fill_rect(renderer, x, y, w, 3.0F, 111, 227, 255, 255);
        SDL_SetRenderScale(renderer, kScale, kScale);
        SDL_SetRenderDrawColor(renderer, 255, 215, 120, 255);
        SDL_RenderDebugText(renderer, (x + 16.0F) / kScale, (y + 14.0F) / kScale,
                            assets.pack.text(ui.lang, "$i18n:ui.inventory").c_str());
        float ty = y + 14.0F + row + 6.0F;
        SDL_SetRenderDrawColor(renderer, 235, 245, 255, 255);
        if (items.empty()) {
            SDL_RenderDebugText(renderer, (x + 16.0F) / kScale, ty / kScale,
                                assets.pack.text(ui.lang, "$i18n:ui.empty_bag").c_str());
        }
        for (const auto& [item_id, quantity] : items) {
            // "base:item/slime_gel" -> text key "item.slime_gel.name"
            std::string key = item_id.substr(item_id.find(':') + 1);
            std::replace(key.begin(), key.end(), '/', '.');
            const std::string name =
                assets.pack.text(ui.lang, "$i18n:" + key + ".name", {{"count", static_cast<std::int64_t>(quantity)}});
            const std::string line = name + "  x" + std::to_string(quantity);
            SDL_RenderDebugText(renderer, (x + 16.0F) / kScale, ty / kScale, line.c_str());
            ty += row;
        }
        SDL_SetRenderScale(renderer, 1.0F, 1.0F);
    }
    if (ui.message_frames > 0 && !ui.message.empty()) {
        SDL_SetRenderScale(renderer, kScale, kScale);
        SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
        SDL_RenderDebugText(renderer, 12.0F * density / kScale, (static_cast<float>(out_h) - 40.0F * density) / kScale,
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
            items.push_back({prop.y, 0, &prop, nullptr, nullptr});
        }
    }
    for (const aether::Enemy& enemy : sim.enemies()) {
        if (enemy.state != aether::EnemyState::Dead) {
            items.push_back({enemy.position.y, 1, nullptr, &enemy, nullptr});
        }
    }
    for (const aether::NpcDef& npc : sim.story().setup().npcs) {
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
            draw_character(renderer, cache, assets, player.moving, player.facing_left, player.clip_tick, blink, {}, fx,
                           fy, k, tile_px);
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
        SDL_RenderDebugText(renderer, sx, sy, f.text.c_str());
    }

    draw_hud(renderer, assets, sim, ui, density);
    draw_quest_tracker(renderer, assets, sim, ui, out_w, density);

    if (!sim.story().dialogue_active()) {
        if (const aether::NpcDef* npc = sim.story().npc_in_range()) {
            const std::string hint = assets.pack.text(ui.lang, "$i18n:ui.interact");
            const float hx = (npc->x - cam.x) * tile - static_cast<float>(hint.size()) * 4.0F;
            const float hy = (npc->y - cam.y) * tile - 2.2F * tile;
            SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
            SDL_RenderDebugText(renderer, hx, hy, hint.c_str());
        }
    }
    draw_dialogue(renderer, assets, sim, ui, out_w, out_h, density);
    draw_inventory_and_notice(renderer, assets, sim, ui, out_w, out_h, density);

    if (debug) {
        char line[160];
        std::snprintf(line, sizeof(line), "%s  %.0f fps  pos %.2f,%.2f  tile %dpx  textures %zu",
                      aether::version_line().c_str(), fps, static_cast<double>(sim.player().position.x),
                      static_cast<double>(sim.player().position.y), tile_px, cache.size());
        SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
        SDL_RenderDebugText(renderer, 8.0F, static_cast<float>(out_h) - 16.0F, line);
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

}  // namespace

int main(int argc, char** argv) {
    bool smoke_test = false;
    std::string map_choice;  // "demo" or "world"; the default depends on the mode
    std::optional<std::uint64_t> forced_seed;
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
        if (std::strncmp(argv[i], "--seed=", 7) == 0) {
            forced_seed = std::strtoull(argv[i] + 7, nullptr, 0);
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

    // The seed: forced, else the one of the last session on this map (so the same world comes back), else a new one.
    std::uint64_t seed = smoke_test ? 1234U : SDL_GetTicksNS();
    if (forced_seed) {
        seed = *forced_seed;
    } else if (!smoke_test) {
        if (const auto text = read_text_file(save_dir() / "auto.json")) {
            if (const auto peek = aether::save_peek(*text); peek && peek->map == g_map_name) {
                seed = peek->seed;
            }
        }
    }
    if (g_map_name == "world") {
        const auto text = assets.pack.read_document(kWorldId);
        std::string world_error;
        const auto params = text ? aether::parse_world_params(*text, world_error) : std::nullopt;
        if (!params) {
            SDL_Log("cannot read the world parameters: %s", world_error.c_str());
            SDL_Quit();
            return 1;
        }
        assets.map = aether::make_tilemap(aether::generate_world(seed, *params), *params);
    }
    std::string combat_error;
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
        const aether::SaveState initial_state = sim.capture();
        double since_autosave = 0.0;
        InputDevices devices;
        devices.open_first_gamepad();
        std::vector<FloatingText> floating;
        Ui ui;
        ui.lang = detect_language();

        if (!smoke_test) {  // continue the last session, if there is one
            std::string ignored;
            const auto previous = read_text_file(save_dir() / "auto.json");
            const auto peek = previous ? aether::save_peek(*previous) : std::nullopt;
            if (peek && peek->map == g_map_name && peek->seed == seed && load_game(sim, save_dir() / "auto.json", ignored)) {
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
                if (event.type == SDL_EVENT_QUIT ||
                    (event.type == SDL_EVENT_KEY_DOWN && event.key.key == SDLK_ESCAPE)) {
                    running = false;
                } else if (event.type == SDL_EVENT_KEY_DOWN && event.key.key == SDLK_F3) {
                    debug = !debug;
                } else if (event.type == SDL_EVENT_KEY_DOWN && !smoke_test &&
                           (event.key.key == SDLK_F5 || event.key.key == SDLK_F9 || event.key.key == SDLK_F7 ||
                            event.key.key == SDLK_I)) {
                    if (event.key.key == SDLK_I) {
                        ui.show_inventory = !ui.show_inventory;
                    } else if (event.key.key == SDLK_F5) {
                        notify(ui, save_game(sim, save_dir() / "quick.json") ? assets.pack.text(ui.lang, "$i18n:ui.saved")
                                                                              : "save failed");
                    } else if (event.key.key == SDLK_F9) {
                        std::string load_error;
                        notify(ui, load_game(sim, save_dir() / "quick.json", load_error)
                                       ? assets.pack.text(ui.lang, "$i18n:ui.loaded")
                                       : assets.pack.text(ui.lang, "$i18n:ui.load_failed"));
                    } else {
                        std::string ignored;
                        sim.restore(initial_state, ignored);
                        notify(ui, assets.pack.text(ui.lang, "$i18n:ui.new_game"));
                    }
                } else if (event.type == SDL_EVENT_KEY_DOWN && !smoke_test) {
                    handle_dialogue_key(sim, ui, event.key.key);
                } else if (event.type == SDL_EVENT_MOUSE_BUTTON_DOWN && !smoke_test && sim.story().dialogue_active()) {
                    activate_dialogue(sim, ui);
                } else if (event.type == SDL_EVENT_GAMEPAD_BUTTON_DOWN && !smoke_test) {
                    handle_dialogue_button(sim, ui, event.gbutton.button);
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
                if (frames == 80) {
                    ui.show_inventory = true;  // the last frames show the bag
                }
                sim.tick(input.x, input.y, input.attack);
            } else if (ui.show_inventory) {
                accumulator = 0.0;  // the bag pauses the game
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

            {
                const aether::DialogueView spoken = sim.story().dialogue_view();
                if (spoken.active && !spoken.is_choice) {
                    ui.last_speaker = spoken.speaker;
                    ui.last_text = spoken.text;
                } else if (!spoken.active) {
                    ui.last_text.clear();
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

            if (ui.message_frames > 0) {
                --ui.message_frames;
            }
            since_autosave += frame_seconds;
            if (!smoke_test && since_autosave >= kAutosaveSeconds) {
                since_autosave = 0.0;
                save_game(sim, save_dir() / "auto.json");
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
                } else if (frames == kSmokeTestFrames - 1) {
                    capture = (screenshot_dir / "bag.png").string();
                }
            }
            render(renderer, cache, assets, sim, ui, floating, tile_px, density, debug, fps, capture);

            if (smoke_test && ++frames >= kSmokeTestFrames) {
                running = false;
                const bool moved = g_map_name == "world" || sim.player().position.x > spawn_x + 1.0F;
                const bool baked = cache.size() > 10;
                const bool enemies = g_map_name == "world"
                                         ? (sim.enemies().size() > 20 && assets.map.props.size() > 1000 && smoke_save_ok)
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
            save_game(sim, save_dir() / "auto.json");
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
