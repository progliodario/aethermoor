# Modding

Mods are content packs: a folder with a `pack.json` and data files that follow the schemas in `schemas/`. No code, no scripting
(ADR 0003). The base game is itself a pack (`data/base/`), so every example of every kind of file is there, and a whole small mod is in
[`examples/mod-example/`](../../examples/mod-example/): one creature, one quest and their texts in Italian and English.

## What a pack can hold

Art recipes, rigs and clips, tilesets, enemies and their behaviors, skills, items, quests, dialogues (with conditions and effects),
protagonists, stamps (hand-made pieces of the world), the world data (regions, landmarks, people, difficulty), tables, and texts in any
number of languages. The guide [`docs/guides/add-content.md`](../guides/add-content.md) walks through each of them; the formats are
specified in [`docs/spec/`](../spec/README.md), and `docs/plan/02-dati-specifiche-e-formati.md` (section 12) says what is and is not
possible.

## Your first mod: a creature and a quest

Copy `examples/mod-example/` to a folder of your own (anywhere: it does not have to be inside the repository) and change it step by step.

1. **The manifest**, `pack.json`. `id` is the namespace of everything you add (lowercase, no spaces): every ID of your files starts with
   it (`example:enemy/slime_honey`). `depends` lists the packs you build on: `["base"]` lets you use everything of the base game (its
   art, items, behaviors, enemies). `languages` lists the languages you write texts in; the first one is the reference.
2. **The creature**, `enemies/slime_honey.json`. It is a copy of a slime of the base game (`data/base/enemies/slime_mint.json`) with
   its own ID, name, stats and drops. It borrows the art of the amber slime (`base:art/creature/slime_amber`) and the behavior
   `base:behavior/skittish`: a mod can use anything of the packs it depends on. The rules of the numbers are in spec 05 (combat) and
   spec 04 (stats); the fights of the game are easy on purpose, so keep new creatures gentle.
3. **The quest**, `quests/side/honey_hunt.json`. One stage, one objective (`kill` five honey slimes), rewards as effects (`add_xp`,
   `add_gold`, `add_item`). The objectives, the stages and the effects are in spec 07.
4. **The texts**, `i18n/<language>/content.json`. Every visible text is a key, written `$i18n:<key>` in the data, with a value in
   every language of the manifest: the same keys in all of them, and the same placeholders (`{name}`). A mod may also use the texts of
   the packs it depends on.
5. **Check it**:

   ```bash
   python tools/validate_data.py path/to/your-mod
   ```

   It validates every file against its schema, checks that every ID you name exists (in your pack or in the packs of `depends`), that
   you do not define again an ID of another pack, that your IDs are in your namespace, and that every text exists in every language.
   It prints `OK` or the list of problems, with the file and the place of each. The CI runs the same check on the example mod.

To add a different kind of thing, copy the closest file of `data/base/`, follow its schema in `schemas/` and run the check again.

## Checking the base game

```bash
python tools/validate_data.py
```

with no argument validates every pack folder found in `data/`.

## State

The mod tooling is not finished: both clients load only `data/base` (a mod is validated, not yet loaded by the game), there is no pack
manager, and the JSON reference that `tools/gen_schema_docs.py` should generate from the schemas does not exist yet (planned). Until then
the schemas in `schemas/` and the specs are the reference. Loading mods in the game is part of the work after 1.0 (the "tools for mods"
of the roadmap).
