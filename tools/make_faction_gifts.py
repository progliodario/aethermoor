#!/usr/bin/env python3
"""Writes the gifts of the factions (spec 07, "Factions"): the guild clerks give the Guild signet to somebody with `GUILD_AT` quests of the
guild, the elders give the Folk charm to somebody with `FOLK_AT` quests of the folk; once a game, whichever clerk or elder is asked (the flag
`faction_gift_<faction>`).

It writes the two items and their texts, and changes the role dialogues of `data/base/dialogues/role/` in place (the nodes written here are
written again, so it can be run any number of times). Then run `make_catalog.py`.
"""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

TONES = ["warm", "mystic", "gruff", "flowery", "stoic", "salty", "grim", "scholarly"]
# faction: (role, standing asked, item, accessory, price, name en, name it, description en, description it)
GIFTS = {
    "guild": ("guild_clerk", 10, "guild_signet", {"atk": 14, "crit_pm": 50}, 1500, "Guild signet", "Sigillo della Gilda",
              "The ring the Guild gives to those it trusts. Attack +14, critical chance +5%.",
              "L'anello che la Gilda dà a chi gode della sua fiducia. Attacco +14, probabilità di critico +5%."),
    "folk": ("elder", 20, "folk_charm", {"max_hp": 80, "def": 4}, 1500, "Folk charm", "Amuleto della Gente",
             "Knotted from a thread of every village you helped. Health +80, defense +4.",
             "Annodato con un filo di ogni villaggio che hai aiutato. Vita +80, difesa +4."),
}
ASK = {"en": {"guild": "Does the Guild have anything for me?", "folk": "The villages speak of me, I hear?"},
       "it": {"guild": "La Gilda ha qualcosa per me?", "folk": "Mi dicono che i villaggi parlano di me?"}}
# tone: (the clerk's line, the elder's line), en and it
GIVE = {
    "en": {
        "warm": ("Ten jobs for the Guild, and every one done properly! This signet is yours. Wear it and every clerk will smile.",
                 "Every village of these parts has sent a thread, and we knotted them together. It is yours, dear, with all our thanks."),
        "mystic": ("The Guild has watched your work as the forest watches the moon. Take the signet; it already knows your hand.",
                   "The villages wove you a charm in the old way. Wear it, and the roads will remember you kindly."),
        "gruff": ("Ten jobs. No complaints. Here. The signet. Don't lose it.", "Every village put a thread in this. Wear it. Don't make a speech."),
        "flowery": ("Champion of the board! The Guild bestows upon you its signet, a ring of rare distinction and some weight!",
                    "Behold, a charm woven by a hundred grateful hands, and only slightly tangled! It is yours, with flowers!"),
        "stoic": ("The Guild trusts you. The signet.", "From the villages. Wear it."),
        "salty": ("Ten jobs an' not one botched! The Guild's signet, matey, an' every clerk o' the coast'll stand ye a drink.",
                  "Every port an' hamlet sent a thread. We knotted 'em proper, sailor's knots. It's yours!"),
        "grim": ("You did the work nobody wanted. The Guild gives you this. It is not enough. It is what there is.",
                 "The villages that are still standing made you this. That says enough."),
        "scholarly": ("By resolution of the Guild, recorded in triplicate: the signet is conferred upon you. Congratulations, formally.",
                      "A charm, woven by every village you assisted. I have catalogued the threads; there are a great many."),
    },
    "it": {
        "warm": ("Dieci incarichi per la Gilda, e tutti fatti come si deve! Questo sigillo è tuo. Portalo e ogni cancelliere ti sorriderà.",
                 "Ogni villaggio di queste parti ha mandato un filo, e li abbiamo annodati insieme. È tuo, caro, con tutta la nostra gratitudine."),
        "mystic": ("La Gilda ha osservato il tuo lavoro come la foresta osserva la luna. Prendi il sigillo: conosce già la tua mano.",
                   "I villaggi ti hanno intrecciato un amuleto all'antica. Portalo, e le strade si ricorderanno di te con gentilezza."),
        "gruff": ("Dieci incarichi. Nessuna lamentela. Ecco. Il sigillo. Non perderlo.", "Ogni villaggio ci ha messo un filo. Portalo. Niente discorsi."),
        "flowery": ("Campione della bacheca! La Gilda ti conferisce il suo sigillo, un anello di rara distinzione e di un certo peso!",
                    "Ecco un amuleto intrecciato da cento mani grate, e solo un poco aggrovigliato! È tuo, con i fiori!"),
        "stoic": ("La Gilda si fida di te. Il sigillo.", "Dai villaggi. Portalo."),
        "salty": ("Dieci incarichi e nemmeno uno pasticciato! Il sigillo della Gilda, mozzo, e ogni cancelliere della costa ti offrirà da bere.",
                  "Ogni porto e borgo ha mandato un filo. Li abbiamo annodati per bene, nodi da marinaio. È tuo!"),
        "grim": ("Hai fatto il lavoro che nessuno voleva. La Gilda ti dà questo. Non basta. È quello che c'è.",
                 "I villaggi ancora in piedi te l'hanno fatto. Questo dice abbastanza."),
        "scholarly": ("Con delibera della Gilda, registrata in triplice copia: il sigillo ti è conferito. Congratulazioni, formalmente.",
                      "Un amuleto, intrecciato da ogni villaggio che hai assistito. Ho catalogato i fili: sono moltissimi."),
    },
}


def write_json(path, doc, like: str | None = None) -> None:
    newline = "\r\n" if like is not None and "\r\n" in like else "\n"
    path.write_text((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").replace("\n", newline), encoding="utf-8", newline="")


def patch(faction: str, role: str, at: int, item: str, tone: str) -> None:
    path = DATA / "dialogues" / "role" / f"{role}_{tone}.json"
    raw = path.read_text(encoding="utf-8", newline="")
    doc = json.loads(raw)
    nodes = doc["nodes"]
    flag = f"faction_gift_{faction}"
    choices = [c for c in nodes["menu"]["choices"] if c.get("next") != "faction_gift"]
    nodes["menu"]["choices"] = [{"text": f"$i18n:dlg.role.faction_gift.{faction}", "next": "faction_gift",
                                 "when": {"all": [{"faction_at_least": {"faction": faction, "count": at}}, {"not": {"flag": flag}}]}}, *choices]
    nodes["faction_gift"] = {"type": "effects", "next": "faction_gift_said",
                             "effects": [{"effect": "set_flag", "flag": flag, "value": True}, {"effect": "add_item", "item": f"base:item/{item}", "qty": 1}]}
    nodes["faction_gift_said"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.faction_gift.{faction}.{tone}", "next": "end"}
    write_json(path, doc, raw)


# The gifts of the factions that have a single person (spec 07, "Factions"): Mira for the Ring of Wayfarers, Selwyn for the Chroniclers. Their
# dialogue opens with the gift, once, and then goes on as before.
# faction: (dialogue file, standing asked, item, accessory, price, name en, name it, description en, description it, line en, line it)
PERSON_GIFTS = {
    "wayfarers": ("mira", 12, "wayfarers_band", {"max_hp": 40, "mdef": 8}, 1500, "Wayfarer's band", "Fascia del viandante",
                  "Woven by the wayfarers of the Ring for one of their own. Health +40, magic defense +8.",
                  "Intessuta dai viandanti dell'Anello per uno dei loro. Vita +40, difesa magica +8.",
                  "The wayfarers asked me to give you this. They say you walk the Ring as if you had always walked it.",
                  "I viandanti mi hanno chiesto di darti questa. Dicono che percorri l'Anello come se l'avessi sempre fatto."),
    "chroniclers": ("selwyn", 5, "archivists_quill", {"matk": 12, "crit_pm": 40}, 1500, "Archivist's quill", "Penna dell'archivista",
                    "A quill that has written five legends, and remembers them. Magic attack +12, critical chance +4%.",
                    "Una penna che ha scritto cinque leggende, e se le ricorda. Attacco magico +12, probabilità di critico +4%.",
                    "Five legends written, five legends true. The Chroniclers would like you to have this quill. Mind the ink: it is old.",
                    "Cinque leggende scritte, cinque leggende vere. I Cronisti vogliono che questa penna sia tua. Attento all'inchiostro: è vecchio."),
}


def patch_person(faction: str, name: str, at: int, item: str) -> None:
    path = DATA / "dialogues" / "npc" / f"{name}.json"
    raw = path.read_text(encoding="utf-8", newline="")
    doc = json.loads(raw)
    nodes = doc["nodes"]
    flag = f"faction_gift_{faction}"
    first = nodes["faction_gift_check"]["else"] if doc["start"] == "faction_gift_check" else doc["start"]
    nodes["faction_gift_check"] = {"type": "condition", "when": {"all": [{"faction_at_least": {"faction": faction, "count": at}}, {"not": {"flag": flag}}]},
                                   "then": "faction_gift", "else": first}
    nodes["faction_gift"] = {"type": "effects", "next": "faction_gift_said",
                             "effects": [{"effect": "set_flag", "flag": flag, "value": True}, {"effect": "add_item", "item": f"base:item/{item}", "qty": 1}]}
    nodes["faction_gift_said"] = {"type": "say", "speaker": next(n["speaker"] for n in nodes.values() if n["type"] == "say" and n.get("speaker")),
                                  "text": f"$i18n:dlg.faction_gift.{faction}", "next": first}
    doc["start"] = "faction_gift_check"
    write_json(path, doc, raw)


def main() -> None:
    for faction, (role, at, item, bonus, price, name_en, name_it, desc_en, desc_it) in GIFTS.items():
        write_json(DATA / "items" / f"{item}.json", {
            "$schema": "../../../schemas/item.schema.json", "id": f"base:item/{item}", "name": f"$i18n:item.{item}.name",
            "description": f"$i18n:item.{item}.desc", "kind": "accessory", "rarity": "epic", "price": price, "accessory": bonus})
        for lang, name, desc in (("en", name_en, desc_en), ("it", name_it, desc_it)):
            set_texts("content.json", lang, {f"item.{item}.name": name, f"item.{item}.desc": desc})
        for tone in TONES:
            patch(faction, role, at, item, tone)
    for lang in ("en", "it"):
        texts = {f"dlg.role.faction_gift.{f}": line for f, line in ASK[lang].items()}
        for tone in TONES:
            clerk, elder = GIVE[lang][tone]
            texts[f"dlg.faction_gift.guild.{tone}"] = clerk
            texts[f"dlg.faction_gift.folk.{tone}"] = elder
        set_texts("roles.json", lang, texts)
    for faction, (name, at, item, bonus, price, name_en, name_it, desc_en, desc_it, line_en, line_it) in PERSON_GIFTS.items():
        write_json(DATA / "items" / f"{item}.json", {
            "$schema": "../../../schemas/item.schema.json", "id": f"base:item/{item}", "name": f"$i18n:item.{item}.name",
            "description": f"$i18n:item.{item}.desc", "kind": "accessory", "rarity": "epic", "price": price, "accessory": bonus})
        for lang, item_name, desc, line in (("en", name_en, desc_en, line_en), ("it", name_it, desc_it, line_it)):
            set_texts("content.json", lang, {f"item.{item}.name": item_name, f"item.{item}.desc": desc})
            set_texts("roles.json", lang, {f"dlg.faction_gift.{faction}": line})
        patch_person(faction, name, at, item)
    print(f"wrote {len(GIFTS) + len(PERSON_GIFTS)} gifts of the factions")


if __name__ == "__main__":
    main()
