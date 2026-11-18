#!/usr/bin/env python3
"""Writes the deeds (spec 11, "Deeds"): facts about all the games, read from the profile (`profile.json`), shown from the title screen.

It writes `data/base/deeds.json` and the texts of the deeds (it and en), and can be run any number of times.
"""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

ECHOES = ["ren", "sakura", "daichi", "haruka", "marco", "yuki", "lena", "gideon"]
REGIONS = ["verdalis", "whisperwood", "ironspine", "sunscar", "frostveil", "tidehaven", "ashen_wastes", "lumeria"]

# id, kind, what (count, or the list of creatures / titles), (name, text) in en and it
DEEDS = [
    ("first_blow", "kills", 1, {"en": ("The First Blow", "Defeat a creature."), "it": ("Il primo colpo", "Sconfiggi una creatura.")}),
    ("hundred_blows", "kills", 100, {"en": ("A Hundred Blows", "Defeat a hundred creatures, counting the best of each kind across games."),
                                     "it": ("Cento colpi", "Sconfiggi cento creature, contando il meglio di ogni specie fra tutte le partite.")}),
    ("thousand_blows", "kills", 1000, {"en": ("A Thousand Blows", "Defeat a thousand creatures, counting the best of each kind across games."),
                                       "it": ("Mille colpi", "Sconfiggi mille creature, contando il meglio di ogni specie fra tutte le partite.")}),
    ("ten_kinds", "kinds", 10, {"en": ("Field Notes", "Defeat ten kinds of creature."), "it": ("Appunti di campo", "Sconfiggi dieci specie di creature.")}),
    ("thirty_kinds", "kinds", 30, {"en": ("Naturalist of Two Worlds", "Defeat thirty kinds of creature."),
                                   "it": ("Naturalista di due mondi", "Sconfiggi trenta specie di creature.")}),
    ("sixty_kinds", "kinds", 60, {"en": ("The Whole Bestiary", "Defeat sixty kinds of creature."), "it": ("Tutto il bestiario", "Sconfiggi sessanta specie di creature.")}),
    ("gel_king", "defeated", ["gel_king"], {"en": ("Uncrowned", "Defeat the {} under the cellar."), "it": ("Senza corona", "Sconfiggi {} sotto la cantina.")}),
    ("wardens", "defeated", ["barrow_warden", "ice_warden", "vault_warden"],
     {"en": ("Past the Wardens", "Defeat {}."),
      "it": ("Oltre i guardiani", "Sconfiggi {}.")}),
    ("sovereigns", "defeated", ["frost_sovereign", "storm_sovereign"],
     {"en": ("No Crown Too High", "Defeat {}."),
      "it": ("Nessuna corona troppo alta", "Sconfiggi {}.")}),
    ("tyrants", "defeated", ["forge_tyrant", "char_tyrant"],
     {"en": ("Fire Against Fire", "Defeat {}."),
      "it": ("Fuoco contro fuoco", "Sconfiggi {}.")}),
    ("deep_waters", "defeated", ["drowned_captain", "cinder_colossus"],
     {"en": ("Water and Ash", "Defeat {}."),
      "it": ("Acqua e cenere", "Sconfiggi {}.")}),
    ("night_hunters", "defeated", ["moonshade_alpha", "rime_revenant"],
     {"en": ("Out of the Dark", "Defeat {}."), "it": ("Fuori dal buio", "Sconfiggi {}.")}),
    ("kings_of_beasts", "defeated", ["polar_king", "dire_alpha"],
     {"en": ("King of Kings", "Defeat {}."), "it": ("Re dei re", "Sconfiggi {}.")}),
    ("every_echo", "defeated", [f"echo_{who}" for who in ECHOES],
     {"en": ("Every Face of Yourself", "Defeat the Echo of each of the eight protagonists: one game each."),
      "it": ("Ogni volto di te", "Sconfiggi l'Eco di ognuno degli otto protagonisti: una partita ciascuno.")}),
    ("five_titles", "titles", 5, {"en": ("A Name People Use", "Earn five titles."), "it": ("Un nome che la gente usa", "Ottieni cinque titoli.")}),
    ("fifteen_titles", "titles", 15, {"en": ("Too Many Names", "Earn fifteen titles."), "it": ("Troppi nomi", "Ottieni quindici titoli.")}),
    ("thirty_titles", "titles", 30, {"en": ("Known Everywhere", "Earn thirty titles."), "it": ("Conosciuto ovunque", "Ottieni trenta titoli.")}),
    ("forty_titles", "titles", 40, {"en": ("Every Name There Is", "Earn forty titles."), "it": ("Tutti i nomi che esistono", "Ottieni quaranta titoli.")}),
    ("hero_and_legend", "earned", ["hero", "legend"], {"en": ("Hero, then Legend", "Earn the titles {}."),
                                                       "it": ("Eroe, poi leggenda", "Ottieni i titoli {}.")}),
    ("friend_of_the_world", "earned", [f"friend_{r}" for r in REGIONS],
     {"en": ("Friend of the World", "Become a friend of all eight regions."), "it": ("Amico del mondo", "Diventa amico di tutte e otto le regioni.")}),
    ("four_factions", "earned", ["guild_champion", "ring_walker", "keeper_of_legends", "heart_of_the_folk"],
     {"en": ("Welcome in Every Hall", "Earn the title of each of the four factions."),
      "it": ("Benvenuto in ogni sala", "Ottieni il titolo di ognuna delle quattro fazioni.")}),
    ("life_of_the_land", "earned", ["green_thumb", "seasoned_forager", "master_artisan", "great_hunter"],
     {"en": ("A Quiet Life, Too", "Earn the titles {}."),
      "it": ("Anche una vita tranquilla", "Ottieni i titoli {}.")}),
    ("beast_friend", "earned", ["beast_friend", "well_fed"],
     {"en": ("Fed and Followed", "Earn the titles {}."), "it": ("Sazio e seguito", "Ottieni i titoli {}.")}),
    ("hearth_and_blade", "earned", ["homemaker", "runesmith"],
     {"en": ("Hearth and Blade", "Earn the titles {}."), "it": ("Focolare e lama", "Ottieni i titoli {}.")}),
    ("second_life", "lives", 1, {"en": ("Again, From the Threshold", "Reincarnate a game."), "it": ("Di nuovo, dalla Soglia", "Reincarna una partita.")}),
    ("many_lives", "lives", 5, {"en": ("Many Lives", "Reincarnate five games."), "it": ("Molte vite", "Reincarna cinque partite.")}),
]


# The gifts of the deeds (spec 11, "Gifts of the deeds"): what every new game finds in its bag once the deed is done (item, quantity).
GIFTS = {
    "first_blow": ("potion_small", 3),
    "hundred_blows": ("potion_medium", 3),
    "thousand_blows": ("potion_large", 3),
    "ten_kinds": ("travel_ration", 5),
    "thirty_kinds": ("rune_might", 1),
    "sixty_kinds": ("rune_dawn", 1),
    "gel_king": ("honey_cake", 5),
    "wardens": ("fang_necklace", 1),
    "sovereigns": ("frost_locket", 1),
    "tyrants": ("ember_ring", 1),
    "deep_waters": ("pearl_pendant", 1),
    "night_hunters": ("owl_charm", 1),
    "kings_of_beasts": ("golem_amulet", 1),
    "every_echo": ("star_brooch", 1),
    "five_titles": ("potion_mana_small", 3),
    "fifteen_titles": ("windleaf_brew", 2),
    "thirty_titles": ("rune_gale", 1),
    "forty_titles": ("rune_ember", 1),
    "hero_and_legend": ("meadow_coat", 1),
    "friend_of_the_world": ("shepherds_blade", 1),
    "four_factions": ("cleansing_draught", 3),
    "life_of_the_land": ("herb_seeds", 5),
    "beast_friend": ("roast_meat", 5),
    "hearth_and_blade": ("rune_stone", 1),
    "second_life": ("potion_medium", 2),
    "many_lives": ("rune_tide", 1),
}
GIFT_WORDS = {"en": "Every new game: {item} x{qty}.", "it": "In ogni partita nuova: {item} x{qty}."}


def names(lang: str, keys: list[str]) -> str:
    """The names of the texts, joined as a list in that language ("A, B and C")."""
    texts = {}
    for file in ("content.json", "core.json"):
        texts.update(json.loads((DATA / "i18n" / lang / file).read_text(encoding="utf-8")))
    words = [texts[k] for k in keys]
    last = " and " if lang == "en" else " e "
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + last + words[-1]


def main() -> None:
    deeds = []
    texts = {"en": {}, "it": {}}
    for deed_id, kind, what, words in DEEDS:
        entry = {"id": deed_id, "kind": kind}
        if kind == "defeated":
            entry["enemies"] = [f"base:enemy/{e}" for e in what]
        elif kind == "earned":
            entry["titles"] = list(what)
        else:
            entry["count"] = what
        entry["name"] = f"$i18n:deed.{deed_id}.name"
        entry["text"] = f"$i18n:deed.{deed_id}.text"
        if deed_id in GIFTS:
            entry["reward"] = {"item": f"base:item/{GIFTS[deed_id][0]}", "qty": GIFTS[deed_id][1]}
        deeds.append(entry)
        for lang in ("en", "it"):
            texts[lang][f"deed.{deed_id}.name"] = words[lang][0]
            text = words[lang][1]
            if kind in ("defeated", "earned") and "{}" in text:  # the names as the game shows them
                keys = [f"enemy.{e}.name" for e in what] if kind == "defeated" else [f"title.{t}" for t in what]
                text = text.replace("{}", names(lang, keys))
            if deed_id in GIFTS:  # and the gift, as the game names the item
                item, qty = GIFTS[deed_id]
                text += " " + GIFT_WORDS[lang].format(item=names(lang, [f"item.{item}.name"]), qty=qty)
            texts[lang][f"deed.{deed_id}.text"] = text
    doc = {"$schema": "../../schemas/deeds.schema.json", "id": "base:deeds/all", "deeds": deeds}
    (DATA / "deeds.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    for lang in ("en", "it"):
        set_texts("content.json", lang, texts[lang])
    print(f"wrote {len(deeds)} deeds")


if __name__ == "__main__":
    main()
