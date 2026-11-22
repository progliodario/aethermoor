#!/usr/bin/env python3
"""Writes the creatures that live only in one season (spec 09, "Seasonal visitors"): four slimes, one a season, with a loot of their own.

The snow slime of winter, the sun slime of summer, the leaf slime of autumn and the rain slime of spring come only as visitors of the
seasons (`make_seasonal_fauna.py`): no fauna entry makes them. Each leaves a material found nowhere else (a snowflake, a sun drop, an
amber leaf, a rain pearl), and the four together brew the tea of the four seasons at a campfire (`make_recipes.py`), a dish that
fortifies, wards and regenerates at once. Their art is written by `art_creatures.py` (the features `snow`, `sun`, `leaf` and `rain`)
from the palette this tool writes the first time.

It writes the creatures `data/base/enemies/slime_<kind>.json` (keeping the drops other tools added), the first file of their art, the
items and their texts (it and en). It can be run any number of times. Then run `art_creatures.py`, `make_seasonal_fauna.py`,
`make_common_affixes.py`, `make_recipes.py`, `make_titles.py`, `make_catalog.py` and `make_facts.py`.
"""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

ART = DATA / "art" / "creatures"
# kind: (level, hp, atk, element, weakness, xp, its material, palette, name en, name it)
SLIMES = {
    "snow": (3, 36, 7, "water", "fire", 12, "snowflake", {"body": "#E4F2FA", "light": "#FFFFFF", "dark": "#8EB4CC", "outline": "#2A4A5E", "eye": "#1E1B28"},
             "Snow slime", "Gelatina di neve"),
    "sun": (4, 40, 8, "fire", "water", 14, "sun_drop", {"body": "#FFC94A", "light": "#FFF2B0", "dark": "#D27A14", "outline": "#5A3008", "eye": "#2A1A10"},
            "Sun slime", "Gelatina del sole"),
    "leaf": (3, 38, 7, "earth", "fire", 13, "amber_leaf", {"body": "#E88A3A", "light": "#FFD08A", "dark": "#9A3E14", "outline": "#4A1A08", "eye": "#2A1408"},
             "Leaf slime", "Gelatina di foglie"),
    "rain": (3, 34, 6, "water", "earth", 12, "rain_pearl", {"body": "#8FD8E6", "light": "#E6FBFF", "dark": "#3E8AA8", "outline": "#163A4A", "eye": "#14222A"},
             "Rain slime", "Gelatina di pioggia"),
}
# material: (price, name en, name it, description en, description it)
MATERIALS = {
    "snowflake": (30, "Snowflake", "Fiocco di neve", "A snowflake that does not melt. Snow slimes leave it, and only in winter.",
                  "Un fiocco di neve che non si scioglie. Lo lasciano le gelatine di neve, e solo d'inverno."),
    "sun_drop": (30, "Sun drop", "Goccia di sole", "A warm golden drop that glows in the dark. Sun slimes leave it, and only in summer.",
                 "Una goccia dorata e calda che brilla al buio. La lasciano le gelatine del sole, e solo d'estate."),
    "amber_leaf": (30, "Amber leaf", "Foglia d'ambra", "A red leaf that never dries. Leaf slimes leave it, and only in autumn.",
                   "Una foglia rossa che non secca mai. La lasciano le gelatine di foglie, e solo d'autunno."),
    "rain_pearl": (30, "Rain pearl", "Perla di pioggia", "A drop of spring rain, round and hard as a pearl. Rain slimes leave it, and only in spring.",
                   "Una goccia di pioggia di primavera, tonda e dura come una perla. La lasciano le gelatine di pioggia, e solo in primavera."),
}
TEA = ("four_seasons_tea", 240, [{"effect": "heal", "amount": 120}, {"effect": "fortify", "amount": 40, "ticks": 3600},
                                 {"effect": "ward", "amount": 40, "ticks": 3600}, {"effect": "regen", "amount": 4, "ticks": 3600}],
       "Tea of the four seasons", "Tè delle quattro stagioni",
       "Brewed from a snowflake, a sun drop, an amber leaf and a rain pearl. Heals, fortifies, wards and mends for a whole hour.",
       "Fatto con un fiocco di neve, una goccia di sole, una foglia d'ambra e una perla di pioggia. Cura, fortifica, protegge e risana per un'ora intera.")


def write(path, doc) -> None:
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    texts: dict[str, dict[str, str]] = {"en": {}, "it": {}}
    for kind, (level, hp, atk, element, weak, xp, material, palette, name_en, name_it) in SLIMES.items():
        name = f"slime_{kind}"
        art = ART / f"{name}.json"
        if not art.exists():  # the first file of the art: its palette; art_creatures.py writes the layers
            doc = json.loads((ART / "slime_ice.json").read_text(encoding="utf-8"))
            doc["id"], doc["palette"] = f"base:art/creature/{name}", palette
            write(art, doc)
        path = DATA / "enemies" / f"{name}.json"
        mine = [{"item": f"base:item/{material}", "qty_min": 1, "qty_max": 2, "weight_pm": 800},
                {"item": "base:item/slime_gel", "qty_min": 1, "qty_max": 1, "weight_pm": 500}]
        # the drops other tools add (the common pieces with an affix) are kept after these two
        kept = [d for d in json.loads(path.read_text(encoding="utf-8"))["drops"] if "pick" in d] if path.exists() else []
        write(path, {"$schema": "../../../schemas/enemy.schema.json", "id": f"base:enemy/{name}", "name": f"$i18n:enemy.{name}.name",
                     "level": level, "stats": {"hp": hp, "atk": atk, "def": 2, "mdef": 2, "speed_x100": 250}, "element": element,
                     "sound": "slime", "weaknesses_pm": {weak: 2000}, "xp": xp, "drops": mine + kept, "radius_x100": 35,
                     "behavior": "base:behavior/melee_chaser_basic", "art": f"base:art/creature/{name}"})
        texts["en"][f"enemy.{name}.name"], texts["it"][f"enemy.{name}.name"] = name_en, name_it
    for material, (price, name_en, name_it, desc_en, desc_it) in MATERIALS.items():
        write(DATA / "items" / f"{material}.json", {"$schema": "../../../schemas/item.schema.json", "id": f"base:item/{material}",
                                                     "name": f"$i18n:item.{material}.name", "description": f"$i18n:item.{material}.desc",
                                                     "kind": "material", "rarity": "uncommon", "price": price, "stack_max": 99})
        texts["en"].update({f"item.{material}.name": name_en, f"item.{material}.desc": desc_en})
        texts["it"].update({f"item.{material}.name": name_it, f"item.{material}.desc": desc_it})
    tea, price, effects, name_en, name_it, desc_en, desc_it = TEA
    write(DATA / "items" / f"{tea}.json", {"$schema": "../../../schemas/item.schema.json", "id": f"base:item/{tea}", "name": f"$i18n:item.{tea}.name",
                                           "description": f"$i18n:item.{tea}.desc", "kind": "food", "rarity": "rare", "price": price,
                                           "stack_max": 99, "use": {"effects": effects}})
    texts["en"].update({f"item.{tea}.name": name_en, f"item.{tea}.desc": desc_en})
    texts["it"].update({f"item.{tea}.name": name_it, f"item.{tea}.desc": desc_it})
    for lang in ("en", "it"):
        set_texts("content.json", lang, texts[lang])
    print(f"wrote {len(SLIMES)} creatures of one season, their {len(MATERIALS)} materials and the tea")


if __name__ == "__main__":
    main()
