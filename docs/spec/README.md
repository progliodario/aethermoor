# Specifications

Normative rules shared by the desktop and Android clients. **Status:** 00 to 14 and 16 to 18 are written (all but 16 and 18 have conformance suites; the protagonists are covered by the `stats` and `combat` suites and by a content test); 15 (the layout of the interface) is still to come. The planned content is described in `docs/plan/02-dati-specifiche-e-formati.md`.

| # | Document | Milestone |
|---|---|---|
| [00](00-conventions.md) | conventions (units, tick, IDs) | M1, done |
| [01](01-numerics.md) | numerics (integers, fixed point, RNG, hash, noise) | M1, done |
| [02](02-entities-and-movement.md) | maps, the player, collisions, the camera, the draw order | M2, done |
| [03](03-systems-order.md) | the fixed time step and the order of work inside a tick | M2, done |
| [04](04-stats-and-combat.md) | stats and combat (formulas, difficulty) | M1 / M3, done |
| [05](05-combat-v1.md) | combat v1: attack, power strike, dodge, parry, elements, status effects (creatures and player), stagger, enemies, behaviors, XP, loot | M3, done |
| [06](06-items.md) | items, using them, equipment, shops, gathering, crafting from the bag (the unique pieces of a workshop are a dialogue, spec 07) | M6a / M6b, done |
| [07](07-quests-and-dialogue.md) | quests, dialogue, conditions and effects, the guild, jobs, workshops, inns, wayfarers | M4a, done |
| [08](08-world-time.md) | world time, seasons, weather, respawn, the routines of the people | M5c, done |
| [09](09-worldgen.md) | world generation: terrain, regions, settlements, landmarks, fauna, stones, the world map | M5, done |
| [10](10-companions.md) | companions: a follower that fights, the stay command, the bond (several companions later) | M7, first version done |
| [11](11-progression.md) | progression: bestiary, counters, titles, echoes (tags and the full reincarnation later) | M8, first version done |
| [12](12-save-format.md) | save format v1, the save slots, export and import, the shared profile | M4b / M5, done |
| [13](13-vector-art.md) | vector art recipes, rasterizer, rigs | M2, done |
| [14](14-audio.md) | audio: synthesized sounds, events, ambience, music and their directors (in the base pack music and regional ambience are off) | M3 / M10, effects done |
| 15 | UI layout | M4 |
| [16](16-input.md) | input: keyboard, mouse, gamepad, touch, panels, settings | M2, done |
| [17](17-localization.md) | localization | M1, done |
| [18](18-protagonists.md) | protagonists: data, gift rules, choosing one for a new game, the prologue, the base roster of eight | M3 / M9, done |

Rule: a rule change updates the spec, the Python reference, the conformance vectors, and both clients in the same change (or opens a `parity-debt` issue).
