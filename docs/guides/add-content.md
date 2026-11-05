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
