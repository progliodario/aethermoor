#!/usr/bin/env python3
"""Writes two people of the hand-made towns (spec 07, "People of the towns"):

- Nana Brin of Fenwick: the grandmother of the house with the chest. She lets the Guest sleep by her hearth for free (`heal_full`) and asks
  three small favours, one after the other (`base:quest/side/brin_firewood`, `brin_posies`, `brin_hides`).
- Corvin the pedlar, in the square of Aldermere: his cart brings the goods of another region every day, in a cycle of eight days (the
  condition `day_mod`, spec 07), and opens a shop of that region (`open_shop` with a `region`, spec 06).

It writes their dialogues, the quests, the texts (it and en) and their place in the world data (`npcs`), and can be run any number of times.
Then run `set_factions.py` (the favours count for the Folk) and `make_catalog.py`.
"""
from __future__ import annotations

import json
import re

from make_towns import DATA, set_texts

WORLD = DATA / "worlds" / "overworld.json"
# key, dialogue, look variant, tile (dx, dy from the center of the world)
PEOPLE = [
    ("fenwick_nana_brin", "brin", "cream", 28, 36),
    ("aldermere_pedlar_corvin", "corvin", "teal", 387, -127),
]
SPEAKERS = {
    "en": {"speaker.fenwick_nana_brin": "Nana Brin, of Fenwick", "speaker.aldermere_pedlar_corvin": "Corvin, the pedlar"},
    "it": {"speaker.fenwick_nana_brin": "Nonna Brin, di Fenwick", "speaker.aldermere_pedlar_corvin": "Corvin, il venditore ambulante"},
}

# Nana Brin's favours: id, item, count, rewards, (name, journal, offer, busy, thanks) in en and it
FAVOURS = [
    ("brin_firewood", "wood_log", 10, [("add_xp", 40), ("add_gold", 30), ("add_item", "grandmothers_pie", 2)],
     {"en": ("Wood for the Hearth", "Nana Brin's hearth is hungry. Bring her ten logs; the trees around Fenwick give them to an axe, or to a fist.",
             "Sit, sit. You walk like my late husband after the harvest. The fire is low, though, and my back is older than the trees. Ten logs?",
             "Ten logs, dear. The trees will not mind. Trees never mind anything.",
             "Look at that fire! Here, two pies. Do not tell Odile they are better than hers."),
      "it": ("Legna per il focolare", "Il focolare di Nonna Brin ha fame. Portale dieci ceppi; gli alberi intorno a Fenwick li danno a un'ascia, o a un pugno.",
             "Siediti, siediti. Cammini come il mio povero marito dopo il raccolto. Però il fuoco è basso, e la mia schiena è più vecchia degli alberi. Dieci ceppi?",
             "Dieci ceppi, caro. Gli alberi non se la prenderanno. Gli alberi non se la prendono mai.",
             "Guarda che fuoco! Ecco, due torte. Non dire a Odile che sono più buone delle sue.")}),
    ("brin_posies", "wildflowers", 8, [("add_xp", 40), ("add_gold", 30), ("add_item", "flower_tea", 3)],
     {"en": ("Posies for the Table", "Nana Brin wants wildflowers on her table again. Eight bunches; the meadows of Verdalis are full of them.",
             "The table looks bare since the girls moved to Aldermere. Eight bunches of wildflowers would make it smile again. Mine too.",
             "Eight bunches. The yellow ones are the happiest, but any will do.",
             "Oh, the colours! The kettle is on: take some tea for the road, it is made from the ones that did not fit the vase."),
      "it": ("Fiori per la tavola", "Nonna Brin vuole di nuovo dei fiori sulla tavola. Otto mazzi; i prati di Verdalis ne sono pieni.",
             "La tavola sembra spoglia da quando le ragazze sono andate ad Aldermere. Otto mazzi di fiori di campo la farebbero sorridere di nuovo. Anche me.",
             "Otto mazzi. I gialli sono i più allegri, ma vanno bene tutti.",
             "Oh, che colori! Il bollitore è sul fuoco: prendi del tè per la strada, è fatto con quelli che non stavano nel vaso.")}),
    ("brin_hides", "boar_hide", 3, [("add_xp", 60), ("add_gold", 60), ("add_item", "hearty_stew", 3)],
     {"en": ("A Quilt for Winter", "Nana Brin is sewing a quilt for the winter and needs three boar hides. Boars root in the woods around Fenwick.",
             "Winter will come, it always does, and this old quilt has more holes than quilt. Three boar hides and I will sew you one too.",
             "Three hides. Boars are rude animals, so do not feel bad.",
             "Three hides, and not a scratch on you! The quilt will be warm, and so will this stew. Eat it hot."),
      "it": ("Una trapunta per l'inverno", "Nonna Brin cuce una trapunta per l'inverno e le servono tre pelli di cinghiale. I cinghiali grufolano nei boschi attorno a Fenwick.",
             "L'inverno arriverà, arriva sempre, e questa vecchia trapunta ha più buchi che trapunta. Tre pelli di cinghiale e ne cucio una anche a te.",
             "Tre pelli. I cinghiali sono animali maleducati, quindi non sentirti in colpa.",
             "Tre pelli, e neanche un graffio! La trapunta sarà calda, e anche questo stufato. Mangialo caldo.")}),
]
BRIN = {
    "en": {"hello": "Come in, come in, Guest. Mind the chest by the door: it is yours to use, every chest in the villages is. Lyra's guests always carry too much.",
           "known": "There you are. Hungry? Tired? Both, by the look of you.",
           "rest": "Sleep by the fire a while", "help": "Can I help with anything?", "bye": "I have to go, Nana.",
           "slept": "There. Rested and warm, and it cost you nothing but a snore. Off you go.",
           "nothing": "Nothing left to do, dear. You have done more than my grandchildren in a year."},
    "it": {"hello": "Entra, entra, Ospite. Attento al baule vicino alla porta: puoi usarlo, come ogni baule dei villaggi. Gli ospiti di Lyra si portano sempre dietro troppa roba.",
           "known": "Eccoti. Hai fame? Sei stanco? Tutte e due le cose, a vederti.",
           "rest": "Dormi un po' accanto al fuoco", "help": "Posso aiutarti in qualcosa?", "bye": "Devo andare, nonna.",
           "slept": "Ecco. Riposato e al caldo, e ti è costato solo un russare. Vai pure.",
           "nothing": "Non c'è più niente da fare, caro. Hai fatto più tu dei miei nipoti in un anno."},
}

# Corvin's cycle of eight days: the region of each day and the line that tells it
CYCLE = ["verdalis", "whisperwood", "ironspine", "tidehaven", "frostveil", "sunscar", "lumeria", "ashen_wastes"]
MARKUP_PCT = 110
CORVIN = {
    "en": {
        "verdalis": "Today the cart smells of bread and grass: the goods of Verdalis, fresh from the farms. Have a look.",
        "whisperwood": "Whisperwood today. Moss, mushrooms and things that glow a little. Do not ask me what they are; I only sell them.",
        "ironspine": "Ore and iron from Ironspine today. The cart nearly broke on the way down, so the prices are fair but firm.",
        "tidehaven": "Tidehaven! Salt, nets and fish that were swimming yesterday. Well, the day before yesterday.",
        "frostveil": "Furs and frost from Frostveil today. My fingers are still blue, but the goods are fine.",
        "sunscar": "The desert came with me today: the goods of Sunscar, and half of its sand in my boots.",
        "lumeria": "Lumeria today. Inks, crystals, books with too many stars in them. The scholars paid me to take them away.",
        "ashen_wastes": "The Ashen Wastes, today. Do not touch the red ones with bare hands. Or do, it is your hand.",
        "cycle": "My cart goes round the whole world, one region a day, eight days and back. Come again tomorrow, it will be different.",
    },
    "it": {
        "verdalis": "Oggi il carro profuma di pane e d'erba: le merci di Verdalis, fresche dalle fattorie. Dai un'occhiata.",
        "whisperwood": "Oggi Whisperwood. Muschio, funghi e cose che brillano un pochino. Non chiedermi cosa sono; io le vendo e basta.",
        "ironspine": "Oggi minerale e ferro da Ironspine. Il carro si è quasi rotto in discesa, quindi i prezzi sono giusti ma fermi.",
        "tidehaven": "Tidehaven! Sale, reti e pesci che nuotavano ieri. Be', l'altro ieri.",
        "frostveil": "Oggi pellicce e gelo da Frostveil. Ho ancora le dita blu, ma la merce è buona.",
        "sunscar": "Oggi è venuto con me il deserto: le merci di Sunscar, e metà della sua sabbia nei miei stivali.",
        "lumeria": "Oggi Lumeria. Inchiostri, cristalli, libri con troppe stelle dentro. Gli studiosi mi hanno pagato per portarli via.",
        "ashen_wastes": "Oggi le Terre di Cenere. Non toccare quelli rossi a mani nude. Oppure sì, la mano è tua.",
        "cycle": "Il mio carro fa il giro del mondo, una regione al giorno, otto giorni e si ricomincia. Torna domani, sarà diverso.",
    },
}


def say(speaker: str, key: str, nxt: str) -> dict:
    return {"type": "say", "speaker": speaker, "text": f"$i18n:{key}", "next": nxt}


def brin_dialogue() -> dict:
    sp = "fenwick_nana_brin"
    nodes: dict[str, dict] = {
        "c_known": {"type": "condition", "when": {"flag": "brin_met"}, "then": "known", "else": "hello"},
        "hello": say(sp, "dlg.home.brin.hello", "met"),
        "met": {"type": "effects", "effects": [{"effect": "set_flag", "flag": "brin_met", "value": True}], "next": "menu"},
        "known": say(sp, "dlg.home.brin.known", "menu"),
        "menu": {"type": "choice", "choices": [
            {"text": "$i18n:dlg.home.brin.rest", "next": "rest"},
            {"text": "$i18n:dlg.home.brin.help", "next": "c0"},
            {"text": "$i18n:dlg.home.brin.bye", "next": "end"}]},
        "rest": {"type": "effects", "effects": [{"effect": "heal_full"}], "next": "slept"},
        "slept": say(sp, "dlg.home.brin.slept", "end"),
        "nothing": say(sp, "dlg.home.brin.nothing", "end"),
    }
    for n, (qid, _item, _count, _rewards, _texts) in enumerate(FAVOURS):
        quest = f"base:quest/side/{qid}"
        after = f"c{n + 1}" if n + 1 < len(FAVOURS) else "nothing"
        nodes[f"c{n}"] = {"type": "condition", "when": {"quest_done": quest}, "then": f"t{n}", "else": f"a{n}"}
        nodes[f"t{n}"] = {"type": "condition", "when": {"flag": f"{qid}_thanked"}, "then": after, "else": f"thanks{n}"}
        nodes[f"thanks{n}"] = say(sp, f"dlg.home.brin.{qid}.thanks", f"flag{n}")
        nodes[f"flag{n}"] = {"type": "effects", "effects": [{"effect": "set_flag", "flag": f"{qid}_thanked", "value": True}], "next": "end"}
        nodes[f"a{n}"] = {"type": "condition", "when": {"quest_active": quest}, "then": f"busy{n}", "else": f"offer{n}"}
        nodes[f"busy{n}"] = say(sp, f"dlg.home.brin.{qid}.busy", "end")
        nodes[f"offer{n}"] = say(sp, f"dlg.home.brin.{qid}.offer", f"choice{n}")
        nodes[f"choice{n}"] = {"type": "choice", "choices": [
            {"text": "$i18n:dlg.wayfarer.accept", "effects": [{"effect": "start_quest", "quest": quest}], "next": "end"},
            {"text": "$i18n:dlg.wayfarer.later", "next": "end"}]}
    return {"$schema": "../../../../schemas/dialogue.schema.json", "id": "base:dialogue/npc/brin", "start": "c_known", "nodes": nodes}


def corvin_dialogue() -> dict:
    sp = "aldermere_pedlar_corvin"
    nodes: dict[str, dict] = {}
    for at, region in enumerate(CYCLE):
        if at + 1 < len(CYCLE):
            nodes[f"d{at}"] = {"type": "condition", "when": {"day_mod": {"every": len(CYCLE), "at": at}}, "then": f"s{at}",
                               "else": f"d{at + 1}" if at + 2 < len(CYCLE) else f"s{at + 1}"}
        nodes[f"s{at}"] = say(sp, f"dlg.home.corvin.{region}", f"shop{at}")
        nodes[f"shop{at}"] = {"type": "effects", "effects": [{"effect": "open_shop", "region": region, "markup_pct": MARKUP_PCT}],
                              "next": "end"}
    first = {"c_known": {"type": "condition", "when": {"flag": "corvin_met"}, "then": "d0", "else": "cycle"},
             "cycle": say(sp, "dlg.home.corvin.cycle", "met"),
             "met": {"type": "effects", "effects": [{"effect": "set_flag", "flag": "corvin_met", "value": True}], "next": "d0"}}
    return {"$schema": "../../../../schemas/dialogue.schema.json", "id": "base:dialogue/npc/corvin", "start": "c_known",
            "nodes": {**first, **nodes}}


def quest(qid: str, item: str, count: int, rewards: list) -> dict:
    out = []
    for r in rewards:
        if r[0] == "add_item":
            out.append({"effect": "add_item", "item": f"base:item/{r[1]}", "qty": r[2]})
        else:
            out.append({"effect": r[0], "amount": r[1]})
    return {"$schema": "../../../../schemas/quest.schema.json", "id": f"base:quest/side/{qid}", "name": f"$i18n:quest.{qid}.name",
            "kind": "side", "faction": "folk",
            "stages": [{"id": "task", "journal": f"$i18n:quest.{qid}.task",
                        "objectives": [{"type": "collect", "item": f"base:item/{item}", "count": count}], "next": "end"}],
            "rewards": out}


def write_json(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def patch_world() -> None:
    """Adds the two people to `npcs` of the world data, one line each, after the last person; a second run changes nothing."""
    raw = WORLD.read_text(encoding="utf-8", newline="")
    for key, file, variant, dx, dy in PEOPLE:
        line = f'{{ "key": "{key}", "dialogue": "base:dialogue/npc/{file}", "variant": "{variant}", "dx": {dx}, "dy": {dy} }}'
        if f'"key": "{key}"' in raw:
            raw = re.sub(r'\{ "key": "' + key + r'"[^\n]*\}', line, raw)
            continue
        last = raw.rindex('{ "key": "')
        end = raw.index("}", last) + 1
        indent = raw[raw.rindex("\n", 0, last) + 1:last]
        raw = raw[:end] + ",\n" + indent + line + raw[end:]
    WORLD.write_text(raw, encoding="utf-8", newline="")


def main() -> None:
    write_json(DATA / "dialogues" / "npc" / "brin.json", brin_dialogue())
    write_json(DATA / "dialogues" / "npc" / "corvin.json", corvin_dialogue())
    for qid, item, count, rewards, _texts in FAVOURS:
        path = DATA / "quests" / "side" / f"{qid}.json"
        data = quest(qid, item, count, rewards)
        if path.exists():  # keep the faction that set_factions.py gave it
            data["faction"] = json.loads(path.read_text(encoding="utf-8")).get("faction", "folk")
        write_json(path, data)
    for lang in ("en", "it"):
        core = dict(SPEAKERS[lang])
        core.update({f"dlg.home.brin.{k}": v for k, v in BRIN[lang].items()})
        core.update({f"dlg.home.corvin.{k}": v for k, v in CORVIN[lang].items()})
        content = {}
        for qid, _item, _count, _rewards, texts in FAVOURS:
            name, task, offer, busy, thanks = texts[lang]
            content[f"quest.{qid}.name"] = name
            content[f"quest.{qid}.task"] = task
            core[f"dlg.home.brin.{qid}.offer"] = offer
            core[f"dlg.home.brin.{qid}.busy"] = busy
            core[f"dlg.home.brin.{qid}.thanks"] = thanks
        set_texts("core.json", lang, core)
        set_texts("content.json", lang, content)
    patch_world()
    print(f"wrote 2 people, {len(FAVOURS)} quests")


if __name__ == "__main__":
    main()
