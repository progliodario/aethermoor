#!/usr/bin/env python3
"""Writes the settlers of the generated villages (spec 07, "Residents", "Settlers"; spec 09, "Settlement people").

Every village stamp has a slot of the role `settler`, its last one; the world data says `"role_when": {"settler": {"renown_at_least": 8}}`,
so the settler of a village is there only once the Guest has finished eight quests in its region (and is never solid). A settler came
because the roads became safe: it greets the Guest in the voice of the region, shares its soup (a rest: `heal_full`) and tells why it came.

Every settler also has a **trade** (the baker of Verdalis, the tea-brewer of Whisperwood, the stonemason of Ironspine...) and a quest of
it, `base:quest/side/settle_<region>`: two things of the region to gather so that its workshop can open, paid with experience, gold and
what the trade makes. Once the quest is done the settler thanks the Guest once (the flag `settle_<region>_thanked`) and then opens its
workshop: the goods of the region at a friend's price (`open_shop` with the `region` and `markup_pct` 90, spec 06, "Goods from afar").
The quest is `repeatable` (spec 07, "Quests"): a workshop always needs more, and once thanked the settler asks for the same things again,
paid each time.

It writes the role dialogues `data/base/dialogues/role/settler_<tone>.json`, the quests and their texts (`roles.json` and `content.json`,
it and en). It can be run any number of times. The stamps and the world data are written by `make_stamps.py` and by hand. Then run
`make_catalog.py` and `make_facts.py`.
"""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

# tone: (hello, why, soup) in en and it; {npc} and {place} are the arguments of the settlement people (spec 07)
WORDS = {
    "warm": {"en": ("Oh! You're the Guest. I'm {npc}, new in {place}. We moved here the week the roads got safe, and we have you to thank.",
                    "Our old village was in a valley the slimes loved. When we heard the Guest had cleared the roads, we packed the cart that very night.",
                    "Sit, sit! There's always soup. There. Better?"),
             "it": ("Oh! Sei l'Ospite. Sono {npc}, nuova di {place}. Ci siamo trasferiti la settimana in cui le strade sono diventate sicure, e dobbiamo ringraziare te.",
                    "Il nostro vecchio villaggio era in una valle amata dalle gelatine. Quando abbiamo saputo che l'Ospite aveva ripulito le strade, abbiamo caricato il carro quella notte stessa.",
                    "Siediti, siediti! La zuppa c'è sempre. Ecco. Va meglio?")},
    "mystic": {"en": ("The leaves said a stranger would come and bring the paths back. I am {npc}; I followed them to {place}.",
                      "The deep wood was too dark to live in. Then a light walked through it, and the dark stepped aside. I came after the light.",
                      "Drink. It is moss tea; it remembers what you were before you were tired."),
               "it": ("Le foglie dicevano che sarebbe arrivato uno straniero a riportare i sentieri. Sono {npc}; le ho seguite fino a {place}.",
                      "Il bosco profondo era troppo buio per viverci. Poi una luce lo ha attraversato, e il buio si è fatto da parte. Io sono venuta dietro alla luce.",
                      "Bevi. È tè di muschio; ricorda chi eri prima di essere stanco.")},
    "gruff": {"en": ("{npc}. New in {place}. Came when the passes opened. You opened them. Good.",
                     "The mine back home caved in. Here there's stone, work and no golems in the way. Thanks to you.",
                     "Stew. Eat. Don't talk."),
              "it": ("{npc}. Nuovo di {place}. Venuto quando i passi si sono aperti. Li hai aperti tu. Bene.",
                     "La miniera a casa è crollata. Qui c'è pietra, lavoro e niente golem tra i piedi. Grazie a te.",
                     "Stufato. Mangia. Non parlare.")},
    "flowery": {"en": ("Welcome, welcome, O sweeper of the dunes! I am {npc}, the newest flower of {place}, planted here by the peace you sowed!",
                       "My caravan lost its way in a sandstorm of scorpions. Then word came of a Guest, and the desert grew kind. We stopped, and we bloomed.",
                       "Taste this, a broth of seven spices and one secret. Your weariness will flee like a thief at dawn!"),
                "it": ("Benvenuto, benvenuto, o spazzino delle dune! Sono {npc}, il fiore più nuovo di {place}, piantato qui dalla pace che hai seminato!",
                       "La mia carovana si era persa in una tempesta di scorpioni. Poi è arrivata la voce di un Ospite, e il deserto si è fatto gentile. Ci siamo fermati, e siamo fioriti.",
                       "Assaggia questo, un brodo di sette spezie e un segreto. La tua stanchezza fuggirà come un ladro all'alba!")},
    "stoic": {"en": ("I am {npc}. I live in {place} now. The ice is quiet; you made it so.",
                     "Where I lived, the wolves came every winter. Here they do not. That is enough reason.",
                     "Sit by the fire. Say nothing. It helps."),
              "it": ("Sono {npc}. Ora vivo a {place}. Il ghiaccio è tranquillo; l'hai reso tu così.",
                     "Dove vivevo, i lupi arrivavano ogni inverno. Qui no. È ragione sufficiente.",
                     "Siediti accanto al fuoco. Non dire niente. Aiuta.")},
    "salty": {"en": ("Ahoy! {npc}'s the name, fresh off the boat to {place}. The crabs behave now; word is that's your doing.",
                     "Our harbour went to the crabs, literally. When the coast got safe I sold the boat and bought a house. Best trade I ever made.",
                     "Chowder, mate. Fish, salt and a splash of the good stuff. Back on your feet?"),
              "it": ("Ahoy! Mi chiamo {npc}, appena sbarcato a {place}. I granchi ora si comportano bene; dicono che sia merito tuo.",
                     "Il nostro porto era finito ai granchi, letteralmente. Quando la costa è diventata sicura ho venduto la barca e comprato una casa. Il miglior affare della mia vita.",
                     "Zuppa di pesce, amico. Pesce, sale e una spruzzata di quello buono. Di nuovo in piedi?")},
    "grim": {"en": ("{npc}. I came to {place} to live, which out here is a new idea. You made it possible.",
                    "Everything I had burned. Twice. Now the fires keep to themselves, and so can I.",
                    "Ash bread and hot water. It is not much. It is warm."),
             "it": ("{npc}. Sono venuta a {place} per vivere, che qui fuori è un'idea nuova. L'hai resa possibile tu.",
                    "Tutto quello che avevo è bruciato. Due volte. Ora i fuochi stanno per conto loro, e posso farlo anch'io.",
                    "Pane di cenere e acqua calda. Non è molto. È caldo.")},
    "scholarly": {"en": ("Greetings. I am {npc}, recently relocated to {place}, a decision supported by the data: since your arrival the attacks are down to nearly none.",
                         "My research needed a quiet sky. The sky here is quiet now. Correlation is not causation, they say; I say, thank you.",
                         "A restorative infusion, brewed at a measured temperature. Drink it all; the dose matters."),
                  "it": ("Saluti. Sono {npc}, da poco trasferita a {place}, una decisione sostenuta dai dati: dal tuo arrivo gli attacchi sono scesi quasi a zero.",
                         "La mia ricerca aveva bisogno di un cielo tranquillo. Ora il cielo qui è tranquillo. Correlazione non è causalità, dicono; io dico grazie.",
                         "Un'infusione ricostituente, preparata a temperatura misurata. Bevila tutta; la dose conta.")},
}

# The trades (spec 07, "Settlers"): tone -> (region, danger, [(item, count), (item, count)], (reward item, qty))
TRADES = {
    "warm": ("verdalis", 1, [("wood_log", 10), ("wild_berries", 6)], ("berry_pancakes", 4)),
    "mystic": ("whisperwood", 3, [("moss_clump", 6), ("fern_frond", 4)], ("moonlit_tea", 2)),
    "gruff": ("ironspine", 4, [("stone_chunk", 10), ("iron_ore", 4)], ("miners_broth", 2)),
    "flowery": ("sunscar", 4, [("cactus_pulp", 6), ("dry_branch", 6)], ("sunfire_skewers", 2)),
    "stoic": ("frostveil", 5, [("ice_crystal", 5), ("wood_log", 8)], ("fish_stew", 3)),
    "salty": ("tidehaven", 3, [("driftwood", 6), ("sea_shell", 6)], ("captains_chowder", 2)),
    "grim": ("ashen_wastes", 7, [("dry_branch", 10), ("stone_chunk", 6)], ("ember_chili", 2)),
    "scholarly": ("lumeria", 5, [("star_dust", 4), ("ice_crystal", 4)], ("starlight_elixir", 1)),
}
MARKUP_PCT = 90  # the workshop of a settler sells the goods of its region at a friend's price

# tone: (trade, offer, busy, thanks, workshop, quest name, journal) in en and it
TRADE_WORDS = {
    "en": {
        "warm": ("I'm a baker! Well, I will be, once the oven is fired. A village without bread is just houses.",
                 "Could you bring me ten logs for the oven and six handfuls of wild berries? The first pancakes are yours, I promise.",
                 "Ten logs and six handfuls of berries, dear. The oven is cold and so are my hands.",
                 "The oven sings! Here, the first pancakes, hot. Come back whenever you like: there's always something rising.",
                 "Fresh from the oven, and from all over Verdalis. For you, a friend's price.",
                 "The Village Oven", "The new baker of a village of Verdalis needs logs for the oven and wild berries for the first pancakes."),
        "mystic": ("I brew teas. Each leaf has a memory; I only help it speak.",
                   "Six clumps of moss from the old stumps and four fern fronds from the shade. Then the kettle can begin to remember.",
                   "The moss and the ferns are still where the wood keeps them.",
                   "The kettle remembers. Drink this when the night is long. And my door is open to you.",
                   "The wood gives, and I pass it on. Take what you need; the price is a friend's.",
                   "Leaves That Remember", "The tea-brewer of a village of Whisperwood needs moss clumps and fern fronds to begin."),
        "gruff": ("Stonemason. Walls, wells, steps. Things that stay.",
                  "Ten chunks of stone. Four of iron ore for the tools. Bring them.",
                  "Stone. Ore. Still waiting.",
                  "Good stone. The well gets a wall. Here. Eat.",
                  "Tools, ore, the good stuff of Ironspine. Cheaper for you.",
                  "Stones That Stay", "The stonemason of a village of Ironspine needs stone chunks and iron ore for the first wall."),
        "flowery": ("I sell spices, O Guest, spices that make a soup sing and a heart dance!",
                    "To grind them I need six cactus pulps, juicy as gossip, and six dry branches for the drying fire!",
                    "The cactus and the branches still wait in the dunes, like lovers at a window!",
                    "My stall is open, and the air smells of paradise! Taste these skewers, and come back to me always!",
                    "All the treasures of Sunscar, and for you, darling, a price like a kiss!",
                    "Seven Spices", "The spice seller of a village of Sunscar needs cactus pulp and dry branches to open the stall."),
        "stoic": ("I fish through the ice. The lake is generous to the patient.",
                  "Five ice crystals to mend the drill. Eight logs for the hut on the ice.",
                  "The crystals. The logs. Then the lake.",
                  "The hut stands on the ice. The fish came. This is yours.",
                  "What the north has, I sell. Less, for you.",
                  "A Hut on the Ice", "The ice fisher of a village of Frostveil needs ice crystals for the drill and logs for the hut."),
        "salty": ("I mend nets, mate. Thirty years at sea taught me one knot, and I tie it well.",
                  "Six pieces of driftwood for the floats and six sea shells for the weights. Then we fish!",
                  "Driftwood and shells, mate. The beach is full of 'em.",
                  "The nets are whole and the boats are out! A pot of chowder, on the house.",
                  "Everything from the docks of Tidehaven, at a sailor's price for a friend.",
                  "Floats and Weights", "The net-mender of a village of Tidehaven needs driftwood and sea shells for the nets."),
        "grim": ("I burn charcoal. Out here, fire you can carry is worth more than gold.",
                 "Ten dry branches and six chunks of stone for the kiln. Then the village has warmth that does not run.",
                 "The kiln is still cold. Branches. Stone.",
                 "The kiln burns low and steady, as it should. Take this. It is hot, like everything here.",
                 "What the Wastes give, I give on. Less than it costs. You earned that.",
                 "Fire You Can Carry", "The charcoal burner of a village of the Ashen Wastes needs dry branches and stone for the kiln."),
        "scholarly": ("I grind lenses. Telescopes, spectacles; a clearer view of things, in every sense.",
                      "Four measures of star dust for the polish and four ice crystals for the cooling bath. Precision requires both.",
                      "The star dust and the crystals remain, regrettably, absent.",
                      "A lens of perfect curvature. The village can see the stars now. Please accept this elixir, distilled under them.",
                      "Instruments and supplies of Lumeria, at a discount supported by gratitude.",
                      "A Clearer View", "The lens grinder of a village of Lumeria needs star dust and ice crystals for the first lens."),
    },
    "it": {
        "warm": ("Sono una fornaia! Cioè, lo sarò, appena il forno sarà acceso. Un villaggio senza pane è solo un mucchio di case.",
                 "Mi porteresti dieci ceppi per il forno e sei manciate di bacche selvatiche? Le prime frittelle sono tue, promesso.",
                 "Dieci ceppi e sei manciate di bacche, caro. Il forno è freddo e anche le mie mani.",
                 "Il forno canta! Ecco le prime frittelle, calde. Torna quando vuoi: c'è sempre qualcosa che lievita.",
                 "Appena sfornato, e da tutta Verdalis. Per te, un prezzo da amico.",
                 "Il forno del villaggio", "La nuova fornaia di un villaggio di Verdalis ha bisogno di ceppi per il forno e di bacche selvatiche per le prime frittelle."),
        "mystic": ("Preparo tè. Ogni foglia ha un ricordo; io la aiuto solo a parlare.",
                   "Sei zolle di muschio dai vecchi ceppi e quattro fronde di felce dall'ombra. Poi il bollitore potrà cominciare a ricordare.",
                   "Il muschio e le felci sono ancora dove il bosco li custodisce.",
                   "Il bollitore ricorda. Bevi questo quando la notte è lunga. E la mia porta è aperta per te.",
                   "Il bosco dà, e io passo oltre. Prendi ciò che ti serve; il prezzo è da amico.",
                   "Foglie che ricordano", "La preparatrice di tè di un villaggio di Whisperwood ha bisogno di zolle di muschio e fronde di felce per cominciare."),
        "gruff": ("Scalpellino. Muri, pozzi, scale. Cose che restano.",
                  "Dieci pezzi di pietra. Quattro di minerale di ferro per gli attrezzi. Portali.",
                  "Pietra. Minerale. Aspetto ancora.",
                  "Buona pietra. Il pozzo avrà un muro. Ecco. Mangia.",
                  "Attrezzi, minerale, la roba buona di Ironspine. Per te costa meno.",
                  "Pietre che restano", "Lo scalpellino di un villaggio di Ironspine ha bisogno di pezzi di pietra e minerale di ferro per il primo muro."),
        "flowery": ("Vendo spezie, o Ospite, spezie che fanno cantare una zuppa e danzare un cuore!",
                    "Per macinarle mi servono sei polpe di cactus, succose come un pettegolezzo, e sei rami secchi per il fuoco che le asciuga!",
                    "Il cactus e i rami aspettano ancora tra le dune, come innamorati alla finestra!",
                    "La mia bancarella è aperta, e l'aria profuma di paradiso! Assaggia questi spiedini, e torna da me sempre!",
                    "Tutti i tesori di Sunscar, e per te, tesoro, un prezzo come un bacio!",
                    "Sette spezie", "La venditrice di spezie di un villaggio di Sunscar ha bisogno di polpa di cactus e rami secchi per aprire la bancarella."),
        "stoic": ("Pesco sotto il ghiaccio. Il lago è generoso con chi ha pazienza.",
                  "Cinque cristalli di ghiaccio per aggiustare il trapano. Otto ceppi per la capanna sul ghiaccio.",
                  "I cristalli. I ceppi. Poi il lago.",
                  "La capanna sta sul ghiaccio. I pesci sono venuti. Questo è tuo.",
                  "Quello che ha il nord, lo vendo. Meno, per te.",
                  "Una capanna sul ghiaccio", "Il pescatore del ghiaccio di un villaggio di Frostveil ha bisogno di cristalli di ghiaccio per il trapano e di ceppi per la capanna."),
        "salty": ("Rammendo reti, amico. Trent'anni di mare mi hanno insegnato un nodo solo, e lo faccio bene.",
                  "Sei pezzi di legno di mare per i galleggianti e sei conchiglie per i pesi. Poi si pesca!",
                  "Legno di mare e conchiglie, amico. La spiaggia ne è piena.",
                  "Le reti sono intere e le barche sono fuori! Una pentola di zuppa, offre la casa.",
                  "Tutto dai moli di Tidehaven, a un prezzo da marinaio per un amico.",
                  "Galleggianti e pesi", "Il rammendatore di reti di un villaggio di Tidehaven ha bisogno di legno di mare e conchiglie per le reti."),
        "grim": ("Faccio carbone. Qui fuori, un fuoco che si può portare vale più dell'oro.",
                 "Dieci rami secchi e sei pezzi di pietra per la carbonaia. Poi il villaggio avrà un calore che non scappa.",
                 "La carbonaia è ancora fredda. Rami. Pietra.",
                 "La carbonaia brucia bassa e costante, come deve. Prendi questo. È caldo, come tutto qui.",
                 "Quello che danno le Terre di Cenere, lo do oltre. Meno di quanto costa. Te lo sei guadagnato.",
                 "Un fuoco da portare", "La carbonaia di un villaggio delle Terre di Cenere ha bisogno di rami secchi e pietra per la carbonaia."),
        "scholarly": ("Molo lenti. Telescopi, occhiali; una visione più chiara delle cose, in ogni senso.",
                      "Quattro misure di polvere di stelle per la lucidatura e quattro cristalli di ghiaccio per il bagno di raffreddamento. La precisione richiede entrambi.",
                      "La polvere di stelle e i cristalli restano, purtroppo, assenti.",
                      "Una lente di curvatura perfetta. Ora il villaggio può vedere le stelle. Accetta questo elisir, distillato sotto di loro.",
                      "Strumenti e provviste di Lumeria, con uno sconto sostenuto dalla gratitudine.",
                      "Una visione più chiara", "La molatrice di lenti di un villaggio di Lumeria ha bisogno di polvere di stelle e cristalli di ghiaccio per la prima lente."),
    },
}
SHARED = {
    "en": {"dlg.role.settler.again": "Does the workshop need more?", "dlg.role.settler.why": "Why did you come here?", "dlg.role.settler.soup": "Something warm?", "dlg.role.settler.bye": "Welcome to the village.",
           "dlg.role.settler.trade": "What do you do here?", "dlg.role.settler.accept": "I'll bring them.", "dlg.role.settler.later": "Not now."},
    "it": {"dlg.role.settler.again": "Alla bottega serve altro?", "dlg.role.settler.why": "Perché sei venuto qui?", "dlg.role.settler.soup": "Qualcosa di caldo?", "dlg.role.settler.bye": "Benvenuto al villaggio.",
           "dlg.role.settler.trade": "Che cosa fai qui?", "dlg.role.settler.accept": "Te li porto io.", "dlg.role.settler.later": "Non ora."},
}


def quest_id(region: str) -> str:
    return f"base:quest/side/settle_{region}"


def quest(tone: str) -> dict:
    region, danger, needs, (gift, qty) = TRADES[tone]
    return {"$schema": "../../../../schemas/quest.schema.json", "id": quest_id(region), "name": f"$i18n:quest.settle_{region}.name",
            "kind": "side", "faction": "folk", "repeatable": True,
            "stages": [{"id": "gather", "journal": f"$i18n:quest.settle_{region}.task",
                        "objectives": [{"type": "collect", "item": f"base:item/{item}", "count": count} for item, count in needs], "next": "end"}],
            "rewards": [{"effect": "add_xp", "amount": 100 + 40 * danger}, {"effect": "add_gold", "amount": 120 + 60 * danger},
                        {"effect": "add_item", "item": f"base:item/{gift}", "qty": qty}]}


def dialogue(tone: str) -> dict:
    key = f"dlg.role.settler.{tone}"
    region = TRADES[tone][0]
    q = quest_id(region)
    thanked = f"settle_{region}_thanked"
    return {"$schema": "../../../../schemas/dialogue.schema.json", "id": f"base:dialogue/role/settler_{tone}", "start": "start", "nodes": {
        "start": {"type": "say", "speaker": "npc", "text": f"$i18n:{key}.hello", "next": "menu"},
        "menu": {"type": "choice", "choices": [
            {"text": "$i18n:dlg.role.settler.trade", "next": "trade"},
            {"text": "$i18n:dlg.role.settler.again", "when": {"all": [{"quest_done": q}, {"flag": thanked}]}, "next": "offer"},
            {"text": "$i18n:dlg.role.settler.why", "next": "why"},
            {"text": "$i18n:dlg.role.settler.soup", "next": "rest"},
            {"text": "$i18n:dlg.role.settler.bye", "next": "end"}]},
        "why": {"type": "say", "speaker": "npc", "text": f"$i18n:{key}.why", "next": "menu"},
        "rest": {"type": "effects", "effects": [{"effect": "heal_full"}], "next": "soup"},
        "soup": {"type": "say", "speaker": "npc", "text": f"$i18n:{key}.soup", "next": "end"},
        # the trade (spec 07, "Settlers"): the quest that opens the workshop, then the thanks once, then the workshop
        "trade": {"type": "condition", "when": {"quest_done": q}, "then": "done", "else": "trade_say"},
        "trade_say": {"type": "say", "speaker": "npc", "text": f"$i18n:{key}.trade", "next": "asked"},
        "asked": {"type": "condition", "when": {"quest_active": q}, "then": "busy", "else": "offer"},
        "offer": {"type": "say", "speaker": "npc", "text": f"$i18n:{key}.offer", "next": "offer_choice"},
        "offer_choice": {"type": "choice", "choices": [
            {"text": "$i18n:dlg.role.settler.accept", "effects": [{"effect": "start_quest", "quest": q}], "next": "end"},
            {"text": "$i18n:dlg.role.settler.later", "next": "menu"}]},
        "busy": {"type": "say", "speaker": "npc", "text": f"$i18n:{key}.busy", "next": "end"},
        "done": {"type": "condition", "when": {"flag": thanked}, "then": "workshop", "else": "thanks"},
        "thanks": {"type": "say", "speaker": "npc", "text": f"$i18n:{key}.thanks", "next": "thanked"},
        "thanked": {"type": "effects", "effects": [{"effect": "set_flag", "flag": thanked, "value": True}], "next": "workshop"},
        "workshop": {"type": "say", "speaker": "npc", "text": f"$i18n:{key}.workshop", "next": "shop"},
        "shop": {"type": "effects", "effects": [{"effect": "open_shop", "region": region, "markup_pct": MARKUP_PCT}], "next": "end"},
    }}


def write_json(path, doc) -> None:
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    texts = {lang: dict(SHARED[lang]) for lang in ("en", "it")}
    content: dict[str, dict[str, str]] = {"en": {}, "it": {}}
    for tone, words in WORDS.items():
        region = TRADES[tone][0]
        write_json(DATA / "dialogues" / "role" / f"settler_{tone}.json", dialogue(tone))
        write_json(DATA / "quests" / "side" / f"settle_{region}.json", quest(tone))
        for lang in ("en", "it"):
            hello, why, soup = words[lang]
            trade, offer, busy, thanks, workshop, name, journal = TRADE_WORDS[lang][tone]
            texts[lang].update({f"dlg.role.settler.{tone}.hello": hello, f"dlg.role.settler.{tone}.why": why,
                                f"dlg.role.settler.{tone}.soup": soup, f"dlg.role.settler.{tone}.trade": trade,
                                f"dlg.role.settler.{tone}.offer": offer, f"dlg.role.settler.{tone}.busy": busy,
                                f"dlg.role.settler.{tone}.thanks": thanks, f"dlg.role.settler.{tone}.workshop": workshop})
            content[lang].update({f"quest.settle_{region}.name": name, f"quest.settle_{region}.task": journal})
    for lang in ("en", "it"):
        set_texts("roles.json", lang, texts[lang])
        set_texts("content.json", lang, content[lang])
    print(f"wrote the settlers of {len(WORDS)} regions, with their trades and quests")


if __name__ == "__main__":
    main()
