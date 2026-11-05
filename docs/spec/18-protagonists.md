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

The gift is flavor and the mechanics above: **no gift has a rule of its own yet** (taming, the second life of the aegis, the mana that never runs out). The text of each gift says what it is today and what is still to come.

## Choosing and keeping

A **new game** (a slot with neither a save nor a protagonist file) asks who to be, on a screen that lists the available protagonists (Ren first, then the others by ID) with, for the selected one, its tagline, its gift and its story. The choice is written in `protagonist.txt` in the folder of the slot (the ID and a line feed) and in the `protagonist` field of the saves (spec 12). A game that exists
without a protagonist file (older saves) is played as `base:protagonist/ren`. A protagonist file that names an ID the pack does not have is ignored (Ren). The slot of the title screen keeps its world and its protagonist until it is deleted (deleting a game deletes its files, the protagonist file too).
Desktop: `--protagonist=<name>` plays that protagonist in a new game or the smoke test.

The choice screen takes `W`/`S` or the arrows, `E`/`Enter`/`Space` or a click to confirm, `1` to `9` to choose directly and `Esc` to go back to the title screen; on touch screens a tap selects a name and a second tap on it confirms, and Back returns to the games.

## Texts

For a protagonist with the ID `base:protagonist/<name>`: `protagonist.<name>.name`, `.tagline`, `.gift` and `.story` in **both** languages (`content.json`). The story is a short paragraph about who they were and how they arrived (the Threshold of Lyra drops every guest in Verdalis, where the home village is).

## The base roster

| Protagonist | Tone | Gift (today) | Stats (str vit dex agi int wis luk) | Skills | Weapon |
|---|---|---|---|---|---|
| Ren Takahashi | comedy_light | System Eye: Analyze | 6 7 8 8 7 7 9 | Slash, Power strike, Dodge roll | Practice sword (atk 3) |
| Sakura Mori | slapstick | Unbound Mana: a huge mana pool, magical blows | 3 6 7 8 11 12 8 | Spark (magical), Arcane burst (360 degrees, 9 mana), Dodge roll | Apprentice staff (atk 1, matk 6) |
| Daichi Okabe | drama | Eternal Aegis: health and defense | 8 11 6 5 4 6 7 | Axe chop, Guard slam (170 degrees, 8 mana), Shield roll (10 ticks, 16 of invulnerability, speed x2.2) | Fire axe (atk 6) |
| Haruka Aizawa | cozy | Universal Tamer: speed and luck | 5 7 8 9 6 9 10 | Staff tap, Gale strike (9 mana), Dodge roll | Walking stick (atk 3, matk 2) |

The other protagonists of the plan (Marco, Yuki, Lena, Gideon) and the rules of the gifts come with the progression systems (spec 11).
