# AGENTS.md

Instructions for AI coding assistants working in this repository.

The rules of work are in **[`CLAUDE.md`](CLAUDE.md)**: they apply to every assistant, not only to Claude. Read it whole before changing anything. In short:

- **Spec first, two clients, one behavior.** A rule lives in `docs/spec/`, the Python reference (`tools/reference/`), the conformance vectors (`tests/conformance/`), the C++ client (`desktop/`) and the Kotlin client (`android/`), changed together.
- **Data driven.** Content is JSON in `data/base/`, every visible text an `$i18n:` key in Italian and English.
- **Never hand-edit generated files** (the vectors, `docs/design/catalog.md`, the facts blocks, most of `data/base/`): change the source and run the tool listed in [`tools/README.md`](tools/README.md).
- **Check before you finish:** `python tools/validate_data.py`, `python -m pytest -q tools/tests`, `python tools/gen_conformance.py --check`.

Where to start reading: [`README.en.md`](README.en.md) (what the game is), [`docs/guides/continue-the-work.md`](docs/guides/continue-the-work.md) (the handbook for whoever continues: read order, state, the loop of a session, a change through every layer, shipping, CI failures), [`docs/dev/architecture.md`](docs/dev/architecture.md) (the map of the code), [`docs/index.md`](docs/index.md) (all the documentation), [`docs/spec/README.md`](docs/spec/README.md) (the rules), [`tools/README.md`](tools/README.md) (the scripts).
