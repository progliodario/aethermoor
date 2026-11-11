#!/usr/bin/env python3
"""Writes the two hand-written towns of Verdalis: Fenwick (the village of the start) and Aldermere (the town of the mother guild),
and the named person of every outpost (`towns_outposts.py`).

For each named person: a dialogue (`data/base/dialogues/npc/<name>.json`), their quests (`data/base/quests/side/`), the texts in both
languages, and their place in the world data (`npcs`); Aldermere is also a landmark with the stamp of a town. Run it after changing the
tables here; it changes only its own lines of the world data."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "base"
WORLD = DATA / "worlds" / "overworld.json"

# The village of the start is `home` of the world data (stamp `village`, anchor 10,7 at 36,40); Aldermere is a new landmark.
ALDERMERE = {"id": "aldermere", "name": "Aldermere", "stamp": "base:stamp/town", "kind": "town", "dx": 384, "dy": -128}

# person: key (also the speaker), file name, look, tile (dx, dy from the center of the world), name (en, it), lines, quests.
# lines: hello (before the first quest is offered), and for every quest: offer, busy, thanks; `after` when everything is done.
# quest: id, name, task (journal), objectives, rewards (xp, gold, guild points, items).
PEOPLE = [
    {
        "key": "fenwick_elder_bran", "file": "bran", "variant": "brown", "dx": 33, "dy": 41,
        "name": ("Bran Alder, elder of Fenwick", "Bran Alder, anziano di Fenwick"),
        "after": ("Fenwick sleeps well since you came, Guest. Sit by the well whenever you like.", "Fenwick dorme bene da quando sei arrivato, Ospite. Siediti al pozzo quando vuoi."),
        "quests": [
            {
                "id": "fenwick_gardens", "name": ("The Gardens of Fenwick", "Gli orti di Fenwick"),
                "task": ("Green slimes are eating the gardens of Fenwick. Clear them out for Elder Bran.", "Gli slime verdi mangiano gli orti di Fenwick. Scacciali per l'anziano Bran."),
                "objectives": [{"type": "kill", "enemy": "base:enemy/slime_green", "count": 6}],
                "rewards": {"xp": 60, "gold": 80, "points": 5, "items": {"base:item/bread": 3}},
                "offer": ("Welcome to Fenwick, Guest. Lyra sends us one of you every few years, and every time the slimes notice first. They are in the cabbages again. Would you?",
                          "Benvenuto a Fenwick, Ospite. Lyra ce ne manda uno ogni qualche anno, e ogni volta i primi ad accorgersene sono gli slime. Sono di nuovo nei cavoli. Ci pensi tu?"),
                "busy": ("Six of them, the green ones. They pop. Do not stand too close.", "Sei, quelli verdi. Scoppiano. Non stare troppo vicino."),
                "thanks": ("That was quick. It took the last Guest a week and a ladder. Take some bread.", "Che rapidità. L'ultimo Ospite ci mise una settimana e una scala. Prendi del pane."),
            },
            {
                "id": "fenwick_wolves", "name": ("Wolves on the Aldermere Road", "Lupi sulla strada per Aldermere"),
                "task": ("Tawny wolves keep the carts of Fenwick from the road to Aldermere. Thin the pack and bring two furs.", "I lupi fulvi tengono i carri di Fenwick lontani dalla strada per Aldermere. Sfoltisci il branco e porta due pellicce."),
                "objectives": [{"type": "kill", "enemy": "base:enemy/wolf_tawny", "count": 5}, {"type": "collect", "item": "base:item/tawny_fur", "count": 2}],
                "rewards": {"xp": 120, "gold": 160, "points": 10, "items": {"base:item/leather_vest": 1}},
                "offer": ("The carts to Aldermere have not left in a month. Wolves, to the east, on the road. For you it is a morning walk, I suspect.",
                          "I carri per Aldermere non partono da un mese. Lupi, a est, sulla strada. Per te sarà una passeggiata, sospetto."),
                "busy": ("Five wolves and two furs. The tanner will do the rest.", "Cinque lupi e due pellicce. Al resto pensa il conciatore."),
                "thanks": ("The carts leave tomorrow. The tanner made you this. It fits everyone, he says, which worries me.", "I carri partono domani. Il conciatore ti ha fatto questa. Sta bene a tutti, dice, e la cosa mi preoccupa."),
            },
        ],
    },
    {
        "key": "fenwick_baker_odile", "file": "odile", "variant": "ochre", "dx": 40, "dy": 42,
        "name": ("Odile, baker of Fenwick", "Odile, fornaia di Fenwick"),
        "after": ("The oven is warm and the door is open. That is all a village needs.", "Il forno è caldo e la porta è aperta. A un villaggio non serve altro."),
        "quests": [
            {
                "id": "fenwick_cakes", "name": ("Berries for the Oven", "Bacche per il forno"),
                "task": ("Odile needs wild berries and healing herbs for her honey cakes. The bushes around Fenwick have both.", "A Odile servono bacche selvatiche ed erbe curative per le torte al miele. I cespugli intorno a Fenwick hanno entrambe."),
                "objectives": [{"type": "collect", "item": "base:item/wild_berries", "count": 6}, {"type": "collect", "item": "base:item/healing_herb", "count": 2}],
                "rewards": {"xp": 50, "gold": 40, "points": 0, "items": {"base:item/honey_cake": 4}},
                "offer": ("You have the look of someone who has not eaten since another world. I can fix that, if you bring me berries. The bushes are full; shake them.",
                          "Hai la faccia di chi non mangia da un altro mondo. Posso rimediare, se mi porti delle bacche. I cespugli sono pieni: scuotili."),
                "busy": ("Six handfuls of berries and two herbs. Do not eat them on the way. Everyone does.", "Sei manciate di bacche e due erbe. Non mangiarle per strada. Lo fanno tutti."),
                "thanks": ("Four cakes for you, and the smell for the whole street.", "Quattro torte per te, e il profumo per tutta la via."),
            },
        ],
    },
    {
        "key": "fenwick_child_tobin", "file": "tobin", "variant": "teal", "dx": 41, "dy": 39,
        "name": ("Tobin, of Fenwick", "Tobin, di Fenwick"),
        "after": ("When I grow up I am going to be a Guest. Bran says it does not work like that. Bran is old.", "Da grande farò l'Ospite. Bran dice che non funziona così. Bran è vecchio."),
        "quests": [
            {
                "id": "fenwick_letter", "name": ("A Letter for the Guild", "Una lettera per la gilda"),
                "task": ("Tobin wrote to the mother guild in Aldermere, east of Fenwick, a little to the north. Take his letter to Quartermaster Rook.", "Tobin ha scritto alla gilda madre di Aldermere, a est di Fenwick, un po' a nord. Porta la sua lettera al quartiermastro Rook."),
                "objectives": [{"type": "talk", "npc_key": "aldermere_quartermaster_rook"}],
                "rewards": {"xp": 80, "gold": 60, "points": 5, "items": {}},
                "offer": ("Are you the Guest? Really? Can you take a letter to the guild in Aldermere? It says I want to join. I am nine. I wrote that I am twelve.",
                          "Sei tu l'Ospite? Davvero? Puoi portare una lettera alla gilda di Aldermere? Dice che voglio entrare. Ho nove anni. Ho scritto dodici."),
                "busy": ("Aldermere is east, a little north, past the wolves. Give it to the quartermaster. He has a beard like a broom.", "Aldermere è a est, un po' a nord, dopo i lupi. Dalla al quartiermastro. Ha una barba che sembra una scopa."),
                "thanks": ("He read it? He READ it? What did the beard do?", "L'ha letta? L'ha LETTA? E la barba cosa ha fatto?"),
            },
        ],
    },
    {
        "key": "aldermere_guildmaster_hestia", "file": "hestia", "variant": "red", "dx": 382, "dy": -130,
        "name": ("Hestia Vane, guildmaster of Aldermere", "Hestia Vane, maestra della gilda di Aldermere"),
        "after": ("The board is yours, Guest. Leave something for the others; they need the practice.", "La bacheca è tua, Ospite. Lascia qualcosa agli altri: hanno bisogno di esercizio."),
        "quests": [
            {
                "id": "aldermere_trial", "name": ("The Trial of Aldermere", "La prova di Aldermere"),
                "task": ("Guildmaster Hestia asks every newcomer the same thing: six mint slimes and four myconids from the meadows around Aldermere.", "La maestra Hestia chiede a ogni nuovo arrivato la stessa cosa: sei slime alla menta e quattro miconidi dei prati intorno ad Aldermere."),
                "objectives": [{"type": "kill", "enemy": "base:enemy/slime_mint", "count": 6}, {"type": "kill", "enemy": "base:enemy/myconid", "count": 4}],
                "rewards": {"xp": 200, "gold": 250, "points": 30, "items": {"base:item/potion_medium": 2}},
                "offer": ("So you are the one Mira wrote about. This is the mother guild; every rank in the world begins at this desk. The trial is the same for all. Most take three days.",
                          "Dunque sei tu quello di cui ha scritto Mira. Questa è la gilda madre: ogni rango del mondo comincia a questo banco. La prova è la stessa per tutti. Di solito ci vogliono tre giorni."),
                "busy": ("Six mint slimes, four myconids. Take your time. Nobody does, of your kind.", "Sei slime alla menta, quattro miconidi. Fai con calma. Quelli come te non lo fanno mai."),
                "thanks": ("Before lunch. Of course. I will stop being surprised by Guests one of these years.", "Prima di pranzo. Naturalmente. Uno di questi anni smetterò di stupirmi degli Ospiti."),
            },
            {
                "id": "aldermere_crown", "name": ("A Crown of Gel", "Una corona di gelatina"),
                "task": ("The Gel King rules a cellar in Verdalis and no party of the guild has come back with dry boots. Guildmaster Hestia wants it gone.", "Il Re Gelatina regna su una cantina di Verdalis e nessuna squadra della gilda è tornata con gli stivali asciutti. La maestra Hestia lo vuole eliminato."),
                "objectives": [{"type": "kill", "enemy": "base:enemy/gel_king", "count": 1}],
                "rewards": {"xp": 400, "gold": 600, "points": 60, "items": {"base:item/steel_sword": 1}},
                "offer": ("There is a slime with a crown in a cellar west of here, not far from Fenwick. Three parties tried. All three came back sticky. I would like a fourth opinion.",
                          "C'è uno slime con la corona in una cantina a ovest di qui, non lontano da Fenwick. Ci hanno provato tre squadre. Sono tornate tutte e tre appiccicose. Vorrei un quarto parere."),
                "busy": ("The Gel King. You will know it by the crown, and by the size.", "Il Re Gelatina. Lo riconosci dalla corona, e dalla stazza."),
                "thanks": ("One blow, the scouts said. One. Take this sword; it was meant for whoever managed it, and I had given up hope of handing it over.",
                           "Un colpo solo, dicono gli esploratori. Uno. Prendi questa spada: era per chi ci fosse riuscito, e avevo perso la speranza di consegnarla."),
            },
        ],
    },
    {
        "key": "aldermere_quartermaster_rook", "file": "rook", "variant": "green", "dx": 386, "dy": -127,
        "name": ("Rook, quartermaster of the guild", "Rook, quartiermastro della gilda"),
        "after": ("Stores are full. First time since I took the job. Do not tell the guildmaster, she will find a use for them.", "I magazzini sono pieni. La prima volta da quando ho questo incarico. Non dirlo alla maestra, troverebbe come svuotarli."),
        "quests": [
            {
                "id": "aldermere_stores", "name": ("Stores for the Guild", "Scorte per la gilda"),
                "task": ("Quartermaster Rook needs iron ore and wood for the guild's stores. Rocks and trees give both to whoever asks firmly.", "Al quartiermastro Rook servono minerale di ferro e legna per le scorte della gilda. Rocce e alberi danno entrambi a chi chiede con decisione."),
                "objectives": [{"type": "collect", "item": "base:item/iron_ore", "count": 4}, {"type": "collect", "item": "base:item/wood_log", "count": 6}],
                "rewards": {"xp": 150, "gold": 200, "points": 15, "items": {"base:item/pike": 1}},
                "offer": ("A letter? From Fenwick? ...Nine years old, by the handwriting. I will keep it. Since you are here and have two arms: I am short of ore and of wood.",
                          "Una lettera? Da Fenwick? ...Nove anni, dalla calligrafia. La tengo. Visto che sei qui e hai due braccia: mi mancano ferro e legna."),
                "busy": ("Four of ore, six logs. Rocks and trees. They do not fight back, mostly.", "Quattro di ferro, sei ceppi. Rocce e alberi. Non reagiscono, di solito."),
                "thanks": ("Counted twice. All there. Take a pike from the rack; it is the one thing I have too many of.", "Contato due volte. C'è tutto. Prendi una picca dalla rastrelliera: è l'unica cosa di cui ne ho troppe."),
            },
        ],
    },
    {
        "key": "aldermere_archivist_selwyn", "file": "selwyn", "variant": "purple", "dx": 382, "dy": -126,
        "name": ("Selwyn, archivist of the guild", "Selwyn, archivista della gilda"),
        "after": ("I have started a new shelf. It is labelled 'Things the Guest did'. It is already full.", "Ho cominciato uno scaffale nuovo. C'è scritto 'Cose fatte dall'Ospite'. È già pieno."),
        "quests": [
            {
                "id": "aldermere_samples", "name": ("Samples for the Archive", "Campioni per l'archivio"),
                "task": ("Archivist Selwyn is writing the guild's bestiary and wants slime gel and spore caps to study.", "L'archivista Selwyn sta scrivendo il bestiario della gilda e vuole gelatina di slime e cappelle di spore da studiare."),
                "objectives": [{"type": "collect", "item": "base:item/slime_gel", "count": 5}, {"type": "collect", "item": "base:item/spore_cap", "count": 3}],
                "rewards": {"xp": 180, "gold": 220, "points": 20, "items": {"base:item/potion_mana_small": 3}},
                "offer": ("A Guest! Do not move. No, do move, I need samples. Gel, five jars' worth, and three spore caps. For the bestiary. You keep one too, I am told, in your head.",
                          "Un Ospite! Non muoverti. Anzi muoviti, mi servono campioni. Gelatina, cinque vasetti, e tre cappelle di spore. Per il bestiario. Ne tieni uno anche tu, mi dicono, in testa."),
                "busy": ("Five of gel, three caps. Label them if you can. Nobody ever labels them.", "Cinque di gelatina, tre cappelle. Etichettali, se puoi. Nessuno li etichetta mai."),
                "thanks": ("Unlabelled. Perfect anyway. Have these; I mix them myself and only one in ten explodes.", "Senza etichetta. Perfetti lo stesso. Prendi queste: le preparo io e ne esplode solo una su dieci."),
            },
        ],
    },
]


def _outposts() -> list:
    from towns_outposts import OUTPOST_PEOPLE as people  # imported late: that table imports nothing from here, but keep the two files independent

    return people


def quest_id(q: dict) -> str:
    return f"base:quest/side/{q['id']}"


def dialogue_of(person: dict) -> dict:
    """Thanks for the last quest finished (once), then the next quest: its offer, or a reminder while it is open; `after` when all are done."""
    key, name = person["key"], person["file"]
    nodes: dict[str, dict] = {}

    def say(text: str, then: str) -> dict:
        return {"type": "say", "speaker": key, "text": f"$i18n:dlg.town.{name}.{text}", "next": then}

    quests = person["quests"]
    for i, q in enumerate(quests):
        nxt = f"c{i + 1}" if i + 1 < len(quests) else "after"
        thanked = f"town_{q['id']}_thanked"
        nodes[f"c{i}"] = {"type": "condition", "when": {"quest_done": quest_id(q)}, "then": f"t{i}", "else": f"a{i}"}
        nodes[f"t{i}"] = {"type": "condition", "when": {"flag": thanked}, "then": nxt, "else": f"thanks{i}"}
        nodes[f"thanks{i}"] = say(f"{q['id']}.thanks", f"flag{i}")
        nodes[f"flag{i}"] = {"type": "effects", "effects": [{"effect": "set_flag", "flag": thanked, "value": True}], "next": "end"}
        nodes[f"a{i}"] = {"type": "condition", "when": {"quest_active": quest_id(q)}, "then": f"busy{i}", "else": f"offer{i}"}
        nodes[f"busy{i}"] = say(f"{q['id']}.busy", "end")
        nodes[f"offer{i}"] = say(f"{q['id']}.offer", f"choice{i}")
        nodes[f"choice{i}"] = {"type": "choice", "choices": [
            {"text": "$i18n:dlg.wayfarer.accept", "effects": [{"effect": "start_quest", "quest": quest_id(q)}], "next": "end"},
            {"text": "$i18n:dlg.wayfarer.later", "next": "end"}]}
    nodes["after"] = say("after", "end")
    return {"$schema": "../../../../schemas/dialogue.schema.json", "id": f"base:dialogue/npc/{name}", "start": "c0", "nodes": nodes}


def quest_of(q: dict) -> dict:
    r = q["rewards"]
    rewards = [{"effect": "add_xp", "amount": r["xp"]}, {"effect": "add_gold", "amount": r["gold"]}]
    if r["points"]:
        rewards.append({"effect": "add_guild_points", "amount": r["points"]})
    rewards += [{"effect": "add_item", "item": item, "qty": qty} for item, qty in r["items"].items()]
    return {"$schema": "../../../../schemas/quest.schema.json", "id": quest_id(q), "name": f"$i18n:quest.{q['id']}.name", "kind": "side",
            "stages": [{"id": "task", "journal": f"$i18n:quest.{q['id']}.task", "objectives": q["objectives"], "next": "end"}], "rewards": rewards}


def set_texts(file: str, lang: str, entries: dict[str, str]) -> None:
    """Sets texts in an i18n file: the keys that exist are replaced in place, the new ones go before the last line of the object."""
    path = DATA / "i18n" / lang / file
    raw = path.read_text(encoding="utf-8", newline="")
    newline = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.replace("\r\n", "\n").split("\n")
    where = {line.split('"')[1]: k for k, line in enumerate(lines) if line.startswith('  "')}
    last = max(where.values())
    new = []
    for key, value in entries.items():
        if key in where:
            comma = "," if lines[where[key]].rstrip().endswith(",") else ""
            lines[where[key]] = f'  "{key}": {json.dumps(value, ensure_ascii=False)}{comma}'
        else:
            new.append(f'  "{key}": {json.dumps(value, ensure_ascii=False)},')
    if new:
        lines[last:last] = new  # before the last entry, which keeps its place and its missing comma
    path.write_text(newline.join(lines), encoding="utf-8", newline="")


OUTPOST_PEOPLE: list = []


def patch_world() -> None:
    """Adds the landmark of Aldermere and the people to the world data, one line each, leaving every other line as it is."""
    raw = WORLD.read_text(encoding="utf-8", newline="")
    newline = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.replace("\r\n", "\n").split("\n")

    def last_of_array(name: str) -> int:
        start = next(k for k, line in enumerate(lines) if line.strip().startswith(f'"{name}": ['))
        return next(k for k in range(start, len(lines)) if lines[k].strip().startswith("]")) - 1

    def add(name: str, marker: str, entry: dict) -> None:
        text = "    { " + ", ".join(f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in entry.items()) + " }"
        found = [k for k, line in enumerate(lines) if marker in line]
        if found:
            lines[found[0]] = text + ("," if lines[found[0]].rstrip().endswith(",") else "")
            return
        last = last_of_array(name)
        if not lines[last].rstrip().endswith(","):
            lines[last] = lines[last].rstrip() + ","
        lines.insert(last + 1, text)

    add("landmarks", f'"id": "{ALDERMERE["id"]}"', ALDERMERE)
    for p in PEOPLE + OUTPOST_PEOPLE:
        add("npcs", f'"key": "{p["key"]}"', {"key": p["key"], "dialogue": f"base:dialogue/npc/{p['file']}", "variant": p["variant"], "dx": p["dx"], "dy": p["dy"]})
    WORLD.write_text(newline.join(lines), encoding="utf-8", newline="")


def main() -> None:
    global OUTPOST_PEOPLE
    OUTPOST_PEOPLE = _outposts()
    core = {"en": {}, "it": {}}
    content = {"en": {}, "it": {}}
    quests = 0
    for p in PEOPLE + OUTPOST_PEOPLE:
        (DATA / "dialogues" / "npc" / f"{p['file']}.json").write_text(json.dumps(dialogue_of(p), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        for i, lang in enumerate(("en", "it")):
            core[lang][f"speaker.{p['key']}"] = p["name"][i]
            core[lang][f"dlg.town.{p['file']}.after"] = p["after"][i]
        for q in p["quests"]:
            quests += 1
            (DATA / "quests" / "side" / f"{q['id']}.json").write_text(json.dumps(quest_of(q), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            for i, lang in enumerate(("en", "it")):
                for part in ("offer", "busy", "thanks"):
                    core[lang][f"dlg.town.{p['file']}.{q['id']}.{part}"] = q[part][i]
                content[lang][f"quest.{q['id']}.name"] = q["name"][i]
                content[lang][f"quest.{q['id']}.task"] = q["task"][i]
    for lang in ("en", "it"):
        set_texts("core.json", lang, core[lang])
        set_texts("content.json", lang, content[lang])
    patch_world()
    print(f"wrote {len(PEOPLE) + len(OUTPOST_PEOPLE)} people and {quests} quests")


if __name__ == "__main__":
    main()
    __import__("set_quest_places").main()  # the guardians' places (spec 07, "Places")
