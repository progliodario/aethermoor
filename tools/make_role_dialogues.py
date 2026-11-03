#!/usr/bin/env python3
"""Builds the role dialogues of the settlement people (data/base/dialogues/role/*.json) and their texts (i18n roles.json).

Five roles (elder, shopkeeper, innkeeper, villager, guild_clerk) speak in eight tones, one per region (spec 09, "Settlement people").
Texts may use {npc}, {place}, {region} and {quirk} (see docs/spec/07-quests-and-dialogue.md, "Dialogue arguments").
Run it after changing a text, then run tools/validate_data.py.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "base"

TONES = ["warm", "mystic", "gruff", "flowery", "stoic", "salty", "grim", "scholarly"]
ROLES = ["elder", "shopkeeper", "innkeeper", "villager", "guild_clerk"]

# --------------------------------------------------------------------------------------------- English
EN = {
    "warm": {
        "elder": "Welcome to {place}, traveller! I'm {npc}. Sit, eat, stay a while. The soup is hot and the slimes mostly stay in the fields. {quirk}",
        "shopkeeper": "{npc}'s Goods, at your service! Look around, buy something, sell something. My smile is free, the rest has a price.",
        "innkeeper": "Ah, a guest! I'm {npc}. The beds are soft and the porridge is only slightly lumpy. Rooms will be ready soon, I promise!",
        "villager": "Oh, hello! I'm {npc}. Lovely day in {place}, isn't it? Even the rain feels friendly around here.",
        "clerk_hello": "Welcome to the guild desk of {place}! I'm {npc}. Looking for honest work?",
        "rumor": "They say a stranger from another world will save us all. I hope they bring appetite, we have a lot of pie.",
    },
    "mystic": {
        "elder": "The trees spoke of your coming to {place}, wanderer. I am {npc}. Listen: in {region} the forest remembers. {quirk}",
        "shopkeeper": "I am {npc}. What you seek may be on my shelves, or may find you if you pay. The trees do not mind coin.",
        "innkeeper": "{npc} keeps the hearth here. Sleep gently, guest: the branches outside whisper, and they do not always lie.",
        "villager": "Shh... do you hear it? I'm {npc}. The leaves of {place} are telling secrets again.",
        "clerk_hello": "The guild keeps a small light in {place}. I am {npc}. Do you walk the path of work?",
        "rumor": "The old tree at the heart of the wood has not blossomed for nine springs. Something sleeps beneath it.",
    },
    "gruff": {
        "elder": "{npc}. I run {place}. We dig, we forge, we don't chatter. {quirk} State your business.",
        "shopkeeper": "{npc}. Gear's on the shelves. Prices are on the tags. Don't haggle, it's pointless.",
        "innkeeper": "{npc}. Bed's a bed. Walls are stone, they don't fall down. Don't break anything.",
        "villager": "Hm. {npc}. If you're lost, {place} is the one with the mountain on top.",
        "clerk_hello": "Guild desk, {place}. {npc}. Work or leave.",
        "rumor": "Strange tapping from the deep shafts, lately. Not ours. Nobody's down there. Nobody should be.",
    },
    "flowery": {
        "elder": "Honored guest, jewel of the desert road! I am {npc}, humble keeper of {place}. Water for you, shade for you, and the best prices anywhere! {quirk}",
        "shopkeeper": "Ah, the discerning eye! {npc} sells only treasures, and today the treasures are in stock! Look, touch, admire, and buy!",
        "innkeeper": "A traveller! I am {npc}. My rooms are cool, my tea is sweet, and my prices are a gift. Almost a gift.",
        "villager": "Peace and plenty, stranger! I am {npc}. {place} is the pearl of the sands, and I mean it with all my heart.",
        "clerk_hello": "Welcome, welcome to the guild house of {place}! {npc} at your service. Work for a man of your talent?",
        "rumor": "A caravan master swears there is an oasis that moves. I swear nothing, but I would follow him.",
    },
    "stoic": {
        "elder": "I am {npc}. This is {place}. We endure the cold, and the cold endures us. {quirk}",
        "shopkeeper": "{npc}. Goods. Prices fixed. Winter does not haggle.",
        "innkeeper": "{npc}. A fire, a bed, a bowl. Close the door behind you.",
        "villager": "{npc}. {place} is quiet. We like it that way.",
        "clerk_hello": "{npc}, guild desk of {place}. Work exists. Speak.",
        "rumor": "The ice in the old temple groans at night. It has not done that in forty winters.",
    },
    "salty": {
        "elder": "Ahoy, landlubber! {npc}, harbour-warden o' {place}. Mind the gulls, they bite. {quirk}",
        "shopkeeper": "{npc}'s Chandlery! Rope, hooks, blades an' bandages, all shipshape. Buy it or sell it, matey!",
        "innkeeper": "{npc}, at the sign o' the Drowned Boot! Beds don't rock, ale does. Rooms be ready soon enough, har har.",
        "villager": "Fair winds, friend! {npc}. {place} smells of fish and freedom, and mostly fish.",
        "clerk_hello": "Guild post o' {place}, {npc} at the wheel. Lookin' for a bit o' honest work, sailor?",
        "rumor": "A lighthouse out on the rocks lit itself last night. The keeper died forty years ago. I'm sayin' nothin'.",
    },
    "grim": {
        "elder": "I am {npc}. This is {place}. Still standing, which is more than most. {quirk}",
        "shopkeeper": "{npc}. Stock is what survived. Prices are what survival costs.",
        "innkeeper": "{npc}. A bed, a roof. Both may collapse. Tonight, probably not.",
        "villager": "Ah. A visitor. I am {npc}. {place} thanks you for noticing it. Briefly.",
        "clerk_hello": "{npc}, guild desk of {place}. Work is plentiful. Survivors are not.",
        "rumor": "The ash falls upward some nights. We stopped asking why.",
    },
    "scholarly": {
        "elder": "Ah, a visitor! {npc}, curator of {place}. Welcome, although 'welcome' is, technically, a hypothesis. {quirk}",
        "shopkeeper": "{npc}, purveyor of instruments and equipment. Prices are listed, annotated and, regrettably, non-negotiable.",
        "innkeeper": "{npc}. Accommodation, with footnotes. Do mind the third stair; it has a theory about gravity.",
        "villager": "Fascinating! A new face. I am {npc}. I study {place}. {place} has not yet agreed to be studied.",
        "clerk_hello": "{npc}, guild registrar of {place}. Employment, in the classical sense. Do you have a moment?",
        "rumor": "A floating island has drifted two degrees off its charted course. Nobody has explained it. Everybody has theories.",
    },
}

# --------------------------------------------------------------------------------------------- Italian
IT = {
    "warm": {
        "elder": "Benvenuto a {place}, viandante! Sono {npc}. Siediti, mangia, fermati un po'. La zuppa è calda e gli slime stanno quasi sempre nei campi. {quirk}",
        "shopkeeper": "Merci di {npc}, al tuo servizio! Guarda, compra, vendi. Il mio sorriso è gratis, il resto ha un prezzo.",
        "innkeeper": "Ah, un ospite! Sono {npc}. I letti sono morbidi e la polenta è solo un po' grumosa. Le stanze saranno pronte presto, promesso!",
        "villager": "Oh, ciao! Io sono {npc}. Bella giornata a {place}, vero? Qui anche la pioggia è gentile.",
        "clerk_hello": "Benvenuto allo sportello della gilda di {place}! Sono {npc}. Cerchi un lavoretto onesto?",
        "rumor": "Dicono che uno straniero da un altro mondo ci salverà tutti. Spero abbia appetito, abbiamo tanta torta.",
    },
    "mystic": {
        "elder": "Gli alberi hanno parlato del tuo arrivo a {place}, viandante. Sono {npc}. Ascolta: a {region} la foresta ricorda. {quirk}",
        "shopkeeper": "Sono {npc}. Ciò che cerchi può essere sui miei scaffali, o trovarti se paghi. Agli alberi le monete non dispiacciono.",
        "innkeeper": "{npc} custodisce il focolare. Dormi piano, ospite: i rami là fuori sussurrano, e non sempre mentono.",
        "villager": "Zitto... lo senti? Io sono {npc}. Le foglie di {place} raccontano di nuovo i loro segreti.",
        "clerk_hello": "La gilda tiene una piccola luce a {place}. Sono {npc}. Cammini sul sentiero del lavoro?",
        "rumor": "Il vecchio albero nel cuore del bosco non fiorisce da nove primavere. Qualcosa dorme sotto di lui.",
    },
    "gruff": {
        "elder": "{npc}. Comando {place}. Scaviamo, forgiamo, non chiacchieriamo. {quirk} Dì cosa vuoi.",
        "shopkeeper": "{npc}. L'attrezzatura è sugli scaffali. I prezzi sono sui cartellini. Non contrattare, è inutile.",
        "innkeeper": "{npc}. Un letto è un letto. Muri di pietra, non crollano. Non rompere niente.",
        "villager": "Hm. {npc}. Se sei perso, {place} è quello con la montagna sopra.",
        "clerk_hello": "Sportello della gilda, {place}. {npc}. Lavoro o fuori.",
        "rumor": "Strani colpi dai pozzi profondi, ultimamente. Non sono i nostri. Là sotto non c'è nessuno. Non dovrebbe esserci.",
    },
    "flowery": {
        "elder": "Ospite onorato, gioiello della via del deserto! Sono {npc}, umile custode di {place}. Acqua per te, ombra per te, e i prezzi migliori che ci siano! {quirk}",
        "shopkeeper": "Ah, che occhio raffinato! {npc} vende solo tesori, e oggi i tesori ci sono! Guarda, tocca, ammira e compra!",
        "innkeeper": "Un viaggiatore! Sono {npc}. Stanze fresche, tè dolce e prezzi che sono un regalo. Quasi un regalo.",
        "villager": "Pace e abbondanza, straniero! Sono {npc}. {place} è la perla delle sabbie, e lo dico con tutto il cuore.",
        "clerk_hello": "Benvenuto, benvenuto alla casa della gilda di {place}! {npc} al tuo servizio. Lavoro per un uomo del tuo talento?",
        "rumor": "Un capocarovana giura che esiste un'oasi che si sposta. Io non giuro nulla, ma lo seguirei.",
    },
    "stoic": {
        "elder": "Sono {npc}. Questa è {place}. Noi sopportiamo il freddo, e il freddo sopporta noi. {quirk}",
        "shopkeeper": "{npc}. Merce. Prezzi fissi. L'inverno non tratta.",
        "innkeeper": "{npc}. Un fuoco, un letto, una scodella. Chiudi la porta.",
        "villager": "{npc}. {place} è tranquilla. Ci piace così.",
        "clerk_hello": "{npc}, sportello della gilda di {place}. Il lavoro c'è. Parla.",
        "rumor": "Il ghiaccio del vecchio tempio geme di notte. Non lo faceva da quarant'anni.",
    },
    "salty": {
        "elder": "Ohé, terraiolo! {npc}, capitano del porto di {place}. Attento ai gabbiani, mordono. {quirk}",
        "shopkeeper": "Fornitura di {npc}! Corde, ami, lame e bende, tutto a posto. Compra o vendi, mozzo!",
        "innkeeper": "{npc}, all'insegna dello Stivale Annegato! I letti non ondeggiano, la birra sì. Le stanze saranno pronte presto, har har.",
        "villager": "Buon vento, amico! {npc}. {place} sa di pesce e di libertà, ma soprattutto di pesce.",
        "clerk_hello": "Posto della gilda di {place}, {npc} al timone. Cerchi un lavoretto onesto, marinaio?",
        "rumor": "Il faro sugli scogli si è acceso da solo ieri notte. Il guardiano è morto quarant'anni fa. Io non dico niente.",
    },
    "grim": {
        "elder": "Sono {npc}. Questa è {place}. Ancora in piedi, che è più di molte. {quirk}",
        "shopkeeper": "{npc}. La merce è ciò che è sopravvissuto. I prezzi sono ciò che costa sopravvivere.",
        "innkeeper": "{npc}. Un letto, un tetto. Possono crollare entrambi. Stanotte, forse no.",
        "villager": "Ah. Una visita. Sono {npc}. {place} ti ringrazia di averla notata. Per poco.",
        "clerk_hello": "{npc}, sportello della gilda di {place}. Il lavoro abbonda. I sopravvissuti no.",
        "rumor": "Certe notti la cenere cade verso l'alto. Abbiamo smesso di chiederci perché.",
    },
    "scholarly": {
        "elder": "Ah, un visitatore! {npc}, curatore di {place}. Benvenuto, anche se 'benvenuto' è, tecnicamente, un'ipotesi. {quirk}",
        "shopkeeper": "{npc}, fornitore di strumenti e attrezzature. I prezzi sono elencati, annotati e, purtroppo, non negoziabili.",
        "innkeeper": "{npc}. Alloggio, con note a piè di pagina. Attenzione al terzo gradino: ha una teoria sulla gravità.",
        "villager": "Affascinante! Una faccia nuova. Sono {npc}. Studio {place}. {place} non ha ancora accettato di essere studiata.",
        "clerk_hello": "{npc}, cancelliere della gilda di {place}. Impiego, in senso classico. Hai un momento?",
        "rumor": "Un'isola fluttuante è andata alla deriva di due gradi rispetto alla rotta. Nessuno lo spiega. Tutti hanno teorie.",
    },
}

CHOICES = {
    "en": {"wares": "Show me your wares.", "rumor": "Any news?", "bye": "Goodbye.", "work": "Show me the board."},
    "it": {"wares": "Fammi vedere la merce.", "rumor": "Novità?", "bye": "Arrivederci.", "work": "Fammi vedere la bacheca."},
}

QUIRKS = {
    "en": {
        "cheese": "{place} is famous for its sharp cheese, and for the smell.",
        "bells": "Every house in {place} has a little bell, and each one rings at its own hour.",
        "bad_luck": "{place} has terrible luck. Nobody has ever won a bet here, not even the baker.",
        "bakers": "Folk say {place} has more bakers than roofs.",
        "singing": "In {place} we sing while we work. Badly, but loudly.",
        "lanterns": "At dusk {place} lights a hundred paper lanterns, and a few of them are on fire.",
        "mushrooms": "The mushrooms of {place} glow at night. Eat them and you will, too. Briefly.",
        "kites": "Children in {place} fly kites tied to the chickens. The chickens have stopped objecting.",
        "honey": "The honey of {place} is sold three valleys away, and the bees want a word with you about it.",
        "riddles": "In {place} nobody answers a question directly. Why do you ask?",
        "cats": "There are more cats than people in {place}. The cats know it.",
        "bridges": "{place} has eleven bridges and only one river, and we are quite proud of the arithmetic.",
    },
    "it": {
        "cheese": "{place} è famosa per il suo formaggio piccante, e per l'odore.",
        "bells": "Ogni casa di {place} ha una campanella, e ognuna suona alla sua ora.",
        "bad_luck": "{place} ha una sfortuna terribile. Nessuno ha mai vinto una scommessa qui, nemmeno il fornaio.",
        "bakers": "Si dice che {place} abbia più fornai che tetti.",
        "singing": "A {place} si canta mentre si lavora. Male, ma forte.",
        "lanterns": "Al tramonto {place} accende cento lanterne di carta, e qualcuna prende fuoco.",
        "mushrooms": "I funghi di {place} brillano di notte. Mangiali e brillerai anche tu. Per poco.",
        "kites": "I bambini di {place} fanno volare gli aquiloni legati alle galline. Le galline hanno smesso di protestare.",
        "honey": "Il miele di {place} si vende a tre valli di distanza, e le api vorrebbero parlarti.",
        "riddles": "A {place} nessuno risponde direttamente a una domanda. Perché lo chiedi?",
        "cats": "A {place} ci sono più gatti che persone. I gatti lo sanno.",
        "bridges": "{place} ha undici ponti e un solo fiume, e siamo molto fieri dell'aritmetica.",
    },
}

PEOPLE_NAMES = {
    "start": ["An", "Bri", "Cor", "Dar", "El", "Fia", "Gor", "Hel", "Ing", "Jor", "Kai", "Lis", "Mar", "Nia", "Ori", "Pip", "Quin", "Rod", "Sal", "Tam", "Ulf", "Vera", "Wil", "Yan", "Zed"],
    "end": ["a", "bert", "dric", "ela", "gar", "ina", "ik", "la", "mund", "na", "o", "rin", "sa", "thor", "us", "wen", "ya", "zo"],
}


BOARD_EN = {
    "warm": {"cull": ("Slimes in the garden", "Chase off the pests bothering {place}: {target} x{count}."),
             "gather": ("Gel for the glue pot", "The folk of {place} need gel to mend things: {target} x{count}.")},
    "mystic": {"cull": ("The restless green ones", "Put to rest what drifts near {place}: {target} x{count}."),
               "gather": ("Offerings of gel", "Bring the shimmer the forest asks for to {place}: {target} x{count}.")},
    "gruff": {"cull": ("Pest control", "Kill them. {place}. {target} x{count}."),
              "gather": ("Gel. Bring it.", "{place} needs it. {target} x{count}.")},
    "flowery": {"cull": ("A noble hunt!", "Glory awaits near {place}: {target} x{count}, and a fine reward!"),
                "gather": ("A treasure of gel!", "Gather the finest gel for the merchants of {place}: {target} x{count}.")},
    "stoic": {"cull": ("Slimes", "The plains near {place}. {target} x{count}."), "gather": ("Gel", "For {place}. {target} x{count}.")},
    "salty": {"cull": ("Slimes off the starboard!", "Clear the meadows round {place}, matey: {target} x{count}."),
              "gather": ("Gel for the caulking", "Fetch caulking gel for the docks o' {place}: {target} x{count}.")},
    "grim": {"cull": ("Pests", "{place} cannot afford them. {target} x{count}."),
             "gather": ("Gel, while it lasts", "{place} needs it before winter takes it. {target} x{count}.")},
    "scholarly": {"cull": ("Population control, a field study", "Retire the specimens near {place}: {target} x{count}."),
                  "gather": ("Gel specimens for study", "A sample for the scholars of {place}: {target} x{count}.")},
}
BOARD_IT = {
    "warm": {"cull": ("Slime in giardino", "Caccia i parassiti che infastidiscono {place}: {target} x{count}."),
             "gather": ("Gel per il barattolo della colla", "La gente di {place} ha bisogno di gel per aggiustare le cose: {target} x{count}.")},
    "mystic": {"cull": ("Le verdi inquiete", "Metti a riposo ciò che vaga vicino a {place}: {target} x{count}."),
               "gather": ("Offerte di gel", "Porta a {place} il bagliore che la foresta chiede: {target} x{count}.")},
    "gruff": {"cull": ("Disinfestazione", "Ammazzali. {place}. {target} x{count}."),
              "gather": ("Gel. Portalo.", "{place} ne ha bisogno. {target} x{count}.")},
    "flowery": {"cull": ("Una nobile caccia!", "La gloria ti attende vicino a {place}: {target} x{count}, e un'ottima ricompensa!"),
                "gather": ("Un tesoro di gel!", "Raccogli il gel più pregiato per i mercanti di {place}: {target} x{count}.")},
    "stoic": {"cull": ("Slime", "Le pianure vicino a {place}. {target} x{count}."), "gather": ("Gel", "Per {place}. {target} x{count}.")},
    "salty": {"cull": ("Slime a dritta!", "Ripulisci i prati intorno a {place}, mozzo: {target} x{count}."),
              "gather": ("Gel per calafatare", "Porta il gel per calafatare ai moli di {place}: {target} x{count}.")},
    "grim": {"cull": ("Parassiti", "{place} non può permetterseli. {target} x{count}."),
             "gather": ("Gel, finché dura", "{place} ne ha bisogno prima che l'inverno se lo prenda. {target} x{count}.")},
    "scholarly": {"cull": ("Controllo della popolazione, uno studio sul campo", "Metti a riposo gli esemplari vicino a {place}: {target} x{count}."),
                  "gather": ("Esemplari di gel per lo studio", "Un campione per gli studiosi di {place}: {target} x{count}.")},
}


def node_say(text_key: str, next_node: str = "end") -> dict:
    return {"type": "say", "speaker": "npc", "text": f"$i18n:{text_key}", "next": next_node}


def dialogue(role: str, tone: str) -> dict:
    base = f"dlg.role.{role}.{tone}"
    nodes: dict[str, dict] = {}
    rumor_choice = {"text": "$i18n:dlg.role.rumor", "next": "rumor"}
    bye_choice = {"text": "$i18n:dlg.role.bye", "next": "end"}
    if role == "shopkeeper":
        nodes["start"] = node_say(f"{base}.hello", "menu")
        nodes["menu"] = {"type": "choice", "choices": [{"text": "$i18n:dlg.role.wares", "next": "shop"}, rumor_choice, bye_choice]}
        nodes["shop"] = {"type": "effects", "effects": [{"effect": "open_shop"}], "next": "end"}
    elif role != "guild_clerk":
        nodes["start"] = node_say(f"{base}.hello", "menu")
        nodes["menu"] = {"type": "choice", "choices": [rumor_choice, bye_choice]}
    else:
        nodes["start"] = node_say(f"{base}.hello", "menu")
        nodes["menu"] = {"type": "choice", "choices": [{"text": "$i18n:dlg.role.work", "next": "board"}, rumor_choice, bye_choice]}
        nodes["board"] = {"type": "effects", "effects": [{"effect": "open_board"}], "next": "end"}
    nodes["rumor"] = node_say(f"dlg.tone.{tone}.rumor")
    return {"$schema": "../../../../schemas/dialogue.schema.json", "id": f"base:dialogue/role/{role}_{tone}", "start": "start", "nodes": nodes}


def texts(lang: str) -> dict[str, str]:
    table = EN if lang == "en" else IT
    out: dict[str, str] = {}
    for tone in TONES:
        t = table[tone]
        for role in ("elder", "shopkeeper", "innkeeper", "villager"):
            out[f"dlg.role.{role}.{tone}.hello"] = t[role]
        out[f"dlg.role.guild_clerk.{tone}.hello"] = t["clerk_hello"]
        for template, (title, journal) in (BOARD_EN if lang == "en" else BOARD_IT)[tone].items():
            out[f"quest.board.{template}.{tone}.name"] = title
            out[f"quest.board.{template}.{tone}.journal"] = journal
        out[f"dlg.tone.{tone}.rumor"] = t["rumor"]
    for key, value in CHOICES[lang].items():
        out[f"dlg.role.{key}"] = value
    for key, value in QUIRKS[lang].items():
        out[f"quirk.{key}"] = value
    return out


def main() -> None:
    out_dir = DATA / "dialogues" / "role"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.json"):
        old.unlink()
    for role in ROLES:
        for tone in TONES:
            data = dialogue(role, tone)
            (out_dir / f"{role}_{tone}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for lang in ("en", "it"):
        path = DATA / "i18n" / lang / "roles.json"
        path.write_text(json.dumps({"$schema": "../../../../schemas/i18n.schema.json", **texts(lang)}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(ROLES) * len(TONES)} dialogues and {len(texts('en'))} texts per language")
    print("people names:", json.dumps(PEOPLE_NAMES))


if __name__ == "__main__":
    main()
