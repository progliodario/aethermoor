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
| `add_guild_points` | `amount` | `guild_points += amount` |
| `open_board` | none | opens the board of the settlement the player is in (see "Guild"); nothing when there is none |
| `open_shop` | none | opens the shop of the place (spec 06); nothing changes when the world has no shop there |

## Quests

A quest has ordered **stages**; each stage lists **objectives** and the `next` stage name or `end`. A quest may have `args` (strings) for its texts, like dialogues (see below).

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

## Guild

The guild is the way a player finds work in any town. State: `guild_points` (an integer, saved with the story).

**Ranks.** `guild.ranks` (world data) lists ranks in increasing order with the points they need (F 0, E 100, D 300, C 700, B 1500, A 3000, S 6000).
The rank of a member is the last one whose points are at most `guild_points`. The effect `add_guild_points` adds points.

**Board.** The board of a settlement is a pure function of the seed, the settlement (its site cell `(sx, sy)`) and the **day** (spec 08; the first day is 1). It has `guild.offers_per_day`
offers, slot `0..n-1`. For slot `s`: `h = hash64(hash64(seed, sx, sy, 200 + s), day, s)`; the template is `guild.templates[(h >> 16) % count]`;
`count = count_min + (h >> 32) % (count_max - count_min + 1)`; the **tier** is `s + 1`; the **minimum rank** is `s` (the last rank at most). Rewards:
`gold = (gold_base + count * gold_per) * tier`, `xp = (xp_base + count * xp_per) * tier`, `points = (points_base + count * points_per) * tier`.
A template has a `type` (`kill` or `collect`), a `target` (an enemy or item ID) and the fields above. Offers do not depend on the player: the same town shows the same
board to everyone on the same day, and a new one the next day. The offer text depends on the **tone** of the region (spec 09): `quest.board.<template>.<tone>.name` and `.journal`.

**Generated quests.** Accepting an offer starts a quest with the id `board:<sx>:<sy>:<day>:<slot>` and one stage `work` with one objective (`kill` or `collect`, the target and the count)
that ends the quest; its rewards are `add_xp`, `add_gold` and `add_guild_points` with the amounts above, and its texts take the arguments `{count}`, `{target}` (an `$i18n:` key of the target's name)
and `{place}` (the settlement). The quest document is rebuilt from its id, so only the progress is saved; a save that names a `board:` quest the world cannot rebuild is invalid.
An accepted offer cannot be taken again (the quest exists, active or done). An offer can be accepted only when the board is open and the rank of the member is at least its minimum rank.

`open_board` is fired from the dialogue of a guild clerk ("I'm looking for work"); the board shows the offers of the settlement of the player's tile, the rank, the guild points and the gold.
Collect objectives keep the rule above: they are satisfied while the inventory holds the count (the items are not consumed).

Conformance suite `guild`: ranks for sample points and the offers (and the quests they become) of several settlements on several days; the combat scenario `board_quest_rewards` runs a generated quest.

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
