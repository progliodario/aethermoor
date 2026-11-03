"""Conformance suite added in M4: story scenarios (quests, dialogue, conditions, effects). Same runner as `combat`."""
from __future__ import annotations

from conformance_m3 import enemy, scenario, segment
from reference import combat

SLIME_ID = "base:enemy/slime_green"

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
            {"text": "c.barter", "when": {"has_item": {"item": "base:item/slime_gel", "qty": 2}}, "next": "barter"}]},
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
    for sc in (flow, decline, frozen, trader, barter):
        with_story(sc)
    return [flow, decline, frozen, trader, barter]


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
}


def suite_save() -> list[dict]:
    from conformance_m3 import build_scenarios as combat_scenarios

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
