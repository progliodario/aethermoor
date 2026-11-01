# 12. Save format

Status: **draft v1**. The load/save implementation arrives in M4. This document fixes the layout so the clients can be built against it.

## Layout

```
saves/
  profile.json        meta-progression shared by all lives (echoes, unlocked protagonists, titles, bestiary)
  slot_1/ ... slot_5/
    run.json          protagonist, world seed, world time, player, party, inventory, quests, flags, variables, RNG streams
    deltas/{cx}_{cy}.json   per-chunk differences against the generated world
    thumbnail.pam
  auto/               three rotating autosaves with the same layout as a slot
```

## Common fields

`save_version` (integer), `game_version`, `data_format_version`, `pack_list` (`id` and `version` per loaded pack), `created_at` (ISO 8601 UTC), `play_time_s`, `crc32` (of the file with this field set to 0).

## Rules

- Writes are atomic: write `file.tmp`, flush, rename; keep three `.bak` copies.
- Only differences against the generated world are stored (never whole chunks).
- Every format change bumps `save_version` and adds a migration `migrate_N_to_N+1`, tested with sample files in `tests/conformance/saves/`.
- A save with an unknown newer `save_version` is refused with a clear message.
- Missing mod content is replaced by placeholders and reported; the save still loads.
- Export/import uses one `.aethersave` zip (profile + one slot). Desktop: file copy or button. Android: Storage Access Framework.
- Numbers are integers wherever the rules are integers. Positions may be stored as floats.
