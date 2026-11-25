# Architecture

The map of the project: what each folder holds, how the layers depend on each other, and how a rule, a piece of content or a picture
travels from its source to the screen of both clients. The why of the big choices is in the [ADRs](../adr/README.md); the rules of
work are in [`CLAUDE.md`](../../CLAUDE.md); how to carry a change through all of this is in
[`docs/guides/continue-the-work.md`](../guides/continue-the-work.md).

## 1. The big picture

```
                 docs/spec/  (the rules, in English, normative)
                     │
        ┌────────────┴─────────────┐
        ▼                          ▼
 tools/reference/ (Python)    data/base/ (JSON content, written mostly by tools/make_*.py)
        │  runs the scenarios          │  read by both clients and by the reference's tests
        ▼  of tools/conformance_*.py   │
 tests/conformance/*.json  ◄───────────┘
 (the vectors: inputs and expected outputs)
        │
        ├──────────────► desktop/tests/conformance_test.cpp  ─► desktop/src/  (C++20, SDL3)
        └──────────────► android/core/src/test/.../*.kt      ─► android/      (Kotlin, libGDX)
```

- **One behavior, two codebases.** The desktop client and the Android client share no code: they share the specs, the data and the
  vectors. Each client has a headless simulation (`WorldSim`) that both its game and its tests drive.
- **The Python reference is the truth.** A rule is first written in `tools/reference/`, exercised by a scenario, and its results are
  frozen as vectors; each client runs every vector and must match within the tolerance of the case.
- **Content is data.** Creatures, items, quests, dialogues, places, art, sounds and texts are JSON under `data/base/`, validated by the
  schemas of `schemas/`. Most of it is written by generators in `tools/`, never by hand.

## 2. Folders

| Folder | What it holds | Written by |
|---|---|---|
| `data/base/` | the base pack: `pack.json`, content by kind (`items/`, `enemies/`, `quests/`, `dialogues/`, `stamps/`, `worlds/`, `art/`, `audio/`, `i18n/it`, `i18n/en`...) and single documents (`home.json`, `defense.json`, `recipes.json`, `titles.json`...) | the generators of `tools/` (see [`tools/README.md`](../../tools/README.md)); a few files by hand |
| `schemas/` | one JSON schema per kind of document | by hand |
| `docs/spec/` | the rules, one document per area (00 conventions ... 18 protagonists) | by hand |
| `docs/plan/` | the plan of the project, the roadmap (06) and the operating program (07), in Italian | by hand, plus the facts block |
| `docs/design/` | the art style, and generated reports: catalog, balance, translations, parity, suites | the tools named in each file |
| `docs/adr/` | the architecture decisions | by hand |
| `docs/dev/`, `docs/guides/`, `docs/modding/` | setup, style, release, accessibility, this file; how to add content and continue; mods | by hand |
| `tools/` | the Python reference, the scenarios, the generators, the checks, `ship.py` | by hand |
| `tools/tests/` | pytest: the reference, the content, the documents, the checks | by hand |
| `tests/conformance/` | the vectors, one file per suite | `tools/gen_conformance.py` |
| `tests/saves/` | the frozen saves of every version, append-only | `tools/make_save_fixtures.py` |
| `tests/frames/` | the references of the smoke-test frames of the desktop | `tools/check_frames.py --write` |
| `desktop/` | the C++ client: `src/`, `tests/`, `CMakeLists.txt`, `vcpkg.json` | by hand |
| `android/` | the Kotlin client: `core/` (headless), `game/` (libGDX), `app/` (the Android launcher) | by hand |
| `examples/mod-example/` | a small mod, checked in CI | by hand |
| `.github/` | the workflows, the issue and pull request templates, the labels | by hand |

## 3. The desktop client (`desktop/`)

CMake builds five static libraries and two executables (`desktop/CMakeLists.txt`). The arrows are the allowed dependencies: the four
first libraries are **headless** (no SDL, no graphics, no input), as rule 10 of `CLAUDE.md` asks.

```
aether_core ◄── aether_data ◄── aether_sim ◄── aethermoor (the game, src/app/)
     ▲              ▲                              ▲
     ├── aether_vector (rasterizer)  ───────────────┤
     └── aether_audio  (synthesizer) ───────────────┘
aether_tests (tests/*.cpp) links all five libraries
```

| Library | Files | What they do |
|---|---|---|
| `aether_core` (`src/core/`) | `numerics` (PCG32, hashes, Q16.16, noise), `rules` (damage, stats, xp), `worldgen` (regions, settlements, landmarks, chunks), `worldtime` (days, seasons, weather), `travel.hpp` (the walk of the travellers), `message_format` (plurals of the texts), `id`, `version` | the deterministic math and the generation of the world |
| `aether_data` (`src/data/`) | `pack` (reading a pack and its texts), `protagonist`, `world_data` (the world document), `lights`, `font`, `hints`, `crash_log` | loading the data |
| `aether_vector` (`src/vector/`) | `recipe`, `raster`, `rig` | the art recipes drawn to bitmaps, the rigs of the people (spec 13) |
| `aether_audio` (`src/audio/`) | `synth`, `events`, `director`, `music` | the sound effects synthesized from data (spec 14) |
| `aether_sim` (`src/sim/`) | `world` (`WorldSim`: the whole simulation), `combat` (the definitions: `CombatSetup`, `ItemDef`, `EnemyDef`, `DefenseDef`...), `combat_loader` (from a pack to a `CombatSetup`), `story` (dialogues, quests, effects, the `StoryHost` interface), `movement`, `tilemap`, `chunk_store` (the streamed world), `world_map`, `save`, `save_bundle`, `profile` | the game without the screen |
| the game (`src/app/`) | `main.cpp` (the window, the input, every panel and the HUD, the title screen, the saves on disk), `texture_cache`, `sound_board`, `features.hpp` | presentation only |

`main.cpp` is long (about 6000 lines) and organised by function: `bag_use`, `handle_craft_key` and `draw_craft`, `draw_hud`,
`run_title`, `run_game` and `main` (which writes the crash log). Search for the function of a panel rather than reading it in order.

## 4. The Android client (`android/`)

| Module | Package | Files | What they do |
|---|---|---|---|
| `core` (pure JVM, no libGDX) | `core` | `Numerics`, `Rules`, `WorldGen`, `WorldTime`, `Travel`, `Pack`, `Protagonist`, `MessageFormat`, `Strings`, `Ids`, `Hints`, `Lights`, `Font`, `GameInfo`, `Features`, `CrashLog` | the same as `aether_core` and `aether_data` |
| | `core.sim` | `World` (`WorldSim`), `Combat`, `CombatLoader`, `Story`, `Movement`, `TileMap`, `ChunkStore`, `WorldMap`, `Save`, `SaveBundle`, `Profile` | the same as `aether_sim` |
| | `core.vector`, `core.audio` | `Recipe`, `Raster`, `Rig`; `Synth`, `EventTable`, `Director`, `Music` | the same as `aether_vector` and `aether_audio` |
| `game` (libGDX) | `game` | `AethermoorGame` (every screen, panel and button), `InputController` (touch and keys), `TextureCache`, `SoundBoard`, `PackFont`, `GdxPackSource` | the same as `src/app/` |
| `app` | `app` | `AndroidLauncher` | the Android entry point |

The tests of `core` (`android/core/src/test/`) are JUnit 5: `ConformanceTest`, `ConformanceM2Test`, `CombatTest`, `WorldGenTest`,
`WorldTest`, `ConformanceAudioDirectorTest`, `PackTest`, `GameInfoTest`, `CrashLogTest`, with the scenario harness in
`ScenarioSupport.kt`. The style of the Kotlin is checked by ktlint and detekt ([`kotlin-style.md`](kotlin-style.md)).

## 5. The simulation

`WorldSim` is the same object in both clients and `CombatSim` in the reference. It is built from a **setup** (`CombatSetup`: what the
data says, loaded by `combat_loader` / `CombatLoader`, or parsed from a scenario by the harnesses), and advanced one **tick** at a time
(60 per second, spec 03). The order of a tick:

1. in a streamed world, the window of chunks around the player and the explored cells (spec 09); the clock of the world
   (`world_ticks`), the travellers (spec 07), the quests that collect (the bag counted again);
2. nothing more while a dialogue is open;
3. the counters of the player (invulnerability, cooldowns, the death save, the abilities), mana, the status effects on the player;
4. the parry, the roll or the movement of the player, then the start of an attack;
5. the attack in progress (`advance_attack`: hits, damage, kills);
6. the companion, then the tamed friend (spec 10);
7. every creature, in the order of the list (statuses, behavior, the march of the defense: spec 05, 18);
8. the defense of Gideon's Dungeon (spec 18): traps, core, waves;
9. the lightning of a storm (spec 08);
10. the status effects of the player that wear off, and the regeneration.

The streamed world (spec 09) keeps 5 x 5 chunks around the player (`ChunkStore`); creatures come from the spawners of those chunks and
leave with them. The story (`Story`) holds the flags, the gold, the quests and the dialogue; it talks to the simulation through the
`StoryHost` interface (`grant_xp`, `heal_full`, `temper_worn`, `recruit_companion`, `start_defense`...). The client drives it with
`interact`, `choose` and `advance`.

**Saves** (spec 12): `WorldSim::capture` writes a `SaveState`, `save.cpp` / `Save.kt` turn it into JSON, and `restore` reads it back.
Optional fields are absent when they hold nothing, so the version changes only when an old save could not be read
(`SAVE_VERSION`, with a migration in all three codebases).

## 6. The reference and the vectors

| File | What it holds |
|---|---|
| `tools/reference/combat.py` | `CombatSim` (the simulation), `run_scenario`, `run_with_save`, `run_from_save`, `save_state`, `load_state` |
| `tools/reference/story.py` | the story: conditions, effects, quests, travellers |
| `tools/reference/worldgen.py`, `worldtime.py`, `numerics.py`, `rules.py`, `movement.py` | the world, the time, the math, the damage, the movement |
| `tools/reference/raster.py`, `pose.py`, `audio.py`, `audio_director.py`, `music.py` | the pictures, the rigs, the sounds |
| `tools/reference/profile.py`, `savebundle.py`, `guild.py`, `routines.py`, `i18n.py`, `ids.py` | the profile, the save bundle, the guild board, the people's day, the texts |
| `tools/conformance_m2.py` ... `conformance_m5.py`, `conformance_audio.py`, `conformance_music.py`, `conformance_profile.py`, `conformance_savebundle.py` | the scenarios and the cases of each suite; `SAVE_SPLITS` in `conformance_m4.py` |
| `tools/gen_conformance.py` | writes `tests/conformance/*.json` from all of them, in parallel |

A **scenario** is a small map (`grid`), a list of creatures, a setup (items, story, companions, defense...) and a **script** of
segments (ticks with an input, and commands such as `use`, `equip`, `interact`, `choose`, `choose_affix`, `companion_switch`). Its
**checkpoints** (one per segment) are what the clients must reproduce. The harnesses read the same JSON: `scenario_from_json` and
`check_checkpoint` in `desktop/tests/conformance_test.cpp`, `scenarioFromJson` and `assertCheckpoint` in `ScenarioSupport.kt`. A new
field of a scenario or of a checkpoint is added in the three places.

## 7. Content and art

- **Generators.** Each kind of content has its generator (`tools/make_*.py`): it holds the tables (names, numbers, texts in `en` and
  `it`) and writes the JSON, the texts and sometimes a line of the world data. Run again, a generator changes nothing; the list is in
  [`tools/README.md`](../../tools/README.md), "Generators of content". The role dialogues were written once by
  `make_role_dialogues.py`, which must never run again.
- **Art.** `tools/art_props.py`, `art_tiles.py`, `art_chars.py`, `art_creatures.py`, `art_looks.py` write the recipes of
  `data/base/art/**` through `tools/make_art.py`; both clients rasterize them at run time with the same algorithm as
  `tools/reference/raster.py` (spec 13). `tools/art_preview.py` draws them to PNG.
- **Places.** `tools/make_stamps.py` writes the stamps (hand-made pieces of the world drawn with characters); a landmark of the world
  data places a stamp at a fixed point from the centre of the world (spec 09).
- **Texts.** `data/base/i18n/en/` and `it/` (`core.json` for the interface and the people, `content.json` for the content,
  `roles.json` for the role dialogues). Every visible text is a `$i18n:` key present in both.

## 8. Continuous integration

| Workflow | Job | What it checks |
|---|---|---|
| `ci-data` | `validate` | ruff, `validate_data.py` (the base pack and the example mod), pytest, `gen_conformance.py --check`, `make_save_fixtures.py --check`, `make_parity.py --check`, `make_suites_map.py --check`, `licenses.py --check` |
| `ci-desktop` | `windows-msvc`, `linux-gcc` | vcpkg (cached), configure, build, `ctest` (unit tests, every conformance suite, the performance test, three smoke tests), the smoke-test frames against `tests/frames/`, the playable build and the frames as artifacts |
| `ci-android` | `build` | `:core:test` (JVM tests, every conformance suite, the performance test), `:app:assembleDebug`, the debug APK as an artifact |
| | `kotlin-style` | ktlint and detekt (with `android/config/detekt-baseline.xml`) |
| `nightly` | `emulator (API 30)`, `emulator (API 34)`, `thread sanitizer (streaming)` | the game on an Android emulator: start, rotation, pause and resume (`android/app/src/androidTest/`); the tests `[streaming]` of the desktop under ThreadSanitizer |
| `labeler` | `label` | labels the pull request from its paths |
| `release` | `validate`, `desktop`, `android`, `package` | on a `v*` tag or by hand: the packages (with `ci-desktop` and `ci-android`, called), `SHA256SUMS`, the SBOM, a draft release on a tag |

`tools/ship.py` waits for all the checks of the pull request before it merges (`nightly` runs on a pull request only when it changes the
workflow or the test on the emulator; `release` never runs on a pull request).
