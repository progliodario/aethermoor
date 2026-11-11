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


# One more quest for each person of Fenwick and Aldermere, after the others (the dialogue offers them in order).
def _q(qid, name, task, objectives, xp, gold, points, items, offer, busy, thanks) -> dict:
    return {"id": qid, "name": name, "task": task, "objectives": objectives, "rewards": {"xp": xp, "gold": gold, "points": points, "items": items},
            "offer": offer, "busy": busy, "thanks": thanks}


MORE_QUESTS = {
    "fenwick_elder_bran": _q(
        "fenwick_mushrooms", ("Mushrooms in the Well", "Funghi nel pozzo"),
        ("Myconids have crept up to the well of Fenwick. Elder Bran asks you to drive four away and bring their caps to the healer.",
         "I miconidi sono arrivati fino al pozzo di Fenwick. L'anziano Bran ti chiede di scacciarne quattro e portare le loro cappelle alla guaritrice."),
        [{"type": "kill", "enemy": "base:enemy/myconid", "count": 4}, {"type": "collect", "item": "base:item/spore_cap", "count": 3}],
        160, 200, 12, {"base:item/potion_medium": 2},
        ("There is a mushroom in the well, Guest. A big one. It walks. I am old enough to have seen everything, and I had not seen that.",
         "C'è un fungo nel pozzo, Ospite. Uno grosso. Cammina. Sono abbastanza vecchio da aver visto di tutto, e quello non l'avevo visto."),
        ("Four of the walking mushrooms, and three caps for the healer.", "Quattro funghi che camminano, e tre cappelle per la guaritrice."),
        ("Clean water again. The healer says the caps make a fine potion; she sends you two.", "Di nuovo acqua pulita. La guaritrice dice che le cappelle fanno una buona pozione: te ne manda due.")),
    "fenwick_baker_odile": _q(
        "fenwick_mint", ("Mint for the Pastry", "Menta per i dolci"),
        ("Odile wants mint leaves for a new pastry. The mint slimes around Fenwick carry the freshest.",
         "Odile vuole foglie di menta per un dolce nuovo. Le più fresche le portano gli slime alla menta attorno a Fenwick."),
        [{"type": "kill", "enemy": "base:enemy/slime_mint", "count": 5}, {"type": "collect", "item": "base:item/mint_leaf", "count": 4}],
        110, 90, 0, {"base:item/honey_cake": 4, "base:item/travel_ration": 2},
        ("I have an idea for a pastry, and the idea is green. The mint slimes keep the best leaves. They are cool to the touch; they will not mind a hot oven, I hope.",
         "Ho un'idea per un dolce, e l'idea è verde. Le foglie migliori le tengono gli slime alla menta. Sono freschi al tatto: spero non gli dispiaccia un forno caldo."),
        ("Five mint slimes, four leaves.", "Cinque slime alla menta, quattro foglie."),
        ("Taste. No, taste properly. Cakes and rations for the road, and the recipe has your name now.", "Assaggia. No, assaggia per bene. Torte e razioni per la strada, e la ricetta ora porta il tuo nome.")),
    "fenwick_child_tobin": _q(
        "fenwick_gel_king", ("The King Under the Cellar", "Il re sotto la cantina"),
        ("Tobin swears a king of slimes lives in the Mossveil Cellar, north of Fenwick. Go and see; if he is there, end his reign.",
         "Tobin giura che nella Mossveil Cellar, a nord di Fenwick, vive un re degli slime. Vai a vedere: se c'è, metti fine al suo regno."),
        [{"type": "kill", "enemy": "base:enemy/gel_king", "count": 1}],
        180, 120, 10, {"base:item/minty_charm": 1},
        ("There is a king in the old cellar! A slime king, with a crown! Nobody believes me. You believe me. You are a Guest, Guests believe everything.",
         "C'è un re nella vecchia cantina! Un re slime, con la corona! Nessuno mi crede. Tu mi credi. Sei un Ospite, gli Ospiti credono a tutto."),
        ("The Gel King, in the Mossveil Cellar. I told you. I TOLD everyone.", "Il Re Gelatina, nella Mossveil Cellar. Te l'avevo detto. L'avevo detto a TUTTI."),
        ("You saw him? With the crown? I knew it. Here, my lucky charm. I do not need luck any more, I have a Guest.",
         "L'hai visto? Con la corona? Lo sapevo. Tieni, il mio portafortuna. Non mi serve più la fortuna, ho un Ospite.")),
    "aldermere_guildmaster_hestia": _q(
        "aldermere_dire_alpha", ("The Alpha of the Dire Den", "L'Alfa atroce della Dire Den"),
        ("The guild has a standing bounty on the Dire Alpha of the Dire Den, in Ironspine. Hestia thinks it is time someone collected it.",
         "La gilda ha una taglia aperta sull'Alfa atroce della Dire Den, a Ironspine. Hestia pensa che sia ora che qualcuno la riscuota."),
        [{"type": "kill", "enemy": "base:enemy/dire_alpha", "count": 1}],
        700, 800, 40, {"base:item/potion_large": 2},
        ("That bounty has been on the board since before I was guildmaster. Every rank-C party that tried came back without a story. You come back with stories, Guest.",
         "Quella taglia è in bacheca da prima che diventassi maestra della gilda. Ogni squadra di rango C che ci ha provato è tornata senza una storia. Tu torni sempre con delle storie, Ospite."),
        ("The Dire Alpha, in the Dire Den of Ironspine.", "L'Alfa atroce, nella Dire Den di Ironspine."),
        ("Collected, at last. The guild pays its debts, and the potions are from my own stores.", "Riscossa, finalmente. La gilda paga i suoi debiti, e le pozioni vengono dalla mia riserva.")),
    "aldermere_quartermaster_rook": _q(
        "aldermere_golem_cores", ("Cores for the Lanterns", "Nuclei per le lanterne"),
        ("Rook wants golem cores to light the guild hall through the winter. The stone golems carry them.",
         "Rook vuole nuclei di golem per illuminare la sala della gilda durante l'inverno. Li portano i golem di pietra."),
        [{"type": "kill", "enemy": "base:enemy/stone_golem", "count": 3}, {"type": "collect", "item": "base:item/golem_core", "count": 2}],
        520, 640, 30, {"base:item/potion_medium": 3},
        ("Oil is dear and candles are worse. A golem's core glows for a century. Two of them, and the guild hall never goes dark. Mind the fists.",
         "L'olio è caro e le candele peggio. Il nucleo di un golem brilla per un secolo. Con due, la sala della gilda non resta mai al buio. Attento ai pugni."),
        ("Three golems, two cores.", "Tre golem, due nuclei."),
        ("Light! The archivist cried. Do not tell him I said so. Potions, from the stores that are full again thanks to you.",
         "Luce! L'archivista ha pianto. Non dirgli che te l'ho detto. Pozioni, dai magazzini che grazie a te sono di nuovo pieni.")),
    "aldermere_archivist_selwyn": _q(
        "aldermere_curator", ("The Last Page of the Observatory", "L'ultima pagina dell'osservatorio"),
        ("Selwyn's catalogue of the Starfall Observatory, in Lumeria, has one page missing: its Curator. Defeat it and bring him the story.",
         "Al catalogo di Selwyn sullo Starfall Observatory, a Lumeria, manca una pagina: il suo Curatore. Sconfiggilo e portagli la storia."),
        [{"type": "kill", "enemy": "base:enemy/astral_curator", "count": 1}],
        900, 1000, 50, {"base:item/potion_mana_medium": 3},
        ("Every page of the observatory is written, but one. 'The Curator', it says, and then nothing. The last scholar who went to finish it did not. Would you?",
         "Ogni pagina dell'osservatorio è scritta, tranne una. 'Il Curatore', dice, e poi niente. L'ultimo studioso che andò a finirla non ci riuscì. Lo faresti tu?"),
        ("The Astral Curator, in the Starfall Observatory of Lumeria.", "Il Curatore astrale, nello Starfall Observatory di Lumeria."),
        ("The page is written. In your words, mostly, and a few of mine. Take these potions; scholars live on mana and tea.",
         "La pagina è scritta. Con parole tue, per lo più, e qualcuna mia. Prendi queste pozioni: gli studiosi vivono di mana e di tè.")),
}
# The archivist's Book of Legends (M9, the stories of the regions): after his first quest, Selwyn asks for the end of seven legends, one guardian
# of a great dungeon in each region (set_quest_places.py gives each its place).
LEGENDS = [
    _q("legend_barrow", ('The Warden Under the Hill', 'Il custode sotto la collina'),
       ("Selwyn's Book of Legends tells of the Barrow Warden of Grunmoor Barrow, in Verdalis. Defeat it and bring him the end of the story.",
        "Il Libro delle Leggende di Selwyn parla del Custode del Tumulo di Grunmoor Barrow, a Verdalis. Sconfiggilo e portagli la fine della storia."),
       [{"type": "kill", "enemy": "base:enemy/barrow_warden", "count": 1}], 300, 300, 15, {'base:item/potion_medium': 2},
       ('The first legend of my book is the oldest, and the closest: a warden who guards a barrow that nobody remembers filling. Will you write its last line?', "La prima leggenda del mio libro è la più antica, e la più vicina: un custode che veglia un tumulo che nessuno ricorda di aver riempito. Ne scriverai l'ultima riga?"),
       ("The Barrow Warden, in Grunmoor Barrow.", "Il Custode del Tumulo, a Grunmoor Barrow."),
       ('So the warden rests. I will write that it went quietly. It did not, did it? I will write that it went quietly anyway.', "Dunque il custode riposa. Scriverò che se n'è andato in silenzio. Non è vero, eh? Lo scriverò lo stesso.")),
    _q("legend_moonshade", ('The Wolf Under the Moon', 'Il lupo sotto la luna'),
       ("Selwyn's Book of Legends tells of the Moonshade Alpha of Whisperwood Hollow, in Whisperwood. Defeat it and bring him the end of the story.",
        "Il Libro delle Leggende di Selwyn parla dell'Alfa dell'ombra lunare di Whisperwood Hollow, a Whisperwood. Sconfiggilo e portagli la fine della storia."),
       [{"type": "kill", "enemy": "base:enemy/moonshade_alpha", "count": 1}], 700, 700, 35, {'base:item/moonmoss_draught': 2},
       ('The second legend: a wolf that hunts by moonlight in Whisperwood, and casts no shadow. The pages say no one has seen it twice.', "La seconda leggenda: un lupo che caccia al chiaro di luna a Whisperwood, e non fa ombra. Le pagine dicono che nessuno l'ha visto due volte."),
       ("The Moonshade Alpha, in Whisperwood Hollow.", "L'Alfa dell'ombra lunare, a Whisperwood Hollow."),
       ('You saw it twice, then. Once coming, once going. The pages will need a new sentence.', "Allora l'hai visto due volte. Una all'andata, una al ritorno. Alle pagine servirà una frase nuova.")),
    _q("legend_foreman", ('The Foreman Who Never Clocked Out', 'Il caposquadra che non smontava mai'),
       ("Selwyn's Book of Legends tells of the Ironbound Foreman of Ironspine Mine, in Ironspine. Defeat it and bring him the end of the story.",
        "Il Libro delle Leggende di Selwyn parla del Caposquadra di ferro di Ironspine Mine, a Ironspine. Sconfiggilo e portagli la fine della storia."),
       [{"type": "kill", "enemy": "base:enemy/iron_foreman", "count": 1}], 600, 650, 30, {'base:item/miners_broth': 3},
       ('The third legend is a sad one: a foreman of the old mine who would not stop working when the mine stopped. He is iron now, they say, all the way through.', 'La terza leggenda è triste: un caposquadra della vecchia miniera che non volle smettere quando la miniera smise. Ora è di ferro, dicono, da parte a parte.'),
       ("The Ironbound Foreman, in Ironspine Mine.", "Il Caposquadra di ferro, a Ironspine Mine."),
       ('His shift is over, then. I hope he heard the bell. Some legends end with a bell.', 'Il suo turno è finito, dunque. Spero abbia sentito la campana. Certe leggende finiscono con una campana.')),
    _q("legend_regent", ('The Regent of the Drowned', 'Il reggente degli annegati'),
       ("Selwyn's Book of Legends tells of the Tide Regent of Drowned Temple, in Tidehaven. Defeat it and bring him the end of the story.",
        "Il Libro delle Leggende di Selwyn parla del Reggente della marea di Drowned Temple, a Tidehaven. Sconfiggilo e portagli la fine della storia."),
       [{"type": "kill", "enemy": "base:enemy/tide_regent", "count": 1}], 650, 700, 32, {'base:item/pearl_elixir': 2},
       ('The fourth legend rules a temple the sea took back: the Tide Regent, who still keeps the court of a kingdom under the water.', "La quarta leggenda regna su un tempio che il mare si è ripreso: il Reggente della marea, che tiene ancora la corte di un regno sott'acqua."),
       ("The Tide Regent, in Drowned Temple.", "Il Reggente della marea, a Drowned Temple."),
       ('A court without a regent. I will write that the fish voted, and voted well.', 'Una corte senza reggente. Scriverò che i pesci hanno votato, e hanno votato bene.')),
    _q("legend_revenant", ('The Revenant in the Ice', 'Lo spettro nel ghiaccio'),
       ("Selwyn's Book of Legends tells of the Rime Revenant of Frostveil Cavern, in Frostveil. Defeat it and bring him the end of the story.",
        "Il Libro delle Leggende di Selwyn parla dello Spettro del gelo di Frostveil Cavern, a Frostveil. Sconfiggilo e portagli la fine della storia."),
       [{"type": "kill", "enemy": "base:enemy/rime_revenant", "count": 1}], 800, 850, 40, {'base:item/frost_tonic': 3},
       ('The fifth legend is cold: a knight frozen into the cavern of Frostveil, who woke up and did not like what he found.', 'La quinta leggenda è fredda: un cavaliere congelato nella caverna di Frostveil, che si è svegliato e non ha gradito ciò che ha trovato.'),
       ("The Rime Revenant, in Frostveil Cavern.", "Lo Spettro del gelo, a Frostveil Cavern."),
       ('Back to sleep, then, and for good. I shall write it in ink that does not freeze. I have some. I bought it for this.', "Di nuovo a dormire, dunque, e per sempre. Lo scriverò con un inchiostro che non gela. Ce l'ho. L'ho comprato apposta.")),
    _q("legend_sentinel", ('The Sentinel of the Ziggurat', 'La sentinella dello ziggurat'),
       ("Selwyn's Book of Legends tells of the Sand Sentinel of Sunken Ziggurat, in Sunscar. Defeat it and bring him the end of the story.",
        "Il Libro delle Leggende di Selwyn parla della Sentinella di sabbia di Sunken Ziggurat, a Sunscar. Sconfiggila e portagli la fine della storia."),
       [{"type": "kill", "enemy": "base:enemy/sand_sentinel", "count": 1}], 900, 950, 45, {'base:item/desert_nectar': 3},
       ('The sixth legend stands guard at a ziggurat half eaten by the sand of Sunscar. What it guards, the book does not say. The book would like to know.', 'La sesta leggenda fa la guardia a uno ziggurat mezzo mangiato dalla sabbia di Sunscar. Cosa sorvegli, il libro non lo dice. Il libro vorrebbe saperlo.'),
       ("The Sand Sentinel, in Sunken Ziggurat.", "La Sentinella di sabbia, a Sunken Ziggurat."),
       ('Sand, you say? It guarded sand. That is the most honest legend in the book.', 'Sabbia, dici? Sorvegliava sabbia. È la leggenda più onesta del libro.')),
    _q("legend_colossus", ('The Colossus of Cinders', 'Il colosso di cenere'),
       ("Selwyn's Book of Legends tells of the Cinder Colossus of Cinder Citadel, in the Ashen Wastes. Defeat it and bring him the end of the story.",
        "Il Libro delle Leggende di Selwyn parla del Colosso di cenere di Cinder Citadel, nelle Terre di Cenere. Sconfiggilo e portagli la fine della storia."),
       [{"type": "kill", "enemy": "base:enemy/cinder_colossus", "count": 1}], 1200, 1300, 60, {'base:item/ember_brew': 3},
       ('The last legend is the largest: a colossus of cinders that walks the citadel of the Ashen Wastes. Only the heroes of songs ever came back from it. Be a song, Guest.', "L'ultima leggenda è la più grande: un colosso di cenere che percorre la cittadella delle Terre di Cenere. Solo gli eroi delle canzoni ne sono tornati. Sii una canzone, Ospite."),
       ("The Cinder Colossus, in Cinder Citadel.", "Il Colosso di cenere, a Cinder Citadel."),
       ('The book is finished. Every legend has an ending, and every ending has your name. I will start a second book. It will be about you.', 'Il libro è finito. Ogni leggenda ha una fine, e ogni fine porta il tuo nome. Comincerò un secondo libro. Parlerà di te.')),
]
for _person in PEOPLE:
    if _person["key"] in MORE_QUESTS:
        _person["quests"].append(MORE_QUESTS[_person["key"]])
    if _person["key"] == "aldermere_archivist_selwyn":
        _person["quests"].extend(LEGENDS)

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
