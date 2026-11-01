# 12. Save format

Status: **v1 (M4b; M5b additions)**. Reference: `CombatSim.save_state` / `load_state` in `tools/reference/combat.py`.
Schema: `schemas/save.schema.json`. Conformance suite: `save` (resume scenarios).

## Files

One JSON file per slot, `<user data>/saves/<slot>.json`, with the slots `auto` (written every 30 s, when the app pauses or
quits) and `quick` (manual). The user data folder is `SDL_GetPrefPath` on desktop and the app-private folder on Android. A
save can be copied by hand between devices and platforms. The inventory-level profile (`profile.json`) and per-chunk deltas
described in the plan arrive with the procedural world and reincarnation.

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
