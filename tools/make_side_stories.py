#!/usr/bin/env python3
"""Writes the side stories of the protagonists (spec 18, "Side stories"; item D of the operating program): for a protagonist, three
quests from a person of the world, one after the other, and an ending that the player chooses in a dialogue (it changes the thing the
Guest takes home). The person talks to everyone, but tells the story only to whoever carries the keepsake of that protagonist (the
condition `has_item`, the same way Maren and Pip tell theirs).

Wave 9a (D1): Ren and Haruka, both in Aldermere. It writes the people into the world data (`npcs`, one line each, written again in
place), their dialogues, the quests and their texts (it and en); it can be run any number of times. Then run `make_catalog.py` and
`make_facts.py`; the clients' tests count the named people of the world (`desktop/tests/combat_test.cpp`, `WorldGenTest.kt`).
"""
from __future__ import annotations

import json

from make_towns import DATA, WORLD, set_texts

# the person: key (also the speaker), file, look, tile (dx, dy from the center of the world), the protagonist, name (en, it);
# lines (en, it): stranger (to everyone else), hello (to the protagonist, before the first quest), after (when all is told);
# quests: id, name, task, objectives, xp, gold, offer, busy, thanks; ending: the question and two answers, each (text, item, reply).
STORIES = [
    {
        "key": "aldermere_ledger_keeper_bertram", "file": "bertram", "variant": "brown", "dx": 381, "dy": -127, "protagonist": "ren",
        "name": ("Bertram Quill, keeper of the guild's ledgers", "Bertram Quill, custode dei registri della gilda"),
        "stranger": ("Not now, Guest, not now. Four hundred forms, one quill, and the quill is losing.",
                     "Non ora, Ospite, non ora. Quattrocento moduli, una penna, e la penna sta perdendo."),
        "hello": ("You... you have the look. The tired eyes of someone who has filed things. You have filed things, haven't you?",
                  "Tu... tu hai lo sguardo. Gli occhi stanchi di chi ha archiviato cose. Tu hai archiviato cose, vero?"),
        "after": ("The archive has never been so tidy. I sleep at night now. Eight hours. I had forgotten the number existed.",
                  "L'archivio non è mai stato così in ordine. Ora la notte dormo. Otto ore. Avevo dimenticato che il numero esistesse."),
        "quests": [
            ("side_ren_1", ("Overtime: The Ledgers", "Straordinari: i registri"),
             ("Bring six spider silks to Bertram Quill in Aldermere: the guild's ledgers fell apart and need binding again.",
              "Porta sei sete di ragno a Bertram Quill ad Aldermere: i registri della gilda si sono sfasciati e vanno rilegati."),
             [{"type": "collect", "item": "base:item/spider_silk", "count": 6}], 400, 300,
             ("The ledgers of the guild came apart. Every page, at once, on a Monday. I need silk to bind them, the cave spiders make the best. "
              "Six threads. You will understand: in your world too, I bet, the binding always fails on a Monday.",
              "I registri della gilda si sono sfasciati. Tutte le pagine, insieme, di lunedì. Mi serve seta per rilegarli, i ragni delle grotte "
              "fanno la migliore. Sei fili. Tu capirai: anche nel tuo mondo, scommetto, la rilegatura cede sempre di lunedì."),
             ("Six spider silks. The pages are waiting in a heap, and the heap is judging me.",
              "Sei sete di ragno. Le pagine aspettano in un mucchio, e il mucchio mi giudica."),
             ("Perfect thread. Look at that binding. You are wasted on monsters, you know.",
              "Filo perfetto. Guarda che rilegatura. Sei sprecato con i mostri, sai.")),
            ("side_ren_2", ("Overtime: An Audit of Wolves", "Straordinari: una verifica dei lupi"),
             ("The farmers filed three hundred complaints about the grey wolves. Bertram's idea of closing them: eight fewer wolves.",
              "I contadini hanno presentato trecento reclami sui lupi grigi. L'idea di Bertram per chiuderli: otto lupi in meno."),
             [{"type": "kill", "enemy": "base:enemy/wolf_grey", "count": 8}], 800, 600,
             ("Three hundred and twelve complaints about the grey wolves. I could answer each one with a letter. Or you could make the "
              "letters unnecessary. Eight wolves, and I stamp them all 'resolved'.",
              "Trecentododici reclami sui lupi grigi. Potrei rispondere a ciascuno con una lettera. Oppure potresti rendere le lettere "
              "inutili tu. Otto lupi, e li timbro tutti 'risolto'."),
             ("Eight grey wolves. I have the stamp ready. It is a very satisfying stamp.",
              "Otto lupi grigi. Ho il timbro pronto. È un timbro molto soddisfacente."),
             ("Resolved, resolved, resolved... three hundred and twelve times. My wrist hurts and I have never been happier.",
              "Risolto, risolto, risolto... trecentododici volte. Mi fa male il polso e non sono mai stato così felice.")),
            ("side_ren_3", ("Overtime: The Annual Report", "Straordinari: la relazione annuale"),
             ("Empty suits of armor keep doing their rounds in the old halls and send the guild their reports. Stop three of them.",
              "Armature vuote continuano a fare il giro delle vecchie sale e mandano alla gilda le loro relazioni. Fermane tre."),
             [{"type": "kill", "enemy": "base:enemy/hollow_armor", "count": 3}], 1600, 1200,
             ("The last thing. There are empty suits of armor out there, hollow, nobody inside, and still they walk their rounds and send "
              "us reports. Every day. Nobody reads them. They do not stop. In your world I think you called them middle management.",
              "L'ultima cosa. Là fuori ci sono armature vuote, cave, senza nessuno dentro, e camminano lo stesso il loro giro e ci mandano "
              "relazioni. Ogni giorno. Nessuno le legge. Non si fermano. Nel tuo mondo credo li chiamaste quadri intermedi."),
             ("Three hollow suits of armor. Retire them. Kindly, if you can; firmly, if you must.",
              "Tre armature cave. Mandale in pensione. Con gentilezza, se puoi; con fermezza, se devi."),
             ("No reports today. None! The silence of an inbox that is empty. You have done in a month what I could not do in twenty years.",
              "Nessuna relazione oggi. Nessuna! Il silenzio di una posta vuota. Hai fatto in un mese quello che io non ho fatto in vent'anni.")),
        ],
        "ending": {
            "ask": ("So, Ren. I have to ask, the guild makes me. The post of head of the archive is free. A desk, a quill of your own, "
                    "a window. Or... you came to this world to stop doing exactly this. Which is it?",
                    "Allora, Ren. Devo chiedertelo, la gilda mi obbliga. Il posto di capo dell'archivio è libero. Una scrivania, una penna "
                    "tutta tua, una finestra. Oppure... sei venuto in questo mondo proprio per smettere di fare questo. Che cosa scegli?"),
            "a": (("Take the desk. Someone has to keep the world in order.", "Prendo la scrivania. Qualcuno deve tenere in ordine il mondo."),
                  "base:item/archivists_quill",
                  ("Then this is yours: the quill of the head archivist. It writes faster than you think, and it never asks for overtime.",
                   "Allora questa è tua: la penna del capo archivista. Scrive più in fretta di quanto pensi, e non chiede mai straordinari.")),
            "b": (("No. I am done with desks. The road is my office now.", "No. Ho chiuso con le scrivanie. Ora il mio ufficio è la strada."),
                  "base:item/wayfarers_band",
                  ("Good. Truly. Take this band of the wayfarers: someone who walks away from a desk should walk far.",
                   "Bene. Davvero. Prendi questa fascia dei viandanti: chi si allontana da una scrivania deve andare lontano.")),
        },
    },
    {
        "key": "aldermere_stablekeeper_mirela", "file": "mirela", "variant": "green", "dx": 387, "dy": -127, "protagonist": "haruka",
        "name": ("Mirela, keeper of the guild's stables", "Mirela, custode delle stalle della gilda"),
        "stranger": ("Mind the elk, Guest, he bites the ones he does not know. He does not know anyone.",
                     "Attento all'alce, Ospite, morde quelli che non conosce. Non conosce nessuno."),
        "hello": ("He let you come close. The elk. He never lets anyone come close. Who are you?",
                  "Ti ha lasciato avvicinare. L'alce. Non lascia avvicinare nessuno. Chi sei?"),
        "after": ("The stables are quiet. Sometimes I catch myself talking to the animals the way you do. They answer more, I swear.",
                  "Le stalle sono tranquille. A volte mi sorprendo a parlare agli animali come fai tu. Rispondono di più, lo giuro."),
        "quests": [
            ("side_haruka_1", ("A Patient with a Cough", "Un paziente con la tosse"),
             ("Mirela's old elk has a cough. Bring five healing herbs and three mint leaves for a warm compress.",
              "Il vecchio alce di Mirela ha la tosse. Porta cinque erbe medicinali e tre foglie di menta per un impacco caldo."),
             [{"type": "collect", "item": "base:item/healing_herb", "count": 5}, {"type": "collect", "item": "base:item/mint_leaf", "count": 3}],
             400, 300,
             ("You are a healer? Of animals? Then look at him: he coughs at night, he will not eat oats. I tried everything I know, and "
              "what I know is horses. Herbs, I think. You will know which.",
              "Sei una guaritrice? Di animali? Allora guardalo: tossisce la notte, non mangia l'avena. Ho provato tutto quello che so, e "
              "quello che so sono i cavalli. Erbe, credo. Tu saprai quali."),
             ("Five healing herbs and three mint leaves, you said. I wrote it down. I never write anything down.",
              "Cinque erbe medicinali e tre foglie di menta, hai detto. L'ho scritto. Io non scrivo mai niente."),
             ("He ate. He ate everything, and then my hat. I have never been so glad to lose a hat.",
              "Ha mangiato. Ha mangiato tutto, e poi il mio cappello. Non sono mai stata così contenta di perdere un cappello.")),
            ("side_haruka_2", ("The Frightened Herd", "La mandria spaventata"),
             ("Tawny wolves circle the pastures of the stables at night, and the herd does not sleep. Send six of them away.",
              "I lupi fulvi girano attorno ai pascoli delle stalle la notte, e la mandria non dorme. Allontanane sei."),
             [{"type": "kill", "enemy": "base:enemy/wolf_tawny", "count": 6}], 800, 600,
             ("The herd has not slept in a week. Tawny wolves, every night, in a circle, patient. They do not even attack: they wait. "
              "I do not want them dead, if there is another way. You, I think, know another way.",
              "La mandria non dorme da una settimana. Lupi fulvi, ogni notte, in cerchio, pazienti. Non attaccano neanche: aspettano. "
              "Non li voglio morti, se c'è un altro modo. Tu, credo, conosci un altro modo."),
             ("Six of the tawny wolves. However you do it, I will not ask.", "Sei dei lupi fulvi. Comunque tu lo faccia, non lo chiederò."),
             ("The herd sleeps. All of them, in a heap, like puppies. Even the bull. Especially the bull.",
              "La mandria dorme. Tutti, in un mucchio, come cuccioli. Anche il toro. Soprattutto il toro.")),
            ("side_haruka_3", ("A Home for the Lost", "Una casa per chi si è perso"),
             ("A young ridge elk lost its herd and wanders hurt in the hills. The bloom slimes follow it. Calm four of them and bring "
              "two slime gels for a salve.",
              "Un giovane alce delle creste ha perso la mandria e vaga ferito per le colline. Gli slime fioriti lo seguono. Calmane quattro "
              "e porta due gel di slime per un unguento."),
             [{"type": "kill", "enemy": "base:enemy/slime_bloom", "count": 4}, {"type": "collect", "item": "base:item/slime_gel", "count": 2}],
             1600, 1200,
             ("There is a calf in the hills. A ridge elk, young, lost. He limps, and the bloom slimes follow him around like a flock of "
              "worried aunts. Calm them, and bring gel for a salve. Then we will see where he belongs.",
              "C'è un piccolo sulle colline. Un alce delle creste, giovane, perso. Zoppica, e gli slime fioriti lo seguono come uno stormo "
              "di zie preoccupate. Calmali, e porta del gel per un unguento. Poi vedremo a chi appartiene."),
             ("Four bloom slimes and two gels. He is waiting by the old oak, they say.",
              "Quattro slime fioriti e due gel. Dicono che aspetti vicino alla vecchia quercia."),
             ("He is here. He walked in by himself, behind you, the whole way. The leg will heal.",
              "È qui. È entrato da solo, dietro di te, per tutta la strada. La zampa guarirà.")),
        ],
        "ending": {
            "ask": ("And now the question I have been avoiding. He follows you, Haruka. He could stay here with the herd, safe, fed, "
                    "warm. Or you could take him back to the hills, where he was born, and let him find his own. You decide.",
                    "E adesso la domanda che evito da giorni. Ti segue, Haruka. Potrebbe restare qui con la mandria, al sicuro, nutrito, "
                    "al caldo. Oppure potresti riportarlo sulle colline, dove è nato, e lasciare che trovi i suoi. Decidi tu."),
            "a": (("Let him stay with the herd. He has had enough of being alone.", "Lascialo con la mandria. È stato solo abbastanza."),
                  "base:item/folk_charm",
                  ("Then he stays. The stable children carved you this charm: they say it brings luck to whoever gives a home.",
                   "Allora resta. I bambini delle stalle ti hanno intagliato questo amuleto: dicono che porta fortuna a chi dà una casa.")),
            "b": (("Take him back to the hills. That is where his family is.", "Riportiamolo sulle colline. La sua famiglia è lì."),
                  "base:item/owl_charm",
                  ("The hills, then. Take this charm: the herders wear it when they let an animal go. It sees far, they say, so it can watch over him.",
                   "Le colline, allora. Prendi questo amuleto: i pastori lo portano quando lasciano andare un animale. Vede lontano, dicono, così può vegliare su di lui.")),
        },
    },
]


def quest_id(qid: str) -> str:
    return f"base:quest/side/{qid}"


def dialogue_of(story: dict) -> dict:
    """The keepsake first: everyone else hears a line; the protagonist hears the quests one after the other (thanks, then the next offer or
    a reminder while it is open), then the ending, chosen once, then `after`."""
    key, file, who = story["key"], story["file"], story["protagonist"]
    nodes: dict[str, dict] = {}

    def say(text: str, then: str) -> dict:
        return {"type": "say", "speaker": key, "text": f"$i18n:dlg.side.{file}.{text}", "next": then}

    nodes["start"] = {"type": "condition", "when": {"has_item": {"item": f"base:item/keepsake_{who}", "qty": 1}}, "then": "met", "else": "stranger"}
    nodes["stranger"] = say("stranger", "end")
    met = f"side_{who}_met"
    nodes["met"] = {"type": "condition", "when": {"flag": met}, "then": "c0", "else": "hello"}
    nodes["hello"] = say("hello", "hello_flag")
    nodes["hello_flag"] = {"type": "effects", "effects": [{"effect": "set_flag", "flag": met, "value": True}], "next": "c0"}
    quests = story["quests"]
    for i, (qid, *_rest) in enumerate(quests):
        nxt = f"c{i + 1}" if i + 1 < len(quests) else "ending_check"
        thanked = f"{qid}_thanked"
        nodes[f"c{i}"] = {"type": "condition", "when": {"quest_done": quest_id(qid)}, "then": f"t{i}", "else": f"a{i}"}
        nodes[f"t{i}"] = {"type": "condition", "when": {"flag": thanked}, "then": nxt, "else": f"thanks{i}"}
        nodes[f"thanks{i}"] = say(f"{qid}.thanks", f"flag{i}")
        nodes[f"flag{i}"] = {"type": "effects", "effects": [{"effect": "set_flag", "flag": thanked, "value": True}], "next": nxt}
        nodes[f"a{i}"] = {"type": "condition", "when": {"quest_active": quest_id(qid)}, "then": f"busy{i}", "else": f"offer{i}"}
        nodes[f"busy{i}"] = say(f"{qid}.busy", "end")
        nodes[f"offer{i}"] = say(f"{qid}.offer", f"choice{i}")
        nodes[f"choice{i}"] = {"type": "choice", "choices": [
            {"text": "$i18n:dlg.wayfarer.accept", "effects": [{"effect": "start_quest", "quest": quest_id(qid)}], "next": "end"},
            {"text": "$i18n:dlg.wayfarer.later", "next": "end"}]}
    ended = f"side_{who}_ended"
    nodes["ending_check"] = {"type": "condition", "when": {"flag": ended}, "then": "after", "else": "ending"}
    nodes["ending"] = say("ending", "ending_choice")
    choices = []
    for side in ("a", "b"):
        _text, item, _reply = story["ending"][side]
        choices.append({"text": f"$i18n:dlg.side.{file}.choice_{side}", "next": f"reply_{side}", "effects": [
            {"effect": "set_flag", "flag": ended, "value": True}, {"effect": "set_flag", "flag": f"side_{who}_chose_{side}", "value": True},
            {"effect": "add_item", "item": item, "qty": 1}]})
        nodes[f"reply_{side}"] = say(f"reply_{side}", "end")
    nodes["ending_choice"] = {"type": "choice", "choices": choices}
    nodes["after"] = say("after", "end")
    return {"$schema": "../../../../schemas/dialogue.schema.json", "id": f"base:dialogue/npc/{file}", "start": "start", "nodes": nodes}


def quest_of(quest: tuple) -> dict:
    qid, _name, _task, objectives, xp, gold, *_lines = quest
    return {"$schema": "../../../../schemas/quest.schema.json", "id": quest_id(qid), "name": f"$i18n:quest.{qid}.name", "kind": "side",
            "faction": "folk", "stages": [{"id": "task", "journal": f"$i18n:quest.{qid}.task", "objectives": objectives, "next": "end"}],
            "rewards": [{"effect": "add_xp", "amount": xp}, {"effect": "add_gold", "amount": gold}]}


def patch_world() -> None:
    """The people in `npcs` of the world data, one line each: a line that has the key is written again, a new one goes at the end."""
    raw = WORLD.read_text(encoding="utf-8", newline="")
    newline = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.replace("\r\n", "\n").split("\n")
    start = next(k for k, line in enumerate(lines) if line.strip().startswith('"npcs": ['))
    for story in STORIES:
        entry = {"key": story["key"], "dialogue": f"base:dialogue/npc/{story['file']}", "variant": story["variant"], "dx": story["dx"], "dy": story["dy"]}
        text = "    { " + ", ".join(f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in entry.items()) + " }"
        found = [k for k, line in enumerate(lines) if f'"key": "{story["key"]}"' in line]
        if found:
            lines[found[0]] = text + ("," if lines[found[0]].rstrip().endswith(",") else "")
            continue
        last = next(k for k in range(start, len(lines)) if lines[k].strip().startswith("]")) - 1
        if not lines[last].rstrip().endswith(","):
            lines[last] = lines[last].rstrip() + ","
        lines.insert(last + 1, text)
    out = newline.join(lines)
    json.loads(out)
    WORLD.write_text(out, encoding="utf-8", newline="")


def main() -> None:
    core: dict[str, dict[str, str]] = {"en": {}, "it": {}}
    content: dict[str, dict[str, str]] = {"en": {}, "it": {}}
    for story in STORIES:
        for item in ("base:item/keepsake_" + story["protagonist"], story["ending"]["a"][1], story["ending"]["b"][1]):
            assert (DATA / "items" / (item.split("/")[-1] + ".json")).exists(), item
        file = story["file"]
        path = DATA / "dialogues" / "npc" / f"{file}.json"
        path.write_text(json.dumps(dialogue_of(story), indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        for quest in story["quests"]:
            qid, name, task, _objectives, _xp, _gold, offer, busy, thanks = quest
            text = json.dumps(quest_of(quest), indent=2, ensure_ascii=False) + "\n"
            (DATA / "quests" / "side" / f"{qid}.json").write_text(text, encoding="utf-8", newline="\n")
            for i, lang in enumerate(("en", "it")):
                content[lang].update({f"quest.{qid}.name": name[i], f"quest.{qid}.task": task[i]})
                core[lang].update({f"dlg.side.{file}.{qid}.offer": offer[i], f"dlg.side.{file}.{qid}.busy": busy[i],
                                   f"dlg.side.{file}.{qid}.thanks": thanks[i]})
        for i, lang in enumerate(("en", "it")):
            core[lang].update({f"speaker.{story['key']}": story["name"][i], f"dlg.side.{file}.stranger": story["stranger"][i],
                               f"dlg.side.{file}.hello": story["hello"][i], f"dlg.side.{file}.after": story["after"][i],
                               f"dlg.side.{file}.ending": story["ending"]["ask"][i]})
            for side in ("a", "b"):
                text, _item, reply = story["ending"][side]
                core[lang].update({f"dlg.side.{file}.choice_{side}": text[i], f"dlg.side.{file}.reply_{side}": reply[i]})
    patch_world()
    for lang in ("en", "it"):
        set_texts("core.json", lang, core[lang])
        set_texts("content.json", lang, content[lang])
    print(f"wrote the side stories of {len(STORIES)} protagonists ({sum(len(s['quests']) for s in STORIES)} quests)")


if __name__ == "__main__":
    main()
