# Development setup

The map of the code is [`architecture.md`](architecture.md); the way to carry a change from the spec to both clients and ship it is
[`docs/guides/continue-the-work.md`](../guides/continue-the-work.md).

## Common

- Git, Python 3.12+ (3.13 works).
- Data validation:

```bash
python -m venv .venv
.venv/Scripts/pip install -r tools/requirements.txt    # Linux/macOS: .venv/bin/pip
.venv/Scripts/python tools/validate_data.py
```

- Optional: [pre-commit](https://pre-commit.com/) (`pip install pre-commit && pre-commit install`).

## Desktop (Windows / Linux)

Requirements: CMake >= 3.28, Ninja, a C++20 compiler (MSVC 2022, GCC >= 13, Clang >= 17), [vcpkg](https://vcpkg.io/).

```bash
# once: clone vcpkg and set VCPKG_ROOT
cmake --preset windows-release        # Linux: linux-release
cmake --build --preset windows-release
ctest --preset windows-release
```

Linux system packages for SDL3 come through vcpkg, but you still need X11/Wayland, ALSA/PulseAudio/PipeWire dev headers. See vcpkg's SDL3 notes for the exact list.

## Android

Requirements: JDK 17 or newer, Android Studio (or command-line SDK with platform 35), Gradle.

```bash
cd android
gradle wrapper --gradle-version 8.10.2    # once, generates gradlew
./gradlew :core:test
./gradlew :app:assembleDebug
```

Set `ANDROID_HOME` or create `android/local.properties` with `sdk.dir=...`.

## Verification

CI (`.github/workflows/`) runs on every pull request and on pushes to `main`:

| Workflow | What it does |
|---|---|
| `ci-data` | `ruff check tools`, `tools/validate_data.py` (the base pack and the example mod), `pytest tools/tests`, `gen_conformance.py --check`, `make_save_fixtures.py --check`, `make_parity.py --check`, `make_suites_map.py --check`, `licenses.py --check` |
| `ci-desktop` | on Windows (MSVC) and Linux (GCC): vcpkg (binary cache), configure, build, `ctest` (unit tests, every conformance suite, the performance test, three smoke tests), prints the numbers of the performance test ([`../design/performance.md`](../design/performance.md)), checks the smoke-test frames against `tests/frames/` (`tools/check_frames.py`), then packages the playable build and uploads it with the frames. Also called by `release` |
| `ci-android` | job `build`: JDK 17, Gradle 8.10.2, `:core:test` (JVM tests, including every conformance suite and the performance test, whose numbers it prints), `:app:assembleDebug`, uploads the debug APK; job `kotlin-style`: ktlint and detekt ([`kotlin-style.md`](kotlin-style.md)). Also called by `release` |
| `nightly` | every night on `main`, by hand, and on a pull request that changes it, `android/app/src/androidTest/` or the chunk store of the desktop: the game on an Android emulator of API 30 and of API 34 (start, rotation, pause and resume; [`../design/performance.md`](../design/performance.md)), and the streaming thread of the desktop under ThreadSanitizer (clang, the packages of Ubuntu, CMake options `AETHER_HEADLESS_ONLY=ON` and `AETHER_WERROR=OFF`: only the headless libraries and their tests) |
| `labeler` | labels the pull request from the paths it touches |
| `release` | on a `v*` tag, or by hand for a dry run: checks the data and that the tag is the version of `project.json`, builds every package with `ci-desktop` and `ci-android`, names the files after the version, writes `SHA256SUMS` and the bill of materials (SPDX, `tools/licenses.py --sbom`) and checks the sums; on a tag it creates a **draft** release with all the files (never published: the owner publishes) |

Local builds need the tools above; the project is developed on a machine without a C++ or Kotlin compiler, so for those two clients CI is the only build and a change to C++ or Kotlin is checked by pushing it. `python tools/gen_conformance.py --check` (are the committed vectors the ones the reference generates?) also runs in CI (`ci-data`), and in `tools/ship.py` before it commits.

## Before you open a pull request

```bash
python tools/validate_data.py
python -m ruff check tools
python -m pytest tools/tests -q
python tools/gen_conformance.py --check      # regenerate with the same command, without --check, after a rule or world-data change
```

If you changed data, also look at the tests that count it (`desktop/tests/combat_test.cpp`, `desktop/tests/sim_test.cpp`, `android/core/src/test/.../WorldGenTest.kt` and `WorldTest.kt`: number of stamps, static people, tiles of the tileset, the gid of the start tile), because they fail in CI only.

## Notes for Windows

- The working tree may show `CRLF will be replaced by LF` warnings: the repository stores LF (`.gitattributes`), Git converts on commit.
- A Python script with a backslash escape in a string, written through a shell heredoc, may lose the backslash: put such a script in a file.

## Tools

All of them are Python scripts in `tools/`; use the virtual environment of the "Common" section.

| Command | What it does |
|---|---|
| `python tools/validate_data.py` | validates the data of the packs against the schemas and the texts of both languages |
| `python tools/gen_conformance.py` (`--check`) | writes (checks) the conformance vectors of `tests/conformance/`, in parallel, about 20 s |
| `python tools/make_stamps.py` (`--show`) | writes `data/base/stamps/` from the templates in the script, and draws them with `--show` |
| `python tools/art_preview.py <pattern> --out sheet.html` | draws art recipes as an HTML sheet, to look at them without the game |
| `python tools/make_catalog.py` | writes `docs/design/catalog.md` (regions, creatures, items, quests, sites) |
| `python tools/make_facts.py` (`--check`) | writes the numbers of the game, counted from the data, into the facts blocks of the READMEs, `CLAUDE.md` and the roadmap |
| `python tools/balance_report.py` | writes `docs/design/balance.md`, a rough model of every fight |
| `python tools/ship.py "<title>" --body-file <file> [--play <folder>]` | checks, commits, pushes, opens the pull request, waits for CI, merges, deletes the branch and the old CI caches, and refreshes the play folder (`../aethermoor-play` by default) |
| `clang-format -i <file>` (from the virtual environment) | formats C++ with `desktop/.clang-format` (120 columns); `ship.py` does it for the C++ files it commits |
| `python -m pytest tools/tests` and `python -m ruff check tools` | the tests of the reference and of the data, and the linter |

To see real frames of the game: `aethermoor --smoke-test --map=world --seed=7 --start=<x>,<y> --screenshot-dir=<folder>` writes PNG screenshots (walking, bag, map) at a place of the world; `--hour=22` shows it at night.
