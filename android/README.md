# Android client

Kotlin + libGDX, Android 11+ (minSdk 30). Three Gradle modules:

| Module | Type | Purpose |
|---|---|---|
| `core` | Kotlin/JVM | Simulation, data, world generation. No Android or libGDX imports. Tested on the JVM. |
| `game` | Android library | libGDX layer: rendering, audio, input, UI |
| `app` | Android application | Launcher activity, manifest, bundles `../data` as assets |

Name, version and application id come from `../project.json`. See [`docs/dev/setup.md`](../docs/dev/setup.md).

```bash
gradle wrapper --gradle-version 8.10.2   # once, generates gradlew
./gradlew :core:test
./gradlew :app:assembleDebug
```

M0 note: the Gradle wrapper is not committed yet (it was not generated in this environment). CI uses the Gradle version pinned in `.github/workflows/ci-android.yml`. Commit the wrapper once generated.
