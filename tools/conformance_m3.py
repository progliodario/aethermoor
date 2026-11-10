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
    "base:item/practice_sword": {"kind": "weapon", "price": 20, "weapon": {"atk": 3, "matk": 0}},
    "base:item/iron_sword": {"kind": "weapon", "price": 150, "weapon": {"atk": 7, "matk": 0}},
    "base:item/ember_blade": {"kind": "weapon", "price": 400, "weapon": {"atk": 7, "matk": 0, "element": "fire"}},
    "base:item/frost_blade": {"kind": "weapon", "price": 400, "weapon": {"atk": 7, "matk": 0, "element": "water"}},
    "base:item/storm_blade": {"kind": "weapon", "price": 400, "weapon": {"atk": 7, "matk": 0, "element": "wind"}},
    "base:item/quake_hammer": {"kind": "weapon", "price": 400, "weapon": {"atk": 7, "matk": 0, "element": "earth"}},
    "base:item/sun_blade": {"kind": "weapon", "price": 400, "weapon": {"atk": 7, "matk": 0, "element": "light"}},
    "base:item/leather_vest": {"kind": "armor", "price": 80, "armor": {"def": 2, "mdef": 1}},
    "base:item/chain_mail": {"kind": "armor", "price": 300, "armor": {"def": 5, "mdef": 2}},
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
    {"id": "first_blood", "name": "t", "kind": "kills", "count": 1, "atk_pct": 20},
    {"id": "slime_hunter", "name": "t", "kind": "kills_of", "count": 2, "enemy": "base:enemy/slime_green", "atk_pct": 30},
    {"id": "wolf_bane", "name": "t", "kind": "kills_of", "count": 2, "enemy": "base:enemy/wolf_grey"},
    {"id": "naturalist", "name": "t", "kind": "species", "count": 2},
    {"id": "helper", "name": "t", "kind": "quests", "count": 1},
    {"id": "forager", "name": "t", "kind": "gathered", "count": 2},
    {"id": "maker", "name": "t", "kind": "crafted", "count": 2},
    {"id": "guard", "name": "t", "kind": "parried", "count": 1},
]
TALENTS = [
    {"id": "might", "name": "t", "stat": "attack", "pct_per_rank": 25, "max_rank": 2},
    {"id": "vigor", "name": "t", "stat": "health", "pct_per_rank": 10, "max_rank": 3},
    {"id": "focus", "name": "t", "stat": "mana", "pct_per_rank": 10, "max_rank": 3},
    {"id": "guard", "name": "t", "stat": "defense", "pct_per_rank": 50, "max_rank": 3},
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
                  segment(1, do=[{"cmd": "craft", "recipe": "tonic"}]), segment(40, attack=True), segment(30)],
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
        scenario("gift_dodge_cooldown", [enemy(12.0, 7.5, **passive)], [segment(70, move=(1, 0), dodge=True)], dodge=DODGE,
                 gift={"dodge_cooldown_pct": 50}),
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
