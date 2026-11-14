#!/usr/bin/env python3
"""Adds the talk of the renown to the role dialogues of the settlement people (spec 07, "Renown").

The elder and the shopkeeper of a settlement greet as a friend somebody who has finished `KNOWN_AT` quests in the region, and the
innkeeper gives such a friend a bed for nothing from `FREE_BED_AT` quests. The dialogues of `data/base/dialogues/role/` are changed in
place (the nodes that are already there are written again, so the tool can be run any number of times) and the texts go to
`i18n/*/roles.json`. Run it after changing the tables here.
"""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

KNOWN_AT = 3
FREE_BED_AT = 5
TONES = ["warm", "mystic", "gruff", "flowery", "stoic", "salty", "grim", "scholarly"]
BED = {"en": "A bed for a friend of the town?", "it": "Un letto per un amico del paese?"}
KNOWN = {
    "en": {
        "warm": {"shopkeeper": "Oh, it's you! {place} talks about you, you know. For a friend the prices shrink a little. Don't tell the others.",
                 "elder": "There's our helper! {place} sleeps better since you came. Sit, sit. The porridge is nearly lump-free today.",
                 "innkeeper": "A bed for the one who helps {place}? On the house. The lumpy porridge too."},
        "mystic": {"shopkeeper": "The trees have spoken your name, and kindly. My shelves lean toward you; so do my prices.",
                   "elder": "The forest remembers what you did for {place}. It rarely remembers anything good. Be proud.",
                   "innkeeper": "Rest, friend of {place}. Tonight the branches will whisper only nice things. I asked them."},
        "gruff": {"shopkeeper": "You. You did good work round here. Prices are lower for you. Don't make it a thing.",
                  "elder": "{place} owes you. We don't say that often. We won't say it twice.",
                  "innkeeper": "Bed's free for you. You earned it. Still don't break anything."},
        "flowery": {"shopkeeper": "The hero of {place}! For you, my treasures are almost a gift, and this time I nearly mean it!",
                    "elder": "Ah, the name the caravans carry! {place} sings of you, slightly off key, with great feeling!",
                    "innkeeper": "For the friend of {place}: my coolest room, my sweetest tea, and no bill. I shall weep later, in private."},
        "stoic": {"shopkeeper": "You helped {place}. Lower prices. That is how we say thanks.",
                  "elder": "{place} knows your name. Here, that is a long speech.",
                  "innkeeper": "A bed. No coin. You are known here."},
        "salty": {"shopkeeper": "Well blow me down, the friend o' {place}! Crew's prices for ye, matey!",
                  "elder": "Har! The whole dock o' {place} drinks to yer name. Mostly they just drink, but still.",
                  "innkeeper": "A bunk for a shipmate o' {place}, no charge! The ale's still extra, I ain't mad."},
        "grim": {"shopkeeper": "You helped. Few do. {place} lowers its prices for you, while there are prices.",
                 "elder": "{place} still stands, and partly because of you. Enjoy it. Things rarely last.",
                 "innkeeper": "A bed, free. You kept the roof up one more night. Seems fair."},
        "scholarly": {"shopkeeper": "Ah, the person cited in three separate complaints that turned out to be compliments. A discount applies; see footnote.",
                      "elder": "Your contribution to {place} is, I am told, statistically significant. We are grateful, within error bars.",
                      "innkeeper": "Complimentary accommodation, for services rendered to {place}. The third stair sends its regards."},
    },
    "it": {
        "warm": {"shopkeeper": "Oh, sei tu! A {place} si parla di te, sai. Per un amico i prezzi si stringono un po'. Non dirlo agli altri.",
                 "elder": "Ecco chi ci aiuta! {place} dorme meglio da quando ci sei tu. Siediti, siediti. Oggi la polenta è quasi senza grumi.",
                 "innkeeper": "Un letto per chi aiuta {place}? Offre la casa. Anche la polenta grumosa."},
        "mystic": {"shopkeeper": "Gli alberi hanno detto il tuo nome, e con gentilezza. I miei scaffali si piegano verso di te; anche i miei prezzi.",
                   "elder": "La foresta ricorda ciò che hai fatto per {place}. Di rado ricorda qualcosa di buono. Vanne fiero.",
                   "innkeeper": "Riposa, amico di {place}. Stanotte i rami sussurreranno solo cose belle. Gliel'ho chiesto io."},
        "gruff": {"shopkeeper": "Tu. Hai lavorato bene da queste parti. Per te i prezzi sono più bassi. Non farne una storia.",
                  "elder": "{place} ti deve qualcosa. Non lo diciamo spesso. Non lo diremo due volte.",
                  "innkeeper": "Per te il letto è gratis. Te lo sei guadagnato. Non rompere niente lo stesso."},
        "flowery": {"shopkeeper": "L'eroe di {place}! Per te i miei tesori sono quasi un regalo, e stavolta lo penso quasi davvero!",
                    "elder": "Ah, il nome che portano le carovane! {place} canta di te, un po' stonata, con grande sentimento!",
                    "innkeeper": "Per l'amico di {place}: la stanza più fresca, il tè più dolce e nessun conto. Piangerò dopo, in privato."},
        "stoic": {"shopkeeper": "Hai aiutato {place}. Prezzi più bassi. È così che diciamo grazie.",
                  "elder": "{place} conosce il tuo nome. Qui, questo è un lungo discorso.",
                  "innkeeper": "Un letto. Niente monete. Qui sei conosciuto."},
        "salty": {"shopkeeper": "Che mi venga un colpo, l'amico di {place}! Prezzi da ciurma per te, mozzo!",
                  "elder": "Har! Tutto il molo di {place} beve al tuo nome. Più che altro beve e basta, ma comunque.",
                  "innkeeper": "Una cuccetta per un compagno di bordo di {place}, senza pagare! La birra si paga ancora, non sono matto."},
        "grim": {"shopkeeper": "Hai aiutato. Pochi lo fanno. {place} abbassa i prezzi per te, finché ci sono prezzi.",
                 "elder": "{place} è ancora in piedi, e un po' è merito tuo. Goditela. Le cose durano di rado.",
                 "innkeeper": "Un letto, gratis. Hai tenuto su il tetto per un'altra notte. Mi pare giusto."},
        "scholarly": {"shopkeeper": "Ah, la persona citata in tre diversi reclami che si sono rivelati complimenti. Si applica uno sconto; vedi nota.",
                      "elder": "Il tuo contributo a {place} è, mi dicono, statisticamente significativo. Siamo grati, entro il margine d'errore.",
                      "innkeeper": "Alloggio in omaggio, per i servizi resi a {place}. Il terzo gradino ti manda i suoi saluti."},
    },
}


def patch(role: str, tone: str) -> None:
    path = DATA / "dialogues" / "role" / f"{role}_{tone}.json"
    raw = path.read_text(encoding="utf-8", newline="")
    newline = "\r\n" if "\r\n" in raw else "\n"
    doc = json.loads(raw)
    nodes = doc["nodes"]
    known = f"$i18n:dlg.role.{role}.{tone}.known"
    if role == "innkeeper":  # a bed for nothing, for a friend of the region
        choice = {"text": "$i18n:dlg.role.friend_bed", "when": {"renown_at_least": FREE_BED_AT}, "next": "friend_bed"}
        choices = [c for c in nodes["menu"]["choices"] if c.get("next") != "friend_bed"]
        nodes["menu"]["choices"] = [choice, *choices]
        nodes["friend_bed"] = {"type": "effects", "effects": [{"effect": "heal_full"}], "next": "friend_rested"}
        nodes["friend_rested"] = {"type": "say", "speaker": "npc", "text": known, "next": "end"}
    else:  # somebody known is greeted as a friend
        if nodes["start"]["type"] == "say":
            nodes["hello"] = nodes["start"]
        nodes["start"] = {"type": "condition", "when": {"renown_at_least": KNOWN_AT}, "then": "known", "else": "hello"}
        nodes["known"] = {"type": "say", "speaker": "npc", "text": known, "next": nodes["hello"]["next"]}
    path.write_text((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").replace("\n", newline), encoding="utf-8", newline="")


def main() -> None:
    for tone in TONES:
        for role in ("shopkeeper", "elder", "innkeeper"):
            patch(role, tone)
    for lang in ("en", "it"):
        texts = {f"dlg.role.{role}.{tone}.known": line for tone in TONES for role, line in KNOWN[lang][tone].items()}
        texts["dlg.role.friend_bed"] = BED[lang]
        set_texts("roles.json", lang, texts)
    print(f"patched {3 * len(TONES)} role dialogues")


if __name__ == "__main__":
    main()
