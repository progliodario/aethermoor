#!/usr/bin/env python3
"""Writes the crafting recipes of the base pack (data/base/recipes.json). Spec 06, "Crafting". Run it after changing the list here."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "base" / "recipes.json"

# recipe id: (output item, quantity, {input item: quantity})
RECIPES = {
    "tonic": ("tonic", 2, {"healing_herb": 1, "wild_berries": 2}),
    "potion_small": ("potion_small", 1, {"healing_herb": 3, "slime_gel": 1}),
    "potion_medium": ("potion_medium", 1, {"healing_herb": 5, "slime_gel": 3, "pine_resin": 1}),
    "potion_mana_small": ("potion_mana_small", 1, {"mint_leaf": 2, "healing_herb": 1}),
    "travel_ration": ("travel_ration", 1, {"wild_berries": 5, "dry_branch": 1}),
    "honey_cake": ("honey_cake", 2, {"wild_berries": 3, "pine_resin": 1}),
    "hand_axe": ("hand_axe", 1, {"stone_chunk": 3, "wood_log": 2}),
    "iron_sword": ("iron_sword", 1, {"iron_ore": 5, "wood_log": 2}),
    # cooking: what the creatures leave and what grows, over a fire of dry branches
    "hearty_stew": ("hearty_stew", 1, {"spore_cap": 2, "healing_herb": 1, "dry_branch": 1}),
    "fish_stew": ("fish_stew", 1, {"crab_shell": 2, "mint_leaf": 1, "dry_branch": 1}),
    "royal_feast": ("royal_feast", 1, {"hearty_stew": 1, "honey_cake": 1, "wild_berries": 5}),
    # stronger potions from the weaker ones
    "potion_large": ("potion_large", 1, {"potion_medium": 2, "spore_cap": 2, "pine_resin": 1}),
    "potion_mana_medium": ("potion_mana_medium", 1, {"potion_mana_small": 2, "mint_leaf": 3, "wisp_ember": 1}),
    # gear from hides and ore
    "leather_vest": ("leather_vest", 1, {"tawny_fur": 4, "spider_silk": 2}),
    "studded_leather": ("studded_leather", 1, {"leather_vest": 1, "iron_ore": 4}),
    "pike": ("pike", 1, {"iron_ore": 4, "wood_log": 3}),
}


# the cooked dishes are made next to a campfire (spec 06, "Stations"): Fenwick, Aldermere and every outpost have one
AT_FIRE = ("hearty_stew", "fish_stew", "royal_feast")


def main() -> None:
    recipes = [{"id": name, "output": {"item": f"base:item/{out}", "qty": qty},
                "inputs": [{"item": f"base:item/{item}", "qty": n} for item, n in inputs.items()],
                **({"station": "base:art/prop/campfire"} if name in AT_FIRE else {})}
               for name, (out, qty, inputs) in RECIPES.items()]
    OUT.write_text(json.dumps({"$schema": "../../schemas/recipes.schema.json", "id": "base:recipes/all", "recipes": recipes}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(recipes)} recipes")


if __name__ == "__main__":
    main()
