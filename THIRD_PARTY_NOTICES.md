# Third-party notices

This file is kept by hand until `tools/licenses.py` (planned) generates it. These are the dependencies the build uses today; any new one must be compatible with GPL-3.0-or-later.

## Desktop (`desktop/vcpkg.json`)

| Component | License | Used for |
|---|---|---|
| SDL3 | zlib | window, renderer, input, gamepad, the debug font |
| nlohmann/json | MIT | reading data and saves |
| Catch2 | BSL-1.0 | tests only |

Vector art uses an in-house software rasterizer (ADR 0012). ThorVG, SDL3_ttf and miniz, named in the early plan, are not used.

## Android (`android/gradle/libs.versions.toml`)

| Component | License | Used for |
|---|---|---|
| libGDX (`gdx`, `gdx-backend-android`) | Apache-2.0 | drawing, input, the activity |
| Kotlin and kotlinx.serialization | Apache-2.0 | all the code, JSON |
| Android Gradle Plugin | Apache-2.0 | build only |
| JUnit | EPL-2.0 | tests only |

## Tools (`tools/requirements.txt`, development only, not shipped)

| Component | License |
|---|---|
| jsonschema | MIT |
| pytest | MIT |
| ruff | MIT |
| clang-format (PyPI wheel) | Apache-2.0 with LLVM exceptions |

## Fonts and art

The game ships no font file and no image: the art is JSON recipes drawn by the game (content: CC BY-SA 4.0, see `LICENSE-CONTENT.md`), and the text uses the fonts built into the libraries (the debug font of SDL on desktop, the default bitmap font of libGDX on Android).
