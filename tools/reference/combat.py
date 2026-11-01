"""Combat simulation v1 (docs/spec/05-combat-v1.md). Integer rules, floating point movement.

The scenario dictionaries are the same ones stored in tests/conformance/combat.json; the clients build
their own structures from them and must reach the same checkpoints.
"""
from __future__ import annotations

import math

from . import movement as mv
from . import numerics as nm
from . import rules

NONE, STARTUP, ACTIVE, RECOVERY = "none", "startup", "active", "recovery"
IDLE, CHASE, ATTACK, RETURN, DEAD = "idle", "chase", "attack", "return", "dead"
PLAYER_HIT_IFRAMES = 45
RESPAWN_IFRAMES = 90
ATTACK_MOVE_MULT = 0.5
MAX_LEVEL = 99
RETURN_ARRIVAL = 0.1


def primary_at_level(base: dict, growth_pm: dict, level: int) -> rules.Primary:
    def stat(key: str) -> int:
        return base[key] + growth_pm[key] * (level - 1) // 1000
    return rules.Primary(stat("str"), stat("vit"), stat("dex"), stat("agi"), stat("int"), stat("wis"), stat("luk"))


class _Enemy:
    def __init__(self, spec: dict) -> None:
        self.d = spec["def"]
        self.x, self.y = spec["pos"]
        self.home = (self.x, self.y)
        self.hp = self.d["hp"]
        self.state = IDLE
        self.t = 0
        self.radius = self.d["radius_x100"] / 100
        self.speed = self.d["speed_x100"] / 100


class CombatSim:
    def __init__(self, scenario: dict) -> None:
        self.grid = mv.Grid(scenario["grid"])
        self.props = [tuple(p) for p in scenario["props"]]
        seed = int(scenario["seed"], 16)
        self.combat = nm.derive_stream(seed, "combat")
        self.loot = nm.derive_stream(seed, "loot")
        pl = scenario["player"]
        self.base, self.growth = pl["base_stats"], pl["growth_pm"]
        self.weapon_atk, self.weapon_matk = pl["weapon_atk"], pl["weapon_matk"]
        self.xp_table = scenario["xp_table"]
        self.skill = scenario["skill"]
        self.spawn = tuple(pl["start"])
        self.x, self.y = self.spawn
        self.facing = (1.0, 0.0)
        self.level = pl.get("level", 1)
        self.xp = 0
        self.derived = self._derive()
        self.hp = self.derived["max_hp"]
        self.iframes = 0
        self.cooldown = 0
        self.phase = NONE
        self.phase_tick = 0
        self.hit_set: set[int] = set()
        self.kills = 0
        self.deaths = 0
        self.inventory: dict[str, int] = {}
        self.enemies = [_Enemy(e) for e in scenario["enemies"]]

    # ------------------------------------------------------------------------------- helpers

    def _derive(self) -> dict[str, int]:
        primary = primary_at_level(self.base, self.growth, self.level)
        return rules.derived_stats(self.level, primary, rules.Equipment(
            weapon_atk=self.weapon_atk, weapon_matk=self.weapon_matk))

    @property
    def speed(self) -> float:
        return self.derived["move_speed_x100"] / 100

    # --------------------------------------------------------------------------------- tick

    def tick(self, raw_x: float, raw_y: float, attack: bool) -> None:
        if self.iframes > 0:
            self.iframes -= 1
        if self.cooldown > 0:
            self.cooldown -= 1

        vx, vy = mv.normalize_input(raw_x, raw_y)
        if (vx != 0.0 or vy != 0.0) and self.phase in (NONE, STARTUP):
            length = math.sqrt(vx * vx + vy * vy)
            self.facing = (vx / length, vy / length)
        mult = ATTACK_MOVE_MULT if self.phase != NONE else 1.0
        self.x, self.y = mv.step(self.x, self.y, vx, vy, self.speed * mult, self.grid, self.props)

        if attack and self.phase == NONE and self.cooldown == 0:
            self.phase, self.phase_tick, self.cooldown = STARTUP, 0, self.skill["cooldown"]
            self.hit_set = set()
        self._advance_attack()

        for index, enemy in enumerate(self.enemies):
            self._update_enemy(index, enemy)

    def _advance_attack(self) -> None:
        s = self.skill
        if self.phase == STARTUP:
            self.phase_tick += 1
            if self.phase_tick >= s["startup"]:
                self.phase, self.phase_tick = ACTIVE, 0
        elif self.phase == ACTIVE:
            self._do_hits()
            self.phase_tick += 1
            if self.phase_tick >= s["active"]:
                self.phase, self.phase_tick = RECOVERY, 0
        elif self.phase == RECOVERY:
            self.phase_tick += 1
            if self.phase_tick >= s["recovery"]:
                self.phase = NONE

    def _do_hits(self) -> None:
        s = self.skill
        cos_half = math.cos(math.radians(s["angle_deg"] / 2))
        for index, enemy in enumerate(self.enemies):
            if enemy.state == DEAD or index in self.hit_set:
                continue
            dx, dy = enemy.x - self.x, enemy.y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > s["radius_x100"] / 100 + enemy.radius:
                continue
            if dist > 0:
                dot = (dx * self.facing[0] + dy * self.facing[1]) / dist
                if dot < cos_half:
                    continue
            self.hit_set.add(index)
            variance = 950 + self.combat.next_bounded(101)
            crit = self.combat.next_bounded(1000) < self.derived["crit_chance_pm"]
            damage = rules.damage(self.derived["atk"], s["power_pct"], enemy.d["def"], 1000, 0, self.level,
                                  enemy.d["level"], variance, crit, self.derived["crit_mult_pm"], 1000)
            enemy.hp -= damage
            if enemy.hp <= 0:
                enemy.hp = 0
                enemy.state = DEAD
                self._on_kill(enemy)

    def _on_kill(self, enemy: _Enemy) -> None:
        self.kills += 1
        for drop in enemy.d["drops"]:
            if self.loot.next_bounded(1000) < drop["weight_pm"]:
                qty = drop["qty_min"]
                if drop["qty_max"] > drop["qty_min"]:
                    qty += self.loot.next_bounded(drop["qty_max"] - drop["qty_min"] + 1)
                self.inventory[drop["item"]] = self.inventory.get(drop["item"], 0) + qty
        self.xp += rules.xp_gain(enemy.d["xp"], enemy.d["level"], self.level)
        while self.level < MAX_LEVEL and self.level - 1 < len(self.xp_table) and self.xp >= self.xp_table[self.level - 1]:
            self.xp -= self.xp_table[self.level - 1]
            self.level += 1
            self.derived = self._derive()
            self.hp = self.derived["max_hp"]

    def _update_enemy(self, index: int, e: _Enemy) -> None:
        if e.state == DEAD:
            return
        b = e.d["behavior"]
        dx, dy = self.x - e.x, self.y - e.y
        dist = math.sqrt(dx * dx + dy * dy)
        if e.state == IDLE:
            if dist <= b["aggro_x100"] / 100:
                e.state, e.t = CHASE, 0
        elif e.state == CHASE:
            if dist > b["leash_x100"] / 100:
                e.state = RETURN
            elif dist <= b["attack_range_x100"] / 100:
                e.state, e.t = ATTACK, 0
            else:
                self._move_enemy(e, self.x, self.y)
        elif e.state == ATTACK:
            e.t += 1
            if e.t == b["windup_ticks"] and dist <= b["hit_range_x100"] / 100 and self.iframes == 0:
                self._hurt_player(e)
            if e.t >= b["windup_ticks"] + b["recovery_ticks"]:
                e.state, e.t = CHASE, 0
        elif e.state == RETURN:
            hx, hy = e.home
            if math.sqrt((hx - e.x) ** 2 + (hy - e.y) ** 2) <= RETURN_ARRIVAL:
                e.state, e.hp = IDLE, e.d["hp"]
            else:
                self._move_enemy(e, hx, hy)

    def _move_enemy(self, e: _Enemy, tx: float, ty: float) -> None:
        dx, dy = tx - e.x, ty - e.y
        dist = math.sqrt(dx * dx + dy * dy)
        step = e.speed * mv.TICK_DT
        if dist > 0:
            if dist <= step:
                e.x, e.y = tx, ty
            else:
                e.x += dx / dist * step
                e.y += dy / dist * step
        e.x, e.y = mv.resolve(e.x, e.y, self.grid, self.props, e.radius)

    def _hurt_player(self, e: _Enemy) -> None:
        variance = 950 + self.combat.next_bounded(101)
        damage = rules.damage(e.d["atk"], 100, self.derived["def"], 1000, 0, e.d["level"], self.level,
                              variance, False, 1500, 1000)
        self.hp -= damage
        self.iframes = PLAYER_HIT_IFRAMES
        if self.hp <= 0:
            self.deaths += 1
            self.hp = self.derived["max_hp"]
            self.x, self.y = self.spawn
            self.phase, self.phase_tick = NONE, 0
            self.iframes = RESPAWN_IFRAMES

    # ------------------------------------------------------------------------------ checkpoint

    def snapshot(self) -> dict:
        return {
            "player": {"hp": self.hp, "level": self.level, "xp": self.xp, "deaths": self.deaths,
                       "x": self.x, "y": self.y},
            "enemies": [{"hp": e.hp, "state": e.state, "x": e.x, "y": e.y} for e in self.enemies],
            "kills": self.kills,
            "inventory": dict(sorted(self.inventory.items())),
        }


def run_scenario(scenario: dict) -> list[dict]:
    sim = CombatSim(scenario)
    out = []
    for segment in scenario["script"]:
        move = segment["move"]
        for _ in range(segment["ticks"]):
            sim.tick(move[0], move[1], segment["attack"])
        out.append(sim.snapshot())
    return out
