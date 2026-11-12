#!/usr/bin/env python3
"""Writes four more creatures of the regions, what they leave and their place in the fauna (12 November 2026):

- the **blossom slime** of Verdalis and Lumeria, with flowers on its back (it leaves wildflowers);
- the **hollow armor** of Ironspine and Whisperwood, a suit of rusty plate that walks with nobody inside;
- the **frost wisp** of Frostveil, a cold flame;
- the **cinder wolf** of the Ashen Wastes, with embers in its fur (its pelt makes a cloak).

Like `make_hunting.py`: an enemy file, a first art file with the palette (`art_creatures.py` then draws the body and the
feature of each), the names, the items and one more entry in the fauna of the regions. Run it after changing the tables
here, then `python tools/art_creatures.py`, `python tools/make_recipes.py`, `python tools/gen_conformance.py` and
`python tools/make_catalog.py`. The fights stay easy: these numbers follow those of the creatures of the same level.
"""
from __future__ import annotations

import copy
import json

from make_hunting import DATA, item_doc, set_texts, write_json

# creature: level, stats, xp, element, weakness, sound, behavior, radius, art it is first copied from, palette, drops, fauna drop, regions, names
CREATURES = {
    "slime_bloom": {
        "level": 2, "stats": {"hp": 34, "atk": 6, "def": 2, "mdef": 2, "speed_x100": 250}, "xp": 9, "element": "earth", "weak": "fire",
        "sound": "slime", "behavior": "melee_chaser_basic", "radius": 35, "from": "slime_green",
        "palette": {"body": "#F08AB8", "light": "#FFD0E6", "dark": "#A8487A", "outline": "#4A1830", "eye": "#1E1B28"},
        "drops": [("wildflowers", 1, 2, 800), ("slime_gel", 1, 1, 500)], "fauna": "wildflowers", "regions": ("verdalis", "lumeria"),
        "en": "Blossom slime", "it": "Slime in fiore"},
    "hollow_armor": {
        "level": 9, "stats": {"hp": 200, "atk": 24, "def": 14, "mdef": 5, "speed_x100": 240}, "xp": 85, "element": "dark", "weak": "light",
        "sound": "knight", "behavior": "brute", "radius": 48, "from": "barrow_warden",
        "palette": {"light": "#B8A090", "body": "#7A6456", "dark": "#3E3028", "outline": "#1A1210", "glow": "#9AE8C8", "bone": "#C8B8A0", "slit": "#0E0A08"},
        "drops": [("rust_flake", 1, 2, 700), ("iron_ore", 1, 2, 500)], "fauna": "rust_flake", "regions": ("ironspine", "whisperwood"),
        "en": "Hollow armor", "it": "Armatura vuota"},
    "frost_wisp": {
        "level": 10, "stats": {"hp": 96, "atk": 27, "def": 2, "mdef": 15, "speed_x100": 320}, "xp": 70, "element": "water", "weak": "fire",
        "sound": "wisp", "behavior": "lunger", "radius": 32, "from": "wisp",
        "palette": {"body": "#BFE8FF", "light": "#FFFFFF", "dark": "#5A8AD8", "outline": "#1E3A6A", "eye": "#1E3A6A", "halo": "#D8F4FF"},
        "drops": [("ice_crystal", 1, 1, 600)], "fauna": "ice_crystal", "regions": ("frostveil",),
        "en": "Frost wisp", "it": "Fuoco fatuo del gelo"},
    "wolf_ember": {
        "level": 13, "stats": {"hp": 180, "atk": 33, "def": 11, "mdef": 9, "speed_x100": 350}, "xp": 120, "element": "fire", "weak": "water",
        "sound": "wolf", "behavior": "stalker", "radius": 40, "from": "wolf_dire",
        "palette": {"fur": "#3A2A2C", "light": "#8A4A3A", "dark": "#160E10", "outline": "#080405", "eye": "#FFB040", "nose": "#080405", "inner": "#C85A3A"},
        "drops": [("ember_pelt", 1, 1, 600)], "fauna": "ember_pelt", "regions": ("ashen_wastes",),
        "en": "Cinder wolf", "it": "Lupo delle braci"},
}
FAUNA_WEIGHT = 2

# item: (kind, price, effects or stats, rarity, name en, name it, description en, description it)
ITEMS = {
    "ember_pelt": ("material", 40, [], "common", "Ember pelt", "Pelliccia di brace", "Black fur that is still warm, with sparks deep inside it.",
                   "Pelo nero ancora caldo, con scintille in fondo."),
    "ember_cloak": ("armor", 520, {"def": 8, "mdef": 6}, "uncommon", "Cinder cloak", "Mantello di brace",
                    "It keeps the warmth of the fire it came from. Snow melts before it lands on you.",
                    "Conserva il calore del fuoco da cui viene. La neve si scioglie prima di posarsi."),
}


def main() -> None:
    en: dict[str, str] = {}
    it: dict[str, str] = {}
    world_path = DATA / "worlds" / "overworld.json"
    world = world_path.read_text(encoding="utf-8", newline="")
    for name, c in CREATURES.items():
        write_json(DATA / "enemies" / f"{name}.json", {
            "$schema": "../../../schemas/enemy.schema.json", "id": f"base:enemy/{name}", "name": f"$i18n:enemy.{name}.name", "level": c["level"],
            "stats": c["stats"], "element": c["element"], "sound": c["sound"], "weaknesses_pm": {c["weak"]: 1500}, "xp": c["xp"],
            "drops": [{"item": f"base:item/{item}", "qty_min": lo, "qty_max": hi, "weight_pm": pm} for item, lo, hi, pm in c["drops"]],
            "radius_x100": c["radius"], "behavior": f"base:behavior/{c['behavior']}", "art": f"base:art/creature/{name}"})
        art_path = DATA / "art" / "creatures" / f"{name}.json"
        if not art_path.exists():  # a first picture with the palette: art_creatures.py draws the real one
            art = copy.deepcopy(json.loads((DATA / "art" / "creatures" / f"{c['from']}.json").read_text(encoding="utf-8")))
            art["id"] = f"base:art/creature/{name}"
            art["palette"] = c["palette"]
            write_json(art_path, art)
        en[f"enemy.{name}.name"], it[f"enemy.{name}.name"] = c["en"], c["it"]
        entry = f'{{ "enemy": "base:enemy/{name}", "drop": "base:item/{c["fauna"]}", "weight": {FAUNA_WEIGHT} }}'
        for region in c["regions"]:
            start = world.index(f'{{ "id": "{region}",')
            fauna = world.index('"fauna": [', start) + len('"fauna": [')
            end = world.index("]", fauna)
            if f"base:enemy/{name}" not in world[fauna:end]:
                world = world[:end] + ", " + entry + world[end:]
    world_path.write_text(world, encoding="utf-8", newline="")
    for name, spec in ITEMS.items():
        write_json(DATA / "items" / f"{name}.json", item_doc(name, spec))
        en[f"item.{name}.name"], it[f"item.{name}.name"] = spec[4], spec[5]
        en[f"item.{name}.desc"], it[f"item.{name}.desc"] = spec[6], spec[7]
    set_texts("en", en)
    set_texts("it", it)
    print(f"wrote {len(CREATURES)} creatures and {len(ITEMS)} items")


if __name__ == "__main__":
    main()
