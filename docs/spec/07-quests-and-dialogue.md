# 07. Quests, dialogue, conditions and effects

Status: **v1 (M4a)**. Reference: `tools/reference/combat.py` (class `CombatSim`, story part).
Conformance suite: `combat` scenarios that carry a `story` section. Schemas: `quest`, `dialogue`, map objects of type `npc`.

## Conditions (closed catalog, v1)

A condition is a JSON object with exactly one key:

| Key | Value | True when |
|---|---|---|
| `flag` | flag name | the flag is set to true |
| `not` | condition | the inner condition is false |
| `all` | list of conditions | all are true (empty list: true) |
| `any` | list of conditions | at least one is true (empty list: false) |
| `quest_active` | quest ID | the quest was started and is not finished |
| `quest_done` | quest ID | the quest is finished |
| `quest_stage` | `{quest, stage}` | the quest is active and its current stage is `stage` |
| `has_item` | `{item, qty}` | the inventory holds at least `qty` of the item |
| `level_at_least` | integer | the player level is at least that value |

## Effects (closed catalog, v1)

An effect is an object with `effect` plus parameters, applied in list order:

| Effect | Parameters | Result |
|---|---|---|
| `add_xp` | `amount` | `xp += amount`, then the level-up loop of spec 05 |
| `add_gold` | `amount` | `gold += amount` |
| `add_item` | `item`, `qty` | inventory `item += qty` |
| `set_flag` | `flag`, `value` | sets the flag to the boolean |
| `start_quest` | `quest` | starts the quest (ignored when it already exists) |

## Quests

A quest has ordered **stages**; each stage lists **objectives** and the `next` stage name or `end`.

- Objectives: `kill {enemy, count}`, `collect {item, count}` (satisfied while the inventory holds `count`), `talk {npc_key}` (satisfied once).
- Starting a quest puts it on its first stage with all progress at 0, then refreshes `collect` objectives.
- Events: killing an enemy increments the `kill` objectives of the current stage that name its ID (capped at `count`);
  talking to an NPC (`interact`) satisfies `talk` objectives naming its key; any event also refreshes `collect` objectives.
- When every objective of the current stage is satisfied the quest moves to `next` (progress reset, `collect` refreshed) and
  this repeats while the new stage is already satisfied. Reaching `end` marks the quest **done** and applies its `rewards` effects.

## Dialogue

A dialogue is a graph of named nodes with a `start` node and the special target `end`.

| Node type | Fields | Behavior |
|---|---|---|
| `say` | `speaker`, `text`, `next` | shown until the player advances |
| `choice` | `choices[{text, when?, effects?, next}]` | shown; only choices whose `when` holds (or that have none) are visible, in data order |
| `set_flag` | `flag`, `value`, `next` | runs immediately |
| `effects` | `effects`, `next` | runs immediately |
| `condition` | `when`, `then`, `else` | runs immediately, goes to `then` or `else` |

- Starting a dialogue and every transition **settle**: non-interactive nodes run until a `say`/`choice` node or `end` is reached (`end` closes the dialogue).
- `advance` on a `say` node follows `next`; on a `choice` node it does nothing.
- `choose(i)` on a `choice` node picks the i-th **visible** choice (out of range: nothing happens), applies its effects, follows its `next`.
- While a dialogue is open the player cannot move or attack (inputs are ignored); enemies keep updating.

## NPCs and interaction

- Map object `type: "npc"`: properties `key` (name used for `talk` and for the text key `speaker.<key>`), `dialogue` (dialogue ID), `variant` (art palette variant of the player rig). NPCs are solid circles of radius 0.3.
- `interact`: when a dialogue is open it behaves as `advance`. Otherwise the nearest NPC within 1.5 tiles (first in list order on ties) is talked to:
  first the `talk` event is processed, then its dialogue starts.

## Dynamic NPCs and dialogue arguments

NPCs that come from the generated world (settlement people, spec 09) have the same fields plus a `name` (a proper noun, not translated) and **arguments**, a map of strings
that the texts of their dialogue may use as `{npc}`, `{place}`, `{region}` and `{quirk}`. The arguments of the NPC being talked to are kept while the dialogue is open
(and saved with it, spec 12). A value that starts with `$i18n:` is a text key that the client resolves in the current language, formatting it with the other (plain) arguments.
In a `say` node the speaker `npc` means the name of the NPC being talked to; any other speaker is the text `speaker.<key>`.
Dynamic NPCs exist in the order they entered the active window of chunks (spec 09, "Streaming"); the `interact` rules above apply to the static and the dynamic NPCs together,
with the static ones first.

## Presentation (not in the contract)

The dialogue box shows the speaker (`speaker.<key>` text), the text and the visible choices. The quest tracker shows the quest name, the
stage journal text and kill/collect progress as `current/total`.
