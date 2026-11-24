#!/usr/bin/env python3
"""Writes Garrick, the carpenter of Fenwick, who works at the annex of the Guest's cottage (spec 06, "Rooms"; spec 07, "People of the
towns"): for the owner of the Guest's cottage (the flag
`cottage_given`) he fixes up the three rooms of its annex, one at a time, each for the price of `ROOMS` of `tools/make_furnishings.py`
(gold and materials, paid by the effects of his dialogue), and sets the flag of the room, which makes its places places of the home.

It writes his dialogue, his texts (it and en) and his line in the world data (`npcs`), and can be run any number of times. Run
`make_furnishings.py` first (the rooms of `home.json`), then `make_catalog.py`.
"""
from __future__ import annotations

import json
import re

from make_furnishings import ROOMS
from make_towns import DATA, set_texts

WORLD = DATA / "worlds" / "overworld.json"
KEY = "fenwick_carpenter_garrick"
FILE = "garrick"
VARIANT = "brown"
AT = (91, 45)  # the tile he stands on, from the center of the world: at the cottage, south of the road, by the annex
# the names of the materials in the choices, en and it
MATERIALS = {"wood_log": ("logs", "ceppi"), "iron_ore": ("iron ores", "minerali di ferro"), "pine_resin": ("pine resins", "resine di pino"),
             "stone_chunk": ("stone chunks", "pezzi di pietra"), "wildflowers": ("wildflowers", "fiori di campo")}
WORDS = {
    "en": {"speaker": "Garrick, carpenter of Fenwick",
           "stranger": "Garrick, carpenter of Fenwick. I build and I mend. This annex here: nobody ever finished it, three rooms of bare boards "
                       "and draughts. Whoever gets this house, I am the one to see.",
           "owner": "The Guest of the cottage! The annex is sound, but the rooms are bare boards and draughts. I can fix them up, one at a "
                    "time. Bring the materials and the coin, and I bring the hammer.",
           "prices": "How much is it?", "bye": "Goodbye, Garrick.",
           "price_list": "The workshop: 600 gold, twelve logs and six iron ores. The study: 900 gold, ten logs and four pine resins. The "
                         "greenhouse: 1200 gold, ten stone chunks and eight bunches of wildflowers. Each has two places for furniture.",
           "done": "All three rooms are finished. Best annex this side of the river, if I may say so.",
           "fix": "Fix up {room} ({gold} gold, {items})",
           "built": "There: {room} is yours. Two places for furniture, and not a single draught. Make something for it at your anvil."},
    "it": {"speaker": "Garrick, falegname di Fenwick",
           "stranger": "Garrick, falegname di Fenwick. Costruisco e aggiusto. Questo annesso, qui: nessuno l'ha mai finito, tre stanze di assi "
                       "nude e spifferi. Chi avrà questa casa, deve parlare con me.",
           "owner": "L'Ospite del cottage! L'annesso è solido, ma le stanze sono assi nude e spifferi. Posso sistemarle, una alla volta. "
                    "Porta i materiali e le monete, al martello penso io.",
           "prices": "Quanto costa?", "bye": "Arrivederci, Garrick.",
           "price_list": "Il laboratorio: 600 monete, dodici ceppi e sei minerali di ferro. Lo studio: 900 monete, dieci ceppi e quattro "
                         "resine di pino. La serra: 1200 monete, dieci pezzi di pietra e otto mazzi di fiori di campo. Ognuna ha due posti "
                         "per i mobili.",
           "done": "Tutte e tre le stanze sono finite. Il miglior annesso da questa parte del fiume, se posso dirlo.",
           "fix": "Sistema {room} ({gold} monete, {items})",
           "built": "Ecco fatto: {room} adesso è a posto. Due posti per i mobili, e neanche uno spiffero. Costruisci qualcosa per la stanza "
                    "alla tua incudine."},
}


def say(key: str, nxt: str) -> dict:
    return {"type": "say", "speaker": KEY, "text": f"$i18n:dlg.home.garrick.{key}", "next": nxt}


def dialogue() -> dict:
    nodes: dict[str, dict] = {
        "c_owner": {"type": "condition", "when": {"flag": "cottage_given"}, "then": "c_done", "else": "stranger"},
        "stranger": say("stranger", "end"),
        "c_done": {"type": "condition", "when": {"all": [{"flag": f"room_{room}"} for room, *_ in ROOMS]}, "then": "done", "else": "owner"},
        "done": say("done", "end"),
        "owner": say("owner", "menu"),
        "prices": say("price_list", "menu"),
    }
    choices = []
    for room, gold, items, _en, _it in ROOMS:
        when = {"all": [{"not": {"flag": f"room_{room}"}}, {"gold_at_least": gold}]
                + [{"has_item": {"item": f"base:item/{item}", "qty": qty}} for item, qty in items.items()]}
        choices.append({"text": f"$i18n:dlg.home.garrick.fix_{room}", "when": when, "next": f"build_{room}"})
        nodes[f"build_{room}"] = {"type": "effects", "effects": [{"effect": "spend_gold", "amount": gold}]
                                  + [{"effect": "remove_item", "item": f"base:item/{item}", "qty": qty} for item, qty in items.items()]
                                  + [{"effect": "set_flag", "flag": f"room_{room}", "value": True}], "next": f"built_{room}"}
        nodes[f"built_{room}"] = say(f"built_{room}", "end")
    choices += [{"text": "$i18n:dlg.home.garrick.prices", "next": "prices"}, {"text": "$i18n:dlg.home.garrick.bye", "next": "end"}]
    nodes["menu"] = {"type": "choice", "choices": choices}
    return {"$schema": "../../../../schemas/dialogue.schema.json", "id": f"base:dialogue/npc/{FILE}", "start": "c_owner", "nodes": nodes}


def texts(lang: str) -> dict[str, str]:
    w = WORDS[lang]
    out = {f"speaker.{KEY}": w["speaker"]}
    out.update({f"dlg.home.garrick.{k}": w[k] for k in ("stranger", "owner", "prices", "bye", "price_list", "done")})
    for room, gold, items, name_en, name_it in ROOMS:
        name = name_en if lang == "en" else name_it
        listed = ", ".join(f"{qty} {MATERIALS[item][0 if lang == 'en' else 1]}" for item, qty in items.items())
        out[f"dlg.home.garrick.fix_{room}"] = w["fix"].format(room=name, gold=gold, items=listed)
        built = w["built"].format(room=name)
        out[f"dlg.home.garrick.built_{room}"] = built[0].upper() + built[1:]
    return out


def patch_world() -> None:
    """Adds Garrick to `npcs` of the world data, one line, after the last person; a second run changes nothing."""
    raw = WORLD.read_text(encoding="utf-8", newline="")
    line = f'{{ "key": "{KEY}", "dialogue": "base:dialogue/npc/{FILE}", "variant": "{VARIANT}", "dx": {AT[0]}, "dy": {AT[1]} }}'
    if f'"key": "{KEY}"' in raw:
        raw = re.sub(r'\{ "key": "' + KEY + r'"[^\n]*\}', line, raw)
    else:
        last = raw.rindex('{ "key": "')
        end = raw.index("}", last) + 1
        indent = raw[raw.rindex("\n", 0, last) + 1:last]
        raw = raw[:end] + ",\n" + indent + line + raw[end:]
    WORLD.write_text(raw, encoding="utf-8", newline="")


def main() -> None:
    path = DATA / "dialogues" / "npc" / f"{FILE}.json"
    path.write_text(json.dumps(dialogue(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    for lang in ("en", "it"):
        set_texts("core.json", lang, texts(lang))
    patch_world()
    print(f"wrote Garrick the carpenter and the {len(ROOMS)} rooms he fixes up")


if __name__ == "__main__":
    main()
