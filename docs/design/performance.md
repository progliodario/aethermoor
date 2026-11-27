# Performance

How fast the simulation and the drawing are, how it is measured and what the numbers are (items C4.2 and C4.3 of the
[operating program](../plan/07-programma-operativo.md); risks R4, performance on phones, and R6, the lost graphics context, of the
[roadmap](../plan/06-roadmap-rischi-backlog.md)). The numbers of the CI compare one change with the last; they do not say "60 frames a
second on a phone": only the owner's phone says that.

## The budgets

The tests fail when a change makes the game many times slower. The budgets are wide on purpose: the machines of the CI are shared and
their speed changes from run to run, so a budget is tens of times the time measured (the numbers below), and still within a frame at
60 Hz (16.7 ms) for a chunk.

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
| 25 November 2026, pull request of C4.2 | desktop, Windows MSVC (`windows-2022`) | 0.675 ms | 0.024 ms |
| | desktop, Linux GCC (`ubuntu-24.04`) | 0.409 ms | 0.013 ms |
| | Android core on the JVM (`ubuntu-24.04`, JDK 17) | 0.703 ms | 0.126 ms |

A chunk is generated in under a millisecond and a tick takes a hundredth of a millisecond on the desktop and a tenth on the JVM: the
simulation is far from the frame budget. What a phone spends goes to drawing, which only the phone can say.

The test on the emulator of that pull request passed on API 30 and API 34 (one test, none failed).

The textures of all the art of the base pack at the largest bucket of each level: about 12 MiB at 64 (low), 49 MiB at 128 (normal) and
196 MiB at 256 (high), counted by the same tests (Android keeps a copy of every picture on the CPU, so up to twice that).

## The drawing of a frame on the desktop

A frame of the desktop is drawn with a few dozen calls into the renderer, most of them one batch of quads. Before C4.3 it
was about two thousand: every tile was its own call with its own texture, every glyph of a text was its own call, and the
minimap alone was 1,600 filled squares.

| Where | Before | After |
|---|---|---|
| 1280 x 720, Fenwick | 1,920 calls, 1,920 draws | 152 calls, 33 draws |
| 2560 x 1440, Fenwick | (not measured) | 152 calls, 33 draws |
| 2560 x 1440, a village | (not measured) | 151 calls, 32 draws |

A draw is a call the renderer cannot join with the one before it: a change of texture, a geometry, a filled shape between
two of them. The calls are the calls of the code; 1,600 filled squares of the minimap are one batch and one draw after the
first, which is why a call is not a draw.

What changed, all of it presentation (the game, the saves and the conformance vectors are untouched):

- **No string and no lookup per tile**: the cache is asked with a `string_view` of the recipe id and hashes it as it is, a
  tile keeps the pointer to its picture and its definition for the current bucket, and the sprite of a tile is baked the
  first time it is drawn.
- **The glyphs of the font in an atlas**: a text is one geometry whatever its length, instead of one texture for each glyph.
- **The art of a bucket in an atlas**: the pictures are laid in shelves of a texture (2048 pixels of side up to bucket 64,
  4096 above; 1 pixel of gap), with the pictures drawn one by one only when the atlas is full.
- **One batch of quads for the things of a scene**: the ground, the water, the props, the long shadows, the crops and the
  parts of the figures, turned about their joints in the vertices. A transparency or a tint is the colour of the corners.
- **The minimap drawn once**: its 1,600 cells become a texture of 120 pixels of side, remade when the player walks 16 tiles
  or the cells change, and drawn as one picture.

Measuring it: `aethermoor --benchmark --frames=400 [--size=2560x1440] [--start=7520.5,7598.5]` opens a fixed scene without
vsync, runs the frames and writes `benchmark.txt` with the mean, the p50, p95 and p99 of the frame, the worst frame, the
calls and the draws of a frame, and the milliseconds of the ground, of the things, of the sky, of the HUD and of the panels.
`F3` shows the same calls and draws in the game. The frames of the tests (`tests/frames`, `tools/check_frames.py`) are the
proof that the pixels did not change: the biggest difference after C4.3 is 1.8 on a tolerance of 38.

The times of `--benchmark` in this VM are those of the software renderer of SDL (about 0.3 ms of p50 a frame at 1280 x 720,
0.44 at 2560 x 1440, the first frame a second of baking); they say how much the code costs, not what a GPU draws. The
number that matters on the owner's machine is the one he reads with `F3` and `--benchmark` on his own card.

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
