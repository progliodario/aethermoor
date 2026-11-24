#!/usr/bin/env python3
"""Writes the side stories of the protagonists (spec 18, "Side stories"; item D of the operating program): for a protagonist, three
quests from a person of the world, one after the other, and an ending that the player chooses in a dialogue (it changes the thing the
Guest takes home). The person talks to everyone, but tells the story only to whoever carries the keepsake of that protagonist (the
condition `has_item`, the same way Maren and Pip tell theirs).

Wave 9a (D1): Ren and Haruka; wave 9b (D2): Daichi and Sakura; wave 9c (D3): Marco and Yuki; wave 9d (D4): Lena and Gideon; all in Aldermere. It writes the people into the world data (`npcs`, one line each, written again in
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
    {
        "key": "aldermere_fire_warden_hale", "file": "hale", "variant": "red", "dx": 381, "dy": -129, "protagonist": "daichi",
        "name": ("Captain Wren Hale, fire warden of Aldermere", "Capitana Wren Hale, guardiana del fuoco di Aldermere"),
        "stranger": ("Keep your lantern away from the hay, Guest. Every fire in this town starts with somebody saying 'it is only a candle'.",
                     "Tieni la lanterna lontana dal fieno, Ospite. Ogni incendio di questa città comincia con qualcuno che dice 'è solo una candela'."),
        "hello": ("You smell of smoke. Not the smell of someone who started a fire: the smell of someone who went in after it. I know that smell.",
                  "Sai di fumo. Non l'odore di chi appicca un fuoco: l'odore di chi ci entra dopo. Lo conosco, quell'odore."),
        "after": ("The brigade drills every morning now. They shout 'Okabe!' when they lift the ladder. I have not had the heart to tell them it is a name.",
                  "La brigata si esercita ogni mattina, ora. Gridano 'Okabe!' quando alzano la scala. Non ho avuto il cuore di dirgli che è un nome."),
        "quests": [
            ("side_daichi_1", ("The Bucket Brigade: Ice for the Wells", "La catena dei secchi: ghiaccio per i pozzi"),
             ("The fire buckets of Aldermere are empty and the wells are low. Bring Captain Hale six ice crystals: they melt slowly and fill a cistern.",
              "I secchi antincendio di Aldermere sono vuoti e i pozzi sono bassi. Porta alla capitana Hale sei cristalli di ghiaccio: si sciolgono piano e riempiono una cisterna."),
             [{"type": "collect", "item": "base:item/ice_crystal", "count": 6}], 600, 400,
             ("A town of wood and straw, and the wells are low. If a fire starts tonight, we fight it with spit. The ice slimes of the north "
              "carry crystals that melt for days. Six of them would fill the cistern by the gate.",
              "Una città di legno e paglia, e i pozzi sono bassi. Se stanotte scoppia un incendio, lo spegniamo con la saliva. Gli slime di ghiaccio "
              "del nord portano cristalli che si sciolgono per giorni. Sei riempirebbero la cisterna vicino alla porta."),
             ("Six ice crystals. The cistern by the gate is the one with the frog painted on it. Do not ask about the frog.",
              "Sei cristalli di ghiaccio. La cisterna vicino alla porta è quella con la rana dipinta sopra. Non chiedere della rana."),
             ("Full to the brim. The frog looks happier. I swear it does.", "Piena fino all'orlo. La rana sembra più contenta. Lo giuro.")),
            ("side_daichi_2", ("The Bucket Brigade: Embers on the Wind", "La catena dei secchi: braci nel vento"),
             ("Ember slimes drift on the hot wind and set the farms on fire. Put out six of them before they reach a barn.",
              "Gli slime di brace vanno alla deriva sul vento caldo e incendiano le fattorie. Spegnine sei prima che arrivino a un fienile."),
             [{"type": "kill", "enemy": "base:enemy/slime_ember", "count": 6}], 1200, 900,
             ("The wind from the Ashen Wastes carries ember slimes, and they land wherever there is something dry. Last week a barn, the "
              "week before a mill. Six of them, before they find the granary.",
              "Il vento delle Terre di Cenere porta gli slime di brace, e atterrano dovunque ci sia qualcosa di secco. La settimana scorsa un "
              "fienile, quella prima un mulino. Sei, prima che trovino il granaio."),
             ("Six ember slimes. Mind your sleeves: they stick.", "Sei slime di brace. Attento alle maniche: si attaccano."),
             ("Not one barn burned this week. Not one. The farmers sent you a cake. It is slightly scorched: they insisted on baking it themselves.",
              "Neanche un fienile bruciato questa settimana. Neanche uno. I contadini ti hanno mandato una torta. È un po' bruciacchiata: hanno insistito a farla loro.")),
            ("side_daichi_3", ("The Bucket Brigade: The Third Floor", "La catena dei secchi: il terzo piano"),
             ("Cinder wolves run burning through the hills and leave fires behind them. Stop four of them, and the hills can breathe.",
              "I lupi di cenere corrono in fiamme per le colline e si lasciano dietro incendi. Fermane quattro, e le colline potranno respirare."),
             [{"type": "kill", "enemy": "base:enemy/wolf_ember", "count": 4}], 2400, 1800,
             ("The last one, and the worst. Cinder wolves: they run through the dry grass burning, and the fire follows them like a tail. "
              "Four of them. You will go in anyway, I know. Your kind always goes in one more time.",
              "L'ultima, e la peggiore. Lupi di cenere: corrono nell'erba secca in fiamme, e il fuoco li segue come una coda. Quattro. Ci "
              "andrai comunque, lo so. Quelli come te rientrano sempre una volta di più."),
             ("Four cinder wolves. And come back. That is an order, not a suggestion.",
              "Quattro lupi di cenere. E torna. È un ordine, non un consiglio."),
             ("You came back. Good. In my brigade that is the only rule that counts: everyone comes back.",
              "Sei tornato. Bene. Nella mia brigata è l'unica regola che conta: tutti tornano.")),
        ],
        "ending": {
            "ask": ("The town council wants a captain for a brigade of volunteers, and they want you. Or you could do what you are best at: "
                    "teach them, and go where the next fire is. Which, Okabe?",
                    "Il consiglio vuole un capitano per una brigata di volontari, e vuole te. Oppure potresti fare quello che ti riesce meglio: "
                    "insegnargli, e andare dove c'è il prossimo incendio. Cosa scegli, Okabe?"),
            "a": (("I will lead the brigade. Someone has to be first through the door.", "Guiderò la brigata. Qualcuno deve entrare per primo."),
                  "base:item/rescue_axe",
                  ("Then take the brigade's axe. It opens doors, roofs and the occasional stubborn slime.",
                   "Allora prendi l'ascia della brigata. Apre porte, tetti e ogni tanto uno slime testardo.")),
            "b": (("Teach them, and move on. They have to learn to save themselves.", "Insegnargli, e ripartire. Devono imparare a salvarsi da soli."),
                  "base:item/ember_ring",
                  ("Wise, and harder. Take this ring: it was forged in a fire that did not win. Neither will the next one.",
                   "Saggio, e più difficile. Prendi questo anello: è stato forgiato in un fuoco che non ha vinto. Non vincerà neanche il prossimo.")),
        },
    },
    {
        "key": "aldermere_astronomer_ottilie", "file": "ottilie", "variant": "purple", "dx": 383, "dy": -129, "protagonist": "sakura",
        "name": ("Ottilie Brask, astronomer of the guild", "Ottilie Brask, astronoma della gilda"),
        "stranger": ("The stars are wrong tonight, Guest. Not very wrong. Just enough to ruin a whole notebook.",
                     "Le stelle sono sbagliate stanotte, Ospite. Non di molto. Quanto basta per rovinare un quaderno intero."),
        "hello": ("You looked at my chart and frowned in the right place. Nobody frowns in the right place. Are you... a natural philosopher?",
                  "Hai guardato la mia carta e hai aggrottato la fronte nel punto giusto. Nessuno la aggrotta nel punto giusto. Sei... una filosofa naturale?"),
        "after": ("I have a student now, did I tell you? She asks why. Always why. I think that is your fault, and I am grateful.",
                  "Adesso ho un'allieva, te l'ho detto? Chiede perché. Sempre perché. Credo sia colpa tua, e te ne sono grata."),
        "quests": [
            ("side_sakura_1", ("The Unfinished Proof: Measurements", "La dimostrazione incompiuta: misure"),
             ("Ottilie's instruments need calibrating, and star dust is the only thing that glows the same everywhere. Bring her five pinches.",
              "Gli strumenti di Ottilie vanno tarati, e la polvere di stelle è l'unica cosa che brilla allo stesso modo dappertutto. Portagliene cinque pizzichi."),
             [{"type": "collect", "item": "base:item/star_dust", "count": 5}], 600, 400,
             ("Every night the sky moves a little differently than my tables say. Either the sky is wrong or my instruments are. I would "
              "prefer the instruments. The glowing slimes of Lumeria carry star dust: five pinches, to calibrate.",
              "Ogni notte il cielo si muove in modo un po' diverso da quello che dicono le mie tavole. O sbaglia il cielo o sbagliano i miei "
              "strumenti. Preferirei gli strumenti. Gli slime luminosi di Lumeria portano polvere di stelle: cinque pizzichi, per tarare."),
             ("Five pinches of star dust. Keep it dry: wet star dust sulks for a week.",
              "Cinque pizzichi di polvere di stelle. Tienila asciutta: la polvere di stelle bagnata tiene il broncio per una settimana."),
             ("Calibrated. And... the sky is still wrong. How wonderful. That means something is really there.",
              "Tarati. E... il cielo è ancora sbagliato. Che meraviglia. Vuol dire che lì c'è davvero qualcosa.")),
            ("side_sakura_2", ("The Unfinished Proof: Noise in the Data", "La dimostrazione incompiuta: rumore nei dati"),
             ("Wisps drift near the observatory and their light spoils the measurements. Chase six of them away.",
              "I fuochi fatui si aggirano vicino all'osservatorio e la loro luce rovina le misure. Scacciane sei."),
             [{"type": "kill", "enemy": "base:enemy/wisp", "count": 6}], 1200, 900,
             ("Noise. In your words, I think: noise in the data. The wisps come to look at the telescope, and they glow, and every number "
              "I write is a number plus a wisp. Six of them, and my nights are clean again.",
              "Rumore. Con le tue parole, credo: rumore nei dati. I fuochi fatui vengono a guardare il telescopio, e brillano, e ogni numero "
              "che scrivo è un numero più un fuoco fatuo. Sei, e le mie notti tornano pulite."),
             ("Six wisps. Gently, if you can: they are curious, not wicked.", "Sei fuochi fatui. Con garbo, se puoi: sono curiosi, non cattivi."),
             ("A clean night. A whole clean night! The numbers line up like soldiers. Something is pulling at the stars, Sakura, and I can measure it.",
              "Una notte pulita. Un'intera notte pulita! I numeri si allineano come soldati. Qualcosa tira le stelle, Sakura, e io posso misurarlo.")),
            ("side_sakura_3", ("The Unfinished Proof: The Last Term", "La dimostrazione incompiuta: l'ultimo termine"),
             ("The pull on the stars comes from the nebula slimes. Calm four of them and bring two nebula ashes: the last term of the equation.",
              "La forza che tira le stelle viene dagli slime nebulosi. Calmane quattro e porta due ceneri di nebulosa: l'ultimo termine dell'equazione."),
             [{"type": "kill", "enemy": "base:enemy/slime_nebula", "count": 4}, {"type": "collect", "item": "base:item/nebula_ash", "count": 2}],
             2400, 1800,
             ("The nebula slimes. They are the missing term: they bend the light of the stars around them, very slightly. Four of them, "
              "measured up close, and two of their ashes to weigh. Then we can write the last line.",
              "Gli slime nebulosi. Sono il termine mancante: piegano la luce delle stelle attorno a sé, pochissimo. Quattro, misurati da vicino, "
              "e due delle loro ceneri da pesare. Poi potremo scrivere l'ultima riga."),
             ("Four nebula slimes and two of their ashes. Bring a notebook. Bring two.",
              "Quattro slime nebulosi e due delle loro ceneri. Porta un quaderno. Portane due."),
             ("It closes. The whole proof closes. Do you know how long I have waited to say that? Do you know how long you have?",
              "Si chiude. La dimostrazione intera si chiude. Sai da quanto aspettavo di dirlo? E tu, sai da quanto lo aspetti?")),
        ],
        "ending": {
            "ask": ("The proof is ours, Sakura, but the Academy will want one name on it. Mine, and you go on with your journey free of it. "
                    "Or yours: a thesis needs someone to defend it, and you have been looking for a defense, I think.",
                    "La dimostrazione è nostra, Sakura, ma l'Accademia vorrà un solo nome. Il mio, e tu riprendi il viaggio libera da tutto questo. "
                    "Oppure il tuo: una tesi ha bisogno di qualcuno che la difenda, e tu una difesa la cerchi da tempo, credo."),
            "a": (("Put your name on it. The stars were yours to watch.", "Mettici il tuo nome. Le stelle le guardavi tu."),
                  "base:item/star_brooch",
                  ("Then wear this, at least: the brooch of the observatory. Every astronomer who shares a discovery gets one. There are very few.",
                   "Allora porta almeno questa: la spilla dell'osservatorio. La riceve ogni astronomo che condivide una scoperta. Sono pochissime.")),
            "b": (("Mine. I have a thesis to defend, and now I have something to defend it with.", "Il mio. Ho una tesi da difendere, e ora ho qualcosa con cui difenderla."),
                  "base:item/focus_staff",
                  ("Good. Defend it well. Take this staff: it keeps a mind focused, and you will need yours, before the Academy.",
                   "Bene. Difendila bene. Prendi questo bastone: tiene la mente concentrata, e la tua ti servirà, davanti all'Accademia.")),
        },
    },
    {
        "key": "aldermere_cook_bruna", "file": "bruna", "variant": "ochre", "dx": 385, "dy": -129, "protagonist": "marco",
        "name": ("Bruna Calder, cook of the guild's hall", "Bruna Calder, cuoca della mensa della gilda"),
        "stranger": ("Stew, Guest? It is the same stew as yesterday. It was also the same stew yesterday.",
                     "Stufato, Ospite? È lo stesso stufato di ieri. Anche ieri era lo stesso stufato."),
        "hello": ("You tasted my stew and made a face. Not a polite face: the face of somebody who knows what is missing. What is missing?",
                  "Hai assaggiato il mio stufato e hai fatto una smorfia. Non una smorfia educata: quella di chi sa che cosa manca. Che cosa manca?"),
        "after": ("The hall is full every night now. The guards come for the soup and stay for the soap, which is a sentence I never thought I would say.",
                  "La mensa è piena tutte le sere, ora. Le guardie vengono per la zuppa e restano per il sapone, una frase che non pensavo avrei mai detto."),
        "quests": [
            ("side_marco_1", ("Salt of the Earth: Soap, at Last", "Il sale della terra: finalmente il sapone"),
             ("Marco knows how to make soap; the guild's kitchen does not. Bring Bruna five crab shells: burned, they give the lime.",
              "Marco sa fare il sapone; la cucina della gilda no. Porta a Bruna cinque gusci di granchio: bruciati, danno la calce."),
             [{"type": "collect", "item": "base:item/crab_shell", "count": 5}], 600, 400,
             ("Soap? A thing that cleans, and you make it? And here I thought sand was the best we could do. What do you need? Shells? "
              "The crabs of the shore have them, and they are not generous. Five, you said.",
              "Il sapone? Una cosa che pulisce, e la si fa? E io che pensavo che la sabbia fosse il meglio. Che cosa ti serve? Gusci? "
              "Li hanno i granchi della riva, e non sono generosi. Cinque, hai detto."),
             ("Five crab shells. Mind the claws: the crabs mind them very much.", "Cinque gusci di granchio. Attento alle chele: i granchi ci tengono molto."),
             ("It foams. It foams! The scullery boys washed their hands without being told. I think I saw one of them cry.",
              "Fa la schiuma. Fa la schiuma! I ragazzi di cucina si sono lavati le mani senza che glielo dicessi. Credo di averne visto piangere uno.")),
            ("side_marco_2", ("Salt of the Earth: The Pressure Problem", "Il sale della terra: il problema della pressione"),
             ("Marco wants to build a pot that cooks under pressure, safely this time. He needs the weight of two golem cores for the valve.",
              "Marco vuole costruire una pentola che cuoce sotto pressione, stavolta in sicurezza. Gli serve il peso di due nuclei di golem per la valvola."),
             [{"type": "kill", "enemy": "base:enemy/stone_golem", "count": 3}, {"type": "collect", "item": "base:item/golem_core", "count": 2}],
             1200, 900,
             ("A pot with a lid that holds, that cooks a stew in an hour instead of a day? And you say the last one... exploded. And you "
              "want to build another. I like you. What does the lid need? The heart of a stone golem, as a weight. Two hearts.",
              "Una pentola con un coperchio che tiene, che cuoce uno stufato in un'ora invece che in un giorno? E dici che l'ultima... è "
              "esplosa. E ne vuoi costruire un'altra. Mi piaci. Che cosa serve al coperchio? Il cuore di un golem di pietra, come peso. Due cuori."),
             ("Three stone golems, and two of their cores. The valve must be heavy, and honest.",
              "Tre golem di pietra, e due dei loro nuclei. La valvola dev'essere pesante, e onesta."),
             ("It whistles. It whistles and it does not explode. Marco, you look like a man who has made peace with something.",
              "Fischia. Fischia e non esplode. Marco, hai la faccia di chi ha fatto pace con qualcosa.")),
            ("side_marco_3", ("Salt of the Earth: Dinner for Forty", "Il sale della terra: cena per quaranta"),
             ("The guild holds a dinner for forty, and the new pot will cook it. Bring eight river fish and four pieces of game meat.",
              "La gilda dà una cena per quaranta, e la cuocerà la pentola nuova. Porta otto pesci di fiume e quattro pezzi di selvaggina."),
             [{"type": "collect", "item": "base:item/river_fish", "count": 8}, {"type": "collect", "item": "base:item/game_meat", "count": 4}],
             2400, 1800,
             ("The guild wants a feast. Forty at table, the guildmaster at the head. You told me how your old life ended: a dinner for forty. "
              "I think you should cook this one. Fish from the river, eight, and four of meat from the hunt.",
              "La gilda vuole un banchetto. Quaranta a tavola, la maestra della gilda a capotavola. Mi hai raccontato come è finita la tua vita "
              "di prima: una cena per quaranta. Credo che questa dovresti cucinarla tu. Pesce di fiume, otto, e quattro di carne di caccia."),
             ("Eight river fish and four of game meat. The forty are already hungry. So am I.",
              "Otto pesci di fiume e quattro di selvaggina. I quaranta hanno già fame. Anch'io."),
             ("Forty plates, forty empty plates, and nobody hurt. Hestia asked for the recipe. I told her it was a matter of units.",
              "Quaranta piatti, quaranta piatti vuoti, e nessun ferito. Hestia ha chiesto la ricetta. Le ho detto che era una questione di unità.")),
        ],
        "ending": {
            "ask": ("The guild wants you as head cook, Marco. The hall, the pot, the forty every night. Or you could take your recipes on the "
                    "road and teach every inn of the world to cook with salt. Which?",
                    "La gilda ti vuole come capocuoco, Marco. La mensa, la pentola, i quaranta ogni sera. Oppure potresti portare le tue ricette "
                    "in giro e insegnare a ogni locanda del mondo a cucinare con il sale. Cosa scegli?"),
            "a": (("I will stay. A kitchen that works is worth a kingdom.", "Resto. Una cucina che funziona vale un regno."),
                  "base:item/chef_cleaver",
                  ("Then the cleaver of the head cook is yours. It cuts bone, rope and arguments.",
                   "Allora la mannaia del capocuoco è tua. Taglia ossa, corde e discussioni.")),
            "b": (("I will go. The world is full of kitchens without salt.", "Parto. Il mondo è pieno di cucine senza sale."),
                  "base:item/caravan_mantle",
                  ("Then take the mantle of the caravans: they have carried every good thing across this world. Now they carry you.",
                   "Allora prendi il mantello delle carovane: hanno portato ogni cosa buona per questo mondo. Ora portano te.")),
        },
    },
    {
        "key": "aldermere_vault_keeper_ilse", "file": "ilse", "variant": "teal", "dx": 387, "dy": -129, "protagonist": "yuki",
        "name": ("Ilse Marrow, keeper of the guild's vault", "Ilse Marrow, custode della cassaforte della gilda"),
        "stranger": ("The vault is closed, Guest. Not locked: nobody locks anything here. Closed. It is a matter of manners.",
                     "La cassaforte è chiusa, Ospite. Non a chiave: qui nessuno chiude niente a chiave. Chiusa. È una questione di educazione."),
        "hello": ("You looked at my door, then at my window, then at the roof. In that order. Nobody in this town looks at a roof. Who are you?",
                  "Hai guardato la mia porta, poi la finestra, poi il tetto. In quest'ordine. In questa città nessuno guarda i tetti. Chi sei?"),
        "after": ("Nothing has gone missing since you came. I am almost bored. Almost.", "Da quando sei arrivata non è sparito niente. Quasi mi annoio. Quasi."),
        "quests": [
            ("side_yuki_1", ("The Honest Thief: The Magpie's Hoard", "La ladra onesta: il tesoro della gazza"),
             ("Silver spoons keep vanishing from the guild's vault, and owl feathers keep turning up in their place. Stop five night owls and bring three feathers as proof.",
              "Dalla cassaforte della gilda spariscono cucchiai d'argento, e al loro posto compaiono piume di gufo. Ferma cinque gufi notturni e porta tre piume come prova."),
             [{"type": "kill", "enemy": "base:enemy/night_owl", "count": 5}, {"type": "collect", "item": "base:item/owl_feather", "count": 3}],
             600, 400,
             ("Someone takes the silver spoons. Every night, one spoon, and in its place a feather. I thought it was a ghost with good "
              "manners. You smile. You know who it is already, don't you?",
              "Qualcuno prende i cucchiai d'argento. Ogni notte un cucchiaio, e al suo posto una piuma. Pensavo fosse un fantasma educato. "
              "Sorridi. Sai già chi è, vero?"),
             ("Five night owls, three feathers. And the spoons, if they kept them.", "Cinque gufi notturni, tre piume. E i cucchiai, se li hanno tenuti."),
             ("Thirty-one spoons, in a nest, polished. They had better taste than the guild. Thank you.",
              "Trentuno cucchiai, in un nido, lucidati. Avevano più gusto della gilda. Grazie.")),
            ("side_yuki_2", ("The Honest Thief: A Painting in the Dark", "La ladra onesta: un quadro nel buio"),
             ("The guild's only painting was carried off into Whisperwood by the shade wolves, who like dark things. Chase off five of them and find it.",
              "L'unico quadro della gilda è stato portato a Whisperwood dai lupi d'ombra, che amano le cose scure. Scacciane cinque e ritrovalo."),
             [{"type": "kill", "enemy": "base:enemy/wolf_shade", "count": 5}], 1200, 900,
             ("The guild had one painting. A dark one: a night sea. The shade wolves took it, I think they like it, it is the color of them. "
              "You know paintings, I can tell by the way you did not look at it. Five of the wolves, and bring it home.",
              "La gilda aveva un solo quadro. Uno scuro: un mare di notte. L'hanno preso i lupi d'ombra, credo che gli piaccia, è del loro "
              "colore. Tu di quadri te ne intendi, lo capisco da come hai evitato di guardarlo. Cinque lupi, e riportalo a casa."),
             ("Five shade wolves. The painting is a night sea, in a black frame. You will know it.",
              "Cinque lupi d'ombra. Il quadro è un mare di notte, in una cornice nera. Lo riconoscerai."),
             ("Not a scratch. You carried it like it was alive. Where did you learn that?",
              "Neanche un graffio. L'hai portato come se fosse vivo. Dove l'hai imparato?")),
            ("side_yuki_3", ("The Honest Thief: The Cave under the Vault", "La ladra onesta: la grotta sotto la cassaforte"),
             ("Bats nest in the cave under the vault, and things keep falling through the floor into it. Clear six of them and bring four bat wings for the mortar of a new floor.",
              "I pipistrelli fanno il nido nella grotta sotto la cassaforte, e le cose continuano a cadere giù dal pavimento. Liberane sei e porta quattro ali di pipistrello per la malta del pavimento nuovo."),
             [{"type": "kill", "enemy": "base:enemy/cave_bat", "count": 6}, {"type": "collect", "item": "base:item/bat_wing", "count": 4}],
             2400, 1800,
             ("The last mystery: the floor of the vault has a hole, and under it a cave, and in the cave bats, and everything that falls "
              "becomes theirs. Six bats, and four of their wings for the mortar: the old masons swear by it.",
              "L'ultimo mistero: il pavimento della cassaforte ha un buco, e sotto c'è una grotta, e nella grotta pipistrelli, e tutto quello "
              "che cade diventa loro. Sei pipistrelli, e quattro delle loro ali per la malta: i vecchi muratori ci giurano."),
             ("Six cave bats and four of their wings. Then we close the floor, and the vault is a vault again.",
              "Sei pipistrelli e quattro delle loro ali. Poi chiudiamo il pavimento, e la cassaforte torna a essere una cassaforte."),
             ("A new floor, and under the old one... Yuki, there was a painting down there too. A very old one. Nobody has seen it in a hundred years.",
              "Un pavimento nuovo, e sotto il vecchio... Yuki, laggiù c'era anche un quadro. Molto vecchio. Nessuno lo vede da cent'anni.")),
        ],
        "ending": {
            "ask": ("Nobody knows it exists, Yuki. A painting that belongs to no one, in a town where nobody locks a door. You could hang it "
                    "in the vault, for everyone. Or you could keep it, and nobody would ever know. I would not tell. What do you do?",
                    "Nessuno sa che esiste, Yuki. Un quadro che non è di nessuno, in una città dove nessuno chiude una porta. Potresti appenderlo "
                    "nella cassaforte, per tutti. Oppure tenerlo, e nessuno lo saprebbe mai. Io non lo direi. Che cosa fai?"),
            "a": (("Hang it in the vault. For once, I want everyone to see it.", "Appendilo nella cassaforte. Per una volta, voglio che lo vedano tutti."),
                  "base:item/guild_signet",
                  ("Then the guild owes you its trust, and here is its seal to prove it. I never thought I would give it to a thief.",
                   "Allora la gilda ti deve la sua fiducia, ed ecco il suo sigillo a dimostrarlo. Non pensavo che l'avrei dato a una ladra.")),
            "b": (("I will keep it. Some things are better loved by one person than looked at by many.", "Lo tengo. Certe cose è meglio che le ami una persona che le guardino in tanti."),
                  "base:item/shadow_dagger",
                  ("I saw nothing. And since you will be carrying a painting through dark places, take this blade: it does not catch the light.",
                   "Non ho visto niente. E visto che porterai un quadro in posti bui, prendi questa lama: non riflette la luce.")),
        },
    },
    {
        "key": "aldermere_physician_finch", "file": "finch", "variant": "cream", "dx": 383, "dy": -127, "protagonist": "lena",
        "name": ("Doctor Aurel Finch, physician of the guild", "Dottor Aurel Finch, medico della gilda"),
        "stranger": ("Bandages on the left, tonics on the right, bad news in the drawer. What can I do for you, Guest?",
                     "Bende a sinistra, tonici a destra, cattive notizie nel cassetto. Che cosa posso fare per te, Ospite?"),
        "hello": ("You read my notes upside down, from across the table, and you corrected one. You were right. Who taught you to read a body?",
                  "Hai letto i miei appunti al contrario, dall'altra parte del tavolo, e ne hai corretto uno. Avevi ragione. Chi ti ha insegnato a leggere un corpo?"),
        "after": ("I write my reports the way you taught me now: what happened, what killed, what was missed. Nobody reads them, but I sleep better.",
                  "Ora scrivo i miei rapporti come mi hai insegnato tu: che cosa è successo, che cosa ha ucciso, che cosa è sfuggito. Nessuno li legge, ma dormo meglio."),
        "quests": [
            ("side_lena_1", ("The Last Diagnosis: Cause of Death, Cold", "L'ultima diagnosi: causa di morte, freddo"),
             ("Frost wolves are found frozen in Frostveil, which frost wolves should not be. Bring Doctor Finch three of their pelts, from five of them.",
              "A Frostveil si trovano lupi del gelo congelati, e i lupi del gelo non dovrebbero congelare. Porta al dottor Finch tre delle loro pellicce, da cinque di loro."),
             [{"type": "kill", "enemy": "base:enemy/wolf_frost", "count": 5}, {"type": "collect", "item": "base:item/frost_pelt", "count": 3}],
             900, 600,
             ("Frost wolves, frozen solid. Animals born in the ice, dead of cold. It makes no sense, and things that make no sense make me "
              "nervous. I need to look at them closely. Three pelts, from the pack around the pass.",
              "Lupi del gelo, congelati. Animali nati nel ghiaccio, morti di freddo. Non ha senso, e le cose senza senso mi rendono nervoso. "
              "Devo guardarli da vicino. Tre pellicce, dal branco attorno al passo."),
             ("Three frost pelts. Do not wash them: the dirt is evidence.", "Tre pellicce del gelo. Non lavarle: lo sporco è una prova."),
             ("Look: frost on the inside of the fur. Something drank their warmth from within. You already suspected it, didn't you?",
              "Guarda: brina all'interno del pelo. Qualcosa ha bevuto il loro calore da dentro. Lo sospettavi già, vero?")),
            ("side_lena_2", ("The Last Diagnosis: A Fever in the Snow", "L'ultima diagnosi: una febbre nella neve"),
             ("A village of Frostveil is sick with a cold fever. Bring four snowflakes and three healing herbs for Doctor Finch's remedy.",
              "Un villaggio di Frostveil è malato di una febbre fredda. Porta quattro fiocchi di neve e tre erbe medicinali per il rimedio del dottor Finch."),
             [{"type": "collect", "item": "base:item/snowflake", "count": 4}, {"type": "collect", "item": "base:item/healing_herb", "count": 3}],
             1500, 1000,
             ("Now the people. A whole village with a fever that makes them shiver by the fire. Same signs as the wolves, earlier. "
              "There is a remedy in the old books: snowflakes that do not melt, and healing herbs. Four and three.",
              "Adesso le persone. Un villaggio intero con una febbre che li fa tremare accanto al fuoco. Gli stessi segni dei lupi, prima. "
              "Nei vecchi libri c'è un rimedio: fiocchi di neve che non si sciolgono, ed erbe medicinali. Quattro e tre."),
             ("Four snowflakes and three healing herbs. The fever does not wait.", "Quattro fiocchi di neve e tre erbe medicinali. La febbre non aspetta."),
             ("They are warm again, all of them. And all of them dreamed the same thing: a small cold light at the window, watching.",
              "Sono di nuovo caldi, tutti. E tutti hanno sognato la stessa cosa: una piccola luce fredda alla finestra, che guardava.")),
            ("side_lena_3", ("The Last Diagnosis: The Cold Light", "L'ultima diagnosi: la luce fredda"),
             ("Frost wisps drink the warmth of the sleeping. Stop five of them, and the wolves and the villages of Frostveil can sleep.",
              "I fuochi fatui del gelo bevono il calore di chi dorme. Fermane cinque, e i lupi e i villaggi di Frostveil potranno dormire."),
             [{"type": "kill", "enemy": "base:enemy/frost_wisp", "count": 5}], 3000, 2000,
             ("The cause. Frost wisps: they sit by the sleeping and drink their warmth, a little every night, until there is none. A "
              "diagnosis is worth nothing without a cure. Five of them.",
              "La causa. Fuochi fatui del gelo: si siedono accanto a chi dorme e ne bevono il calore, un poco ogni notte, finché non ne resta. "
              "Una diagnosi non vale niente senza una cura. Cinque."),
             ("Five frost wisps. They are fragile, and they are not innocent.", "Cinque fuochi fatui del gelo. Sono fragili, e non sono innocenti."),
             ("No fevers. No frozen wolves. Case closed, as you say. I have never closed one before.",
              "Niente febbri. Niente lupi congelati. Caso chiuso, come dici tu. Non ne avevo mai chiuso uno.")),
        ],
        "ending": {
            "ask": ("The guild needs a second physician, Lena, and I need someone who sees what I miss. Or... you came here with a second "
                    "chance. Maybe it is not for other people's deaths. Maybe it is for your life. Which?",
                    "La gilda ha bisogno di un secondo medico, Lena, e io di qualcuno che veda quello che mi sfugge. Oppure... sei arrivata qui con "
                    "una seconda possibilità. Forse non è per le morti degli altri. Forse è per la tua vita. Cosa scegli?"),
            "a": (("I will stay. Somebody has to notice what kills, before it does.", "Resto. Qualcuno deve accorgersi di ciò che uccide, prima che uccida."),
                  "base:item/frost_locket",
                  ("Then wear this locket: there is a frost wisp inside, the last one, asleep. A reminder of the first case we closed.",
                   "Allora porta questo medaglione: dentro c'è un fuoco fatuo del gelo, l'ultimo, addormentato. Un ricordo del primo caso che abbiamo chiuso.")),
            "b": (("I will live a little. My notes can wait.", "Vivrò un po'. I miei appunti possono aspettare."),
                  "base:item/glacier_spear",
                  ("Good. Then live far, and live well. Take this spear: the people of the pass gave it to me for you. They said you would go north.",
                   "Bene. Allora vivi lontano, e vivi bene. Prendi questa lancia: me l'ha data la gente del passo per te. Hanno detto che saresti andata a nord.")),
        },
    },
    {
        "key": "aldermere_baker_dorrit", "file": "dorrit", "variant": "brown", "dx": 385, "dy": -127, "protagonist": "gideon",
        "name": ("Dorrit Ash, baker from the Ashen Wastes", "Dorrit Ash, fornaia delle Terre di Cenere"),
        "stranger": ("Ash bread, Guest? My grandmother's recipe, from the Wastes. It tastes of smoke. Everything there did.",
                     "Pane di cenere, Ospite? La ricetta di mia nonna, delle Terre. Sa di fumo. Laggiù tutto sapeva di fumo."),
        "hello": ("That black sword. My grandmother told stories about a sword like that. She said it belonged to the King of the Wastes. "
                  "You do not look like a king. You look like a man who needs bread.",
                  "Quella spada nera. Mia nonna raccontava storie su una spada così. Diceva che era del Re delle Terre. Non sembri un re. "
                  "Sembri un uomo che ha bisogno di pane."),
        "after": ("The refugees of the Wastes buy my bread on Sundays and talk about going home. For the first time, they talk about it as a good thing.",
                  "I profughi delle Terre comprano il mio pane la domenica e parlano di tornare a casa. Per la prima volta, ne parlano come di una cosa bella."),
        "quests": [
            ("side_gideon_1", ("The Debts of a King: Poisoned Fields", "I debiti di un re: campi avvelenati"),
             ("Char slimes poison the fields of the refugees from the Ashen Wastes. Clear six of them and bring three char chunks, to show the farmers the ground is clean.",
              "Gli slime di carbone avvelenano i campi dei profughi delle Terre di Cenere. Eliminane sei e porta tre pezzi di carbone, per mostrare ai contadini che la terra è pulita."),
             [{"type": "kill", "enemy": "base:enemy/slime_char", "count": 6}, {"type": "collect", "item": "base:item/char_chunk", "count": 3}],
             900, 600,
             ("My people came from the Wastes three generations ago, after the old king fell. They farm a strip of land at the edge of the "
              "ash, and the char slimes eat the roots. Six of them, and three of their chunks for the farmers to see.",
              "La mia gente è venuta dalle Terre tre generazioni fa, dopo la caduta del vecchio re. Coltivano una striscia di terra al bordo "
              "della cenere, e gli slime di carbone mangiano le radici. Sei, e tre dei loro pezzi da mostrare ai contadini."),
             ("Six char slimes and three chunks. The farmers trust what they can hold.", "Sei slime di carbone e tre pezzi. I contadini si fidano di quello che possono tenere in mano."),
             ("The first green shoots on the ash in a hundred years. The farmers want to know your name. I told them 'the baker's friend'.",
              "I primi germogli verdi sulla cenere da cent'anni. I contadini vogliono sapere il tuo nome. Gli ho detto 'l'amico della fornaia'.")),
            ("side_gideon_2", ("The Debts of a King: A Hearth for the Wastes", "I debiti di un re: un focolare per le Terre"),
             ("The refugees want ovens that warm without burning. Bring Dorrit four ember cores and two magma shards to build them.",
              "I profughi vogliono forni che scaldino senza bruciare. Porta a Dorrit quattro nuclei di brace e due schegge di magma per costruirli."),
             [{"type": "collect", "item": "base:item/ember_core", "count": 4}, {"type": "collect", "item": "base:item/magma_shard", "count": 2}],
             1500, 1000,
             ("In the Wastes fire was a weapon. My grandmother said the king made it so. I want it to be bread again. An oven that keeps the "
              "heat of an ember core and never burns: four cores, and two magma shards for the walls.",
              "Nelle Terre il fuoco era un'arma. Mia nonna diceva che l'aveva voluto il re. Io voglio che torni a essere pane. Un forno che "
              "trattiene il calore di un nucleo di brace e non brucia mai: quattro nuclei, e due schegge di magma per le pareti."),
             ("Four ember cores and two magma shards. You hold them as if you knew them.", "Quattro nuclei di brace e due schegge di magma. Li tieni come se li conoscessi."),
             ("The first loaf from the new oven. Taste it. It tastes of smoke, still, but of the good kind. Of home.",
              "La prima pagnotta dal forno nuovo. Assaggia. Sa ancora di fumo, ma di quello buono. Di casa.")),
            ("side_gideon_3", ("The Debts of a King: The Old Fortress", "I debiti di un re: la vecchia fortezza"),
             ("Magma slimes crawl out of the ruins of the old fortress of the Wastes toward the refugee farms. Stop five of them.",
              "Gli slime di magma escono strisciando dalle rovine della vecchia fortezza delle Terre verso le fattorie dei profughi. Fermane cinque."),
             [{"type": "kill", "enemy": "base:enemy/slime_magma", "count": 5}], 3000, 2000,
             ("The magma slimes come out of the old fortress, the one of the king. Nobody goes near it: they say it still remembers him. "
              "Five of them, and the farms are safe. You are pale. Do you know that place?",
              "Gli slime di magma escono dalla vecchia fortezza, quella del re. Nessuno ci va vicino: dicono che si ricordi ancora di lui. "
              "Cinque, e le fattorie sono al sicuro. Sei pallido. Conosci quel posto?"),
             ("Five magma slimes from the old fortress. Come back before dark.", "Cinque slime di magma dalla vecchia fortezza. Torna prima che faccia buio."),
             ("You came back from the fortress, and you came back different. Lighter. I made you bread. Sit.",
              "Sei tornato dalla fortezza, e sei tornato diverso. Più leggero. Ti ho fatto il pane. Siediti.")),
        ],
        "ending": {
            "ask": ("I will ask you once, and then never again. My grandmother said the king had a black sword and eyes that did not blink "
                    "in the smoke. You do not blink in my oven's smoke, Gideon. You can tell me, or not. I will bake for you either way.",
                    "Te lo chiedo una volta, e poi mai più. Mia nonna diceva che il re aveva una spada nera e occhi che non battevano ciglio nel "
                    "fumo. Tu non batti ciglio nel fumo del mio forno, Gideon. Puoi dirmelo, oppure no. Cucinerò per te in ogni caso."),
            "a": (("It was me. I was the King of the Wastes. I am sorry.", "Ero io. Ero il Re delle Terre. Mi dispiace."),
                  "base:item/sovereigns_mantle",
                  ("Then this was yours too. My grandmother kept it: the mantle of the king, from the day he fell. She said someone should give it "
                   "back to him if he ever came home a better man. I think she meant you.",
                   "Allora anche questo era tuo. Mia nonna lo conservava: il mantello del re, dal giorno della sua caduta. Diceva che qualcuno "
                   "avrebbe dovuto restituirglielo se fosse mai tornato a casa migliore. Credo intendesse te.")),
            "b": (("I am a Guest, and your friend. That is all I want to be.", "Sono un Ospite, e un tuo amico. È tutto quello che voglio essere."),
                  "base:item/tyrants_hammer",
                  ("Then a friend gets the hammer of the forge, the one my family brought from the Wastes. It made swords once. Now it makes ovens. Like you.",
                   "Allora a un amico va il martello della fucina, quello che la mia famiglia portò dalle Terre. Una volta faceva spade. Ora fa forni. Come te.")),
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
