# Performance

How fast the simulation and the drawing are, how it is measured and what the numbers are (item C4.2 of the
[operating program](../plan/07-programma-operativo.md); risks R4, performance on phones, and R6, the lost graphics context, of the
[roadmap](../plan/06-roadmap-rischi-backlog.md)). The numbers of the CI compare one change with the last; they do not say "60 frames a
second on a phone": only the owner's phone says that.

## The budgets

The tests fail when a change makes the game many times slower. The budgets are wide on purpose: the machines of the CI are shared and
their speed changes from run to run, so a budget is about five times the time measured. A frame at 60 Hz is 16.7 ms.

| What | How it is measured | Budget |
|---|---|---|
| Generating a chunk of the world (spec 09) | 300 chunks generated anew, in windows of 5 x 5 chunks far from each other, after 100 chunks to warm up | 25 ms a chunk |
| A tick of the simulation (spec 03) | 600 ticks of Ren walking east through the streamed world (seed 42), after 120 ticks to warm up | 4 ms a tick |
| The textures of a level of quality (spec 13, "Quality") | every recipe of the art of the pack baked once at the largest bucket of the level, four bytes a pixel | low 32 MiB, normal 128 MiB, high 512 MiB |

The tests are `desktop/tests/performance_test.cpp` (Catch2, run by `ctest` with the other unit tests) and
`android/core/src/test/.../core/PerformanceTest.kt` (JUnit, run by `gradle :core:test` on the JVM); the budget of the textures is also
checked in the reference (`tools/tests/test_content.py`). Each writes a line of numbers to `performance.txt` in the folder of its build,
and the CI prints it in the step "The numbers of the performance test" of `ci-desktop` and `ci-android`.

## The numbers of the CI

<!-- The numbers below are copied from the step "The numbers of the performance test" of a CI run; refresh them when a change
     makes the generation or the tick faster or slower on purpose. -->

| Run | Client | A chunk | A tick |
|---|---|---|---|
| first measure (pull request of C4.2) | desktop, Windows MSVC | to be filled from the run | |
| | desktop, Linux GCC | | |
| | Android core on the JVM (Linux) | | |

The textures of all the art of the base pack at the largest bucket of each level: about 12 MiB at 64 (low), 49 MiB at 128 (normal) and
196 MiB at 256 (high), counted by the same tests (Android keeps a copy of every picture on the CPU, so up to twice that).

## On the emulator, every night

`.github/workflows/nightly.yml` runs the game on an Android emulator of API 30 and of API 34 (`android/app/src/androidTest/.../LifecycleTest.kt`):
it starts and draws, turns to landscape and back to portrait, goes to the background (the surface and the context may be lost) and comes
back, and it is still the same game: neither the activity nor the game is created again, and the textures are managed. It runs every night
on `main`, by hand (`gh workflow run nightly.yml`), and on a pull request that changes the workflow or the test. The emulator draws with
a software renderer: its frame times say nothing about a phone.

**The lost context.** The textures of the art (`game/TextureCache.kt`) and of the font (`game/PackFont.kt`) are managed textures of
libGDX made from pixmaps that are kept: when Android takes the OpenGL context away (a pause, a long time in the background), libGDX
loads every one of them again by itself. Before this, they were plain textures, and a lost context left them empty.

## On the owner's phone

The CI cannot measure a phone. The owner writes down, with the [release checklist](../dev/release-checklist.md) (section 3), the frames
a second on a phone in three places: the start in Fenwick, a village of the world, a fight with many creatures; and the quality of the
graphics that was used. The numbers go in the table below.

| Date | Phone | Android | Quality | Fenwick | A village | A big fight |
|---|---|---|---|---|---|---|
| (none yet) | | | | | | |
