# Adding content

How to add the usual things to the base pack (`data/base`). Everything is data: no code changes unless a rule changes (then see the rule in [`CLAUDE.md`](../../CLAUDE.md): spec, reference, vectors, both clients).

Before and after any change: `python tools/validate_data.py`. When the world data, a stamp or anything the world generation reads changes: `python tools/make_stamps.py` (if a stamp changed) and `python tools/gen_conformance.py` (about 20 s); the tests that compare the clients with the vectors fail until the vectors are current. `python tools/ship.py` runs the whole set of checks and carries a change to a merged pull request.

## Texts

All visible text is an `$i18n:` key with a text in **both** `data/base/i18n/it/` and `data/base/i18n/en/` (`core.json` for the interface and the story, `content.json` for names and descriptions of things, `roles.json` for what the people of the settlements say). Keys are `kind.name.part` (`item.potion_large.name`). Plural names use the message format of spec 17.

## An item

Copy the closest file in `data/base/items/` (a weapon, an armor, a consumable or a material), change the ID (`base:item/<name>`, snake_case, stable: renaming needs a save migration), give it a `rarity` and a `price`, and add `item.<name>.name` and `.desc` in both languages. Weapons have `weapon {atk, matk}`, armors `armor {def, mdef}`, consumables `use.effects` (`heal`). To sell it, add it to the `shop.stock` of a region in `data/base/worlds/overworld.json`.

A consumable's `use.effects` are applied by the engine: `heal` (`amount` of health) and `restore_mp` (`amount` of mana points), both listed in [spec 06](../spec/06-items.md); a new kind of effect is a rule change (spec, reference, vectors, both clients). Mana potions are `data/base/items/potion_mana_*.json`.

## A skill

Skills are `data/base/skills/<owner>/<name>.json` (`schemas/skill.schema.json`) and are listed in the `starting_skills` of a protagonist (`data/base/protagonists/`). The engine knows three kinds today, picked by the content of the file, and nothing else is interpreted yet:

- the first skill with a `hitbox` is the basic **attack** (`base:skill/common/slash`);
- the second skill with a `hitbox` is the **power strike**: it needs `cost.mp` (spec 05, "Mana");
- a skill with a `movement` block (`speed_mult_x100`, `iframes`) is the **dodge roll** (`timing.active` is its length in ticks, `cooldown_ticks` its cooldown).

So changing the numbers of these skills is a data change (run `python tools/gen_conformance.py` only if a scenario copies them; the conformance scenarios carry their own numbers), but a new kind of skill (a third attack, a spell, a buff) is a rule change that starts in [spec 05](../spec/05-combat-v1.md). `base:skill/ren/analyze` is a presentation feature (the Analyze panel) and has no rules.

## A protagonist

The eight base protagonists are the examples: `data/base/protagonists/<name>.json` (`schemas/protagonist.schema.json`) and, for each one, the files that its data names. A new one needs, in this order:

1. **Look**: a palette variant of the same name in the four recipes of `data/base/art/characters/ren/` (`head`, `torso`, `arm`, `leg`: `skin`, `hair`, `shirt`, `shirt_dark`, `pants`, `boots`), given as `art_variant`.
2. **Weapon and keepsake**: `data/base/items/<weapon>.json` (kind `weapon`, `atk` and `matk`) and `keepsake_<name>.json` (kind `key`, price 0, so that it cannot be sold).
3. **Skills**: `data/base/skills/<name>/`: a basic attack and a power strike (two skills with a `hitbox`, the second with a `cost.mp`; `damage.kind` is `physical` or `magical`) and, optionally, an own dodge (a skill of type `movement` with a `movement` block); `base:skill/common/dodge` is the default. Rules in [spec 05](../spec/05-combat-v1.md).
4. **The protagonist file**: base stats and growth (the stat screen of the chooser shows what they give at level 1), `starting_items` (weapon, bread, potions, the keepsake), `starting_skills` in that order, `art_variant`, and `gift_rules` if the gift has numbers (the five knobs of [spec 18](../spec/18-protagonists.md)). `python tools/balance_report.py` does not model other protagonists than Ren.
5. **Texts** in both languages (`content.json`): `protagonist.<name>.name`, `.tagline`, `.gift`, `.story`; the names and descriptions of the skills and items.
6. **A personal story** (optional but expected): two quests `quests/side/personal_<name>_1.json` and `_2.json` and a question in the menu of Pip (`data/base/dialogues/npc/pip.json`) shown with the condition `has_item` on the keepsake; the rewards of the second quest include a unique weapon.

`python tools/validate_data.py`, `python tools/make_catalog.py` and the tests (`python -m pytest tools/tests`: `test_every_protagonist_is_complete`) check the rest.

## A recipe, and a prop to gather from

The crafting recipes and the props that give materials are tables written by a script: change the table in `tools/make_recipes.py` (recipe: output, quantity, inputs; every item must exist) or in
`tools/make_gathering.py` (the materials and, for each prop art, its drops with a chance and a range, and the ticks it takes to grow back), run the script and the validator. Rules: [spec 06](../spec/06-items.md), "Gathering" and "Crafting".

A dish or a brew can do more than heal: `fortify` (attack, percent, for `ticks`) and `ward` (defense, percent, for `ticks`) in the item's `use.effects` (spec 06, "Fortify" and "Ward").
An accessory is an item of kind `accessory` with `accessory {atk, matk, def, mdef, max_hp, crit_pm}` (spec 06, "Equipment"); add its recipe in `tools/make_recipes.py` (`AT_ANVIL`).
Fishing is gathering from a prop that grows on the beaches (`base:art/prop/reeds`, sound `water`); a new kind of fish is a drop of its node in `tools/make_gathering.py`.

## Game to hunt

The game of the hunt is a table in `tools/make_hunting.py`: level, stats, palette (on the body of the wolves), drops, the fauna drop and the regions where it lives, and its items. Give it a look of its own
in `tools/art_creature_looks.py` (`WOLVES`), then run `python tools/make_hunting.py`, `python tools/art_creatures.py`, `python tools/make_recipes.py` (for the recipes that use its drops) and
`python tools/gen_conformance.py` (the fauna changes the world). Rules: [spec 06](../spec/06-items.md), "Hunting".

## A companion

`tools/make_companions.py` has one line for each companion: whose it is, the creature art it is drawn with, its names, attack, range, cooldown and speed. Running it writes `data/base/companions/` and the
`companion` of each protagonist. Rules: [spec 10](../spec/10-companions.md).

## A talent

`tools/make_talents.py` lists the talents: the stat they multiply (`attack`, `health`, `mana`, `defense`), the percent of a rank, the ranks and the names, and how many points a level gives. Rules: [spec 11](../spec/11-progression.md), "Talents". A new kind of stat is a rule change.

## A title

`tools/make_titles.py` lists the titles in order of rank: a kind (`kills`, `kills_of` with a creature, `level`, `species`, `quests`, or a counter: `gathered`, `crafted`, `parried`), a count and the names. Titles are computed,
not saved, so a new one is earned at once by who already satisfies it, and every title in the profile is one percent of health for all games (the echoes): add them with care. Rules: [spec 11](../spec/11-progression.md).

## A named person with quests

`tools/make_towns.py` has a table of people: where they stand (tiles from the center of the world, on walkable ground), their look, their lines and their quests (objectives and rewards). It writes the dialogue, the quests, the texts and
the person's line in `npcs` of the world data. The count of `npcs` is checked by a test of each client (see the last section).

## A prologue

`tools/make_prologues.py` has, for each protagonist, the lines of Lyra and the two answers, in both languages; it writes `data/base/dialogues/<name>/prologue.json` and the texts. Rules: [spec 18](../spec/18-protagonists.md), "Prologue".

## A sound

`tools/make_sfx.py` builds every sound effect recipe and the table of events (`data/base/audio/events.json`). Listen to a sound before adding it: `python tools/audio_wav.py sfx <name> --out x.wav`. The music and the loops
of ambience of the regions are switched off in the base pack (see [spec 14](../spec/14-audio.md), "Ambience"): do not turn them back on without the owner having listened to them.

## A creature

1. Art: copy a recipe from `data/base/art/creatures/` and change its `palette` (same keys) for a recolor, or draw a new one (`schemas/art_recipe.schema.json`: layers of `rect`, `ellipse`, `polygon` and `path` with flat, linear or radial fills). Look at it with `python tools/art_preview.py <name> --out sheet.html` and open the sheet in a browser.
2. `data/base/enemies/<name>.json`: level, `stats`, `weaknesses_pm`, `xp`, `drops` (one item with a weight in permille), `radius_x100`, a `behavior` from `data/base/behaviors/` and the art.
3. Where it lives: add it to the `fauna` of a region (`enemy`, `drop`, `weight`), or to a stamp (below). The guild board and the commissions find it through the fauna.
4. Names and the drop item as in the sections above.

`python tools/balance_report.py` and `python tools/make_catalog.py` show where a new creature sits among the others.

## A quest and its dialogue

A quest is `data/base/quests/<kind>/<name>.json`: stages with `kill`, `collect` and `talk` objectives and a `rewards` list (or no rewards when the dialogue that pays it does the effects). A dialogue is `data/base/dialogues/...`: nodes `say`, `choice`, `condition` and `effects`; the conditions and effects are a closed catalog (spec 07). People of the settlements speak `dialogues/role/<role>_<tone>.json` (eight tones, one per region); named people are listed in `npcs` of the world data and have `dialogues/npc/<name>.json`, a `speaker.<key>` text and a position in tiles from the center of the world.

The usual pattern for something that is offered once and paid once is a choice with a `when` that hides it while the quest is active or done, and an `effects` node that sets a flag and pays. `tools/tests/test_reference.py` has tests that play such flows through the reference engine; copy one when you add a new flow.

## A place (stamp and landmark)

Stamps are drawn in `tools/make_stamps.py` (a `Canvas` with `put`, `rect`, `hline`, `vline` and `house`; the legend characters at the top say what each one is: walls, floors, props, enemy spawners, people) and written to `data/base/stamps/`. A landmark in `landmarks` of the world data places a stamp at a fixed place: `dx`, `dy` are tiles from the center of the world, and the point must be the **middle of a site cell** (`dx` and `dy` equal to 128 modulo 256) with one landmark per cell. A prop has no tile of its own, so put it on terrain that is not a wall. The terrain around a landmark is cleared of water and mountains (spec 09, "Clearings").

When you add a stamp, the tests of both clients that count the stamps and the people of the world (`desktop/tests/combat_test.cpp`, `android/core/src/test/kotlin/.../WorldGenTest.kt`) need the new number.

## A region

In `regions` of the world data: `x_pm` and `y_pm` (position in permille of the world), `danger`, `tone` (the voice of its people: it needs the dialogues of the roles in that tone), `shop`, `fauna`, and, so that it looks like its name, `bias` (elevation, temperature, moisture), `ground` (tile gids by biome) and `props` (spec 09, "Regions look like their names").

## A language

A new folder `data/base/i18n/<lang>/` with `core.json`, `content.json` and `roles.json`, and the language in `languages` of `data/base/pack.json`. `python tools/validate_data.py` lists the missing keys.

## What the clients check by hard-coded numbers

Some tests of the clients count things (stamps, people of the world, tiles of the tileset, the gid of the start tile). If CI fails after a data change, look there first.
