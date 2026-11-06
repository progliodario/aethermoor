# Android client

Kotlin and libGDX, Android 11+ (minSdk 30), portrait and landscape. Three Gradle modules:

| Module | Type | Purpose |
|---|---|---|
| `core` | Kotlin/JVM | Everything that is not drawing: numerics, rules, world generation and time, the story engine, combat, saves, the pack loader, the vector rasterizer and rigs. No Android or libGDX imports; tested on the JVM against the shared conformance vectors. |
| `game` | Android library | The libGDX layer (`AethermoorGame`): rendering, the HUD and panels, touch input (`InputController`), the texture cache, reading the pack from the assets (`GdxPackSource`) |
| `app` | Android application | The launcher activity, the manifest, and the bundling of `../data` as assets |

Name, version and application id come from `../project.json`. Setup: [`docs/dev/setup.md`](../docs/dev/setup.md). The desktop client has the same features; the two clients are kept equal by the specs and the vectors (`docs/spec/`, `tests/conformance/`).

```bash
cd android
gradle :core:test
gradle :app:assembleDebug
```

The Gradle wrapper is not committed (it was never generated on the machine the project is developed on). CI uses the Gradle version pinned in `.github/workflows/ci-android.yml` (8.10.2); with a local Gradle of that version, `gradle wrapper --gradle-version 8.10.2` generates `gradlew` if you prefer it. CI uploads the debug APK as the artifact `aethermoor-debug-apk`.

## Controls

A floating stick on the left half of the screen moves (the first touch is its origin, 64 dp gives full speed); any touch on the right half attacks. Buttons on the screen open the bag, the world map, the journal and switch the language; a talk button appears next to people; in the bottom right corner, a Dodge button, a Strike button (the power strike, while there is mana) and an Analyze button (only for Ren); a tap on the small map in the corner opens the world map; a new game first asks who to be (a tap selects, a second tap confirms); lists (bag, shop, board, stones, journal) are scrolled and chosen by touch. The Back key saves the game and returns to the list of games. A physical keyboard works as on desktop (`WASD`, `J`, `E`, `I`, `Q`, `M`, `F2`). The full list is in [spec 16](../docs/spec/16-input.md).

## State

Compiled and unit-tested by CI (JVM tests of `core`, including all the conformance vectors, and `assembleDebug`). It has not been run on a device or an emulator yet: what the screen looks like and how the touch controls feel is unverified, and the visual changes are written to mirror the desktop ones without having been looked at.

## Tests

`core/src/test/kotlin/...`: the conformance suites (`ConformanceTest`, `ConformanceM2Test`), combat and story scenarios (`CombatTest`), the pack (`PackTest`), world generation (`WorldGenTest`) and the world and the tileset (`WorldTest`). Some of them count what the data holds (stamps, people, tiles): when you add content, update them.
