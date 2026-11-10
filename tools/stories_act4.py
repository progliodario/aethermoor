"""The epilogue of the story of each protagonist, "The Echo Itself": one quest that `make_stories.py` adds after the third act.

With every piece of the old world returned, what is left is the moment itself, the one that brought the Guest here, grown into a creature:
the Echo (`tools/make_echoes.py`), waiting in a sanctum of the ring of eight around the start. Same shape as the acts, one quest."""
from __future__ import annotations

KILL = "kill"

ACT4 = {
    "ren": {
        "done": ("No more overtime, Ren. Lyra has struck it from the calendar of the world. She asks what you will do with your evenings. I suggested the tavern. You suggested a nap. She approves.",
                 "Niente più straordinari, Ren. Lyra li ha cancellati dal calendario del mondo. Chiede che cosa farai delle tue serate. Ho suggerito la taverna. Tu un pisolino. Lei approva."),
        "quests": [
            (("The Echo Itself", "L'eco stessa"), ("The last overtime of Ren's old life has taken a shape and waits in the Sanctum of Numbers, west of the start. Clock out.", "L'ultimo straordinario della vecchia vita di Ren ha preso forma e aspetta nel Santuario dei Numeri, a ovest della partenza. Timbra l'uscita."),
             [(KILL, "echo_ren", 1)], {"xp": 6000, "gold": 8000, "items": {"potion_large": 5}},
             ("One thing came through that was never a thing: the hour you stayed late, every night, for years. It has a body now, in a sanctum near the meadow where you woke.", "Una cosa è passata che non era mai stata una cosa: l'ora in cui restavi fino a tardi, ogni sera, per anni. Ora ha un corpo, in un santuario vicino al prato dove ti sei svegliato."),
             ("The Sanctum of Numbers, west of the start, a little north.", "Il Santuario dei Numeri, a ovest della partenza, un po' a nord."),
             ("It said 'just five more minutes' before it fell. You said 'no'. I have never heard you say it before.", "Prima di cadere ha detto 'ancora cinque minuti'. Tu hai detto 'no'. Non te l'avevo mai sentito dire.")),
        ],
    },
    "sakura": {
        "done": ("The equation is finished, and so, Lyra says, is the doctorate. She has signed it herself. It glows a little. Do not let the slimes near it.",
                 "L'equazione è finita, e così, dice Lyra, il dottorato. L'ha firmato lei stessa. Brilla un po'. Non lasciarlo vicino agli slime."),
        "quests": [
            (("The Echo Itself", "L'eco stessa"), ("The equation Sakura never finished has become a creature of light in the Sanctum of Light, west of the start. Finish it.", "L'equazione che Sakura non ha mai finito è diventata una creatura di luce nel Santuario della Luce, a ovest della partenza. Finiscila."),
             [(KILL, "echo_sakura", 1)], {"xp": 6000, "gold": 8000, "items": {"potion_mana_medium": 5}},
             ("Three minutes before your doctorate, you left one line unfinished. It followed you, and it has grown tired of waiting. It is in a sanctum near the meadow.", "Tre minuti prima del dottorato, hai lasciato una riga incompiuta. Ti ha seguita, e si è stancata di aspettare. È in un santuario vicino al prato."),
             ("The Sanctum of Light, west of the start, a little south.", "Il Santuario della Luce, a ovest della partenza, un po' a sud."),
             ("Equals sign, and then nothing more to write. You sat on the steps of the sanctum and laughed until you cried.", "Il segno di uguale, e poi niente più da scrivere. Ti sei seduta sui gradini del santuario e hai riso fino alle lacrime.")),
        ],
    },
    "daichi": {
        "done": ("The third floor is safe. Every floor is. Lyra asks you to put down the axe for one afternoon. I have hidden it. You found it in a minute. I am going to try a better place.",
                 "Il terzo piano è salvo. Tutti i piani lo sono. Lyra ti chiede di posare l'ascia per un pomeriggio. L'ho nascosta. L'hai trovata in un minuto. Proverò un posto migliore."),
        "quests": [
            (("The Echo Itself", "L'eco stessa"), ("The moment the floor gave way has taken a shape of smoke and fire in the Sanctum of Embers, north of the start. Walk out.", "L'istante in cui il pavimento ha ceduto ha preso forma di fumo e fuoco nel Santuario delle Braci, a nord della partenza. Esci."),
             [(KILL, "echo_daichi", 1)], {"xp": 6000, "gold": 8000, "items": {"potion_large": 5}},
             ("You put out every fire in this world except one: the instant the floor gave way. It is in a sanctum near the meadow. This time, you walk out.", "Hai spento ogni fuoco di questo mondo tranne uno: l'istante in cui il pavimento ha ceduto. È in un santuario vicino al prato. Stavolta esci tu."),
             ("The Sanctum of Embers, north of the start, a little west.", "Il Santuario delle Braci, a nord della partenza, un po' a ovest."),
             ("You walked out of the smoke on your own feet. The village was waiting at the door, all of them. They had been counting.", "Sei uscito dal fumo sulle tue gambe. Il villaggio aspettava sulla porta, tutto. Stavano contando.")),
        ],
    },
    "haruka": {
        "done": ("The rain has stopped, on the road and in you. Lyra's cat now lives at the shrine. It was not my decision. I am told it was yours.",
                 "La pioggia ha smesso, sulla strada e dentro di te. Il gatto di Lyra ora vive al santuario. Non l'ho deciso io. Mi dicono l'abbia deciso tu."),
        "quests": [
            (("The Echo Itself", "L'eco stessa"), ("The rain on the road where Haruka stopped has become a creature in the Sanctum of Rain, south of the start. Let it pass.", "La pioggia sulla strada dove Haruka si è fermata è diventata una creatura nel Santuario della Pioggia, a sud della partenza. Lasciala passare."),
             [(KILL, "echo_haruka", 1)], {"xp": 6000, "gold": 8000, "items": {"tonic": 10}},
             ("The rain of that night never stopped falling, Haruka. Somewhere it is still raining on that road. Here, it is raining in a sanctum near the meadow.", "La pioggia di quella notte non ha mai smesso di cadere, Haruka. Da qualche parte piove ancora su quella strada. Qui, piove in un santuario vicino al prato."),
             ("The Sanctum of Rain, south of the start, a little west.", "Il Santuario della Pioggia, a sud della partenza, un po' a ovest."),
             ("The sky cleared over the sanctum, and a dog's bark came from nowhere, once, happy. You knew it. So did I, somehow.", "Il cielo si è aperto sopra il santuario, e da nessuna parte è arrivato un abbaio, una volta, felice. Tu l'hai riconosciuto. Anch'io, in qualche modo.")),
        ],
    },
    "marco": {
        "done": ("Dinner for forty, at last. Lyra came. She had seconds. She would like the recipe, and she would like you to stop calling her 'signora'.",
                 "La cena per quaranta, finalmente. Lyra è venuta. Ha fatto il bis. Vorrebbe la ricetta, e vorrebbe che smettessi di chiamarla 'signora'."),
        "quests": [
            (("The Echo Itself", "L'eco stessa"), ("The pressure that blew Marco out of his world has gathered in the Sanctum of Steam, north of the start. Let it out, gently.", "La pressione che ha sbalzato Marco fuori dal suo mondo si è raccolta nel Santuario del Vapore, a nord della partenza. Falla uscire, piano."),
             [(KILL, "echo_marco", 1)], {"xp": 6000, "gold": 8000, "items": {"royal_feast": 2}},
             ("The pot is gone and the Tyrant is gone, but not the pressure itself, the one that blew you here. It sits in a sanctum near the meadow, and it is rising.", "La pentola non c'è più e il Tiranno nemmeno, ma la pressione stessa sì, quella che ti ha sbalzato qui. Sta in un santuario vicino al prato, e sale."),
             ("The Sanctum of Steam, north of the start, a little east.", "Il Santuario del Vapore, a nord della partenza, un po' a est."),
             ("A whistle, a sigh, and the smell of the best ragù in two worlds. You have invited forty people to dinner. You have invited me. I accept.", "Un fischio, un sospiro, e il profumo del miglior ragù di due mondi. Hai invitato quaranta persone a cena. Hai invitato anche me. Accetto.")),
        ],
    },
    "yuki": {
        "done": ("The frame is empty, and you hung it in the shrine anyway, beside the three paintings. You said the empty one is the most valuable. I think I understood.",
                 "La cornice è vuota, e l'hai appesa nel santuario lo stesso, accanto ai tre quadri. Hai detto che quella vuota è la più preziosa. Credo di aver capito."),
        "quests": [
            (("The Echo Itself", "L'eco stessa"), ("The jump from the rooftop, the last frame of Yuki's old life, waits in the Sanctum of Frames, south of the start. Land.", "Il salto dal tetto, l'ultimo fotogramma della vecchia vita di Yuki, aspetta nel Santuario delle Cornici, a sud della partenza. Atterra."),
             [(KILL, "echo_yuki", 1)], {"xp": 6000, "gold": 10000, "items": {"potion_large": 5}},
             ("You never landed, Yuki. That is the last of it: the jump itself, still in the air, in a sanctum near the meadow. It is time to touch the ground.", "Non sei mai atterrata, Yuki. È l'ultima cosa: il salto stesso, ancora a mezz'aria, in un santuario vicino al prato. È ora di toccare terra."),
             ("The Sanctum of Frames, south of the start, a little east.", "Il Santuario delle Cornici, a sud della partenza, un po' a est."),
             ("You landed. Both feet. You stood very still for a while, the way people do when they have been falling for a long time.", "Sei atterrata. Con tutti e due i piedi. Sei rimasta immobile per un po', come chi è caduto per tanto tempo.")),
        ],
    },
    "lena": {
        "done": ("The report is signed. Cause of death: none, yet. You filed it under 'pending', and smiled. Lyra has asked to be your first patient. For a check-up, she insists.",
                 "Il referto è firmato. Causa di morte: nessuna, per ora. L'hai archiviato tra 'in sospeso', e hai sorriso. Lyra ha chiesto di essere la tua prima paziente. Per un controllo, insiste."),
        "quests": [
            (("The Echo Itself", "L'eco stessa"), ("The report on Lena's own death was never written. It has written itself, in the Sanctum of Silence, east of the start. Sign it.", "Il referto sulla morte di Lena non è mai stato scritto. Si è scritto da solo, nel Santuario del Silenzio, a est della partenza. Firmalo."),
             [(KILL, "echo_lena", 1)], {"xp": 6000, "gold": 8000, "items": {"potion_mana_medium": 5}},
             ("Every death you met has been closed but one: yours. Nobody wrote it down, so it wrote itself, and it is waiting in a sanctum near the meadow for your signature.", "Ogni morte che hai incontrato è stata chiusa tranne una: la tua. Nessuno l'ha messa per iscritto, così si è scritta da sola, e aspetta la tua firma in un santuario vicino al prato."),
             ("The Sanctum of Silence, east of the start, a little north.", "Il Santuario del Silenzio, a est della partenza, un po' a nord."),
             ("You signed it 'Lena Voss, alive'. The silence of the sanctum broke into birdsong. I do not think that was a coincidence.", "L'hai firmato 'Lena Voss, viva'. Il silenzio del santuario si è rotto in un canto d'uccelli. Non credo sia stato un caso.")),
        ],
    },
    "gideon": {
        "done": ("No throne anywhere, not even a shadow of one. You fix roofs in Fenwick and the children call you 'Mister Gideon'. Lyra has asked me to tell you that she is proud of you. I would like to add that I am too.",
                 "Nessun trono da nessuna parte, nemmeno l'ombra di uno. Aggiusti tetti a Fenwick e i bambini ti chiamano 'signor Gideon'. Lyra mi ha chiesto di dirti che è fiera di te. Vorrei aggiungere che lo sono anch'io."),
        "quests": [
            (("The Echo Itself", "L'eco stessa"), ("Three hundred years on a throne have left a shape behind: the throne itself, in the Sanctum of Ash, east of the start. Stand up from it.", "Trecento anni su un trono hanno lasciato una forma: il trono stesso, nel Santuario della Cenere, a est della partenza. Alzati."),
             [(KILL, "echo_gideon", 1)], {"xp": 6000, "gold": 8000, "items": {"potion_large": 5}},
             ("The kingdom is free and the generals are at rest. But the throne remembers your weight, Gideon, and it has come looking for you. It is in a sanctum near the meadow.", "Il regno è libero e i generali riposano. Ma il trono ricorda il tuo peso, Gideon, ed è venuto a cercarti. È in un santuario vicino al prato."),
             ("The Sanctum of Ash, east of the start, a little south.", "Il Santuario della Cenere, a est della partenza, un po' a sud."),
             ("It asked you to sit, one last time. You said you had a roof to fix in Fenwick. It crumbled at that. I think it had never been refused for a roof before.", "Ti ha chiesto di sederti, un'ultima volta. Hai detto che avevi un tetto da aggiustare a Fenwick. A quel punto si è sbriciolato. Credo che nessuno l'avesse mai rifiutato per un tetto.")),
        ],
    },
}
