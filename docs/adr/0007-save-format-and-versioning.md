# ADR 0007: Save format and versioning

- Status: accepted
- Date: 2026-11-01

## Context

Saves must be portable, human readable, safe against corruption, and upgradable.

## Decision

JSON files with `save_version`, CRC, atomic writes with backups, per-chunk deltas, a shared `profile.json`, and `.aethersave` zip export/import. Migrations are specified and tested.

## Consequences

Readable and moddable saves; no anti-cheat. Any format change needs a migration and conformance vectors.

## Implementation (2026-11-03)

Done (spec 12): JSON saves with `save_version`, atomic writes, three save slots, resume equivalence tested on both clients and the Python reference. Not done yet: the CRC, backups, a shared `profile.json`, per-chunk deltas beyond the cleared spawners and the explored cells, and the `.aethersave` export.
