"""Combat simulation v1 (docs/spec/05-combat-v1.md). Integer rules, floating point movement.

The scenario dictionaries are the same ones stored in tests/conformance/combat.json; the clients build
their own structures from them and must reach the same checkpoints.
"""
from __future__ import annotations

import math

from . import movement as mv
from . import numerics as nm
from . import rules
from .story import NPC_RADIUS, Story

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
        story_setup = scenario.get("story")
        if story_setup:
            self.props += [(n["pos"][0], n["pos"][1], NPC_RADIUS) for n in story_setup["npcs"]]
        seed = int(scenario["seed"], 16)
        self.combat = nm.derive_stream(seed, "combat")
        self.loot = nm.derive_stream(seed, "loot")
        pl = scenario["player"]
        self.base, self.growth = pl["base_stats"], pl["growth_pm"]
        self.weapon_atk, self.weapon_matk = pl["weapon_atk"], pl["weapon_matk"]
        self.xp_table = scenario["xp_table"]
        self.skill = scenario["skill"]
        self.strike = scenario.get("strike")  # the power strike: a skill dict like `skill` plus "mp"; None: none (spec 05, "Mana")
        self.cur_skill = self.skill  # the skill of the swing in progress
        self.dodge = scenario.get("dodge")  # {"ticks", "speed_mult_x100", "iframes", "cooldown"}, or None: no dodge (spec 05, "Dodge roll")
        self.dodge_ticks = 0
        self.dodge_cooldown = 0
        self.dodge_dir = (1.0, 0.0)
        self.spawn = tuple(pl["start"])
        self.x, self.y = self.spawn
        self.facing = (1.0, 0.0)
        self.facing_left = False
        self.moving = False
        self.clip_tick = 0
        self.level = pl.get("level", 1)
        self.xp = 0
        self.inventory: dict[str, int] = dict(scenario.get("inventory", {}))
        # item id -> {"kind", "price", "stack_max"?, "effects"?, "weapon"?: {"atk", "matk"}, "armor"?: {"def", "mdef"}}
        self.items: dict[str, dict] = scenario.get("items", {})
        self.equipped = {"weapon": scenario.get("equipped", {}).get("weapon", ""), "armor": scenario.get("equipped", {}).get("armor", "")}
        self.shop: dict | None = None  # the open shop: {"price_pm": ..., "stock": [...]}
        self.shop_def: dict | None = scenario.get("shop")  # what the shop of this place sells
        self.derived = self._derive()
        self.hp = self.derived["max_hp"]
        self.mp_u = self.derived["max_mp"] * 6000  # mana in units of 1/6000 of a point
        self.iframes = 0
        self.cooldown = 0
        self.phase = NONE
        self.phase_tick = 0
        self.hit_set: set[int] = set()
        self.kills = 0
        self.deaths = 0
        self.enemies = [_Enemy(e) for e in scenario["enemies"]]
        self.story = Story(self, story_setup) if story_setup else None
        if self.story is not None:
            self.story.gold = scenario.get("start_gold", 0)

    # ------------------------------------------------------------------------------- helpers

    def _derive(self) -> dict[str, int]:
        primary = primary_at_level(self.base, self.growth, self.level)
        weapon = self.items.get(self.equipped["weapon"], {}).get("weapon")
        armor = self.items.get(self.equipped["armor"], {}).get("armor")
        return rules.derived_stats(self.level, primary, rules.Equipment(
            weapon_atk=weapon["atk"] if weapon else self.weapon_atk,
            weapon_matk=weapon["matk"] if weapon else self.weapon_matk,
            armor_def=armor["def"] if armor else 0,
            armor_mdef=armor["mdef"] if armor else 0))

    @property
    def speed(self) -> float:
        return self.derived["move_speed_x100"] / 100

    # --------------------------------------------------------------------------------- tick

    def tick(self, raw_x: float, raw_y: float, attack: bool, dodge: bool = False, strike: bool = False) -> None:
        if self.story is not None and self.story.dialogue_active:
            raw_x, raw_y, attack, dodge, strike = 0.0, 0.0, False, False, False
        if self.iframes > 0:
            self.iframes -= 1
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= 1
        self.mp_u = min(self.derived["max_mp"] * 6000, self.mp_u + self.derived["mp_regen_x100"])

        vx, vy = mv.normalize_input(raw_x, raw_y)
        if dodge and self.dodge is not None and self.dodge_ticks == 0 and self.dodge_cooldown == 0 and self.phase == NONE:
            dx, dy = (vx, vy) if (vx != 0.0 or vy != 0.0) else self.facing
            length = math.sqrt(dx * dx + dy * dy)
            self.dodge_dir = (dx / length, dy / length)
            self.facing = self.dodge_dir
            if self.dodge_dir[0] != 0.0:
                self.facing_left = self.dodge_dir[0] < 0.0
            self.dodge_ticks, self.dodge_cooldown = self.dodge["ticks"], self.dodge["cooldown"]
            self.iframes = max(self.iframes, self.dodge["iframes"])
        if self.dodge_ticks > 0:
            self.dodge_ticks -= 1
            if not self.moving:
                self.moving, self.clip_tick = True, 0
            else:
                self.clip_tick += 1
            self.x, self.y = mv.step(self.x, self.y, self.dodge_dir[0], self.dodge_dir[1],
                                     self.speed * self.dodge["speed_mult_x100"] / 100, self.grid, self.props)
        else:
            if (vx != 0.0 or vy != 0.0) and self.phase in (NONE, STARTUP):
                length = math.sqrt(vx * vx + vy * vy)
                self.facing = (vx / length, vy / length)
            mult = ATTACK_MOVE_MULT if self.phase != NONE else 1.0
            moving_now = vx != 0.0 or vy != 0.0
            if vx != 0.0:
                self.facing_left = vx < 0.0
            if moving_now != self.moving:
                self.moving, self.clip_tick = moving_now, 0
            else:
                self.clip_tick += 1
            self.x, self.y = mv.step(self.x, self.y, vx, vy, self.speed * mult, self.grid, self.props)

            if self.phase == NONE and self.cooldown == 0:
                if strike and self.strike is not None and self.mp_u >= self.strike["mp"] * 6000:
                    self.mp_u -= self.strike["mp"] * 6000
                    self.cur_skill = self.strike
                    self.phase, self.phase_tick, self.cooldown = STARTUP, 0, self.strike["cooldown"]
                    self.hit_set = set()
                elif attack:
                    self.cur_skill = self.skill
                    self.phase, self.phase_tick, self.cooldown = STARTUP, 0, self.skill["cooldown"]
                    self.hit_set = set()
        self._advance_attack()

        for index, enemy in enumerate(self.enemies):
            self._update_enemy(index, enemy)

    def _advance_attack(self) -> None:
        s = self.cur_skill
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
        s = self.cur_skill
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
        self.grant_xp(rules.xp_gain(enemy.d["xp"], enemy.d["level"], self.level))
        if self.story is not None:
            self.story.on_kill(enemy.d.get("id", ""))

    def season_id(self) -> str:
        return ""  # a combat scenario has no world time

    def tod_pm(self) -> int:
        return 0

    def heal_full(self) -> None:
        self.hp = self.derived["max_hp"]
        self.mp_u = self.derived["max_mp"] * 6000

    def grant_xp(self, amount: int) -> None:
        self.xp += amount
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
            self.dodge_ticks, self.dodge_cooldown = 0, 0
            self.mp_u = self.derived["max_mp"] * 6000
            self.iframes = RESPAWN_IFRAMES

    # ---------------------------------------------------------------------------------- saves

    def use_item(self, item_id: str) -> bool:
        """Uses one item of the inventory (docs/spec/06-items.md). Returns False, changing nothing, when it is refused."""
        if self.story is not None and self.story.dialogue_active:
            return False
        item = self.items.get(item_id)
        if item is None or self.inventory.get(item_id, 0) < 1:
            return False
        heal = sum(e["amount"] for e in item["effects"] if e["effect"] == "heal")
        mana = sum(e["amount"] for e in item["effects"] if e["effect"] == "restore_mp")
        full_mp = self.derived["max_mp"] * 6000
        if not ((heal > 0 and self.hp < self.derived["max_hp"]) or (mana > 0 and self.mp_u < full_mp)):
            return False
        if heal > 0:
            self.hp = min(self.derived["max_hp"], self.hp + heal)
        if mana > 0:
            self.mp_u = min(full_mp, self.mp_u + mana * 6000)
        self.inventory[item_id] -= 1
        if self.inventory[item_id] == 0:
            del self.inventory[item_id]
        return True

    def equip(self, item_id: str) -> bool:
        """Equips a weapon or an armor of the inventory (docs/spec/06-items.md). Returns False, changing nothing, when refused."""
        item = self.items.get(item_id)
        if item is None or self.inventory.get(item_id, 0) < 1:
            return False
        slot = {"weapon": "weapon", "armor": "armor"}.get(item.get("kind", ""))
        if slot is None or slot not in item or self.equipped[slot] == item_id:
            return False
        self.equipped[slot] = item_id
        self.derived = self._derive()
        self.hp = min(self.hp, self.derived["max_hp"])
        return True

    def _stack_max(self, item_id: str) -> int:
        item = self.items[item_id]
        return item.get("stack_max", 1 if item.get("kind") in ("weapon", "armor", "accessory") else 99)

    def open_shop(self) -> bool:
        """Opens the shop of the place (the `open_shop` dialogue effect)."""
        if self.shop_def is None:
            return False
        self.shop = self.shop_def
        return True

    def close_shop(self) -> None:
        self.shop = None

    def open_board(self) -> None:
        """The `open_board` dialogue effect: the world shows the board (nothing to model in a scenario)."""

    def buy(self, item_id: str) -> bool:
        """Buys one item from the open shop (spec 06). Returns False, changing nothing, when refused."""
        if self.shop is None or self.story is None or item_id not in self.shop["stock"]:
            return False
        item = self.items.get(item_id)
        if item is None or item.get("price", 0) <= 0 or self.inventory.get(item_id, 0) >= self._stack_max(item_id):
            return False
        price = max(1, item["price"] * self.shop["price_pm"] // 1000)
        if self.story.gold < price:
            return False
        self.story.gold -= price
        self.inventory[item_id] = self.inventory.get(item_id, 0) + 1
        return True

    def sell(self, item_id: str) -> bool:
        """Sells one item of the inventory to the open shop (spec 06). Returns False, changing nothing, when refused."""
        if self.shop is None or self.story is None:
            return False
        item = self.items.get(item_id)
        owned = self.inventory.get(item_id, 0)
        if item is None or owned < 1 or item.get("price", 0) <= 0:
            return False
        if owned == 1 and item_id in self.equipped.values():
            return False
        self.story.gold += max(1, item["price"] // 2)
        self.inventory[item_id] = owned - 1
        if self.inventory[item_id] == 0:
            del self.inventory[item_id]
        return True

    def save_state(self) -> dict:
        """The save document of docs/spec/12-save-format.md (without the file-level metadata)."""
        return {
            "player": {
                "x": self.x, "y": self.y, "facing": [self.facing[0], self.facing[1]],
                "facing_left": self.facing_left, "moving": self.moving, "clip_tick": self.clip_tick,
                "hp": self.hp, "level": self.level, "xp": self.xp, "deaths": self.deaths, "kills": self.kills,
                "iframes": self.iframes, "cooldown": self.cooldown, "phase": self.phase,
                "phase_tick": self.phase_tick,
                "hit_set": [i in self.hit_set for i in range(len(self.enemies))],
            },
            "rng": {
                "combat": {"state": f"0x{self.combat.state:016x}", "inc": f"0x{self.combat.inc:016x}"},
                "loot": {"state": f"0x{self.loot.state:016x}", "inc": f"0x{self.loot.inc:016x}"},
            },
            "enemies": [{"x": e.x, "y": e.y, "hp": e.hp, "state": e.state, "state_tick": e.t} for e in self.enemies],
            "inventory": dict(sorted(self.inventory.items())),
            "equipped": dict(self.equipped),
            "story": self.story.save_state() if self.story is not None else None,
        }

    def load_state(self, save: dict) -> None:
        p = save["player"]
        self.x, self.y = p["x"], p["y"]
        self.facing = (p["facing"][0], p["facing"][1])
        self.facing_left, self.moving, self.clip_tick = p["facing_left"], p["moving"], p["clip_tick"]
        self.level, self.xp, self.deaths, self.kills = p["level"], p["xp"], p["deaths"], p["kills"]
        self.derived = self._derive()
        self.hp = p["hp"]
        self.iframes, self.cooldown, self.phase, self.phase_tick = p["iframes"], p["cooldown"], p["phase"], p["phase_tick"]
        self.hit_set = {i for i, hit in enumerate(p["hit_set"]) if hit}
        self.dodge_ticks, self.dodge_cooldown = 0, 0  # a roll in progress is not saved (spec 05)
        self.mp_u, self.cur_skill = self.derived["max_mp"] * 6000, self.skill  # nor is the mana: a loaded game starts full
        for name, stream in (("combat", self.combat), ("loot", self.loot)):
            stream.state = int(save["rng"][name]["state"], 16)
            stream.inc = int(save["rng"][name]["inc"], 16)
        for enemy, data in zip(self.enemies, save["enemies"]):
            enemy.x, enemy.y, enemy.hp, enemy.state, enemy.t = data["x"], data["y"], data["hp"], data["state"], data["state_tick"]
        self.inventory = dict(save["inventory"])
        self.equipped = {"weapon": "", "armor": "", **save.get("equipped", {})}
        self.derived = self._derive()
        if self.story is not None and save["story"] is not None:
            self.story.load_state(save["story"])

    # ------------------------------------------------------------------------------ checkpoint

    def snapshot(self) -> dict:
        return {
            "player": {"hp": self.hp, "level": self.level, "xp": self.xp, "deaths": self.deaths,
                       "x": self.x, "y": self.y},
            "enemies": [{"hp": e.hp, "state": e.state, "x": e.x, "y": e.y} for e in self.enemies],
            "kills": self.kills,
            "inventory": dict(sorted(self.inventory.items())),
            "equipped": dict(self.equipped),
            **({"story": self.story.snapshot()} if self.story is not None else {}),
        }


def run_segment(sim: CombatSim, segment: dict) -> None:
    """Runs the story commands of a script segment, then its ticks."""
    move = segment["move"]
    for command in segment.get("do", []):
        if command["cmd"] == "use":
            sim.use_item(command["item"])
            continue
        if command["cmd"] in ("equip", "buy", "sell"):
            getattr(sim, command["cmd"])(command["item"])
            continue
        if command["cmd"] == "start_quest":
            sim.story.start_quest(command["quest"])
            continue
        if command["cmd"] == "open_shop":
            sim.open_shop()
            continue
        if command["cmd"] == "close_shop":
            sim.close_shop()
            continue
        if sim.story is None:
            continue
        if command["cmd"] == "interact":
            sim.story.interact()
        elif command["cmd"] == "advance":
            sim.story.advance()
        elif command["cmd"] == "choose":
            sim.story.choose(command["index"])
    for _ in range(segment["ticks"]):
        sim.tick(move[0], move[1], segment["attack"], segment.get("dodge", False), segment.get("strike", False))


def run_scenario(scenario: dict) -> list[dict]:
    sim = CombatSim(scenario)
    out = []
    for segment in scenario["script"]:
        run_segment(sim, segment)
        out.append(sim.snapshot())
    return out


def run_with_save(scenario: dict, split: int) -> tuple[dict, list[dict]]:
    """Save document taken before segment `split`, and the checkpoints of the segments from `split` on."""
    sim = CombatSim(scenario)
    save: dict = {}
    checkpoints = []
    for index, segment in enumerate(scenario["script"]):
        if index == split:
            save = sim.save_state()
        run_segment(sim, segment)
        if index >= split:
            checkpoints.append(sim.snapshot())
    return save, checkpoints
