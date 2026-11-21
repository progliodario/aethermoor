#!/usr/bin/env python3
"""Writes the feasts of the villages (spec 07, "Feasts"): every region has a feast day in the cycle of eight days of the pedlars
(`make_home.CYCLE`: the feast of a region is on the day its pedlars' goods would be its own, `day_mod` with `every` 8 and `at` its index).

On the feast day, the innkeeper of every village and town of the region has one more choice, first in the menu: the feast. The Guest eats
with the village (`heal_full`), the first time also takes home a dish of the region (the flag `feast_<region>_gift`) and then the feast
market opens: the goods of the region at 75 percent (`open_shop` with the `region`, spec 06, "Goods from afar").

It changes the role dialogues `data/base/dialogues/role/innkeeper_<tone>.json` in place (the nodes written here are written again, and the
choice keeps its place, so it can be run any number of times) and writes their texts (`roles.json`, it and en).
"""
from __future__ import annotations

import json

from make_home import CYCLE
from make_towns import DATA, set_texts

MARKUP_PCT = 75
# region: (tone, the dish given the first time, how many)
REGIONS = {
    "verdalis": ("warm", "grandmothers_pie", 2), "whisperwood": ("mystic", "moonlit_tea", 2), "ironspine": ("gruff", "forge_stew", 2),
    "tidehaven": ("salty", "captains_chowder", 2), "frostveil": ("stoic", "hearth_broth", 2), "sunscar": ("flowery", "desert_nectar", 2),
    "lumeria": ("scholarly", "starlight_souffle", 2), "ashen_wastes": ("grim", "ember_brew", 1),
}
SHARED = {
    "en": {"dlg.role.feast.ask": "Why is everyone so cheerful today?"},
    "it": {"dlg.role.feast.ask": "Perché oggi sono tutti così allegri?"},
}
# tone: (the feast, the gift of the first time, the market) in en and it
WORDS = {
    "en": {
        "warm": ("It's the Harvest Feast! Long tables in the square, and nobody pays for supper today. Sit, eat, you're one of us.",
                 "And take a pie home, love. Grandmother's recipe. Don't tell her I gave it away.",
                 "The farmers brought their best. Everything's cheaper today, feast prices!"),
        "mystic": ("Tonight the wood feasts. The lanterns are lit for the trees, and the trees are lit for us. Eat, and be part of the light.",
                   "This tea is brewed once a year, for the feast. It is yours.",
                   "The stalls of the feast are open; the wood is generous today, and so are we."),
        "gruff": ("Forge Day. The hammers rest, the ovens don't. Eat. You've earned it.",
                  "Take a pot of the forge stew. First feast, first pot. Tradition.",
                  "Feast market. Good steel, low prices. Today only."),
        "salty": ("It's the Blessing of the Boats, mate! The nets are hung with flowers and the chowder's free for all hands!",
                  "Here, a pot of the captain's chowder. First feast aboard, you get the good pot.",
                  "The traders of the docks are all out today, and the prices are as low as the tide!"),
        "stoic": ("The Long Night feast. We eat together so that the cold eats alone. Sit by the fire.",
                  "Broth of the hearth. For your first feast. Keep it for a cold day.",
                  "The feast market. Less, today."),
        "flowery": ("The Festival of Lanterns, O Guest! The whole oasis dances under a thousand lights, and every plate is free!",
                    "A flask of desert nectar for you, sweet as the first night of the festival! Your first, and never your last!",
                    "The bazaar of the festival is open, and the prices have fainted from joy!"),
        "scholarly": ("The Night of the Comet, an annual observance. Free refreshments, by tradition and by measured generosity.",
                      "A starlight souffle, prepared to exact proportions, for a first attendance. Customary.",
                      "The fair of instruments is open. A festival discount applies, as documented."),
        "grim": ("The Ember Wake. Once a year we light every fire and remember who we are still. Eat. It is free.",
                 "One brew of embers, for your first wake. Drink it when you need to burn.",
                 "The wake market. Cheap, for once."),
    },
    "it": {
        "warm": ("È la Festa del Raccolto! Tavolate lunghe in piazza, e oggi nessuno paga la cena. Siediti, mangia, sei dei nostri.",
                 "E portati a casa una torta, caro. La ricetta della nonna. Non dirle che l'ho regalata.",
                 "I contadini hanno portato il meglio. Oggi è tutto più economico, prezzi da festa!"),
        "mystic": ("Stanotte il bosco fa festa. Le lanterne sono accese per gli alberi, e gli alberi per noi. Mangia, e fai parte della luce.",
                   "Questo tè si prepara una volta l'anno, per la festa. È tuo.",
                   "Le bancarelle della festa sono aperte; oggi il bosco è generoso, e anche noi."),
        "gruff": ("Giorno della Forgia. I martelli riposano, i forni no. Mangia. Te lo sei guadagnato.",
                  "Prendi una pentola di stufato della forgia. Prima festa, prima pentola. Tradizione.",
                  "Mercato della festa. Buon acciaio, prezzi bassi. Solo oggi."),
        "salty": ("È la Benedizione delle Barche, amico! Le reti sono piene di fiori e la zuppa è gratis per tutto l'equipaggio!",
                  "Ecco, una pentola di zuppa del capitano. Prima festa a bordo, ti tocca la pentola buona.",
                  "I mercanti dei moli sono tutti fuori oggi, e i prezzi sono bassi come la marea!"),
        "stoic": ("La festa della Lunga Notte. Mangiamo insieme perché il freddo mangi da solo. Siediti accanto al fuoco.",
                  "Brodo del focolare. Per la tua prima festa. Tienilo per un giorno freddo.",
                  "Il mercato della festa. Meno, oggi."),
        "flowery": ("La Festa delle Lanterne, o Ospite! Tutta l'oasi danza sotto mille luci, e ogni piatto è gratis!",
                    "Una fiaschetta di nettare del deserto per te, dolce come la prima notte della festa! La tua prima, e mai l'ultima!",
                    "Il bazar della festa è aperto, e i prezzi sono svenuti dalla gioia!"),
        "scholarly": ("La Notte della Cometa, una ricorrenza annuale. Rinfreschi gratuiti, per tradizione e per generosità misurata.",
                      "Un soufflé di luce stellare, preparato in proporzioni esatte, per una prima partecipazione. È consuetudine.",
                      "La fiera degli strumenti è aperta. Si applica uno sconto di festa, come documentato."),
        "grim": ("La Veglia delle Braci. Una volta l'anno accendiamo ogni fuoco e ricordiamo chi siamo ancora. Mangia. È gratis.",
                 "Un infuso di braci, per la tua prima veglia. Bevilo quando ti serve bruciare.",
                 "Il mercato della veglia. Economico, per una volta."),
    },
}


def write_json(path, doc, like: str) -> None:
    newline = "\r\n" if "\r\n" in like else "\n"
    path.write_text((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").replace("\n", newline), encoding="utf-8", newline="")


def patch_innkeeper(region: str, tone: str, dish: str, qty: int) -> None:
    path = DATA / "dialogues" / "role" / f"innkeeper_{tone}.json"
    raw = path.read_text(encoding="utf-8", newline="")
    doc = json.loads(raw)
    nodes = doc["nodes"]
    old = nodes["menu"]["choices"]
    where = next((i for i, c in enumerate(old) if c.get("next") == "feast"), 0)  # the choice keeps its place (first, the first time)
    choices = [c for c in old if c.get("next") != "feast"]
    choice = {"text": "$i18n:dlg.role.feast.ask", "when": {"day_mod": {"every": len(CYCLE), "at": CYCLE.index(region)}}, "next": "feast"}
    nodes["menu"]["choices"] = choices[:where] + [choice] + choices[where:]
    gift = f"feast_{region}_gift"
    key = f"dlg.feast.{tone}"
    nodes["feast"] = {"type": "effects", "effects": [{"effect": "heal_full"}], "next": "feast_say"}
    nodes["feast_say"] = {"type": "say", "speaker": "npc", "text": f"$i18n:{key}.feast", "next": "feast_gift_check"}
    nodes["feast_gift_check"] = {"type": "condition", "when": {"flag": gift}, "then": "feast_market", "else": "feast_gift"}
    nodes["feast_gift"] = {"type": "effects", "effects": [{"effect": "set_flag", "flag": gift, "value": True},
                                                          {"effect": "add_item", "item": f"base:item/{dish}", "qty": qty}], "next": "feast_gift_say"}
    nodes["feast_gift_say"] = {"type": "say", "speaker": "npc", "text": f"$i18n:{key}.gift", "next": "feast_market"}
    nodes["feast_market"] = {"type": "say", "speaker": "npc", "text": f"$i18n:{key}.market", "next": "feast_shop"}
    nodes["feast_shop"] = {"type": "effects", "effects": [{"effect": "open_shop", "region": region, "markup_pct": MARKUP_PCT}], "next": "end"}
    write_json(path, doc, raw)


def main() -> None:
    texts = {lang: dict(SHARED[lang]) for lang in ("en", "it")}
    for region, (tone, dish, qty) in REGIONS.items():
        patch_innkeeper(region, tone, dish, qty)
        for lang in ("en", "it"):
            feast, gift, market = WORDS[lang][tone]
            texts[lang].update({f"dlg.feast.{tone}.feast": feast, f"dlg.feast.{tone}.gift": gift, f"dlg.feast.{tone}.market": market})
    for lang in ("en", "it"):
        set_texts("roles.json", lang, texts[lang])
    print(f"wrote the feasts of {len(REGIONS)} regions")


if __name__ == "__main__":
    main()
