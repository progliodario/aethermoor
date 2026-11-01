"""Gameplay formulas (docs/spec/04-stats-and-combat.md). Integer math only."""
from __future__ import annotations

import math
from dataclasses import dataclass

from .numerics import clamp

MAX_LEVEL = 99


@dataclass(frozen=True)
class Primary:
    str_: int
    vit: int
    dex: int
    agi: int
    int_: int
    wis: int
    luk: int


@dataclass(frozen=True)
class Equipment:
    hp: int = 0
    mp: int = 0
    weapon_atk: int = 0
    weapon_matk: int = 0
    armor_def: int = 0
    armor_mdef: int = 0


def derived_stats(level: int, p: Primary, eq: Equipment) -> dict[str, int]:
    """Derived statistics. Rates are permille (_pm); speeds and regen are x100 values."""
    return {
        "max_hp": 50 + p.vit * 12 + level * 8 + eq.hp,
        "max_mp": 20 + p.wis * 8 + p.int_ * 3 + level * 3 + eq.mp,
        "atk": p.str_ * 2 + p.dex // 2 + eq.weapon_atk,
        "matk": p.int_ * 2 + p.wis // 2 + eq.weapon_matk,
        "def": p.vit * 12 // 10 + eq.armor_def,
        "mdef": p.wis * 12 // 10 + eq.armor_mdef,
        "move_speed_x100": 400 * (1000 + min(p.agi * 2, 400)) // 1000,
        "attack_speed_pm": min(1000 + p.agi * 4 + p.dex * 2, 2000),
        "crit_chance_pm": min(50 + p.luk * 15 + p.dex * 10, 600),
        "crit_mult_pm": min(1500 + p.luk * 3, 2500),
        "status_resist_pm": min(p.wis * 3 + p.luk, 750),
        "mp_regen_x100": 50 + p.wis * 5,
    }


def damage(
    atk: int,
    power_pct: int,
    def_target: int,
    elem_mult_pm: int,
    pen_pm: int,
    lvl_attacker: int,
    lvl_target: int,
    variance_pm: int,
    crit: bool,
    crit_mult_pm: int,
    buff_mod_pm: int,
) -> int:
    """Final damage. Every step floors; the result is at least 1."""
    raw = atk * power_pct // 100
    elem = raw * elem_mult_pm // 1000
    def_eff = def_target * (1000 - pen_pm) // 1000
    mitigated = elem * 100 // (100 + def_eff)
    lvl_mod = clamp(1000 + 30 * (lvl_attacker - lvl_target), 700, 1300)
    x = mitigated * lvl_mod // 1000
    x = x * variance_pm // 1000
    x = x * (crit_mult_pm if crit else 1000) // 1000
    x = x * buff_mod_pm // 1000
    return max(1, x)


def xp_table_value(level: int) -> int:
    """XP needed to go from `level` to `level + 1` (generation formula, spec 04)."""
    return math.floor(30 * level ** 1.6 + 20 * level)


def generate_xp_table() -> list[int]:
    """Values for levels 1..98 (the game reads the generated table, never the formula)."""
    return [xp_table_value(level) for level in range(1, MAX_LEVEL)]


def xp_gain(enemy_xp: int, lvl_enemy: int, lvl_player: int) -> int:
    factor = clamp(1000 + 100 * (lvl_enemy - lvl_player), 100, 1500)
    return enemy_xp * factor // 1000
