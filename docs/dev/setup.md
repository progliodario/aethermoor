# Development setup

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
| `ci-data` | `ruff check tools`, `tools/validate_data.py`, `pytest tools/tests`, `gen_conformance.py --check` |
| `ci-desktop` | on Windows (MSVC) and Linux (GCC): vcpkg (binary cache), configure, build, `ctest` (unit tests, every conformance suite, three smoke tests), then packages the playable build and uploads it with the smoke-test frames |
| `ci-android` | JDK 17, Gradle 8.10.2, `:core:test` (JVM tests, including every conformance suite), `:app:assembleDebug`, uploads the debug APK |
| `labeler` | labels the pull request from the paths it touches |
| `release` | on a `v*` tag: validates the data and creates a draft release (no artifacts yet) |

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
| `python tools/balance_report.py` | writes `docs/design/balance.md`, a rough model of every fight |
| `python tools/ship.py "<title>" --body-file <file> [--play <folder>]` | checks, commits, pushes, opens the pull request, waits for CI, merges, and refreshes a play folder |
| `clang-format -i <file>` (from the virtual environment) | formats C++ with `desktop/.clang-format` (120 columns); `ship.py` does it for the C++ files it commits |
| `python -m pytest tools/tests` and `python -m ruff check tools` | the tests of the reference and of the data, and the linter |

To see real frames of the game: `aethermoor --smoke-test --map=world --seed=7 --start=<x>,<y> --screenshot-dir=<folder>` writes PNG screenshots (walking, bag, map) at a place of the world.
