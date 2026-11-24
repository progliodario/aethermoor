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

## A session, from start to end

1. **Start clean.** `git checkout main && git pull`; `git status` is clean and `gh pr list` shows no open pull request (if one is open, finish
   it first: read its checks, fix, ship). Read the notes of [`docs/plan/06-roadmap-rischi-backlog.md`](docs/plan/06-roadmap-rischi-backlog.md),
   section 8.4: the first items of "A breve" are the next work.
2. **One branch for the whole batch** (`feat/...`, `content/...`, `chore/...`). Do several items of 8.4, each the whole way (spec, reference,
   vectors, both clients, data, texts in `it` and `en`, client tests that count the data).
3. **Before shipping:** run the generators the change needs (see "Generated files"), then `make_catalog.py` and `make_facts.py`; add the change
   to `CHANGELOG.md` (section `[Unreleased]`), take the items done out of 8.4 "A breve" and add them to 8.3, in Italian.
4. **Ship:** `python tools/ship.py "<title>" --body-file <body> --trailer "Co-Authored-By: ..."`. It runs the checks, opens the pull request,
   waits for CI, squash merges, deletes the branch (local and remote), prunes the old CI caches and copies the Windows build into the
   play folder (`../aethermoor-play`, when it exists). If CI fails, fix on the same branch and run it again (`--skip-checks` when only CI failed).
5. **Tell the owner** what changed in the game, what was checked (CI, tests) and what was not (nothing is seen on screen from here).

## Pitfalls already met

- A new field of the save needs a split in `SAVE_SPLITS` of `tools/conformance_m4.py` and must be restored before anything that reads it
  (the world ticks come back before the creatures of the stream, which depend on the season); then `tools/make_save_fixtures.py` appends
  its case to the frozen copy `tests/saves/v<N>.json`. A change that old saves cannot read bumps `SAVE_VERSION` (reference) and
  `kSaveVersion`/`SAVE_VERSION` (clients) with a migration in all three, and writes the copy of the new version (spec 12).
- A new dependency needs its row in `tools/licenses.json` (`ci-data` fails without it); a new suite of vectors needs a test in both
  clients (`tools/make_parity.py --check`).
- A new kind of dialogue file must not reuse an id: the dialogue of a person is `npc/<id>.json`, and a new person named like an old one
  overwrites it (`test_every_person_of_the_world_has_a_dialogue_of_its_own`).
- Generators that patch JSON must parse it (`json.loads`), never cut it at the first `]`: lists nest (`seasons` of a fauna entry, `pick` of a drop).
- C++ aggregates (`DropDef`, `QuestDef`...) need every field in brace initializers: GCC fails on `missing-field-initializers`.
- detekt fails on a function grown too complex (`CyclomaticComplexMethod`): take a branch out into a function of its own. ktlint wants the
  arguments of a call one per line once they do not fit on one.
- The client tests count drops, people, stamps and tiles: a new drop or person changes `desktop/tests/` and `android/core/src/test/`.

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
| the facts blocks (between the comments `facts:begin` and `facts:end`: READMEs, this file, the roadmap) | `tools/make_facts.py` |
| `data/base/art/**`, `fonts/aether.json`, `audio/sfx/`, `stamps/` | the art tools, `make_font.py`, `make_sfx.py`, `make_stamps.py` |
| `recipes.json`, `titles.json`, `tags.json`, `talents.json`, `deeds.json`, `gathering.json`, `companions/`, prologues, stories, towns, tales, pedlars | the `make_*.py` of `tools/README.md` |
| `data/base/tables/xp_table.json`, `maps/demo.tmj` | `gen_tables.py`, `make_demo_map.py` |
| `tests/frames/*.json` (the references of the smoke-test frames) | `tools/check_frames.py --write` from the frames of a CI run |
| `docs/design/parity.md`, `THIRD_PARTY_NOTICES.md` | `tools/make_parity.py`, `tools/licenses.py` (from `tools/licenses.json`, which is edited by hand) |
| `tests/saves/v*.json` (the frozen saves of every version: **never** changed, only appended to) | `tools/make_save_fixtures.py` |

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

# Ship a change in one go: checks, signed-off commit, push, PR, wait for CI, squash merge, tidy branch and CI caches, refresh the play build
python tools/ship.py "feat: title" --body-file body.md --trailer "Co-Authored-By: ..."   # --play DIR, default ../aethermoor-play
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
| What | How many (counted from the data by `tools/make_facts.py`) |
|---|---|
| World | 8 regions, 45 hand-made sites (dungeons, lairs, outposts, sanctums, Fenwick, the Guest's cottage, Aldermere) and about 130 generated settlements |
| Protagonists | 8, each with a companion (8 companions) and a story of six acts (120 story quests) |
| Creatures | 79, of which 27 guardians and 8 Echoes |
| Quests | 407 (24 tales of the villagers) |
| Items and recipes | 286 items, 82 recipes (8 secret) |
| Progression | 49 titles, 8 tags, 16 talents, 29 deeds |
| Named people | 56 in the world data, besides the generated villagers |
| Sound | 174 synthesized sound effects (music and ambience are off) |
| Texts | 4211 keys, in Italian and English |
| Same rules on both clients | 31 files of conformance vectors, 609 cases, run by the C++ and the Kotlin tests |
| Documents | 19 specs, 14 ADRs |
<!-- facts:end -->

- **What the game holds:** every creature, item, quest and site is in [`docs/design/catalog.md`](docs/design/catalog.md); the systems,
  area by area, in section 8.3 of the roadmap; the rules in `docs/spec/`. Which generator writes which content: [`tools/README.md`](tools/README.md).
- **What comes next:** section 8.4 of the roadmap, "A breve" first; the program of the batches, with the files and the acceptance of every item, is in [`docs/plan/07-programma-operativo.md`](docs/plan/07-programma-operativo.md), and every item is a GitHub issue in a milestone.
- **Difficulty:** `enemy_hp_pct` 100 and `enemy_atk_pct` 70 (easy on purpose, see "How to work").
- **Sound:** effects are on; music and regional ambience are off.
- **Parity:** feature gating exists (ADR 0009) but is not used: `supported_features` is empty in `project.json` and in both clients; parity is
  kept by the shared specs and vectors. Configurable keys are desktop only (Android uses touch).
- **Kotlin style debt:** detekt keeps the findings of the old code in `android/config/detekt-baseline.xml`; shrink it, never grow it.
