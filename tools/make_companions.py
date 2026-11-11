#!/usr/bin/env python3
"""Writes the companions of the base pack (data/base/companions/), their names, and gives each protagonist theirs. Spec 10.
Run it after changing the table here."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "base"

# Care (spec 10): from this bond on, every companion heals the player now and then (ten seconds, 5% of the health).
CARE_BOND, CARE_TICKS, CARE_PCT = 10, 600, 5

# companion: (protagonist, creature art, name en, name it, atk_base, atk_per_level, range_x100, cooldown_ticks, speed_x100, scale_pct)
COMPANIONS = {
    "orb": ("ren", "wisp", "Orb", "Orbe", 7, 1, 350, 110, 330, 70),
    "newton": ("sakura", "night_owl", "Newton", "Newton", 8, 1, 400, 100, 340, 70),
    "ember": ("daichi", "wolf_tawny", "Ember", "Brace", 10, 1, 250, 90, 360, 60),
    "pip": ("haruka", "slime_mint", "Pip", "Pip", 6, 1, 200, 80, 320, 90),
    "pot": ("marco", "shore_crab", "Pot", "Pentola", 9, 1, 220, 100, 300, 80),
    "shade": ("yuki", "cave_bat", "Shade", "Ombra", 9, 1, 300, 75, 380, 80),
    "mort": ("lena", "cave_spider", "Mort", "Mortina", 8, 1, 280, 85, 340, 80),
    "gloom": ("gideon", "wolf_shade", "Gloom", "Tenebra", 11, 1, 300, 90, 360, 60),
}


def write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def add_texts(lang: str, entries: dict[str, str]) -> None:
    path = DATA / "i18n" / lang / "content.json"
    raw = path.read_text(encoding="utf-8", newline="")
    newline = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.replace("\r\n", "\n").split("\n")
    existing = {line.split('"')[1] for line in lines if line.startswith('  "')}
    anchor = max(k for k, line in enumerate(lines) if line.startswith('  "item.'))
    for key, value in entries.items():
        if key in existing:
            continue
        anchor += 1
        lines.insert(anchor, f'  "{key}": {json.dumps(value, ensure_ascii=False)},')
    path.write_text(newline.join(lines), encoding="utf-8", newline="")


def main() -> None:
    en: dict[str, str] = {}
    it: dict[str, str] = {}
    for name, (who, art, name_en, name_it, atk, per_level, reach, cooldown, speed, scale) in COMPANIONS.items():
        write_json(DATA / "companions" / f"{name}.json", {
            "$schema": "../../../schemas/companion.schema.json", "id": f"base:companion/{name}", "name": f"$i18n:companion.{name}.name",
            "art": f"base:art/creature/{art}", "scale_pct": scale, "atk_base": atk, "atk_per_level": per_level, "range_x100": reach,
            "cooldown_ticks": cooldown, "speed_x100": speed, "follow_x100": 220, "care_bond": CARE_BOND, "care_ticks": CARE_TICKS, "care_pct": CARE_PCT})
        en[f"companion.{name}.name"], it[f"companion.{name}.name"] = name_en, name_it
        path = DATA / "protagonists" / f"{who}.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc["companion"] = f"base:companion/{name}"
        write_json(path, doc)
    add_texts("en", en)
    add_texts("it", it)
    print(f"wrote {len(COMPANIONS)} companions")


if __name__ == "__main__":
    main()
