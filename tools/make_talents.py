#!/usr/bin/env python3
"""Writes the talents of the base pack (data/base/talents.json) and their names. Spec 11, "Talents". Run it after changing the table here."""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

POINTS_PER_LEVEL = 1
# id: (stat, percent for each rank, ranks, name en, name it); stat is attack, health, mana or defense
TALENTS = {
    "might": ("attack", 5, 10, "Might", "Potenza"),
    "vigor": ("health", 6, 10, "Vigor", "Vigore"),
    "focus": ("mana", 8, 10, "Focus", "Concentrazione"),
    "guard": ("defense", 8, 10, "Guard", "Guardia"),
}


def main() -> None:
    doc = {"$schema": "../../schemas/talents.schema.json", "id": "base:talents/all", "points_per_level": POINTS_PER_LEVEL,
           "talents": [{"id": name, "name": f"$i18n:talent.{name}.name", "stat": stat, "pct_per_rank": pct, "max_rank": ranks}
                       for name, (stat, pct, ranks, _, _) in TALENTS.items()]}
    (DATA / "talents.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    set_texts("content.json", "en", {f"talent.{name}.name": t[3] for name, t in TALENTS.items()})
    set_texts("content.json", "it", {f"talent.{name}.name": t[4] for name, t in TALENTS.items()})
    print(f"wrote {len(TALENTS)} talents")


if __name__ == "__main__":
    main()
