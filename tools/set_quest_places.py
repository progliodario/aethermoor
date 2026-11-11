#!/usr/bin/env python3
"""Gives every quest stage that asks to defeat a guardian the place of that guardian (`place`, a landmark ID; spec 07, "Places"), so that the
clients can set the goal on the map. Run it after adding quests or landmarks; a stage that already has a place keeps it."""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "base"


def main() -> None:
    world = json.loads((DATA / "worlds" / "overworld.json").read_text(encoding="utf-8"))
    where: dict[str, str] = {}
    for landmark in world["landmarks"]:
        stamp = json.loads((DATA / "stamps" / (landmark["stamp"].split("/")[-1] + ".json")).read_text(encoding="utf-8"))
        for ch, entry in stamp["legend"].items():
            if "spawner" in entry and any(ch in row for row in stamp["rows"]):
                enemy = json.loads((DATA / "enemies" / (entry["spawner"].split("/")[-1] + ".json")).read_text(encoding="utf-8"))
                if enemy.get("behavior", "").endswith("guardian"):
                    where.setdefault(entry["spawner"], landmark["id"])
    count = 0
    for path in sorted((DATA / "quests").rglob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for stage in doc["stages"]:
            for objective in stage["objectives"]:
                if objective.get("type") == "kill" and objective["enemy"] in where and "place" not in stage:
                    stage["place"] = where[objective["enemy"]]
                    changed = True
        if changed:
            count += 1
            path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"gave a place to {count} quests")


if __name__ == "__main__":
    main()
