#include "core/rules.hpp"

#include <algorithm>

#include "core/numerics.hpp"

namespace aether {

DerivedStats derived_stats(std::int64_t level, const Primary& p, const Equipment& eq) {
    DerivedStats s;
    s.max_hp = 50 + p.vit * 12 + level * 8 + eq.hp;
    s.max_mp = 20 + p.wis * 8 + p.int_ * 3 + level * 3 + eq.mp;
    s.atk = p.str * 2 + p.dex / 2 + eq.weapon_atk;
    s.matk = p.int_ * 2 + p.wis / 2 + eq.weapon_matk;
    s.def = p.vit * 12 / 10 + eq.armor_def;
    s.mdef = p.wis * 12 / 10 + eq.armor_mdef;
    s.move_speed_x100 = 400 * (1000 + std::min<std::int64_t>(p.agi * 2, 400)) / 1000;
    s.attack_speed_pm = std::min<std::int64_t>(1000 + p.agi * 4 + p.dex * 2, 2000);
    s.crit_chance_pm = std::min<std::int64_t>(50 + p.luk * 15 + p.dex * 10, 600);
    s.crit_mult_pm = std::min<std::int64_t>(1500 + p.luk * 3, 2500);
    s.status_resist_pm = std::min<std::int64_t>(p.wis * 3 + p.luk, 750);
    s.mp_regen_x100 = 50 + p.wis * 5;
    return s;
}

std::int64_t damage(const DamageInput& in) {
    const std::int64_t raw = in.atk * in.power_pct / 100;
    const std::int64_t elem = raw * in.elem_mult_pm / 1000;
    const std::int64_t def_eff = in.def_target * (1000 - in.pen_pm) / 1000;
    const std::int64_t mitigated = elem * 100 / (100 + def_eff);
    const std::int64_t lvl_mod = clamp_i64(1000 + 30 * (in.lvl_attacker - in.lvl_target), 700, 1300);
    std::int64_t x = mitigated * lvl_mod / 1000;
    x = x * in.variance_pm / 1000;
    x = x * (in.crit ? in.crit_mult_pm : 1000) / 1000;
    x = x * in.buff_mod_pm / 1000;
    return std::max<std::int64_t>(1, x);
}

std::int64_t xp_gain(std::int64_t enemy_xp, std::int64_t lvl_enemy, std::int64_t lvl_player) {
    const std::int64_t factor = clamp_i64(1000 + 100 * (lvl_enemy - lvl_player), 100, 1500);
    return enemy_xp * factor / 1000;
}

}  // namespace aether
