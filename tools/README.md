# Tools

Python scripts (3.12 or newer; the virtual environment of [`docs/dev/setup.md`](../docs/dev/setup.md)). Run them from the root of the repository. The generators write files that are committed: run them after changing what they read and commit the result. Every script that writes a file writes it with LF line endings.

## In short

| I changed... | Run |
|---|---|
| any data or schema | `python tools/validate_data.py` |
| a rule (spec, `reference/`) or the data a scenario reads | `python tools/gen_conformance.py` (then the vectors are committed with the change) |
| the table of a generator (recipes, titles, people, quests...) | that generator (see "Generators of content"), then `make_catalog.py` |
| anything that changes a number of the game (quests, creatures, items...) | `python tools/make_facts.py` (the numbers in the READMEs, `CLAUDE.md` and the roadmap) |
| anything, before shipping | `python -m pytest -q tools/tests` (the reference, the content, the documents) |

`tools/ship.py` runs the checks (validation, ruff, pytest, the vectors) before it commits.

## Checks

| Script | What it does |
|---|---|
| `validate_data.py` | validates the project metadata, every pack against the schemas, the references between files and the texts of both languages |
| `gen_conformance.py` (`--check`, `--serial`) | writes (or checks) `tests/conformance/*.json` from the reference, in parallel; never edit those files by hand |
| `gen_tables.py` (`--check`) | writes `data/base/tables/xp_table.json` from the formulas of spec 04 |
| `check_frames.py` (`--write`) | the automatic checks of the graphics (spec 16, "Checks of the frames"): the smoke-test frames of the desktop CI against their references `tests/frames/` (not blank, not black, near the fingerprint); `--write` writes the references from a CI run's frames |
| `make_facts.py` (`--check`) | writes the numbers of the game, counted from the data, into the blocks between `<!-- facts:begin -->` and `<!-- facts:end -->` of the READMEs, `CLAUDE.md` and the roadmap |
| `tests/` | `pytest`: the reference against known answers (`test_reference.py`), the data and the protagonists (`test_content.py`), the validator (`test_validate_data.py`), the documents (`test_docs.py`: links, every tool listed here, the facts blocks) |

## The reference of the rules

`reference/`: the Python implementation of the rules that both clients must match (numerics, rules, movement, combat, story, guild, world generation, world time, routines, i18n, ids, poses, the rasterizer of the art recipes). `conformance_m2.py`, `conformance_m3.py`, `conformance_m4.py` and `conformance_m5.py` build the suites of the vectors (named after the milestone that added them) and are imported by `gen_conformance.py`. The specs in [`docs/spec/`](../docs/spec/README.md) say what the reference must do.

## Generators of content

| Script | What it writes |
|---|---|
| `make_stamps.py` (`--show`) | `data/base/stamps/`: the hand-made pieces of the world, drawn with characters; `--show` draws them in the terminal |
| `make_role_dialogues.py` | the first version of the role dialogues of the settlement people and their texts (`dialogues/role/`, `i18n/*/roles.json`). **Do not run it**: the dialogues have grown since (errands, hunts, favors, workshops, inns, renown) and it would write them over |
| `make_secret_recipes.py` | writes the secret dishes of the regions (items and texts), teaches them to the shopkeepers (the role dialogues, changed in place) and gives `make_recipes.py` their recipes (spec 06, "Recipe book"); then run `make_recipes.py` and `make_catalog.py` |
| `make_friend_quests.py` | writes the quest that the elder of every settlement keeps for a friend of the region (`quests/side/friend_<region>.json`, spec 07 "Renown") and the goods from afar of the shopkeepers (spec 06), changing the role dialogues in place, with their texts; it can be run any number of times; then run `make_catalog.py` |
| `make_renown_talk.py` | adds the talk of the renown to the role dialogues, in place, and its texts (spec 07, "Renown"): the greeting of the elders and the shopkeepers to a friend of the region, the free bed of the innkeepers; it can be run any number of times |
| `make_demo_map.py` (`--check`) | `data/base/maps/demo.tmj`, the demo map |
| `make_catalog.py` | `docs/design/catalog.md`: regions, creatures, items, quests, sites and their world positions |
| `balance_report.py` | `docs/design/balance.md`: a rough model of every fight, with the difficulty of the world data |
| `make_font.py` (`--show`) | writes the font of the interface, `data/base/fonts/aether.json` (spec 13, "Font"): every glyph is drawn there as strokes; `--show out.png "text"` draws a text with it |
| `make_art.py` (`tiles`, `props`) | writes the recipes of the terrain tiles (`art_tiles.py`: painted macro tiles of 4 x 4 tiles, walls and floors) and of the props (`art_props.py`), with `artkit.py` (style: [`docs/design/art-style.md`](../docs/design/art-style.md)) |
| `art_chars.py` (`art_looks.py`, `art_looks_side.py`) | writes the people: the parts of the humanoid rig seen from the front and from behind, the palettes of the protagonists and the villagers, what each one wears (`only`/`except` layers), the rig and its two clips |
| `art_creatures.py` | writes every creature from the body of its family (slimes, beasts, guardians in armor, the single ones) and its own feature, keeping the palette of its file; run `make_echoes.py` after it |
| `compose.py` | composes the music of `data/base/audio/music/` and `music_rules.json` (spec 14) from moods, modes and progressions |
| `audio_wav.py` | writes a sound (`sfx <name>`) or a piece of music (`music <name> --layers base,combat`) to a WAV file, to listen to it |
| `make_recipes.py` | writes the crafting recipes `data/base/recipes.json` (spec 06, "Crafting"); it takes the secret dishes from `make_secret_recipes.py` and the runes and furniture from `make_furnishings.py` |
| `make_affixes.py` | writes the affixed weapon and armor of every region (spec 06, "Affixes") with their texts, and gives them to the guardians of the region as drops and to its shop for its friends (`renown_stock`), with the roll of the pieces found (`affix_roll`, spec 06, "Rolled affixes"); it can be run any number of times; then run `gen_conformance.py` and `make_catalog.py` |
| `make_furnishings.py` | writes the runes (engraved on the worn weapon at an anvil, spec 06 "Runes"), the furniture of the Guest's cottage (spec 06, "Furniture"), `data/base/home.json` and their texts, and gives `make_recipes.py` their recipes; it can be run any number of times; then run `make_recipes.py`, `make_catalog.py` and `make_facts.py` |
| `make_companions.py` | writes the companions `data/base/companions/` with their names, and gives each protagonist theirs (spec 10) |
| `make_home.py` | writes Nana Brin of Fenwick (free rest, three favours), Corvin the pedlar of Aldermere, the eight pedlars of the outposts and Old Tam of the Guest's cottage (the goods of a region a day, `day_mod`): dialogues, quests, texts and their lines in `npcs` (spec 07, "People of the towns"); then run `make_catalog.py` |
| `make_caravan.py` | writes Odo, the master of the caravan, who stands at a different outpost every day (`route`, spec 07 "Travellers") and sells the goods of the next one: his dialogue, his three errands (quests), texts and line in `npcs`; it can be run any number of times |
| `make_season_creatures.py` | writes the four creatures that live only in one season (spec 09, "Seasonal visitors"), their materials, the tea of the four seasons and their texts, and the first file of their art; it can be run any number of times; then run `art_creatures.py`, `make_seasonal_fauna.py`, `make_common_affixes.py`, `make_recipes.py` and `make_titles.py` |
| `make_seasonal_fauna.py` | writes the seasonal visitors of the fauna (also the snow slime and the sun slime, which live only in a season) (`seasons` of a fauna entry, spec 09 "Seasonal visitors") into the world data, in place; it can be run any number of times; then run `gen_conformance.py` |
| `make_common_affixes.py` | writes the twenty-four common pieces with an affix and the twelve with two (dropped by the guardians) (spec 06, "Rolled affixes") and their texts, and gives every creature of the fauna a drop "one of a list" of the pieces of its tier (`pick`, spec 05); it can be run any number of times; then run `gen_conformance.py` and `make_catalog.py` |
| `make_feasts.py` | writes the feast of every region and its games into the role dialogues of the innkeepers (spec 07, "Feasts"), the quests of the games (`quests/side/feast_<region>.json`) and their texts, in place; it can be run any number of times |
| `make_smiths.py` | writes the anvil of the shopkeepers into their role dialogues (the effect `temper`, spec 06 "Tempering") and its texts, in place; it can be run any number of times |
| `make_wandering_smith.py` | writes Brannoc, the wandering smith (spec 07, "Travellers"): his dialogue, his texts and his line with a `route` in the world data; it can be run any number of times |
| `make_bard.py` | writes Lark, the wandering bard (spec 07, "Travellers"): her dialogue with the songs of the regions, her texts and her line with a `route` in the world data; it can be run any number of times |
| `make_standing_bounties.py` | writes the standing bounty of every region (a repeatable quest on a guardian, spec 07 "Standing bounties") into the role dialogues of the guild clerks, in place, with the quests and their texts; it can be run any number of times; then run `set_quest_places.py` |
| `make_settlers.py` | writes the role dialogues of the settlers of the generated villages (`role/settler_<tone>.json`, spec 07 "Residents"), their trades and quests (`quests/side/settle_<region>.json`) and their texts; the slot is in the village stamps (`make_stamps.py`, the character `1` of the village stamps, a meaning of their own: `local` of `stamp()`) and the condition in `settlements.role_when` of the world data; it can be run any number of times |
| `make_residents.py` | writes the residents of the outposts (spec 07, "Residents"): eight people who come once the Guest has renown 6 in their region (`when`), with their dialogues (a rune given once), texts and lines in `npcs`; it can be run any number of times |
| `make_deeds.py` | writes the deeds of all the games (`data/base/deeds.json`) and their texts, with the names of creatures and titles as the game shows them (spec 11, "Deeds") |
| `make_towns.py` (`towns_outposts.py`) | writes the two hand-written towns and the named person of every outpost: the named people of Fenwick and Aldermere, their dialogues and quests, their texts, and their lines in the world data (`npcs`, the landmark of Aldermere) |
| `make_stories.py` (`stories_act2.py`, `stories_act3.py`, `stories_act4.py`, `stories_act5.py`, `stories_act6.py`) | writes the story in three acts, the epilogue, the fifth act ("A Life Here") and the sixth ("Two Guests") of each protagonist: Sister Maren's dialogue in Aldermere, ten quests for each protagonist, their texts, two staves for the magic users and her line in the world data |
| `make_talents.py` | writes the talents `data/base/talents.json` and their names (spec 11, "Talents") |
| `make_echoes.py` | writes the Echoes, the personal bosses of the protagonists: their art (a guardian's, recoloured), the enemies, their names and the sanctums in `landmarks`; then run `make_stamps.py`, `make_stories.py`, `gen_conformance.py` |
| `make_region_tales.py` | writes the tales of the villagers (three quests for each region) and changes the villagers' role dialogues in place (spec 07, "Tales of the villagers"); it runs `set_factions.py`; then run `make_catalog.py` |
| `make_faction_gifts.py` | writes the gifts of the factions (the Guild signet of the clerks, the Folk charm of the elders, Mira's Wayfarer's band, Selwyn's Archivist's quill; run it again after `make_towns.py`) and changes the role dialogues in place (spec 07, "Factions"); then run `make_catalog.py` |
| `check_translations.py` (`--check`) | writes `docs/design/translations.md`: texts that may be left in the other language (spec 17) |
| `set_factions.py` | gives every quest the faction it counts for, from its file name, and writes the names of the factions (spec 07, "Factions"); `make_towns.py`, `make_stories.py`, `make_friend_quests.py` and `set_quest_places.py` run it |
| `set_quest_places.py` | gives every quest stage that asks to defeat a guardian the `place` of that guardian, so that the goal of the map goes there (spec 07, "Places"); `make_stories.py` and `make_towns.py` run it |
| `make_wildlife.py` | writes four more creatures of the regions (blossom slime, hollow armor, frost wisp, cinder wolf: enemies, a first art file with their palette, fauna of the regions) and their items; then run `art_creatures.py`, `make_recipes.py`, `gen_conformance.py` and `make_catalog.py` |
| `make_hunting.py` | writes the game of the hunt (wild boar, ridge elk, dune fox: enemies, a first art file with their palette, fauna of the regions) and its items (spec 06, "Hunting"); then run `art_creatures.py` (it draws them), `make_recipes.py` and `gen_conformance.py` |
| `make_titles.py` | writes the titles `data/base/titles.json` and their names (spec 11) |
| `make_tags.py` | writes the tags `data/base/tags.json`, their names and what they do (spec 11, "Tags"): traits earned like titles, one worn at a time |
| `make_prologues.py` | writes the prologue of each protagonist, `data/base/dialogues/<name>/prologue.json`, and its texts (spec 18, "Prologue") |
| `make_gathering.py` | writes the gatherable materials (items and their texts) and `data/base/gathering.json` (spec 06, "Gathering") |
| `make_sfx.py` | writes the sound effect recipes of `data/base/audio/sfx/` and the table `events.json` (spec 14); the regional ambience is switched off there |
| `conformance_audio.py`, `conformance_music.py`, `conformance_savebundle.py`, `conformance_profile.py` | the suites of the sound synthesizer and directors, of the music, of the save bundle and of the profile, used by `gen_conformance.py` like `conformance_m2.py` to `conformance_m5.py` |
| `art_preview.py` (`--figures`, `--scene`; `art_scene.py`) | draws art recipes to PNG with the reference rasterizer (`reference/raster.py`) and collects them in a page and in one picture; every person assembled; a piece of world |

## Working with GitHub

| Script | What it does |
|---|---|
| `ship.py` | checks, signed-off commit, push, pull request, waits for CI, squash merge, deletion of the branch and of the old CI caches, refresh of the play folder (`../aethermoor-play` when it exists; see its header for the flags) |
| `sync_labels.py` | creates or updates the labels of `.github/labels.json` |

## Running a generator again

Every generator of this folder was run on a clean tree and checked to change nothing (17 November 2026), with these exceptions:

| Script | Why | What to do |
|---|---|---|
| `make_role_dialogues.py` | the first version of the role dialogues; they have grown since | **never run it**: change the role dialogues in place, as the other tools do |
| `compose.py` | it writes `music_rules.json`, which turns the music back on; the owner switched it off | do not run it without the owner's yes |
| `make_hunting.py`, `make_wildlife.py` | they write a first art file of their creatures | run `art_creatures.py` after them (it draws the creatures again) |
| `make_echoes.py` | it writes the Echoes and their sanctums | run `make_stamps.py`, `make_stories.py`, `gen_conformance.py` after it |

`make_towns.py` runs `set_quest_places.py`, `set_factions.py` and `make_faction_gifts.py` itself. The tools that change the role dialogues in place (`make_region_tales.py`, `make_friend_quests.py`, `make_faction_gifts.py`, `make_secret_recipes.py`, `make_renown_talk.py`) keep their choices where they are in the menus, so they can run in any order and any number of times.

On Windows, a script may stop now and then with `OSError: [Errno 22] Invalid argument` on a file it has just written: something of the system (an antivirus or the indexer) holds the file for a moment. Run it again.
