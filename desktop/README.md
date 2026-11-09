# Desktop client (Windows and Linux)

C++20 and SDL3. Name and version come from `../project.json` at configure time. Setup of the tools: [`docs/dev/setup.md`](../docs/dev/setup.md).

```bash
cmake --preset windows-release        # Linux: linux-release
cmake --build --preset windows-release
ctest --preset windows-release
build/windows-release/Release/aethermoor.exe        # Linux: build/linux-release/aethermoor
```

The build copies `../data` next to the executable (`data/base/pack.json` is looked up there first, then in the repository). The packaged test build is what CI uploads on every run (artifacts `aethermoor-windows-msvc`, holding `aethermoor-windows-x64.zip`, and `aethermoor-linux-gcc`, holding `aethermoor-linux-x64.tar.gz`, kept 30 days): the executable, the DLLs on Windows, the `data` folder and [`PLAY.txt`](PLAY.txt), which tells a player the controls and what to try, in English and Italian. `tools/ship.py --play <folder>` copies the Windows one over a local play folder.

## Command line

| Flag | Meaning |
|---|---|
| `--version` | prints the name and version and exits |
| `--smoke-test` | opens a window (with `SDL_VIDEODRIVER=dummy` in CI), bakes the art, walks the player for a few frames and exits with an error if something is wrong |
| `--screenshot-dir=DIR` | with the smoke test: writes PNG frames into `DIR`: walking, the bag, the Analyze panel, the world map framed and whole, the title screen, the protagonist screen of each protagonist (`chooser_0.png`...), and a dialogue on the demo map |
| `--map=demo\|world` | the hand-made demo map or the streamed 16384 x 16384 world (default: `world`, and `demo` for the smoke test) |
| `--seed=N` | the seed of a new world (a saved game keeps its own) |
| `--start=X,Y` | puts the player at a tile, to look at a place (a village, a dungeon) in a smoke test |
| `--slot=N` | developer option: opens game 1 to 3 without the title screen |
| `--protagonist=<name>` | developer option: plays that protagonist (`ren`, `sakura`, `daichi`, `haruka`, `marco`, `yuki`, `lena`, `gideon`) in a new game or the smoke test |

To see real frames of a place of the world: `aethermoor --smoke-test --map=world --seed=7 --start=<x>,<y> --screenshot-dir=<folder>`.

## Controls

The full list is in [`PLAY.txt`](PLAY.txt) and in [spec 16](../docs/spec/16-input.md). In short: `WASD` or arrows to move, `J`, `Space` or the left mouse button to attack, `E` or `Enter` to talk and confirm, `I` the bag, `Q` the journal, `M` the world map, `F2` the language, `F5`/`F9`/`F7` quick save, quick load, new game, `F3` the debug overlay, `K` the power strike, `U` the parry, `C` the crafting panel, `L` or `Left Shift` the dodge roll, `F8` sound on and off, `F10` the volumes, `Z` Analyze (Ren), `N` the small map, `P`/`X` on the map to mark and remove a goal, `Esc` closes a panel, then goes back to the title screen, and quits from there. A gamepad moves with the left stick (`A`/south attacks and confirms, `X`/west talks, `B`/east closes a panel or rolls out of the way, `RB` is the power strike).

## Layout

```text
src/app/      main.cpp (window, input, HUD, panels: the only code that links SDL3), texture cache, feature list
src/core/     numerics, ids, message format, rules (formulas), world generation, world time, version
src/data/     the pack loader, the world data, the protagonist
src/vector/   art recipes, the software rasterizer, rigs and clips (spec 13, ADR 0012)
src/sim/      tile maps, movement, combat, the story engine, the streamed world (chunks), saves, the world map
tests/        Catch2: version, conformance vectors, pack, simulation, combat and story scenarios
```

Four static libraries, all headless (no SDL, no graphics, audio or input code, rule 10 of `CLAUDE.md`): `aether_core`, `aether_data`, `aether_vector` and `aether_sim`; only the `aethermoor` executable links SDL3. Vector art uses the in-house rasterizer (ADR 0012), not ThorVG. The text is drawn with the debug font of SDL, which has the ASCII characters only: `debug_text()` in `main.cpp` draws the accented letters of the Italian texts as a letter with a small accent.

## Tests

`ctest` runs `aether_tests` (Catch2, including every conformance suite of `tests/conformance/`) and three smoke tests (the demo map, the world and a village of the world). Some tests count what the data holds (stamps, people, tiles of the tileset): when you add content, update them, or CI will tell you.

Saves are in the user data folder (`SDL_GetPrefPath`: `%APPDATA%\progliodario\Aethermoor\saves` on Windows), one folder per game, plus `settings.json`.
