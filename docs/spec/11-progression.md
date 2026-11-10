# 11. Progression: bestiary and titles

Status: **v1 (bestiary and titles; tags and reincarnation come later)**. Reference: `CombatSim._on_kill` and `CombatSim.earned_titles` in `tools/reference/combat.py`.
Schema: `schemas/titles.schema.json`. Conformance: the scenarios `bestiary_titles`, `counter_titles` and `board_quest_rewards` of the suite `combat` (the checkpoints carry `bestiary`, `counters` and `titles`).

## Bestiary

Every time a creature dies by the hand of the player (or of the companion, spec 10) the **bestiary** counts it: `bestiary[id] += 1`, with `id` the ID of the creature (`base:enemy/slime_green`).
A creature without an ID is not counted. The bestiary is a map from ID to kills; its size is the number of **species** met. It is saved (`bestiary` in the save document, spec 12; absent when empty and in older saves)
and it is the same for all the maps of a game.

## Counters

Three **counters** tell how one plays: `gathered` goes up by one for every gathering that finds a prop (spec 06, even when it gives nothing), `crafted` for every recipe made (a refused one does not count),
`parried` for every attack stopped by a parry (spec 05). They are saved (`counters` in the save document, spec 12; a counter at zero is absent). These are the first step of the tags: a title can ask for them.

## Titles

`data/base/titles.json` (ID `base:titles/all`) lists titles in order of rank: `id`, `name` (a text key) and a condition, `kind` and `count`:

| kind | the title is earned when |
|---|---|
| `kills` | the player has killed `count` creatures in all |
| `kills_of` | the bestiary holds at least `count` kills of `enemy` |
| `level` | the player is at level `count` or more |
| `species` | the bestiary holds `count` creatures or more |
| `quests` | `count` quests are finished |
| `gathered`, `crafted`, `parried` | the counter of that name is at `count` or more |

The titles earned are **not saved**: they are computed from the state, in the order of the data (`earned_titles`), so a title cannot be lost nor given twice, and a new title in a later version is
earned at once by those who already satisfy it. The last title earned is the one that counts as the current one.

## Titles with effects

A title may have `atk_pct`: while the title is earned, the attack of every hit of the player (the `atk`, or the `matk` of a magical skill) is `atk * (100 + sum of atk_pct of the earned titles) / 100`, computed
before a weaken on the player takes its quarter (spec 05). The sum is read at each hit, so a title earned in the middle of a fight counts from the next blow. The companion's hits are not changed. In the base pack every title
is worth 3 percent, the first one 2, and the rare ones 5, 8 or 10 (`tools/make_titles.py`): with all fifteen the hits are 65 percent stronger. Conformance: the scenario `title_attack`.

## Echoes (the first form of reincarnation)

What the player reached in past games is not lost: every title in the profile (spec 12, "Profile") is an **echo**, and a game that starts, or is loaded, has `echo_pct = min(number of titles in the profile, 15)`.
The maximum health of the player is `max_hp * (100 + echo_pct) / 100` (integer division), computed after the formula of spec 04 and before anything else uses it (healing, burn, the death save). The echoes are the
same in all the games and are not saved in them (the profile is read when the game is built). One percent for each title is small on purpose: it softens a new life, it does not replace playing it.
Reference: `CombatSim._derive` (`echo_pct` of the scenario); conformance: the scenario `echo_health`.

## Display

The journal (spec 07) shows, after the quests, the companion (name, whether it stays or follows, its bond and the attack the bond adds, spec 10), the counters and the echoes, then the titles (the ones not earned yet as `???`) and the bestiary (name and kills, by ID). The name of a creature is the text key `enemy.<name>.name`.

## Later

Tags (traits earned by how one plays), the full reincarnation (a new life with a chosen carry-over, not only the echoes), and titles with other effects than attack.
