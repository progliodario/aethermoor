# CLAUDE.md

Guide for Claude, any other AI assistant ([`AGENTS.md`](AGENTS.md) points here) and humans working in this repo. The project owner mostly changes the game by asking Claude, so this file is the source of working rules. Read it whole before changing anything.

## What this is

**Aethermoor** (working title): top-down real-time isekai fantasy action RPG, 2D vector graphics, open world, eight playable protagonists, single player, offline.
Two native clients with **separate code** and **shared data and specs**:

- `desktop/`: C++20, SDL3, with the in-house vector rasterizer (ADR 0012 and 0013). Windows and Linux.
- `android/`: Kotlin, libGDX, the same rasterizer in Kotlin. Android 11+ (minSdk 30).

Full plan: `docs/plan/README.md` (Italian). Decisions: `docs/adr/`. Index of all docs: `docs/index.md`.

## Golden rules

1. **Spec first.** Gameplay rules are written in `docs/spec/` before or together with the code.
2. **Data driven.** Never hardcode names, texts, balance numbers or content in code. Content is JSON under `data/`; visible text only via `$i18n:` keys, always in `it` **and** `en`.
3. **Two clients, one behavior.** A change to rules touches: spec, reference (`tools/reference/`), conformance vectors, `desktop/`, `android/`. If a client lags, open a `parity-debt` issue and use a feature gate. Do not silently diverge.
4. **Never hand-edit generated files** (list below): change their source and run the tool. Above all `tests/conformance/*.json`: regenerate with `tools/gen_conformance.py`.
5. **Determinism.** World generation uses only integer / Q16.16 math and the hash/PCG32 defined in the spec. No `float`, `sin`, `cos`, `pow`, `sqrt` there. Never use `-ffast-math`; keep `-ffp-contract=off` (GCC/Clang) and `/fp:strict` (MSVC).
6. **Gameplay math is integer** (percent and permille) plus data tables. No `pow` in formulas: use tables.
7. **Stable IDs.** `namespace:category/name`. Renaming an ID needs a save migration.
8. **No network, no telemetry, no secrets** in the repo (keystores, tokens).
9. **Licenses.** Code GPL-3.0-or-later, content CC BY-SA 4.0. Only add GPLv3-compatible dependencies.
10. **Core stays headless.** `core/data/sim/worldgen` must not import graphics, audio, input, UI or platform code.

## How to work

- **Full autonomy.** The owner has delegated every design decision (story, tone, balance, content) and wants Claude to do all the work without asking: decide, implement, ship, and keep going down the roadmap (`docs/plan/06-roadmap-rischi-backlog.md`, section 8). A question now and then is fine when a choice is truly the owner's taste, but never wait on one: pick the best option, say what was chosen, go on. Only publishing and governance stay with the owner (a public release, branch protection, repository settings, licenses of outside material, code signing).
- **Big PRs, many roadmap items each.** At every prompt of the owner, do a lot: several roadmap items (features, content, fixes, docs) in one branch and one PR, shipped with `tools/ship.py` when CI is green. The owner explicitly does not want small PRs.
- **Fights must be too easy.** The protagonist is overpowered, as in every isekai: this is a core theme, not a balance bug. Tune the creatures and the world so that ordinary fights are won in a blow or two and guardians are a show, not a wall. Never make the game harder to make it "balanced".
- **Music and ambience stay off** (no `music_rules.json`, empty `ambience.regions` in `events.json`): the owner found them unpleasant. Do not turn them back on, and do not run `tools/compose.py`, without asking.
- **Who tests what.** This machine has no C++ or Kotlin compiler: CI is the only build. The owner play-tests every change in depth on Windows, Linux and Android and reports what is wrong; the owner never edits files or runs tools. Report honestly what was run and what was not (e.g. "desktop not built locally", "not seen on screen").
- Before a multi-file change, state the plan and the list of files.
- Tests of both clients count what the data holds (stamps, static people, tiles of the tileset, the gids of the start tile): grep `desktop/tests/` and `android/core/src/test/` and update them in the same change as the data, or CI fails.

## Where to change what

| To change... | Spec | Reference (Python) | Desktop (C++) | Android (Kotlin) |
|---|---|---|---|---|
| a rule of the simulation (combat, items, farming, chests...) | `docs/spec/04`-`06`, `08`, `10`, `11` | `tools/reference/combat.py`; scenarios in `tools/conformance_m3.py` (save splits in `conformance_m4.py`) | `desktop/src/sim/world.{hpp,cpp}`, `combat.hpp`, `combat_loader.cpp` | `android/core/.../core/sim/World.kt`, `Combat.kt`, `CombatLoader.kt` |
| dialogue conditions and effects, quests | `docs/spec/07` | `tools/reference/story.py` | `desktop/src/sim/story.{hpp,cpp}` | `core/sim/Story.kt` |
| the save document | `docs/spec/12` | `save_state`/`load_state` in `combat.py` | `desktop/src/sim/save.cpp` | `core/sim/Save.kt` |
| the profile (echoes, deeds, reincarnation) | `docs/spec/11`, `12` | `tools/reference/profile.py`, `tools/conformance_profile.py` | `desktop/src/sim/profile.{hpp,cpp}` | `core/sim/Profile.kt` |
| world generation, world time, weather | `docs/spec/08`, `09` | `tools/reference/worldgen.py`, `worldtime.py` | `desktop/src/core/`, `desktop/src/data/world_data.cpp` | `core/WorldTime.kt`, `core/WorldGen.kt` |
| the interface (panels, HUD, title screen, input) | `docs/spec/16` | none | `desktop/src/app/main.cpp` | `android/game/.../game/AethermoorGame.kt` |
| art (recipes, rasterizer) | `docs/spec/13` | `tools/reference/raster.py`, `tools/art_*.py` | `desktop/src/vector/` | `android/core/.../core/vector/`, `game/TextureCache.kt` |

The conformance harnesses that run the vectors are `desktop/tests/conformance_test.cpp` and `android/core/src/test/.../ScenarioSupport.kt` (plus `ConformanceAudioDirectorTest.kt` for the profile): a new field of a scenario needs both. Content (people, quests, items, places) is data written by generators: see `tools/README.md`, "Generators of content".

## Generated files: never edit by hand

| Files | Written by |
|---|---|
| `tests/conformance/*.json` | `tools/gen_conformance.py` (from `tools/reference/` and `tools/conformance_*.py`) |
| `docs/design/catalog.md`, `balance.md`, `translations.md` | `tools/make_catalog.py`, `balance_report.py`, `check_translations.py` |
| the blocks between `<!-- facts:begin -->
| What | How many (counted from the data by `tools/make_facts.py`) |
|---|---|
| World | 8 regions, 45 hand-made sites (dungeons, lairs, outposts, sanctums, Fenwick, the Guest's cottage, Aldermere) and about 130 generated settlements |
| Protagonists | 8, each with a companion (8 companions) and a story of six acts (112 story quests) |
| Creatures | 75, of which 27 guardians and 8 Echoes |
| Quests | 354 (24 tales of the villagers) |
| Items and recipes | 279 items, 81 recipes (8 secret) |
| Progression | 45 titles, 8 tags, 16 talents, 26 deeds |
| Named people | 48 in the world data, besides the generated villagers |
| Sound | 174 synthesized sound effects (music and ambience are off) |
| Texts | 3828 keys, in Italian and English |
| Same rules on both clients | 30 files of conformance vectors, 573 cases, run by the C++ and the Kotlin tests |
| Documents | 18 specs, 13 ADRs |
<!-- facts:end -->` (READMEs, this file, the roadmap) | `tools/make_facts.py` |
| `data/base/art/**`, `fonts/aether.json`, `audio/sfx/`, `stamps/` | the art tools, `make_font.py`, `make_sfx.py`, `make_stamps.py` |
| `recipes.json`, `titles.json`, `tags.json`, `talents.json`, `deeds.json`, `gathering.json`, `companions/`, prologues, stories, towns, tales, pedlars | the `make_*.py` of `tools/README.md` |
| `data/base/tables/xp_table.json`, `maps/demo.tmj` | `gen_tables.py`, `make_demo_map.py` |
| `tests/frames/*.json` (the references of the smoke-test frames) | `tools/check_frames.py --write` from the frames of a CI run |

Many generators also change the role dialogues (`data/base/dialogues/role/`) in place; `tools/make_role_dialogues.py` wrote their first version and must **never** run again (it would write over everything added since). Every other generator was checked to change nothing when run again (see `tools/README.md`, "Running a generator again").

## Commands

```bash
# Python: the virtual environment of docs/dev/setup.md (on this Windows machine: .venv/Scripts/python.exe)
python tools/validate_data.py            # data, schemas, references, texts (always before committing data)
python -m pytest -q tools/tests          # the reference, the content, the documents (links, tools listed, facts)
python tools/gen_conformance.py          # regenerate the vectors (parallel, about 20 s); --check only checks
python tools/make_facts.py               # the numbers of the game in the docs; --check only checks
python tools/make_catalog.py             # docs/design/catalog.md
python tools/balance_report.py           # docs/design/balance.md: fights too hard or too slow (there should be none)
python tools/check_translations.py       # docs/design/translations.md: texts left in the other language

# The art is written by code and saved as JSON (style: docs/design/art-style.md); look at it without the game
python tools/make_art.py tiles props     # also art_chars.py (people), art_creatures.py then make_echoes.py, make_font.py
python tools/art_preview.py --scene --out sheet.html   # PNG pictures drawn by the reference rasterizer; --figures, or a pattern

# Ship a change in one go: checks, signed-off commit, push, PR, wait for CI, squash merge, refresh the play build
python tools/ship.py "feat: title" --body-file body.md --trailer "Co-Authored-By: ..." --play <play folder>
#   --skip-checks after a fix to a CI-only failure (the local checks already passed)

# Desktop (needs CMake >= 3.28, Ninja, vcpkg; see docs/dev/setup.md)
cmake --preset windows-release     # or linux-release
cmake --build --preset windows-release
ctest --preset windows-release

# Android (needs JDK 17+, Android SDK; see docs/dev/setup.md)
cd android && gradle :core:test :app:assembleDebug
```

## Environment notes (the owner's Windows machine)

- No C++ or Kotlin compiler: write C++ and Kotlin carefully and let CI build them. MSVC treats warnings as errors (implicit narrowing such as `size_t` to `float` fails the Windows build): cast explicitly.
- A script whose strings hold a backslash (such as `\n`): create it with the Write tool, not with a shell heredoc (the heredoc loses the backslash).
- A generator may stop with `OSError: [Errno 22] Invalid argument` on a file it has just written (the system holds it for a moment): run it again.
- Every printable character of the stamp legend (`tools/make_stamps.py`) is taken, the Echoes' too: a new meaning goes in the `local` legend of the stamps that use it (`stamp(..., local=...)`), never in the common one (an assert and a test catch a clash).
- The C++ is formatted by `ship.py` (clang-format) before it commits; long comments may be wrapped onto a second line.
- If vcpkg fails to download in CI (a flake), rerun the failed job (`gh run rerun <id> --failed`) and `ship.py --skip-checks`.
- Keep the CI fast: the vcpkg cache key ends with `github.run_id` so that every run saves what it built (an exact key that never changes keeps a stale cache forever and rebuilds SDL3 on every run); if a desktop Configure step takes minutes, look for `Restored 0 package(s)` in its log.
- The desktop CI checks the smoke-test frames (`tools/check_frames.py`). A change that moves them on purpose (a new HUD, new art at the start) fails that step: download the frames of its run (`gh run download <id> -n screenshots-windows-msvc`), look at them, then write the references again with `--write` and push.

## Definition of Done

- [ ] Spec updated (`docs/spec/`) and ADR if architectural
- [ ] Data and schema updated; `python tools/validate_data.py` passes
- [ ] i18n keys present in `it` and `en`
- [ ] Conformance vectors regenerated if rules changed; tests pass on both clients
- [ ] Desktop and Android implemented, or `parity-debt` issue linked and feature gated
- [ ] Generated documents refreshed (`make_catalog.py`, `make_facts.py`) and `pytest` green
- [ ] `CHANGELOG.md` updated for user-visible changes
- [ ] Docs updated in the same PR (spec, `tools/README.md` for a new tool, this file for a new rule of work)

## Style

- C++: `PascalCase` types, `snake_case` functions/variables, `m_name_` members, `kConstant`, namespace `aether`. `clang-format` config in `desktop/.clang-format`.
- Kotlin: the style of ktlint (`intellij_idea`, the rules of `.editorconfig`) and detekt (`android/config/detekt.yml`), both checked in CI by the job `kotlin-style`: trailing commas in multi-line lists, a blank line before a documented property, `if`/`else` with braces when it spans lines. A failure leaves a patch of `ktlint --format` in the artifact `kotlin-style`: see `docs/dev/kotlin-style.md`. Package `io.github.progliodario.aethermoor`.
- Python: ruff (`ruff.toml`); every file written with LF line endings (`newline="\n"`).
- JSON: 2 spaces, `snake_case` keys, `$schema` in every file, fractional values as integers (`_x100`, `_pm`).
- Docs: plain English (Italian for `docs/plan/` and `README.md`), short sentences; no numbers that can go stale outside the facts blocks.
- Commits: Conventional Commits, scope per area, `Signed-off-by` (DCO).
- Branches: `feat/...`, `fix/...`, `docs/...`, `content/...`, `chore/...`. Squash merge.

## Common tasks

- **Add enemy / item / skill / quest / place / region:** follow [`docs/guides/add-content.md`](docs/guides/add-content.md): copy the closest file in `data/base/`, follow its schema in `schemas/`, add i18n keys (it+en), run the validator, regenerate the vectors and the catalog (`tools/gen_conformance.py`, `tools/make_stamps.py`, `tools/make_catalog.py`, `tools/make_facts.py`).
- **Add a named person:** add them to the table of the generator that writes their place (`tools/make_home.py`, `make_towns.py`, `towns_outposts.py`); people must stand on open floor (`tools/tests/test_content.py` checks it) and the clients' tests count them.
- **Add protagonist:** follow the section "A protagonist" of [`docs/guides/add-content.md`](docs/guides/add-content.md) and [spec 18](docs/spec/18-protagonists.md).
- **Change a rule:** `docs/spec` → `tools/reference` → `tools/conformance_m*.py` (a scenario) → `tools/gen_conformance.py` → desktop → android (see "Where to change what").
- **Add a language:** new folder `data/base/i18n/<lang>/`, add it to `pack.json` languages.

## Slash commands (`.claude/commands/`)

`/validate`, `/spec-change`, `/parity-check`.

## Where things stand

The numbers (counted from the data by `tools/make_facts.py`):

<!-- facts:begin -->
<!-- facts:end -->

- **World:** a streamed 16384 x 16384 world with eight regions, generated settlements and hand-made sites: dungeons and lairs with guardians, eight outposts, eight sanctums of the Echoes (`tools/make_echoes.py`), Fenwick (the home village), the Guest's cottage east of it (Old Tam; Nana Brin gives it, flag `cottage_given`) and Aldermere (the guild town). Fenwick, Aldermere and every outpost have named people with quests (`tools/make_towns.py`, `tools/towns_outposts.py`; Nana Brin, Old Tam, Corvin the pedlar and the eight pedlars of the outposts, who sell the goods of a region a day with the condition `day_mod`, are written by `tools/make_home.py`; the eight residents of the outposts, people with `when` who come with the renown of the region and are never solid, by `tools/make_residents.py`, and a settler in every generated village (the role `settler` of `settlements.role_when`, the character `1` of the village stamps), with a trade, a quest and a workshop, by `tools/make_settlers.py`: spec 07, "Residents"; a feast day for every region at its innkeepers, with its games (eight quests), `tools/make_feasts.py`: spec 07, "Feasts"; Odo, the master of the caravan, a person with a `route` who stands at another outpost every day, by `tools/make_caravan.py`, and Brannoc the wandering smith the other way round, by `tools/make_wandering_smith.py`, and Lark the bard who sings of the tales finished, by `tools/make_bard.py`: spec 07, "Travellers"; the shopkeepers temper for gold, `tools/make_smiths.py`, the effect `temper`). Seasons, weather (rain and night hide the player from creatures, rain and snow slow them, the wind of the weather speeds the player, `wind_pm` and `wind_haste_pm`; fog hides the player more, `fog_pm` and `fog_aggro_cut_pm`, and the lightning of storms strikes the creatures that chase the player, `lightning_ticks`; the seasons slow the creatures or hide the player, `creature_slow_pm` and `creature_aggro_cut_pm` of a season: spec 08; seasonal visitors in the fauna, `seasons` of a fauna entry, `tools/make_seasonal_fauna.py`: spec 09; snow in Frostveil), Threshold Stones; the map reveals 5 x 5 cells around the player.
- **People and content:** eight protagonists (Ren, Sakura, Daichi, Haruka, Marco, Yuki, Lena, Gideon: spec 18), each with a prologue, a companion, two personal quests, a story in three acts, an epilogue against their own Echo and a fifth act, "A Life Here", and a sixth, "Two Guests", that ties the protagonists in pairs (`tools/make_stories.py`, `stories_act2.py` to `stories_act6.py`). Tales of the villagers, three per region (`tools/make_region_tales.py`). The content in tables: `docs/design/catalog.md`.
- **Combat:** attack, power strike, dodge, parry, elements, status effects on creatures and on the player, stagger, a guardian bar at the top of the screen. The world difficulty is `enemy_hp_pct` 100 and `enemy_atk_pct` 70: easy on purpose.
- **Progression:** levels, a tree of talents, four of them abilities (whirl, kill_heal, kill_mana, riposte) and two used on command (burst and mend, `use_ability`: `tools/make_talents.py`), titles with effects (attack, gathering, crafting, fine work, parry, experience; one of renown for each region; `tools/make_titles.py`), a bestiary, a status window, a shared `profile.json` with echoes (titles, past lives, deeds), the heirloom of gold and weapon (reincarnation from the title screen at level 10), deeds read from the profile (`data/base/deeds.json`, `tools/make_deeds.py`, spec 11; listed from the title screen with `A`), whose gifts (`reward`) every new game finds in its bag, runes engraved on the worn weapon at an anvil (`runes` in the save, spec 06, `tools/make_furnishings.py`), tags worn one at a time (`data/base/tags.json`, `tools/make_tags.py`, `tag` in the save, `Y` on desktop: spec 11, "Tags").
- **Life:** guild, shops whose prices move with the day (`market_swing_pm`, spec 06), keep wares for friends (`renown_stock`), sell the goods of another region (`open_shop` with a `region`; `tools/make_friend_quests.py` also writes the quest every elder keeps for a friend) and fall with the renown of the region (a counter `renown:<region>` for every quest finished there, and `faction:<id>` for the faction of the quest, spec 07, `tools/set_factions.py`; the condition `faction_at_least`, and the gifts of `tools/make_faction_gifts.py`; `tools/make_renown_talk.py` writes its talk into the role dialogues), inns, gathering, fishing in the reeds of the beaches, farming (garden plots in every village, seeds in every shop, `plots` in the save, a seed sown in the rain grows sooner and the season changes how fast, `season_grow_pm`: spec 06), chests (one in every village and town and in the cottage, all holding the same things, `chest` in the save, the stamp legend `\`: spec 06), animals (a hen coop and a goat pen, gathering nodes), a glut that lowers what shops pay for what you sell too often, hunting (`tools/make_hunting.py`, `tools/make_wildlife.py`), meals that fortify, brews that ward, dishes that regenerate and a brew of haste, an accessory slot, affixes on weapons and armors (`affix`, sixteen regional pieces dropped by the guardians, `tools/make_affixes.py`; a piece found has its affix rolled, `affix_roll`, `rolls` in the save; twenty-four common pieces with an affix and twelve with two, `tools/make_common_affixes.py`, dropped "one of a list", `pick`; the tempering oil rolls the affix of a worn piece again at an anvil, `temper`: spec 05, 06), a cleansing draught, crafting (secret dishes taught by the shopkeepers, `requires_flag`, `tools/make_secret_recipes.py`), two stations (a campfire for dishes, an anvil for fine gear, runes and furniture), the furniture of the cottage (six spots in the house and four in the garden, the characters `1` and `2` of the cottage stamp, `data/base/home.json`; every kind of piece placed adds like a title, `furniture` in the save: spec 06, `tools/make_furnishings.py`) and quality (a recipe can come out fine, spec 06), companions (stay/follow, come back, bond with its moments, care; Haruka's taming and tamed friend, `friend` in the save, spec 10; Yuki's pocket `pocket_keep_pm` and Gideon's `companion_atk_pct`, spec 18).
- **Graphics:** anime art (ADR 0013, spec 13 v2): every recipe is written by a tool (`art_tiles.py`, `art_props.py`, `art_chars.py` with `art_looks.py` and `art_looks_side.py`, `art_creatures.py`) and uses blur, clip, multiply/add and noise fills; people are 4.6 heads tall and seen from the front, from the side and from behind, the ground is painted macro tiles (4 x 4 tiles) that fade into each other (`blend` in the tileset), beasts turn to face the player. The night multiplies the world by a blue and the lights add to it, the wind moves the plants (`sway`), motes drift (spec 08, "The colour of the hour"), water moves and the protagonist swings the arm when striking (spec 13, "Water", "The blow"), props and creatures cast long shadows at dawn and dusk. Textures are baked a few milliseconds a frame after the first frames (spec 13, "Baking in instalments"). A tile is 64 pixels times the density.
- **Interface:** credits and deeds from the title screen, translations checked by `tools/check_translations.py` (a test fails on a text left in the other language), options of accessibility (hints, damage numbers, flashes, large text: `settings.json`, spec 16), hints for the first minutes (`data/base/hints.json`, spec 16, remembered by the story flags `hint_<id>`), three save slots with export and import, Italian and English, configurable keys on the desktop (`keys.json`, the `F4` panel). Both clients draw their text with the font of the pack (`data/base/fonts/aether.json`, `tools/make_font.py`; on Android `PackFont.kt` bakes it into a libGDX font). Panels and bars are drawn by `draw_panel`/`draw_bar` and `drawPanel`/`drawBar`.
- **Sound:** effects are on; music and regional ambience are off (see "How to work").
- **Parity:** feature gating exists (ADR 0009) but is not used: `supported_features` is empty in `project.json` and in both clients, and parity is kept by the shared specs and vectors. Configurable keys are desktop only (Android uses touch).
- The status of the roadmap and what comes next: `docs/plan/06-roadmap-rischi-backlog.md`, section 8.
