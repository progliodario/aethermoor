#!/usr/bin/env python3
"""Writes the four strays of the Guest's cottage, the companions that may join the party (spec 10, "The party"): Biscuit, a caravan dog;
Hoot, an owl of the barn; Sly, a fox that likes berries; and Cinder, an ember slime that sleeps by the anvil and keeps the Guest warm.
Old Tam lets the owner of the cottage take them along (`tools/make_home.py` writes his dialogue with the choices of `PETS`): each choice
recruits its companion (the effect `recruit_companion`, spec 07) and sets the flag `party_<name>`.

It writes the companions (`data/base/companions/<name>.json`) and their texts and Tam's lines about them (it and en), and can be run any
number of times. Then run `make_home.py` (Tam's dialogue) and `make_catalog.py`.
"""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

# name: art, scale, stats, the condition of Tam's choice (besides owning the cottage), what it costs (items removed), and the words
PETS = {
    "biscuit": {"art": "wolf_tawny", "scale_pct": 55, "atk_base": 7, "atk_per_level": 1, "range_x100": 200, "cooldown_ticks": 70,
                "speed_x100": 360, "follow_x100": 200, "when": [], "cost": {},
                "en": ("Biscuit", "Take Biscuit, the dog Odo's caravan left behind",
                       "Biscuit wags everything he has. A dog that was left behind never forgets who took him along."),
                "it": ("Biscotto", "Prendi Biscotto, il cane rimasto indietro dalla carovana di Odo",
                       "Biscotto scodinzola con tutto quello che ha. Un cane rimasto indietro non dimentica chi l'ha portato con sé.")},
    "hoot": {"art": "night_owl", "scale_pct": 60, "atk_base": 8, "atk_per_level": 1, "range_x100": 300, "cooldown_ticks": 90,
             "speed_x100": 400, "follow_x100": 240, "when": [{"level_at_least": 10}], "cost": {},
             "en": ("Hoot", "Take Hoot, the owl of the barn (level 10)",
                    "Hoot looks at you for a long time, then lands on your shoulder. Owls choose; you have been chosen."),
             "it": ("Gufetto", "Prendi Gufetto, il gufo del fienile (livello 10)",
                    "Gufetto ti guarda a lungo, poi ti si posa sulla spalla. I gufi scelgono; sei stato scelto.")},
    "sly": {"art": "dune_fox", "scale_pct": 60, "atk_base": 6, "atk_per_level": 1, "range_x100": 180, "cooldown_ticks": 50,
            "speed_x100": 380, "follow_x100": 200, "when": [], "cost": {"wild_berries": 3},
            "en": ("Sly", "Win over Sly, the fox of the garden (3 wild berries)",
                   "Sly eats the berries one by one, very slowly, and then decides that you are probably all right."),
            "it": ("Furbo", "Conquista Furbo, la volpe del giardino (3 bacche selvatiche)",
                   "Furbo mangia le bacche una per una, molto lentamente, e poi decide che probabilmente vai bene.")},
    "cinder": {"art": "slime_ember", "scale_pct": 70, "atk_base": 9, "atk_per_level": 1, "range_x100": 220, "cooldown_ticks": 80,
               "speed_x100": 300, "follow_x100": 220, "care_bond": 10, "care_ticks": 600, "care_pct": 4, "when": [],
               "cost": {"ember_core": 1},
               "en": ("Cinder", "Wake Cinder, the ember slime by the anvil (1 ember core)",
                      "Cinder swallows the ember core, glows like a sunset and bounces after you. It is warm to stand next to."),
               "it": ("Brace", "Sveglia Brace, la gelatina di brace vicino all'incudine (1 nucleo di brace)",
                      "Brace inghiotte il nucleo di brace, si accende come un tramonto e ti salta dietro. Starle accanto scalda.")},
}
STRAYS = {
    "en": {"strays": "The animals of the cottage",
           "strays_line": "The cottage draws strays, Guest. The hens complain, but they always do. Any of them would follow you, if you asked "
                          "properly. Only one walks with you at a time; the others wait here and keep what they learned.",
           "strays_back": "Not now"},
    "it": {"strays": "Gli animali del cottage",
           "strays_line": "Il cottage attira i randagi, Ospite. Le galline si lamentano, ma lo fanno sempre. Ognuno di loro ti seguirebbe, se "
                          "glielo chiedessi come si deve. Ne cammina con te uno alla volta; gli altri aspettano qui e tengono quello che hanno "
                          "imparato.",
           "strays_back": "Non adesso"},
}
STATS = ("scale_pct", "atk_base", "atk_per_level", "range_x100", "cooldown_ticks", "speed_x100", "follow_x100", "care_bond", "care_ticks",
         "care_pct")


def tam_nodes() -> tuple[dict, dict]:
    """Tam's choice that opens the strays, and the nodes of the strays (for `make_home.tam_dialogue`)."""
    choices = []
    nodes: dict[str, dict] = {"strays": {"type": "say", "speaker": "cottage_keeper_tam", "text": "$i18n:dlg.home.tam.strays_line",
                                         "next": "strays_menu"}}
    for name, pet in PETS.items():
        when = {"all": [{"not": {"flag": f"party_{name}"}}] + pet["when"]
                + [{"has_item": {"item": f"base:item/{item}", "qty": qty}} for item, qty in pet["cost"].items()]}
        choices.append({"text": f"$i18n:dlg.home.tam.take_{name}", "when": when, "next": f"take_{name}"})
        nodes[f"take_{name}"] = {"type": "effects", "effects": [{"effect": "remove_item", "item": f"base:item/{item}", "qty": qty}
                                                                 for item, qty in pet["cost"].items()]
                                 + [{"effect": "recruit_companion", "companion": f"base:companion/{name}"},
                                    {"effect": "set_flag", "flag": f"party_{name}", "value": True}], "next": f"took_{name}"}
        nodes[f"took_{name}"] = {"type": "say", "speaker": "cottage_keeper_tam", "text": f"$i18n:dlg.home.tam.took_{name}", "next": "end"}
    choices.append({"text": "$i18n:dlg.home.tam.strays_back", "next": "menu"})
    nodes["strays_menu"] = {"type": "choice", "choices": choices}
    return {"text": "$i18n:dlg.home.tam.strays", "when": {"flag": "cottage_given"}, "next": "strays"}, nodes


def main() -> None:
    for name, pet in PETS.items():
        doc = {"$schema": "../../../schemas/companion.schema.json", "id": f"base:companion/{name}", "name": f"$i18n:companion.{name}.name",
               "art": f"base:art/creature/{pet['art']}", **{k: pet[k] for k in STATS if k in pet}}
        text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
        (DATA / "companions" / f"{name}.json").write_text(text, encoding="utf-8", newline="\n")
    for lang in ("en", "it"):
        set_texts("content.json", lang, {f"companion.{name}.name": pet[lang][0] for name, pet in PETS.items()})
        core = {f"dlg.home.tam.{k}": v for k, v in STRAYS[lang].items()}
        for name, pet in PETS.items():
            core[f"dlg.home.tam.take_{name}"] = pet[lang][1]
            core[f"dlg.home.tam.took_{name}"] = pet[lang][2]
        set_texts("core.json", lang, core)
    print(f"wrote {len(PETS)} companions that may join the party")


if __name__ == "__main__":
    main()
