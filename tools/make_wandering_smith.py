#!/usr/bin/env python3
"""Writes Brannoc, the wandering smith (spec 07, "Travellers"; spec 06, "Tempering"): a second traveller of the roads.

He goes round the eight outposts the other way from Odo, the master of the caravan (`make_caravan.py`): on day `d` he stands at the
outpost of region `CYCLE[-((d - 1) % 8)]` (day 1 Verdalis, then the Ashen Wastes, Lumeria, Sunscar...). He carries an anvil on his
cart: for a few coins he tempers the affix of the weapon the Guest holds (or of the armor), paid only when there is one to temper (the
effect `temper`), cheaper than the shopkeepers. He greets the Guest the first time (the flag `brannoc_met`) and says where he goes next.

It writes his dialogue `data/base/dialogues/npc/brannoc.json`, his texts (it and en) and his line in `npcs` of the world data (a free
cobblestone of every outpost). It can be run any number of times. Then run `make_catalog.py` and `make_facts.py`.
"""
from __future__ import annotations

import json
import re

from make_caravan import OUTPOST
from make_home import CYCLE, say
from make_residents import free_tile
from make_towns import DATA, set_texts

WORLD = DATA / "worlds" / "overworld.json"
KEY = "wandering_smith_brannoc"
GOLD = 40
ROUTE = [CYCLE[(-k) % len(CYCLE)] for k in range(len(CYCLE))]  # the other way round
WORDS = {
    "en": {"speaker": "Brannoc, the wandering smith",
           "hello": "Brannoc. I go round the outposts the other way from Odo: somebody has to mend what his wagons break. My anvil rides with me.",
           "temper": f"Temper my gear ({GOLD} gold)", "where": "Where do you go next?", "bye": "Safe roads.",
           "done": "Quenched and true. If it had no affix to temper, you owe me nothing; I am a smith, not a thief.",
           "next": "Tomorrow the cart rolls to {next}. The road is long, but the anvil does not complain."},
    "it": {"speaker": "Brannoc, il fabbro errante",
           "hello": "Brannoc. Giro gli avamposti nel verso opposto a Odo: qualcuno deve riparare quello che i suoi carri rompono. La mia incudine viaggia con me.",
           "temper": f"Temprami l'attrezzatura ({GOLD} monete)", "where": "Dove vai adesso?", "bye": "Strade sicure.",
           "done": "Temprato e dritto. Se non aveva un affisso da temprare, non mi devi niente; sono un fabbro, non un ladro.",
           "next": "Domani il carro va verso {next}. La strada è lunga, ma l'incudine non si lamenta."},
}


def dialogue() -> dict:
    nodes: dict[str, dict] = {
        "c_known": {"type": "condition", "when": {"flag": "brannoc_met"}, "then": "menu", "else": "hello"},
        "hello": say(KEY, "dlg.brannoc.hello", "met"),
        "met": {"type": "effects", "effects": [{"effect": "set_flag", "flag": "brannoc_met", "value": True}], "next": "menu"},
        "menu": {"type": "choice", "choices": [
            {"text": "$i18n:dlg.brannoc.temper", "when": {"gold_at_least": GOLD}, "effects": [{"effect": "temper", "gold": GOLD}], "next": "done"},
            {"text": "$i18n:dlg.brannoc.where", "next": "d0"},
            {"text": "$i18n:dlg.brannoc.bye", "next": "end"}]},
        "done": say(KEY, "dlg.brannoc.done", "end"),
    }
    for at in range(len(ROUTE)):  # where he goes tomorrow, by the day of the cycle
        if at + 1 < len(ROUTE):
            nodes[f"d{at}"] = {"type": "condition", "when": {"day_mod": {"every": len(ROUTE), "at": at}}, "then": f"s{at}",
                               "else": f"d{at + 1}" if at + 2 < len(ROUTE) else f"s{at + 1}"}
        nodes[f"s{at}"] = say(KEY, f"dlg.brannoc.next_{ROUTE[(at + 1) % len(ROUTE)]}", "end")
    return {"$schema": "../../../../schemas/dialogue.schema.json", "id": "base:dialogue/npc/brannoc", "start": "c_known", "nodes": nodes}


def main() -> None:
    world = json.loads(WORLD.read_text(encoding="utf-8"))
    others = [n for n in world["npcs"] if n["key"] != KEY]
    taken = {(n["dx"], n["dy"]) for n in others} | {tuple(stop) for n in others for stop in n.get("route", [])}
    route = []
    for region in ROUTE:
        landmark = next(lm for lm in world["landmarks"] if lm["id"] == OUTPOST[region])
        stop = free_tile(world, OUTPOST[region], (landmark["dx"], landmark["dy"]), taken)
        taken.add(stop)
        route.append(stop)
    text = json.dumps(dialogue(), indent=2, ensure_ascii=False) + "\n"
    (DATA / "dialogues" / "npc" / "brannoc.json").write_text(text, encoding="utf-8", newline="\n")
    for lang in ("en", "it"):
        names = json.loads((DATA / "i18n" / lang / "content.json").read_text(encoding="utf-8"))
        w = WORDS[lang]
        texts = {f"speaker.{KEY}": w["speaker"], "dlg.brannoc.hello": w["hello"], "dlg.brannoc.temper": w["temper"],
                 "dlg.brannoc.where": w["where"], "dlg.brannoc.bye": w["bye"], "dlg.brannoc.done": w["done"]}
        for region in CYCLE:
            texts[f"dlg.brannoc.next_{region}"] = w["next"].format(next=names[f"region.{region}.name"])
        set_texts("core.json", lang, texts)
    stops = ", ".join(f"[{x}, {y}]" for x, y in route)
    line = (f'{{ "key": "{KEY}", "dialogue": "base:dialogue/npc/brannoc", "variant": "brown", "dx": {route[0][0]}, "dy": {route[0][1]}, '
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
    print(f"wrote Brannoc, with a route of {len(route)} stops")


if __name__ == "__main__":
    main()
