#!/usr/bin/env python3
"""Writes the affixed pieces of the regions (spec 06, "Affixes") and gives them to the guardians.

An affix is a block of flat bonuses on a weapon or an armor (`affix`, the same fields as an accessory's): while the piece is worn it adds
them to the derived stats, after the accessory. Every region has an affixed weapon and an affixed armor of its own, which its guardians
(the creatures that drop the accessory of the region) leave one time in five. A piece found on a creature has its affix rolled, from
100 to 160 percent (`affix_roll`, spec 06, "Rolled affixes").

It writes the items `data/base/items/<piece>.json` and their texts, and adds or updates the two drops in the files of the guardians.
It can be run any number of times. Then run `gen_conformance.py` (the vectors read the creatures), `make_catalog.py` and `make_facts.py`.
"""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

DROP_PM = 200
# how strong the affix of a piece found on a creature comes out (spec 06, "Rolled affixes"): never weaker than the one of the shop
ROLL = {"min_pct": 100, "max_pct": 160}
# the accessory every guardian of a region already drops tells the region (spec 06, "Equipment")
REGION_OF_ACCESSORY = {"fang_necklace": "verdalis", "owl_charm": "whisperwood", "golem_amulet": "ironspine", "bat_charm": "ironspine",
                       "sand_charm": "sunscar", "frost_locket": "frostveil", "pearl_pendant": "tidehaven", "ember_ring": "ashen_wastes",
                       "star_brooch": "lumeria"}

# region: [(piece, kind, base stats, affix, price, name en, name it, description en, description it), ...]
PIECES = {
    "verdalis": [
        ("shepherds_blade", "weapon", {"atk": 15, "matk": 0}, {"max_hp": 40}, 1100, "Shepherd's blade", "Lama del pastore",
         "A plain blade blessed at every lambing. Affix: +40 health.", "Una lama semplice benedetta a ogni figliatura. Affisso: +40 di salute."),
        ("meadow_coat", "armor", {"def": 7, "mdef": 5}, {"max_hp": 60}, 1000, "Meadow coat", "Cappotto dei prati",
         "Wool from the hills of Verdalis, warm as a hearth. Affix: +60 health.", "Lana delle colline di Verdalis, calda come un focolare. Affisso: +60 di salute."),
    ],
    "whisperwood": [
        ("owl_eye_dagger", "weapon", {"atk": 15, "matk": 2, "element": "dark"}, {"crit_pm": 60}, 1200, "Owl-eye dagger", "Pugnale occhio di gufo",
         "It sees the gap in any guard. Dark. Affix: +6% critical chance.", "Vede il varco in ogni guardia. Oscurità. Affisso: +6% di colpo critico."),
        ("moss_cloak", "armor", {"def": 6, "mdef": 8}, {"crit_pm": 40, "mdef": 2}, 1100, "Moss cloak", "Mantello di muschio",
         "It grows back where it tears. Affix: +4% critical chance, +2 magic defense.", "Ricresce dove si strappa. Affisso: +4% di colpo critico, +2 di difesa magica."),
    ],
    "ironspine": [
        ("forgeborn_axe", "weapon", {"atk": 20, "matk": 0, "element": "earth"}, {"def": 3, "drain_pm": 80}, 1400, "Forgeborn axe", "Ascia della forgia",
         "Quenched in a mountain spring. Earth. Affix: +3 defense, every hit gives back 8% of its damage.",
         "Temprata in una sorgente di montagna. Terra. Affisso: +3 di difesa, ogni colpo restituisce l'8% del danno."),
        ("forgeborn_plate", "armor", {"def": 11, "mdef": 4}, {"def": 4}, 1300, "Forgeborn plate", "Corazza della forgia",
         "Hammered on the anvils of Ironspine, thick as a door. Affix: +4 defense.", "Battuta sulle incudini di Ironspine, spessa come una porta. Affisso: +4 di difesa."),
    ],
    "sunscar": [
        ("dune_scimitar", "weapon", {"atk": 18, "matk": 0, "element": "fire"}, {"atk": 6}, 1400, "Dune scimitar", "Scimitarra delle dune",
         "The sun is in the steel. Fire. Affix: +6 attack.", "Il sole è nell'acciaio. Fuoco. Affisso: +6 di attacco."),
        ("sandsilk_robe", "armor", {"def": 7, "mdef": 7}, {"crit_pm": 30, "max_hp": 20}, 1200, "Sand-silk robe", "Veste di seta delle sabbie",
         "Light as a breeze, tough as a camel. Affix: +3% critical chance, +20 health.",
         "Leggera come una brezza, resistente come un cammello. Affisso: +3% di colpo critico, +20 di salute."),
    ],
    "frostveil": [
        ("glacier_spear", "weapon", {"atk": 19, "matk": 0, "element": "water"}, {"mdef": 4, "max_hp": 20}, 1400, "Glacier spear", "Lancia del ghiacciaio",
         "Carved from ice that never melts. Water. Affix: +4 magic defense, +20 health.",
         "Scolpita in un ghiaccio che non si scioglie mai. Acqua. Affisso: +4 di difesa magica, +20 di salute."),
        ("snowbear_coat", "armor", {"def": 10, "mdef": 8}, {"mdef": 6, "max_hp": 30}, 1400, "Snowbear coat", "Pelliccia d'orso bianco",
         "The bear did not need it any more. Affix: +6 magic defense, +30 health.",
         "All'orso non serviva più. Affisso: +6 di difesa magica, +30 di salute."),
    ],
    "tidehaven": [
        ("tidecaller_cutlass", "weapon", {"atk": 18, "matk": 0, "element": "water"}, {"drain_pm": 100}, 1400, "Tidecaller cutlass", "Sciabola della marea",
         "It pulls like the tide. Water. Affix: every hit gives back 10% of its damage.",
         "Tira come la marea. Acqua. Affisso: ogni colpo restituisce il 10% del danno."),
        ("sailcloth_vest", "armor", {"def": 8, "mdef": 7}, {"max_hp": 40, "def": 1}, 1100, "Sailcloth vest", "Giubba di tela da vela",
         "Sewn from the sail of a ship that came home. Affix: +40 health, +1 defense.",
         "Cucita con la vela di una nave tornata a casa. Affisso: +40 di salute, +1 di difesa."),
    ],
    "ashen_wastes": [
        ("cinder_brand", "weapon", {"atk": 24, "matk": 0, "element": "fire"}, {"atk": 8, "crit_pm": 30}, 1800, "Cinder brand", "Marchio di cenere",
         "Still warm after a hundred years. Fire. Affix: +8 attack, +3% critical chance.",
         "Ancora calda dopo cent'anni. Fuoco. Affisso: +8 di attacco, +3% di colpo critico."),
        ("ashwalker_mail", "armor", {"def": 12, "mdef": 8}, {"def": 3, "atk": 3}, 1700, "Ashwalker mail", "Maglia del camminatore di cenere",
         "Grey links that drink the heat. Affix: +3 defense, +3 attack.", "Anelli grigi che bevono il calore. Affisso: +3 di difesa, +3 di attacco."),
    ],
    "lumeria": [
        ("starglass_staff", "weapon", {"atk": 4, "matk": 22, "element": "light"}, {"matk": 8}, 1800, "Starglass staff", "Bastone di vetro stellare",
         "A lens for spells. Light. Affix: +8 magic.", "Una lente per gli incantesimi. Luce. Affisso: +8 di magia."),
        ("comet_robe", "armor", {"def": 6, "mdef": 14}, {"matk": 6, "mdef": 3}, 1600, "Comet robe", "Veste della cometa",
         "Embroidered with the path of a comet. Affix: +6 magic, +3 magic defense.",
         "Ricamata con la scia di una cometa. Affisso: +6 di magia, +3 di difesa magica."),
    ],
}


def write_json(path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    texts: dict[str, dict[str, str]] = {"en": {}, "it": {}}
    for pieces in PIECES.values():
        for piece, kind, stats, affix, price, name_en, name_it, desc_en, desc_it in pieces:
            write_json(DATA / "items" / f"{piece}.json", {
                "$schema": "../../../schemas/item.schema.json", "id": f"base:item/{piece}", "name": f"$i18n:item.{piece}.name",
                "description": f"$i18n:item.{piece}.desc", "kind": kind, "rarity": "rare", "price": price, kind: stats, "affix": affix, "affix_roll": ROLL})
            texts["en"].update({f"item.{piece}.name": name_en, f"item.{piece}.desc": desc_en})
            texts["it"].update({f"item.{piece}.name": name_it, f"item.{piece}.desc": desc_it})
    for lang in ("en", "it"):
        set_texts("content.json", lang, texts[lang])
    guardians = 0
    for path in sorted((DATA / "enemies").glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        regions = {REGION_OF_ACCESSORY[d["item"].split("/")[-1]] for d in doc["drops"] if d["item"].split("/")[-1] in REGION_OF_ACCESSORY}
        if len(regions) != 1:
            continue
        ids = [f"base:item/{p[0]}" for p in PIECES[regions.pop()]]
        drops = [d for d in doc["drops"] if d["item"] not in ids]
        drops += [{"item": item, "qty_min": 1, "qty_max": 1, "weight_pm": DROP_PM} for item in ids]
        if drops != doc["drops"]:
            doc["drops"] = drops
            write_json(path, doc)
        guardians += 1
    patch_shops()
    print(f"wrote {sum(len(p) for p in PIECES.values())} affixed pieces, dropped by {guardians} guardians and sold to the friends of each region")


# The shop of every region also keeps its two pieces for its friends (spec 07, "Renown"): the weapon from this renown, the armor from that.
SHOP_RENOWN = (15, 20)


def patch_shops() -> None:
    """Adds the affixed pieces of every region to the `renown_stock` of its shop, in the world data, in place; a second run changes nothing."""
    path = DATA / "worlds" / "overworld.json"
    raw = path.read_text(encoding="utf-8", newline="")
    lines = raw.split("\n")
    for k, line in enumerate(lines):
        for region, pieces in PIECES.items():
            if not line.lstrip().startswith(f'{{ "id": "{region}", "name": "$i18n:region.'):
                continue
            start = line.index('"renown_stock": [') + len('"renown_stock": [')
            end = line.index("]", start)
            entries = line[start:end]
            for (piece, *_rest), renown in zip(pieces, SHOP_RENOWN):
                if f'"base:item/{piece}"' not in entries:
                    entries += f', {{ "item": "base:item/{piece}", "renown": {renown} }}'
            lines[k] = line[:start] + entries + line[end:]
    path.write_text("\n".join(lines), encoding="utf-8", newline="")


if __name__ == "__main__":
    main()
