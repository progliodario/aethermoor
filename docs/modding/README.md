# Modding

Mods are content packs: a folder with a `pack.json` and data files that follow the schemas in `schemas/`. No code, no scripting (ADR 0003). The base game is itself a pack (`data/base/`), so every example is there.

## What a pack can hold

Art recipes, rigs and clips, tilesets, enemies and their behaviors, skills, items, quests, dialogues (with conditions and effects), protagonists, stamps (hand-made pieces of the world), the world data (regions, landmarks, people, difficulty), tables, and texts in any number of languages. The guide [`docs/guides/add-content.md`](../guides/add-content.md) walks through each of them and the checks to run; the formats are specified in [`docs/spec/`](../spec/README.md), and `docs/plan/02-dati-specifiche-e-formati.md` (section 12) says what is and is not possible.

## Checking a pack

```bash
python tools/validate_data.py
```

validates every pack folder found in `data/` against the schemas, checks that every referenced ID exists and that the texts of all declared languages have the same keys and the same placeholders.

## State

The mod tooling is not finished: both clients load only `data/base` (a second pack folder is validated but not loaded yet), there is no pack manager, and the JSON reference that `tools/gen_schema_docs.py` should generate from the schemas does not exist yet (planned). Until then the schemas in `schemas/` and the specs are the reference.
