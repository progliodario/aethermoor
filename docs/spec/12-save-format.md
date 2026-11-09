# 12. Save format

Status: **v1 (M4b; M5b additions; the slots of the title screen)**. Reference: `CombatSim.save_state` / `load_state` in `tools/reference/combat.py`.
Schema: `schemas/save.schema.json`. Conformance suite: `save` (resume scenarios).

## Files

One JSON file per save, `<user data>/saves/slot<N>/<name>.json`, with the games (slots) `slot1`, `slot2` and `slot3` and, in each,
the saves `auto` (written every 30 s, when the app pauses or quits) and `quick` (manual, desktop). The user data folder is
`SDL_GetPrefPath` on desktop and the app-private folder on Android. A save can be copied by hand between devices and platforms.
The inventory-level profile (`profile.json`) and per-chunk deltas described in the plan arrive with reincarnation.

## Slots

A game is a slot: its own world (its own seed), progress and saves. Three slots exist.

- **Title screen.** At launch the client lists the slots before it builds any world: a used slot shows `level` and `story.gold` of its
  `auto` save, read without building the world (`save_peek`: `seed`, `map`, `player.level`, `story.gold`), an empty slot says it is a new game.
  Choosing a used slot continues it; choosing an empty one starts a new world with a new random seed. The seed is written
  into the saves of the slot, so the same world comes back.
- **Delete.** A used slot can be deleted after a second confirmation (desktop: `D` twice; Android: the cross, then the cross again). Deleting removes
  the files of that slot only.
- **Migration.** A save written before slots (`saves/auto.json`, `saves/quick.json`) is moved to `slot1` the first time a client starts.
- **Files of a slot** (`saves/slot<N>/`): `auto.json` and `quick.json` (the saves, spec above), `protagonist.txt` (the ID of the protagonist chosen for the game, spec 18; absent in older games, which are played as Ren) and `goal.txt` (the goal marked on the
  map, `x y` in tiles, spec 09, "The map view"; removed with the goal). The last two are not part of the save document. `settings.json` (the language, spec 16) is next to the `saves` folder, not in a slot.
- **Dev options.** Desktop `--slot=N` skips the title screen; `--smoke-test` uses its own folder and never touches the three slots.
- **Back to the title.** Leaving a game (desktop: `Esc` with no panel open; Android: the Back key with no panel open, `Esc` on a keyboard) writes the `auto` save and returns to the title screen, where another game can be chosen; the world of the next game is built when it is chosen, from its own seed, and nothing of the previous world is kept (the map cells already seen are forgotten with it). With a panel open, Back closes the panel. On the title screen `Esc` or Back quits, and so does closing the window in a game. `--slot=N` and `--smoke-test` on desktop keep their one game and quit on `Esc`.

## Export and import

A game can be moved to another device or backed up as one file, a **bundle** (`.aethersave`): a JSON text
`{"aethersave": 1, "game_version": "0.0.1", "files": {"auto.json": "<text>", "protagonist.txt": "<text>", ...}}`. `files` holds, as strings, the files of the slot
with these names and no others: `auto.json`, `quick.json`, `protagonist.txt`, `goal.txt`. Exporting writes the files that exist (it leaves the others out).

**Importing** takes a bundle and writes its files into an **empty** slot. A bundle is refused (nothing is written) when it is not JSON, is not an object, has no integer
`aethersave` equal to 1, has no object `files`, has a file with another name (a name with a folder in it too), a file whose content is not a string, no `auto.json` and no
`quick.json`, or a save that is not a JSON object with an integer `save_version`. The conformance suite `savebundle` covers these cases and the round trip.

Desktop: on the title screen `X` exports the chosen game to `<user data>/exports/slot<N>.aethersave`, and `I` imports the file `<user data>/exports/import.aethersave` into the chosen game, if it
is empty. Android: every row of the title screen has a button, Export on a used game and Import on an empty one (`X` and `I` on a keyboard). The folder is `exports` in the storage of the app that a file manager
can reach (`Android/data/<package>/files/exports`; the private folder when the device has none); a share or open dialog of the system is not used yet, so on some devices the folder can only be reached from a computer.

## Document

```json
{
  "save_version": 1,
  "game_version": "0.0.1",
  "data_format_version": 1,
  "protagonist": "base:protagonist/ren",
  "seed": "0x00000000DEADBEEF",
  "map": "demo",
  "player": { "x": 5.5, "y": 15.5, "facing": [1.0, 0.0], "facing_left": false, "moving": false, "clip_tick": 0,
              "hp": 142, "level": 1, "xp": 0, "deaths": 0, "kills": 0, "iframes": 0, "cooldown": 0,
              "phase": "none", "phase_tick": 0, "hit_set": [false, false] },
  "rng": { "combat": {"state": "0x...", "inc": "0x..."}, "loot": {"state": "0x...", "inc": "0x..."} },
  "enemies": [ { "x": 4.9, "y": 4.5, "hp": 5, "state": "idle", "state_tick": 0 } ],
  "inventory": { "base:item/bread": 3 },
  "story": { "flags": {}, "gold": 0,
             "quests": { "base:quest/guild/slime_extermination": { "stage": "kill", "progress": [2], "done": false } },
             "dialogue": { "id": "base:dialogue/npc/mira", "node": "offer_choice" } }
}
```

- `map` is `demo` (the hand-made map), `world` (the streamed world generated from `seed`, spec 09) or empty (old saves). A client
  rebuilds the same map from it before loading; a save of another map is not restored.
- `enemies` is in the order of the map spawners; only changed state is stored (definitions and home positions come from data).
- **Streamed world** (`map` is `world`): `enemies` lists only the enemies of the active window, in the order of the live game, and each one has
  `"spawner": [x, y]` (its spawner tile, which also gives its home); `cleared_spawners` lists the spawners whose enemy was killed as `[x, y, died_tick]` (spec 08, the world tick of the death). On load the
  window is rebuilt around the saved player position; every enemy must belong to a spawner of the window (the enemy of a cleared spawner is dead), and every
  uncleared spawner of the window must have its enemy, otherwise the save is invalid for this build. `cleared_spawners` and `spawner` are absent on fixed maps.
- `explored` (streamed world) is the list of explored world map cells `[x, y]`, ordered by row then column (spec 09); absent in old saves.
- `counters` (spec 11) is an object from counter name (`gathered`, `crafted`, `parried`) to a count; absent when empty and in older saves.
- `bestiary` (spec 11) is an object from creature ID to kills; absent when empty and in older saves.
- `companion` (a protagonist with a companion, spec 10) is `{"x", "y", "cooldown"}`: where the companion is and how many ticks until it hits again; absent in older saves (it is put next to the player).
- `stones` (streamed world) is the list of the tiles `[x, y]` of the Threshold Stones that were used, in the order they were woken (spec 09); absent in old saves.
- `story.guild_points` is the guild points of the player (spec 07); absent in old saves (0). Quests whose id starts with `board:` are generated quests: only their progress is saved.
- `equipped` is `{weapon, armor}`: the item ids worn (spec 06); absent in old saves (the starting weapon, no armor).
- `world_ticks` is the world clock (spec 08); a save without it starts at the world's `time.start_tick`.
- `story` is null when the world has no story. `dialogue` is null when no dialogue is open; otherwise it has `id`, `node` and, when the NPC had arguments (spec 07), `args` (a map of strings).
- 64-bit values are hex strings. Positions are floats (a client reads them as 32-bit floats).
- Random stream states are the PCG32 `state` and `inc` after the last draw: resuming a save continues the same random sequence.
- Derived stats are not stored; they are recomputed from the level, the protagonist data and the equipment.

## Rules

- **Loading** builds the world from data (the same map and seed-independent setup), then overwrites the mutable state. A save whose
  `save_version` is higher than the client supports is refused with a clear message; the world is left unchanged.
- **Entities that no longer exist** in data (enemy count mismatch) make the save invalid for this build; the client reports it and keeps
  the current world.
- **Writing is atomic**: write `<slot>.json.tmp`, then rename over `<slot>.json`.
- **Resume equivalence** (tested): running part of a scenario, saving, loading into a fresh world and finishing gives the same
  checkpoints as running it without interruption, on both clients, also when loading a save written by the Python reference.
- Every incompatible format change bumps `save_version` and adds a migration `migrate_N_to_N+1` with a fixture in `tests/conformance`. Optional
  fields that older readers can ignore (`map`, `cleared_spawners`, `spawner`) do not.

## Not yet in v1

CRC of the file, `profile.json` (meta-progression), other changes of the streamed world (arrive with the world systems), thumbnails, `.aethersave` export.
