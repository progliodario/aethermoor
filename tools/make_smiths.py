#!/usr/bin/env python3
"""Writes the smithing of the shopkeepers of the villages (spec 06, "Tempering"; spec 07, the effect `temper`).

Every shopkeeper of a generated village or town keeps an anvil: for a few coins it tempers the affix of the weapon the Guest holds (or
of the armor), as a tempering oil would, and the coins are paid only when there is a piece whose affix rolls. The choice comes right after
the wares (the clients' tests open the shop with the first choice) and shows only with the gold for it.

It changes the role dialogues `data/base/dialogues/role/shopkeeper_<tone>.json` in place (the nodes written here are written again and
the choice keeps its place, so it can be run any number of times) and writes their texts (`roles.json`, it and en).
"""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

GOLD = 60
TONES = ("warm", "mystic", "gruff", "flowery", "stoic", "salty", "grim", "scholarly")
SHARED = {"en": {"dlg.role.smith.ask": f"Could you temper my gear? ({GOLD} gold)"},
          "it": {"dlg.role.smith.ask": f"Potresti temprare la mia attrezzatura? ({GOLD} monete)"}}
# tone: what the shopkeeper says at the anvil, in en and it
WORDS = {
    "en": {"warm": "There, good as new, better even! If it had nothing to temper, love, you paid nothing.",
           "mystic": "The metal remembers the fire, and the fire remembers you. If there was nothing to wake, nothing is owed.",
           "gruff": "Done. If it had no affix, no charge.",
           "flowery": "Behold, polished like the moon on the dunes! And if it had nothing to temper, darling, it is free as the wind!",
           "stoic": "Done. Nothing to temper, nothing to pay.",
           "salty": "Hammered and quenched, mate, like a hull before a storm! No affix, no coin.",
           "grim": "It took the fire. If there was nothing to take it, keep your coin.",
           "scholarly": "The tempering is complete; the variance favours you. Absent an affix, no fee is charged."},
    "it": {"warm": "Ecco, come nuovo, anzi meglio! Se non c'era niente da temprare, caro, non hai pagato niente.",
           "mystic": "Il metallo ricorda il fuoco, e il fuoco ricorda te. Se non c'era niente da svegliare, niente è dovuto.",
           "gruff": "Fatto. Se non aveva affisso, niente da pagare.",
           "flowery": "Ammira, lucido come la luna sulle dune! E se non c'era niente da temprare, tesoro, è gratis come il vento!",
           "stoic": "Fatto. Niente da temprare, niente da pagare.",
           "salty": "Battuto e temprato, amico, come uno scafo prima della tempesta! Niente affisso, niente monete.",
           "grim": "Ha preso il fuoco. Se non c'era niente a prenderlo, tieni le tue monete.",
           "scholarly": "La tempra è completa; la varianza ti è favorevole. In assenza di affisso, nessun compenso è dovuto."},
}


def patch(tone: str) -> None:
    path = DATA / "dialogues" / "role" / f"shopkeeper_{tone}.json"
    raw = path.read_text(encoding="utf-8", newline="")
    doc = json.loads(raw)
    nodes = doc["nodes"]
    old = nodes["menu"]["choices"]
    where = next((i for i, c in enumerate(old) if c.get("next") == "smith"), 1)  # after the wares, the first time
    choices = [c for c in old if c.get("next") != "smith"]
    choice = {"text": "$i18n:dlg.role.smith.ask", "when": {"gold_at_least": GOLD}, "effects": [{"effect": "temper", "gold": GOLD}], "next": "smith"}
    nodes["menu"]["choices"] = choices[:where] + [choice] + choices[where:]
    nodes["smith"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.smith.{tone}.done", "next": "end"}
    newline = "\r\n" if "\r\n" in raw else "\n"
    path.write_text((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").replace("\n", newline), encoding="utf-8", newline="")


def main() -> None:
    for tone in TONES:
        patch(tone)
    for lang in ("en", "it"):
        set_texts("roles.json", lang, {**SHARED[lang], **{f"dlg.smith.{tone}.done": WORDS[lang][tone] for tone in TONES}})
    print(f"wrote the anvils of the shopkeepers of {len(TONES)} regions")


if __name__ == "__main__":
    main()
