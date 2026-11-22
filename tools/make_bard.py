#!/usr/bin/env python3
"""Writes Lark, the wandering bard (spec 07, "Travellers"): the third traveller of the roads, who carries the news of what the Guest did.

She goes round the eight outposts four days ahead of Odo (`make_home.CYCLE` turned by four: day 1 Frostveil, then Sunscar, Lumeria, the
Ashen Wastes, Verdalis, Whisperwood, Ironspine, Tidehaven), so that she is never at the same outpost as Odo. She has a song for every
region whose villagers' trouble the Guest ended (the third tale of the region done, `base:quest/side/tale_<region>_3`, spec 07, "Tales of
the villagers"): asked for a song, she sings the first one the Guest has not heard yet (the flag `bard_<region>`) and the Guest learns
from it (experience). When all eight are heard she gives the Guest a dawn rune, once (the flag `bard_gift`). Without a new song she tells
where she goes tomorrow.

She also has a quest, **the Song of the Road** (`base:quest/side/way_lark_road_song`, for the Ring of Wayfarers): a song about the three
travellers needs the stories of the other two, so the Guest finds Brannoc, then Odo, wherever the day puts them, and comes back to her
(three `talk` stages). She thanks the Guest once (the flag `lark_road_song_thanked`).

It writes her dialogue `data/base/dialogues/npc/lark.json`, her texts (it and en) and her line in `npcs` of the world data (a free
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
KEY = "wandering_bard_lark"
ROUTE = [CYCLE[(k + 4) % len(CYCLE)] for k in range(len(CYCLE))]
XP = 120
ROAD = "base:quest/side/way_lark_road_song"
# the Song of the Road: (stage, npc key, journal en, journal it)
ROAD_STAGES = [
    ("brannoc", "wandering_smith_brannoc", "Lark is writing a song about the travellers of the roads. Find Brannoc the wandering smith and hear his story.",
     "Lark scrive una canzone sui viaggiatori delle strade. Trova Brannoc, il fabbro errante, e ascolta la sua storia."),
    ("odo", "caravan_master_odo", "Brannoc told his story. Now find Odo, the master of the caravan, wherever his wagons are today.",
     "Brannoc ha raccontato la sua storia. Ora trova Odo, il capo della carovana, ovunque siano oggi i suoi carri."),
    ("lark", "wandering_bard_lark", "You have the stories of Brannoc and Odo. Bring them to Lark, at whatever outpost she sings today.",
     "Hai le storie di Brannoc e di Odo. Portale a Lark, in qualunque avamposto canti oggi."),
]
ROAD_WORDS = {
    "en": {"name": "The Song of the Road", "ask": "Can I help with a song?", "status": "About the song of the road...", "report": "I have the stories.",
           "offer": "A song about the three of us who never stop: Brannoc, Odo and me. But I only know my own story. Find them, wherever the day puts them, and bring me theirs.",
           "busy": "Brannoc goes one way, Odo the other. Ask at the outposts; somebody always saw a cart.",
           "song": "'One hammers, one drives, one sings; and the Guest walks between them, and the roads are safe.' Listen. It is yours too. Take this: a song should leave something behind."},
    "it": {"name": "La canzone della strada", "ask": "Posso aiutarti con una canzone?", "status": "A proposito della canzone della strada...", "report": "Ho le storie.",
           "offer": "Una canzone su noi tre che non ci fermiamo mai: Brannoc, Odo e io. Ma conosco solo la mia storia. Trovali, ovunque li porti il giorno, e portami le loro.",
           "busy": "Brannoc va da una parte, Odo dall'altra. Chiedi agli avamposti; qualcuno ha sempre visto un carro.",
           "song": "'Uno batte, uno guida, una canta; e l'Ospite cammina tra loro, e le strade sono sicure.' Ascolta. È anche tua. Prendi questo: una canzone deve lasciare qualcosa."},
}
WORDS = {
    "en": {"speaker": "Lark, the wandering bard",
           "hello": "Lark, singer of roads. Every outpost has a story, and lately every story has you in it. Sit; a song costs nothing but an ear.",
           "song": "Sing me a song.", "bye": "Until the next road.",
           "none": "No new song about you yet, Guest. Go and do something worth a verse; the villages will tell me.",
           "gift": "Eight songs, eight regions, one Guest. Take this dawn rune: I have sung of you so often that it feels like yours.",
           "next": "Tomorrow I sing in {next}. Come and listen."},
    "it": {"speaker": "Lark, la cantastorie errante",
           "hello": "Lark, cantastorie delle strade. Ogni avamposto ha una storia, e ultimamente in ogni storia ci sei tu. Siediti; una canzone costa solo un orecchio.",
           "song": "Cantami una canzone.", "bye": "Alla prossima strada.",
           "none": "Ancora nessuna canzone nuova su di te, Ospite. Va' e fai qualcosa che valga una strofa; i villaggi me lo diranno.",
           "gift": "Otto canzoni, otto regioni, un Ospite. Prendi questa runa dell'alba: ho cantato di te così spesso che mi sembra tua.",
           "next": "Domani canto a {next}. Vieni ad ascoltare."},
}
# region: the song of the third tale of its villagers, en and it
SONGS = {
    "verdalis": ("They say the boars came down to dig the turnips of the hill, and the Guest came after them, and the turnips grow there still.",
                 "Dicono che i cinghiali scendessero a scavare le rape della collina, e l'Ospite li seguì, e le rape crescono ancora là."),
    "whisperwood": ("In the wood where owls fell silent and the lantern lights went wrong, a stranger walked between the trees and gave them back their song.",
                    "Nel bosco dove i gufi tacquero e le lanterne mentivano, uno straniero camminò tra gli alberi e restituì loro il canto."),
    "ironspine": ("The golems walked the quarries, stone on stone and step on step; the Guest went up the mountain, and the mountain owes a debt.",
                  "I golem camminavano nelle cave, pietra su pietra e passo su passo; l'Ospite salì la montagna, e la montagna ha un debito."),
    "sunscar": ("Oh, the dunes had thieves and scorpions and a sun that would not rest, but the Guest brought shade to Sunscar, and the oases are blessed!",
                "Oh, le dune avevano ladri e scorpioni e un sole che non riposava, ma l'Ospite portò ombra a Sunscar, e le oasi sono benedette!"),
    "frostveil": ("The wolves of the long winter came hungry to the door; the Guest stood in the snow, and the wolves came back no more.",
                  "I lupi del lungo inverno vennero affamati alla porta; l'Ospite restò nella neve, e i lupi non tornarono più."),
    "tidehaven": ("Heave, my lads, the crabs are gone and the coral's clear and bright! The Guest swept all the shore for us, and we fish by lantern light!",
                  "Issa, ragazzi, i granchi se ne sono andati e il corallo è chiaro e brillante! L'Ospite ci ha ripulito la riva, e peschiamo al lume della lanterna!"),
    "ashen_wastes": ("Where the ash falls like the snow and the cinders never cool, the Guest walked through the fire and left the embers still.",
                     "Dove la cenere cade come neve e le braci non si raffreddano mai, l'Ospite attraversò il fuoco e lasciò le braci quiete."),
    "lumeria": ("The domes went dark with nebulae and the stars were hard to see; the Guest cleared all the heavens, and they shine for you and me.",
                "Le cupole si oscurarono di nebulose e le stelle si vedevano a fatica; l'Ospite ripulì tutti i cieli, e brillano per te e per me."),
}


def dialogue() -> dict:
    nodes: dict[str, dict] = {
        "c_known": {"type": "condition", "when": {"flag": "lark_met"}, "then": "menu", "else": "hello"},
        "hello": say(KEY, "dlg.lark.hello", "met"),
        "met": {"type": "effects", "effects": [{"effect": "set_flag", "flag": "lark_met", "value": True}], "next": "menu"},
        "menu": {"type": "choice", "choices": [
            {"text": "$i18n:dlg.lark.song", "next": "song0"},
            {"text": "$i18n:dlg.lark.road_ask", "when": {"not": {"any": [{"quest_active": ROAD}, {"quest_done": ROAD}]}}, "next": "road_offer"},
            {"text": "$i18n:dlg.lark.road_status", "when": {"quest_active": ROAD}, "next": "road_busy"},
            {"text": "$i18n:dlg.lark.road_report", "when": {"all": [{"quest_done": ROAD}, {"not": {"flag": "lark_road_song_thanked"}}]}, "next": "road_thanks"},
            {"text": "$i18n:dlg.lark.bye", "next": "end"}]},
        "road_offer": say(KEY, "dlg.lark.road_offer", "road_choice"),
        "road_choice": {"type": "choice", "choices": [
            {"text": "$i18n:dlg.wayfarer.accept", "effects": [{"effect": "start_quest", "quest": ROAD}], "next": "end"},
            {"text": "$i18n:dlg.wayfarer.later", "next": "menu"}]},
        "road_busy": say(KEY, "dlg.lark.road_busy", "end"),
        "road_thanks": {"type": "effects", "effects": [{"effect": "set_flag", "flag": "lark_road_song_thanked", "value": True}], "next": "road_song"},
        "road_song": say(KEY, "dlg.lark.road_song", "end"),
    }
    regions = list(SONGS)
    for n, region in enumerate(regions):  # the first song the Guest has earned and not heard yet
        after = f"song{n + 1}" if n + 1 < len(regions) else "gift_check"
        nodes[f"song{n}"] = {"type": "condition", "when": {"all": [{"quest_done": f"base:quest/side/tale_{region}_3"},
                                                                    {"not": {"flag": f"bard_{region}"}}]},
                             "then": f"sing{n}", "else": after}
        nodes[f"sing{n}"] = {"type": "effects", "effects": [{"effect": "set_flag", "flag": f"bard_{region}", "value": True},
                                                            {"effect": "add_xp", "amount": XP}], "next": f"verse{n}"}
        nodes[f"verse{n}"] = say(KEY, f"dlg.lark.song_{region}", "end")
    every = [{"flag": f"bard_{region}"} for region in regions]
    nodes["gift_check"] = {"type": "condition", "when": {"all": every + [{"not": {"flag": "bard_gift"}}]}, "then": "gift", "else": "none"}
    nodes["gift"] = {"type": "effects", "effects": [{"effect": "set_flag", "flag": "bard_gift", "value": True},
                                                    {"effect": "add_item", "item": "base:item/rune_dawn", "qty": 1}], "next": "gift_say"}
    nodes["gift_say"] = say(KEY, "dlg.lark.gift", "end")
    nodes["none"] = say(KEY, "dlg.lark.none", "d0")
    for at in range(len(ROUTE)):  # where she goes tomorrow, by the day of the cycle
        if at + 1 < len(ROUTE):
            nodes[f"d{at}"] = {"type": "condition", "when": {"day_mod": {"every": len(ROUTE), "at": at}}, "then": f"s{at}",
                               "else": f"d{at + 1}" if at + 2 < len(ROUTE) else f"s{at + 1}"}
        nodes[f"s{at}"] = say(KEY, f"dlg.lark.next_{ROUTE[(at + 1) % len(ROUTE)]}", "end")
    return {"$schema": "../../../../schemas/dialogue.schema.json", "id": "base:dialogue/npc/lark", "start": "c_known", "nodes": nodes}


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
    (DATA / "dialogues" / "npc" / "lark.json").write_text(text, encoding="utf-8", newline="\n")
    quest = {"$schema": "../../../../schemas/quest.schema.json", "id": ROAD, "name": "$i18n:quest.way_lark_road_song.name", "kind": "side",
             "faction": "wayfarers",
             "stages": [{"id": stage, "journal": f"$i18n:quest.way_lark_road_song.{stage}", "objectives": [{"type": "talk", "npc_key": key}],
                         "next": ROAD_STAGES[k + 1][0] if k + 1 < len(ROAD_STAGES) else "end"} for k, (stage, key, _en, _it) in enumerate(ROAD_STAGES)],
             "rewards": [{"effect": "add_xp", "amount": 1500}, {"effect": "add_gold", "amount": 800},
                         {"effect": "add_item", "item": "base:item/rune_gale", "qty": 1}, {"effect": "add_item", "item": "base:item/tempering_oil", "qty": 2}]}
    road = DATA / "quests" / "side" / "way_lark_road_song.json"
    road.write_text(json.dumps(quest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    for k, lang in enumerate(("en", "it")):
        r = ROAD_WORDS[lang]
        content = {"quest.way_lark_road_song.name": r["name"]}
        content.update({f"quest.way_lark_road_song.{stage}": (en, it)[k] for stage, _key, en, it in ROAD_STAGES})
        set_texts("content.json", lang, content)
        set_texts("core.json", lang, {"dlg.lark.road_ask": r["ask"], "dlg.lark.road_status": r["status"], "dlg.lark.road_report": r["report"],
                                      "dlg.lark.road_offer": r["offer"], "dlg.lark.road_busy": r["busy"], "dlg.lark.road_song": r["song"]})
    for k, lang in enumerate(("en", "it")):
        names = json.loads((DATA / "i18n" / lang / "content.json").read_text(encoding="utf-8"))
        w = WORDS[lang]
        texts = {f"speaker.{KEY}": w["speaker"], "dlg.lark.hello": w["hello"], "dlg.lark.song": w["song"], "dlg.lark.bye": w["bye"],
                 "dlg.lark.none": w["none"], "dlg.lark.gift": w["gift"]}
        texts.update({f"dlg.lark.song_{region}": song[k] for region, song in SONGS.items()})
        for region in CYCLE:
            texts[f"dlg.lark.next_{region}"] = w["next"].format(next=names[f"region.{region}.name"])
        set_texts("core.json", lang, texts)
    stops = ", ".join(f"[{x}, {y}]" for x, y in route)
    line = (f'{{ "key": "{KEY}", "dialogue": "base:dialogue/npc/lark", "variant": "purple", "dx": {route[0][0]}, "dy": {route[0][1]}, '
            f'"route": [{stops}] }}')
    raw = WORLD.read_text(encoding="utf-8", newline="")
    if f'"key": "{KEY}"' in raw:
        raw = re.sub(r'\{ "key": "' + KEY + r'"[^\n]*\}', line, raw)
    else:
        last = raw.rindex('{ "key": "')
        end = raw.index("\n", last)
        indent = raw[raw.rindex("\n", 0, last) + 1:last]
        raw = raw[:end] + ",\n" + indent + line + raw[end:]
    WORLD.write_text(raw, encoding="utf-8", newline="")
    print(f"wrote Lark, with a route of {len(route)} stops and {len(SONGS)} songs")


if __name__ == "__main__":
    main()
