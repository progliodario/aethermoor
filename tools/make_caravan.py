#!/usr/bin/env python3
"""Writes Odo, the master of the caravan (spec 07, "Travellers"): a merchant who really travels.

His wagons go round the eight outposts, one a day, in the cycle of the pedlars (`make_home.CYCLE`): on day `d` he stands at the outpost
of region `CYCLE[(d - 1) % 8]` (the `route` of his line in `npcs`), and he sells, at the plain price, the goods of the region he goes to
the next day (`open_shop` with a `region`). He greets the Guest the first time (the flag `odo_met`).

It writes his dialogue `data/base/dialogues/npc/odo.json`, his texts (it and en) and his line in `npcs` of the world data (a free
cobblestone of every outpost, next to its pedlar). It can be run any number of times. Then run `make_catalog.py` and `make_facts.py`.
"""
from __future__ import annotations

import json
import re

from make_home import CYCLE, say
from make_residents import free_tile
from make_towns import DATA, set_texts

WORLD = DATA / "worlds" / "overworld.json"
KEY = "caravan_master_odo"
OUTPOST = {"verdalis": "verdalis_outpost", "whisperwood": "whisperwood_outpost", "ironspine": "ironspine_outpost",
           "tidehaven": "tidehaven_outpost", "frostveil": "frostveil_outpost", "sunscar": "sunscar_outpost",
           "lumeria": "lumeria_outpost", "ashen_wastes": "ashen_outpost"}
WORDS = {
    "en": {"speaker": "Odo, master of the caravan",
           "hello": "Odo of the long road, at your service. My wagons never sleep two nights in the same place: every day another outpost, all eight and round again. Look for me on the roads.",
           "day": "Tomorrow we roll to {next}, so the wagons are full of its goods. Buy them here at the price they cost there; I make my coin on the road, not on you."},
    "it": {"speaker": "Odo, capo della carovana",
           "hello": "Odo della lunga strada, al tuo servizio. I miei carri non dormono mai due notti nello stesso posto: ogni giorno un altro avamposto, tutti e otto e di nuovo da capo. Cercami lungo le strade.",
           "day": "Domani si riparte verso {next}, quindi i carri sono pieni delle sue merci. Comprale qui al prezzo che costano là; io guadagno sulla strada, non su di te."},
}


def dialogue() -> dict:
    nodes: dict[str, dict] = {
        "c_known": {"type": "condition", "when": {"flag": "odo_met"}, "then": "d0", "else": "hello"},
        "hello": say(KEY, "dlg.caravan.odo.hello", "met"),
        "met": {"type": "effects", "effects": [{"effect": "set_flag", "flag": "odo_met", "value": True}], "next": "d0"},
    }
    for at in range(len(CYCLE)):
        bound = CYCLE[(at + 1) % len(CYCLE)]  # where he goes tomorrow: its goods are on the wagons
        if at + 1 < len(CYCLE):
            nodes[f"d{at}"] = {"type": "condition", "when": {"day_mod": {"every": len(CYCLE), "at": at}}, "then": f"s{at}",
                               "else": f"d{at + 1}" if at + 2 < len(CYCLE) else f"s{at + 1}"}
        nodes[f"s{at}"] = say(KEY, f"dlg.caravan.odo.{bound}", f"shop{at}")
        nodes[f"shop{at}"] = {"type": "effects", "effects": [{"effect": "open_shop", "region": bound, "markup_pct": 100}], "next": "end"}
    return {"$schema": "../../../../schemas/dialogue.schema.json", "id": "base:dialogue/npc/odo", "start": "c_known", "nodes": nodes}


def main() -> None:
    world = json.loads(WORLD.read_text(encoding="utf-8"))
    others = [n for n in world["npcs"] if n["key"] != KEY]
    taken = {(n["dx"], n["dy"]) for n in others}
    pedlars = [(n["dx"], n["dy"]) for n in others if n["key"].startswith("pedlar_")]
    route = []
    for region in CYCLE:
        landmark = next(lm for lm in world["landmarks"] if lm["id"] == OUTPOST[region])
        near = next(p for p in pedlars if abs(p[0] - landmark["dx"]) < 16 and abs(p[1] - landmark["dy"]) < 16)
        stop = free_tile(world, OUTPOST[region], near, taken)
        taken.add(stop)
        route.append(stop)
    text = json.dumps(dialogue(), indent=2, ensure_ascii=False) + "\n"
    (DATA / "dialogues" / "npc" / "odo.json").write_text(text, encoding="utf-8", newline="\n")
    for lang in ("en", "it"):
        names = json.loads((DATA / "i18n" / lang / "content.json").read_text(encoding="utf-8"))
        texts = {f"speaker.{KEY}": WORDS[lang]["speaker"], "dlg.caravan.odo.hello": WORDS[lang]["hello"]}
        for region in CYCLE:
            texts[f"dlg.caravan.odo.{region}"] = WORDS[lang]["day"].format(next=names[f"region.{region}.name"])
        set_texts("core.json", lang, texts)
    stops = ", ".join(f"[{x}, {y}]" for x, y in route)
    line = (f'{{ "key": "{KEY}", "dialogue": "base:dialogue/npc/odo", "variant": "ochre", "dx": {route[0][0]}, "dy": {route[0][1]}, '
            f'"route": [{stops}] }}')
    raw = WORLD.read_text(encoding="utf-8", newline="")
    if f'"key": "{KEY}"' in raw:
        raw = re.sub(r'\{ "key": "' + KEY + r'"[^\n]*\}', line, raw)
    else:
        last = raw.rindex('{ "key": "')
        end = raw.index("\n", last)
        indent = raw[raw.rindex("\n", 0, last) + 1:last]
        raw = raw[:end] + ",\n" + indent + line + raw[end:]  # the last person of the list has no comma after it
    WORLD.write_text(raw, encoding="utf-8", newline="")
    print(f"wrote Odo, with a route of {len(route)} stops")


if __name__ == "__main__":
    main()
