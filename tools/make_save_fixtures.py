#!/usr/bin/env python3
"""The frozen copies of the save documents of every version (spec 12, "Fixtures of the save"): tests/saves/v<N>.json.

Usage: python tools/make_save_fixtures.py [--check]
  (no flag)  write tests/saves/v<SAVE_VERSION>.json if it does not exist; if it exists, append the cases of the save suite
             (SAVE_SPLITS of tools/conformance_m4.py) that it does not hold yet. A case already written is never changed, and the
             file of an older version is never touched: they are what the players' old saves look like.
  --check    write nothing; fail when a version from 1 to SAVE_VERSION has no file, when a file is not of its version, or when the
             reference writes a field of the save that no case of the current fixture holds (a new field needs a case, so that
             the next version has to load it).

A fixture case is {"scenario", "split", "save"}: the save document written by the reference before segment `split` of the
scenario of that name, with its `save_version`. `game` is a save of the streamed world with every field the clients write: they
parse it, write it again and must keep every field and value of it. tools/gen_conformance.py turns every case into the suite `save_fixtures`, which
the reference and both clients run: they load the frozen document (migrated when it is older) and must reach the checkpoints of
the reference.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reference import combat  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SAVES = ROOT / "tests" / "saves"


# A save of the streamed world as the clients write it (spec 12, "Document"), with every optional field: the reference does not write
# the fields of the world alone (explored, stones, cleared spawners, the companion, the friend, the plots). Both clients parse it,
# write it again and must keep every field and every value. Added to a fixture only when it has no game yet; never changed after.
GAME_V1 = {
    "save_version": 1, "game_version": "0.0.1", "data_format_version": 1, "protagonist": "base:protagonist/haruka",
    "seed": "0x000000005eed1234", "map": "world",
    "player": {"x": 8192.5, "y": 8200.25, "facing": [0.0, 1.0], "facing_left": True, "moving": False, "clip_tick": 12, "hp": 310,
               "level": 14, "xp": 1250, "deaths": 2, "kills": 187, "iframes": 0, "cooldown": 0, "phase": "none", "phase_tick": 0,
               "hit_set": [False, False]},
    "rng": {"combat": {"state": "0x1d2c3b4a59687766", "inc": "0x00000000000000c5"},
            "loot": {"state": "0x0a0b0c0d0e0f1011", "inc": "0x0000000000000a37"}},
    "enemies": [{"x": 8200.5, "y": 8190.5, "hp": 64, "state": "idle", "state_tick": 0, "spawner": [8200, 8190]},
                {"x": 8180.75, "y": 8210.5, "hp": 0, "state": "dead", "state_tick": 30, "spawner": [8181, 8210]}],
    "cleared_spawners": [[8181, 8210, 1440120], [8150, 8233, 1300000]],
    "world_ticks": 1441000,
    "equipped": {"weapon": "base:item/iron_sword", "armor": "base:item/leather_vest", "accessory": "base:item/fang_necklace"},
    "chest": {"base:item/bread": 6, "base:item/wood_log": 12},
    "plots": [[819050, 820030, "base:item/herb_seeds", 1445000], [819150, 820030, "base:item/berry_seeds", 1446000]],
    "rolls": {"base:item/iron_sword_keenness": 135},
    "runes": {"base:item/iron_sword": "base:item/rune_ember"},
    "tag": "berserker",
    "furniture": [[819300, 819800, "base:item/quilt_bed"], [819500, 819800, "base:item/weapon_rack"]],
    "talents": {"vigor": 2, "whirl": 1},
    "counters": {"crafted": 9, "gathered": 140, "parried": 21, "renown:verdalis": 7},
    "bestiary": {"base:enemy/slime_green": 61, "base:enemy/wolf_tawny": 12},
    "friend": {"enemy": "base:enemy/wolf_tawny", "x": 8193.5, "y": 8201.0, "cooldown": 20, "stay": True},
    "companion": {"x": 8191.5, "y": 8199.5, "cooldown": 15, "stay": True, "bond": 23},
    "explored": [[255, 256], [256, 256], [256, 257]],
    "stones": [[8190, 8205], [9000, 7100]],
    "inventory": {"base:item/bread": 3, "base:item/iron_sword": 1, "base:item/iron_sword_keenness": 1, "base:item/leather_vest": 1,
                  "base:item/fang_necklace": 1, "base:item/potion_small": 5},
    "story": {"flags": {"met_mira": True, "hint_move": True}, "gold": 1830, "guild_points": 44,
              "quests": {"base:quest/guild/slime_extermination": {"stage": "kill", "progress": [2], "done": False},
                         "base:quest/fenwick/first_steps": {"stage": "end", "progress": [], "done": True}},
              "dialogue": {"id": "base:dialogue/npc/mira", "node": "offer_choice", "args": {"name": "Mira"}}},
}


def fixture_path(version: int) -> Path:
    return SAVES / f"v{version}.json"


def scenarios_by_name() -> dict[str, dict]:
    from conformance_m3 import all_scenarios as combat_scenarios
    from conformance_m4 import build_scenarios as story_scenarios

    return {sc["name"]: sc for sc in combat_scenarios() + story_scenarios()}


def current_cases() -> list[dict]:
    """The cases the reference writes today: one for every split of SAVE_SPLITS."""
    from conformance_m4 import SAVE_SPLITS

    by_name = scenarios_by_name()
    cases = []
    for name, splits in SAVE_SPLITS.items():
        for split in splits:
            sc = {k: v for k, v in by_name[name].items() if k != "name"}
            save, _ = combat.run_with_save(sc, split)
            cases.append({"scenario": name, "split": split, "save": {"save_version": combat.SAVE_VERSION, **save}})
    return cases


def field_paths(save: dict) -> set[str]:
    """The fields of a save document: its keys, and the keys of the objects under `player`, `story` and `companion`."""
    paths = set(save)
    for key in ("player", "story", "companion", "friend"):
        if isinstance(save.get(key), dict):
            paths |= {f"{key}.{inner}" for inner in save[key]}
    return paths


def problems() -> list[str]:
    out = []
    for version in range(1, combat.SAVE_VERSION + 1):
        path = fixture_path(version)
        if not path.exists():
            out.append(f"{path.relative_to(ROOT)} is missing: every save version keeps its frozen copy "
                       f"(run tools/make_save_fixtures.py before changing the format again)")
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("save_version") != version:
            out.append(f"{path.relative_to(ROOT)}: save_version is {doc.get('save_version')!r}, not {version}")
        if "game" in doc and doc["game"].get("save_version") != version:
            out.append(f"{path.relative_to(ROOT)}: the game save is not of version {version}")
        for case in doc.get("cases", []):
            if case.get("save", {}).get("save_version") != version:
                out.append(f"{path.relative_to(ROOT)}: the save of {case.get('scenario')} at {case.get('split')} is not of version {version}")
    current = fixture_path(combat.SAVE_VERSION)
    if current.exists():
        frozen: set[str] = set()
        for case in json.loads(current.read_text(encoding="utf-8")).get("cases", []):
            frozen |= field_paths(case["save"])
        written: set[str] = set()
        for case in current_cases():
            written |= field_paths(case["save"])
        for field in sorted(written - frozen):
            out.append(f"the reference writes the field '{field}' of the save, but no case of {current.relative_to(ROOT)} holds it: "
                       f"add the scenario to SAVE_SPLITS and run tools/make_save_fixtures.py (spec 12, \"Fixtures of the save\")")
    return out


def write() -> list[str]:
    path = fixture_path(combat.SAVE_VERSION)
    if path.exists():
        doc = json.loads(path.read_text(encoding="utf-8"))
    else:
        doc = {"save_version": combat.SAVE_VERSION,
               "note": "Frozen: written once by tools/make_save_fixtures.py. Never change or remove a case; new cases are appended.",
               "cases": []}
    have = {(c["scenario"], c["split"]) for c in doc["cases"]}
    added = [c for c in current_cases() if (c["scenario"], c["split"]) not in have]
    doc["cases"] += added
    game = "game" not in doc and combat.SAVE_VERSION == 1
    if game:  # the save of the streamed world of version 1; a later version writes its own when its format changes
        doc["game"] = GAME_V1
    if added or game or not path.exists():
        SAVES.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    return [f"{c['scenario']} at {c['split']}" for c in added]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        added = write()
        print(f"{fixture_path(combat.SAVE_VERSION).relative_to(ROOT)}: {len(added)} case(s) added" + (": " + ", ".join(added) if added else ""))
    found = problems()
    for problem in found:
        print("ERROR:", problem)
    if not found and args.check:
        print("OK: a frozen save for every version")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
