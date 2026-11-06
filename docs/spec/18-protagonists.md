# 18. Protagonists

Status: **v1**. Data: `data/base/protagonists/*.json` (`schemas/protagonist.schema.json`). No conformance suite of its own: the rules a protagonist feeds (stats, skills, items) are covered by `stats` and `combat`.

## What a protagonist is

A protagonist is data: a name, a tone, **base stats** and **growth** (spec 04), a **gift** (`cheat`, an identifier, with its text), the **starting items** and the **starting skills**, and a **palette variant** of the character art (`art_variant`, optional: a variant name defined by the recipes of `data/base/art/characters/ren/`). `initially_available` says whether it can be
chosen in a new game. Nothing about a protagonist is in the code except what the engine does with these fields:

- the base stats and growth give the derived stats at every level (spec 04): a mage with a lot of intelligence and wisdom has a deep mana pool and fast regeneration, a firefighter with vitality has a lot of health;
- the weapon is the first starting item of kind `weapon` (spec 05); its `atk` and `matk` count;
- the skills are those of `starting_skills`, read by kind (spec 05): the first with a `hitbox` is the basic attack, the second the power strike, the one with a `movement` block the dodge roll. A skill with `damage.kind: magical` hits with `matk`;
- the starting items that are not equipment fill the inventory of a new game;
- `base:skill/ren/analyze` in the skills turns on the Analyze panel (a presentation feature: without it the key `Z` and its button do nothing).

## Gift rules

A protagonist may have `gift_rules`, an object of integers with these keys (all optional; a missing key is the neutral value):

| Key | Neutral | Effect |
|---|---|---|
| `mp_regen_pct` | 100 | the mana regeneration per tick is `mp_regen_x100 * mp_regen_pct / 100` (integer division; spec 05, "Mana") |
| `aggro_pct` | 100 | the aggro distance of every creature is `aggro_x100 * aggro_pct / 100` (integer division): below 100 creatures notice the player later (spec 05) |
| `heal_pct` | 100 | the health that an item restores (`heal`, spec 06) is `amount * heal_pct / 100` (integer division, applied to the sum of the `heal` effects) |
| `dodge_cooldown_pct` | 100 | the cooldown of the dodge roll is `cooldown * dodge_cooldown_pct / 100` (integer division, spec 05) |
| `death_save_ticks` | 0 | when a blow would bring the health to 0 or less and the **death save** is ready, the health becomes 1 instead and the death save is not ready for `death_save_ticks` ticks; 0 disables it |

The death save is not saved (a loaded game has it ready). In scenarios the object is `gift`. The conformance scenarios are `gift_death_save`, `gift_mp_regen`, `gift_heal`, `gift_aggro` and `gift_dodge_cooldown`.

The base roster uses them: Sakura `mp_regen_pct` 300; Daichi `death_save_ticks` 1800 (the Eternal Aegis: one blow survived every thirty seconds); Haruka `aggro_pct` 50 (the creatures notice her late); Marco `heal_pct` 200 (food and potions work twice as well); Yuki `dodge_cooldown_pct` 50. Ren's gift is the Analyze panel (a presentation feature). Gifts that are not in these knobs (the pocket that never fills, taming, a second life per dungeon) are not implemented; their texts say what each gift is today.


## Choosing and keeping

A **new game** (a slot with neither a save nor a protagonist file) asks who to be, on a screen that lists the available protagonists (Ren first, then the others by ID) with, for the selected one, its tagline, its gift and its story. The choice is written in `protagonist.txt` in the folder of the slot (the ID and a line feed) and in the `protagonist` field of the saves (spec 12). A game that exists
without a protagonist file (older saves) is played as `base:protagonist/ren`. A protagonist file that names an ID the pack does not have is ignored (Ren). The slot of the title screen keeps its world and its protagonist until it is deleted (deleting a game deletes its files, the protagonist file too).
Desktop: `--protagonist=<name>` plays that protagonist in a new game or the smoke test.

The choice screen takes `W`/`S` or the arrows, `E`/`Enter`/`Space` or a click to confirm, `1` to `9` to choose directly and `Esc` to go back to the title screen; on touch screens a tap selects a name and a second tap on it confirms, and Back returns to the games.

## Personal stories

Every protagonist starts with a **keepsake** (`base:item/keepsake_<name>`, kind `key`, price 0 so it cannot be sold, quantity 1) and Pip, the lad of the home village (spec 07), has for each of them a question in his menu that is shown only when the player holds that keepsake
(the condition `has_item`): "I keep seeing numbers. Is that normal?" for Ren, "Do you know anything about mana?" for Sakura, "Is there anyone here who needs help?" for Daichi, "Are there animals around here that need care?" for Haruka. It opens a short chain of **two quests**
(`base:quest/side/personal_<name>_1` and `_2`, offered in order, with Pip saying what he needs, what is still to do, and a farewell when it is done): the first pays 90 XP, 120 gold and two small potions, the second 170 XP, 240 gold and a **unique rare weapon**
(the Ledger blade, the Focus staff, the Rescue axe, the Herbalist cane). The objectives use only what lives around the home village (green and mint slimes, tawny wolves, myconids and their gel, leaves, furs and spore caps). No new rule is involved: it is data and texts.

## Texts

For a protagonist with the ID `base:protagonist/<name>`: `protagonist.<name>.name`, `.tagline`, `.gift` and `.story` in **both** languages (`content.json`). The story is a short paragraph about who they were and how they arrived (the Threshold of Lyra drops every guest in Verdalis, where the home village is).

## The base roster

| Protagonist | Tone | Gift (today) | Stats (str vit dex agi int wis luk) | Skills | Weapon |
|---|---|---|---|---|---|
| Ren Takahashi | comedy_light | System Eye: Analyze | 6 7 8 8 7 7 9 | Slash, Power strike, Dodge roll | Practice sword (atk 3) |
| Sakura Mori | slapstick | Unbound Mana: a huge mana pool, magical blows | 3 6 7 8 11 12 8 | Spark (magical), Arcane burst (360 degrees, 9 mana), Dodge roll | Apprentice staff (atk 1, matk 6) |
| Daichi Okabe | drama | Eternal Aegis: health and defense | 8 11 6 5 4 6 7 | Axe chop, Guard slam (170 degrees, 8 mana), Shield roll (10 ticks, 16 of invulnerability, speed x2.2) | Fire axe (atk 6) |
| Haruka Aizawa | cozy | Universal Tamer: speed and luck | 5 7 8 9 6 9 10 | Staff tap, Gale strike (9 mana), Dodge roll | Walking stick (atk 3, matk 2) |

| Marco Ferri | adventure | Modern Knowledge: food and potions heal twice as much (`heal_pct` 200) | 6 8 8 6 9 7 7 | Spanner swing, Pressure blast (220 range, 9 mana), Dodge roll | Wrench (atk 5) |
| Yuki Shirogane | noir | Pocket Dimension: the dodge recovers twice as fast (`dodge_cooldown_pct` 50) | 4 5 11 12 7 6 10 | Dagger flick (fast), Shadow cut (70 degrees, 8 mana), Shadow step (8 ticks, speed x3.2, 12 of invulnerability) | Thin dagger (atk 5) |

| Lena Voss | dark | Return to Death: a death save every 40 s (`death_save_ticks` 2400) | 4 6 9 8 10 9 6 | Incision, Autopsy strike (magical, 8 mana), Dodge roll | Scalpel (atk 4, matk 3) |
| Gideon Valmor | dark_comedy | Lord of Darkness: creatures notice him at 30 percent of the distance, healing works at 60 percent (`aggro_pct` 30, `heal_pct` 60) | 9 9 6 6 8 7 5 | Dark slash, Dominion (360 degrees, 10 mana), Dodge roll | Black blade (atk 8) |

All eight protagonists of the plan are playable. The deeper rules of the gifts (taming, the pocket, the Dark Tide) come with the progression systems (spec 11).
