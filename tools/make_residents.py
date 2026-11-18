#!/usr/bin/env python3
"""Writes the residents (spec 07, "Residents"): eight people who move to the outposts once the Guest is known in their region.

Every resident stands at the outpost of a region with `"when": {"renown_at_least": 6}`: until six quests are finished in that region it
is not there (not drawn, not talked to, never solid). Then it greets the Guest, gives a rune of the region once (the flag
`resident_<name>_gift`) and has a word about the new life there.

It writes the dialogues `data/base/dialogues/npc/resident_<name>.json`, the texts (it and en) and the lines in `npcs` of the world data
(a free cobblestone of the outpost next to its pedlar). It can be run any number of times. Then run `make_catalog.py` and `make_facts.py`.
"""
from __future__ import annotations

import json
import re

from make_towns import DATA, set_texts

WORLD = DATA / "worlds" / "overworld.json"
RENOWN = 6

# name, region, the outpost landmark, variant, rune, (speaker, hello, gift, talk) in en and it
RESIDENTS = [
    ("maela", "verdalis", "verdalis_outpost", "green", "rune_might", {
        "en": ("Maela, a farmer from the east",
               "You're the Guest who cleared the roads? Then I owe you this farm. We came west the week we heard the slimes were gone from the fields.",
               "Take this. My father carved it for a sword he never had. You have one.",
               "The soil here is so good you could plant a boot and get shoes. Come by at harvest; there'll be pie."),
        "it": ("Maela, contadina venuta dall'est",
               "Sei l'Ospite che ha ripulito le strade? Allora ti devo questa fattoria. Siamo venuti a ovest la settimana in cui abbiamo saputo che le gelatine avevano lasciato i campi.",
               "Prendi questa. L'ha incisa mio padre per una spada che non ha mai avuto. Tu ce l'hai.",
               "La terra qui è così buona che pianti uno stivale e ti nascono le scarpe. Passa al raccolto; ci sarà la torta.")}),
    ("sorrel", "whisperwood", "whisperwood_outpost", "purple", "rune_dusk", {
        "en": ("Sorrel, a herb-witch",
               "The trees whispered your name before you came. They said the paths were safe again, so I listened, and here I am.",
               "A rune of dusk. The shadows taught me to carve it. They will not mind if you borrow it.",
               "I gather by moonlight now, and nothing gathers me. That is a good life, in Whisperwood."),
        "it": ("Sorrel, strega delle erbe",
               "Gli alberi sussurravano il tuo nome prima che arrivassi. Dicevano che i sentieri erano di nuovo sicuri, così ho ascoltato, ed eccomi qui.",
               "Una runa del crepuscolo. Me l'hanno insegnata le ombre. Non si offenderanno se la prendi in prestito.",
               "Ora raccolgo al chiaro di luna, e nessuno raccoglie me. È una bella vita, a Whisperwood.")}),
    ("bram", "ironspine", "ironspine_outpost", "red", "rune_stone", {
        "en": ("Bram, a stonecutter",
               "Heard the passes were clear. Heard it was you. Good. I came for the stone.",
               "Stone rune. Cut it myself. Hits like a rockfall. Take it.",
               "Quarry's open again. Men sing in it. Never thought I'd say that about Ironspine."),
        "it": ("Bram, scalpellino",
               "Ho sentito che i passi erano sgombri. Ho sentito che eri tu. Bene. Sono venuto per la pietra.",
               "Runa di pietra. Tagliata da me. Colpisce come una frana. Prendila.",
               "La cava è di nuovo aperta. Gli uomini ci cantano. Non pensavo di dirlo mai di Ironspine.")}),
    ("yasmin", "sunscar", "sunscar_outpost", "ochre", "rune_ember", {
        "en": ("Yasmin, a caravan cook",
               "O bright one, O friend of every dune! My caravan stopped here for a night and stayed for good, because of the peace you brought.",
               "An ember rune, warm as my grandmother's oven and twice as fierce. May it season your every blow!",
               "I cook for the whole outpost now. The scorpions keep away and the spices keep coming. Paradise has sand in it, it turns out."),
        "it": ("Yasmin, cuoca di carovana",
               "O luminoso, o amico di ogni duna! La mia carovana si è fermata qui per una notte ed è rimasta per sempre, per la pace che hai portato.",
               "Una runa di brace, calda come il forno di mia nonna e due volte più feroce. Che insaporisca ogni tuo colpo!",
               "Ora cucino per tutto l'avamposto. Gli scorpioni stanno lontani e le spezie arrivano. Il paradiso ha la sabbia, a quanto pare.")}),
    ("hald", "frostveil", "frostveil_outpost", "cream", "rune_tide", {
        "en": ("Hald, an ice fisher",
               "The ice is quiet now. They say that is your doing. I came to fish it.",
               "A tide rune. Cold water, cold blade. It is yours.",
               "We sit by the holes and say nothing for hours. It is the best company I have had."),
        "it": ("Hald, pescatore sul ghiaccio",
               "Il ghiaccio ora è tranquillo. Dicono che sia merito tuo. Sono venuto a pescarci.",
               "Una runa della marea. Acqua fredda, lama fredda. È tua.",
               "Stiamo seduti accanto ai buchi e non diciamo niente per ore. È la miglior compagnia che abbia mai avuto.")}),
    ("cormac", "tidehaven", "tidehaven_outpost", "teal", "rune_gale", {
        "en": ("Cormac, a retired sailor",
               "Ahoy, Guest! Swallowed the anchor at last, I did. The crabs are behaved and the coast is safe, so here I drop it.",
               "A gale rune, off my old ship's figurehead. She'd want to sail again, even on a sword.",
               "Mending nets and telling lies, that's my life now. The fish are getting bigger in every story."),
        "it": ("Cormac, marinaio in pensione",
               "Ahoy, Ospite! Ho gettato l'ancora per sempre, finalmente. I granchi si comportano bene e la costa è sicura, e qui la lascio.",
               "Una runa della burrasca, presa dalla polena della mia vecchia nave. Vorrebbe navigare ancora, anche su una spada.",
               "Rammendo reti e racconto frottole, questa è la mia vita ora. I pesci diventano più grossi a ogni storia.")}),
    ("ash", "ashen_wastes", "ashen_outpost", "", "rune_ember", {
        "en": ("Ash, a cinder-gardener",
               "People said nothing grows out here. Then you came, and the fires calmed. So I came to make something grow.",
               "An ember rune. Found it in the ashes, where everything ends up. Use it before it ends up there again.",
               "Three green shoots this week. In the Ashen Wastes. Do not laugh; it is the biggest thing that has happened here in a century."),
        "it": ("Ash, giardiniera della cenere",
               "Dicevano che qui fuori non cresce niente. Poi sei arrivato tu, e i fuochi si sono calmati. Così sono venuta a far crescere qualcosa.",
               "Una runa di brace. L'ho trovata nella cenere, dove tutto va a finire. Usala prima che ci finisca di nuovo.",
               "Tre germogli verdi questa settimana. Nelle Terre di Cenere. Non ridere; è la cosa più grande successa qui da un secolo.")}),
    ("ines", "lumeria", "lumeria_outpost", "purple", "rune_dawn", {
        "en": ("Ines, an apprentice astronomer",
               "My thesis is on the effect of a single Guest on regional stability. Preliminary results: you. Hence my relocation.",
               "A dawn rune. Calibrated, inscribed and peer-reviewed by me. Please report your findings.",
               "The observatory lets me use the small telescope now. Last night I found a comet. I have named it after you, provisionally."),
        "it": ("Ines, apprendista astronoma",
               "La mia tesi riguarda l'effetto di un singolo Ospite sulla stabilità regionale. Risultati preliminari: tu. Da qui il mio trasferimento.",
               "Una runa dell'alba. Calibrata, incisa e revisionata da me. Ti prego di riferire i risultati.",
               "L'osservatorio ora mi lascia usare il telescopio piccolo. Ieri notte ho trovato una cometa. Le ho dato il tuo nome, in via provvisoria.")}),
]
SHARED = {
    "en": {"dlg.resident.ask": "How is life here?", "dlg.resident.bye": "Goodbye."},
    "it": {"dlg.resident.ask": "Come va la vita qui?", "dlg.resident.bye": "Arrivederci."},
}


def write_json(path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def dialogue(name: str, rune: str) -> dict:
    sp = f"resident_{name}"
    flag = f"resident_{name}_gift"
    return {"$schema": "../../../../schemas/dialogue.schema.json", "id": f"base:dialogue/npc/resident_{name}", "start": "c_gift", "nodes": {
        "c_gift": {"type": "condition", "when": {"flag": flag}, "then": "talk", "else": "hello"},
        "hello": {"type": "say", "speaker": sp, "text": f"$i18n:dlg.resident.{name}.hello", "next": "gift"},
        "gift": {"type": "say", "speaker": sp, "text": f"$i18n:dlg.resident.{name}.gift", "next": "give"},
        "give": {"type": "effects", "effects": [{"effect": "add_item", "item": f"base:item/{rune}", "qty": 1},
                                                {"effect": "set_flag", "flag": flag, "value": True}], "next": "end"},
        "talk": {"type": "choice", "choices": [{"text": "$i18n:dlg.resident.ask", "next": "life"}, {"text": "$i18n:dlg.resident.bye", "next": "end"}]},
        "life": {"type": "say", "speaker": sp, "text": f"$i18n:dlg.resident.{name}.talk", "next": "end"},
    }}


def free_tile(world: dict, landmark_id: str, near: tuple[int, int], taken: set[tuple[int, int]]) -> tuple[int, int]:
    """The free cobblestone of the outpost nearest to `near` (relative to the centre of the world): no wall, prop, spawner or person."""
    landmark = next(lm for lm in world["landmarks"] if lm["id"] == landmark_id)
    stamp = json.loads((DATA / "stamps" / (landmark["stamp"].split("/")[-1] + ".json")).read_text(encoding="utf-8"))
    x0, y0 = landmark["dx"] - stamp["anchor"][0], landmark["dy"] - stamp["anchor"][1]
    best = None
    for j, row in enumerate(stamp["rows"]):
        for i, ch in enumerate(row):
            entry = stamp["legend"].get(ch)
            if entry is None or entry.get("tile") != 14 or {"prop", "spawner", "npc"} & set(entry):
                continue
            x, y = x0 + i, y0 + j
            if (x, y) in taken:
                continue
            # as few people right next to it as the outpost allows, so that they can be told apart; then the nearest
            crowd = sum(1 for tx, ty in taken if abs(x - tx) <= 1 and abs(y - ty) <= 1)
            d = (x - near[0]) ** 2 + (y - near[1]) ** 2
            if best is None or (crowd, d, x, y) < best[0]:
                best = ((crowd, d, x, y), (x, y))
    assert best is not None, landmark_id
    return best[1]


def patch_world(placed: list[tuple[str, str, str, int, int]]) -> None:
    raw = WORLD.read_text(encoding="utf-8", newline="")
    for key, name, variant, dx, dy in placed:
        line = (f'{{ "key": "{key}", "dialogue": "base:dialogue/npc/resident_{name}", "variant": "{variant}", "dx": {dx}, "dy": {dy}, '
                f'"when": {{ "renown_at_least": {RENOWN} }} }}')
        if f'"key": "{key}"' in raw:
            raw = re.sub(r'\{ "key": "' + key + r'"[^\n]*\}', line, raw)
            continue
        last = raw.rindex('{ "key": "')
        end = raw.index("\n", last)
        indent = raw[raw.rindex("\n", 0, last) + 1:last]
        raw = raw[:end] + ",\n" + indent + line + raw[end:]  # the last person of the list has no comma after it
    WORLD.write_text(raw, encoding="utf-8", newline="")


def main() -> None:
    world = json.loads(WORLD.read_text(encoding="utf-8"))
    others = [n for n in world["npcs"] if not n["key"].startswith("resident_")]
    taken = {(n["dx"], n["dy"]) for n in others}
    pedlars = {n["key"]: (n["dx"], n["dy"]) for n in others if n["key"].startswith("pedlar_")}
    by_outpost = {}
    for lm in world["landmarks"]:
        if lm["id"].endswith("_outpost"):
            by_outpost[lm["id"]] = next(p for p in pedlars.values()
                                        if abs(p[0] - lm["dx"]) < 16 and abs(p[1] - lm["dy"]) < 16)
    placed = []
    texts = {lang: dict(SHARED[lang]) for lang in ("en", "it")}
    for name, _region, outpost, variant, rune, words in RESIDENTS:
        x, y = free_tile(world, outpost, by_outpost[outpost], taken)
        taken.add((x, y))
        placed.append((f"resident_{name}", name, variant, x, y))
        write_json(DATA / "dialogues" / "npc" / f"resident_{name}.json", dialogue(name, rune))
        for lang in ("en", "it"):
            speaker, hello, gift, talk = words[lang]
            texts[lang].update({f"speaker.resident_{name}": speaker, f"dlg.resident.{name}.hello": hello,
                                f"dlg.resident.{name}.gift": gift, f"dlg.resident.{name}.talk": talk})
    for lang in ("en", "it"):
        set_texts("core.json", lang, texts[lang])
    patch_world(placed)
    print(f"wrote {len(placed)} residents")


if __name__ == "__main__":
    main()
