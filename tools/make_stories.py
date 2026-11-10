#!/usr/bin/env python3
"""Writes the first act of the story of each protagonist: three quests in a row, given by Sister Maren at the shrine of Lyra in Aldermere.

Maren (`shrine_keeper_maren`) has one dialogue with a line for each protagonist, shown to whoever carries that protagonist's keepsake (the
same way Pip tells the personal quests). The act of each protagonist is called "The First Echo": something of their old world has come
through the Threshold with them, and the third quest ends at a guardian of Verdalis. Run it after changing the tables here."""
from __future__ import annotations

import json

from make_towns import DATA, WORLD, set_texts

MAREN = {"key": "shrine_keeper_maren", "dialogue": "base:dialogue/npc/maren", "variant": "cream", "dx": 386, "dy": -129}
NAME = ("Sister Maren, keeper of Lyra's shrine", "Suor Maren, custode del santuario di Lyra")
HELLO = ("Lyra's shrine is small, Guest, and so am I. But she talks to me sometimes, and lately she talks about you.",
         "Il santuario di Lyra è piccolo, Ospite, e io pure. Ma ogni tanto lei mi parla, e ultimamente parla di te.")
BYE = ("Nothing for now, Sister.", "Niente per ora, sorella.")

KILL, COLLECT = "kill", "collect"
# protagonist: `ask` (the line of the menu), `done` (after the act), and three quests:
# (name, task, objectives, rewards {xp, gold, items}, offer, busy, thanks), every text as (en, it).
ACTS = {
    "ren": {
        "ask": ("The numbers I see: some of them are wrong.", "I numeri che vedo: alcuni sono sbagliati."),
        "done": ("The warden's number was your old desk, was it not? Lyra says the Threshold let it through with you. There will be more. You will count them.",
                 "Il numero del custode era la tua vecchia scrivania, vero? Lyra dice che la Soglia l'ha fatta passare con te. Ce ne saranno altri. Li conterai tu."),
        "quests": [
            (("A Second Line", "Una seconda riga"), ("Some green slimes carry a number that is not theirs. Defeat eight and see what the numbers do.", "Alcuni slime verdi portano un numero che non è il loro. Sconfiggine otto e guarda che cosa fanno i numeri."),
             [(KILL, "slime_green", 8)], {"xp": 150, "gold": 150, "items": {"potion_small": 3}},
             ("Wrong how? ...A second line, under the first, in a hand you know. Oh dear. Go and look at more of them. Eight should do.", "Sbagliati come? ...Una seconda riga, sotto la prima, in una calligrafia che conosci. Oh cielo. Vai a guardarne altri. Otto dovrebbero bastare."),
             ("Eight green slimes. Read the second line, not the first.", "Otto slime verdi. Leggi la seconda riga, non la prima."),
             ("The same four digits on every one. An extension number, you say? I do not know what that is, and I do not like it.", "Le stesse quattro cifre su ognuno. Un numero interno, dici? Non so cosa sia, e non mi piace.")),
            (("Ink for the Shrine", "Inchiostro per il santuario"), ("Sister Maren can make the hidden line show itself with spore caps and mint leaves.", "Suor Maren può far comparire la riga nascosta con cappelle di spore e foglie di menta."),
             [(COLLECT, "spore_cap", 4), (COLLECT, "mint_leaf", 4)], {"xp": 200, "gold": 200, "items": {"potion_mana_small": 3}},
             ("There is an ink that shows what the Threshold hides. It needs spore caps and mint. The myconids and the mint slimes will not give them up politely.", "C'è un inchiostro che mostra ciò che la Soglia nasconde. Servono cappelle di spore e menta. I miconidi e gli slime alla menta non le cedono con le buone."),
             ("Four caps, four leaves. I will warm the bowl.", "Quattro cappelle, quattro foglie. Io scaldo la ciotola."),
             ("There. The line points north-west, to the old barrow. Something there is counting too.", "Ecco. La riga punta a nord-ovest, al vecchio tumulo. Laggiù qualcosa sta contando a sua volta.")),
            (("The First Echo", "Il primo eco"), ("The hidden numbers lead to Grunmoor Barrow, north-west of Fenwick. Defeat its warden.", "I numeri nascosti portano al Tumulo di Grunmoor, a nord-ovest di Fenwick. Sconfiggi il suo custode."),
             [(KILL, "barrow_warden", 1)], {"xp": 500, "gold": 600, "items": {"knight_sword": 1, "brigandine": 1}},
             ("The warden of Grunmoor has stood a thousand years and never counted anything. Now it does. Go and see what it has of yours.", "Il custode di Grunmoor sta lì da mille anni e non ha mai contato niente. Adesso conta. Vai a vedere che cosa ha di tuo."),
             ("Grunmoor Barrow, north-west of Fenwick. Mind the warden; or rather, let it mind you.", "Il Tumulo di Grunmoor, a nord-ovest di Fenwick. Attento al custode; o meglio, che stia attento lui."),
             ("It fell, and the numbers stopped. Take these: the guild keeps them for whoever ends a thing like that.", "È caduto, e i numeri si sono fermati. Prendi: la gilda li tiene per chi mette fine a cose così.")),
        ],
    },
    "sakura": {
        "ask": ("My machine. I think it is still running.", "La mia macchina. Credo sia ancora accesa."),
        "done": ("So the door you opened never quite closed. Lyra is not angry. She says: next time, a smaller door.", "Dunque la porta che hai aperto non si è mai chiusa del tutto. Lyra non è arrabbiata. Dice: la prossima volta, una porta più piccola."),
        "quests": [
            (("Stray Light", "Luce vagante"), ("The mint slimes around Aldermere glow at night since Sakura arrived. Defeat eight and collect what they drop.", "Gli slime alla menta intorno ad Aldermere brillano di notte da quando è arrivata Sakura. Sconfiggine otto e raccogli ciò che lasciano."),
             [(KILL, "slime_mint", 8), (COLLECT, "mint_leaf", 3)], {"xp": 150, "gold": 150, "items": {"potion_mana_small": 4}},
             ("Running? Child, the mint slimes have been glowing since the night you fell. Glowing in equations. Go and see.", "Accesa? Figliola, gli slime alla menta brillano dalla notte in cui sei caduta. Brillano a equazioni. Vai a vedere."),
             ("Eight mint slimes, three leaves. Try not to correct their mathematics.", "Otto slime alla menta, tre foglie. Cerca di non correggere i loro calcoli."),
             ("Your handwriting, on a leaf. Lyra finds this very funny. I find it worrying.", "La tua calligrafia, su una foglia. Lyra lo trova molto divertente. Io lo trovo preoccupante.")),
            (("A Lens of Gel", "Una lente di gelatina"), ("Sakura needs slime gel and pine resin to build a lens that shows where the light leaks from.", "A Sakura servono gelatina di slime e resina di pino per costruire una lente che mostri da dove esce la luce."),
             [(COLLECT, "slime_gel", 5), (COLLECT, "pine_resin", 2)], {"xp": 200, "gold": 200, "items": {"potion_mana_medium": 1}},
             ("You want to build an instrument. Of course you do. Gel for the lens, resin to hold it. The pines have resin if you ask the trunk firmly.", "Vuoi costruire uno strumento. Naturalmente. Gelatina per la lente, resina per tenerla. I pini danno resina, se la chiedi al tronco con decisione."),
             ("Five of gel, two of resin. I will find you a table.", "Cinque di gelatina, due di resina. Ti trovo un tavolo."),
             ("It works. It points south, at Mint Hollow. And it hums your name.", "Funziona. Punta a sud, verso la Conca della Menta. E canticchia il tuo nome.")),
            (("The First Echo", "Il primo eco"), ("The light leaks from Mint Hollow, south-west of Fenwick. Defeat the Mint Matron that drank it.", "La luce esce dalla Conca della Menta, a sud-ovest di Fenwick. Sconfiggi la Matrona di Menta che l'ha bevuta."),
             [(KILL, "mint_matron", 1)], {"xp": 500, "gold": 600, "items": {"mage_robe": 1, "potion_mana_medium": 2}},
             ("The Matron of the Hollow has swallowed a piece of your machine and grown clever. A clever slime is the last thing Verdalis needs.", "La Matrona della Conca ha ingoiato un pezzo della tua macchina ed è diventata furba. Uno slime furbo è l'ultima cosa che serve a Verdalis."),
             ("Mint Hollow, south-west of Fenwick. It will try to argue. Do not let it.", "La Conca della Menta, a sud-ovest di Fenwick. Proverà a discutere. Non lasciarglielo fare."),
             ("Gone, and the glow with it. This robe was woven for a scholar. You are the nearest thing we have.", "Sparita, e il bagliore con lei. Questa veste fu tessuta per uno studioso. Tu sei la cosa più simile che abbiamo.")),
        ],
    },
    "daichi": {
        "ask": ("I smell smoke. Nobody else does.", "Sento odore di fumo. Nessun altro lo sente."),
        "done": ("It was your fire, the one from the third floor. It followed you, and you put it out twice. Rest, if you know how.", "Era il tuo incendio, quello del terzo piano. Ti ha seguito, e l'hai spento due volte. Riposa, se sai come si fa."),
        "quests": [
            (("Where There Is Smoke", "Dove c'è fumo"), ("Tawny wolves are fleeing something on the hills. Drive back six of them and keep the road safe.", "I lupi fulvi scappano da qualcosa sulle colline. Respingine sei e tieni sicura la strada."),
             [(KILL, "wolf_tawny", 6)], {"xp": 150, "gold": 150, "items": {"potion_small": 4}},
             ("Smoke. Yes. The wolves smell it too: they are running toward the road, toward the carts. First the people, you would say.", "Fumo. Sì. Lo sentono anche i lupi: corrono verso la strada, verso i carri. Prima le persone, diresti tu."),
             ("Six tawny wolves, before they reach the carts.", "Sei lupi fulvi, prima che arrivino ai carri."),
             ("The road is safe. And their fur was singed. Something is burning that does not burn here.", "La strada è sicura. E avevano il pelo bruciacchiato. Brucia qualcosa che qui non brucia.")),
            (("A Line in the Grass", "Una linea nell'erba"), ("Daichi wants a firebreak around Aldermere: logs and stone to hold a line.", "Daichi vuole una fascia tagliafuoco intorno ad Aldermere: ceppi e pietra per tenere una linea."),
             [(COLLECT, "wood_log", 6), (COLLECT, "stone_chunk", 4)], {"xp": 200, "gold": 200, "items": {"hearty_stew": 2}},
             ("A firebreak, you call it. Timber and stone in a ring, before there is any fire to stop. Nobody here thinks that way. Do it.", "Una fascia tagliafuoco, la chiami. Legna e pietra in cerchio, prima che ci sia un fuoco da fermare. Qui nessuno ragiona così. Falla."),
             ("Six logs, four stones. The trees and the rocks will not mind.", "Sei ceppi, quattro pietre. Agli alberi e alle rocce non dispiacerà."),
             ("The ring is laid. And the smoke comes from one place now: the old barrow.", "Il cerchio è fatto. E adesso il fumo viene da un posto solo: il vecchio tumulo.")),
            (("The First Echo", "Il primo eco"), ("The smoke rises from Grunmoor Barrow, north-west of Fenwick. Its warden burns with a fire from another world.", "Il fumo sale dal Tumulo di Grunmoor, a nord-ovest di Fenwick. Il suo custode arde di un fuoco di un altro mondo."),
             [(KILL, "barrow_warden", 1)], {"xp": 500, "gold": 600, "items": {"war_axe": 1, "splint_mail": 1}},
             ("The warden of Grunmoor is burning and does not fall. That is your fire, Guest. I think you know how it ends.", "Il custode di Grunmoor brucia e non cade. Quello è il tuo fuoco, Ospite. Credo tu sappia come finisce."),
             ("Grunmoor Barrow, north-west of Fenwick. Go in. You always do.", "Il Tumulo di Grunmoor, a nord-ovest di Fenwick. Entra. Lo fai sempre."),
             ("Out. Cold. The smith made this axe for a hand that does not shake. Yours does not.", "Spento. Freddo. Il fabbro ha fatto quest'ascia per una mano che non trema. La tua non trema.")),
        ],
    },
    "haruka": {
        "ask": ("The slimes here are sick, Sister.", "Gli slime qui sono malati, sorella."),
        "done": ("You healed a thing nobody thought could be ill. Lyra asks whether you would look at her cat. I did not know she had a cat.", "Hai guarito una cosa che nessuno pensava potesse ammalarsi. Lyra chiede se daresti un'occhiata al suo gatto. Non sapevo avesse un gatto."),
        "quests": [
            (("Bedside Manner", "Le buone maniere"), ("The green slimes near Aldermere are feverish and wild. Calm eight of them the only way they understand.", "Gli slime verdi vicino ad Aldermere hanno la febbre e sono furiosi. Calmane otto nell'unico modo che capiscono."),
             [(KILL, "slime_green", 8), (COLLECT, "slime_gel", 4)], {"xp": 150, "gold": 150, "items": {"potion_small": 4}},
             ("Sick? Slimes? ...You touched one. Of course you did. Bring me samples, then, and calm the worst of them.", "Malati? Gli slime? ...Ne hai toccato uno. Naturalmente. Portami dei campioni, allora, e calma i peggiori."),
             ("Eight green slimes, four of gel. Wash your hands. I do not know why I said that.", "Otto slime verdi, quattro di gelatina. Lavati le mani. Non so perché l'ho detto."),
             ("The gel is warm. Slime gel is never warm. You were right, and I owe you an apology and a kettle.", "La gelatina è calda. La gelatina di slime non è mai calda. Avevi ragione, e ti devo delle scuse e un bollitore.")),
            (("A Tonic for the Meadow", "Un tonico per il prato"), ("Haruka can brew a remedy for the slimes from healing herbs and wild berries.", "Haruka può preparare un rimedio per gli slime con erbe curative e bacche selvatiche."),
             [(COLLECT, "healing_herb", 5), (COLLECT, "wild_berries", 6)], {"xp": 200, "gold": 200, "items": {"tonic": 6}},
             ("A medicine for monsters. The guild will laugh. Let them. Herbs and berries, from the bushes; I will lend you the shrine's pot.", "Una medicina per mostri. La gilda riderà. Lasciali ridere. Erbe e bacche, dai cespugli; ti presto la pentola del santuario."),
             ("Five herbs, six handfuls of berries.", "Cinque erbe, sei manciate di bacche."),
             ("They drank it. All of them, in a line, like children. But one did not come: the big one, in the Hollow.", "L'hanno bevuto. Tutti, in fila, come bambini. Ma uno non è venuto: quello grosso, nella Conca.")),
            (("The First Echo", "Il primo eco"), ("The fever began with the Mint Matron of Mint Hollow, south-west of Fenwick. End her pain.", "La febbre è cominciata dalla Matrona di Menta della Conca, a sud-ovest di Fenwick. Metti fine al suo dolore."),
             [(KILL, "mint_matron", 1)], {"xp": 500, "gold": 600, "items": {"warding_robe": 1, "potion_medium": 3}},
             ("The Matron is the mother of every mint slime in Verdalis, and she is past any tonic. You know what a vet does then. I am sorry.", "La Matrona è la madre di ogni slime alla menta di Verdalis, e nessun tonico può più aiutarla. Sai cosa fa un veterinario in questi casi. Mi dispiace."),
             ("Mint Hollow, south-west of Fenwick. Be quick. Be kind.", "La Conca della Menta, a sud-ovest di Fenwick. Fai presto. Sii gentile."),
             ("It is done, and the meadow is quiet. This robe keeps harm away. Lyra says you have taken enough of it for others.", "È fatta, e il prato è tranquillo. Questa veste tiene lontano il male. Lyra dice che ne hai preso abbastanza per gli altri.")),
        ],
    },
    "marco": {
        "ask": ("Something here is under pressure. I can hear it.", "Qui c'è qualcosa sotto pressione. Lo sento."),
        "done": ("You vented a king. The guild has no form for that. I have written 'cooking accident', which you will find familiar.", "Hai sfiatato un re. La gilda non ha un modulo per questo. Ho scritto 'incidente di cucina', che ti suonerà familiare."),
        "quests": [
            (("A Matter of Units", "Questione di unità"), ("The myconids near Aldermere swell and burst since Marco arrived. Defeat six and gather their caps.", "I miconidi vicino ad Aldermere si gonfiano e scoppiano da quando è arrivato Marco. Sconfiggine sei e raccogli le loro cappelle."),
             [(KILL, "myconid", 6), (COLLECT, "spore_cap", 3)], {"xp": 150, "gold": 150, "items": {"travel_ration": 3}},
             ("Pressure. The mushroom folk have been popping like corks all week. If that is your doing, it is also your job.", "Pressione. I funghi scoppiano come tappi da una settimana. Se è opera tua, è anche compito tuo."),
             ("Six myconids, three caps. Stand upwind.", "Sei miconidi, tre cappelle. Mettiti sopravento."),
             ("Steam inside a mushroom. You say that with such delight. Please stop saying it with such delight.", "Vapore dentro un fungo. Lo dici con una tale gioia. Per favore smetti di dirlo con una tale gioia.")),
            (("A Proper Valve", "Una valvola come si deve"), ("Marco will build a valve to let the pressure out: iron ore and wood for the fitting.", "Marco costruirà una valvola per far uscire la pressione: minerale di ferro e legna per il raccordo."),
             [(COLLECT, "iron_ore", 4), (COLLECT, "wood_log", 4)], {"xp": 200, "gold": 200, "items": {"honey_cake": 4}},
             ("A valve. I will pretend to know the word. Iron and wood, you say; the rocks and the trees have both.", "Una valvola. Fingerò di conoscere la parola. Ferro e legna, dici: rocce e alberi hanno entrambi."),
             ("Four of ore, four logs. The smith is curious. Do not explain it to him yet.", "Quattro di ferro, quattro ceppi. Il fabbro è curioso. Non spiegarglielo ancora."),
             ("It whistles. And the whistle comes loudest from the cellar by Fenwick, where the big one lives.", "Fischia. E il fischio è più forte dalla cantina vicino a Fenwick, dove vive quello grosso.")),
            (("The First Echo", "Il primo eco"), ("The pressure gathers in Mossveil Cellar, north of Fenwick. Defeat the Gel King before he bursts.", "La pressione si accumula nella Cantina di Mossveil, a nord di Fenwick. Sconfiggi il Re Gelatina prima che scoppi."),
             [(KILL, "gel_king", 1)], {"xp": 500, "gold": 600, "items": {"claymore": 1, "brigandine": 1}},
             ("The Gel King is three times his size and still growing. You know what a sealed pot does. So does half of your old kitchen.", "Il Re Gelatina è tre volte più grosso e continua a crescere. Tu sai cosa fa una pentola sigillata. Lo sa anche mezza tua vecchia cucina."),
             ("Mossveil Cellar, north of Fenwick. Open him gently.", "La Cantina di Mossveil, a nord di Fenwick. Aprilo con delicatezza."),
             ("No explosion. I am almost disappointed. The smith sends this, and asks what a 'gasket' is.", "Nessuna esplosione. Sono quasi delusa. Il fabbro ti manda questa, e chiede cos'è una 'guarnizione'.")),
        ],
    },
    "yuki": {
        "ask": ("Someone has been in my pocket. That is not possible.", "Qualcuno ha frugato nella mia tasca. Non è possibile."),
        "done": ("A thief robbed, and she gave the painting back. Lyra is telling everyone. I am sorry; she has few stories this good.", "Una ladra derubata, e ha restituito il quadro. Lyra lo sta raccontando a tutti. Mi dispiace: ha poche storie così belle."),
        "quests": [
            (("Light Fingers", "Dita leggere"), ("Things vanish from Aldermere and turn up on tawny wolves. Take back what six of them carry.", "Ad Aldermere spariscono cose che ricompaiono addosso ai lupi fulvi. Riprendi ciò che portano sei di loro."),
             [(KILL, "wolf_tawny", 6), (COLLECT, "tawny_fur", 2)], {"xp": 150, "gold": 200, "items": {"potion_small": 3}},
             ("Your pocket that nobody can open? Then you will like this: half the town has lost a spoon, and the wolves are wearing them.", "La tua tasca che nessuno può aprire? Allora questo ti piacerà: mezza città ha perso un cucchiaio, e li portano addosso i lupi."),
             ("Six tawny wolves, two furs. Count the spoons.", "Sei lupi fulvi, due pellicce. Conta i cucchiai."),
             ("Eleven spoons and a candlestick. And a corner of canvas, painted. You have gone quite pale.", "Undici cucchiai e un candeliere. E un angolo di tela, dipinta. Sei diventata pallida.")),
            (("Bait", "L'esca"), ("Yuki will lay a trap for the thief: spider-fine thread is not at hand, so pine resin and dry branches will do.", "Yuki tenderà una trappola al ladro: resina di pino e rami secchi faranno al caso."),
             [(COLLECT, "pine_resin", 3), (COLLECT, "dry_branch", 4)], {"xp": 200, "gold": 250, "items": {"potion_small": 3}},
             ("You want to catch a thief. I will not ask how you know the way. Resin and dry branches, you say. The pines and the dead trees.", "Vuoi prendere un ladro. Non ti chiedo come conosci il metodo. Resina e rami secchi, dici. I pini e gli alberi morti."),
             ("Three of resin, four branches.", "Tre di resina, quattro rami."),
             ("Sticky footprints, as big as a table, going north-west. Into the barrow. Nothing alive has feet like that.", "Impronte appiccicose, grandi come un tavolo, verso nord-ovest. Dentro il tumulo. Niente di vivo ha piedi così.")),
            (("The First Echo", "Il primo eco"), ("The thief is the warden of Grunmoor Barrow, north-west of Fenwick, and it has Yuki's painting.", "Il ladro è il custode del Tumulo di Grunmoor, a nord-ovest di Fenwick, e ha il quadro di Yuki."),
             [(KILL, "barrow_warden", 1)], {"xp": 500, "gold": 800, "items": {"saber": 1, "scale_mail": 1}},
             ("The warden collects what does not belong here. Your painting does not. Neither, forgive me, do you. Go and settle which of you keeps it.", "Il custode raccoglie ciò che non appartiene a questo mondo. Il tuo quadro non gli appartiene. E nemmeno tu, perdonami. Vai a stabilire chi dei due se lo tiene."),
             ("Grunmoor Barrow, north-west of Fenwick. Steal it back. Just this once I will call it that.", "Il Tumulo di Grunmoor, a nord-ovest di Fenwick. Riprenditelo. Per questa volta lo chiamo così."),
             ("You hung it in the shrine. It is the first beautiful thing these walls have had. Take this; the guild pays honest work honestly.", "L'hai appeso nel santuario. È la prima cosa bella che queste mura abbiano avuto. Prendi: la gilda paga onestamente il lavoro onesto.")),
        ],
    },
    "lena": {
        "ask": ("I have seen this death before. On my table.", "Questa morte l'ho già vista. Sul mio tavolo."),
        "done": ("Your last case, finished in another world. You may close the file. Lyra kept the pen for you.", "Il tuo ultimo caso, chiuso in un altro mondo. Puoi archiviare il fascicolo. Lyra ti ha tenuto la penna."),
        "quests": [
            (("Cause Unknown", "Causa ignota"), ("Myconids are dying around Aldermere with no wound. Examine six, in the only way they allow.", "Intorno ad Aldermere i miconidi muoiono senza ferite. Esaminane sei, nell'unico modo che permettono."),
             [(KILL, "myconid", 6), (COLLECT, "spore_cap", 4)], {"xp": 150, "gold": 150, "items": {"potion_mana_small": 3}},
             ("Before? Then you will want to see more. The mushroom folk lie down and do not get up. No mark on them. Bring me what you find.", "Già vista? Allora vorrai vederne altre. I funghi si sdraiano e non si rialzano. Nessun segno. Portami ciò che trovi."),
             ("Six myconids, four caps. You are humming. Please do not hum.", "Sei miconidi, quattro cappelle. Stai canticchiando. Per favore non canticchiare.")
             , ("The same grey ring under every cap. You drew it in your notes before I showed you. That frightens me more than the ring.", "Lo stesso anello grigio sotto ogni cappella. L'hai disegnato nei tuoi appunti prima che te lo mostrassi. Questo mi spaventa più dell'anello.")),
            (("A Second Opinion", "Un secondo parere"), ("Lena needs mint leaves and healing herbs to test what the grey ring is.", "A Lena servono foglie di menta ed erbe curative per capire che cos'è l'anello grigio."),
             [(COLLECT, "mint_leaf", 4), (COLLECT, "healing_herb", 4)], {"xp": 200, "gold": 200, "items": {"potion_mana_medium": 1}},
             ("A test. With leaves. I thought you only looked at the dead. Very well: mint and herbs.", "Un'analisi. Con le foglie. Pensavo guardassi solo i morti. Va bene: menta ed erbe."),
             ("Four leaves of mint, four herbs.", "Quattro foglie di menta, quattro erbe."),
             ("It turned black. You say that means it came from the water, and the water comes from the cellar. I believe you. Nobody argues with you twice.", "È diventato nero. Dici che vuol dire che viene dall'acqua, e l'acqua viene dalla cantina. Ti credo. Nessuno ti contraddice due volte.")),
            (("The First Echo", "Il primo eco"), ("The poison seeps from Mossveil Cellar, north of Fenwick. The Gel King carries it. End the case.", "Il veleno filtra dalla Cantina di Mossveil, a nord di Fenwick. Lo porta il Re Gelatina. Chiudi il caso."),
             [(KILL, "gel_king", 1)], {"xp": 500, "gold": 600, "items": {"mage_robe": 1, "runed_blade": 1}},
             ("The Gel King swallowed something that fell with you: the last thing you were studying. It is killing the meadow from below.", "Il Re Gelatina ha ingoiato qualcosa che è caduto con te: l'ultima cosa che stavi studiando. Sta uccidendo il prato da sotto."),
             ("Mossveil Cellar, north of Fenwick. Write it up afterwards. You will anyway.", "La Cantina di Mossveil, a nord di Fenwick. Il verbale lo scrivi dopo. Lo faresti comunque."),
             ("Case closed, you say, and you almost smiled. Take the blade and the robe. A doctor of the dead should at least be warm.", "Caso chiuso, dici, e quasi sorridevi. Prendi la lama e la veste. Un medico dei morti dovrebbe almeno stare al caldo.")),
        ],
    },
    "gideon": {
        "ask": ("Something in this land still calls me king.", "Qualcosa in questa terra mi chiama ancora re."),
        "done": ("You refused a crown. Lyra did not think you would. She lost a wager to me, and I intend to collect.", "Hai rifiutato una corona. Lyra non credeva l'avresti fatto. Ha perso una scommessa con me, e intendo riscuotere."),
        "quests": [
            (("Loyal Subjects", "Sudditi fedeli"), ("Tawny wolves kneel when Gideon passes and then raid the farms in his name. Correct eight of them.", "I lupi fulvi si inginocchiano quando passa Gideon e poi razziano le fattorie in suo nome. Correggine otto."),
             [(KILL, "wolf_tawny", 8)], {"xp": 150, "gold": 150, "items": {"potion_small": 3}},
             ("King. Yes. The wolves have been stealing sheep 'for the throne', the shepherds say. Which throne, I wonder. Deal with your court.", "Re. Sì. I lupi rubano pecore 'per il trono', dicono i pastori. Quale trono, mi chiedo. Occupati della tua corte."),
             ("Eight tawny wolves. Dismiss them. Permanently.", "Otto lupi fulvi. Congedali. In via definitiva."),
             ("The shepherds sent a cheese. For you. Nobody ever sent you a cheese before, did they?", "I pastori hanno mandato un formaggio. Per te. Nessuno ti aveva mai mandato un formaggio, vero?")),
            (("Tribute, Returned", "Il tributo restituito"), ("Gideon will pay back what was taken in his name: furs and gel for the farms.", "Gideon ripagherà ciò che è stato preso in suo nome: pellicce e gelatina per le fattorie."),
             [(COLLECT, "tawny_fur", 3), (COLLECT, "slime_gel", 5)], {"xp": 200, "gold": 200, "items": {"hearty_stew": 3}},
             ("You wish to repay them. From your own hand. I will sit down; I am not as young as I was. Furs and gel will mend what was lost.", "Vuoi ripagarli. Di tua mano. Mi siedo: non ho più l'età. Pellicce e gelatina ripareranno ciò che è andato perduto."),
             ("Three furs, five of gel.", "Tre pellicce, cinque di gelatina."),
             ("They bowed to you. Not from fear. You did not know what to do with your hands. It was the best thing I have seen all year.", "Si sono inchinati. Non per paura. Non sapevi dove mettere le mani. È la cosa più bella che ho visto quest'anno.")),
            (("The First Echo", "Il primo eco"), ("A voice from Mossveil Cellar offers Gideon his old crown. The Gel King wears it. Answer him.", "Una voce dalla Cantina di Mossveil offre a Gideon la sua vecchia corona. La porta il Re Gelatina. Rispondigli."),
             [(KILL, "gel_king", 1)], {"xp": 500, "gold": 600, "items": {"moon_blade": 1, "plate_cuirass": 1}},
             ("There is a king in the cellar by Fenwick. He found a crown that fell with you, and he says it is yours if you come and rule. Well?", "C'è un re nella cantina vicino a Fenwick. Ha trovato una corona caduta con te, e dice che è tua se vai a regnare. Ebbene?"),
             ("Mossveil Cellar, north of Fenwick. Give him your answer.", "La Cantina di Mossveil, a nord di Fenwick. Dagli la tua risposta."),
             ("You left the crown in the mud. Take this blade instead. It suits a man who has decided what he is.", "Hai lasciato la corona nel fango. Prendi questa lama, piuttosto. Si addice a un uomo che ha deciso che cosa essere.")),
        ],
    },
}


def qid(name: str, i: int) -> str:
    return f"base:quest/side/act1_{name}_{i + 1}"


def main() -> None:
    core = {"en": {}, "it": {}}
    content = {"en": {}, "it": {}}
    for i, lang in enumerate(("en", "it")):
        core[lang]["speaker.shrine_keeper_maren"] = NAME[i]
        core[lang]["dlg.maren.hello"] = HELLO[i]
        core[lang]["dlg.maren.bye"] = BYE[i]

    def say(text: str, then: str) -> dict:
        return {"type": "say", "speaker": MAREN["key"], "text": f"$i18n:dlg.maren.{text}", "next": then}

    nodes: dict[str, dict] = {"start": say("hello", "menu")}
    choices = []
    for name, act in ACTS.items():
        choices.append({"text": f"$i18n:dlg.maren.{name}.ask", "when": {"has_item": {"item": f"base:item/keepsake_{name}", "qty": 1}}, "next": f"{name}_c0"})
        for i, lang in enumerate(("en", "it")):
            core[lang][f"dlg.maren.{name}.ask"] = act["ask"][i]
            core[lang][f"dlg.maren.{name}.done"] = act["done"][i]
        count = len(act["quests"])
        for n, (title, task, objectives, rewards, offer, busy, thanks) in enumerate(act["quests"]):
            nxt = f"{name}_c{n + 1}" if n + 1 < count else f"{name}_done"
            thanked = f"act1_{name}_{n + 1}_thanked"
            nodes[f"{name}_c{n}"] = {"type": "condition", "when": {"quest_done": qid(name, n)}, "then": f"{name}_t{n}", "else": f"{name}_a{n}"}
            nodes[f"{name}_t{n}"] = {"type": "condition", "when": {"flag": thanked}, "then": nxt, "else": f"{name}_thanks{n}"}
            nodes[f"{name}_thanks{n}"] = say(f"{name}.q{n + 1}.thanks", f"{name}_flag{n}")
            nodes[f"{name}_flag{n}"] = {"type": "effects", "effects": [{"effect": "set_flag", "flag": thanked, "value": True}], "next": "end"}
            nodes[f"{name}_a{n}"] = {"type": "condition", "when": {"quest_active": qid(name, n)}, "then": f"{name}_busy{n}", "else": f"{name}_offer{n}"}
            nodes[f"{name}_busy{n}"] = say(f"{name}.q{n + 1}.busy", "end")
            nodes[f"{name}_offer{n}"] = say(f"{name}.q{n + 1}.offer", f"{name}_choice{n}")
            nodes[f"{name}_choice{n}"] = {"type": "choice", "choices": [
                {"text": "$i18n:dlg.wayfarer.accept", "effects": [{"effect": "start_quest", "quest": qid(name, n)}], "next": "end"},
                {"text": "$i18n:dlg.wayfarer.later", "next": "end"}]}
            quest = {
                "$schema": "../../../../schemas/quest.schema.json", "id": qid(name, n), "name": f"$i18n:quest.act1_{name}_{n + 1}.name", "kind": "side",
                "stages": [{"id": "task", "journal": f"$i18n:quest.act1_{name}_{n + 1}.task", "next": "end", "objectives": [
                    {"type": "kill", "enemy": f"base:enemy/{target}", "count": c} if kind == KILL else {"type": "collect", "item": f"base:item/{target}", "count": c}
                    for kind, target, c in objectives]}],
                "rewards": [{"effect": "add_xp", "amount": rewards["xp"]}, {"effect": "add_gold", "amount": rewards["gold"]}, {"effect": "add_guild_points", "amount": 20 * (n + 1)}]
                + [{"effect": "add_item", "item": f"base:item/{item}", "qty": qty} for item, qty in rewards["items"].items()],
            }
            # the objectives go before `next` in the files of the pack: keep that order
            stage = quest["stages"][0]
            quest["stages"][0] = {"id": stage["id"], "journal": stage["journal"], "objectives": stage["objectives"], "next": stage["next"]}
            (DATA / "quests" / "side" / f"act1_{name}_{n + 1}.json").write_text(json.dumps(quest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            for i, lang in enumerate(("en", "it")):
                core[lang][f"dlg.maren.{name}.q{n + 1}.offer"] = offer[i]
                core[lang][f"dlg.maren.{name}.q{n + 1}.busy"] = busy[i]
                core[lang][f"dlg.maren.{name}.q{n + 1}.thanks"] = thanks[i]
                content[lang][f"quest.act1_{name}_{n + 1}.name"] = title[i]
                content[lang][f"quest.act1_{name}_{n + 1}.task"] = task[i]
        nodes[f"{name}_done"] = say(f"{name}.done", "end")
    choices.append({"text": "$i18n:dlg.maren.bye", "next": "end"})
    nodes["menu"] = {"type": "choice", "choices": choices}
    doc = {"$schema": "../../../../schemas/dialogue.schema.json", "id": MAREN["dialogue"], "start": "start", "nodes": nodes}
    (DATA / "dialogues" / "npc" / "maren.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for lang in ("en", "it"):
        set_texts("core.json", lang, core[lang])
        set_texts("content.json", lang, content[lang])

    # Maren's line in `npcs` of the world data: replaced when it is there, added after the last one otherwise
    raw = WORLD.read_text(encoding="utf-8", newline="")
    newline = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.replace("\r\n", "\n").split("\n")
    text = "    { " + ", ".join(f"{json.dumps(k)}: {json.dumps(v)}" for k, v in MAREN.items()) + " }"
    found = [k for k, line in enumerate(lines) if f'"key": "{MAREN["key"]}"' in line]
    if found:
        lines[found[0]] = text + ("," if lines[found[0]].rstrip().endswith(",") else "")
    else:
        start = next(k for k, line in enumerate(lines) if line.strip().startswith('"npcs": ['))
        last = next(k for k in range(start, len(lines)) if lines[k].strip().startswith("]")) - 1
        lines[last] = lines[last].rstrip() + ","
        lines.insert(last + 1, text)
    WORLD.write_text(newline.join(lines), encoding="utf-8", newline="")
    print(f"wrote the first act of {len(ACTS)} protagonists: {sum(len(a['quests']) for a in ACTS.values())} quests")


if __name__ == "__main__":
    main()
