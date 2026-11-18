#!/usr/bin/env python3
"""Writes the tags of the base pack (data/base/tags.json), their names and what they do (spec 11, "Tags").

A tag is a trait the game reads from how one plays: it is earned like a title, when a counter reaches its number, but it does not
work by itself: the player wears one tag at a time (`Y` on desktop, the `Tag` button of the journal on Android) and only that one
adds its effect, a stronger one than a title's. Run it after changing the table here; then run `make_catalog.py` and `make_facts.py`.
"""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

# id: (kind, count, what it adds, (name, what it does) in en and it); the order is the order the player cycles through them
TAGS = {
    "berserker": ("kills", 60, {"atk_pct": 15},
                  {"en": ("Berserker", "Sixty victories. Your hits are 15% stronger."),
                   "it": ("Berserker", "Sessanta vittorie. I tuoi colpi sono più forti del 15%.")}),
    "sentinel": ("parried", 20, {"parry_bonus": 10, "atk_pct": 5},
                 {"en": ("Sentinel", "Twenty attacks parried. Your parry lasts much longer, and you hit 5% harder."),
                  "it": ("Sentinella", "Venti attacchi parati. La tua parata dura molto di più, e colpisci più forte del 5%.")}),
    "pathfinder": ("gathered", 50, {"gather_bonus": 2},
                   {"en": ("Pathfinder", "Fifty things gathered. Two more of everything you gather."),
                    "it": ("Cercatore", "Cinquanta raccolte. Due in più di tutto ciò che raccogli.")}),
    "artificer": ("crafted", 15, {"craft_bonus": 1, "fine_pm": 150},
                  {"en": ("Artificer", "Fifteen things made. One more of every recipe, and 15% more fine work."),
                   "it": ("Artefice", "Quindici creazioni. Uno in più di ogni ricetta, e il 15% in più di opere pregiate.")}),
    "epicure": ("used", 30, {"xp_pct": 15},
                {"en": ("Epicure", "Thirty things eaten or drunk. 15% more experience from every victory."),
                 "it": ("Epicureo", "Trenta cose mangiate o bevute. Il 15% di esperienza in più da ogni vittoria.")}),
    "grower": ("harvested", 10, {"gather_bonus": 2, "xp_pct": 5},
               {"en": ("Grower", "Ten harvests. Two more of everything you gather, and 5% more experience."),
                "it": ("Coltivatore", "Dieci raccolti. Due in più di tutto ciò che raccogli, e il 5% di esperienza in più.")}),
    "naturalist": ("species", 15, {"xp_pct": 20},
                   {"en": ("Naturalist", "Fifteen kinds of creature defeated. 20% more experience from every victory."),
                    "it": ("Naturalista", "Quindici specie di creature sconfitte. Il 20% di esperienza in più da ogni vittoria.")}),
    "champion": ("quests", 25, {"atk_pct": 8, "xp_pct": 10},
                 {"en": ("Champion of the People", "Twenty-five quests finished. Your hits are 8% stronger, and 10% more experience."),
                  "it": ("Campione del popolo", "Venticinque missioni finite. I tuoi colpi sono più forti dell'8%, e il 10% di esperienza in più.")}),
}


def main() -> None:
    tags = []
    texts: dict[str, dict[str, str]] = {"en": {}, "it": {}}
    for tag_id, (kind, count, adds, words) in TAGS.items():
        tags.append({"id": tag_id, "name": f"$i18n:tag.{tag_id}", "kind": kind, "count": count, **adds})
        for lang in ("en", "it"):
            name, does = words[lang]
            texts[lang].update({f"tag.{tag_id}": name, f"tag.{tag_id}.desc": does})
    doc = {"$schema": "../../schemas/tags.schema.json", "id": "base:tags/all", "tags": tags}
    (DATA / "tags.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    for lang in ("en", "it"):
        set_texts("content.json", lang, texts[lang])
    print(f"wrote {len(tags)} tags")


if __name__ == "__main__":
    main()
