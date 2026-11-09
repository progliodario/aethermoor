# 11. Progression: bestiary and titles

Status: **v1 (bestiary and titles; tags and reincarnation come later)**. Reference: `CombatSim._on_kill` and `CombatSim.earned_titles` in `tools/reference/combat.py`.
Schema: `schemas/titles.schema.json`. Conformance: the scenario `bestiary_titles` of the suite `combat` (the checkpoints carry `bestiary` and `titles`).

## Bestiary

Every time a creature dies by the hand of the player (or of the companion, spec 10) the **bestiary** counts it: `bestiary[id] += 1`, with `id` the ID of the creature (`base:enemy/slime_green`).
A creature without an ID is not counted. The bestiary is a map from ID to kills; its size is the number of **species** met. It is saved (`bestiary` in the save document, spec 12; absent when empty and in older saves)
and it is the same for all the maps of a game.

## Titles

`data/base/titles.json` (ID `base:titles/all`) lists titles in order of rank: `id`, `name` (a text key) and a condition, `kind` and `count`:

| kind | the title is earned when |
|---|---|
| `kills` | the player has killed `count` creatures in all |
| `kills_of` | the bestiary holds at least `count` kills of `enemy` |
| `level` | the player is at level `count` or more |
| `species` | the bestiary holds `count` creatures or more |
| `quests` | `count` quests are finished |

The titles earned are **not saved**: they are computed from the state, in the order of the data (`earned_titles`), so a title cannot be lost nor given twice, and a new title in a later version is
earned at once by those who already satisfy it. The last title earned is the one that counts as the current one.

## Display

The journal (spec 07) shows, after the quests, the titles (the ones not earned yet as `???`) and the bestiary (name and kills, by ID). The name of a creature is the text key `enemy.<name>.name`.

## Later

Tags (traits earned by how one plays), reincarnation (a new life that keeps part of the progress), a shared `profile.json` across saves, and titles with effects.
