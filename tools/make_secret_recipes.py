#!/usr/bin/env python3
"""Writes the secret dishes of the regions (spec 06, "Recipe book"): eight dishes, one for each region, whose recipe the shopkeeper of
that region teaches for gold.

- the items `data/base/items/<dish>.json` and their texts;
- `SECRET`, read by `make_recipes.py`, which writes the recipes with `requires_flag` (`recipe_<dish>`);
- the shopkeepers' dialogues (`data/base/dialogues/role/shopkeeper_<tone>.json`), changed in place, and their texts.

It can be run any number of times. Then run `make_recipes.py` and `make_catalog.py`.
"""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

# dish: (region, tone, price of the lesson, price of the dish, inputs, effects, name en, name it, description en, description it)
SECRET = {
    "grandmothers_pie": ("verdalis", "warm", 300, 120, {"wild_berries": 4, "honey_cake": 1, "healing_herb": 2, "dry_branch": 1},
                         [{"effect": "heal", "amount": 120}, {"effect": "regen", "amount": 8, "ticks": 900}],
                         "Grandmother's pie", "Torta della nonna",
                         "The pie every grandmother of Verdalis swears is hers. Heals 120 and 8 more every second for fifteen seconds.",
                         "La torta che ogni nonna di Verdalis giura sia sua. Cura 120, e 8 ogni secondo per quindici secondi."),
    "moonlit_tea": ("whisperwood", "mystic", 400, 140, {"moss_clump": 2, "mint_leaf": 2, "shade_wisp": 1, "dry_branch": 1},
                    [{"effect": "restore_mp", "amount": 60}, {"effect": "haste", "amount": 30, "ticks": 1800}],
                    "Moonlit tea", "Tè al chiaro di luna",
                    "Steeped under a moon that may not have been there. 60 mana, and +30% walking speed for thirty seconds.",
                    "In infusione sotto una luna che forse non c'era. 60 di mana, e +30% di velocità a piedi per trenta secondi."),
    "forge_stew": ("ironspine", "gruff", 500, 160, {"game_meat": 2, "rust_flake": 2, "iron_ore": 1, "dry_branch": 1},
                   [{"effect": "fortify", "amount": 40, "ticks": 1800}, {"effect": "ward", "amount": 300, "ticks": 1800}],
                   "Forge stew", "Stufato della forgia",
                   "Cooked on the coals of a forge. Tastes of iron; nobody complains. Attack +40% and defense +300% for thirty seconds.",
                   "Cotto sulle braci di una forgia. Sa di ferro; nessuno si lamenta. Attacco +40% e difesa +300% per trenta secondi."),
    "sunfire_skewers": ("sunscar", "flowery", 500, 160, {"game_meat": 2, "amber_drop": 1, "cactus_pulp": 2, "dry_branch": 1},
                        [{"effect": "heal", "amount": 80}, {"effect": "fortify", "amount": 60, "ticks": 1200}],
                        "Sunfire skewers", "Spiedini di fuoco solare",
                        "Spiced until the spice gives up. Heals 80, and attack +60% for twenty seconds.",
                        "Speziati finché la spezia si arrende. Cura 80, e attacco +60% per venti secondi."),
    "hearth_broth": ("frostveil", "stoic", 600, 180, {"game_meat": 1, "polar_fur": 1, "healing_herb": 3, "dry_branch": 1},
                     [{"effect": "heal", "amount": 150}, {"effect": "ward", "amount": 400, "ticks": 1200}],
                     "Hearth broth", "Brodo del focolare",
                     "What Frostveil gives a guest before asking a name. Heals 150, and defense +400% for twenty seconds.",
                     "Ciò che il Velo di Gelo dà a un ospite prima di chiedergli il nome. Cura 150, e difesa +400% per venti secondi."),
    "captains_chowder": ("tidehaven", "salty", 400, 150, {"river_fish": 2, "crab_shell": 2, "sea_shell": 1, "dry_branch": 1},
                         [{"effect": "heal", "amount": 100}, {"effect": "regen", "amount": 10, "ticks": 600}, {"effect": "restore_mp", "amount": 30}],
                         "Captain's chowder", "Zuppa del capitano",
                         "Every captain has a recipe and every recipe has a captain. Heals 100, 10 every second for ten seconds, and 30 mana.",
                         "Ogni capitano ha una ricetta e ogni ricetta ha un capitano. Cura 100, 10 ogni secondo per dieci secondi, e 30 di mana."),
    "ember_chili": ("ashen_wastes", "grim", 700, 200, {"game_meat": 2, "ember_core": 1, "char_chunk": 1, "dry_branch": 1},
                    [{"effect": "fortify", "amount": 80, "ticks": 1200}, {"effect": "cleanse"}],
                    "Ember chili", "Chili di brace",
                    "Hot enough to burn away whatever else is burning you. Takes the bad effects away, and attack +80% for twenty seconds.",
                    "Così piccante da bruciare via tutto ciò che ti sta bruciando. Toglie gli stati alterati, e attacco +80% per venti secondi."),
    "starlight_souffle": ("lumeria", "scholarly", 700, 200, {"star_dust": 2, "wild_berries": 3, "mint_leaf": 2, "dry_branch": 1},
                          [{"effect": "restore_mp", "amount": 120}, {"effect": "haste", "amount": 40, "ticks": 1200}, {"effect": "regen", "amount": 6, "ticks": 1200}],
                          "Starlight soufflé", "Soufflé di luce stellare",
                          "It rises only if observed. 120 mana, +40% walking speed and 6 health every second, for twenty seconds.",
                          "Si alza solo se osservato. 120 di mana, +40% di velocità a piedi e 6 di vita ogni secondo, per venti secondi."),
}
SHARED = {
    "en": {"dlg.role.recipe.ask": "Do you know a recipe of these parts?", "dlg.role.recipe.learn": "Teach me.", "dlg.role.recipe.later": "Another time."},
    "it": {"dlg.role.recipe.ask": "Conosci una ricetta di queste parti?", "dlg.role.recipe.learn": "Insegnamela.", "dlg.role.recipe.later": "Un'altra volta."},
}
# tone: (offer, learned, too poor), en and it; {gold} is not an argument of the dialogues, so the price is written in the line
TALK = {
    "en": {
        "warm": ("Oh, the pie! Every grandmother here has her own, and mine is the real one. I'll teach you for {gold} gold, and that's a friend's price.",
                 "Butter cold, berries warm, and never tell anyone who taught you. Bake it at a fire.", "Come back with {gold} gold, dear. I'll keep the oven warm."),
        "mystic": ("The moonlit tea is not sold. It is taught, for {gold} gold, which is a kind of moonlight too.",
                   "Steep it while you think of nothing. If you think of something, steep it longer. At a fire.", "The tea will wait for {gold} gold. Tea is patient."),
        "gruff": ("Forge stew. {gold} gold. You won't find it written down.", "Meat, rust, a bit of ore. At a fire. Don't ask why it works.",
                  "{gold} gold. Come back when you have it."),
        "flowery": ("Ah, the sunfire skewers, pride of the dunes! A secret of my family, revealed to you alone for a mere {gold} gold!",
                    "Spice, then more spice, then courage! At a fire, under the stars, ideally with music!", "Alas! {gold} gold, and not a coin less, even for you."),
        "stoic": ("Hearth broth. {gold} gold.", "Slow fire. Patience. That is all of it.", "{gold} gold."),
        "salty": ("The captain's chowder? Arr, every captain guards it with 'is life. I'll sell ye mine for {gold} gold.",
                  "Fish, crab, a shell for luck, an' stir it widdershins. At a fire, matey.", "That ain't {gold} gold, matey. Not even close."),
        "grim": ("Ember chili. It keeps people alive out here. {gold} gold, and you will use it more than you think.",
                 "Meat, an ember core, a lump of char. At a fire. Eat it before it eats you.", "{gold} gold. We all have to eat."),
        "scholarly": ("The starlight soufflé is documented in exactly one manuscript, which I wrote. Tuition is {gold} gold.",
                      "Fold the star dust in gently; it is easily offended. Bake at a fire, under observation.", "Tuition remains {gold} gold. I have checked the arithmetic twice."),
    },
    "it": {
        "warm": ("Oh, la torta! Ogni nonna qui ha la sua, e la mia è quella vera. Te la insegno per {gold} monete d'oro, ed è un prezzo da amico.",
                 "Burro freddo, frutti di bosco tiepidi, e non dire mai a nessuno chi te l'ha insegnata. Cuocila a un fuoco.", "Torna con {gold} monete d'oro, caro. Il forno lo tengo caldo."),
        "mystic": ("Il tè al chiaro di luna non si vende. Si insegna, per {gold} monete d'oro, che sono anch'esse un po' di luce di luna.",
                   "Lascialo in infusione mentre non pensi a niente. Se pensi a qualcosa, lascialo di più. A un fuoco.", "Il tè aspetterà {gold} monete d'oro. Il tè è paziente."),
        "gruff": ("Stufato della forgia. {gold} monete. Non lo trovi scritto da nessuna parte.", "Carne, ruggine, un po' di minerale. A un fuoco. Non chiedere perché funziona.",
                  "{gold} monete. Torna quando le hai."),
        "flowery": ("Ah, gli spiedini di fuoco solare, orgoglio delle dune! Un segreto della mia famiglia, rivelato a te solo per appena {gold} monete d'oro!",
                    "Spezie, poi altre spezie, poi coraggio! A un fuoco, sotto le stelle, meglio con la musica!", "Ahimè! {gold} monete d'oro, e non una di meno, nemmeno per te."),
        "stoic": ("Brodo del focolare. {gold} monete.", "Fuoco lento. Pazienza. È tutto qui.", "{gold} monete."),
        "salty": ("La zuppa del capitano? Arr, ogni capitano la custodisce con la vita. Ti vendo la mia per {gold} monete d'oro.",
                  "Pesce, granchio, una conchiglia per fortuna, e gira al contrario. A un fuoco, mozzo.", "Queste non sono {gold} monete, mozzo. Neanche lontanamente."),
        "grim": ("Chili di brace. Qui fuori tiene in vita la gente. {gold} monete, e lo userai più di quanto pensi.",
                 "Carne, un nucleo di brace, un pezzo di carbone. A un fuoco. Mangialo prima che mangi te.", "{gold} monete. Tutti dobbiamo mangiare."),
        "scholarly": ("Il soufflé di luce stellare è documentato in un solo manoscritto, che ho scritto io. La lezione costa {gold} monete d'oro.",
                      "Incorpora la polvere di stelle con delicatezza: si offende facilmente. Cuoci a un fuoco, sotto osservazione.", "La lezione costa ancora {gold} monete d'oro. Ho controllato i conti due volte."),
    },
}


def write_json(path, doc, like: str | None = None) -> None:
    newline = "\r\n" if like is not None and "\r\n" in like else "\n"
    path.write_text((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").replace("\n", newline), encoding="utf-8", newline="")


def patch_shopkeeper(dish: str, tone: str, lesson: int) -> None:
    path = DATA / "dialogues" / "role" / f"shopkeeper_{tone}.json"
    raw = path.read_text(encoding="utf-8", newline="")
    doc = json.loads(raw)
    nodes = doc["nodes"]
    flag = f"recipe_{dish}"
    choices = [c for c in nodes["menu"]["choices"] if c.get("next") != "recipe_offer"]
    at = next(i for i, c in enumerate(choices) if c.get("next") == "shop") + 1
    nodes["menu"]["choices"] = [*choices[:at], {"text": "$i18n:dlg.role.recipe.ask", "when": {"not": {"flag": flag}}, "next": "recipe_offer"}, *choices[at:]]
    nodes["recipe_offer"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.recipe.{tone}.offer", "next": "recipe_choice"}
    nodes["recipe_choice"] = {"type": "choice", "choices": [
        {"text": "$i18n:dlg.role.recipe.learn", "next": "recipe_pay"}, {"text": "$i18n:dlg.role.recipe.later", "next": "end"}]}
    nodes["recipe_pay"] = {"type": "condition", "when": {"gold_at_least": lesson}, "then": "recipe_taught", "else": "recipe_poor"}
    nodes["recipe_taught"] = {"type": "effects", "effects": [{"effect": "spend_gold", "amount": lesson}, {"effect": "set_flag", "flag": flag, "value": True}],
                              "next": "recipe_learned"}
    nodes["recipe_learned"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.recipe.{tone}.learned", "next": "end"}
    nodes["recipe_poor"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.recipe.{tone}.poor", "next": "end"}
    write_json(path, doc, raw)


def main() -> None:
    texts = {"en": dict(SHARED["en"]), "it": dict(SHARED["it"])}
    for dish, (_region, tone, lesson, price, _inputs, effects, name_en, name_it, desc_en, desc_it) in SECRET.items():
        item = {"$schema": "../../../schemas/item.schema.json", "id": f"base:item/{dish}", "name": f"$i18n:item.{dish}.name",
                "description": f"$i18n:item.{dish}.desc", "kind": "food", "rarity": "rare", "price": price, "stack_max": 99,
                "use": {"effects": effects}}
        write_json(DATA / "items" / f"{dish}.json", item)
        patch_shopkeeper(dish, tone, lesson)
        for lang, name, desc in (("en", name_en, desc_en), ("it", name_it, desc_it)):
            offer, learned, poor = TALK[lang][tone]
            texts[lang].update({f"dlg.recipe.{tone}.offer": offer.replace("{gold}", str(lesson)),
                                f"dlg.recipe.{tone}.learned": learned, f"dlg.recipe.{tone}.poor": poor.replace("{gold}", str(lesson))})
            set_texts("content.json", lang, {f"item.{dish}.name": name, f"item.{dish}.desc": desc})
    for lang in ("en", "it"):
        set_texts("roles.json", lang, texts[lang])
    print(f"wrote {len(SECRET)} secret dishes and taught them to the shopkeepers")


if __name__ == "__main__":
    main()
