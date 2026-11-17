#!/usr/bin/env python3
"""Gives every quest of the base pack the faction it counts for (`faction`, spec 07, "Factions"), from its file name, and writes the names of
the factions. The quests of the stories of the protagonists count for none. Run it after any tool that writes quests (`make_towns.py`,
`make_stories.py` and `make_friend_quests.py` rewrite their files); a quest whose faction is right is left alone.
"""
from __future__ import annotations

import json
from pathlib import Path

from make_towns import set_texts

DATA = Path(__file__).resolve().parent.parent / "data" / "base"

# faction: (name en, name it)
FACTIONS = {
    "guild": ("the Guild", "la Gilda"),
    "wayfarers": ("the Ring of Wayfarers", "l'Anello dei Viandanti"),
    "chroniclers": ("the Chroniclers", "i Cronisti"),
    "folk": ("the Folk", "la Gente"),
}
STORY = ("act", "personal_", "epilogue", "prologue")


def faction_of(path: Path) -> str:
    name = path.stem
    if path.parent.name == "guild" or name.startswith(("clerk_", "bounty_")):
        return "guild"
    if name.startswith(("way_", "letter_", "parcel_")):
        return "wayfarers"
    if name.startswith("legend_"):
        return "chroniclers"
    if name.startswith(STORY):
        return ""
    return "folk"


def main() -> None:
    changed = 0
    for path in sorted((DATA / "quests").rglob("*.json")):
        raw = path.read_text(encoding="utf-8", newline="")
        doc = json.loads(raw)
        want = faction_of(path)
        if doc.get("faction", "") == want:
            continue
        out = {}
        for key, value in doc.items():  # the faction goes after the kind, or after the name
            if key != "faction":
                out[key] = value
            if key == ("kind" if "kind" in doc else "name") and want:
                out["faction"] = want
        newline = "\r\n" if "\r\n" in raw else "\n"
        path.write_text((json.dumps(out, indent=2, ensure_ascii=False) + "\n").replace("\n", newline), encoding="utf-8", newline="")
        changed += 1
    set_texts("core.json", "en", {f"faction.{f}.name": names[0] for f, names in FACTIONS.items()})
    set_texts("core.json", "it", {f"faction.{f}.name": names[1] for f, names in FACTIONS.items()})
    print(f"set the faction of {changed} quests")


if __name__ == "__main__":
    main()
