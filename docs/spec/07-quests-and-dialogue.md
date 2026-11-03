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
| `gold_at_least` | integer | the gold is at least that value |
| `season` | season ID | the season of the day is that one (spec 08); never true in a world without seasons or on a map without world time |
| `tod_between` | `[from_pm, to_pm]` | the time of day (permille, 0 = midnight) is in `[from_pm, to_pm)`; when `from_pm > to_pm` the range crosses midnight (`[800, 250]` is the night); always `from_pm == 0` on a map without world time |

## Effects (closed catalog, v1)

An effect is an object with `effect` plus parameters, applied in list order:

| Effect | Parameters | Result |
|---|---|---|
| `add_xp` | `amount` | `xp += amount`, then the level-up loop of spec 05 |
| `add_gold` | `amount` | `gold += amount` |
| `add_item` | `item`, `qty` | inventory `item += qty` |
| `spend_gold` | `amount` | `gold = max(0, gold - amount)` (guard it with `gold_at_least`) |
| `heal_full` | none | the health of the player becomes the maximum |
| `remove_item` | `item`, `qty` | inventory `item -= min(qty, held)`; the entry disappears at 0 (guard it with `has_item`) |
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
A template has a `type` (`kill` or `collect`), a `target` and the fields above. The target is an enemy or item ID, or one of two values that take the **fauna of the region of the settlement** (spec 09):
`$fauna` (the enemy) and `$drop` (its drop), of the entry `pick(fauna, h >> 48)` (the same weighted choice as spawners: `(h >> 48) mod W`); this way a board asks for what lives around the town. Offers do not depend on the player: the same town shows the same
board to everyone on the same day, and a new one the next day. The offer text depends on the **tone** of the region (spec 09): `quest.board.<template>.<tone>.name` and `.journal`.

**Generated quests.** Accepting an offer starts a quest with the id `board:<sx>:<sy>:<day>:<slot>` and one stage `work` with one objective (`kill` or `collect`, the target and the count)
that ends the quest (there are four templates: `cull` and `gather`, and the larger `purge` and `stockpile` of 8 to 12 kills and 9 to 15 items); its rewards are `add_xp`, `add_gold` and `add_guild_points` with the amounts above, and its texts take the arguments `{count}`, `{target}` (an `$i18n:` key of the target's name)
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

## Local errands (elders)

The tone of a region is also the tone of its elders' dialogue (`base:dialogue/role/elder_<tone>`, spec 09), and there is one tone per region, so each region has **one local errand**: a `side` quest
(`base:quest/side/...`) with a single stage that asks to kill a number of the region's own enemies and to hold a number of the item they drop. Nothing in the engine is new:
the elder's menu shows "Is there anything I can do for you?" until the quest exists, "About that errand..." while it is active, and "The errand is done." once it is done and its payment flag
(`errand_<quest>_paid`) is not set. That last choice runs the payment as dialogue effects (`set_flag`, `add_xp`, `add_gold`, `add_item` of small potions), so the quest itself has no `rewards`
and the payment is made once, by the elder the player talks to, whichever settlement of the region that is. The elder texts are in `roles.json`.

| Tone | Region | Kill | Hold | Payment |
|---|---|---|---|---|
| warm | Verdalis | 8 green slimes | 6 slime gel | 60 XP, 150 gold, 2 potions |
| mystic | Whisperwood | 5 shade wolves | 4 shade wisps | 140 XP, 300 gold, 3 potions |
| gruff | Ironspine | 6 slate slimes | 5 slate shards | 200 XP, 400 gold, 3 potions |
| flowery | Sunscar | 8 sand slimes | 6 slime gel | 180 XP, 380 gold, 3 potions |
| stoic | Frostveil | 6 frost wolves | 4 frost pelts | 260 XP, 520 gold, 3 potions |
| salty | Tidehaven | 6 tide slimes | 5 tide pearls | 170 XP, 360 gold, 3 potions |
| grim | Ashen Wastes | 6 ember slimes | 4 ember cores | 380 XP, 800 gold, 4 potions |
| scholarly | Lumeria | 5 glow slimes | 5 star dust | 280 XP, 560 gold, 3 potions |

A paid errand opens the elder's **second errand** ("Is there a harder job?"): a `side` quest with one `kill` objective against the strongest creature of the region, paid in the same way (flag `hunt_<quest>_paid`)
with XP, gold, guild points and large potions. The targets are the Gel King (Verdalis), the Moonshade Alpha (Whisperwood), the Dire Alpha (Ironspine), the Amber Queen (Sunscar), the Ice Warden (Frostveil),
the Coral Matron (Tidehaven), the Magma Heart (Ashen Wastes) and the Storm Sovereign (Lumeria).

Each elder also has one **seasonal job** (a `side` quest with a `collect` objective on two materials of the region), offered only in its season: "Is there a seasonal job?" leads to the offer when the `season` of the day is the one of the
region and to a line that says when to come back otherwise (the harvest cart in Verdalis, autumn; the wisp bloom in Whisperwood, spring; winter stores in Ironspine; the festival of petals in Sunscar, spring; the short summer in Frostveil;
the storm season in Tidehaven, autumn; the cold ash in the Ashen Wastes, winter; the solstice survey in Lumeria, summer). It is paid by the dialogue (flag `season_<quest>_paid`: XP, gold and two large potions).

## Innkeepers' favors and legends

Like the elders' errands, each region's **innkeeper** (`base:dialogue/role/innkeeper_<tone>`) asks one favor: a `side` quest with a single `collect` objective for a material that a creature of the region drops
(wolf fangs in Verdalis, dire fangs in Whisperwood, slate shards in Ironspine, amber drops in Sunscar, ice crystals in Frostveil, coral fragments in Tidehaven, magma shards in the Ashen Wastes, storm feathers in Lumeria).
The menu shows "Anything you need around the inn?", "About that favor..." and "I brought what you asked." under the same conditions as the elders' (flag `pantry_<quest>_paid`), and the payment is a
dialogue effect list: XP, gold and one or two medium potions. Villagers and innkeepers also answer "Know any old legends?" with a text of the region's tone (`dlg.tone.<tone>.legend`) that says
where its dungeon is. The texts are in `roles.json`.

## Workshops (shopkeepers)

The shopkeeper of every region can **make one unique piece of equipment** from monster parts, once per game: the menu shows "Could you make something from monster parts?" until the flag `craft_<item>_done` is set; the
shopkeeper names the two kinds of parts and how many, and the choice "Here are the parts. Make it." is visible only when the player holds enough of both (`has_item`). It runs `remove_item` for each part, `add_item` of the
result and `set_flag`. The parts are drops of the region's own creatures, so the equipment (a weapon or an armor of rarity rare or epic) is a reward of hunting that region:

| Tone | Region | Parts | Result |
|---|---|---|---|
| warm | Verdalis | 8 wolf fangs, 12 slime gel | Fang dagger (atk 14) |
| mystic | Whisperwood | 6 shade wisps, 3 dire fangs | Wisp mantle (def 7, mdef 8) |
| gruff | Ironspine | 14 slate shards, 6 wolf fangs | Slate cleaver (atk 18) |
| flowery | Sunscar | 8 amber drops, 10 slime gel | Amber plate (def 9, mdef 6) |
| stoic | Frostveil | 8 frost pelts, 4 ice crystals | Frostfur coat (def 10, mdef 7) |
| salty | Tidehaven | 6 tide pearls, 8 coral fragments | Pearl rapier (atk 19) |
| grim | Ashen Wastes | 8 ember cores, 5 magma shards | Ember greatsword (atk 24) |
| scholarly | Lumeria | 8 star dust, 4 storm feathers | Starlit vestment (def 8, mdef 14) |

Villagers and shopkeepers also answer "How is the road around here?" with a text of the region's tone (`dlg.tone.<tone>.road`).

## Inns, commissions and gossip

- **Inns.** Every innkeeper rents a bed and sells food to take along. The bed choice is visible when `gold_at_least` the price (8 to 18 gold by tone); it runs `spend_gold` and `heal_full` and the innkeeper says the player slept.
  Otherwise the same line leads to a polite refusal. The meal choice (honey cake, grilled fish or hearty stew, two to four of them) runs `spend_gold` and `add_item`.
- **Commissions.** Every guild clerk has a `comm_hub` ("Do you have special commissions?") that offers three `side` quests of two stages each (`hunt`, a `kill` objective, then `gather`, a `collect` objective) with the creatures and materials of
  the region. The first needs level 1 to 7 (by region), the second 3 to 11 more and the third up to level 14, and each needs the previous one paid (flag `comm_clerk_<tone>_<n>_paid`). Payment is a dialogue effect list: XP, gold
  (scaled by the danger of the region), guild points and potions (medium for the first two, a large one for the third).
- **Seasons and nights.** Villagers answer "How is the season treating you?" with a line for the season of the day (`season` conditions chained in the dialogue, four lines per tone), and innkeepers offer
  "Any tales for a dark night?" only at night (`tod_between` `[800, 250]`, from 19:12 to 6:00), with one tale per tone.
- **Gossip.** Villagers answer "Any gossip?" with three lines of their tone in a row (`dlg.gossip.<tone>.<n>`).

## Wayfarers

Eight **wayfarers**, named people with a dialogue each (`base:dialogue/npc/<name>`, key `wayfarer_<name>`), stand in the squares of the outposts (spec 09), one tile below the site point of the landmark (`npcs` of the world data).
Each tells a story in three quests (`base:quest/side/way_<name>_1..3`), offered in order by a chain of `quest_done`, `quest_active` and `flag` conditions like Mira's:

1. a **task**: one stage with a `kill` and a `collect` objective on the creatures and materials of the region;
2. a **letter**: stage `deliver` (`talk` to the next wayfarer of the ring), then `report` (`talk` to the sender again). The ring is Tamsin (Verdalis) to Dorn (Ironspine) to Kessa (Ashen Wastes) to Zahra (Sunscar) to Ottavio (Lumeria)
   to Marlo (Tidehaven) to Ilvi (Frostveil) to Elowen (Whisperwood) and back to Tamsin. A talk satisfies the objective before the dialogue starts, so the receiver finds the quest of its sender in stage `report` and shows
   a line about the letter once (flag `letter_<sender>_read`);
3. a **big hunt**: a `kill` and a `collect` objective with larger counts, then a `talk` to report. Its rewards include a unique rare or epic piece of equipment.

When the third quest of all eight wayfarers is done, Mira's dialogue starts with a closing line instead of the chain of letters (a `condition` of eight `quest_done`, once: flag `mira_ring_paid`) and pays 2500 XP, 6000 gold, 600 guild points and the epic Ring-walker's mantle (defense 15, magic defense 15).

Rewards are `add_xp`, `add_gold` and `add_guild_points` of the quest, scaled by the region (100 to 250 percent). Their names are `speaker.wayfarer_<name>` in the texts.

## Journal

The journal lists every quest of the story state: first those in progress (name, the journal text of the current stage with the quest arguments, and the
`current/total` of each kill/collect objective), then the finished ones (name only). It reads only the story state, so it needs no data of its own and a
generated quest (see "Guild") appears like any other. With no quest it shows the text `ui.journal_empty`. Opening the journal pauses the game.

## Presentation (not in the contract)

The dialogue box shows the speaker (`speaker.<key>` text), the text and the visible choices. The quest tracker shows the quest name, the
stage journal text and kill/collect progress as `current/total`.
