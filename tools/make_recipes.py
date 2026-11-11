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
    "grilled_fish": ("grilled_fish", 2, {"river_fish": 2, "dry_branch": 1}),
    "fishermans_stew": ("fish_stew", 2, {"river_fish": 3, "healing_herb": 1, "dry_branch": 1}),
    # the hunt (spec 06, "Hunting"): meat over a fire, hides and antlers at an anvil
    "roast_meat": ("roast_meat", 2, {"game_meat": 2, "dry_branch": 1}),
    "hunters_stew": ("hunters_stew", 1, {"game_meat": 2, "healing_herb": 1, "mint_leaf": 1, "dry_branch": 1}),
    "hunters_jerkin": ("hunters_jerkin", 1, {"leather_vest": 1, "boar_hide": 3, "elk_antler": 1}),
    "antler_spear": ("antler_spear", 1, {"wood_log": 2, "elk_antler": 2, "iron_ore": 2}),
    "fox_cloak": ("fox_cloak", 1, {"fox_pelt": 4, "spider_silk": 2}),
    "royal_feast": ("royal_feast", 1, {"hearty_stew": 1, "honey_cake": 1, "wild_berries": 5}),
    # stronger potions from the weaker ones
    "potion_large": ("potion_large", 1, {"potion_medium": 2, "spore_cap": 2, "pine_resin": 1}),
    "potion_mana_medium": ("potion_mana_medium", 1, {"potion_mana_small": 2, "mint_leaf": 3, "wisp_ember": 1}),
    # gear from hides and ore
    "leather_vest": ("leather_vest", 1, {"tawny_fur": 4, "spider_silk": 2}),
    "studded_leather": ("studded_leather", 1, {"leather_vest": 1, "iron_ore": 4}),
    "pike": ("pike", 1, {"iron_ore": 4, "wood_log": 3}),
    # the brews of the regions: every material the creatures leave has a use
    "moonmoss_draught": ("moonmoss_draught", 1, {"moss_clump": 2, "shade_wisp": 1, "owl_feather": 1}),
    "miners_broth": ("miners_broth", 1, {"rust_flake": 2, "wolf_fang": 2, "healing_herb": 1}),
    "desert_nectar": ("desert_nectar", 1, {"amber_drop": 2, "scorpion_sting": 1}),
    "frost_tonic": ("frost_tonic", 1, {"ice_crystal": 2, "polar_fur": 1}),
    "pearl_elixir": ("pearl_elixir", 1, {"pearl_dust": 2, "tide_pearl": 1, "coral_fragment": 1}),
    "ember_brew": ("ember_brew", 1, {"ember_core": 1, "magma_shard": 1, "char_chunk": 1}),
    "starlight_elixir": ("starlight_elixir", 1, {"star_dust": 2, "nebula_ash": 1, "storm_feather": 1}),
    "windleaf_brew": ("windleaf_brew", 1, {"storm_feather": 1, "mint_leaf": 2}),
    # fine gear, at an anvil (every town has one): the plain piece and materials
    "fine_iron_sword": ("fine_iron_sword", 1, {"iron_sword": 1, "iron_ore": 3, "golem_core": 1}),
    "fine_hand_axe": ("fine_hand_axe", 1, {"hand_axe": 1, "iron_ore": 3, "wood_log": 3}),
    "fine_pike": ("fine_pike", 1, {"pike": 1, "iron_ore": 4, "slate_shard": 3}),
    "fine_leather_vest": ("fine_leather_vest", 1, {"leather_vest": 1, "tawny_fur": 2, "spider_silk": 2}),
    "fine_studded_leather": ("fine_studded_leather", 1, {"studded_leather": 1, "iron_ore": 3, "spider_silk": 2}),
}


# the cooked dishes are made next to a campfire (spec 06, "Stations"): Fenwick, Aldermere and every outpost have one
AT_FIRE = ("hearty_stew", "fish_stew", "royal_feast", "miners_broth", "grilled_fish", "fishermans_stew", "roast_meat", "hunters_stew")
# the fine gear is made at an anvil
AT_ANVIL = ("fine_iron_sword", "fine_hand_axe", "fine_pike", "fine_leather_vest", "fine_studded_leather", "hunters_jerkin", "antler_spear", "fox_cloak")


def main() -> None:
    recipes = [{"id": name, "output": {"item": f"base:item/{out}", "qty": qty},
                "inputs": [{"item": f"base:item/{item}", "qty": n} for item, n in inputs.items()],
                **({"station": "base:art/prop/campfire"} if name in AT_FIRE else {"station": "base:art/prop/anvil"} if name in AT_ANVIL else {})}
               for name, (out, qty, inputs) in RECIPES.items()]
    OUT.write_text(json.dumps({"$schema": "../../schemas/recipes.schema.json", "id": "base:recipes/all", "recipes": recipes}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(recipes)} recipes")


if __name__ == "__main__":
    main()
