"""Conformance suite added in M4: story scenarios (quests, dialogue, conditions, effects). Same runner as `combat`."""
from __future__ import annotations

from conformance_m3 import ROLLED_ITEMS, enemy, scenario, segment
from reference import combat

SLIME_ID = "base:enemy/slime_green"
WOLF_ID = "base:enemy/wolf_grey"

SLIME_QUEST = {
    "id": "test:quest/slimes",
    "stages": [
        {"id": "kill", "journal": "q.kill", "objectives": [{"type": "kill", "enemy": SLIME_ID, "count": 2}],
         "next": "report"},
        {"id": "report", "journal": "q.report", "objectives": [{"type": "talk", "npc_key": "clerk"}], "next": "end"},
    ],
    "rewards": [{"effect": "add_xp", "amount": 40}, {"effect": "add_gold", "amount": 120}],
}
GEL_QUEST = {
    "id": "test:quest/gel",
    "stages": [
        {"id": "collect", "journal": "q.collect",
         "objectives": [{"type": "collect", "item": "base:item/slime_gel", "count": 2}], "next": "end"},
    ],
    "rewards": [{"effect": "add_xp", "amount": 100}],
}
CLERK_DIALOGUE = {
    "id": "test:dialogue/clerk",
    "start": "start",
    "nodes": {
        "start": {"type": "condition", "when": {"quest_done": "test:quest/slimes"}, "then": "thanks", "else": "active_check"},
        "active_check": {"type": "condition", "when": {"quest_active": "test:quest/slimes"}, "then": "busy",
                         "else": "offer"},
        "offer": {"type": "say", "speaker": "clerk", "text": "t.offer", "next": "offer_choice"},
        "offer_choice": {"type": "choice", "choices": [
            {"text": "c.accept", "effects": [{"effect": "start_quest", "quest": "test:quest/slimes"}],
             "next": "accepted"},
            {"text": "c.decline", "next": "end"}]},
        "accepted": {"type": "say", "speaker": "clerk", "text": "t.accepted", "next": "end"},
        "busy": {"type": "say", "speaker": "clerk", "text": "t.busy", "next": "end"},
        "thanks": {"type": "say", "speaker": "clerk", "text": "t.thanks", "next": "end"},
    },
}
TRADER_DIALOGUE = {
    "id": "test:dialogue/trader",
    "start": "start",
    "nodes": {
        "start": {"type": "condition", "when": {"flag": "seen"}, "then": "return_visit", "else": "greet"},
        "greet": {"type": "say", "speaker": "trader", "text": "t.greet", "next": "menu"},
        "menu": {"type": "choice", "choices": [
            {"text": "c.start", "when": {"not": {"flag": "seen"}},
             "effects": [{"effect": "set_flag", "flag": "seen", "value": True},
                         {"effect": "start_quest", "quest": "test:quest/gel"}], "next": "after"},
            {"text": "c.hidden", "when": {"flag": "seen"}, "next": "end"},
            {"text": "c.gift", "next": "gift"},
            {"text": "c.barter", "when": {"has_item": {"item": "base:item/slime_gel", "qty": 2}}, "next": "barter"},
            {"text": "c.rest", "when": {"gold_at_least": 5}, "next": "rest"}]},
        "rest": {"type": "effects", "effects": [{"effect": "spend_gold", "amount": 5}, {"effect": "heal_full"}], "next": "after"},
        "barter": {"type": "effects", "effects": [{"effect": "remove_item", "item": "base:item/slime_gel", "qty": 2},
                                                  {"effect": "add_gold", "amount": 7}], "next": "after"},
        "gift": {"type": "effects", "effects": [{"effect": "add_item", "item": "base:item/slime_gel", "qty": 2}],
                 "next": "after"},
        "after": {"type": "say", "speaker": "trader", "text": "t.after", "next": "mark"},
        "mark": {"type": "set_flag", "flag": "visited", "value": True, "next": "end"},
        "return_visit": {"type": "say", "speaker": "trader", "text": "t.return", "next": "end"},
    },
}


def story(*npcs) -> dict:
    return {"quests": {q["id"]: q for q in (SLIME_QUEST, GEL_QUEST)},
            "dialogues": {d["id"]: d for d in (CLERK_DIALOGUE, TRADER_DIALOGUE)},
            "npcs": list(npcs)}


CLERK = {"key": "clerk", "pos": [4.0, 4.5], "dialogue": "test:dialogue/clerk"}
TRADER = {"key": "trader", "pos": [4.0, 6.5], "dialogue": "test:dialogue/trader"}


def do(*commands, ticks: int = 0, move=(0, 0), attack=False) -> dict:
    return {**segment(ticks, move=move, attack=attack), "do": list(commands)}


def with_story(sc: dict, extra_enemy_id: bool = True) -> dict:
    sc["story"] = story(CLERK, TRADER)
    for e in sc["enemies"]:
        e["def"]["id"] = SLIME_ID
    return sc


def build_scenarios() -> list[dict]:
    passive = {"behavior_overrides": {"aggro_x100": 0}, "speed_x100": 0}
    interact, advance = {"cmd": "interact"}, {"cmd": "advance"}

    def choose(i):
        return {"cmd": "choose", "index": i}

    flow = scenario(
        "clerk_quest",
        [enemy(4.9, 4.5, hp=5, **passive), enemy(4.9, 4.8, hp=5, **passive)],
        [segment(20, move=(1, 0)), do(interact), do(advance), do(choose(0)), do(advance),
         segment(120, attack=True), do(interact), do(advance)])
    decline = scenario(
        "decline_then_busy",
        [], [segment(20, move=(1, 0)), do(interact), do(advance), do(choose(1)), do(interact), do(advance),
             do(choose(0)), do(advance), do(interact), do(advance)])
    frozen = scenario(
        "dialogue_freezes_player",
        [enemy(3.7, 4.5, **passive)],
        [segment(20, move=(1, 0)), do(interact), segment(60, move=(1, 0), attack=True), do(advance)])
    trader = scenario(
        "trader_conditions_and_effects",
        [], [do(interact), do(advance), do(choose(1)), do(advance), do(interact), do(advance), do(choose(0)),
             do(interact), do(advance)],
        player={"start": [3.4, 5.6]})
    barter = scenario(
        "trader_barter",
        [], [do(interact), do(advance), do(choose(1)), do(advance), do(interact), do(advance), do(choose(2)), do(advance),
             do(interact), do(advance), do(choose(1)), do(advance), do(interact), do(advance), do(choose(2)), do(advance)],
        player={"start": [3.4, 5.6]})
    rest = scenario(
        "trader_inn",
        [enemy(3.8, 5.6, hp=40)],
        [segment(30), do(interact), do(advance), do(choose(1)), do(advance), do(interact), do(advance), do(choose(2)), do(advance),
         do(interact), do(advance), do(choose(2)), do(advance)],
        player={"start": [3.4, 5.6]})
    for sc in (flow, decline, frozen, trader, barter, rest):
        with_story(sc)
    # Residents (spec 07, "Residents"): the settler is not there until the herald sets the flag: the player walks through its place and
    # cannot talk to it; after the herald, it can be talked to (and it is still not solid).
    resident = scenario(
        "resident_arrives",
        [], [segment(40, move=(1, 0)), do(interact), segment(40, move=(-1, 0)), do(interact), do(advance), segment(35, move=(1, 0)),
             do(interact), do(advance)])
    resident["story"] = {"quests": {}, "dialogues": {
        "test:dialogue/herald": {"id": "test:dialogue/herald", "start": "s", "nodes": {
            "s": {"type": "set_flag", "flag": "settled", "value": True, "next": "t"},
            "t": {"type": "say", "speaker": "herald", "text": "t.herald", "next": "end"}}},
        "test:dialogue/settler": {"id": "test:dialogue/settler", "start": "s", "nodes": {
            "s": {"type": "say", "speaker": "settler", "text": "t.settler", "next": "end"}}}},
        "npcs": [{"key": "herald", "pos": [2.6, 5.8], "dialogue": "test:dialogue/herald"},
                 {"key": "settler", "pos": [4.5, 4.5], "dialogue": "test:dialogue/settler", "when": {"flag": "settled"}}]}
    # Travellers (spec 07, "Travellers"): a day is 60 ticks; the merchant stands at the first stop on day 1, at the second on day 2 (out of reach
    # where the player stands, who walks through the first stop), at the first again on day 3.
    traveller = scenario(
        "traveller_moves",
        [], [do(interact), do(advance), segment(60), do(interact), segment(40, move=(1, 0)), do(interact), do(advance), segment(30, move=(-1, 0)),
             do(interact), do(advance)],
        player={"start": [3.4, 4.5]}, day_ticks=60)
    traveller["story"] = {"quests": {}, "dialogues": {
        "test:dialogue/merchant": {"id": "test:dialogue/merchant", "start": "s", "nodes": {
            "s": {"type": "say", "speaker": "merchant", "text": "t.goods", "next": "end"}}}},
        "npcs": [{"key": "merchant", "pos": [4.0, 4.5], "dialogue": "test:dialogue/merchant", "route": [[4.0, 4.5], [6.6, 4.5]]}]}
    # The smith (spec 07, "Effects": `temper`; spec 06, "Tempering"): with the iron sword worn nothing rolls, so nothing is paid; with the keen
    # sword worn the roll is drawn and 50 gold are paid, twice; with 40 gold left the smith refuses (the choice is not shown).
    smith = scenario(
        "smith_tempers",
        [], [do(interact), do(advance), do(choose(0)), do({"cmd": "equip", "item": "test:item/keen_sword"}, interact), do(advance), do(choose(0)),
             do(interact), do(advance), do(choose(0)), do(interact), do(advance), do(choose(0))],
        player={"start": [3.4, 4.5]}, inventory={"test:item/keen_sword": 1, "base:item/iron_sword": 1},
        equipped={"weapon": "base:item/iron_sword"}, start_gold=140)
    smith["items"] = {**smith["items"], **ROLLED_ITEMS}
    smith["story"] = {"quests": {}, "dialogues": {
        "test:dialogue/smith": {"id": "test:dialogue/smith", "start": "s", "nodes": {
            "s": {"type": "say", "speaker": "smith", "text": "t.smith", "next": "menu"},
            "menu": {"type": "choice", "choices": [
                {"text": "t.temper", "when": {"gold_at_least": 50}, "effects": [{"effect": "temper", "gold": 50}], "next": "end"},
                {"text": "t.bye", "next": "end"}]}}}},
        "npcs": [{"key": "smith", "pos": [4.0, 4.5], "dialogue": "test:dialogue/smith"}]}
    # Repeatable quests (spec 07, "Quests"): the hunt pays twice, because once done it can be started anew; a quest that is not repeatable,
    # once done, is not started again (the second gel quest is refused: its reward is paid once).
    repeat = scenario(
        "repeatable_quest",
        [enemy(3.6, 4.5, hp=5, id=SLIME_ID, **passive), enemy(2.2, 6.1, hp=5, id=SLIME_ID, **passive)],
        [do({"cmd": "start_quest", "quest": "test:quest/hunt"}, {"cmd": "start_quest", "quest": "test:quest/once"}),
         segment(30, attack=True),
         do({"cmd": "start_quest", "quest": "test:quest/hunt"}, {"cmd": "start_quest", "quest": "test:quest/once"}),
         segment(20, move=(0, 1)), segment(30, attack=True)],
        inventory={"base:item/slime_gel": 1}, start_gold=0)
    repeat["story"] = {"npcs": [], "dialogues": {}, "quests": {
        "test:quest/hunt": {"id": "test:quest/hunt", "name": "t", "repeatable": True,
                            "stages": [{"id": "s", "objectives": [{"type": "kill", "enemy": SLIME_ID, "count": 1}], "next": "end"}],
                            "rewards": [{"effect": "add_gold", "amount": 10}]},
        "test:quest/once": {"id": "test:quest/once", "name": "t",
                            "stages": [{"id": "s", "objectives": [{"type": "collect", "item": "base:item/slime_gel", "count": 1}], "next": "end"}],
                            "rewards": [{"effect": "add_gold", "amount": 100}]}}}
    # Timed quests (spec 07, "Timed quests"): a day is 100 ticks. The late quest (one day) is active on day 1, as the clerk says, and over on
    # day 2: the clerk says so, and the slime killed then does not count for it. Started again on day 2 it counts again; the trial (two days,
    # started on day 2) is done in time on day 2 with the wolf, and the second slime finishes the late quest.
    timed = scenario(
        "timed_quests",
        [enemy(3.6, 4.5, hp=5, id=SLIME_ID, **passive), enemy(2.2, 6.1, hp=5, id=WOLF_ID, **passive),
         enemy(2.5, 6.2, hp=5, id=SLIME_ID, **passive)],
        [do({"cmd": "start_quest", "quest": "test:quest/late"}), do(interact, ticks=1), do(advance), segment(110),
         do(interact), do(advance), do({"cmd": "start_quest", "quest": "test:quest/trial"}),
         segment(30, attack=True), do({"cmd": "start_quest", "quest": "test:quest/late"}),
         segment(20, move=(0, 1)), segment(30, attack=True)],
        start_gold=0, day_ticks=100)
    timed["story"] = {"npcs": [{"key": "clerk", "pos": [1.4, 4.5], "dialogue": "test:dialogue/clerk"}], "dialogues": {
        "test:dialogue/clerk": {"id": "test:dialogue/clerk", "start": "s", "nodes": {
            "s": {"type": "condition", "when": {"quest_active": "test:quest/late"}, "then": "busy", "else": "free"},
            "busy": {"type": "say", "speaker": "clerk", "text": "t.busy", "next": "end"},
            "free": {"type": "say", "speaker": "clerk", "text": "t.free", "next": "end"}}}},
        "quests": {
            "test:quest/late": {"id": "test:quest/late", "name": "t", "time_limit_days": 1,
                                "stages": [{"id": "s", "objectives": [{"type": "kill", "enemy": SLIME_ID, "count": 1}], "next": "end"}],
                                "rewards": [{"effect": "add_gold", "amount": 500}]},
            "test:quest/trial": {"id": "test:quest/trial", "name": "t", "time_limit_days": 2,
                                 "stages": [{"id": "s", "objectives": [{"type": "kill", "enemy": WOLF_ID, "count": 1}], "next": "end"}],
                                 "rewards": [{"effect": "add_gold", "amount": 50}]}}}
    # Travellers walk (spec 07): a day of 1000 ticks; the traveller arrives by tick 250, stays until 750, then walks toward the next stop at
    # 1/16 of a tile per tick, never past the middle of the leg (five tiles of ten); at midnight it is at the middle, on its way in.
    walker = scenario(
        "traveller_walks",
        [], [segment(1), segment(199), segment(50), segment(400), segment(150), segment(100), segment(100), segment(250),
             segment(150), do(interact), do(advance), segment(500)],
        player={"start": [14.0, 5.5]}, day_ticks=1000)
    walker["story"] = {"quests": {}, "dialogues": {
        "test:dialogue/merchant": {"id": "test:dialogue/merchant", "start": "s", "nodes": {
            "s": {"type": "say", "speaker": "merchant", "text": "t.goods", "next": "end"}}}},
        "npcs": [{"key": "merchant", "pos": [4.0, 4.5], "dialogue": "test:dialogue/merchant", "route": [[4.0, 4.5], [14.0, 4.5]],
                  "walk": {"arrive_pm": 250, "depart_pm": 750, "speed_x256": 16}}]}
    return [flow, decline, frozen, trader, barter, rest, resident, traveller, smith, repeat, timed, walker]


def suite_story() -> list[dict]:
    cases = []
    for sc in build_scenarios():
        checkpoints = combat.run_scenario(sc)
        name = sc.pop("name")
        cases.append({"name": f"story_{name}", "input": {"op": "combat", **sc},
                      "expect": {"checkpoints": checkpoints, "tol": 0.02}})
    return cases


SAVE_SPLITS = {
    "clerk_quest": (3, 5),            # a choice is open; then mid-quest, before the fight
    "chase_hurts_then_dies": (1,),    # the slime is attacking, random streams have advanced
    "player_death": (1,),             # after a death and respawn
    "leash_and_return": (2,),         # the slime is walking home
    "trader_conditions_and_effects": (2, 5),  # inventory, flags and an open dialogue
    "affixes_worn": (2,),             # the affixes come back with the equipment (spec 06, "Affixes")
    "affixes_rolled": (2, 4),         # the rolls of the pieces found (spec 06, "Rolled affixes"), before and after a sale
    "repeatable_quest": (2,),          # a repeatable quest done, then started anew after a load
    "temper_affix": (4,),             # the tempered roll is saved (spec 06, "Tempering")
    "affix_choice": (3, 5),           # the chosen piece, its roll and rune, and the loot stream of the draws (spec 06, "Choosing an affix")
    "tags_worn": (3, 5),              # the worn tag is saved (spec 11, "Tags")
    "traveller_moves": (3,),           # the traveller is where the day says after a load
    "resident_arrives": (3, 5),       # the flag that brings the resident is saved, so it is there after a load
    "chest_storage": (3, 5),          # things in the chest (spec 06, "Chests"); a loaded game has it closed
    "runes_engrave": (2, 4),          # runes on two weapons (spec 06, "Runes"); the worn one still adds to the attack
    "furniture_home": (3,),           # furniture on two spots (spec 06, "Furniture"); what it adds counts after a load
    "party_of_companions": (6, 10),   # the party, the companion that follows and the bonds that wait are saved (spec 10, "The party")
    "cottage_rooms": (4,),            # the flag of a bought room is saved: its places stay places after a load (spec 06, "Rooms")
    "timed_quests": (7, 9),
    "traveller_walks": (4, 8),
    "week_of_play": (4, 12),          # the week: on the morning of the harvest, and on the fifth day with the traveller at its stop        # a traveller on its way out, then in: where it is comes from the time, not from the save           # the day a timed quest started is saved (spec 07, "Timed quests"): one over, one in time; then restarted
}


def suite_save() -> list[dict]:
    from conformance_m3 import all_scenarios as combat_scenarios

    by_name = {sc["name"]: sc for sc in combat_scenarios() + build_scenarios()}
    cases = []
    for name, splits in SAVE_SPLITS.items():
        for split in splits:
            sc = dict(by_name[name])
            sc.pop("name")
            save, checkpoints = combat.run_with_save(sc, split)
            cases.append({"name": f"save_{name}_at_{split}",
                          "input": {"op": "save_resume", "split": split, "save": save, **sc},
                          "expect": {"checkpoints": checkpoints, "tol": 0.02}})
    return cases


def suite_save_fixtures() -> list[dict]:
    """The frozen saves of every version (tests/saves/, spec 12, "Fixtures of the save"): each case resumes the scenario of its name
    from the frozen document, as the reference reads it today (migrated when it is older); the `game` save of a fixture is parsed and
    written again by the clients, which must keep all of it."""
    import json
    from pathlib import Path

    from conformance_m3 import all_scenarios as combat_scenarios

    by_name = {sc["name"]: sc for sc in combat_scenarios() + build_scenarios()}
    folder = Path(__file__).resolve().parent.parent / "tests" / "saves"
    cases = []
    for path in sorted(folder.glob("v*.json"), key=lambda f: int(f.stem[1:])):
        doc = json.loads(path.read_text(encoding="utf-8"))
        version = doc["save_version"]
        for fixture in doc["cases"]:
            sc = {k: v for k, v in by_name[fixture["scenario"]].items() if k != "name"}
            checkpoints = combat.run_from_save(sc, fixture["save"], fixture["split"])
            cases.append({"name": f"v{version}_{fixture['scenario']}_at_{fixture['split']}",
                          "input": {"op": "save_resume", "version": version, "split": fixture["split"], "save": fixture["save"], **sc},
                          "expect": {"checkpoints": checkpoints, "tol": 0.02}})
        if "game" in doc:
            cases.append({"name": f"v{version}_game", "input": {"op": "save_roundtrip", "version": version, "save": doc["game"]},
                          "expect": {"keeps": "every field and value of the save"}})
    return cases
