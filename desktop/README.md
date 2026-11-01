# Desktop client (Windows and Linux)

C++20, SDL3. Name and version come from `../project.json` at configure time. See [`docs/dev/setup.md`](../docs/dev/setup.md).

```bash
cmake --preset windows-release        # Linux: linux-release
cmake --build --preset windows-release
ctest --preset windows-release
build/windows-release/Release/aethermoor.exe        # Linux: build/linux-release/aethermoor
```

Flags: `--version`, `--smoke-test` (renders a few frames and exits; used by CI with the dummy video driver).

Layout (planned in `docs/plan/01-architettura-e-repository.md`): `src/{app,core,data,sim,worldgen,gfx,audio,input,ui,platform}`. Only `app` and `core` exist at M0. The `core` library must stay free of SDL and any graphics/audio/input code.

M0 note: ThorVG is **not** linked yet. It arrives with the vector rasterizer in M2, to avoid an unused dependency.
