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
    "base:item/leather_vest": {"kind": "armor", "price": 80, "armor": {"def": 2, "mdef": 1}},
    "base:item/chain_mail": {"kind": "armor", "price": 300, "armor": {"def": 5, "mdef": 2}},
}
BREAD = ITEMS
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


def segment(ticks: int, move=(0, 0), attack=False, do=None, dodge=False, strike=False) -> dict:
    result = {"ticks": ticks, "move": list(move), "attack": attack}
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
                 story={"quests": {quest["id"]: quest}, "dialogues": {}, "npcs": []}),
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
