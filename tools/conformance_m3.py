"""Conformance suite added in M3: combat scenarios. Imported by gen_conformance.py."""
from __future__ import annotations

from reference import combat, guild, rules, worldgen

SLIME = {
    "hp": 28, "atk": 6, "def": 2, "level": 1, "xp": 6, "radius_x100": 35, "speed_x100": 250,
    "drops": [{"item": "base:item/slime_gel", "qty_min": 1, "qty_max": 2, "weight_pm": 700}],
    "behavior": {"aggro_x100": 600, "leash_x100": 900, "attack_range_x100": 120, "hit_range_x100": 150,
                 "windup_ticks": 18, "recovery_ticks": 30},
}
SLASH = {"startup": 6, "active": 4, "recovery": 10, "cooldown": 24, "power_pct": 100, "radius_x100": 160,
         "angle_deg": 110}
DODGE = {"ticks": 12, "speed_mult_x100": 260, "iframes": 14, "cooldown": 40}  # base:skill/common/dodge (spec 05, "Dodge roll")
STRIKE = {"startup": 10, "active": 4, "recovery": 16, "cooldown": 90, "power_pct": 230, "radius_x100": 190, "angle_deg": 140,
          "mp": 10}  # base:skill/ren/power_strike (spec 05, "Mana")
MAGE = {"str": 3, "vit": 6, "dex": 6, "agi": 7, "int": 30, "wis": 20, "luk": 8}
PLAYER = {
    "start": [2.2, 4.5], "level": 1,
    "base_stats": {"str": 6, "vit": 7, "dex": 8, "agi": 8, "int": 7, "wis": 7, "luk": 9},
    "growth_pm": {"str": 1000, "vit": 1000, "dex": 1200, "agi": 1100, "int": 1000, "wis": 1000, "luk": 1300},
    "weapon_atk": 3, "weapon_matk": 0,
}


def arena(width: int = 14, height: int = 9) -> list[str]:
    rows = ["#" * width]
    rows += ["#" + "." * (width - 2) + "#" for _ in range(height - 2)]
    rows.append("#" * width)
    return rows


def enemy(x: float, y: float, **overrides) -> dict:
    definition = {**SLIME, **overrides}
    if "behavior_overrides" in overrides:
        definition["behavior"] = {**SLIME["behavior"], **overrides.pop("behavior_overrides")}
        definition.pop("behavior_overrides")
    return {"pos": [x, y], "def": definition}


ITEMS = {
    "base:item/bread": {"kind": "food", "price": 5, "effects": [{"effect": "heal", "amount": 30}]},
    "base:item/potion_mana_small": {"kind": "consumable", "price": 40, "effects": [{"effect": "restore_mp", "amount": 30}]},
    "base:item/slime_gel": {"kind": "material", "price": 3, "effects": []},
    "base:item/cleansing_draught": {"kind": "food", "price": 60, "effects": [{"effect": "cleanse"}]},
    "base:item/windleaf_brew": {"kind": "food", "price": 90, "effects": [{"effect": "haste", "amount": 50, "ticks": 90}]},
    "base:item/honey_cake": {"kind": "food", "price": 20, "effects": [{"effect": "regen", "amount": 6, "ticks": 600}]},
    "base:item/frost_tonic": {"kind": "food", "price": 160, "effects": [{"effect": "ward", "amount": 400, "ticks": 300}]},
    "base:item/roast_meat": {"kind": "food", "price": 30, "effects": [{"effect": "heal", "amount": 20}, {"effect": "fortify", "amount": 50, "ticks": 200}]},
    "base:item/practice_sword": {"kind": "weapon", "price": 20, "weapon": {"atk": 3, "matk": 0}},
    "base:item/iron_sword": {"kind": "weapon", "price": 150, "weapon": {"atk": 7, "matk": 0}},
    "base:item/ember_blade": {"kind": "weapon", "price": 400, "weapon": {"atk": 7, "matk": 0, "element": "fire"}},
    "base:item/frost_blade": {"kind": "weapon", "price": 400, "weapon": {"atk": 7, "matk": 0, "element": "water"}},
    "base:item/storm_blade": {"kind": "weapon", "price": 400, "weapon": {"atk": 7, "matk": 0, "element": "wind"}},
    "base:item/quake_hammer": {"kind": "weapon", "price": 400, "weapon": {"atk": 7, "matk": 0, "element": "earth"}},
    "base:item/sun_blade": {"kind": "weapon", "price": 400, "weapon": {"atk": 7, "matk": 0, "element": "light"}},
    "base:item/leather_vest": {"kind": "armor", "price": 80, "armor": {"def": 2, "mdef": 1}},
    "base:item/chain_mail": {"kind": "armor", "price": 300, "armor": {"def": 5, "mdef": 2}},
    "base:item/fang_necklace": {"kind": "accessory", "price": 200, "accessory": {"atk": 12, "max_hp": 40}},
    "base:item/bat_charm": {"kind": "accessory", "price": 200, "accessory": {"drain_pm": 300}},
}
BREAD = ITEMS
COMPANION = {"atk_base": 12, "atk_per_level": 1, "range_x100": 300, "cooldown_ticks": 60, "speed_x100": 320, "follow_x100": 220}
RECIPES = [
    {"id": "tonic", "output": {"item": "base:item/tonic", "qty": 2},
     "inputs": [{"item": "base:item/healing_herb", "qty": 1}, {"item": "base:item/wild_berries", "qty": 2}]},
    {"id": "potion_small", "output": {"item": "base:item/potion_small", "qty": 1},
     "inputs": [{"item": "base:item/healing_herb", "qty": 3}, {"item": "base:item/slime_gel", "qty": 1}]},
]
TITLES = [
    {"id": "grown", "name": "t", "kind": "level", "count": 2},
    {"id": "first_blood", "name": "t", "kind": "kills", "count": 1, "atk_pct": 20, "xp_pct": 50},
    {"id": "slime_hunter", "name": "t", "kind": "kills_of", "count": 2, "enemy": "base:enemy/slime_green", "atk_pct": 30},
    {"id": "wolf_bane", "name": "t", "kind": "kills_of", "count": 2, "enemy": "base:enemy/wolf_grey"},
    {"id": "naturalist", "name": "t", "kind": "species", "count": 2},
    {"id": "helper", "name": "t", "kind": "quests", "count": 1},
    {"id": "forager", "name": "t", "kind": "gathered", "count": 2, "gather_bonus": 1},
    {"id": "maker", "name": "t", "kind": "crafted", "count": 1, "craft_bonus": 2},
    {"id": "guard", "name": "t", "kind": "parried", "count": 1},
]
TALENTS = [
    {"id": "might", "name": "t", "stat": "attack", "pct_per_rank": 25, "max_rank": 2},
    {"id": "vigor", "name": "t", "stat": "health", "pct_per_rank": 10, "max_rank": 3},
    {"id": "focus", "name": "t", "stat": "mana", "pct_per_rank": 10, "max_rank": 3},
    {"id": "guard", "name": "t", "stat": "defense", "pct_per_rank": 50, "max_rank": 3},
]
TALENT_TREE = [
    {"id": "might", "name": "t", "stat": "attack", "pct_per_rank": 10, "max_rank": 3},
    {"id": "keen", "name": "t", "stat": "critical", "pct_per_rank": 50, "max_rank": 2, "requires": {"talent": "might", "rank": 2}},
    {"id": "swift", "name": "t", "stat": "speed", "pct_per_rank": 15, "max_rank": 2, "requires": {"talent": "might", "rank": 3}},
    {"id": "arcane", "name": "t", "stat": "magic", "pct_per_rank": 40, "max_rank": 2},
]
# Talents that are abilities (spec 11, "Abilities"): their percent is a power, not a stat.
ABILITIES = [
    {"id": "riposte", "name": "t", "stat": "riposte", "pct_per_rank": 150, "max_rank": 2},
    {"id": "second_wind", "name": "t", "stat": "kill_heal", "pct_per_rank": 10, "max_rank": 2},
    {"id": "flow", "name": "t", "stat": "kill_mana", "pct_per_rank": 30, "max_rank": 2},
    {"id": "whirl", "name": "t", "stat": "whirl", "pct_per_rank": 10, "max_rank": 2},
]
GATHER_NODES = [
    {"prop": "base:art/prop/bush", "sound": "plant", "cooldown_ticks": 60, "reach_x100": 150,
     "drops": [{"item": "base:item/wild_berries", "qty_min": 1, "qty_max": 3, "weight_pm": 800}, {"item": "base:item/healing_herb", "qty_min": 1, "qty_max": 2, "weight_pm": 400}]},
    {"prop": "base:art/prop/rock", "sound": "stone", "cooldown_ticks": 60, "reach_x100": 150,
     "drops": [{"item": "base:item/stone_chunk", "qty_min": 1, "qty_max": 2, "weight_pm": 1000}, {"item": "base:item/iron_ore", "qty_min": 1, "qty_max": 1, "weight_pm": 300}]},
]
GATHER_PROPS = [
    {"art": "base:art/prop/bush", "x": 3.0, "y": 4.5, "radius": 0.3},
    {"art": "base:art/prop/rock", "x": 2.5, "y": 5.5, "radius": 0.3},
    {"art": "base:art/prop/tree_oak", "x": 2.0, "y": 3.5, "radius": 0.3},
    {"art": "base:art/prop/bush", "x": 9.0, "y": 4.5, "radius": 0.3},
]
EMPTY_STORY = {"quests": {}, "dialogues": {}, "npcs": []}


def scenario(name: str, enemies: list[dict], script: list[dict], player: dict | None = None,
             seed: str = "0x0000000000C0FFEE", inventory: dict | None = None, skill: dict | None = None, **extra) -> dict:
    return {
        **extra,
        "name": name,
        "grid": arena(), "props": [], "seed": seed,
        "player": {**PLAYER, **(player or {})},
        "skill": skill or SLASH,
        "xp_table": rules.generate_xp_table()[:12],
        "enemies": enemies,
        "script": script,
        **({"inventory": inventory, "items": ITEMS} if inventory is not None else {}),
    }


def segment(ticks: int, move=(0, 0), attack=False, do=None, dodge=False, strike=False, parry=False) -> dict:
    result = {"ticks": ticks, "move": list(move), "attack": attack}
    if parry:
        result["parry"] = True
    if strike:
        result["strike"] = True
    if dodge:
        result["dodge"] = True
    if do:
        result["do"] = do
    return result


def board_quest() -> dict:
    """The quest of a kill offer of a real board (a settlement of the base world, day 1): spec 07, "Guild"."""
    params = worldgen.load_params()
    for site in worldgen.settlements_in(7, params, 0, 0, 63, 63):
        for offer in guild.offers_for(7, params, site, 1):
            if offer["type"] == "kill" and offer["count"] == 3:
                return guild.quest_def(offer)
    raise AssertionError("no kill offer of three")


def build_scenarios() -> list[dict]:
    passive = {"behavior_overrides": {"aggro_x100": 0}, "speed_x100": 0}
    quest = board_quest()
    target = quest["stages"][0]["objectives"][0]["enemy"]
    return [
        scenario("stationary_kill", [enemy(3.5, 4.5, **passive)], [segment(30, attack=True), segment(200, attack=True)]),
        scenario("miss_behind", [enemy(3.4, 4.5, **passive)], [segment(90, attack=True)], player={"start": [4.5, 4.5]}),
        scenario("chase_and_fight", [enemy(8.1, 4.5)], [segment(120, attack=True), segment(120, attack=True)]),
        scenario("chase_hurts_then_dies", [enemy(8.1, 4.5)], [segment(150), segment(150, attack=True)]),
        scenario("level_up", [enemy(3.5, 4.5, hp=5, xp=500, **passive), enemy(3.6, 4.7, hp=5, xp=500, **passive),
                              enemy(3.4, 4.3, hp=5, xp=500, **passive)],
                 [segment(40, attack=True)]),
        # Bestiary and titles (spec 11): every kill is counted by creature, and a title is earned when its condition holds.
        scenario("bestiary_titles", [enemy(3.5, 4.5, hp=5, id="base:enemy/slime_green", **passive),
                                     enemy(3.6, 4.7, hp=5, id="base:enemy/slime_green", **passive),
                                     enemy(3.4, 4.3, hp=5, id="base:enemy/wolf_grey", **passive),
                                     enemy(9.0, 7.0, hp=5, id="base:enemy/wolf_grey", **passive)],
                 [segment(1), segment(40, attack=True), segment(20)], titles=TITLES),
        # The counters of spec 11 (gathered, crafted, parried) and the titles of level: gathering twice, crafting twice (a refused recipe does not count),
        # parries against a slime that fights, and a level gained from three rich ones.
        scenario("counter_titles", [enemy(3.5, 4.5, hp=5, xp=500, id="base:enemy/slime_green", **passive),
                                    enemy(3.6, 4.7, hp=5, xp=500, id="base:enemy/slime_green", **passive),
                                    enemy(3.4, 4.3, hp=5, xp=500, id="base:enemy/slime_green", **passive),
                                    enemy(4.2, 4.5, atk=60)],
                 [segment(6), *[s for _ in range(3) for s in (segment(1, parry=True), segment(5), segment(12), segment(60))],
                  segment(1, do=[{"cmd": "gather"}]), segment(1, do=[{"cmd": "gather"}]), segment(1, do=[{"cmd": "gather"}]),
                  segment(1, do=[{"cmd": "craft", "recipe": "tonic"}, {"cmd": "craft", "recipe": "nothing"}]),
                  segment(1, do=[{"cmd": "craft", "recipe": "tonic"}]), segment(40, attack=True), segment(30), segment(1, do=[{"cmd": "gather"}]), segment(1, do=[{"cmd": "gather"}])],
                 inventory={"base:item/healing_herb": 4, "base:item/wild_berries": 4}, recipes=RECIPES, titles=TITLES,
                 gather_nodes=GATHER_NODES,
                 gather_props=[{"art": "base:art/prop/bush", "x": 3.0, "y": 6.0, "radius": 0.3}, {"art": "base:art/prop/rock", "x": 2.0, "y": 3.0, "radius": 0.3}]),
        # Status effects on the player (spec 05): a creature of an element that hits may burn (health goes down by itself, never to zero), chill (half speed),
        # stun (no attack, roll or parry) or weaken (softer hits); the player walks and fights through them.
        *[scenario(f"player_status_{element}", [enemy(4.2, 4.5, hp=600, atk=40, element=element)],
                   [segment(120), segment(90, move=(-1, 0)), segment(120, attack=True), segment(120, move=(0, 1), dodge=True), segment(150, attack=True),
                    segment(1, parry=True), segment(120, attack=True)])
          for element in ("fire", "water", "wind", "earth", "dark")],
        # Stagger (spec 05): hits fill the bar of a creature; when it is full the creature is broken for 120 ticks (stunned, and hits do a quarter more).
        # The power strike fills twice as much; a creature with `stagger_pct` 0 is never broken.
        scenario("stagger_breaks", [enemy(3.6, 4.5, hp=400, atk=30), enemy(3.4, 5.1, hp=400, atk=30, stagger_pct=0)],
                 [segment(120, attack=True), segment(120, attack=True), segment(120, attack=True), segment(120, attack=True), segment(120, attack=True)]),
        scenario("stagger_strike", [enemy(3.6, 4.5, hp=600, atk=30, stagger_pct=20)],
                 [segment(60, strike=True), segment(100, attack=True), segment(100, strike=True), segment(150, attack=True)], strike=STRIKE),
        # The element of a skill (spec 05): a power strike of fire is of fire whatever the weapon (here a blade of water), the plain slash keeps the element of the weapon.
        scenario("skill_element", [enemy(3.5, 4.5, hp=900, weaknesses_pm={"fire": 1500, "water": 500}, **passive),
                                   enemy(3.4, 4.9, hp=900, element="fire", **passive)],
                 [segment(1, do=[{"cmd": "equip", "item": "base:item/frost_blade"}]), segment(60, strike=True), segment(60, attack=True),
                  segment(100, strike=True), segment(150, attack=True)],
                 inventory={"base:item/frost_blade": 1}, strike={**STRIKE, "element": "fire"}),
        # Echoes (spec 11): the profile of past games adds a percent of maximum health from the start (here 10 percent, and with armor on top); it holds through a level up.
        scenario("echo_health", [enemy(3.5, 4.5, hp=5, xp=500, **passive), enemy(8.1, 4.5, atk=40)],
                 [segment(40, attack=True), segment(150), segment(1, do=[{"cmd": "equip", "item": "base:item/chain_mail"}]), segment(150)],
                 inventory={"base:item/chain_mail": 1}, echo_pct=10),
        # Titles with effects (spec 11): the first kill earns a title worth 20 percent of attack, the second slime one worth 30 more; the big slime
        # that is hit all along takes more with every title.
        scenario("title_attack", [enemy(3.5, 4.5, hp=5, id="base:enemy/slime_green", **passive), enemy(3.4, 4.9, hp=4000, **passive),
                                  enemy(3.4, 4.1, hp=70, id="base:enemy/slime_green", **passive)],
                 [segment(40, attack=True), segment(40, attack=True), segment(40, attack=True), segment(40, attack=True), segment(40, attack=True),
                  segment(40, attack=True)], titles=TITLES),
        # Talents (spec 11): a point for each level gained (two here). At level 1 nothing can be learned; three rich slimes give levels, then the points go to
        # might (two ranks, a third is refused), vigor, guard, focus, an unknown talent (refused), until none is left. A slime that fights shows the
        # defense, a big one the attack.
        scenario("talents_learned", [enemy(3.5, 4.5, hp=5, xp=500, **passive), enemy(3.6, 4.7, hp=5, xp=500, **passive), enemy(3.4, 4.3, hp=5, xp=500, **passive),
                                     enemy(3.4, 4.9, hp=6000, **passive), enemy(8.1, 4.5, hp=900, atk=60)],
                 [segment(1, do=[{"cmd": "talent", "talent": "might"}]), segment(40, attack=True), segment(60, attack=True),
                  segment(1, do=[{"cmd": "talent", "talent": "might"}, {"cmd": "talent", "talent": "might"}, {"cmd": "talent", "talent": "might"}]),
                  segment(60, attack=True),
                  segment(1, do=[{"cmd": "talent", "talent": "vigor"}, {"cmd": "talent", "talent": "guard"}, {"cmd": "talent", "talent": "focus"},
                                 {"cmd": "talent", "talent": "nothing"}, {"cmd": "talent", "talent": "guard"}]),
                  segment(120, attack=True), segment(1, do=[{"cmd": "talent", "talent": t} for t in ("vigor", "vigor", "guard", "focus", "focus", "vigor")]), segment(120)],
                 talents=TALENTS, talent_points_per_level=2),
        # The talent tree (spec 11): keen needs might at rank 2 and swift at rank 3; before that they are refused. Swift is seen in the walk, keen in the
        # critical hits on a big slime, arcane in the magic.
        scenario("talent_tree", [enemy(3.5, 4.5, hp=5, xp=500, **passive), enemy(3.6, 4.7, hp=5, xp=500, **passive), enemy(3.4, 4.3, hp=5, xp=500, **passive),
                                 enemy(5.5, 4.5, hp=9000, **passive)],
                 [segment(40, attack=True), segment(1, do=[{"cmd": "talent", "talent": t} for t in ("keen", "swift", "might", "keen", "might", "keen", "keen", "swift")]),
                  segment(30, move=(1, 0)), segment(240, attack=True),
                  segment(1, do=[{"cmd": "talent", "talent": t} for t in ("might", "swift", "swift", "arcane", "arcane", "arcane")]), segment(30, move=(1, 0))],
                 talents=TALENT_TREE, talent_points_per_level=3),
        # The parry of a guard (spec 11): once a parry earns the title, the window is 20 ticks wider, so the late parries after it still stop the blows.
        scenario("title_parry", [enemy(4.2, 4.5, atk=60)],
                 [segment(6), *[s for _ in range(6) for s in (segment(1, parry=True), segment(5, attack=True), segment(12), segment(60))], segment(7),
                  *[s for _ in range(4) for s in (segment(1, parry=True), segment(75))]],
                 titles=[{"id": "guard", "name": "t", "kind": "parried", "count": 1, "parry_bonus": 20}]),
        # Stations (spec 06): a stew needs a campfire within two tiles; far from it the recipe is refused, next to it it is made; a recipe with no station
        # is made anywhere.
        scenario("craft_at_fire", [enemy(12.0, 7.5, **passive)],
                 [segment(1, do=[{"cmd": "craft", "recipe": "stew"}, {"cmd": "craft", "recipe": "tonic"}]), segment(100, move=(1, 0)),
                  segment(1, do=[{"cmd": "craft", "recipe": "stew"}, {"cmd": "craft", "recipe": "stew"}])],
                 inventory={"base:item/healing_herb": 6, "base:item/wild_berries": 4, "base:item/spore_cap": 4, "base:item/dry_branch": 2},
                 recipes=RECIPES + [{"id": "stew", "output": {"item": "base:item/hearty_stew", "qty": 1}, "station": "base:art/prop/campfire",
                                     "inputs": [{"item": "base:item/spore_cap", "qty": 2}, {"item": "base:item/healing_herb", "qty": 1}, {"item": "base:item/dry_branch", "qty": 1}]}],
                 gather_nodes=GATHER_NODES, gather_props=[{"art": "base:art/prop/campfire", "x": 9.5, "y": 5.5, "radius": 0.3}]),
        scenario("player_death", [enemy(6.7, 4.5, atk=400)], [segment(100), segment(100), segment(100)]),
        # Hurt by a slime, the player eats bread: health goes up and one bread is gone. A second bread at full health is refused,
        # and so are the gel (no effect), an item that is not owned and a use while the player is hurt but the stack is empty.
        scenario("use_bread_heals", [enemy(8.1, 4.5, atk=40)],
                 [segment(150), segment(1, do=[{"cmd": "use", "item": "base:item/bread"}]),
                  segment(1, do=[{"cmd": "use", "item": "base:item/bread"}, {"cmd": "use", "item": "base:item/slime_gel"},
                                 {"cmd": "use", "item": "base:item/sword"}]),
                  segment(300, attack=True),
                  segment(1, do=[{"cmd": "use", "item": "base:item/bread"}, {"cmd": "use", "item": "base:item/bread"}])],
                 inventory={"base:item/bread": 3, "base:item/slime_gel": 2}),
        # Mana potions (spec 06): two power strikes cost twenty points, the potion gives them back (and a second one at full mana is refused).
        scenario("use_mana_potion", [enemy(3.5, 4.5, hp=400, **{"behavior_overrides": {"aggro_x100": 0}, "speed_x100": 0})],
                 [segment(1, do=[{"cmd": "use", "item": "base:item/potion_mana_small"}]), segment(60, strike=True),
                  segment(100, strike=True), segment(1, do=[{"cmd": "use", "item": "base:item/potion_mana_small"}]),
                  segment(1, do=[{"cmd": "use", "item": "base:item/potion_mana_small"}])],
                 inventory={"base:item/potion_mana_small": 3}, strike=STRIKE),
        scenario("use_refused_at_full_health", [enemy(12.0, 7.5, **passive)],
                 [segment(10, do=[{"cmd": "use", "item": "base:item/bread"}])],
                 inventory={"base:item/bread": 1}),
        # Equipment (spec 06): the iron sword hits harder, armor makes the slime's hits weaker; refused: not owned, not equipment, already worn.
        # Elements (spec 05): an ember blade (fire) hits a creature weak to fire harder, one of fire softer, a plain one as usual,
        # and one immune to it not at all (a hit always does at least 1).
        scenario("element_hits", [enemy(3.5, 4.5, hp=400, weaknesses_pm={"fire": 1500}, **passive),
                                  enemy(3.4, 4.1, hp=400, element="fire", **passive),
                                  enemy(3.4, 4.9, hp=400, **passive),
                                  enemy(3.7, 4.5, hp=400, weaknesses_pm={"fire": 0}, **passive)],
                 [segment(1, do=[{"cmd": "equip", "item": "base:item/ember_blade"}]), segment(40, attack=True)],
                 inventory={"base:item/ember_blade": 1}),
        # Status effects (spec 05): every element of a weapon has its own, rolled on each hit: fire burns, water chills, wind and earth stun,
        # light and dark weaken. A creature that fights back shows them in its health, its place and its state.
        *[scenario(f"status_{name}", [enemy(5.0, 4.5, hp=900, atk=30, weaknesses_pm={"wind": 1500} if name == "storm" else {})],
                   [segment(1, do=[{"cmd": "equip", "item": f"base:item/{blade}"}]), segment(150, attack=True), segment(150, attack=True),
                    segment(150, attack=True), segment(120)],
                   inventory={f"base:item/{blade}": 1})
          for name, blade in (("burn", "ember_blade"), ("chill", "frost_blade"), ("storm", "storm_blade"), ("quake", "quake_hammer"), ("weaken", "sun_blade"))],
        # The parry (spec 05): a window of 14 ticks in which an attack that lands does no damage and stuns the attacker for 60 ticks; a wait of 70 ticks
        # before the next one; no attack or roll while it lasts.
        scenario("parry_blocks_and_stuns", [enemy(4.2, 4.5, atk=60)],
                 [segment(6), *[s for _ in range(5) for s in (segment(1, parry=True), segment(5, attack=True), segment(12), segment(60))],
                  segment(60, attack=True), segment(120)]),
        scenario("parry_early_and_late", [enemy(4.2, 4.5, atk=60)],
                 [segment(30), segment(1, parry=True), segment(80), segment(1, parry=True), segment(1, parry=True), segment(100)]),
        # Gathering (spec 06): the nearest gatherable prop in reach gives its drops, rolled from the seed, the prop and how many times it was gathered;
        # it grows back after its cooldown; a prop out of reach or with no node gives nothing.
        scenario("gather_nodes", [enemy(12.0, 7.5, **passive)],
                 [segment(1, do=[{"cmd": "gather"}]), segment(1, do=[{"cmd": "gather"}]), segment(1, do=[{"cmd": "gather"}]),
                  segment(70), segment(1, do=[{"cmd": "gather"}]), segment(1, do=[{"cmd": "gather"}]),
                  segment(1, move=(1, 0), do=[]), segment(90, move=(1, 0)), segment(1, do=[{"cmd": "gather"}]), segment(130, move=(-1, 0)),
                  segment(1, do=[{"cmd": "gather"}]), segment(1, do=[{"cmd": "gather"}]), segment(70), segment(1, do=[{"cmd": "gather"}])],
                 inventory={}, gather_nodes=GATHER_NODES, gather_props=GATHER_PROPS),
        # Crafting (spec 06): the inputs leave the bag and the output arrives; a recipe that is missing something, that does not exist, or a second one
        # that the bag can no longer pay for is refused and changes nothing.
        scenario("craft_recipes", [enemy(12.0, 7.5, **passive)],
                 [segment(1, do=[{"cmd": "craft", "recipe": "tonic"}]), segment(1, do=[{"cmd": "craft", "recipe": "tonic"}]),
                  segment(1, do=[{"cmd": "craft", "recipe": "tonic"}]), segment(1, do=[{"cmd": "craft", "recipe": "potion_small"}]),
                  segment(1, do=[{"cmd": "craft", "recipe": "nothing"}]), segment(1, do=[{"cmd": "craft", "recipe": "potion_small"}])],
                 inventory={"base:item/healing_herb": 4, "base:item/wild_berries": 4, "base:item/slime_gel": 1}, recipes=RECIPES),
        # The companion (spec 10): it hits the nearest creature in range every cooldown, without the player doing anything, and follows the player when he walks away;
        # more than 8 tiles away it comes back at once.
        scenario("companion_fights", [enemy(5.0, 4.5, hp=60, **passive), enemy(5.4, 6.0, hp=60, **passive)],
                 [segment(70), segment(70), segment(70), segment(140)], companion=COMPANION),
        # Commands and bond (spec 10): told to stay, the companion does not follow (and still hits what comes in its range); told again, or left more than
        # 8 tiles behind, it follows. Every creature it kills is one of bond, and five of bond are one more point of attack.
        {**scenario("companion_stays", [enemy(10.5, 6.5, hp=30, **passive)],
                 [segment(1, do=[{"cmd": "companion_stay"}]), segment(90, move=(1, 0)), segment(1, do=[{"cmd": "companion_stay"}]), segment(90),
                  segment(1, do=[{"cmd": "companion_stay"}]), segment(240, move=(1, 0)), segment(60)], companion=COMPANION), "grid": arena(24, 9)},
        scenario("companion_bond", [enemy(3.0 + 0.3 * (i % 4), 3.9 + 0.4 * (i // 4), hp=8, **passive) for i in range(12)] + [enemy(4.6, 4.5, hp=200, **passive)],
                 [segment(200), segment(200), segment(200), segment(200), segment(200)], companion={**COMPANION, "cooldown_ticks": 12}),
        # Teamwork (spec 10): the companion goes first for the creature the player hit last, even when another is nearer to it.
        scenario("companion_teamwork", [enemy(3.6, 4.5, hp=400, **passive), enemy(1.6, 4.5, hp=400, **passive), enemy(2.2, 5.6, hp=400, **passive)],
                 [segment(30, attack=True), segment(120), segment(1, move=(-1, 0)), segment(40, attack=True), segment(120)], companion=COMPANION),
        # Care (spec 10): from `care_bond` kills on, every `care_ticks` the companion heals the player by `care_pct` of the health (at least 1, never above the
        # maximum, never a dead player). The wolf bites the player first; the companion kills the first slime, and the healing starts.
        scenario("companion_care", [enemy(4.6, 4.5, hp=10, **passive), enemy(7.43, 4.5, hp=900, atk=24)],
                 [segment(60), segment(120), segment(120), segment(120), segment(300)],
                 companion={**COMPANION, "care_bond": 1, "care_ticks": 50, "care_pct": 10}),
        # Fortify (spec 06): a meal with `fortify` can be eaten at full health; while it lasts the hits are `amount` percent stronger (added to the titles'), then it wears off.
        scenario("fortify_meal", [enemy(3.0, 4.5, hp=3000, **passive)],
                 [segment(40, attack=True), segment(1, do=[{"cmd": "use", "item": "base:item/roast_meat"}]), segment(60, attack=True),
                  segment(200), segment(60, attack=True), segment(1, do=[{"cmd": "use", "item": "base:item/roast_meat"}]), segment(1, do=[{"cmd": "use", "item": "base:item/roast_meat"}])],
                 inventory={"base:item/roast_meat": 2}),
        # Ward (spec 06): a brew with `ward` raises the defense against the creatures' hits by `amount` percent while it lasts, then it wears off.
        scenario("ward_brew", [enemy(3.0, 4.5, hp=5000, atk=40)],
                 [segment(1, do=[{"cmd": "use", "item": "base:item/frost_tonic"}]), segment(200), segment(200), segment(200)],
                 inventory={"base:item/frost_tonic": 1}),
        # Regen (spec 06): a dish with `regen` gives back `amount` health every second (60 ticks) while it lasts, never above the maximum.
        scenario("regen_cake", [enemy(3.0, 4.5, hp=200, atk=26)],
                 [segment(150, attack=True), segment(1, do=[{"cmd": "use", "item": "base:item/honey_cake"}]), segment(150, attack=True), segment(300), segment(300)],
                 inventory={"base:item/honey_cake": 1}),
        # Haste (spec 06): a brew with `haste` makes walking `amount` percent faster while it lasts; then the walk is as before.
        {**scenario("haste_brew", [enemy(2.0, 7.5, **passive)],
                    [segment(40, move=(1, 0)), segment(1, do=[{"cmd": "use", "item": "base:item/windleaf_brew"}]), segment(40, move=(1, 0)),
                     segment(60), segment(40, move=(1, 0))],
                    inventory={"base:item/windleaf_brew": 1}), "grid": arena(40, 9)},
        # An accessory (spec 06, "Equipment"): a third slot; its flat bonuses come last, after the weapon, the armor and the talents. Equipping it again
        # is refused, and it cannot be sold while it is the only one worn.
        scenario("accessory_worn", [enemy(3.0, 4.5, hp=3000, **passive)],
                 [segment(40, attack=True), segment(1, do=[{"cmd": "equip", "item": "base:item/fang_necklace"}, {"cmd": "equip", "item": "base:item/fang_necklace"}]),
                  segment(40, attack=True)],
                 inventory={"base:item/fang_necklace": 1}),
        # Cleanse (spec 06): a draught with `cleanse` ends burn, chill, stun and weaken at once; with none of them it is refused and kept.
        scenario("cleanse_draught", [enemy(4.2, 4.5, hp=900, atk=30, element="water")],
                 [segment(1, do=[{"cmd": "use", "item": "base:item/cleansing_draught"}]), segment(150), segment(1, do=[{"cmd": "use", "item": "base:item/cleansing_draught"}]),
                  segment(60, move=(-1, 0)), segment(100), segment(1, do=[{"cmd": "use", "item": "base:item/cleansing_draught"}]), segment(60, move=(-1, 0))],
                 inventory={"base:item/cleansing_draught": 3}),
        # Drain (spec 06, "Equipment"): an accessory with `drain_pm` gives back that share of the damage of every hit (at least 1) to a hurt player.
        scenario("accessory_drain", [enemy(3.0, 4.5, hp=900, atk=24)],
                 [segment(1, do=[{"cmd": "equip", "item": "base:item/bat_charm"}]), segment(200, attack=True), segment(200, attack=True)],
                 inventory={"base:item/bat_charm": 1}),
        scenario("companion_follows", [enemy(10.5, 4.5, hp=30, **passive)],
                 [segment(60, move=(1, 0)), segment(60, move=(1, 0)), segment(100), segment(60, move=(0, 1)), segment(100)], companion=COMPANION),
        scenario("equip_changes_stats", [enemy(8.1, 4.5, atk=40)],
                 [segment(200), segment(1, do=[{"cmd": "equip", "item": "base:item/iron_sword"},
                                               {"cmd": "equip", "item": "base:item/iron_sword"},
                                               {"cmd": "equip", "item": "base:item/steel_sword"},
                                               {"cmd": "equip", "item": "base:item/bread"},
                                               {"cmd": "equip", "item": "base:item/chain_mail"}]),
                  segment(120, attack=True), segment(120), segment(1, do=[{"cmd": "equip", "item": "base:item/practice_sword"}])],
                 inventory={"base:item/bread": 1, "base:item/practice_sword": 1, "base:item/iron_sword": 1,
                            "base:item/chain_mail": 1, "base:item/leather_vest": 1},
                 equipped={"weapon": "base:item/practice_sword"}),
        # Shops (spec 06): buying and selling need the shop to be open, the item in its stock and enough gold; prices follow the region.
        scenario("shop_buy_and_sell", [enemy(12.0, 7.5, **passive)],
                 [segment(1, do=[{"cmd": "buy", "item": "base:item/bread"}]),
                  segment(1, do=[{"cmd": "open_shop"}, {"cmd": "buy", "item": "base:item/bread"}, {"cmd": "buy", "item": "base:item/bread"},
                                 {"cmd": "buy", "item": "base:item/chain_mail"}, {"cmd": "buy", "item": "base:item/iron_sword"},
                                 {"cmd": "buy", "item": "base:item/iron_sword"}]),
                  segment(1, do=[{"cmd": "sell", "item": "base:item/practice_sword"}, {"cmd": "equip", "item": "base:item/iron_sword"},
                                 {"cmd": "sell", "item": "base:item/practice_sword"}, {"cmd": "sell", "item": "base:item/slime_gel"},
                                 {"cmd": "sell", "item": "base:item/slime_gel"}, {"cmd": "sell", "item": "base:item/slime_gel"},
                                 {"cmd": "sell", "item": "base:item/leather_vest"}]),
                  segment(1, do=[{"cmd": "close_shop"}, {"cmd": "sell", "item": "base:item/bread"}])],
                 inventory={"base:item/practice_sword": 1, "base:item/slime_gel": 2, "base:item/leather_vest": 1},
                 equipped={"weapon": "base:item/practice_sword"}, story=EMPTY_STORY, start_gold=200,
                 shop={"price_pm": 1200, "stock": ["base:item/bread", "base:item/iron_sword", "base:item/leather_vest"]}),
        # A generated board quest runs like any quest and its rewards include guild points (spec 07, "Guild").
        scenario("board_quest_rewards", [enemy(3.5, 4.5, id=target, **passive), enemy(3.6, 4.7, id=target, **passive),
                                         enemy(3.4, 4.3, id=target, **passive)],
                 [segment(1, do=[{"cmd": "start_quest", "quest": quest["id"]}]), segment(40, attack=True), segment(20)],
                 story={"quests": {quest["id"]: quest}, "dialogues": {}, "npcs": []}, titles=TITLES),
        # The dodge roll (spec 05): a roll of 12 ticks at 2.6 times the speed in the direction of the input, a cooldown that refuses the second
        # roll, then a third one (down) once the cooldown has run out; the roll is the same without input (the facing); against a wall it stops at the wall.
        scenario("dodge_roll", [enemy(12.0, 7.5, **passive)],
                 [segment(5, move=(1, 0)), segment(1, move=(1, 0), dodge=True), segment(20), segment(1, move=(0, 1), dodge=True),
                  segment(30), segment(1, move=(0, 1), dodge=True), segment(45), segment(1, dodge=True), segment(30)],
                 dodge=DODGE),
        # Held down, the dodge starts again every time the cooldown ends (every 40 ticks), also against the east wall.
        scenario("dodge_cooldown", [enemy(12.0, 7.5, **passive)], [segment(130, move=(1, 0), dodge=True)], dodge=DODGE),
        # The slime of "chase_hurts_then_dies" lands its first blow at about tick 90 and the roll started at tick 75 is in the air: no damage
        # for 14 ticks of invulnerability; the same moment without the skill (the dodge input is ignored) costs health.
        scenario("dodge_iframes", [enemy(8.1, 4.5)],
                 [segment(75), segment(1, move=(-1, 0), dodge=True), segment(60), segment(60)], dodge=DODGE),
        scenario("dodge_without_skill", [enemy(8.1, 4.5)],
                 [segment(75), segment(1, move=(-1, 0), dodge=True), segment(60), segment(60)]),
        # Attack and dodge together: the dodge wins; an attack in the middle of a swing blocks the dodge.
        scenario("dodge_and_attack", [enemy(3.5, 4.5, **passive)],
                 [segment(3, attack=True), segment(1, move=(0, 1), attack=True, dodge=True), segment(40, attack=True),
                  segment(1, move=(0, -1), attack=True, dodge=True), segment(20)], dodge=DODGE),
        # The power strike (spec 05, "Mana"): it hits harder than the slash on a tough passive target, a second strike while the cooldown runs is refused
        # (and the attack input of the same tick takes over), and the same moments without the skill only slash.
        scenario("power_strike", [enemy(3.5, 4.5, hp=400, **passive)],
                 [segment(40, strike=True), segment(100, strike=True), segment(100, attack=True)], strike=STRIKE),
        scenario("power_strike_without_skill", [enemy(3.5, 4.5, hp=400, **passive)],
                 [segment(40, strike=True), segment(100, strike=True), segment(100, attack=True)]),
        # Too little mana: the first strike costs 60 of the hundred points, the second is refused and the attack input of the same tick slashes instead.
        scenario("strike_without_mana", [enemy(3.5, 4.5, hp=400, **passive)],
                 [segment(40, strike=True), segment(120, strike=True, attack=True), segment(120, strike=True, attack=True)],
                 strike={**STRIKE, "mp": 60}),
        # Both inputs at once: the strike wins.
        scenario("strike_wins_over_attack", [enemy(3.5, 4.5, hp=400, **passive)], [segment(60, strike=True, attack=True)], strike=STRIKE),
        # Damage kind (spec 05): a mage (intelligence 30, wisdom 20) hits with MATK when the skill is magical and with ATK when it is not.
        scenario("magical_attack", [enemy(3.5, 4.5, hp=400, **passive)], [segment(60, attack=True), segment(60, attack=True)],
                 player={"base_stats": MAGE}, skill={**SLASH, "kind": "magical"}),
        scenario("physical_attack_of_a_mage", [enemy(3.5, 4.5, hp=400, **passive)], [segment(60, attack=True), segment(60, attack=True)],
                 player={"base_stats": MAGE}),
        scenario("magical_strike", [enemy(3.5, 4.5, hp=400, **passive)], [segment(60, strike=True), segment(100, strike=True)],
                 player={"base_stats": MAGE, "weapon_matk": 6}, strike={**STRIKE, "kind": "magical", "mp": 6}),
        # Gift rules (spec 18): each knob against the same script without it.
        scenario("gift_death_save", [enemy(6.7, 4.5, atk=400)], [segment(100), segment(100), segment(100), segment(200)],
                 gift={"death_save_ticks": 150}),
        scenario("gift_mp_regen", [enemy(3.5, 4.5, hp=900, **passive)], [segment(40, strike=True), segment(200, strike=True), segment(200, strike=True)],
                 strike={**STRIKE, "mp": 60}, gift={"mp_regen_pct": 1000}),
        scenario("gift_heal", [enemy(8.1, 4.5, atk=40)],
                 [segment(150), segment(1, do=[{"cmd": "use", "item": "base:item/bread"}]), segment(10)],
                 inventory={"base:item/bread": 2}, gift={"heal_pct": 200}),
        scenario("gift_aggro", [enemy(6.2, 4.5)], [segment(200)], gift={"aggro_pct": 50}),
        # the rain hides the player (spec 08): at 5.3 tiles a slime notices in fair weather and in light rain (5.46), not in full rain (6 * 0.7 = 4.2)
        scenario("rain_hides", [enemy(7.5, 4.5)], [segment(120)], weather={"rain_pm": 1000, "rain_aggro_cut_pm": 300}),
        scenario("rain_light", [enemy(7.5, 4.5)], [segment(120)], weather={"rain_pm": 300, "rain_aggro_cut_pm": 300}),
        # the night hides the player too (spec 08): at light 180 a cut of 250 leaves 795 permille (4.77 tiles)
        scenario("night_hides", [enemy(7.5, 4.5)], [segment(120)], weather={"light_pm": 180, "night_aggro_cut_pm": 250}),
        scenario("night_dusk", [enemy(7.5, 4.5)], [segment(120)], weather={"light_pm": 700, "night_aggro_cut_pm": 250}),
        scenario("night_and_rain", [enemy(5.6, 4.5)], [segment(120)],
                 weather={"rain_pm": 1000, "rain_aggro_cut_pm": 300, "light_pm": 180, "night_aggro_cut_pm": 250}),
        scenario("rain_and_gift", [enemy(4.9, 4.5)], [segment(120)], gift={"aggro_pct": 50}, weather={"rain_pm": 1000, "rain_aggro_cut_pm": 300}),
        scenario("gift_dodge_cooldown", [enemy(12.0, 7.5, **passive)], [segment(70, move=(1, 0), dodge=True)], dodge=DODGE,
                 gift={"dodge_cooldown_pct": 50}),
        # Quality (spec 06): a recipe with `fine_pm` rolls from the seed and the number of things made; a fine tonic is one more tonic, a fine sword is
        # the fine sword instead of the plain one. After three things made the title adds 400 permille to the chance. A recipe without `fine_pm` never rolls.
        scenario("craft_quality", [enemy(12.0, 7.5, **passive)],
                 [segment(1, do=[{"cmd": "craft", "recipe": name}]) for name in
                  ("tonic_q", "sword_q", "tonic", "tonic_q", "sword_q", "tonic_q", "sword_q", "tonic_q", "sword_q", "tonic_q", "sword_q", "tonic_q")],
                 inventory={"base:item/healing_herb": 12, "base:item/wild_berries": 24, "base:item/slime_gel": 9},
                 recipes=RECIPES + [
                     {"id": "tonic_q", "output": {"item": "base:item/tonic", "qty": 2}, "fine_pm": 400,
                      "inputs": [{"item": "base:item/healing_herb", "qty": 1}, {"item": "base:item/wild_berries", "qty": 2}]},
                     {"id": "sword_q", "output": {"item": "base:item/iron_sword", "qty": 1}, "fine_pm": 400, "fine_item": "base:item/fine_iron_sword",
                      "inputs": [{"item": "base:item/slime_gel", "qty": 1}]}],
                 titles=[{"id": "maker", "name": "t", "kind": "crafted", "count": 3, "fine_pm": 400},
                         {"id": "master", "name": "t", "kind": "crafted_fine", "count": 2}]),
        # Recall (spec 10, "Commands"): told to stay, the companion is left five tiles behind; called back it is next to the player at once and follows again.
        # Without a companion the command does nothing.
        {**scenario("companion_recall", [enemy(20.5, 6.5, hp=30, **passive)],
                    [segment(1, do=[{"cmd": "companion_stay"}]), segment(75, move=(1, 0)), segment(1, do=[{"cmd": "companion_recall"}]),
                     segment(60, move=(1, 0)), segment(30)], companion=COMPANION), "grid": arena(24, 9)},
        scenario("companion_recall_without", [enemy(12.0, 7.5, **passive)], [segment(1, do=[{"cmd": "companion_recall"}]), segment(10)]),
        # Abilities of the talents (spec 11): riposte, a parry hits the attacker back with the attack times the power of the talent, with no roll, and
        # can kill it; before the talent the same parry only stuns.
        scenario("talent_riposte", [enemy(4.2, 4.5, atk=60, hp=150)],
                 [segment(6), segment(1, parry=True), segment(77), segment(1, do=[{"cmd": "talent", "talent": "riposte"}, {"cmd": "talent", "talent": "riposte"}]),
                  *[s for _ in range(5) for s in (segment(1, parry=True), segment(77))]],
                 player={"level": 3}, talents=ABILITIES, talent_points_per_level=2),
        # A kill gives back health and mana: the slime bites, then the strikes kill it and the next one; with the talents the health comes back at each kill
        # and the mana lets the second strike (60 of 100 points) start as soon as its cooldown ends.
        *[scenario(name, [enemy(8.1, 4.5, atk=40, hp=20), enemy(3.4, 5.4, hp=20, **passive), enemy(3.4, 3.6, hp=900, **passive)],
                   [segment(150), segment(1, do=[{"cmd": "talent", "talent": t} for t in learned]), segment(100, strike=True), segment(100, strike=True),
                    segment(100, strike=True)],
                   player={"level": 3}, talents=ABILITIES, talent_points_per_level=2, strike={**STRIKE, "mp": 60})
          for name, learned in (("talent_kill_gifts", ("second_wind", "second_wind", "flow", "flow")), ("talent_kill_gifts_without", ()))],
        # Whirl: the power strike hits all around and farther; the creature behind the player and the one just out of reach are hit only with the talent.
        scenario("talent_whirl", [enemy(3.5, 4.5, hp=900, **passive), enemy(1.5, 4.5, hp=900, **passive), enemy(4.7, 4.5, hp=900, **passive)],
                 [segment(40, strike=True), segment(60), segment(1, do=[{"cmd": "talent", "talent": "whirl"}, {"cmd": "talent", "talent": "whirl"}]),
                  segment(40, strike=True), segment(100, attack=True)],
                 player={"level": 3}, talents=ABILITIES, talent_points_per_level=2, strike=STRIKE),
        # Renown (spec 07): every quest finished adds one to the renown of the region; the shop takes `renown_step_pm` off its prices for each, up to
        # `renown_max_pm`. Bread costs 6, then 5 (one quest, 50 permille), an iron sword 158 (three quests, the cap of 120 permille), and selling does
        # not change. The counter of the region earns a title.
        scenario("renown_prices", [enemy(12.0, 7.5, **passive)],
                 [segment(1, do=[{"cmd": "open_shop"}, {"cmd": "buy", "item": "base:item/bread"}]),
                  segment(1, do=[{"cmd": "start_quest", "quest": "test:quest/a"}, {"cmd": "buy", "item": "base:item/bread"}]),
                  segment(1, do=[{"cmd": "start_quest", "quest": "test:quest/b"}, {"cmd": "start_quest", "quest": "test:quest/c"},
                                 {"cmd": "buy", "item": "base:item/iron_sword"}, {"cmd": "sell", "item": "base:item/slime_gel"}]),
                  segment(1, do=[{"cmd": "start_quest", "quest": "test:quest/d"}, {"cmd": "buy", "item": "base:item/bread"}])],
                 inventory={"base:item/slime_gel": 2}, start_gold=400, region="vale",
                 story={"quests": {f"test:quest/{q}": {"id": f"test:quest/{q}", "stages": [
                     {"id": "have", "journal": "q", "objectives": [{"type": "collect", "item": "base:item/slime_gel", "count": 1}], "next": "end"}],
                     "rewards": []} for q in "abcd"}, "dialogues": {}, "npcs": []},
                 shop={"price_pm": 1200, "stock": ["base:item/bread", "base:item/iron_sword"], "renown_step_pm": 50, "renown_max_pm": 120},
                 titles=[{"id": "known", "name": "t", "kind": "renown:vale", "count": 2}]),
        # The `renown_at_least` condition: the elder greets a stranger, and then somebody known, after two quests.
        scenario("renown_dialogue", [enemy(12.0, 7.5, **passive)],
                 [segment(1, do=[{"cmd": "interact"}]), segment(1, do=[{"cmd": "advance"}]),
                  segment(1, do=[{"cmd": "start_quest", "quest": "test:quest/a"}, {"cmd": "interact"}]), segment(1, do=[{"cmd": "advance"}]),
                  segment(1, do=[{"cmd": "start_quest", "quest": "test:quest/b"}, {"cmd": "interact"}]), segment(1, do=[{"cmd": "advance"}])],
                 inventory={"base:item/slime_gel": 1}, player={"start": [3.4, 4.5]},
                 story={"quests": {f"test:quest/{q}": {"id": f"test:quest/{q}", "stages": [
                     {"id": "have", "journal": "q", "objectives": [{"type": "collect", "item": "base:item/slime_gel", "count": 1}], "next": "end"}],
                     "rewards": []} for q in "ab"},
                     "dialogues": {"test:dialogue/elder": {"id": "test:dialogue/elder", "start": "start", "nodes": {
                         "start": {"type": "condition", "when": {"renown_at_least": 2}, "then": "known", "else": "stranger"},
                         "known": {"type": "say", "speaker": "elder", "text": "t.known", "next": "end"},
                         "stranger": {"type": "say", "speaker": "elder", "text": "t.stranger", "next": "end"}}}},
                     "npcs": [{"key": "elder", "pos": [4.0, 4.5], "dialogue": "test:dialogue/elder"}]}),
        scenario("leash_and_return", [enemy(4.0, 4.5, behavior_overrides={"leash_x100": 300})],
                 [segment(20, attack=True), segment(150, move=(1, 0)), segment(250)]),
    ]


def suite_combat() -> list[dict]:
    cases = []
    for sc in build_scenarios():
        checkpoints = combat.run_scenario(sc)
        name = sc.pop("name")
        cases.append({"name": f"combat_{name}", "input": {"op": "combat", **sc},
                      "expect": {"checkpoints": checkpoints, "tol": 0.02}})
    return cases
