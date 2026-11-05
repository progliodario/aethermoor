# Aethermoor

> Working title. A top-down, real-time isekai fantasy action RPG with vector graphics. Free and open source.
> Versione italiana: [README.md](README.md)

**Status:** a playable test version (one protagonist, Ren), played by hand on Windows only (Linux and Android are built and tested by CI; Android has never been run on a device). You explore a 16384 x 16384 tile world generated from a seed (eight regions, day and night, seasons, weather) with about 130 settlements, 35 hand-made sites (dungeons with bosses, lairs, nests, outposts with wayfarers and their stories), 60 creatures, 112 items, a guild with a board and commissions, shops, inns, Threshold Stones to travel, a journal, three save slots and Italian and English. The other protagonists with their gifts, companions and the base are still to come. The catalog of the content is in [`docs/design/catalog.md`](docs/design/catalog.md). See the [roadmap](docs/plan/06-roadmap-rischi-backlog.md) (Italian).

## What it is

Eight or more souls are pulled into Aethermoor, each with a "Gift" that breaks the rules. Who you choose to be changes the tone, the mechanics and the story. The world is shared, and the destinies cross.

- Top-down open world: hand-made towns, procedural wilderness
- 8+ protagonists, each with their own plot and mechanics
- Adventurers' guild with ranks, status window, titles and tags
- Companions, bonds, a base to build, farming, cooking, crafting
- Reincarnation as meta-progression
- All content is JSON data: moddable
- Single player only, no network, no ads

## Platforms

| Platform | Code | Technology |
|---|---|---|
| Windows and Linux | [`desktop/`](desktop) | C++20, SDL3, an in-house vector rasterizer ([ADR 0012](docs/adr/0012-in-house-software-rasterizer.md)) |
| Android 11+ | [`android/`](android) | Kotlin, libGDX, the same rasterizer in Kotlin |

The two clients are separate implementations that read the same data in [`data/`](data) and follow the same specs in [`docs/spec/`](docs/spec).

## Trying it

Every GitHub CI run uploads the test build for Windows and Linux (artifacts `aethermoor-windows-msvc` and `aethermoor-linux-gcc`, kept 30 days): unpack it, run `aethermoor` with the `data` folder next to it, and read [`desktop/PLAY.txt`](desktop/PLAY.txt) for the controls and what to try. In short: `WASD` to move, `J` or `Space` to attack, `E` to talk, `I` the bag, `Q` the journal, `M` the map, `Esc` to go back to the list of games. The Android build (a debug APK, artifact `aethermoor-debug-apk`) compiles and passes its tests in CI but has never been run on a phone. There is no public release yet.

## Getting started (developers)

1. Read the [project plan](docs/plan/README.md) (Italian) and [`CLAUDE.md`](CLAUDE.md).
2. Set up your environment: [`docs/dev/setup.md`](docs/dev/setup.md).
3. Validate the data:

```bash
python -m venv .venv
.venv/Scripts/pip install -r tools/requirements.txt   # on Linux: .venv/bin/pip
python tools/validate_data.py
```

The everyday tools (conformance vectors, the content catalog, the balance report, `ship.py` which runs the checks, commits, opens the PR and merges in one go) are in the table of [`docs/dev/setup.md`](docs/dev/setup.md). To add content (an item, a creature, a quest, a place, a region, a language) there is a [guide](docs/guides/add-content.md).

## Layout

```text
docs/      plan (it), specs (en), design and catalog, guides, ADRs, setup
schemas/   JSON Schemas of the data
data/      the game content (pack "base": art, creatures, items, quests, dialogues, world, it/en texts)
tests/     conformance vectors shared by the two clients (generated, never edited by hand)
tools/     Python scripts: validation, the reference of the rules, generators, ship.py
desktop/   Windows and Linux client (C++)
android/   Android client (Kotlin)
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

Code: [GPL-3.0](LICENSE). Content (data, texts, design documents): [CC BY-SA 4.0](LICENSE-CONTENT.md).
