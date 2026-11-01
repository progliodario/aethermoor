# ADR 0012: In-house software rasterizer for vector art

- Status: accepted (amends ADR 0004)
- Date: 2026-11-01

## Context

ADR 0004 planned ThorVG on desktop and `android.graphics` on Android to rasterize art recipes. While starting M2 two
problems appeared:

- The desktop CI is the only place where the C++ build can be verified, and ThorVG's C++ API has changed between
  releases; integrating it blind risks long fix loops.
- Two different rasterizers cannot share conformance tests: the clients would only be checked against golden images
  with loose tolerances, and `android.graphics` cannot run in plain JVM unit tests.

## Decision

Both clients implement the **same small software rasterizer** specified in `docs/spec/13-vector-art.md` (nonzero
scanline coverage with 4 sub-scanlines and exact horizontal coverage, gradients, round strokes). The C++ version lives
in `desktop/src/vector`, the Kotlin version in the pure-JVM `core` module. Output goes to RGBA8 bitmaps that the
platform layer uploads as textures (SDL textures, libGDX `Pixmap`/`Texture`).

The recipe format is unchanged, so ThorVG (or SVG import) can be added later as an alternative backend without touching
data.

## Consequences

- Identical geometry on all platforms; conformance probes run headless in CI on both clients.
- More code to maintain (about 400 lines per client) and fewer features than a full vector library (no dashes,
  no clipping masks, no blur in M2). Features are added to the spec first.
- Baking cost is on the CPU at load/zoom change; bitmaps are small and cached by scale bucket.
