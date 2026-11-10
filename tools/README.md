# Tools

Python scripts (3.12 or newer; the virtual environment of [`docs/dev/setup.md`](../docs/dev/setup.md)). Run them from the root of the repository. The generators write files that are committed: run them after changing what they read and commit the result.

## Checks

| Script | What it does |
|---|---|
| `validate_data.py` | validates the project metadata, every pack against the schemas, the references between files and the texts of both languages |
| `gen_conformance.py` (`--check`, `--serial`) | writes (or checks) `tests/conformance/*.json` from the reference, in parallel; never edit those files by hand |
| `gen_tables.py` (`--check`) | writes `data/base/tables/xp_table.json` from the formulas of spec 04 |
| `tests/` | `pytest`: the reference against known answers (`test_reference.py`), the data and the protagonists (`test_content.py`), the validator (`test_validate_data.py`) |

## The reference of the rules

`reference/`: the Python implementation of the rules that both clients must match (numerics, rules, movement, combat, story, guild, world generation, world time, routines, i18n, ids, poses). `conformance_m2.py`, `conformance_m3.py`, `conformance_m4.py` and `conformance_m5.py` build the suites of the vectors (named after the milestone that added them) and are imported by `gen_conformance.py`. The specs in [`docs/spec/`](../docs/spec/README.md) say what the reference must do.

## Generators of content

| Script | What it writes |
|---|---|
| `make_stamps.py` (`--show`) | `data/base/stamps/`: the hand-made pieces of the world, drawn with characters; `--show` draws them in the terminal |
| `make_role_dialogues.py` | the role dialogues of the settlement people and their texts (`dialogues/role/`, `i18n/*/roles.json`) |
| `make_demo_map.py` (`--check`) | `data/base/maps/demo.tmj`, the demo map |
| `make_catalog.py` | `docs/design/catalog.md`: regions, creatures, items, quests, sites and their world positions |
| `balance_report.py` | `docs/design/balance.md`: a rough model of every fight, with the difficulty of the world data |
| `make_art.py` (`tiles`, `props`) | writes the recipes of the terrain tiles and the props with `artkit.py` and `art_props.py` (style: [`docs/design/art-style.md`](../docs/design/art-style.md)) |
| `art_chars.py` (`art_looks.py`) | rewrites the parts of the humanoid rig (head, torso, arm, leg) with shading, details and the look of each protagonist and villager (`only`/`except` layers), keeping palettes and variants |
| `art_creatures.py` (`art_creature_looks.py`, `art_single_looks.py`) | rebuilds the detail layers over the creature recipes (jelly, fur, plates, glints) and the feature of each slime, wolf and knight; safe to run again |
| `compose.py` | composes the music of `data/base/audio/music/` and `music_rules.json` (spec 14) from moods, modes and progressions |
| `audio_wav.py` | writes a sound (`sfx <name>`) or a piece of music (`music <name> --layers base,combat`) to a WAV file, to listen to it |
| `make_recipes.py` | writes the crafting recipes `data/base/recipes.json` (spec 06, "Crafting") |
| `make_companions.py` | writes the companions `data/base/companions/` with their names, and gives each protagonist theirs (spec 10) |
| `make_towns.py` | writes the two hand-written towns: the named people of Fenwick and Aldermere, their dialogues and quests, their texts, and their lines in the world data (`npcs`, the landmark of Aldermere) |
| `make_stories.py` (`stories_act2.py`) | writes the first two acts of each protagonist's story: Sister Maren's dialogue in Aldermere, six quests for each protagonist, their texts, two staves for the magic users and her line in the world data |
| `make_talents.py` | writes the talents `data/base/talents.json` and their names (spec 11, "Talents") |
| `make_titles.py` | writes the titles `data/base/titles.json` and their names (spec 11) |
| `make_prologues.py` | writes the prologue of each protagonist, `data/base/dialogues/<name>/prologue.json`, and its texts (spec 18, "Prologue") |
| `make_gathering.py` | writes the gatherable materials (items and their texts) and `data/base/gathering.json` (spec 06, "Gathering") |
| `make_sfx.py` | writes the sound effect recipes of `data/base/audio/sfx/` and the table `events.json` (spec 14); the regional ambience is switched off there |
| `conformance_audio.py`, `conformance_music.py`, `conformance_savebundle.py`, `conformance_profile.py` | the suites of the sound synthesizer and directors, of the music, of the save bundle and of the profile, used by `gen_conformance.py` like `conformance_m2.py` to `conformance_m5.py` |
| `art_preview.py` (`--figures`) | an HTML sheet with art recipes, or with every person assembled, to look at them without the game |

## Working with GitHub

| Script | What it does |
|---|---|
| `ship.py` | checks, signed-off commit, push, pull request, waits for CI, squash merge and refresh of a play folder (see its header for the flags) |
| `sync_labels.py` | creates or updates the labels of `.github/labels.json` |
