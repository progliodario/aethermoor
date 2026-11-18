#!/usr/bin/env python3
"""Writes the runes and the furniture of the base pack (spec 06, "Runes" and "Furniture").

- the runes `data/base/items/rune_<name>.json`: used from the bag next to an anvil, a rune is engraved on the worn weapon, which then hits
  with its element and a little harder;
- the furniture `data/base/items/<piece>.json`: used from the bag next to an empty place of the Guest's cottage, a piece stands there and
  adds what it adds like a title, every kind once;
- `data/base/home.json`: the prop of the empty places and their reach;
- the texts of all of them, in Italian and English;
- `RECIPES`, read by `make_recipes.py`: every rune and every piece is made at an anvil.

It can be run any number of times. Then run `make_recipes.py`, `make_catalog.py` and `make_facts.py`.
"""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

ANVIL = "base:art/prop/anvil"

# rune: (element, atk, matk, rarity, price, inputs, name en, name it, description en, description it)
RUNES = {
    "rune_ember": ("fire", 6, 4, "uncommon", 220, {"ember_core": 1, "iron_ore": 2},
                   "Ember rune", "Runa di brace",
                   "Engrave it on the weapon you hold, at an anvil: it burns with fire, and hits 6 harder.",
                   "Incidila sull'arma che impugni, a un'incudine: brucia di fuoco, e colpisce 6 più forte."),
    "rune_tide": ("water", 6, 4, "uncommon", 220, {"tide_pearl": 1, "iron_ore": 2},
                  "Tide rune", "Runa della marea",
                  "Engrave it on the weapon you hold, at an anvil: it strikes with water and chills, and hits 6 harder.",
                  "Incidila sull'arma che impugni, a un'incudine: colpisce d'acqua e congela, e colpisce 6 più forte."),
    "rune_gale": ("wind", 6, 4, "uncommon", 220, {"storm_feather": 2, "iron_ore": 2},
                  "Gale rune", "Runa della burrasca",
                  "Engrave it on the weapon you hold, at an anvil: it cuts with wind and stuns, and hits 6 harder.",
                  "Incidila sull'arma che impugni, a un'incudine: taglia di vento e stordisce, e colpisce 6 più forte."),
    "rune_stone": ("earth", 8, 0, "uncommon", 240, {"golem_core": 1, "slate_shard": 2},
                   "Stone rune", "Runa di pietra",
                   "Engrave it on the weapon you hold, at an anvil: it falls like a landslide, and hits 8 harder.",
                   "Incidila sull'arma che impugni, a un'incudine: cade come una frana, e colpisce 8 più forte."),
    "rune_dawn": ("light", 6, 6, "rare", 280, {"star_dust": 2, "iron_ore": 2},
                  "Dawn rune", "Runa dell'alba",
                  "Engrave it on the weapon you hold, at an anvil: it shines with light and weakens, and hits 6 harder.",
                  "Incidila sull'arma che impugni, a un'incudine: splende di luce e indebolisce, e colpisce 6 più forte."),
    "rune_dusk": ("dark", 6, 6, "rare", 280, {"shade_wisp": 2, "iron_ore": 2},
                  "Dusk rune", "Runa del crepuscolo",
                  "Engrave it on the weapon you hold, at an anvil: it bites with darkness and weakens, and hits 6 harder.",
                  "Incidila sull'arma che impugni, a un'incudine: morde di tenebra e indebolisce, e colpisce 6 più forte."),
    "rune_might": ("none", 12, 0, "rare", 320, {"iron_ore": 6, "magma_shard": 1},
                   "Rune of might", "Runa della forza",
                   "Engrave it on the weapon you hold, at an anvil: the weapon keeps its own element, and hits 12 harder.",
                   "Incidila sull'arma che impugni, a un'incudine: l'arma tiene il suo elemento, e colpisce 12 più forte."),
}

# piece: (prop art, what it adds, price, inputs, name en, name it, description en, description it)
FURNITURE = {
    "quilt_bed": ("bed", {"xp_pct": 10}, 260, {"wood_log": 6, "boar_hide": 2, "hen_feather": 4},
                  "Quilted bed", "Letto con la trapunta",
                  "Place it in the cottage. You sleep like a child and wake up wiser: 10% more experience from every victory.",
                  "Posalo nel cottage. Dormi come un bambino e ti svegli più saggio: 10% di esperienza in più da ogni vittoria."),
    "weapon_rack": ("weapon_rack", {"atk_pct": 5}, 240, {"wood_log": 4, "iron_ore": 3},
                    "Weapon rack", "Rastrelliera",
                    "Place it in the cottage. A blade kept well cuts well: your hits are 5% stronger.",
                    "Posala nel cottage. Una lama tenuta bene taglia bene: i tuoi colpi sono più forti del 5%."),
    "bookshelf": ("bookshelf", {"fine_pm": 50}, 240, {"wood_log": 5, "owl_feather": 2},
                  "Bookshelf", "Libreria",
                  "Place it in the cottage. Old manuals of every craft: 5% more chance that what you make comes out fine.",
                  "Posala nel cottage. Vecchi manuali di ogni mestiere: 5% di probabilità in più che ciò che crei riesca pregiato."),
    "herb_rack": ("herb_rack", {"gather_bonus": 1}, 200, {"wood_log": 3, "healing_herb": 4, "dry_branch": 2},
                  "Drying rack", "Essiccatoio",
                  "Place it in the cottage. Herbs dried the right way teach you where to look: one more of everything you gather.",
                  "Posalo nel cottage. Le erbe seccate come si deve ti insegnano dove cercare: uno in più di tutto ciò che raccogli."),
    "training_dummy": ("training_dummy", {"parry_bonus": 4}, 180, {"wood_log": 3, "tawny_fur": 2, "dry_branch": 3},
                       "Training dummy", "Manichino",
                       "Place it in the cottage. It never hits back, which is the point: your parry lasts a little longer.",
                       "Posalo nel cottage. Non risponde mai, ed è proprio questo il bello: la tua parata dura un po' di più."),
    "work_table": ("work_table", {"craft_bonus": 1}, 300, {"wood_log": 6, "stone_chunk": 4, "iron_ore": 2},
                   "Work table", "Banco da lavoro",
                   "Place it in the cottage. Room for every tool, at last: every recipe gives one more.",
                   "Posalo nel cottage. Finalmente posto per ogni attrezzo: ogni ricetta ne dà uno in più."),
}

# What make_recipes.py writes: recipe id -> (output item, quantity, inputs); all of them at an anvil.
RECIPES = {name: (name, 1, spec[5]) for name, spec in RUNES.items()}
RECIPES.update({name: (name, 1, spec[3]) for name, spec in FURNITURE.items()})

HOME = {"$schema": "../../schemas/home.schema.json", "id": "base:home/cottage", "spot": "base:art/prop/furniture_spot", "reach_x100": 150}


def write_json(path, doc) -> None:
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    texts: dict[str, dict[str, str]] = {"en": {}, "it": {}}
    for name, (element, atk, matk, rarity, price, _inputs, name_en, name_it, desc_en, desc_it) in RUNES.items():
        rune = {**({"element": element} if element != "none" else {}), "atk": atk, **({"matk": matk} if matk else {}), "station": ANVIL}
        write_json(DATA / "items" / f"{name}.json", {"$schema": "../../../schemas/item.schema.json", "id": f"base:item/{name}",
                                                       "name": f"$i18n:item.{name}.name", "description": f"$i18n:item.{name}.desc",
                                                       "kind": "rune", "rarity": rarity, "price": price, "stack_max": 9, "rune": rune})
        texts["en"].update({f"item.{name}.name": name_en, f"item.{name}.desc": desc_en})
        texts["it"].update({f"item.{name}.name": name_it, f"item.{name}.desc": desc_it})
    for name, (art, adds, price, _inputs, name_en, name_it, desc_en, desc_it) in FURNITURE.items():
        write_json(DATA / "items" / f"{name}.json", {"$schema": "../../../schemas/item.schema.json", "id": f"base:item/{name}",
                                                       "name": f"$i18n:item.{name}.name", "description": f"$i18n:item.{name}.desc",
                                                       "kind": "furniture", "rarity": "uncommon", "price": price, "stack_max": 3,
                                                       "furniture": {"art": f"base:art/prop/{art}", **adds}})
        texts["en"].update({f"item.{name}.name": name_en, f"item.{name}.desc": desc_en})
        texts["it"].update({f"item.{name}.name": name_it, f"item.{name}.desc": desc_it})
    write_json(DATA / "home.json", HOME)
    for lang in ("en", "it"):
        set_texts("content.json", lang, texts[lang])
    print(f"wrote {len(RUNES)} runes, {len(FURNITURE)} pieces of furniture and the home")


if __name__ == "__main__":
    main()
