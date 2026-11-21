#!/usr/bin/env python3
"""Writes the common pieces with an affix (spec 06, "Rolled affixes"; spec 05, "Loot") and gives them to the creatures of the fauna.

Three tiers of plain pieces, a weapon and an armor each (the iron sword and the leather vest; the knight's sword and the chain mail; the
claymore and the knight's plate), come with four affixes each: of vigor (health), of might (attack), of keenness (critical chance) and
of the leech (a drain). That is twenty-four items, `base:item/<base>_<affix>`, rolled from 100 to 150 percent when found. Every creature
of the fauna of the regions (and every seasonal visitor) leaves one of the eight pieces of its tier, by its level, one time in thirty: a
drop "one of a list" (`pick`), so the piece is drawn among the eight.

Twelve rare pieces have **two affixes** (an affix block with the bonuses of both, at the top tier): the claymore and the knight's plate
of every pair of the four, `base:item/<base>_<affix>_<affix>`, rolled from 100 to 150 percent. Every guardian (and every Echo) leaves one
of the twelve one time in four, a drop "one of a list" too.

It writes the items and their texts, and adds or updates the drops in the files of the creatures. It can be run any number of times.
Then run `gen_conformance.py`, `make_catalog.py` and `make_facts.py`.
"""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

DROP_PM = 30
ROLL = {"min_pct": 100, "max_pct": 150}
# tier: (the highest level of a creature of the tier, weapon, armor)
TIERS = [(4, "iron_sword", "leather_vest"), (8, "knight_sword", "chain_mail"), (99, "claymore", "knight_plate")]
# affix: (the bonus by tier, name en, name it, what it does en, it)
AFFIXES = {
    "vigor": ([{"max_hp": 30}, {"max_hp": 60}, {"max_hp": 90}], "{base} of vigor", "{base} del vigore", "+{max_hp} health", "+{max_hp} di salute"),
    "might": ([{"atk": 3}, {"atk": 5}, {"atk": 8}], "{base} of might", "{base} della forza", "+{atk} attack", "+{atk} di attacco"),
    "keenness": ([{"crit_pm": 40}, {"crit_pm": 60}, {"crit_pm": 80}], "{base} of keenness", "{base} dell'acume",
                 "+{crit}% critical chance", "+{crit}% di colpo critico"),
    "leech": ([{"drain_pm": 60}, {"drain_pm": 80}, {"drain_pm": 100}], "{base} of the leech", "{base} della sanguisuga",
              "every hit gives back {drain}% of its damage", "ogni colpo restituisce il {drain}% del danno"),
}
RARITY = ["uncommon", "rare", "rare"]
DOUBLE_PM = 250
DOUBLE_BASES = ("claymore", "knight_plate")
PAIRS = [("vigor", "might"), ("vigor", "keenness"), ("vigor", "leech"), ("might", "keenness"), ("might", "leech"), ("keenness", "leech")]
# the name of a piece with two affixes: {base} {first} and {second}
DOUBLE_NAMES = {"en": "{base} of {first} and {second}", "it": "{base} {first} e {second}"}
WORDS = {"en": {"vigor": "vigor", "might": "might", "keenness": "keenness", "leech": "the leech"},
         "it": {"vigor": "del vigore", "might": "della forza", "keenness": "dell'acume", "leech": "della sanguisuga"}}


def write_json(path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def pieces_of(tier: int) -> list[str]:
    _top, weapon, armor = TIERS[tier]
    return [f"{base}_{affix}" for base in (weapon, armor) for affix in AFFIXES]


def main() -> None:
    names = {lang: load(DATA / "i18n" / lang / "content.json") for lang in ("en", "it")}
    texts: dict[str, dict[str, str]] = {"en": {}, "it": {}}
    for tier, (_top, weapon, armor) in enumerate(TIERS):
        for base in (weapon, armor):
            doc = load(DATA / "items" / f"{base}.json")
            for affix, (bonuses, name_en, name_it, what_en, what_it) in AFFIXES.items():
                bonus = bonuses[tier]
                piece = f"{base}_{affix}"
                write_json(DATA / "items" / f"{piece}.json", {
                    "$schema": "../../../schemas/item.schema.json", "id": f"base:item/{piece}", "name": f"$i18n:item.{piece}.name",
                    "description": f"$i18n:item.{piece}.desc", "kind": doc["kind"], "rarity": RARITY[tier], "price": doc["price"] * 2,
                    doc["kind"]: doc[doc["kind"]], "affix": bonus, "affix_roll": ROLL})
                values = {"max_hp": bonus.get("max_hp", 0), "atk": bonus.get("atk", 0), "crit": bonus.get("crit_pm", 0) // 10,
                          "drain": bonus.get("drain_pm", 0) // 10}
                for lang, name, what, label in (("en", name_en, what_en, "Affix"), ("it", name_it, what_it, "Affisso")):
                    plain = names[lang][f"item.{base}.name"]
                    texts[lang][f"item.{piece}.name"] = name.format(base=plain)
                    texts[lang][f"item.{piece}.desc"] = f"{names[lang][f'item.{base}.desc']} {label}: {what.format(**values)}."
    doubles = []
    for base in DOUBLE_BASES:  # the pieces with two affixes, at the top tier
        doc = load(DATA / "items" / f"{base}.json")
        for first, second in PAIRS:
            piece = f"{base}_{first}_{second}"
            bonus = {**AFFIXES[first][0][-1], **AFFIXES[second][0][-1]}
            write_json(DATA / "items" / f"{piece}.json", {
                "$schema": "../../../schemas/item.schema.json", "id": f"base:item/{piece}", "name": f"$i18n:item.{piece}.name",
                "description": f"$i18n:item.{piece}.desc", "kind": doc["kind"], "rarity": "epic", "price": doc["price"] * 3,
                doc["kind"]: doc[doc["kind"]], "affix": bonus, "affix_roll": ROLL})
            values = {"max_hp": bonus.get("max_hp", 0), "atk": bonus.get("atk", 0), "crit": bonus.get("crit_pm", 0) // 10,
                      "drain": bonus.get("drain_pm", 0) // 10}
            for lang, label, which in (("en", "Two affixes", 3), ("it", "Due affissi", 4)):
                plain = names[lang][f"item.{base}.name"]
                texts[lang][f"item.{piece}.name"] = DOUBLE_NAMES[lang].format(base=plain, first=WORDS[lang][first], second=WORDS[lang][second])
                what = ", ".join(AFFIXES[a][which].format(**values) for a in (first, second))
                texts[lang][f"item.{piece}.desc"] = f"{names[lang][f'item.{base}.desc']} {label}: {what}."
            doubles.append(f"base:item/{piece}")
    for lang in ("en", "it"):
        set_texts("content.json", lang, texts[lang])
    world = load(DATA / "worlds" / "overworld.json")
    fauna = {e["enemy"] for region in world["regions"] for e in region["fauna"]}
    fauna |= {v["enemy"] for region in world["regions"] for e in region["fauna"] for v in e.get("seasons", [])}
    every = {f"base:item/{p}" for tier in range(len(TIERS)) for p in pieces_of(tier)}
    changed = 0
    for enemy in sorted(fauna):
        path = DATA / "enemies" / (enemy.split("/")[-1] + ".json")
        doc = load(path)
        tier = next(i for i, (top, *_r) in enumerate(TIERS) if doc["level"] <= top)
        ids = [f"base:item/{p}" for p in pieces_of(tier)]
        drops = [d for d in doc["drops"] if d["item"] not in every]
        drops.append({"item": ids[0], "pick": ids[1:], "qty_min": 1, "qty_max": 1, "weight_pm": DROP_PM})
        if drops != doc["drops"]:
            doc["drops"] = drops
            write_json(path, doc)
            changed += 1
    guardians = 0
    for path in sorted((DATA / "enemies").glob("*.json")):
        doc = load(path)
        if not str(doc.get("behavior", "")).endswith("guardian"):
            continue
        guardians += 1
        drops = [d for d in doc["drops"] if d["item"] not in doubles]
        drops.append({"item": doubles[0], "pick": doubles[1:], "qty_min": 1, "qty_max": 1, "weight_pm": DOUBLE_PM})
        if drops != doc["drops"]:
            doc["drops"] = drops
            write_json(path, doc)
            changed += 1
    print(f"wrote {len(every)} common pieces with an affix, dropped by {len(fauna)} creatures of the fauna, and {len(doubles)} with two,"
          f" dropped by {guardians} guardians ({changed} files changed)")


if __name__ == "__main__":
    main()
