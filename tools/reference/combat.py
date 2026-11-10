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
# Status effects (spec 05, "Status effects"): the element of the weapon -> (status, chance in permille, ticks).
STATUS_OF = {"fire": ("burn", 350, 150), "water": ("chill", 400, 180), "wind": ("stun", 300, 45), "earth": ("stun", 300, 75),
             "light": ("weaken", 350, 240), "dark": ("weaken", 350, 240)}
BURN_PERIOD = 30
PLAYER_BURN_PCT = 2  # a burn on the player takes this much of the maximum health every period, and never the last point
# The parry (spec 05, "Parry"): the window, the wait before the next one, what it does to the attacker, the safety it gives.
PARRY_TICKS = 14
# Stagger (spec 05, "Stagger"): the default share of the health that fills the bar, how long the creature is broken, and the damage it takes then.
STAGGER_PCT = 40
STAGGER_TICKS = 120
STAGGER_DAMAGE_PCT = 125
PARRY_COOLDOWN = 70
PARRY_STUN = 60
PARRY_IFRAMES = 20
# The companion (spec 10): it never comes farther than this from the player, and its body is this big.
COMPANION_LEASH = 8.0
COMPANION_RADIUS = 0.25
# Talents (spec 11, "Talents"): what each kind of talent multiplies.
TALENT_STATS = {"attack": ("atk", "matk"), "health": ("max_hp",), "mana": ("max_mp",), "defense": ("def", "mdef"), "magic": ("matk",),
                "critical": ("crit_chance_pm",), "speed": ("move_speed_x100",)}
COMPANION_BOND_STEP = 5   # kills of the companion for one more point of attack
COMPANION_BOND_MAX = 10   # the most the bond adds


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
        self.burn = self.burn_clock = self.chill = self.weaken = self.stun = 0  # ticks left; not saved
        self.stagger = self.broken = 0  # the stagger bar and the ticks left of being broken; not saved


class CombatSim:
    def __init__(self, scenario: dict) -> None:
        self.grid = mv.Grid(scenario["grid"])
        self.props = [tuple(p) for p in scenario["props"]]
        story_setup = scenario.get("story")
        if story_setup:
            self.props += [(n["pos"][0], n["pos"][1], NPC_RADIUS) for n in story_setup["npcs"]]
        seed = int(scenario["seed"], 16)
        self.seed = seed
        # Gathering (spec 06, "Gathering"): the nodes by prop art, the props that can be gathered from, and what is gathered: (x100, y100) -> (tick it grows back, times)
        self.gather_nodes = {n["prop"]: n for n in scenario.get("gather_nodes", [])}
        self.gather_props = [(g["art"], g["x"], g["y"], g["radius"]) for g in scenario.get("gather_props", [])]
        self.props += [(x, y, r) for _, x, y, r in self.gather_props]
        self.gathered: dict[tuple[int, int], tuple[int, int]] = {}
        self.world_ticks = 0
        self.companion = scenario.get("companion")  # the definition of the companion (spec 10), or None
        self.comp_x, self.comp_y = scenario["player"]["start"]
        self.comp_cooldown = self.companion["cooldown_ticks"] if self.companion else 0
        self.comp_stay = False  # told to stay where it is (spec 10, "Commands")
        self.comp_bond = 0      # the creatures it has killed (spec 10, "Bond")
        self.titles = scenario.get("titles", [])  # titles (spec 11)
        self.counters: dict[str, int] = {}  # gathered, crafted, parried (spec 11)
        self.bestiary: dict[str, int] = {}  # creature id -> how many were killed (spec 11)
        self.recipes = {r["id"]: r for r in scenario.get("recipes", [])}  # crafting (spec 06, "Crafting")
        self.combat = nm.derive_stream(seed, "combat")
        self.loot = nm.derive_stream(seed, "loot")
        pl = scenario["player"]
        self.base, self.growth = pl["base_stats"], pl["growth_pm"]
        self.weapon_atk, self.weapon_matk = pl["weapon_atk"], pl["weapon_matk"]
        self.xp_table = scenario["xp_table"]
        self.skill = scenario["skill"]
        self.strike = scenario.get("strike")  # the power strike: a skill dict like `skill` plus "mp"; None: none (spec 05, "Mana")
        self.cur_skill = self.skill  # the skill of the swing in progress
        self.talent_defs = scenario.get("talents", [])  # the talents that can be learned (spec 11, "Talents")
        self.talent_points_per_level = scenario.get("talent_points_per_level", 1)
        self.talents: dict[str, int] = {}  # talent id -> rank
        self.echo_pct = scenario.get("echo_pct", 0)  # +percent of the maximum health, from the profile (spec 11, "Echoes")
        self.gift = scenario.get("gift", {})  # percentages and the death save of the protagonist (spec 18, "Gift rules")
        self.death_save_cd = 0
        self.dodge = scenario.get("dodge")  # {"ticks", "speed_mult_x100", "iframes", "cooldown"}, or None: no dodge (spec 05, "Dodge roll")
        self.dodge_ticks = 0
        self.p_burn = self.p_burn_clock = self.p_chill = self.p_stun = self.p_weaken = 0  # status effects on the player (spec 05)
        self.dodge_cooldown = 0
        self.parry_ticks = 0
        self.parry_cooldown = 0
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
        derived = rules.derived_stats(self.level, primary, rules.Equipment(
            weapon_atk=weapon["atk"] if weapon else self.weapon_atk,
            weapon_matk=weapon["matk"] if weapon else self.weapon_matk,
            armor_def=armor["def"] if armor else 0,
            armor_mdef=armor["mdef"] if armor else 0))
        derived["max_hp"] = derived["max_hp"] * (100 + self.echo_pct) // 100  # the echoes of past games (spec 11)
        for talent in self.talent_defs:  # the talents, in the order of the data (spec 11, "Talents")
            rank = self.talents.get(talent["id"], 0)
            if rank > 0:
                for key in TALENT_STATS[talent["stat"]]:
                    derived[key] = derived[key] * (100 + talent["pct_per_rank"] * rank) // 100
        return derived

    def talent_points(self) -> int:
        """The talent points not spent yet: one share for every level gained, less the ranks learned."""
        return (self.level - 1) * self.talent_points_per_level - sum(self.talents.values())

    def learn_talent(self, talent_id: str) -> bool:
        """Spends one point on a rank of a talent (spec 11, "Talents"). Returns False, changing nothing, when it is refused."""
        if self.story is not None and self.story.dialogue_active:
            return False
        talent = next((t for t in self.talent_defs if t["id"] == talent_id), None)
        if talent is None or self.talent_points() < 1 or self.talents.get(talent_id, 0) >= talent["max_rank"]:
            return False
        need = talent.get("requires")  # a branch of the tree opens when the talent before it has the rank asked
        if need is not None and self.talents.get(need["talent"], 0) < need["rank"]:
            return False
        self.talents[talent_id] = self.talents.get(talent_id, 0) + 1
        self.derived = self._derive()
        self.hp = min(self.hp, self.derived["max_hp"])
        return True

    @property
    def speed(self) -> float:
        return self.derived["move_speed_x100"] / 100

    # --------------------------------------------------------------------------------- tick

    def tick(self, raw_x: float, raw_y: float, attack: bool, dodge: bool = False, strike: bool = False, parry: bool = False) -> None:
        self.world_ticks += 1
        if self.story is not None and self.story.dialogue_active:
            raw_x, raw_y, attack, dodge, strike, parry = 0.0, 0.0, False, False, False, False
        if self.iframes > 0:
            self.iframes -= 1
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= 1
        if self.parry_cooldown > 0:
            self.parry_cooldown -= 1
        if self.death_save_cd > 0:
            self.death_save_cd -= 1
        self.mp_u = min(self.derived["max_mp"] * 6000, self.mp_u + self.derived["mp_regen_x100"] * self.gift.get("mp_regen_pct", 100) // 100)

        if self.p_burn > 0:  # status effects on the player (spec 05, "Status effects on the player")
            self.p_burn -= 1
            self.p_burn_clock += 1
            if self.p_burn_clock % BURN_PERIOD == 0:
                self.hp = max(1, self.hp - max(1, self.derived["max_hp"] * PLAYER_BURN_PCT // 100))
        if self.p_stun > 0:
            self.p_stun -= 1
            attack = dodge = strike = parry = False

        if parry and self.parry_ticks == 0 and self.parry_cooldown == 0 and self.phase == NONE and self.dodge_ticks == 0:
            self.parry_ticks, self.parry_cooldown = PARRY_TICKS, PARRY_COOLDOWN
        if self.parry_ticks > 0:  # a parry in progress allows no attack and no roll
            attack = dodge = strike = False

        vx, vy = mv.normalize_input(raw_x, raw_y)
        if dodge and self.dodge is not None and self.dodge_ticks == 0 and self.dodge_cooldown == 0 and self.phase == NONE:
            dx, dy = (vx, vy) if (vx != 0.0 or vy != 0.0) else self.facing
            length = math.sqrt(dx * dx + dy * dy)
            self.dodge_dir = (dx / length, dy / length)
            self.facing = self.dodge_dir
            if self.dodge_dir[0] != 0.0:
                self.facing_left = self.dodge_dir[0] < 0.0
            self.dodge_ticks, self.dodge_cooldown = self.dodge["ticks"], self.dodge["cooldown"] * self.gift.get("dodge_cooldown_pct", 100) // 100
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
            if self.p_chill > 0:
                mult *= 0.5
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
        if self.companion is not None:
            self._update_companion()

        for index, enemy in enumerate(self.enemies):
            self._update_enemy(index, enemy)
        if self.parry_ticks > 0:
            self.parry_ticks -= 1
        if self.p_chill > 0:
            self.p_chill -= 1
        if self.p_weaken > 0:
            self.p_weaken -= 1

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

    def _update_companion(self) -> None:
        """The companion follows the player and hits the nearest creature in range now and then (spec 10)."""
        c = self.companion
        dx, dy = self.x - self.comp_x, self.y - self.comp_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > COMPANION_LEASH:
            self.comp_x, self.comp_y = self.x, self.y
            self.comp_stay = False  # too far: it comes back and follows again
        elif not self.comp_stay and dist > c["follow_x100"] / 100:
            step = min(c["speed_x100"] / 100 * mv.TICK_DT, dist - c["follow_x100"] / 100)
            self.comp_x += dx / dist * step
            self.comp_y += dy / dist * step
            self.comp_x, self.comp_y = mv.resolve(self.comp_x, self.comp_y, self.grid, self.props, COMPANION_RADIUS)
        if self.comp_cooldown > 0:
            self.comp_cooldown -= 1
        if self.comp_cooldown > 0:
            return
        target = None
        best = 0.0
        for enemy in self.enemies:
            if enemy.state == DEAD:
                continue
            d = math.sqrt((enemy.x - self.comp_x) ** 2 + (enemy.y - self.comp_y) ** 2)
            if d <= c["range_x100"] / 100 + enemy.radius and (target is None or d < best):
                target, best = enemy, d
        if target is None:
            return
        atk = c["atk_base"] + c["atk_per_level"] * (self.level - 1) + min(self.comp_bond // COMPANION_BOND_STEP, COMPANION_BOND_MAX)
        damage = rules.damage(atk, 100, target.d["def"], 1000, 0, self.level, target.d["level"], 1000, False, 1500, 1000)
        target.hp -= damage
        self.comp_cooldown = c["cooldown_ticks"]
        if target.hp <= 0:
            target.hp = 0
            target.state = DEAD
            self.comp_bond += 1
            self._on_kill(target)

    def companion_stay(self) -> bool:
        """Tells the companion to stay where it is, or to follow again (spec 10, "Commands"). False when there is no companion."""
        if self.companion is None:
            return False
        self.comp_stay = not self.comp_stay
        return True

    def _hit_element(self) -> str:
        """The element of the hit in progress (spec 05, "Elements"): the skill's own, or the weapon's when the skill has none."""
        element = self.cur_skill.get("element", "none")
        if element != "none":
            return element
        weapon = self.items.get(self.equipped["weapon"], {}).get("weapon") or {}
        return weapon.get("element", "none")

    def _apply_status(self, enemy: _Enemy) -> None:
        """The status effect of a hit of the equipped weapon (spec 05, "Status effects"): a roll for every hit of an element, unless the creature is immune to it."""
        element = self._hit_element()
        if element == "none" or self._elem_mult(enemy) == 0:
            return
        status, chance, ticks = STATUS_OF[element]
        if self.combat.next_bounded(1000) >= chance:
            return
        if status == "burn":
            enemy.burn, enemy.burn_clock = ticks, 0
        elif status == "chill":
            enemy.chill = ticks
        elif status == "stun":
            enemy.stun = ticks
        else:
            enemy.weaken = ticks

    def _elem_mult(self, enemy: _Enemy) -> int:
        """The element multiplier of a hit of the equipped weapon against an enemy (spec 05, "Elements")."""
        element = self._hit_element()
        if element == "none":
            return 1000
        weaknesses = enemy.d.get("weaknesses_pm", {})
        if element in weaknesses:
            return weaknesses[element]
        return 500 if enemy.d.get("element", "none") == element else 1000

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
            attack = self.derived["matk"] if s.get("kind") == "magical" else self.derived["atk"]
            attack = attack * (100 + self.title_attack_pct()) // 100  # the titles earned make the hits stronger (spec 11)
            if self.p_weaken > 0:
                attack = attack * 75 // 100
            damage = rules.damage(attack, s["power_pct"], enemy.d["def"], self._elem_mult(enemy), 0, self.level,
                                  enemy.d["level"], variance, crit, self.derived["crit_mult_pm"], 1000)
            if enemy.broken > 0:
                damage = damage * STAGGER_DAMAGE_PCT // 100
            enemy.hp -= damage
            if enemy.hp > 0:
                self._apply_status(enemy)
                pct = enemy.d.get("stagger_pct", STAGGER_PCT)
                if pct > 0 and enemy.broken == 0:  # the stagger bar (spec 05, "Stagger")
                    enemy.stagger += damage * (2 if self.strike is not None and s is self.strike else 1)
                    if enemy.stagger >= max(1, enemy.d["hp"] * pct // 100):
                        enemy.stagger, enemy.broken = 0, STAGGER_TICKS
                        enemy.stun = max(enemy.stun, STAGGER_TICKS)
            if enemy.hp <= 0:
                enemy.hp = 0
                enemy.state = DEAD
                self._on_kill(enemy)

    def earned_titles(self) -> list[str]:
        """The ids of the titles whose condition holds, in the order of the data (spec 11)."""
        done = sum(1 for q in self.story.quests.values() if q["done"]) if self.story is not None else 0
        out = []
        for t in self.titles:
            kind, count = t["kind"], t["count"]
            have = {"kills": self.kills, "kills_of": self.bestiary.get(t.get("enemy", ""), 0), "level": self.level,
                    "species": len(self.bestiary), "quests": done}.get(kind, self.counters.get(kind, 0))
            if have >= count:
                out.append(t["id"])
        return out

    def title_bonus(self, key: str) -> int:
        """What the earned titles add to gathering (`gather_bonus`, one more of every drop found) or to crafting (`craft_bonus`, one more of the
        output) (spec 11, "Titles with effects")."""
        earned = set(self.earned_titles())
        return sum(t.get(key, 0) for t in self.titles if t["id"] in earned)

    def title_attack_pct(self) -> int:
        """The percent that the earned titles add to the attack of the player's hits (spec 11, "Titles with effects")."""
        earned = set(self.earned_titles())
        return sum(t.get("atk_pct", 0) for t in self.titles if t["id"] in earned)

    def _on_kill(self, enemy: _Enemy) -> None:
        self.kills += 1
        if enemy.d.get("id", ""):
            self.bestiary[enemy.d["id"]] = self.bestiary.get(enemy.d["id"], 0) + 1
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
        if e.broken > 0:
            e.broken -= 1
        if e.burn > 0:  # a burn hurts every BURN_PERIOD ticks, whatever the defense
            e.burn -= 1
            e.burn_clock += 1
            if e.burn_clock % BURN_PERIOD == 0:
                e.hp -= max(1, e.d["hp"] * 3 // 100)
                if e.hp <= 0:
                    e.hp = 0
                    e.state = DEAD
                    self._on_kill(e)
                    return
        if e.stun > 0:  # a stunned creature does nothing
            e.stun -= 1
            return
        self._behave(e)
        if e.chill > 0:
            e.chill -= 1
        if e.weaken > 0:
            e.weaken -= 1

    def _behave(self, e: _Enemy) -> None:
        b = e.d["behavior"]
        dx, dy = self.x - e.x, self.y - e.y
        dist = math.sqrt(dx * dx + dy * dy)
        if e.state == IDLE:
            if dist <= b["aggro_x100"] * self.gift.get("aggro_pct", 100) // 100 / 100:
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
                e.stagger = 0
            else:
                self._move_enemy(e, hx, hy)

    def _move_enemy(self, e: _Enemy, tx: float, ty: float) -> None:
        dx, dy = tx - e.x, ty - e.y
        dist = math.sqrt(dx * dx + dy * dy)
        step = (e.speed / 2 if e.chill > 0 else e.speed) * mv.TICK_DT
        if dist > 0:
            if dist <= step:
                e.x, e.y = tx, ty
            else:
                e.x += dx / dist * step
                e.y += dy / dist * step
        e.x, e.y = mv.resolve(e.x, e.y, self.grid, self.props, e.radius)

    def _hurt_player(self, e: _Enemy) -> None:
        if self.parry_ticks > 0:  # parried: no damage, the attacker is stunned and the player is safe for a moment
            e.stun = PARRY_STUN
            self.counters["parried"] = self.counters.get("parried", 0) + 1
            self.iframes = max(self.iframes, PARRY_IFRAMES)
            return
        variance = 950 + self.combat.next_bounded(101)
        atk = e.d["atk"] * 75 // 100 if e.weaken > 0 else e.d["atk"]
        damage = rules.damage(atk, 100, self.derived["def"], 1000, 0, e.d["level"], self.level,
                              variance, False, 1500, 1000)
        self.hp -= damage
        self.iframes = PLAYER_HIT_IFRAMES
        if self.hp <= 0 and self.gift.get("death_save_ticks", 0) > 0 and self.death_save_cd == 0:
            self.hp, self.death_save_cd = 1, self.gift["death_save_ticks"]  # the death save (spec 18)
        if self.hp <= 0:
            self.deaths += 1
            self.hp = self.derived["max_hp"]
            self.x, self.y = self.spawn
            self.phase, self.phase_tick = NONE, 0
            self.dodge_ticks, self.dodge_cooldown = 0, 0
            self.parry_ticks = self.parry_cooldown = 0
            self.p_burn = self.p_burn_clock = self.p_chill = self.p_stun = self.p_weaken = 0
            self.mp_u = self.derived["max_mp"] * 6000
            self.iframes = RESPAWN_IFRAMES
            return
        element = e.d.get("element", "none")
        if element != "none":  # the status of the creature's element (spec 05, "Status effects on the player")
            status, chance, ticks = STATUS_OF[element]
            if self.combat.next_bounded(1000) < chance:
                if status == "burn":
                    self.p_burn, self.p_burn_clock = ticks, 0
                elif status == "chill":
                    self.p_chill = ticks
                elif status == "stun":
                    self.p_stun = ticks
                else:
                    self.p_weaken = ticks

    # ---------------------------------------------------------------------------------- saves

    def craft(self, recipe_id: str) -> bool:
        """Makes a recipe from the bag (spec 06, "Crafting"). Returns False, changing nothing, when it is refused."""
        if self.story is not None and self.story.dialogue_active:
            return False
        recipe = self.recipes.get(recipe_id)
        if recipe is None or any(self.inventory.get(i["item"], 0) < i["qty"] for i in recipe["inputs"]):
            return False
        for i in recipe["inputs"]:
            self.inventory[i["item"]] -= i["qty"]
            if self.inventory[i["item"]] == 0:
                del self.inventory[i["item"]]
        out = recipe["output"]
        self.inventory[out["item"]] = self.inventory.get(out["item"], 0) + out["qty"] + self.title_bonus("craft_bonus")  # the titles of an artisan
        self.counters["crafted"] = self.counters.get("crafted", 0) + 1
        return True

    def gather(self) -> list[tuple[str, int]] | None:
        """Gathers from the nearest prop that can be gathered from within reach (spec 06, "Gathering"). None: nothing to gather here, or it has not grown back;
        otherwise the items found (possibly none), which are added to the bag."""
        if self.story is not None and self.story.dialogue_active:
            return None
        best = None
        for art, x, y, radius in self.gather_props:
            node = self.gather_nodes.get(art)
            if node is None:
                continue
            dist = math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
            if dist > node["reach_x100"] / 100 + radius:
                continue
            key = (math.floor(x * 100 + 0.5), math.floor(y * 100 + 0.5))
            if key in self.gathered and self.world_ticks < self.gathered[key][0]:
                continue
            candidate = (dist, x, y, key, node)
            if best is None or candidate[:3] < best[:3]:
                best = candidate
        if best is None:
            return None
        _, _, _, key, node = best
        times = self.gathered.get(key, (0, 0))[1]
        h = nm.hash64(nm.fnv1a64(b"gather") ^ self.seed, key[0], key[1], times)
        found = []
        for i, drop in enumerate(node["drops"]):
            if nm.mix64((h + 2 * i) & 0xFFFFFFFFFFFFFFFF) % 1000 < drop["weight_pm"]:
                qty = drop["qty_min"] + nm.mix64((h + 2 * i + 1) & 0xFFFFFFFFFFFFFFFF) % (drop["qty_max"] - drop["qty_min"] + 1)
                qty += self.title_bonus("gather_bonus")  # the titles of a forager
                found.append((drop["item"], qty))
                self.inventory[drop["item"]] = self.inventory.get(drop["item"], 0) + qty
        self.gathered[key] = (self.world_ticks + node["cooldown_ticks"], times + 1)
        self.counters["gathered"] = self.counters.get("gathered", 0) + 1
        return found

    def use_item(self, item_id: str) -> bool:
        """Uses one item of the inventory (docs/spec/06-items.md). Returns False, changing nothing, when it is refused."""
        if self.story is not None and self.story.dialogue_active:
            return False
        item = self.items.get(item_id)
        if item is None or self.inventory.get(item_id, 0) < 1:
            return False
        heal = sum(e["amount"] for e in item["effects"] if e["effect"] == "heal") * self.gift.get("heal_pct", 100) // 100
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
            **({"bestiary": dict(sorted(self.bestiary.items()))} if self.bestiary else {}),
            **({"counters": dict(sorted(self.counters.items()))} if self.counters else {}),
            **({"talents": dict(sorted(self.talents.items()))} if self.talents else {}),
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
        self.parry_ticks = self.parry_cooldown = 0
        self.p_burn = self.p_burn_clock = self.p_chill = self.p_stun = self.p_weaken = 0
        self.death_save_cd = 0
        self.mp_u, self.cur_skill = self.derived["max_mp"] * 6000, self.skill  # nor is the mana: a loaded game starts full
        for name, stream in (("combat", self.combat), ("loot", self.loot)):
            stream.state = int(save["rng"][name]["state"], 16)
            stream.inc = int(save["rng"][name]["inc"], 16)
        for enemy, data in zip(self.enemies, save["enemies"]):
            enemy.x, enemy.y, enemy.hp, enemy.state, enemy.t = data["x"], data["y"], data["hp"], data["state"], data["state_tick"]
        self.inventory = dict(save["inventory"])
        self.equipped = {"weapon": "", "armor": "", **save.get("equipped", {})}
        self.bestiary = dict(save.get("bestiary", {}))
        self.counters = dict(save.get("counters", {}))
        self.talents = dict(save.get("talents", {}))
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
            **({"talents": dict(sorted(self.talents.items())), "talent_points": self.talent_points(), "max_hp": self.derived["max_hp"],
                "max_mp": self.derived["max_mp"], "matk": self.derived["matk"], "crit_chance_pm": self.derived["crit_chance_pm"],
                "move_speed_x100": self.derived["move_speed_x100"]} if self.talent_defs else {}),
            **({"companion": {"x": self.comp_x, "y": self.comp_y, "stay": self.comp_stay, "bond": self.comp_bond}} if self.companion is not None else {}),
            **({"bestiary": dict(sorted(self.bestiary.items())), "titles": self.earned_titles(),
                "counters": dict(sorted(self.counters.items()))} if self.titles else {}),
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
        if command["cmd"] == "talent":
            sim.learn_talent(command["talent"])
            continue
        if command["cmd"] == "companion_stay":
            sim.companion_stay()
            continue
        if command["cmd"] == "craft":
            sim.craft(command["recipe"])
            continue
        if command["cmd"] == "gather":
            sim.gather()
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
        sim.tick(move[0], move[1], segment["attack"], segment.get("dodge", False), segment.get("strike", False), segment.get("parry", False))


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
