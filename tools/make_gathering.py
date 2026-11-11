#!/usr/bin/env python3
"""Writes the materials that can be gathered (data/base/items/), their texts, and the table of gatherable props
(data/base/gathering.json). Spec 06, "Gathering". Run it after changing the lists here."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "base"

# item: (kind, price, effects, name en, name it, description en, description it)
ITEMS = {
    "wild_berries": ("food", 3, [("heal", 10)], "Wild berries", "Bacche selvatiche", "Sweet and a little sour. Restores a little health.", "Dolci e un po' aspre. Ripristinano un po' di salute."),
    "healing_herb": ("material", 6, [], "Healing herb", "Erba curativa", "A bitter leaf that is used in potions.", "Una foglia amara che si usa nelle pozioni."),
    "wood_log": ("material", 4, [], "Wood log", "Ceppo di legno", "Good, dry wood.", "Buon legno asciutto."),
    "pine_resin": ("material", 5, [], "Pine resin", "Resina di pino", "Sticky and sweet-smelling.", "Appiccicosa e profumata."),
    "dry_branch": ("material", 2, [], "Dry branch", "Ramo secco", "It burns well.", "Brucia bene."),
    "stone_chunk": ("material", 3, [], "Stone chunk", "Pezzo di pietra", "Heavy and sharp at one end.", "Pesante e affilato da un lato."),
    "iron_ore": ("material", 12, [], "Iron ore", "Minerale di ferro", "Rusty red, heavy for its size.", "Rosso ruggine, pesante per la sua grandezza."),
    "cactus_pulp": ("food", 3, [("heal", 8)], "Cactus pulp", "Polpa di cactus", "Cool and watery. Restores a little health.", "Fresca e acquosa. Ripristina un po' di salute."),
    # fishing in the reeds of the shores
    "river_fish": ("food", 6, [("heal", 15)], "Fresh fish", "Pesce fresco", "Still wet. Better grilled, but it will do raw. Restores a little health.", "Ancora bagnato. Meglio alla griglia, ma va bene anche crudo. Ripristina un po' di salute."),
    "golden_carp": ("material", 80, [], "Golden carp", "Carpa dorata", "A rare fish with scales like coins. Merchants pay well for it.", "Un pesce raro con le squame come monete. I mercanti lo pagano bene."),
}

# prop art -> what it gives; every drop rolls on its own (`weight_pm` out of 1000), `qty` is a range
NODES = [
    {"prop": "base:art/prop/bush", "sound": "plant", "cooldown_ticks": 7200, "reach_x100": 150,
     "drops": [("wild_berries", 1, 3, 800), ("healing_herb", 1, 2, 300)]},
    {"prop": "base:art/prop/tree_oak", "sound": "wood", "cooldown_ticks": 10800, "reach_x100": 150,
     "drops": [("wood_log", 1, 2, 1000), ("dry_branch", 1, 1, 400)]},
    {"prop": "base:art/prop/pine", "sound": "wood", "cooldown_ticks": 10800, "reach_x100": 150,
     "drops": [("wood_log", 1, 2, 900), ("pine_resin", 1, 1, 500)]},
    {"prop": "base:art/prop/dead_tree", "sound": "wood", "cooldown_ticks": 9000, "reach_x100": 150,
     "drops": [("dry_branch", 1, 3, 1000)]},
    {"prop": "base:art/prop/rock", "sound": "stone", "cooldown_ticks": 12600, "reach_x100": 150,
     "drops": [("stone_chunk", 1, 2, 1000), ("iron_ore", 1, 1, 150)]},
    {"prop": "base:art/prop/cactus", "sound": "plant", "cooldown_ticks": 9000, "reach_x100": 150,
     "drops": [("cactus_pulp", 1, 2, 900)]},
    # fishing: the reeds that grow on the beaches, where the fish hide
    {"prop": "base:art/prop/reeds", "sound": "water", "cooldown_ticks": 6000, "reach_x100": 150,
     "drops": [("river_fish", 1, 2, 900), ("golden_carp", 1, 1, 60)]},
]


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
    for name, (kind, price, effects, name_en, name_it, desc_en, desc_it) in ITEMS.items():
        doc = {"$schema": "../../../schemas/item.schema.json", "id": f"base:item/{name}", "name": f"$i18n:item.{name}.name",
               "description": f"$i18n:item.{name}.desc", "kind": kind, "rarity": "common", "price": price, "stack_max": 99}
        if effects:
            doc["use"] = {"effects": [{"effect": e, "amount": a} for e, a in effects]}
        write_json(DATA / "items" / f"{name}.json", doc)
        en[f"item.{name}.name"], en[f"item.{name}.desc"] = name_en, desc_en
        it[f"item.{name}.name"], it[f"item.{name}.desc"] = name_it, desc_it
    add_texts("en", en)
    add_texts("it", it)
    nodes = [{"prop": n["prop"], "sound": n["sound"], "cooldown_ticks": n["cooldown_ticks"], "reach_x100": n["reach_x100"],
              "drops": [{"item": f"base:item/{item}", "qty_min": lo, "qty_max": hi, "weight_pm": w} for item, lo, hi, w in n["drops"]]} for n in NODES]
    write_json(DATA / "gathering.json", {"$schema": "../../schemas/gathering.schema.json", "id": "base:gathering/nodes", "nodes": nodes})
    print(f"wrote {len(ITEMS)} items and {len(NODES)} gatherable props")


if __name__ == "__main__":
    main()
