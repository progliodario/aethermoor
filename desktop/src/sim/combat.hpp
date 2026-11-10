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
    bool magical = false;          // hits with matk instead of atk (spec 05, "Damage kind")
    std::string element = "none";  // the element of its hits; none: the element of the weapon (spec 05, "Elements")
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

// The rules of a gift (spec 18, "Gift rules"): percentages (100 is neutral) and the ticks of the death save (0: none).
struct GiftDef {
    int mp_regen_pct = 100;
    int aggro_pct = 100;
    int heal_pct = 100;
    int dodge_cooldown_pct = 100;
    int death_save_ticks = 0;
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
    std::string element = "none";   // spec 05, "Elements"
    std::int64_t stagger_pct = 40;  // the share of the health that fills the stagger bar; 0: never (spec 05, "Stagger")
    std::string sound;              // the family of voices of the creature (spec 14)
    std::map<std::string, std::int64_t> weaknesses_pm;  // element -> multiplier in permille
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
    std::string weapon_element = "none";  // spec 05, "Elements"
    bool is_armor = false;
    std::int64_t armor_def = 0;
    std::int64_t armor_mdef = 0;
};

// What a shop sells: prices in permille of the base price (spec 06).
struct ShopDef {
    int price_pm = 1000;
    std::vector<std::string> stock;
};

// A prop that can be gathered from (spec 06, "Gathering").
struct GatherDrop {
    std::string item;
    std::int64_t qty_min = 1;
    std::int64_t qty_max = 1;
    std::int64_t weight_pm = 0;
};

struct GatherNode {
    std::string sound;  // plant, wood or stone: the sound of gathering
    int cooldown_ticks = 0;
    int reach_x100 = 150;
    std::vector<GatherDrop> drops;
};

// A companion that follows the player and fights (spec 10).
struct CompanionDef {
    std::string id;
    std::string name;  // an $i18n: key
    std::string art;   // the creature art it is drawn with
    int scale_pct = 100;
    std::int64_t atk_base = 0;
    std::int64_t atk_per_level = 0;
    int range_x100 = 300;
    int cooldown_ticks = 60;
    int speed_x100 = 320;
    int follow_x100 = 220;
};

// A crafting recipe (spec 06, "Crafting").
struct RecipeDef {
    std::string id;
    std::string output;
    std::int64_t output_qty = 1;
    std::vector<std::pair<std::string, std::int64_t>> inputs;
};

// A title (spec 11): earned when its condition holds. kind: kills, kills_of, level, species or quests.
struct TitleDef {
    std::string id;
    std::string name;
    std::string kind;
    std::int64_t count = 1;
    std::string enemy;         // kills_of only
    std::int64_t atk_pct = 0;  // percent added to the attack of the player's hits while the title is earned
};

// A talent (spec 11, "Talents"): every rank multiplies a kind of stat. stat: attack, health, mana or defense.
struct TalentDef {
    std::string id;
    std::string name;
    std::string stat;
    std::int64_t pct_per_rank = 0;
    int max_rank = 1;
    std::string
        requires_talent;  // the talent that must have `requires_rank` first (the branches of the tree); empty: none
    int requires_rank = 0;
};

struct CombatSetup {
    bool enabled = false;
    std::vector<TalentDef> talents;  // the talents that can be learned, in the order of the data
    int talent_points_per_level = 1;
    int echo_pct = 0;  // percent added to the maximum health, from the profile of past games (spec 11, "Echoes")
    PlayerSetup player;
    SkillDef skill;
    DodgeDef dodge;
    StrikeDef strike;
    GiftDef gift;
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
    std::map<std::string, GatherNode> gather_nodes;  // the props that can be gathered from, by art ID
    std::vector<RecipeDef> recipes;                  // crafting recipes, in the order of the data
    std::optional<CompanionDef> companion;           // the companion of the protagonist (spec 10)
    std::vector<TitleDef> titles;                    // the titles that can be earned (spec 11), in order of rank
};

enum class AttackPhase { None, Startup, Active, Recovery };
enum class EnemyState { Idle, Chase, Attack, Return, Dead };

const char* to_string(EnemyState state);

// Primary stats at `level` (spec 05): base + growth_pm * (level - 1) / 1000.
Primary primary_at_level(const PlayerSetup& setup, std::int64_t level);

}  // namespace aether
