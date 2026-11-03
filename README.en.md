# Aethermoor

> Working title. A top-down, real-time isekai fantasy action RPG with vector graphics. Free and open source.
> Versione italiana: [README.md](README.md)

**Status:** M2 (engine base). A vector character walks around a map on Windows, Linux and Android; there is no combat or story yet. See the [roadmap](docs/plan/06-roadmap-rischi-backlog.md) (Italian).

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
