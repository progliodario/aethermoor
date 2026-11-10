## What

The first act of every protagonist's story, "The First Echo": Sister Maren in Aldermere gives each of the eight protagonists three quests of their own, ending at a guardian of Verdalis. 24 quests, it + en.

## How

- `tools/make_stories.py` (data only, spec 07 and 18): one dialogue with a line per protagonist gated by the keepsake, the quests, the texts, Maren's line in `npcs`.
- Tests of both clients: 17 static people. Worldgen vectors regenerated (the world data changed). READMEs, CLAUDE.md, spec 18, catalog.

## Checked

Data validation, the Python tests (targets spawn, items can be found, people stand on open floor), vectors and catalog run locally. Desktop and Android not built locally: CI is the only build. Not seen on screen.
