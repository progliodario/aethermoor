# Desktop client (Windows and Linux)

C++20, SDL3. Name and version come from `../project.json` at configure time. See [`docs/dev/setup.md`](../docs/dev/setup.md).

```bash
cmake --preset windows-release        # Linux: linux-release
cmake --build --preset windows-release
ctest --preset windows-release
build/windows-release/Release/aethermoor.exe        # Linux: build/linux-release/aethermoor
```

Flags: `--version`, `--smoke-test` (renders a few frames and exits; used by CI with the dummy video driver).

Layout (planned in `docs/plan/01-architettura-e-repository.md`): `src/{app,core,data,vector,sim,...}`. The `core` library must stay free of SDL and any graphics/audio/input code.

Vector art uses the in-house software rasterizer (ADR 0012), not ThorVG. Libraries: `aether_core` (numerics, rules), `aether_data` (packs), `aether_vector` (recipes, rasterizer, rigs), `aether_sim` (maps, movement, world); all headless. Only `app` links SDL3.

Controls: WASD or arrows, gamepad left stick; F3 toggles the debug overlay; Esc quits.
