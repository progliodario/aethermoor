# Third-party notices

Written by `tools/licenses.py` from `tools/licenses.json`: do not edit by hand. These are the dependencies the build uses; any new
one must have a row in the table, with a license compatible with GPL-3.0-or-later (`ci-data` runs `tools/licenses.py --check`).

## Desktop (`desktop/vcpkg.json`)

| Component | License | Where | Used for |
|---|---|---|---|
| SDL3 (`sdl3`) | Zlib | in the game | window, renderer, input, gamepad, the fallback font |
| nlohmann/json (`nlohmann-json`) | MIT | in the game | reading data and saves |
| Catch2 (`catch2`) | BSL-1.0 | tests only | the tests of the desktop |

## Android (`android/gradle/libs.versions.toml`, `android/*/build.gradle.kts`)

| Component | License | Where | Used for |
|---|---|---|---|
| libGDX (`com.badlogicgames.gdx:gdx`) | Apache-2.0 | in the game | drawing, input |
| libGDX Android backend (`com.badlogicgames.gdx:gdx-backend-android`) | Apache-2.0 | in the game | the activity, the GL surface |
| libGDX natives (`com.badlogicgames.gdx:gdx-platform`) | Apache-2.0 | in the game | the native libraries of libGDX (arm64-v8a, x86_64) |
| kotlinx.serialization (`org.jetbrains.kotlinx:kotlinx-serialization-json`) | Apache-2.0 | in the game | JSON: data and saves |
| JUnit (bill of materials) (`org.junit:junit-bom`) | EPL-2.0 | tests only | the versions of JUnit |
| JUnit Jupiter (`org.junit.jupiter:junit-jupiter`) | EPL-2.0 | tests only | the tests of Android |
| JUnit Platform Launcher (`org.junit.platform:junit-platform-launcher`) | EPL-2.0 | tests only | running the tests of Android |
| Android Gradle Plugin (`com.android.application`) | Apache-2.0 | build only | building the APK |
| Android Gradle Plugin (library) (`com.android.library`) | Apache-2.0 | build only | building the game module |
| Kotlin (Android) and its standard library (`org.jetbrains.kotlin.android`) | Apache-2.0 | in the game | all the code of Android |
| Kotlin (JVM) and its standard library (`org.jetbrains.kotlin.jvm`) | Apache-2.0 | in the game | the core module |

## Tools (`tools/requirements.txt` and the workflows; development only, not shipped)

| Component | License | Where | Used for |
|---|---|---|---|
| jsonschema (`jsonschema`) | MIT | development only | checking the data against the schemas |
| pytest (`pytest`) | MIT | development only | the tests of the tools |
| ruff (`ruff`) | MIT | development only | the style of the Python |
| clang-format (PyPI wheel) (`clang-format`) | Apache-2.0 WITH LLVM-exception | development only | the style of the C++ |
| ktlint (`pinterest/ktlint`) | MIT | development only | the style of the Kotlin, in CI |
| detekt (`detekt/detekt`) | Apache-2.0 | development only | the checks of the Kotlin, in CI |

Vector art uses an in-house software rasterizer (ADR 0012). ThorVG, SDL3_ttf and miniz, named in the early plan, are not used.

## Fonts and art

The game ships no image file: the art is JSON recipes drawn by the game. The font of the interface is `data/base/fonts/aether.json`,
written by the project's own tool (`tools/make_font.py`) as strokes, not a font of another author. Art and font are content under
CC BY-SA 4.0 (see `LICENSE-CONTENT.md`). The debug font of SDL is only a fallback on desktop; Android builds a libGDX bitmap font
from the pack font.
