# Specifications

Normative rules shared by the desktop and Android clients. **Status:** 00 to 09, 12, 13, 16, 17 and 18 are written and have conformance suites; 10, 11, 14 and 15 are still to come with their milestones. The planned content is described in `docs/plan/02-dati-specifiche-e-formati.md`.

| # | Document | Milestone |
|---|---|---|
| [00](00-conventions.md) | conventions (units, tick, IDs) | M1, done |
| [01](01-numerics.md) | numerics (integers, fixed point, RNG, hash, noise) | M1, done |
| [02](02-entities-and-movement.md) | maps, the player, collisions, the camera, the draw order | M2, done |
| [03](03-systems-order.md) | the fixed time step and the order of work inside a tick | M2, done |
| [04](04-stats-and-combat.md) | stats and combat (formulas, difficulty) | M1 / M3, done |
| [05](05-combat-v1.md) | combat v1: attack, enemies, behaviors, XP, loot (status effects and elements later) | M3, done |
| [06](06-items.md) | items, using them, equipment, shops (crafting is a workshop dialogue, spec 07) | M6a / M6b, done |
| [07](07-quests-and-dialogue.md) | quests, dialogue, conditions and effects, the guild, jobs, workshops, inns, wayfarers | M4a, done |
| [08](08-world-time.md) | world time, seasons, weather, respawn, the routines of the people | M5c, done |
| [09](09-worldgen.md) | world generation: terrain, regions, settlements, landmarks, fauna, stones, the world map | M5, done |
| [18](18-protagonists.md) | protagonists: data, choosing one for a new game, the base roster | M3 / M8, done for four |
| 10 | companions and AI | M7 |
| 11 | progression, titles, tags, reincarnation | M8 |
| [12](12-save-format.md) | save format v1 and the save slots | M4b / M5, done |
| [13](13-vector-art.md) | vector art recipes, rasterizer, rigs | M2, done |
| 14 | audio synthesis | M3 / M10 |
| 15 | UI layout | M4 |
| [16](16-input.md) | input: keyboard, mouse, gamepad, touch, panels, settings | M2, done |
| [17](17-localization.md) | localization | M1, done |

Rule: a rule change updates the spec, the Python reference, the conformance vectors, and both clients in the same change (or opens a `parity-debt` issue).
