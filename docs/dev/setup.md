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

CI builds and tests the desktop client on Windows (MSVC) and Linux (GCC) and the Android client (JVM unit tests and `assembleDebug`). Local builds need the tools above; the project was developed on a machine without them, so CI is the reference.
