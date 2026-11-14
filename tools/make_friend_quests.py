#!/usr/bin/env python3
"""Writes what a region keeps for its friends (spec 07, "Renown") and the goods from afar (spec 06, "Goods from afar").

- **A task for a friend**: the elder of every settlement offers one more quest to somebody with `FRIEND_AT` quests finished in the region:
  a hunt of a strong creature of the region, paid well. The quest files are `data/base/quests/side/friend_<region>.json`.
- **Goods from afar**: the shopkeeper of every settlement also sells what the caravan brought from the next region of the ring of the
  wayfarers (spec 07, "Wayfarers"), at `MARKUP_PCT` percent of the prices of that region.

The role dialogues of `data/base/dialogues/role/` are changed in place (the nodes written here are written again, so the tool can be run any
number of times); the texts go to `i18n/*/roles.json` and `i18n/*/content.json`. Run it after changing the tables here, then
`make_catalog.py`.
"""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

FRIEND_AT = 8
MARKUP_PCT = 125
# region: (tone of its people, the creature to hunt, how many, danger of the region, the next region of the ring)
REGIONS = {
    "verdalis": ("warm", "wolf_tawny", 6, 1, "ironspine"),
    "whisperwood": ("mystic", "wolf_dire", 6, 3, "verdalis"),
    "ironspine": ("gruff", "stone_golem", 4, 4, "ashen_wastes"),
    "sunscar": ("flowery", "dune_scorpion", 6, 4, "lumeria"),
    "frostveil": ("stoic", "wolf_polar", 6, 5, "whisperwood"),
    "tidehaven": ("salty", "slime_pearl", 6, 3, "frostveil"),
    "ashen_wastes": ("grim", "wolf_ember", 6, 7, "sunscar"),
    "lumeria": ("scholarly", "wolf_storm", 6, 5, "tidehaven"),
}
SHARED = {
    "en": {"dlg.role.friend.ask": "Is there something only a friend could do?", "dlg.role.friend.status": "About that task for a friend...",
           "dlg.role.friend.report": "The task for a friend is done.", "dlg.role.caravan": "What did the caravan bring?"},
    "it": {"dlg.role.friend.ask": "C'è qualcosa che solo un amico potrebbe fare?", "dlg.role.friend.status": "A proposito di quel compito da amico...",
           "dlg.role.friend.report": "Il compito da amico è fatto.", "dlg.role.caravan": "Che cosa ha portato la carovana?"},
}
# tone: (offer, busy, thanks, quest name, journal)
TALK = {
    "en": {
        "warm": ("You've done so much for us that I dare ask one thing more. The tawny wolves have come down to the sheepfolds. Six of them, and the lambs sleep again.",
                 "The wolves still howl at night. No hurry, dear. Eat something first.",
                 "Not a howl since yesterday! The whole village baked for you. And this is from the common chest.",
                 "A friend of the fold", "Hunt the tawny wolves that come down to the sheepfolds of Verdalis."),
        "mystic": ("The forest trusts you now, so I may say it aloud: the dire wolves walk where the old stones sleep. Six must go, or the stones will wake.",
                   "The stones still stir. The wolves are not gone.",
                   "The stones sleep. The forest will not thank you, so I do, with this.",
                   "What walks among the stones", "Hunt the dire wolves that walk among the old stones of Whisperwood."),
        "gruff": ("You. You're one of us now, near enough. Stone golems in the upper galleries. Four. Break them.",
                  "Golems are still up there. I can hear them.",
                  "Quiet galleries. Good work. Take it. Don't make a speech.",
                  "The upper galleries", "Break the stone golems that have taken the upper galleries of Ironspine."),
        "flowery": ("Dearest friend of the sands! The dune scorpions have taken the caravan road, and my cousin's camels refuse to walk! Six stings fewer, I beg you!",
                    "The camels still refuse. They are sensitive creatures. So am I.",
                    "The road is open and the camels are singing! Well, groaning. Take this, with a hundred blessings and a receipt!",
                    "The road of the camels", "Hunt the dune scorpions that hold the caravan road of Sunscar."),
        "stoic": ("You are known here. So: polar wolves at the ice holes. Six. The fishers cannot work.",
                  "The wolves are still at the ice.",
                  "The fishers work again. This is yours.",
                  "The ice holes", "Hunt the polar wolves that keep the fishers of Frostveil from the ice holes."),
        "salty": ("Ahoy, shipmate o' ours! Pearl slimes be cloggin' the slipway, and no hull can touch water. Scrape off six, an' the yard's yours to command!",
                  "Slipway's still slippery in the wrong way, matey.",
                  "She launched this mornin', smooth as rum! Here's yer share, an' ye earned every coin.",
                  "The clogged slipway", "Clear the pearl slimes from the slipway of Tidehaven."),
        "grim": ("You have stayed longer than most, so I ask. Cinder wolves circle the last well. Six fewer, and we drink another season.",
                 "The wolves still circle. The well still stands. For now.",
                 "We drink another season. Take this. It is more than we can spare, which is why it is yours.",
                 "The last well", "Hunt the cinder wolves that circle the last well of the Ashen Wastes."),
        "scholarly": ("As a recognised associate of this community, you may be told: storm wolves are disturbing the observatory. Six, if you would. The readings are ruined.",
                      "The readings remain ruined. The wolves, regrettably, remain.",
                      "A clean reading at last! Your name goes in the acknowledgements, and this goes in your pocket.",
                      "Interference at the observatory", "Hunt the storm wolves that disturb the observatory of Lumeria."),
    },
    "it": {
        "warm": ("Hai fatto così tanto per noi che oso chiederti ancora una cosa. I lupi fulvi sono scesi fino agli ovili. Sei di loro, e gli agnelli tornano a dormire.",
                 "I lupi ululano ancora di notte. Senza fretta, caro. Prima mangia qualcosa.",
                 "Da ieri neanche un ululato! Tutto il villaggio ha sfornato per te. E questo viene dalla cassa comune.",
                 "Un amico dell'ovile", "Caccia i lupi fulvi che scendono agli ovili di Verdalis."),
        "mystic": ("Ora la foresta si fida di te, quindi posso dirlo ad alta voce: i lupi atroci camminano dove dormono le antiche pietre. Sei devono andarsene, o le pietre si sveglieranno.",
                   "Le pietre si agitano ancora. I lupi non se ne sono andati.",
                   "Le pietre dormono. La foresta non ti ringrazierà, quindi lo faccio io, con questo.",
                   "Ciò che cammina tra le pietre", "Caccia i lupi atroci che camminano tra le antiche pietre del Bosco dei Sussurri."),
        "gruff": ("Tu. Ormai sei dei nostri, o quasi. Golem di pietra nelle gallerie alte. Quattro. Spaccali.",
                  "I golem sono ancora lassù. Li sento.",
                  "Gallerie silenziose. Buon lavoro. Prendi. Niente discorsi.",
                  "Le gallerie alte", "Spacca i golem di pietra che hanno preso le gallerie alte della Dorsale di Ferro."),
        "flowery": ("Carissimo amico delle sabbie! Gli scorpioni delle dune hanno preso la via delle carovane, e i cammelli di mio cugino si rifiutano di camminare! Sei pungiglioni in meno, ti supplico!",
                    "I cammelli si rifiutano ancora. Sono creature sensibili. Anch'io.",
                    "La via è aperta e i cammelli cantano! Be', brontolano. Prendi questo, con cento benedizioni e una ricevuta!",
                    "La via dei cammelli", "Caccia gli scorpioni delle dune che tengono la via delle carovane della Cicatrice del Sole."),
        "stoic": ("Qui sei conosciuto. Dunque: lupi polari ai buchi nel ghiaccio. Sei. I pescatori non possono lavorare.",
                  "I lupi sono ancora sul ghiaccio.",
                  "I pescatori lavorano di nuovo. Questo è tuo.",
                  "I buchi nel ghiaccio", "Caccia i lupi polari che tengono i pescatori del Velo di Gelo lontani dai buchi nel ghiaccio."),
        "salty": ("Ohé, compagno di bordo! Le melme di perla intasano lo scalo, e nessuno scafo tocca l'acqua. Grattane via sei, e il cantiere è ai tuoi ordini!",
                  "Lo scalo scivola ancora dalla parte sbagliata, mozzo.",
                  "L'abbiamo varata stamattina, liscia come il rum! Ecco la tua parte, guadagnata fino all'ultima moneta.",
                  "Lo scalo intasato", "Libera lo scalo del Porto della Marea dalle melme di perla."),
        "grim": ("Sei rimasto più a lungo dei più, quindi te lo chiedo. I lupi delle braci girano attorno all'ultimo pozzo. Sei in meno, e beviamo un'altra stagione.",
                 "I lupi girano ancora. Il pozzo è ancora in piedi. Per ora.",
                 "Beviamo un'altra stagione. Prendi questo. È più di quanto possiamo permetterci, ed è per questo che è tuo.",
                 "L'ultimo pozzo", "Caccia i lupi delle braci che girano attorno all'ultimo pozzo delle Terre di Cenere."),
        "scholarly": ("In qualità di associato riconosciuto di questa comunità, puoi saperlo: i lupi della tempesta disturbano l'osservatorio. Sei, se non ti dispiace. Le letture sono rovinate.",
                      "Le letture restano rovinate. I lupi, purtroppo, restano.",
                      "Finalmente una lettura pulita! Il tuo nome va nei ringraziamenti, e questo va in tasca tua.",
                      "Interferenze all'osservatorio", "Caccia i lupi della tempesta che disturbano l'osservatorio di Lumeria."),
    },
}


def write_json(path, doc, like: str | None = None) -> None:
    newline = "\r\n" if like is not None and "\r\n" in like else "\n"
    path.write_text((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").replace("\n", newline), encoding="utf-8", newline="")


def patch_elder(region: str, tone: str, danger: int) -> None:
    path = DATA / "dialogues" / "role" / f"elder_{tone}.json"
    raw = path.read_text(encoding="utf-8", newline="")
    doc = json.loads(raw)
    nodes = doc["nodes"]
    quest = f"base:quest/side/friend_{region}"
    paid = f"friend_{region}_paid"
    mine = ("friend_offer", "friend_busy", "friend_paid")
    choices = [c for c in nodes["menu"]["choices"] if c.get("next") not in mine]
    nodes["menu"]["choices"] = [
        {"text": "$i18n:dlg.role.friend.ask", "next": "friend_offer",
         "when": {"all": [{"renown_at_least": FRIEND_AT}, {"not": {"any": [{"quest_active": quest}, {"quest_done": quest}]}}]}},
        {"text": "$i18n:dlg.role.friend.status", "when": {"quest_active": quest}, "next": "friend_busy"},
        {"text": "$i18n:dlg.role.friend.report", "when": {"all": [{"quest_done": quest}, {"not": {"flag": paid}}]}, "next": "friend_paid"},
        *choices]
    nodes["friend_offer"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.friend.{tone}.offer", "next": "friend_choice"}
    nodes["friend_choice"] = {"type": "choice", "choices": [
        {"text": "$i18n:dlg.role.errand.accept", "effects": [{"effect": "start_quest", "quest": quest}], "next": "end"},
        {"text": "$i18n:dlg.role.errand.later", "next": "end"}]}
    nodes["friend_busy"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.friend.{tone}.busy", "next": "end"}
    nodes["friend_paid"] = {"type": "effects", "next": "friend_thanks", "effects": [
        {"effect": "set_flag", "flag": paid, "value": True}, {"effect": "add_xp", "amount": 150 * danger},
        {"effect": "add_gold", "amount": 400 + 200 * danger}, {"effect": "add_item", "item": "base:item/potion_large", "qty": 2}]}
    nodes["friend_thanks"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.friend.{tone}.thanks", "next": "end"}
    write_json(path, doc, raw)


def patch_shopkeeper(tone: str, far: str) -> None:
    path = DATA / "dialogues" / "role" / f"shopkeeper_{tone}.json"
    raw = path.read_text(encoding="utf-8", newline="")
    doc = json.loads(raw)
    nodes = doc["nodes"]
    choices = [c for c in nodes["menu"]["choices"] if c.get("next") != "caravan"]
    at = next(i for i, c in enumerate(choices) if c.get("next") == "shop") + 1
    nodes["menu"]["choices"] = [*choices[:at], {"text": "$i18n:dlg.role.caravan", "next": "caravan"}, *choices[at:]]
    nodes["caravan"] = {"type": "effects", "effects": [{"effect": "open_shop", "region": far, "markup_pct": MARKUP_PCT}], "next": "end"}
    write_json(path, doc, raw)


def main() -> None:
    for region, (tone, enemy, count, danger, far) in REGIONS.items():
        quest = {"$schema": "../../../../schemas/quest.schema.json", "id": f"base:quest/side/friend_{region}",
                 "name": f"$i18n:quest.friend_{region}.name", "kind": "side",
                 "stages": [{"id": "hunt", "journal": f"$i18n:quest.friend_{region}.hunt",
                             "objectives": [{"type": "kill", "enemy": f"base:enemy/{enemy}", "count": count}], "next": "end"}],
                 "rewards": []}
        write_json(DATA / "quests" / "side" / f"friend_{region}.json", quest)
        patch_elder(region, tone, danger)
        patch_shopkeeper(tone, far)
    for lang in ("en", "it"):
        roles = dict(SHARED[lang])
        content = {}
        for region, (tone, *_rest) in REGIONS.items():
            offer, busy, thanks, name, journal = TALK[lang][tone]
            roles.update({f"dlg.friend.{tone}.offer": offer, f"dlg.friend.{tone}.busy": busy, f"dlg.friend.{tone}.thanks": thanks})
            content.update({f"quest.friend_{region}.name": name, f"quest.friend_{region}.hunt": journal})
        set_texts("roles.json", lang, roles)
        set_texts("content.json", lang, content)
    print(f"wrote {len(REGIONS)} quests for friends and the goods from afar of {len(REGIONS)} shopkeepers")


if __name__ == "__main__":
    main()
