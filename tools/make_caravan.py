#!/usr/bin/env python3
"""Writes Odo, the master of the caravan (spec 07, "Travellers"): a merchant who really travels.

His wagons go round the eight outposts, one a day, in the cycle of the pedlars (`make_home.CYCLE`): on day `d` he stands at the outpost
of region `CYCLE[(d - 1) % 8]` (the `route` of his line in `npcs`), and he sells, at the plain price, the goods of the region he goes to
the next day (`open_shop` with a `region`). He greets the Guest the first time (the flag `odo_met`), and has three errands for the
caravan, one after the other (`base:quest/side/way_odo_*`, they count for the Ring of Wayfarers): what the wagons need on the road.

It writes his dialogue `data/base/dialogues/npc/odo.json`, his texts (it and en) and his line in `npcs` of the world data (a free
cobblestone of every outpost, next to its pedlar). It can be run any number of times. Then run `make_catalog.py` and `make_facts.py`.
"""
from __future__ import annotations

import json
import re

from make_home import CYCLE, quest, say
from make_residents import free_tile
from make_towns import DATA, set_texts

# how the travellers walk between their stops (spec 07, "Travellers walk"): in by six, out at six, 1/16 of a tile per tick
WALK = {"arrive_pm": 250, "depart_pm": 750, "speed_x256": 16}

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


# The errands of the caravan (spec 07, "Travellers"): id, item, count, rewards, (name, journal, offer, busy, thanks) in en and it
ERRANDS = [
    ("way_odo_axles", "wood_log", 12, [("add_xp", 80), ("add_gold", 120), ("add_item", "rune_gale", 1)],
     {"en": ("Axles for the Wagons", "Odo's wagons need new axles before the next mountain road. Bring him twelve logs; he is at a different outpost every day.",
             "One of my axles groaned all the way here. Twelve good logs and I can spare you a rune I picked up on the coast. Will you?",
             "Twelve logs, friend. Find me at any outpost: I am never far, only elsewhere.",
             "Oak, and dry. The wagons will sing. Here, the rune: it pulls like a gale."),
      "it": ("Assi per i carri", "I carri di Odo hanno bisogno di assi nuovi prima della prossima strada di montagna. Portagli dodici ceppi; ogni giorno è in un avamposto diverso.",
             "Uno dei miei assi ha cigolato per tutta la strada. Dodici bei ceppi e posso cederti una runa trovata sulla costa. Ci stai?",
             "Dodici ceppi, amico. Trovami in un avamposto qualsiasi: non sono mai lontano, solo altrove.",
             "Quercia, e secca. I carri canteranno. Ecco la runa: tira come una burrasca.")}),
    ("way_odo_horseshoes", "iron_ore", 8, [("add_xp", 100), ("add_gold", 160), ("add_item", "potion_medium", 3)],
     {"en": ("Shoes for the Horses", "The horses of the caravan have worn their shoes thin. Odo needs eight lumps of iron ore for the smith of the next outpost.",
             "My horses walk eight regions a week and their shoes walk with them. Eight lumps of iron ore, and I will pay like a merchant who means it.",
             "Eight lumps of ore. The horses are patient; I am less so.",
             "Iron for eight horses, and gold for you. The road thanks you, and so do I."),
      "it": ("Ferri per i cavalli", "I cavalli della carovana hanno consumato i ferri. A Odo servono otto pezzi di minerale di ferro per il fabbro del prossimo avamposto.",
             "I miei cavalli percorrono otto regioni a settimana e i ferri con loro. Otto pezzi di minerale di ferro, e pagherò come un mercante che fa sul serio.",
             "Otto pezzi di minerale. I cavalli sono pazienti; io meno.",
             "Ferro per otto cavalli, e oro per te. La strada ti ringrazia, e anch'io.")}),
    ("way_odo_provisions", "travel_ration", 5, [("add_xp", 120), ("add_gold", 200), ("add_item", "shepherds_blade", 1)],
     {"en": ("Provisions for the Long Road", "The cooks of the caravan are out of travel rations. Bring Odo five; a campfire and some berries make them.",
             "The longest road is ahead: Frostveil to the Ashen Wastes, nobody in between. Five travel rations, and a blade I have been keeping for someone like you.",
             "Five rations. Berries and a dry branch at a fire, nothing more.",
             "Now we can go anywhere. Take the blade; a shepherd of Verdalis gave it to me, and you have kept the roads like a shepherd keeps a flock."),
      "it": ("Provviste per la lunga strada", "I cuochi della carovana hanno finito le razioni da viaggio. Portane cinque a Odo; si fanno con un falò e qualche bacca.",
             "Davanti c'è la strada più lunga: dal Velo di Gelo alle Terre di Cenere, senza nessuno in mezzo. Cinque razioni da viaggio, e una lama che tengo da parte per qualcuno come te.",
             "Cinque razioni. Bacche e un ramo secco a un falò, niente di più.",
             "Ora possiamo andare ovunque. Prendi la lama; me l'ha data un pastore di Verdalis, e tu hai custodito le strade come un pastore il suo gregge.")}),
]


def dialogue() -> dict:
    nodes: dict[str, dict] = {
        "c_known": {"type": "condition", "when": {"flag": "odo_met"}, "then": "e0", "else": "hello"},
        "hello": say(KEY, "dlg.caravan.odo.hello", "met"),
        "met": {"type": "effects", "effects": [{"effect": "set_flag", "flag": "odo_met", "value": True}], "next": "e0"},
    }
    for n, (qid, _item, _count, _rewards, _texts) in enumerate(ERRANDS):  # the errands, one after the other, then the goods of the day
        q = f"base:quest/side/{qid}"
        after = f"e{n + 1}" if n + 1 < len(ERRANDS) else "d0"
        nodes[f"e{n}"] = {"type": "condition", "when": {"quest_done": q}, "then": f"t{n}", "else": f"a{n}"}
        nodes[f"t{n}"] = {"type": "condition", "when": {"flag": f"{qid}_thanked"}, "then": after, "else": f"thanks{n}"}
        nodes[f"thanks{n}"] = say(KEY, f"dlg.caravan.{qid}.thanks", f"flag{n}")
        nodes[f"flag{n}"] = {"type": "effects", "effects": [{"effect": "set_flag", "flag": f"{qid}_thanked", "value": True}], "next": "d0"}
        nodes[f"a{n}"] = {"type": "condition", "when": {"quest_active": q}, "then": f"busy{n}", "else": f"offer{n}"}
        nodes[f"busy{n}"] = say(KEY, f"dlg.caravan.{qid}.busy", "d0")
        nodes[f"offer{n}"] = say(KEY, f"dlg.caravan.{qid}.offer", f"choice{n}")
        nodes[f"choice{n}"] = {"type": "choice", "choices": [
            {"text": "$i18n:dlg.wayfarer.accept", "effects": [{"effect": "start_quest", "quest": q}], "next": "d0"},
            {"text": "$i18n:dlg.wayfarer.later", "next": "d0"}]}
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
    for qid, item, count, rewards, _texts in ERRANDS:
        doc = quest(qid, item, count, rewards)
        doc["faction"] = "wayfarers"  # what set_factions.py gives a quest whose file starts with way_
        path = DATA / "quests" / "side" / f"{qid}.json"
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    for lang in ("en", "it"):
        names = json.loads((DATA / "i18n" / lang / "content.json").read_text(encoding="utf-8"))
        texts = {f"speaker.{KEY}": WORDS[lang]["speaker"], "dlg.caravan.odo.hello": WORDS[lang]["hello"]}
        content = {}
        for qid, _item, _count, _rewards, words in ERRANDS:
            name, task, offer, busy, thanks = words[lang]
            content[f"quest.{qid}.name"], content[f"quest.{qid}.task"] = name, task
            texts.update({f"dlg.caravan.{qid}.offer": offer, f"dlg.caravan.{qid}.busy": busy, f"dlg.caravan.{qid}.thanks": thanks})
        set_texts("content.json", lang, content)
        for region in CYCLE:
            texts[f"dlg.caravan.odo.{region}"] = WORDS[lang]["day"].format(next=names[f"region.{region}.name"])
        set_texts("core.json", lang, texts)
    stops = ", ".join(f"[{x}, {y}]" for x, y in route)
    line = (f'{{ "key": "{KEY}", "dialogue": "base:dialogue/npc/odo", "variant": "ochre", "dx": {route[0][0]}, "dy": {route[0][1]}, '
            f'"route": [{stops}], "walk": {json.dumps(WALK)} }}')
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
