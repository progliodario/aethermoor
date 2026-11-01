#pragma once

// Combat data structures. Spec: docs/spec/05-combat-v1.md. Reference: tools/reference/combat.py.

#include <cstdint>
#include <map>
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

struct CombatSetup {
    bool enabled = false;
    PlayerSetup player;
    SkillDef skill;
    std::vector<EnemySpawn> spawns;
    std::vector<std::int64_t> xp_table;  // table[level - 1] = XP to go from `level` to `level + 1`
    std::uint64_t seed = 0;
    int start_level = 1;
    StorySetup story;
    std::map<std::string, std::int64_t> start_inventory;  // items owned in a new game
};

enum class AttackPhase { None, Startup, Active, Recovery };
enum class EnemyState { Idle, Chase, Attack, Return, Dead };

const char* to_string(EnemyState state);

// Primary stats at `level` (spec 05): base + growth_pm * (level - 1) / 1000.
Primary primary_at_level(const PlayerSetup& setup, std::int64_t level);

}  // namespace aether
