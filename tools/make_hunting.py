#!/usr/bin/env python3
"""Writes the game of the hunt (spec 06, "Hunting"): two wild creatures that are shy and easy, what they leave, their texts, their art (from the
tawny wolf's body, with their own palette and features from `art_creature_looks.py`), and their place in the fauna of the regions. Run it after
changing the tables here, then `python tools/art_creatures.py`, `python tools/make_recipes.py` and `python tools/gen_conformance.py`."""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "base"

# creature: (level, hp, atk, def, speed_x100, xp, palette, drops [(item, qty_min, qty_max, weight_pm)], fauna drop, regions, name en, name it)
GAME = {
    "wild_boar": (2, 40, 7, 2, 300, 10,
                  {"fur": "#6B4A2E", "light": "#9A7350", "dark": "#3E2716", "outline": "#1E120A", "eye": "#1A0F08", "nose": "#2A1B0A", "inner": "#C88A70"},
                  [("game_meat", 1, 2, 850), ("boar_hide", 1, 1, 500)], "boar_hide", ("verdalis", "whisperwood", "tidehaven"),
                  "Wild boar", "Cinghiale"),
    "ridge_elk": (4, 60, 9, 3, 360, 16,
                  {"fur": "#A8754A", "light": "#D9AE7E", "dark": "#6A4524", "outline": "#2E1C0C", "eye": "#20140A", "nose": "#2A1B0A", "inner": "#E8C0A0"},
                  [("game_meat", 1, 2, 850), ("elk_antler", 1, 1, 450)], "elk_antler", ("frostveil", "ironspine", "lumeria"),
                  "Ridge elk", "Alce dei crinali"),
}
FAUNA_WEIGHT = 2

# item: (kind, price, effects [(effect, amount[, ticks])] or armor/weapon stats, rarity, name en, name it, description en, description it)
ITEMS = {
    "game_meat": ("food", 8, [("heal", 20)], "common", "Game meat", "Selvaggina", "Fresh from the hunt. Better roasted, but it will do. Restores a little health.",
                  "Fresca di caccia. Meglio arrosto, ma va bene così. Ripristina un po' di salute."),
    "boar_hide": ("material", 14, [], "common", "Boar hide", "Pelle di cinghiale", "Thick and bristly. Tanners love it.", "Spessa e ispida. I conciatori la adorano."),
    "elk_antler": ("material", 22, [], "common", "Elk antler", "Corno d'alce", "Light, hard, and very pointy.", "Leggero, duro e molto appuntito."),
    "roast_meat": ("food", 30, [("heal", 70), ("fortify", 10, 1800)], "common", "Roast meat", "Arrosto", "Crackling outside, tender inside. Restores health and fortifies: +10% attack for 30 s.",
                   "Croccante fuori, tenero dentro. Ripristina la salute e fortifica: +10% di attacco per 30 s."),
    "hunters_stew": ("food", 45, [("heal", 120), ("fortify", 20, 3600)], "common", "Hunter's stew", "Stufato del cacciatore", "Meat, herbs and patience. Restores a lot of health and fortifies: +20% attack for a minute.",
                     "Carne, erbe e pazienza. Ripristina molta salute e fortifica: +20% di attacco per un minuto."),
    "hunters_jerkin": ("armor", 260, {"def": 5, "mdef": 2}, "uncommon", "Hunter's jerkin", "Giubba del cacciatore",
                       "Boar hide over leather, with antler toggles. Light and tough.", "Pelle di cinghiale sopra il cuoio, con alamari di corno. Leggera e robusta."),
    "antler_spear": ("weapon", 300, {"atk": 16, "matk": 0}, "uncommon", "Antler spear", "Lancia di corno", "A long shaft with an elk's antler for a point. It reaches far.",
                     "Un'asta lunga con un corno d'alce per punta. Arriva lontano."),
}


def write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def set_texts(lang: str, entries: dict[str, str]) -> None:
    """Sets texts in content.json: existing keys are replaced in place, new ones go after the last `item.` key."""
    path = DATA / "i18n" / lang / "content.json"
    raw = path.read_text(encoding="utf-8", newline="")
    newline = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.replace("\r\n", "\n").split("\n")
    index = {line.split('"')[1]: k for k, line in enumerate(lines) if line.startswith('  "')}
    anchor = max(k for k, line in enumerate(lines) if line.startswith('  "item.'))
    for key, value in entries.items():
        line = f'  "{key}": {json.dumps(value, ensure_ascii=False)},'
        if key in index:
            lines[index[key]] = line if lines[index[key]].endswith(",") else line[:-1]
        else:
            anchor += 1
            lines.insert(anchor, line)
    path.write_text(newline.join(lines), encoding="utf-8", newline="")


def item_doc(name: str, spec: tuple) -> dict:
    kind, price, extra, rarity = spec[:4]
    doc = {"$schema": "../../../schemas/item.schema.json", "id": f"base:item/{name}", "name": f"$i18n:item.{name}.name",
           "description": f"$i18n:item.{name}.desc", "kind": kind, "rarity": rarity, "price": price}
    if kind in ("food", "material"):
        doc["stack_max"] = 99
    if kind == "food":
        doc["use"] = {"effects": [{"effect": e[0], "amount": e[1], **({"ticks": e[2]} if len(e) > 2 else {})} for e in extra]}
    elif kind == "armor":
        doc["armor"] = extra
    elif kind == "weapon":
        doc["weapon"] = extra
    return doc


def main() -> None:
    en: dict[str, str] = {}
    it: dict[str, str] = {}
    template = json.loads((DATA / "art" / "creatures" / "wolf_tawny.json").read_text(encoding="utf-8"))
    world_path = DATA / "worlds" / "overworld.json"
    world = world_path.read_text(encoding="utf-8")
    for name, (level, hp, atk, defense, speed, xp, palette, drops, fauna_drop, regions, name_en, name_it) in GAME.items():
        write_json(DATA / "enemies" / f"{name}.json", {
            "$schema": "../../../schemas/enemy.schema.json", "id": f"base:enemy/{name}", "name": f"$i18n:enemy.{name}.name", "level": level,
            "stats": {"hp": hp, "atk": atk, "def": defense, "mdef": 2, "speed_x100": speed}, "element": "none", "sound": "wolf",
            "weaknesses_pm": {"fire": 1500}, "xp": xp,
            "drops": [{"item": f"base:item/{item}", "qty_min": lo, "qty_max": hi, "weight_pm": pm} for item, lo, hi, pm in drops],
            "radius_x100": 38, "behavior": "base:behavior/skittish", "art": f"base:art/creature/{name}"})
        art = copy.deepcopy(template)
        art["id"] = f"base:art/creature/{name}"
        art["palette"] = palette
        write_json(DATA / "art" / "creatures" / f"{name}.json", art)
        en[f"enemy.{name}.name"], it[f"enemy.{name}.name"] = name_en, name_it
        # the fauna of the regions: one more entry each, in the compact style of the world file
        entry = f'{{ "enemy": "base:enemy/{name}", "drop": "base:item/{fauna_drop}", "weight": {FAUNA_WEIGHT} }}'
        for region in regions:
            start = world.index(f'{{ "id": "{region}",')
            fauna = world.index('"fauna": [', start) + len('"fauna": [')
            end = world.index("]", fauna)
            if f"base:enemy/{name}" not in world[fauna:end]:
                world = world[:end] + ", " + entry + world[end:]
    world_path.write_text(world, encoding="utf-8")
    for name, spec in ITEMS.items():
        write_json(DATA / "items" / f"{name}.json", item_doc(name, spec))
        en[f"item.{name}.name"], it[f"item.{name}.name"] = spec[4], spec[5]
        en[f"item.{name}.desc"], it[f"item.{name}.desc"] = spec[6], spec[7]
    set_texts("en", en)
    set_texts("it", it)
    print(f"wrote {len(GAME)} creatures of the hunt and {len(ITEMS)} items")


if __name__ == "__main__":
    main()
