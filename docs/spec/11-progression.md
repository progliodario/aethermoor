# 11. Progression: bestiary and titles

Status: **v1 (bestiary, counters, titles with effects, talents, echoes; tags, real skill trees and the full reincarnation come later)**. Reference: `CombatSim._on_kill` and `CombatSim.earned_titles` in `tools/reference/combat.py`.
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

## Talents

`data/base/talents.json` (ID `base:talents/all`, schema `talents`) lists the talents and `points_per_level`. A talent has an `id`, a `name`, a `stat` (`attack`, `health`, `mana`, `defense`, `magic`, `critical` or `speed`), `pct_per_rank`, `max_rank` and, for the branches of the tree, `requires` (`{talent, rank}`).

- **Points.** The player has `(level - 1) * points_per_level` points in all; the points left are that number less the ranks learned.
- **Learning.** `learn_talent(id)` is refused, changing nothing, while a dialogue is open, when the talent does not exist, when no point is left, when the talent is at `max_rank`, and when it `requires` a talent that has not reached that rank yet (its branch is closed). Otherwise the rank goes up by one, the derived stats
  are computed again and the health is capped at the new maximum (it is not refilled).
- **Effect.** When the derived stats are computed (spec 04), after the echoes, each talent with a rank above 0 multiplies its stats, in the order of the data: `stat * (100 + pct_per_rank * rank) / 100` (integer division).
  `attack` is `atk` and `matk`, `health` is `max_hp`, `mana` is `max_mp`, `defense` is `def` and `mdef`, `magic` is `matk`, `critical` is `crit_chance_pm`, `speed` is `move_speed_x100`.
- **Save.** `talents` in the save document (spec 12) is an object from talent ID to rank; absent when nothing was learned.

The base pack has a tree of ten talents and one point a level (`tools/make_talents.py`): four roots of ten ranks, Might (attack, 5 percent a rank), Vigor (health, 6), Focus (mana, 8) and Guard (defense, 8); a second ring of five ranks that opens at rank 5 of its root, Keen Eye (critical, 15; after Might), Second Wind (health, 8; after Vigor), Arcana (magic, 10; after Focus) and Fleet Foot (speed, 4; after Guard); and a crown, Legend (attack, 10; after Keen Eye 5) and Bulwark (defense, 12; after Second Wind 5).
Both clients show them in the crafting panel (`Tab` on a keyboard, a button of the panel on Android). Conformance: the scenarios `talents_learned` and `talent_tree` (their checkpoints carry `talents`, `talent_points`, `max_hp`, `max_mp`, `matk`, `crit_chance_pm`, `move_speed_x100`). The panels show what opens a closed branch.

## Titles with effects

A title may have `atk_pct`: while the title is earned, the attack of every hit of the player (the `atk`, or the `matk` of a magical skill) is `atk * (100 + sum of atk_pct of the earned titles) / 100`, computed
before a weaken on the player takes its quarter (spec 05). The sum is read at each hit, so a title earned in the middle of a fight counts from the next blow. The companion's hits are not changed. In the base pack every title
is worth 3 percent, the first one 2, and the rare ones 5, 8 or 10 (`tools/make_titles.py`): with all fifteen the hits are 65 percent stronger. Conformance: the scenario `title_attack`.

## Reincarnation

A game whose protagonist has reached **level 10** can be **reincarnated** from the title screen (desktop: `R` on the game, then `R` again to confirm; Android: the `Rebirth` button of the row, twice). The game ends: the profile
(spec 12) gains one **past life** (`lives += 1`), and the slot is emptied (its saves, the protagonist kept for it and its goal), so the next game there chooses who to be. A game below level 10 is refused and nothing changes.
What the game had reached is already in the profile, which every save updates. Past lives never go down.

## Heirloom

When a game is reincarnated, **half of its gold** (`gold * 50 / 100`, from the autosave the title screen reads) is added to the **heirloom** of the profile. The next **new game** (a slot without a save, in any slot) takes the whole
heirloom when it starts: its gold goes up by it, the profile's heirloom goes back to 0, and a notice says how much it was. Several reincarnations before a new game add up. Reference: `reincarnate` and `claim_heirloom` in
`tools/reference/profile.py`; conformance: the suite `profile`.

## Echoes

What the player reached in past games is not lost: every title in the profile (spec 12, "Profile") is an **echo**, and so is every past life: a game that starts, or is loaded, has `echo_pct = min(number of titles in the profile, 15) + 3 * min(lives, 10)`, 45 at most.
The maximum health of the player is `max_hp * (100 + echo_pct) / 100` (integer division), computed after the formula of spec 04 and before anything else uses it (healing, burn, the death save). The echoes are the
same in all the games and are not saved in them (the profile is read when the game is built). The titles soften a new life; the past lives are what makes a Guest who has lived many times plainly stronger than one who has not.
Reference: `CombatSim._derive` (`echo_pct` of the scenario) and `echo_pct`, `reincarnate` in `tools/reference/profile.py`; conformance: the scenario `echo_health` and the suite `profile`.

## Display

The journal (spec 07) shows, after the quests, the companion (name, whether it stays or follows, its bond and the attack the bond adds, spec 10), the counters and the echoes, then the titles (the ones not earned yet as `???`) and the bestiary (name and kills, by ID). The name of a creature is the text key `enemy.<name>.name`.

## Later

Tags (traits earned by how one plays), a chosen carry-over for the reincarnation (today a past life gives health to every game and half of its gold to the next one), and titles with other effects than attack.
