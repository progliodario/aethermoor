# Specifications

Normative rules shared by the desktop and Android clients. **Status:** 00, 01, 04 (formulas), 12 (draft) and 17 are written (M1); the others follow their milestone; the planned content is described in `docs/plan/02-dati-specifiche-e-formati.md`.

| # | Document | Milestone |
|---|---|---|
| [00](00-conventions.md) | conventions (units, tick, IDs) | M1, done |
| [01](01-numerics.md) | numerics (integers, fixed point, RNG, hash, noise) | M1, done |
| 02 | entities and components | M1 |
| 03 | systems order | M1 |
| [04](04-stats-and-combat.md) | stats and combat (formulas done; hitboxes in M3) | M1 / M3 |
| 05 | skills, status effects, elements | M3 |
| 06 | items, crafting, economy | M4 / M6 |
| 07 | quests and dialogue | M4 |
| 08 | world time, weather, NPC schedules | M5 |
| 09 | world generation | M5 |
| 10 | companions and AI | M7 |
| 11 | progression, titles, tags, reincarnation | M8 |
| [12](12-save-format.md) | save format (draft) | M1, M4 |
| 13 | vector art recipes | M2 |
| 14 | audio synthesis | M3 / M10 |
| 15 | UI layout | M4 |
| 16 | input | M2 |
| [17](17-localization.md) | localization | M1, done |

Rule: a rule change updates the spec, the Python reference, the conformance vectors, and both clients in the same change (or opens a `parity-debt` issue).
