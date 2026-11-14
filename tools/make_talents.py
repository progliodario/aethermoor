#!/usr/bin/env python3
"""Writes the talents of the base pack (data/base/talents.json) and their names. Spec 11, "Talents". Run it after changing the table here."""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

POINTS_PER_LEVEL = 1
# id: (stat, percent for each rank, ranks, name en, name it, requires (talent, rank) or None)
# stat: attack (atk and matk), health, mana, defense (def and mdef), magic (matk), critical (the chance), speed (walking)
# Abilities (spec 11, "Abilities"): riposte (a parry hits back with that percent of the attack), kill_heal and kill_mana (a kill gives back
# that percent of the maximum health or mana), whirl (the power strike hits all around, and that percent farther).
# Active abilities (used on command, see ACTIVE): burst (every creature around takes that percent of the attack), mend (that percent of the
# maximum health comes back).
# Four roots, then a second ring that opens at rank 5 of its root, then a crown that opens at rank 5 of a second-ring talent; every root
# also opens an ability at rank 3.
TALENTS = {
    "might": ("attack", 5, 10, "Might", "Potenza", None),
    "vigor": ("health", 6, 10, "Vigor", "Vigore", None),
    "focus": ("mana", 8, 10, "Focus", "Concentrazione", None),
    "guard": ("defense", 8, 10, "Guard", "Guardia", None),
    "keen_eye": ("critical", 15, 5, "Keen Eye", "Occhio acuto", ("might", 5)),
    "second_wind": ("health", 8, 5, "Second Wind", "Secondo fiato", ("vigor", 5)),
    "arcana": ("magic", 10, 5, "Arcana", "Arcano", ("focus", 5)),
    "fleet_foot": ("speed", 4, 5, "Fleet Foot", "Piede lesto", ("guard", 5)),
    "legend": ("attack", 10, 5, "Legend", "Leggenda", ("keen_eye", 5)),
    "bulwark": ("defense", 12, 5, "Bulwark", "Baluardo", ("second_wind", 5)),
    "whirlwind": ("whirl", 10, 3, "Whirlwind", "Turbine", ("might", 3)),
    "bloodlust": ("kill_heal", 4, 5, "Battle Hunger", "Fame di battaglia", ("vigor", 3)),
    "flow": ("kill_mana", 8, 5, "Flow", "Flusso", ("focus", 3)),
    "riposte": ("riposte", 60, 5, "Riposte", "Risposta", ("guard", 3)),
    "shockwave": ("burst", 60, 5, "Shockwave", "Onda d'urto", ("might", 5)),
    "mend": ("mend", 15, 5, "Mend", "Rimarginare", ("vigor", 5)),
}
# Active abilities (spec 11, "Active abilities"): used on command. id: (mana, ticks before the next one, reach of a burst in hundredths of a tile)
ACTIVE = {"shockwave": (12, 480, 350), "mend": (10, 900, 0)}


def main() -> None:
    doc = {"$schema": "../../schemas/talents.schema.json", "id": "base:talents/all", "points_per_level": POINTS_PER_LEVEL,
           "talents": [{"id": name, "name": f"$i18n:talent.{name}.name", "stat": stat, "pct_per_rank": pct, "max_rank": ranks,
                        **({"requires": {"talent": req[0], "rank": req[1]}} if req else {}),
                        **({"active": {"mp": ACTIVE[name][0], "cooldown_ticks": ACTIVE[name][1],
                                       **({"radius_x100": ACTIVE[name][2]} if ACTIVE[name][2] else {})}} if name in ACTIVE else {})}
                       for name, (stat, pct, ranks, _, _, req) in TALENTS.items()]}
    (DATA / "talents.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    set_texts("content.json", "en", {f"talent.{name}.name": t[3] for name, t in TALENTS.items()})
    set_texts("content.json", "it", {f"talent.{name}.name": t[4] for name, t in TALENTS.items()})
    print(f"wrote {len(TALENTS)} talents")


if __name__ == "__main__":
    main()
