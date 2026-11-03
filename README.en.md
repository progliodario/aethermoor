# Aethermoor

> Working title. A top-down, real-time isekai fantasy action RPG with vector graphics. Free and open source.
> Versione italiana: [README.md](README.md)

**Status:** a playable test version (one protagonist, Ren). On Windows, Linux and Android you explore a 16384 x 16384 tile world generated from a seed (eight regions, day and night, seasons, weather) with about 130 settlements, 35 hand-made sites (dungeons with bosses, lairs, nests, outposts with wayfarers and their stories), 60 creatures, 110 items, a guild with a board and commissions, shops, inns, Threshold Stones to travel, a journal, three save slots and Italian and English. The other protagonists with their gifts, companions and the base are still to come. The catalog of the content is in [`docs/design/catalog.md`](docs/design/catalog.md). See the [roadmap](docs/plan/06-roadmap-rischi-backlog.md) (Italian).

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
| Windows and Linux | [`desktop/`](desktop) | C++20, SDL3, ThorVG |
| Android 11+ | [`android/`](android) | Kotlin, libGDX |

The two clients are separate implementations that read the same data in [`data/`](data) and follow the same specs in [`docs/spec/`](docs/spec).

## Getting started (developers)

1. Read the [project plan](docs/plan/README.md) (Italian) and [`CLAUDE.md`](CLAUDE.md).
2. Set up your environment: [`docs/dev/setup.md`](docs/dev/setup.md).
3. Validate the data:

```bash
python -m venv .venv
.venv/Scripts/pip install -r tools/requirements.txt   # on Linux: .venv/bin/pip
python tools/validate_data.py
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

Code: [GPL-3.0](LICENSE). Content (data, texts, design documents): [CC BY-SA 4.0](LICENSE-CONTENT.md).
