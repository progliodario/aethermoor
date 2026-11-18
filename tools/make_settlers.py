#!/usr/bin/env python3
"""Writes the settlers of the generated villages (spec 07, "Residents"; spec 09, "Settlement people").

Every village stamp has a slot of the role `settler`, its last one; the world data says `"role_when": {"settler": {"renown_at_least": 8}}`,
so the settler of a village is there only once the Guest has finished eight quests in its region (and is never solid). A settler came
because the roads became safe: it greets the Guest in the voice of the region, shares its soup (a rest: `heal_full`) and tells why it came.

It writes the role dialogues `data/base/dialogues/role/settler_<tone>.json` and their texts (`roles.json`, it and en). It can be run any
number of times. The stamps and the world data are written by `make_stamps.py` and by hand.
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
SHARED = {
    "en": {"dlg.role.settler.why": "Why did you come here?", "dlg.role.settler.soup": "Something warm?", "dlg.role.settler.bye": "Welcome to the village."},
    "it": {"dlg.role.settler.why": "Perché sei venuto qui?", "dlg.role.settler.soup": "Qualcosa di caldo?", "dlg.role.settler.bye": "Benvenuto al villaggio."},
}


def dialogue(tone: str) -> dict:
    key = f"dlg.role.settler.{tone}"
    return {"$schema": "../../../../schemas/dialogue.schema.json", "id": f"base:dialogue/role/settler_{tone}", "start": "start", "nodes": {
        "start": {"type": "say", "speaker": "npc", "text": f"$i18n:{key}.hello", "next": "menu"},
        "menu": {"type": "choice", "choices": [
            {"text": "$i18n:dlg.role.settler.why", "next": "why"},
            {"text": "$i18n:dlg.role.settler.soup", "next": "rest"},
            {"text": "$i18n:dlg.role.settler.bye", "next": "end"}]},
        "why": {"type": "say", "speaker": "npc", "text": f"$i18n:{key}.why", "next": "menu"},
        "rest": {"type": "effects", "effects": [{"effect": "heal_full"}], "next": "soup"},
        "soup": {"type": "say", "speaker": "npc", "text": f"$i18n:{key}.soup", "next": "end"},
    }}


def main() -> None:
    texts = {lang: dict(SHARED[lang]) for lang in ("en", "it")}
    for tone, words in WORDS.items():
        doc = dialogue(tone)
        text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
        (DATA / "dialogues" / "role" / f"settler_{tone}.json").write_text(text, encoding="utf-8", newline="\n")
        for lang in ("en", "it"):
            hello, why, soup = words[lang]
            texts[lang].update({f"dlg.role.settler.{tone}.hello": hello, f"dlg.role.settler.{tone}.why": why,
                                f"dlg.role.settler.{tone}.soup": soup})
    for lang in ("en", "it"):
        set_texts("roles.json", lang, texts[lang])
    print(f"wrote the settlers of {len(WORDS)} regions")


if __name__ == "__main__":
    main()
