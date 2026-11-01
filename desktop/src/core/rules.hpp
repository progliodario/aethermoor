#pragma once

// Gameplay formulas. Spec: docs/spec/04-stats-and-combat.md. Reference: tools/reference/rules.py.
// Integer math only; every division is a floor division of non-negative values.

#include <cstdint>

namespace aether {

struct Primary {
    std::int64_t str = 0;
    std::int64_t vit = 0;
    std::int64_t dex = 0;
    std::int64_t agi = 0;
    std::int64_t int_ = 0;
    std::int64_t wis = 0;
    std::int64_t luk = 0;
};

struct Equipment {
    std::int64_t hp = 0;
    std::int64_t mp = 0;
    std::int64_t weapon_atk = 0;
    std::int64_t weapon_matk = 0;
    std::int64_t armor_def = 0;
    std::int64_t armor_mdef = 0;
};

struct DerivedStats {
    std::int64_t max_hp = 0;
    std::int64_t max_mp = 0;
    std::int64_t atk = 0;
    std::int64_t matk = 0;
    std::int64_t def = 0;
    std::int64_t mdef = 0;
    std::int64_t move_speed_x100 = 0;
    std::int64_t attack_speed_pm = 0;
    std::int64_t crit_chance_pm = 0;
    std::int64_t crit_mult_pm = 0;
    std::int64_t status_resist_pm = 0;
    std::int64_t mp_regen_x100 = 0;
};

DerivedStats derived_stats(std::int64_t level, const Primary& primary, const Equipment& equipment);

struct DamageInput {
    std::int64_t atk = 0;  // ATK or MATK of the attacker
    std::int64_t power_pct = 100;
    std::int64_t def_target = 0;  // DEF or MDEF of the target
    std::int64_t elem_mult_pm = 1000;
    std::int64_t pen_pm = 0;
    std::int64_t lvl_attacker = 1;
    std::int64_t lvl_target = 1;
    std::int64_t variance_pm = 1000;
    bool crit = false;
    std::int64_t crit_mult_pm = 1500;
    std::int64_t buff_mod_pm = 1000;
};

std::int64_t damage(const DamageInput& in);

std::int64_t xp_gain(std::int64_t enemy_xp, std::int64_t lvl_enemy, std::int64_t lvl_player);

}  // namespace aether
