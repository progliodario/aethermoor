#!/usr/bin/env python3
"""Writes the feasts of the villages (spec 07, "Feasts"): every region has a feast day in the cycle of eight days of the pedlars
(`make_home.CYCLE`: the feast of a region is on the day its pedlars' goods would be its own, `day_mod` with `every` 8 and `at` its index).

On the feast day, the innkeeper of every village and town of the region has one more choice, first in the menu: the feast. The Guest eats
with the village (`heal_full`), the first time also takes home a dish of the region (the flag `feast_<region>_gift`) and then the feast
market opens: the goods of the region at 75 percent (`open_shop` with the `region`, spec 06, "Goods from afar"). On the feast day the
innkeeper also offers the **games of the feast**, a contest of the region (`base:quest/side/feast_<region>`, for the Folk): something to
bring, gathered, fished or won from the creatures, paid with experience, gold, a tempering oil (spec 06, "Tempering") and a prize of
the region. A contest started can be finished on any day; the innkeeper asks how it goes.

It changes the role dialogues `data/base/dialogues/role/innkeeper_<tone>.json` in place (the nodes written here are written again, and the
choices keep their place, so it can be run any number of times), writes the quests of the games and their texts (`roles.json` and
`content.json`, it and en). Then run `make_catalog.py` and `make_facts.py`.
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
# region: [(item, count), ...] to bring, and the prize of the region
GAMES = {
    "verdalis": ([("wild_berries", 8), ("egg", 3)], ("honey_cake", 4)), "whisperwood": ([("fern_frond", 6)], ("moonlit_tea", 1)),
    "ironspine": ([("stone_chunk", 12)], ("rune_stone", 1)), "tidehaven": ([("golden_carp", 1), ("river_fish", 4)], ("pearl_elixir", 1)),
    "frostveil": ([("ice_crystal", 6)], ("frost_tonic", 1)), "sunscar": ([("amber_drop", 3)], ("sunfire_skewers", 2)),
    "lumeria": ([("star_dust", 5)], ("starlight_elixir", 1)), "ashen_wastes": ([("ember_core", 4)], ("ember_chili", 2)),
}
DANGER = {"verdalis": 1, "whisperwood": 3, "ironspine": 4, "tidehaven": 3, "frostveil": 5, "sunscar": 4, "lumeria": 5, "ashen_wastes": 7}
SHARED = {
    "en": {"dlg.role.feast.ask": "Why is everyone so cheerful today?", "dlg.role.feast.games": "Are there games at the feast?",
           "dlg.role.feast.games_status": "About the contest of the feast...", "dlg.role.feast.join": "Count me in!",
           "dlg.role.feast.not_now": "Maybe later."},
    "it": {"dlg.role.feast.ask": "Perché oggi sono tutti così allegri?", "dlg.role.feast.games": "Ci sono giochi alla festa?",
           "dlg.role.feast.games_status": "A proposito della gara della festa...", "dlg.role.feast.join": "Ci sto!",
           "dlg.role.feast.not_now": "Forse più tardi."},
}
# tone: (the contest, how it goes, name of the quest, journal) in en and it
GAME_WORDS = {
    "en": {
        "warm": ("The pie contest! Bring eight handfuls of berries and three eggs, and the judges will taste your pie. Last year the miller won with a pie the size of a wheel.",
                 "The judges are still hungry, love. Berries and eggs!", "The Pie Contest", "Bring berries and eggs to the innkeeper of a village of Verdalis for the pie contest of the Harvest Feast."),
        "mystic": ("The lantern weaving. Six fern fronds, woven into a lantern that does not burn. The trees judge.",
                   "The ferns wait in the shade.", "The Lantern Weaving", "Bring fern fronds to the innkeeper of a village of Whisperwood to weave a lantern for the feast."),
        "gruff": ("Stone toss. Bring twelve chunks of stone; we see who throws them farthest. You'll win. Bring them anyway.",
                  "Stone. Twelve.", "The Stone Toss", "Bring twelve stone chunks to the innkeeper of a village of Ironspine for the stone toss of Forge Day."),
        "salty": ("The fishing contest, mate! The biggest catch wins: bring a golden carp and four river fish and the cup is yours.",
                  "Nothing on the line yet? The reeds, mate, the reeds!", "The Biggest Catch", "Bring a golden carp and four river fish to the innkeeper of a village of Tidehaven for the fishing contest."),
        "stoic": ("Ice carving. Six crystals. Carve something. The best one stands until spring.",
                  "The crystals. Then the knife.", "The Ice Carving", "Bring six ice crystals to the innkeeper of a village of Frostveil for the ice carving of the Long Night."),
        "flowery": ("The perfume contest, O Guest! Three drops of amber, and you shall compose a scent to make the moon blush!",
                    "The amber still sleeps in the slimes of the dunes, alas!", "The Scent of the Festival", "Bring three drops of amber to the innkeeper of a village of Sunscar for the perfume contest of the Festival of Lanterns."),
        "scholarly": ("The star-counting, a contest of precision. Five measures of star dust, and a chart drawn by your own hand.",
                      "The star dust remains outstanding.", "Counting the Stars", "Bring five measures of star dust to the innkeeper of a village of Lumeria for the star-counting of the Night of the Comet."),
        "grim": ("The ember walk. Bring four ember cores; we carry them across the square barehanded. Or you do.",
                 "Four cores. The square waits.", "The Ember Walk", "Bring four ember cores to the innkeeper of a village of the Ashen Wastes for the ember walk of the Wake."),
    },
    "it": {
        "warm": ("La gara delle torte! Porta otto manciate di bacche e tre uova, e i giudici assaggeranno la tua torta. L'anno scorso ha vinto il mugnaio con una torta grande come una ruota.",
                 "I giudici hanno ancora fame, caro. Bacche e uova!", "La gara delle torte", "Porta bacche e uova al locandiere di un villaggio di Verdalis per la gara delle torte della Festa del Raccolto."),
        "mystic": ("L'intreccio delle lanterne. Sei fronde di felce, intrecciate in una lanterna che non brucia. Giudicano gli alberi.",
                   "Le felci aspettano nell'ombra.", "L'intreccio delle lanterne", "Porta fronde di felce al locandiere di un villaggio di Whisperwood per intrecciare una lanterna per la festa."),
        "gruff": ("Lancio della pietra. Porta dodici pezzi di pietra; vediamo chi li lancia più lontano. Vincerai tu. Portali lo stesso.",
                  "Pietra. Dodici.", "Il lancio della pietra", "Porta dodici pezzi di pietra al locandiere di un villaggio di Ironspine per il lancio della pietra del Giorno della Forgia."),
        "salty": ("La gara di pesca, amico! Vince la preda più grande: porta una carpa dorata e quattro pesci di fiume e la coppa è tua.",
                  "Ancora niente all'amo? Il canneto, amico, il canneto!", "La preda più grande", "Porta una carpa dorata e quattro pesci di fiume al locandiere di un villaggio di Tidehaven per la gara di pesca."),
        "stoic": ("Scultura nel ghiaccio. Sei cristalli. Scolpisci qualcosa. La migliore resta fino a primavera.",
                  "I cristalli. Poi il coltello.", "La scultura nel ghiaccio", "Porta sei cristalli di ghiaccio al locandiere di un villaggio di Frostveil per la scultura nel ghiaccio della Lunga Notte."),
        "flowery": ("La gara dei profumi, o Ospite! Tre gocce d'ambra, e comporrai un profumo che farà arrossire la luna!",
                    "L'ambra dorme ancora nelle gelatine delle dune, ahimè!", "Il profumo della festa", "Porta tre gocce d'ambra al locandiere di un villaggio di Sunscar per la gara dei profumi della Festa delle Lanterne."),
        "scholarly": ("La conta delle stelle, una gara di precisione. Cinque misure di polvere di stelle, e una carta disegnata di tuo pugno.",
                      "La polvere di stelle è ancora da consegnare.", "Contare le stelle", "Porta cinque misure di polvere di stelle al locandiere di un villaggio di Lumeria per la conta delle stelle della Notte della Cometa."),
        "grim": ("La camminata sulle braci. Porta quattro nuclei di brace; li portiamo attraverso la piazza a mani nude. O lo fai tu.",
                 "Quattro nuclei. La piazza aspetta.", "La camminata sulle braci", "Porta quattro nuclei di brace al locandiere di un villaggio delle Terre di Cenere per la camminata sulle braci della Veglia."),
    },
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
    q = f"base:quest/side/feast_{region}"
    untouched = {"not": {"any": [{"quest_active": q}, {"quest_done": q}]}}
    games = [{"text": "$i18n:dlg.role.feast.games", "when": {"all": [choice["when"], untouched]}, "next": "feast_games"},
             {"text": "$i18n:dlg.role.feast.games_status", "when": {"quest_active": q}, "next": "feast_games_busy"}]
    choices = [c for c in choices if c.get("next") not in ("feast_games", "feast_games_busy")]
    nodes["menu"]["choices"] = choices[:where] + [choice] + games + choices[where:]
    nodes["feast_games"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.feast.{tone}.games", "next": "feast_games_choice"}
    nodes["feast_games_choice"] = {"type": "choice", "choices": [
        {"text": "$i18n:dlg.role.feast.join", "effects": [{"effect": "start_quest", "quest": q}], "next": "end"},
        {"text": "$i18n:dlg.role.feast.not_now", "next": "menu"}]}
    nodes["feast_games_busy"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.feast.{tone}.games_busy", "next": "end"}
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
    content: dict[str, dict[str, str]] = {"en": {}, "it": {}}
    for region, (tone, dish, qty) in REGIONS.items():
        patch_innkeeper(region, tone, dish, qty)
        needs, (prize, prize_qty) = GAMES[region]
        quest = {"$schema": "../../../../schemas/quest.schema.json", "id": f"base:quest/side/feast_{region}", "name": f"$i18n:quest.feast_{region}.name",
                 "kind": "side", "faction": "folk",
                 "stages": [{"id": "bring", "journal": f"$i18n:quest.feast_{region}.task",
                             "objectives": [{"type": "collect", "item": f"base:item/{item}", "count": count} for item, count in needs], "next": "end"}],
                 "rewards": [{"effect": "add_xp", "amount": 80 + 40 * DANGER[region]}, {"effect": "add_gold", "amount": 100 + 50 * DANGER[region]},
                             {"effect": "add_item", "item": "base:item/tempering_oil", "qty": 1},
                             {"effect": "add_item", "item": f"base:item/{prize}", "qty": prize_qty}]}
        path = DATA / "quests" / "side" / f"feast_{region}.json"
        path.write_text(json.dumps(quest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        for lang in ("en", "it"):
            feast, gift, market = WORDS[lang][tone]
            games, busy, name, task = GAME_WORDS[lang][tone]
            texts[lang].update({f"dlg.feast.{tone}.feast": feast, f"dlg.feast.{tone}.gift": gift, f"dlg.feast.{tone}.market": market,
                                f"dlg.feast.{tone}.games": games, f"dlg.feast.{tone}.games_busy": busy})
            content[lang].update({f"quest.feast_{region}.name": name, f"quest.feast_{region}.task": task})
    for lang in ("en", "it"):
        set_texts("roles.json", lang, texts[lang])
        set_texts("content.json", lang, content[lang])
    print(f"wrote the feasts of {len(REGIONS)} regions")


if __name__ == "__main__":
    main()
