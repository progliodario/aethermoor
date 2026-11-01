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
QUEST = "base:quest/guild/slime_extermination"

# --------------------------------------------------------------------------------------------- English
EN = {
    "warm": {
        "elder": "Welcome to {place}, traveller! I'm {npc}. Sit, eat, stay a while. The soup is hot and the slimes mostly stay in the fields. {quirk}",
        "shopkeeper": "{npc}'s Goods, at your service! The shelves are being restocked, but my smile is free and always in stock.",
        "innkeeper": "Ah, a guest! I'm {npc}. The beds are soft and the porridge is only slightly lumpy. Rooms will be ready soon, I promise!",
        "villager": "Oh, hello! I'm {npc}. Lovely day in {place}, isn't it? Even the rain feels friendly around here.",
        "clerk_hello": "Welcome to the guild desk of {place}! I'm {npc}. Looking for honest work?",
        "clerk_offer": "A pest problem! Green slimes are chewing up the plains. Five of them, and the guild pays a fair price. Interested?",
        "clerk_accepted": "Wonderful! Come back safe, and with all your fingers. The soup will be waiting.",
        "clerk_busy": "Still on the slimes? Take your time. Well, a little less time than that.",
        "clerk_thanks": "The slimes are gone and my desk is quiet again. You're a hero, and I mean it kindly.",
        "rumor": "They say a stranger from another world will save us all. I hope they bring appetite, we have a lot of pie.",
    },
    "mystic": {
        "elder": "The trees spoke of your coming to {place}, wanderer. I am {npc}. Listen: in {region} the forest remembers. {quirk}",
        "shopkeeper": "I am {npc}. What you seek may be on my shelves, or on a shelf not yet built. Return when the moon is thin.",
        "innkeeper": "{npc} keeps the hearth here. Sleep gently, guest: the branches outside whisper, and they do not always lie.",
        "villager": "Shh... do you hear it? I'm {npc}. The leaves of {place} are telling secrets again.",
        "clerk_hello": "The guild keeps a small light in {place}. I am {npc}. Do you walk the path of work?",
        "clerk_offer": "Green creatures drift over the plains like lost thoughts. Five must be put to rest. Will you walk that path?",
        "clerk_accepted": "May the roots guide your steps. Return when the task is done, or the task has done you.",
        "clerk_busy": "The path is not yet walked to its end. The slimes still wander.",
        "clerk_thanks": "The plains are calm. The leaves say your name now. Do not let it go to your head.",
        "rumor": "The old tree at the heart of the wood has not blossomed for nine springs. Something sleeps beneath it.",
    },
    "gruff": {
        "elder": "{npc}. I run {place}. We dig, we forge, we don't chatter. {quirk} State your business.",
        "shopkeeper": "{npc}. Shelves are bare, the forge is hot. Come back when it isn't.",
        "innkeeper": "{npc}. Bed's a bed. Walls are stone, they don't fall down. Don't break anything.",
        "villager": "Hm. {npc}. If you're lost, {place} is the one with the mountain on top.",
        "clerk_hello": "Guild desk, {place}. {npc}. Work or leave.",
        "clerk_offer": "Slimes on the plains. Five. Kill them. Guild pays. Take it or don't.",
        "clerk_accepted": "Good. Don't die. Paperwork's a nightmare.",
        "clerk_busy": "Not done. Go kill slimes.",
        "clerk_thanks": "Done, then. Fine work. Don't let it swell your head. The ceilings are low.",
        "rumor": "Strange tapping from the deep shafts, lately. Not ours. Nobody's down there. Nobody should be.",
    },
    "flowery": {
        "elder": "Honored guest, jewel of the desert road! I am {npc}, humble keeper of {place}. Water for you, shade for you, and the best prices anywhere! {quirk}",
        "shopkeeper": "Ah, the discerning eye! {npc} sells only treasures. Alas, today the treasures are in the caravan. Tomorrow! Tomorrow, my friend!",
        "innkeeper": "A traveller! I am {npc}. My rooms are cool, my tea is sweet, and my prices are a gift. Almost a gift.",
        "villager": "Peace and plenty, stranger! I am {npc}. {place} is the pearl of the sands, and I mean it with all my heart.",
        "clerk_hello": "Welcome, welcome to the guild house of {place}! {npc} at your service. Work for a man of your talent?",
        "clerk_offer": "Slimes, my friend! Five green villains upon the plains. The guild pays handsomely, I would never say otherwise. Shall we shake on it?",
        "clerk_accepted": "A pleasure! A pure pleasure! Go, and may the sands bless your blade.",
        "clerk_busy": "Still hunting? A great hunter takes his time. A good hunter, a little less.",
        "clerk_thanks": "Magnificent! The plains sing your name! Between us, the guild would pay more, but I have said nothing.",
        "rumor": "A caravan master swears there is an oasis that moves. I swear nothing, but I would follow him.",
    },
    "stoic": {
        "elder": "I am {npc}. This is {place}. We endure the cold, and the cold endures us. {quirk}",
        "shopkeeper": "{npc}. The stock is low. Winter takes what it takes.",
        "innkeeper": "{npc}. A fire, a bed, a bowl. Close the door behind you.",
        "villager": "{npc}. {place} is quiet. We like it that way.",
        "clerk_hello": "{npc}, guild desk of {place}. Work exists. Speak.",
        "clerk_offer": "Slimes. Five. The plains. The guild pays. Accept or do not.",
        "clerk_accepted": "So be it. Return alive.",
        "clerk_busy": "Unfinished. The cold is patient. The slimes are not.",
        "clerk_thanks": "It is done. You did well. Rest.",
        "rumor": "The ice in the old temple groans at night. It has not done that in forty winters.",
    },
    "salty": {
        "elder": "Ahoy, landlubber! {npc}, harbour-warden o' {place}. Mind the gulls, they bite. {quirk}",
        "shopkeeper": "{npc}'s Chandlery! Rope, hooks, a fine bit o' tar. The crates be still in the hold, matey, come back at low tide.",
        "innkeeper": "{npc}, at the sign o' the Drowned Boot! Beds don't rock, ale does. Rooms be ready soon enough, har har.",
        "villager": "Fair winds, friend! {npc}. {place} smells of fish and freedom, and mostly fish.",
        "clerk_hello": "Guild post o' {place}, {npc} at the wheel. Lookin' for a bit o' honest work, sailor?",
        "clerk_offer": "Slimes! Five o' the green wretches in the meadows, bold as barnacles. Guild pays fair coin. Sign on?",
        "clerk_accepted": "That's the spirit! Fair winds, and don't fall overboard.",
        "clerk_busy": "Still battlin' slimes? The tide waits for no one, but it waits more than I do.",
        "clerk_thanks": "Slimes be gone! Ye did fine work, matey. Drinks be on the guild. Probably.",
        "rumor": "A lighthouse out on the rocks lit itself last night. The keeper died forty years ago. I'm sayin' nothin'.",
    },
    "grim": {
        "elder": "I am {npc}. This is {place}. Still standing, which is more than most. {quirk}",
        "shopkeeper": "{npc}. Nothing in stock. Everything burns eventually.",
        "innkeeper": "{npc}. A bed, a roof. Both may collapse. Tonight, probably not.",
        "villager": "Ah. A visitor. I am {npc}. {place} thanks you for noticing it. Briefly.",
        "clerk_hello": "{npc}, guild desk of {place}. Work is plentiful. Survivors are not.",
        "clerk_offer": "Green slimes, five. The plains still hold them. A rare mercy: easy work. Take it before it ends.",
        "clerk_accepted": "Go. Try not to be part of the ash.",
        "clerk_busy": "Still alive? Good sign. Still unfinished. Bad one.",
        "clerk_thanks": "Done. It will not last, but it was done. That is something.",
        "rumor": "The ash falls upward some nights. We stopped asking why.",
    },
    "scholarly": {
        "elder": "Ah, a visitor! {npc}, curator of {place}. Welcome, although 'welcome' is, technically, a hypothesis. {quirk}",
        "shopkeeper": "{npc}, purveyor of instruments and curiosities. My catalogue is incomplete; so, I confess, is my inventory.",
        "innkeeper": "{npc}. Accommodation, with footnotes. Do mind the third stair; it has a theory about gravity.",
        "villager": "Fascinating! A new face. I am {npc}. I study {place}. {place} has not yet agreed to be studied.",
        "clerk_hello": "{npc}, guild registrar of {place}. Employment, in the classical sense. Do you have a moment?",
        "clerk_offer": "A field survey: five green slimes on the plains, to be... retired. The guild compensates the researcher. Your answer, please.",
        "clerk_accepted": "Excellent. Do record your observations; the guild library accepts them gladly.",
        "clerk_busy": "The survey remains incomplete. The data, as ever, is wriggling.",
        "clerk_thanks": "Conclusive results! The plains are, as hypothesised, slime-free. Citation pending.",
        "rumor": "A floating island has drifted two degrees off its charted course. Nobody has explained it. Everybody has theories.",
    },
}

# --------------------------------------------------------------------------------------------- Italian
IT = {
    "warm": {
        "elder": "Benvenuto a {place}, viandante! Sono {npc}. Siediti, mangia, fermati un po'. La zuppa è calda e gli slime stanno quasi sempre nei campi. {quirk}",
        "shopkeeper": "Merci di {npc}, al tuo servizio! Gli scaffali si stanno riempiendo, ma il mio sorriso è gratis e non finisce mai.",
        "innkeeper": "Ah, un ospite! Sono {npc}. I letti sono morbidi e la polenta è solo un po' grumosa. Le stanze saranno pronte presto, promesso!",
        "villager": "Oh, ciao! Io sono {npc}. Bella giornata a {place}, vero? Qui anche la pioggia è gentile.",
        "clerk_hello": "Benvenuto allo sportello della gilda di {place}! Sono {npc}. Cerchi un lavoretto onesto?",
        "clerk_offer": "Un problema di parassiti! Gli slime verdi rosicchiano le pianure. Cinque, e la gilda paga il giusto. Ti interessa?",
        "clerk_accepted": "Meraviglioso! Torna sano e con tutte le dita. La zuppa ti aspetta.",
        "clerk_busy": "Ancora con gli slime? Prenditi il tuo tempo. Un po' meno di così, però.",
        "clerk_thanks": "Gli slime sono spariti e il mio sportello è tranquillo. Sei un eroe, e lo dico con affetto.",
        "rumor": "Dicono che uno straniero da un altro mondo ci salverà tutti. Spero abbia appetito, abbiamo tanta torta.",
    },
    "mystic": {
        "elder": "Gli alberi hanno parlato del tuo arrivo a {place}, viandante. Sono {npc}. Ascolta: a {region} la foresta ricorda. {quirk}",
        "shopkeeper": "Sono {npc}. Ciò che cerchi forse è sui miei scaffali, o su uno scaffale non ancora costruito. Torna a luna sottile.",
        "innkeeper": "{npc} custodisce il focolare. Dormi piano, ospite: i rami là fuori sussurrano, e non sempre mentono.",
        "villager": "Zitto... lo senti? Io sono {npc}. Le foglie di {place} raccontano di nuovo i loro segreti.",
        "clerk_hello": "La gilda tiene una piccola luce a {place}. Sono {npc}. Cammini sul sentiero del lavoro?",
        "clerk_offer": "Creature verdi vagano per le pianure come pensieri smarriti. Cinque vanno messe a riposo. Percorrerai quel sentiero?",
        "clerk_accepted": "Le radici guidino i tuoi passi. Torna quando il compito è finito, o quando ha finito te.",
        "clerk_busy": "Il sentiero non è ancora percorso fino in fondo. Gli slime vagano ancora.",
        "clerk_thanks": "Le pianure sono calme. Le foglie ora dicono il tuo nome. Non montarti la testa.",
        "rumor": "Il vecchio albero nel cuore del bosco non fiorisce da nove primavere. Qualcosa dorme sotto di lui.",
    },
    "gruff": {
        "elder": "{npc}. Comando {place}. Scaviamo, forgiamo, non chiacchieriamo. {quirk} Dì cosa vuoi.",
        "shopkeeper": "{npc}. Scaffali vuoti, forgia accesa. Torna quando è spenta.",
        "innkeeper": "{npc}. Un letto è un letto. Muri di pietra, non crollano. Non rompere niente.",
        "villager": "Hm. {npc}. Se sei perso, {place} è quello con la montagna sopra.",
        "clerk_hello": "Sportello della gilda, {place}. {npc}. Lavoro o fuori.",
        "clerk_offer": "Slime sulle pianure. Cinque. Ammazzali. La gilda paga. Prendere o lasciare.",
        "clerk_accepted": "Bene. Non morire. Le scartoffie sono un incubo.",
        "clerk_busy": "Non è finita. Vai ad ammazzare slime.",
        "clerk_thanks": "Fatto, allora. Buon lavoro. Non gonfiarti la testa. I soffitti sono bassi.",
        "rumor": "Strani colpi dai pozzi profondi, ultimamente. Non sono i nostri. Là sotto non c'è nessuno. Non dovrebbe esserci.",
    },
    "flowery": {
        "elder": "Ospite onorato, gioiello della via del deserto! Sono {npc}, umile custode di {place}. Acqua per te, ombra per te, e i prezzi migliori che ci siano! {quirk}",
        "shopkeeper": "Ah, che occhio raffinato! {npc} vende solo tesori. Ahimè, oggi i tesori sono in carovana. Domani! Domani, amico mio!",
        "innkeeper": "Un viaggiatore! Sono {npc}. Stanze fresche, tè dolce e prezzi che sono un regalo. Quasi un regalo.",
        "villager": "Pace e abbondanza, straniero! Sono {npc}. {place} è la perla delle sabbie, e lo dico con tutto il cuore.",
        "clerk_hello": "Benvenuto, benvenuto alla casa della gilda di {place}! {npc} al tuo servizio. Lavoro per un uomo del tuo talento?",
        "clerk_offer": "Slime, amico mio! Cinque furfanti verdi sulle pianure. La gilda paga generosamente, non direi mai il contrario. Ci stringiamo la mano?",
        "clerk_accepted": "Un piacere! Un puro piacere! Va', e che le sabbie benedicano la tua lama.",
        "clerk_busy": "Ancora a caccia? Un grande cacciatore si prende il suo tempo. Un buon cacciatore, un po' meno.",
        "clerk_thanks": "Magnifico! Le pianure cantano il tuo nome! Tra noi, la gilda pagherebbe di più, ma non ho detto nulla.",
        "rumor": "Un capocarovana giura che esiste un'oasi che si sposta. Io non giuro nulla, ma lo seguirei.",
    },
    "stoic": {
        "elder": "Sono {npc}. Questa è {place}. Noi sopportiamo il freddo, e il freddo sopporta noi. {quirk}",
        "shopkeeper": "{npc}. Le scorte sono poche. L'inverno prende ciò che prende.",
        "innkeeper": "{npc}. Un fuoco, un letto, una scodella. Chiudi la porta.",
        "villager": "{npc}. {place} è tranquilla. Ci piace così.",
        "clerk_hello": "{npc}, sportello della gilda di {place}. Il lavoro c'è. Parla.",
        "clerk_offer": "Slime. Cinque. Le pianure. La gilda paga. Accetta o no.",
        "clerk_accepted": "E sia. Torna vivo.",
        "clerk_busy": "Incompiuto. Il freddo è paziente. Gli slime no.",
        "clerk_thanks": "È fatto. Hai fatto bene. Riposa.",
        "rumor": "Il ghiaccio del vecchio tempio geme di notte. Non lo faceva da quarant'anni.",
    },
    "salty": {
        "elder": "Ohé, terraiolo! {npc}, capitano del porto di {place}. Attento ai gabbiani, mordono. {quirk}",
        "shopkeeper": "Fornitura di {npc}! Corde, ami, una bella mano di catrame. Le casse sono ancora nella stiva, mozzo, torna con la bassa marea.",
        "innkeeper": "{npc}, all'insegna dello Stivale Annegato! I letti non ondeggiano, la birra sì. Le stanze saranno pronte presto, har har.",
        "villager": "Buon vento, amico! {npc}. {place} sa di pesce e di libertà, ma soprattutto di pesce.",
        "clerk_hello": "Posto della gilda di {place}, {npc} al timone. Cerchi un lavoretto onesto, marinaio?",
        "clerk_offer": "Slime! Cinque di quei miserabili verdi nei prati, sfacciati come cozze. La gilda paga in monete sante. Ti arruoli?",
        "clerk_accepted": "Questo è lo spirito! Buon vento, e non cadere in mare.",
        "clerk_busy": "Ancora in battaglia con gli slime? La marea non aspetta nessuno, ma aspetta più di me.",
        "clerk_thanks": "Slime spariti! Bel lavoro, mozzo. I drink li offre la gilda. Probabilmente.",
        "rumor": "Il faro sugli scogli si è acceso da solo ieri notte. Il guardiano è morto quarant'anni fa. Io non dico niente.",
    },
    "grim": {
        "elder": "Sono {npc}. Questa è {place}. Ancora in piedi, che è più di molte. {quirk}",
        "shopkeeper": "{npc}. Niente in magazzino. Tutto prima o poi brucia.",
        "innkeeper": "{npc}. Un letto, un tetto. Possono crollare entrambi. Stanotte, forse no.",
        "villager": "Ah. Una visita. Sono {npc}. {place} ti ringrazia di averla notata. Per poco.",
        "clerk_hello": "{npc}, sportello della gilda di {place}. Il lavoro abbonda. I sopravvissuti no.",
        "clerk_offer": "Slime verdi, cinque. Le pianure li tengono ancora. Una rara grazia: lavoro facile. Prendilo prima che finisca.",
        "clerk_accepted": "Va'. Cerca di non finire nella cenere.",
        "clerk_busy": "Ancora vivo? Buon segno. Ancora incompiuto. Cattivo segno.",
        "clerk_thanks": "Fatto. Non durerà, ma è fatto. È qualcosa.",
        "rumor": "Certe notti la cenere cade verso l'alto. Abbiamo smesso di chiederci perché.",
    },
    "scholarly": {
        "elder": "Ah, un visitatore! {npc}, curatore di {place}. Benvenuto, anche se 'benvenuto' è, tecnicamente, un'ipotesi. {quirk}",
        "shopkeeper": "{npc}, fornitore di strumenti e curiosità. Il mio catalogo è incompleto; lo è, confesso, anche il mio magazzino.",
        "innkeeper": "{npc}. Alloggio, con note a piè di pagina. Attenzione al terzo gradino: ha una teoria sulla gravità.",
        "villager": "Affascinante! Una faccia nuova. Sono {npc}. Studio {place}. {place} non ha ancora accettato di essere studiata.",
        "clerk_hello": "{npc}, cancelliere della gilda di {place}. Impiego, in senso classico. Hai un momento?",
        "clerk_offer": "Un rilievo sul campo: cinque slime verdi nelle pianure, da... mandare in pensione. La gilda compensa il ricercatore. La tua risposta, prego.",
        "clerk_accepted": "Eccellente. Registra le tue osservazioni; la biblioteca della gilda le accoglie volentieri.",
        "clerk_busy": "Il rilievo resta incompleto. I dati, come sempre, si dimenano.",
        "clerk_thanks": "Risultati conclusivi! Le pianure sono, come ipotizzato, prive di slime. Citazione in attesa.",
        "rumor": "Un'isola fluttuante è andata alla deriva di due gradi rispetto alla rotta. Nessuno lo spiega. Tutti hanno teorie.",
    },
}

CHOICES = {
    "en": {"rumor": "Any news?", "bye": "Goodbye.", "work": "I'm looking for work.", "accept": "I'll take it.", "decline": "Not now."},
    "it": {"rumor": "Novità?", "bye": "Arrivederci.", "work": "Cerco lavoro.", "accept": "Ci sto.", "decline": "Non adesso."},
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


def node_say(text_key: str, next_node: str = "end") -> dict:
    return {"type": "say", "speaker": "npc", "text": f"$i18n:{text_key}", "next": next_node}


def dialogue(role: str, tone: str) -> dict:
    base = f"dlg.role.{role}.{tone}"
    nodes: dict[str, dict] = {}
    rumor_choice = {"text": "$i18n:dlg.role.rumor", "next": "rumor"}
    bye_choice = {"text": "$i18n:dlg.role.bye", "next": "end"}
    if role != "guild_clerk":
        nodes["start"] = node_say(f"{base}.hello", "menu")
        nodes["menu"] = {"type": "choice", "choices": [rumor_choice, bye_choice]}
    else:
        nodes["start"] = {"type": "condition", "when": {"quest_done": QUEST}, "then": "thanks", "else": "active_check"}
        nodes["active_check"] = {"type": "condition", "when": {"quest_active": QUEST}, "then": "busy", "else": "hello"}
        nodes["hello"] = node_say(f"{base}.hello", "menu")
        nodes["menu"] = {"type": "choice", "choices": [
            {"text": "$i18n:dlg.role.work", "next": "offer"}, rumor_choice, bye_choice]}
        nodes["offer"] = node_say(f"{base}.offer", "offer_choice")
        nodes["offer_choice"] = {"type": "choice", "choices": [
            {"text": "$i18n:dlg.role.accept", "effects": [{"effect": "start_quest", "quest": QUEST}], "next": "accepted"},
            {"text": "$i18n:dlg.role.decline", "next": "end"}]}
        nodes["accepted"] = node_say(f"{base}.accepted")
        nodes["busy"] = node_say(f"{base}.busy")
        nodes["thanks"] = node_say(f"{base}.thanks")
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
        for part in ("offer", "accepted", "busy", "thanks"):
            out[f"dlg.role.guild_clerk.{tone}.{part}"] = t[f"clerk_{part}"]
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
