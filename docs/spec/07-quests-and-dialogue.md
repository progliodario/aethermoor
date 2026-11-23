# 07. Quests, dialogue, conditions and effects

Status: **v1.6 (M4a quests and dialogue, then the guild, the journal, jobs, workshops, inns, seasons and the people of the outposts; the conditions and effects are in the tables)**. Reference: `tools/reference/combat.py` (class `CombatSim`, story part).
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
| `day_mod` | `{every, at}` | the day of the world is the day `at` of a cycle of `every` days: `(day - 1) % every == at`, where `day` is the day of the world (spec 08; 1 on a map without world time) |
| `faction_at_least` | `{faction, count}` | the standing with the faction (the counter `faction:<faction>`, see "Factions") is at least `count` |
| `renown_at_least` | integer | the renown of the region where the player stands is at least that value (see "Renown") |

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
| `temper` | optional `gold` (default 0) | when the gold is at least `gold` and a worn piece can be tempered (spec 06, "Tempering": the worn weapon whose item has `affix_roll`, else the worn armor), its roll is drawn again and the better kept, and `gold` is paid; otherwise nothing happens and nothing is paid |
| `open_shop` | optional `region`, `markup_pct` | opens the shop of the place (spec 06); nothing changes when the world has no shop there. With a `region` it opens the goods of that region at `markup_pct` percent (default 100) of its prices (spec 06, "Goods from afar") |

## Quests

A quest has ordered **stages**; each stage lists **objectives** and the `next` stage name or `end`. A quest may have `args` (strings) for its texts, like dialogues (see below).

- Objectives: `kill {enemy, count}`, `collect {item, count}` (satisfied while the inventory holds `count`), `talk {npc_key}` (satisfied once).
- Starting a quest puts it on its first stage with all progress at 0, then refreshes `collect` objectives. A quest that exists already
  is not started again (`start_quest` is ignored), unless the quest is `repeatable` (default false) and done: then it starts anew, on its
  first stage, not done, and pays its rewards (and counts for the renown and its faction) again when it is done again. Conformance: the
  scenario `repeatable_quest` of the suite `story` and a save split of it.
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
- **Travellers**: an NPC may have `route`, a list of positions (tiles; `[dx, dy]` from the centre of the world in the world data). On day `d`
  (spec 08; 1 without a clock) it stands at stop `(d - 1) % len(route)`: at the start of every tick, after the clock advances, the
  travellers are put where the day says (before a tick, where their data puts them; after a game is loaded, at once where the loaded day says). A traveller is **never solid**. Conformance: the
  scenario `traveller_moves` of the suite `story` (a day of 60 ticks) and a save split of it.
- **Residents**: an NPC may have `when`, a condition of the closed catalog above. It is there only while the condition holds: otherwise it is not drawn and cannot be talked to (`interact` and the `talk` event skip it). A resident is **never solid**, there or not, so that its coming and going never moves the player or a creature. In the scenarios the NPCs of `story.npcs` may have `when`; in the world data, the entries of `npcs` (spec 09). Conformance: the scenario `resident_arrives` of the suite `story` and a save split of it.

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

## Standing bounties

The clerk of the guild in every town of a region keeps a **standing bounty** on a great creature of the region (`tools/make_standing_bounties.py`):
`base:quest/side/bounty_standing_<region>`, `repeatable` (section "Quests"), on the Gel King (Verdalis), the Moonshade Alpha
(Whisperwood), the Forge Tyrant (Ironspine), the Sand Sentinel (Sunscar), the Ice Warden (Frostveil), the Coral Matron (Tidehaven), the
Magma Heart (the Ashen Wastes) and the Storm Sovereign (Lumeria). Guardians come back like every creature (spec 08, "Respawn"), so the
bounty can be taken again and again: offered while it is not active, it pays experience, gold and guild points that grow with the danger
of the region, for the Guild.

## Inns, commissions and gossip

- **Inns.** Every innkeeper rents a bed and sells food to take along. The bed choice is visible when `gold_at_least` the price (8 to 18 gold by tone); it runs `spend_gold` and `heal_full` and the innkeeper says the player slept.
  Otherwise the same line leads to a polite refusal. The meal choice (honey cake, grilled fish or hearty stew, two to four of them) runs `spend_gold` and `add_item`.
- **Commissions.** Every guild clerk has a `comm_hub` ("Do you have special commissions?") that offers three `side` quests of two stages each (`hunt`, a `kill` objective, then `gather`, a `collect` objective) with the creatures and materials of
  the region. The first needs level 1 to 7 (by region), the second 3 to 11 more and the third up to level 14, and each needs the previous one paid (flag `comm_clerk_<tone>_<n>_paid`). Payment is a dialogue effect list: XP, gold
  (scaled by the danger of the region), guild points and potions (medium for the first two, a large one for the third).
- **Seasons and nights.** Villagers answer "How is the season treating you?" with a line for the season of the day (`season` conditions chained in the dialogue, four lines per tone), and innkeepers offer
  "Any tales for a dark night?" only at night (`tod_between` `[800, 250]`, from 19:12 to 6:00), with one tale per tone.
- **Gossip.** Villagers answer "Any gossip?" with three lines of their tone in a row (`dlg.gossip.<tone>.<n>`).

## Pip

Pip (`tutor_pip`, `base:dialogue/npc/pip`) stands in the meadow next to the start, two tiles from Mira. His dialogue is a menu of six questions of a new player (fighting, healing, money, the Threshold Stones, where to go first, not getting lost), each answered by one line that leads back to the menu. Besides them, a question per protagonist that is shown only to the one who holds that protagonist's keepsake (`has_item`) opens its two personal quests in order (spec 18, "Personal stories").

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

## Renown

The **renown** of a region is the number of quests the player finished while standing in it: when a quest becomes done (its last stage is complete, before its rewards are applied) the counter `renown:<region id>` goes up by one (spec 11, "Counters"; a map without regions counts under `renown:`, a conformance scenario under `renown:<region>` of its `region`). Every quest counts: the stories, the errands, the board of the guild. It is saved with the other counters, so the save format does not change.

- **Prices.** A shop has `renown_step_pm` and `renown_max_pm` (`regions[].shop` in the world data, spec 09): while it is open the renown of the region takes `discount_pm = min(renown_max_pm, renown * renown_step_pm)` off the buying prices (spec 06, "Shops"); selling is not changed. The base pack takes 15 permille for each quest, up to 250 (a quarter off after seventeen quests), in every region.
- **Wares for friends.** A shop may have `renown_stock`, a list of `{item, renown}`: when the shop opens, every item whose `renown` the renown of the region has reached joins the stock, after the usual goods; a quest finished while the shop is open counts from the next time it opens. In the base pack every region keeps two rare or epic pieces of its own for somebody with five and with ten quests there.
- **A task for a friend.** In the base pack the elder of every settlement offers one more quest to somebody with eight quests in the region (`base:quest/side/friend_<region>`, `tools/make_friend_quests.py`): a hunt of a strong creature of the region, offered, followed and paid like the errands (the flag `friend_<region>_paid`), for `150 * danger` experience, `400 + 200 * danger` gold and two large potions.
- **Dialogue.** The condition `renown_at_least` holds when the renown of the region where the player stands is at least its value. In the base pack (`tools/make_renown_talk.py`) the elder and the shopkeeper of every settlement greet as a friend somebody with three quests in the region, and the innkeeper gives a bed for nothing (the effect `heal_full`) from five.
- **Titles.** A title can ask for the counter of a region (`kind` `renown:<region id>`): the base pack has a "Friend of ..." for each of the eight regions, at ten quests.
- **Presentation.** The shop panel says how much the renown takes off ("Renown -15%"), and the status window the quests finished in the region where the player is.

Conformance: the scenarios `renown_prices`, `renown_dialogue` and `renown_wares`.

## Factions

A quest may have a `faction`. When it becomes done, besides the renown of the region, the counter `faction:<faction>` goes up by one (spec 11, "Counters"; saved with the others). The quests of the board count for `guild` (spec 07, "Guild": `quest_from_offer` gives it). A title can ask for a faction (`kind` `faction:<id>`), and the status window lists the standing with every faction met ("Standing: the Guild 3   the Folk 7"; the names are `faction.<id>.name`).

The base pack has four (`tools/set_factions.py`, which gives every quest its faction from its file name and is run by the tools that write quests): **the Guild** (the board, the clerks, Hestia's bounties, the great dungeons), **the Ring of Wayfarers** (the wayfarers, the letters and the parcels of the courier), **the Chroniclers** (Selwyn's legends) and **the Folk** (everything else: the towns, the outposts, the errands, the pantries, the seasons, the tasks for a friend). The stories of the protagonists count for none. The factions also give: the guild clerks hand the **Guild signet** (an accessory: attack +14, critical +5%) to somebody with ten quests of the guild, and the elders the **Folk charm** (health +80, defense +4) to somebody with twenty of the folk; once a game, whoever is asked (the flag `faction_gift_<faction>`; `tools/make_faction_gifts.py`). Mira gives the **Wayfarer's band** (health +40, magic defense +8) to somebody with twelve quests of the Ring, and Selwyn the **Archivist's quill** (magic attack +12, critical +4%) for five legends: their dialogues open with the gift, once, and then go on as before. Four titles: Champion of the Guild (15 quests, +10% experience), Ring-walker (12, one more of every drop gathered), Keeper of Legends (5) and Heart of the Folk (30, one more of every recipe made). Conformance: the scenarios `faction_standing`, `faction_dialogue` (and `board_quest_rewards`, whose quest counts for the guild).

## Tales of the villagers

The villagers of every region have a trouble of their own, told in three quests one after the other (`base:quest/side/tale_<region>_1`, `_2` and `_3`, `tools/make_region_tales.py`): each asks to hunt some creatures of the region and to bring back what they leave (the mint slimes of the kitchen gardens of Verdalis, the owls that fell silent in Whisperwood, the bats in the shafts of Ironspine, the picnic thieves of Sunscar...). Any villager of the region offers them, follows them and pays them, like the elders' errands: each opens once the one before is paid (the flags `tale_<region>_<n>_paid`); the reward is experience and gold that grow with the danger of the region and with the tale, and medium potions. The third tale is a harder hunt (the boars in the turnips of Verdalis, the golems in the quarries of Ironspine, the nebula slimes in the observatory domes of Lumeria...). Twenty-four quests, all for the Folk.

## Feasts

Every region has a **feast day** in the cycle of eight days of the pedlars (section "People of the towns"): the day its own goods
would be on the pedlars' carts (`day_mod` with `every` 8 and `at` the index of the region in the cycle: Verdalis 0, Whisperwood 1,
Ironspine 2, Tidehaven 3, Frostveil 4, Sunscar 5, Lumeria 6, the Ashen Wastes 7). On that day the innkeeper of every village and town
of the region has one more choice, first in the menu: the Guest eats with the village (`heal_full`), the first time also takes home
two dishes of the region (the flag `feast_<region>_gift`; one ember brew in the Ashen Wastes) and then the feast market opens, the goods
of the region at 75 percent (`open_shop` with the `region`, spec 06, "Goods from afar"). Each region has its own: the Harvest Feast
of Verdalis, the lanterns of Whisperwood, the Forge Day of Ironspine, the Blessing of the Boats of Tidehaven, the Long Night of
Frostveil, the Festival of Lanterns of Sunscar, the Night of the Comet of Lumeria and the Ember Wake of the Ashen Wastes
(`tools/make_feasts.py`). After the words of the feast the innkeeper says how the feast is kept in the season of the day (the
condition `season`: flowers in spring, tables under the stars in summer, the harvest in autumn, the great fire indoors in winter).

On the feast day the innkeeper also offers the **games of the feast** (one more choice, after the feast): a contest of the region,
`base:quest/side/feast_<region>` (for the Folk), offered while it is neither active nor done: the pie contest of Verdalis (berries and
eggs), the lantern weaving of Whisperwood (fern fronds), the stone toss of Ironspine (stone chunks), the biggest catch of Tidehaven (a
golden carp and river fish), the ice carving of Frostveil (ice crystals), the scent of the festival of Sunscar (drops of amber), the
counting of the stars of Lumeria (star dust) and the ember walk of the Ashen Wastes (ember cores). A contest started can be finished on
any day, and the innkeeper asks how it goes; it pays experience and gold that grow with the danger of the region, a tempering oil
(spec 06, "Tempering") and a prize of the region.

The **villagers** talk of the feasts too (two more choices of their menu, first): on the feast day of their region they wish the Guest
a happy feast; on the feast day of the next region of the cycle (the neighbours) they tell that half the village has gone there.

## People of the towns

Fenwick and Aldermere have people with names (`tools/make_towns.py`), and two more written by `tools/make_home.py`:

- **Nana Brin**, in the house of Fenwick with the chest (spec 06, "Chests"): she lets the Guest sleep by her hearth for free (`heal_full`) and asks three small favours, one after the other, each a collection paid with gold, experience and something from her kitchen: ten logs of wood (`base:quest/side/brin_firewood`), eight bunches of wildflowers (`brin_posies`) and three boar hides (`brin_hides`). They count for the Folk.
- **Corvin the pedlar**, on the square of Aldermere: his cart goes round the eight regions, one a day, in a cycle of eight days (the condition `day_mod` with `every` 8), and he opens the shop of the region of the day (`open_shop` with a `region` and `markup_pct` 110, spec 06, "Goods from afar"). Conformance of the condition: the scenario `day_cycle`.
- **Old Tam**, keeper of **the Guest's cottage** east of Fenwick (the landmark `guest_cottage`, spec 09): anyone may sleep by its fire for free (`heal_full`). When Nana Brin's three favours are done she gives the cottage to the Guest (the flag `cottage_given`), and Tam welcomes its owner home. The cottage has a chest (spec 06, "Chests"), a campfire, an anvil, three garden plots, a hen coop, a goat pen and a Threshold Stone.
- **The pedlars of the roads**: one at the outpost of every region (Hobb, Fennick, Garrow, Marisol, Ylva, Rashid, Celeste and Tarn). Their carts go round the same cycle as Corvin's, each a day ahead of the one before, so that on any day the pedlars sell the goods of different regions, at 115 percent. Each greets the Guest the first time (the flag `<name>_met`).
- **Odo, the master of the caravan** (`tools/make_caravan.py`), a merchant who really travels: his wagons go round the eight outposts in the cycle of the pedlars, one a day (his `route`: day 1 the outpost of Verdalis, then Whisperwood, Ironspine, Tidehaven, Frostveil, Sunscar, Lumeria, the Ashen Wastes), and he sells at the plain price the goods of the region where he goes the next day (`open_shop` with `region` and `markup_pct` 100, the condition `day_mod`). He greets the Guest the first time (the flag `odo_met`), and before his goods he offers three errands for the caravan, one after the other, each a collection that counts for the Ring of Wayfarers: twelve logs for the axles, eight lumps of iron ore for the horses, five travel rations for the long road (`base:quest/side/way_odo_axles`, `way_odo_horseshoes`, `way_odo_provisions`), paid with gold, experience and a gale rune, potions and the shepherd's blade.
- **Brannoc, the wandering smith** (`tools/make_wandering_smith.py`), the second traveller: he goes round the eight outposts the other way from Odo (day 1 Verdalis, then the Ashen Wastes, Lumeria, Sunscar, Frostveil, Tidehaven, Ironspine, Whisperwood), greets the Guest the first time (the flag `brannoc_met`), says where he goes tomorrow and tempers the worn piece for 40 gold (the effect `temper`). The **shopkeepers** of the villages and towns keep an anvil too and temper for 60 gold (`tools/make_smiths.py`; the choice right after the wares). Conformance of the effect: the scenario `smith_tempers` of the suite `story`.
- **Lark, the wandering bard** (`tools/make_bard.py`), the third traveller: she goes round the eight outposts four days ahead of Odo (day 1 Frostveil, then Sunscar, Lumeria, the Ashen Wastes, Verdalis, Whisperwood, Ironspine, Tidehaven) and carries the news. For every region whose villagers' third tale the Guest finished (`tale_<region>_3`, section "Tales of the villagers") she has a song: asked, she sings the first one not heard yet (the flag `bard_<region>`, 120 experience); when all eight are heard she gives a dawn rune once (the flag `bard_gift`); without a new song she says where she goes tomorrow. She greets the Guest the first time (the flag `lark_met`). Every season she offers **the hunt of the season** (`base:quest/side/way_lark_hunt_<season>`, `repeatable`): six slimes of the creature of that season (rain in spring, sun in summer, leaves in autumn, snow in winter), offered on a day of the season while it is not active, and paid every time. Her quest, **the Song of the Road** (`base:quest/side/way_lark_road_song`, for the Ring of Wayfarers), sends the Guest after the other two travellers: three `talk` stages, Brannoc, then Odo, then Lark again, wherever the day puts each of them (the map points at where they stand today); it pays experience, gold, a gale rune and two tempering oils. Whoever won the games of all eight feasts (section "Feasts") gets from her, once, the **ribbon of the eight feasts**, an accessory (+4 attack, +40 health, +5% critical chance; the flag `lark_feasts_gift`).
- **The settlers of the villages** (`tools/make_settlers.py`): every village stamp (`village`, `village_b` to `village_d`) has a slot of the role `settler`, its last one, and the world data says `"role_when": {"settler": {"renown_at_least": 8}}` (spec 09, "Settlement people"): the settler of a generated village is there once the Guest has finished eight quests in its region. It greets the Guest in the voice of the region, tells why it came (the roads are safe now) and shares something warm (`heal_full`). Every settler has a **trade** of its region: the baker of Verdalis, the tea-brewer of Whisperwood, the stonemason of Ironspine, the spice seller of Sunscar, the ice fisher of Frostveil, the net-mender of Tidehaven, the charcoal burner of the Ashen Wastes and the lens grinder of Lumeria. Its quest (`base:quest/side/settle_<region>`, for the Folk) asks for two things of the region to gather, so that the workshop can open, and pays experience and gold that grow with the danger of the region and something the trade makes. Then the settler thanks the Guest once (the flag `settle_<region>_thanked`) and opens its workshop: the goods of its region at 90 percent (`open_shop` with the `region` and `markup_pct` 90, spec 06, "Goods from afar"). Any settler of the region gives, follows and pays the quest. It is `repeatable` (section "Quests"): once thanked, the settler asks for the same things again ("Does the workshop need more?"), paid every time.
- **The residents of the outposts** (`tools/make_residents.py`): eight people who move to the outpost of a region once the Guest is known there (`"when": {"renown_at_least": 6}`, section "Renown"): Maela the farmer (Verdalis), Sorrel the herb-witch (Whisperwood), Bram the stonecutter (Ironspine), Yasmin the caravan cook (Sunscar), Hald the ice fisher (Frostveil), Cormac the retired sailor (Tidehaven), Ash the cinder-gardener (the Ashen Wastes) and Ines the apprentice astronomer (Lumeria). Each greets the Guest, gives a rune of the region once (spec 06, "Runes"; the flag `resident_<name>_gift`) and then has a word about the new life there.

## Journal

The journal lists every quest of the story state: first those in progress (name, the journal text of the current stage with the quest arguments, and the
`current/total` of each kill/collect objective), then the finished ones (name only). It reads only the story state, so it needs no data of its own and a
generated quest (see "Guild") appears like any other. With no quest it shows the text `ui.journal_empty`. Opening the journal pauses the game.

## Presentation (not in the contract)

The dialogue box shows the speaker (`speaker.<key>` text), the text and the visible choices. The quest tracker shows the quest name, the
stage journal text and kill/collect progress as `current/total`.

## Places

Every quest stage sends the player somewhere. This is not a rule of the simulation (nothing here changes the state or the vectors): it is how the clients guide, and both find the place the same way,
for the current stage of each quest in progress, in this order:

1. `place`, when the stage has it: the ID of a landmark of the world data (spec 09). `tools/set_quest_places.py` gives every stage that asks to defeat a guardian the place of its lair (62 quests of the
   base pack); the generators of quests run it.
2. Else the first objective that tells where, in the order of the objectives:
   - **talk**: the person to talk to (a person of the story data, or a person of a settlement), where they stand;
   - **kill** or **collect**: the creatures that are the target, or that drop the item asked for (the drops of the enemies of the world and of the fauna of every region); the nearest landmark
     whose stamp has a spawner of one of them; else the nearest outpost (a landmark of kind `hamlet`) in a region whose fauna has one of them.
3. Else, for a **collect** objective of something gathered (spec 06, "Gathering"), the nearest prop within 48 tiles of the player, among the land already loaded, whose node drops it
   (reeds for fish, bushes for berries...): the name shown is `ui.place_nearby`.
4. Else the nearest outpost: it covers what grows anywhere when nothing is near (berries, wood, ore).

"Nearest" is measured from the player, in tiles (squared distance, the first in the order of the data on a tie). The name shown is the landmark's name, the person's name, or `speaker.<key>`.

The clients use the place three times:

- **The goal of the map** (spec 09, "The map view"): when the player has no goal, the first quest whose current stage has not done it before in this session puts the goal there and says so
  (`ui.goal_quest`). A goal the player set is never moved, and each stage does it once.
- **The quest tracker and the journal** show a line under each quest in progress: `ui.quest_place` ("Go to: Mint Hollow").
- **Choosing the quest**: `Q` on the map (the [Quest] button on Android) moves the goal, and the view, to the place of the next quest in progress, in the order of the quests; with none it says `ui.no_quest_place`.
- **The map view** draws an orange square on the place of every quest in progress, kept inside the view, with its key (`ui.map_key_quest`).
