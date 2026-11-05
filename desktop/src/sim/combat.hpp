#pragma once

// Combat data structures. Spec: docs/spec/05-combat-v1.md. Reference: tools/reference/combat.py.

#include <cstdint>
#include <map>
#include <optional>
#include <string>
#include <vector>

#include "core/rules.hpp"
#include "sim/story.hpp"

namespace aether {

struct SkillDef {
    int startup = 6;
    int active = 4;
    int recovery = 10;
    int cooldown = 24;
    std::int64_t power_pct = 100;
    int radius_x100 = 160;
    int angle_deg = 110;
};

// The dodge roll (spec 05, "Dodge roll"): from a skill of type "movement"; `enabled` is false when the protagonist has
// none.
struct DodgeDef {
    bool enabled = false;
    int ticks = 12;
    int speed_mult_x100 = 260;
    int iframes = 14;
    int cooldown = 40;
};

// The power strike (spec 05, "Mana"): the second skill with a hitbox; `enabled` is false when the protagonist has none.
struct StrikeDef {
    bool enabled = false;
    SkillDef skill;
    std::int64_t mp = 10;
};

struct DropDef {
    std::string item;
    std::int64_t qty_min = 1;
    std::int64_t qty_max = 1;
    std::int64_t weight_pm = 0;
};

struct BehaviorDef {
    int aggro_x100 = 600;
    int leash_x100 = 900;
    int attack_range_x100 = 120;
    int hit_range_x100 = 150;
    int windup_ticks = 18;
    int recovery_ticks = 30;
};

struct EnemyDef {
    std::string id;
    std::string art;
    std::int64_t level = 1;
    std::int64_t hp = 1;
    std::int64_t atk = 0;
    std::int64_t def = 0;
    std::int64_t xp = 0;
    int radius_x100 = 35;
    int speed_x100 = 250;
    std::vector<DropDef> drops;
    BehaviorDef behavior;
};

struct EnemySpawn {
    EnemyDef def;
    float x = 0.0F;
    float y = 0.0F;
};

struct PlayerSetup {
    Primary base;
    Primary growth_pm;
    std::int64_t weapon_atk = 0;
    std::int64_t weapon_matk = 0;
};

// What using an item does (spec 06): a list of effects.
struct ItemEffect {
    std::string effect;  // "heal"
    std::int64_t amount = 0;
};

struct ItemDef {
    std::string kind;  // weapon, armor, food, material, ...
    std::int64_t price = 0;
    int stack_max = 0;  // 0: the default of the kind (spec 06)
    std::vector<ItemEffect> effects;
    bool is_weapon = false;
    std::int64_t weapon_atk = 0;
    std::int64_t weapon_matk = 0;
    bool is_armor = false;
    std::int64_t armor_def = 0;
    std::int64_t armor_mdef = 0;
};

// What a shop sells: prices in permille of the base price (spec 06).
struct ShopDef {
    int price_pm = 1000;
    std::vector<std::string> stock;
};

struct CombatSetup {
    bool enabled = false;
    PlayerSetup player;
    SkillDef skill;
    DodgeDef dodge;
    StrikeDef strike;
    std::vector<EnemySpawn> spawns;
    std::vector<std::int64_t> xp_table;  // table[level - 1] = XP to go from `level` to `level + 1`
    std::uint64_t seed = 0;
    int start_level = 1;
    StorySetup story;
    std::map<std::string, std::int64_t> start_inventory;  // items owned in a new game
    std::map<std::string, ItemDef> items;                 // every item, by item ID
    std::string start_weapon;                             // the weapon worn in a new game (an item ID, or empty)
    std::string start_armor;                              // the armor worn in a new game (an item ID, or empty)
    std::optional<ShopDef> shop;  // the shop of fixed maps and scenarios (streamed worlds use their regions)
    std::map<std::string, EnemyDef> stream_enemies;  // the enemies of the fauna of a streamed world, by ID
};

enum class AttackPhase { None, Startup, Active, Recovery };
enum class EnemyState { Idle, Chase, Attack, Return, Dead };

const char* to_string(EnemyState state);

// Primary stats at `level` (spec 05): base + growth_pm * (level - 1) / 1000.
Primary primary_at_level(const PlayerSetup& setup, std::int64_t level);

}  // namespace aether
