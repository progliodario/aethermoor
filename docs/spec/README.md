# Specifications

Normative rules shared by the desktop and Android clients. **Status:** 00, 01, 04 (formulas), 12 (draft) and 17 are written (M1); the others follow their milestone; the planned content is described in `docs/plan/02-dati-specifiche-e-formati.md`.

| # | Document | Milestone |
|---|---|---|
| [00](00-conventions.md) | conventions (units, tick, IDs) | M1, done |
| [01](01-numerics.md) | numerics (integers, fixed point, RNG, hash, noise) | M1, done |
| [02](02-entities-and-movement.md) | entities, maps and movement (M2 subset) | M2, done |
| [03](03-systems-order.md) | systems order and game loop (M2 subset) | M2, done |
| [04](04-stats-and-combat.md) | stats and combat (formulas done; hitboxes in M3) | M1 / M3 |
| [05](05-combat-v1.md) | combat v1: attack, enemies, XP, loot (status effects and elements later) | M3, done |
| 06 | items, crafting, economy | M4 / M6 |
| [07](07-quests-and-dialogue.md) | quests, dialogue, conditions and effects | M4a, done |
| 08 | world time, weather, NPC schedules | M5 |
| 09 | world generation | M5 |
| 10 | companions and AI | M7 |
| 11 | progression, titles, tags, reincarnation | M8 |
| [12](12-save-format.md) | save format (draft) | M1, M4 |
| [13](13-vector-art.md) | vector art recipes, rasterizer, rigs | M2, done |
| 14 | audio synthesis | M3 / M10 |
| 15 | UI layout | M4 |
| [16](16-input.md) | input (M2 subset) | M2, done |
| [17](17-localization.md) | localization | M1, done |

Rule: a rule change updates the spec, the Python reference, the conformance vectors, and both clients in the same change (or opens a `parity-debt` issue).
