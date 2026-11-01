# ADR 0007: Save format and versioning

- Status: accepted
- Date: 2026-11-01

## Context

Saves must be portable, human readable, safe against corruption, and upgradable.

## Decision

JSON files with `save_version`, CRC, atomic writes with backups, per-chunk deltas, a shared `profile.json`, and `.aethersave` zip export/import. Migrations are specified and tested.

## Consequences

Readable and moddable saves; no anti-cheat. Any format change needs a migration and conformance vectors.
