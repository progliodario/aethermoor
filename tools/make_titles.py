#!/usr/bin/env python3
"""Writes the titles of the base pack (data/base/titles.json) and their names. Spec 11. Run it after changing the table here."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "base"

# id: (kind, count, enemy or None, name en, name it); the order is the order of rank: the last one earned is the one shown
TITLES = {
    "newcomer": ("level", 2, None, "Newcomer", "Nuovo arrivato"),
    "slime_hunter": ("kills_of", 10, "slime_green", "Slime Hunter", "Cacciatore di slime"),
    "pest_control": ("kills", 25, None, "Pest Control", "Disinfestatore"),
    "wolf_bane": ("kills_of", 8, "wolf_grey", "Wolf Bane", "Flagello dei lupi"),
    "adventurer": ("level", 10, None, "Adventurer", "Avventuriero"),
    "helper": ("quests", 5, None, "Helper of the Folk", "Aiuto della gente"),
    "naturalist": ("species", 10, None, "Naturalist", "Naturalista"),
    "forager": ("gathered", 30, None, "Forager", "Raccoglitore"),
    "artisan": ("crafted", 15, None, "Artisan", "Artigiano"),
    "unbreakable": ("parried", 25, None, "Unbreakable Guard", "Guardia incrollabile"),
    "veteran": ("kills", 150, None, "Veteran", "Veterano"),
    "gel_slayer": ("kills_of", 1, "gel_king", "Gel King's Bane", "Rovina del Re Gelatina"),
    "hero": ("level", 25, None, "Hero", "Eroe"),
    "chronicler": ("species", 30, None, "Chronicler of Beasts", "Cronista delle bestie"),
    "legend": ("quests", 40, None, "Legend of the Realm", "Leggenda del reame"),
}


# What a title adds to the attack of the player's hits, in percent, while it is earned (spec 11, "Titles with effects"); 3 when not listed.
# What a title of a way of playing adds besides attack (spec 11): one more of every drop gathered, more of every recipe made.
PERKS = {"forager": {"gather_bonus": 1}, "artisan": {"craft_bonus": 1}}
ATTACK_PCT = {"newcomer": 2, "veteran": 5, "gel_slayer": 5, "hero": 8, "chronicler": 8, "legend": 10}


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
    titles = []
    en: dict[str, str] = {}
    it: dict[str, str] = {}
    for name, (kind, count, enemy, name_en, name_it) in TITLES.items():
        entry = {"id": name, "name": f"$i18n:title.{name}", "kind": kind, "count": count}
        entry["atk_pct"] = ATTACK_PCT.get(name, 3)
        entry.update(PERKS.get(name, {}))
        if enemy:
            entry["enemy"] = f"base:enemy/{enemy}"
        titles.append(entry)
        en[f"title.{name}"], it[f"title.{name}"] = name_en, name_it
    doc = {"$schema": "../../schemas/titles.schema.json", "id": "base:titles/all", "titles": titles}
    (DATA / "titles.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    add_texts("en", en)
    add_texts("it", it)
    print(f"wrote {len(titles)} titles")


if __name__ == "__main__":
    main()
