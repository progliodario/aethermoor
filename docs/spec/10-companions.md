# 10. Companions

Status: **v1.3 (a follower that fights, the stay command, a bond that grows with its kills, care: a close companion heals the player, the party: more companions, one of them at a time, and the duo strike)**. Reference: `CombatSim._update_companion` in `tools/reference/combat.py`.
Schema: `schemas/companion.schema.json`. Conformance: the scenarios `companion_fights`, `companion_follows`, `companion_stays`, `companion_bond` and `companion_duo` (the checkpoints carry `companion`: position, `stay`, `bond`) of the suite `combat`.

Every protagonist has a **companion** (`companion` in the protagonist data, spec 18): a small creature that walks with the player and hits the enemies near it now and then, so that fights are
shared. It cannot be hurt, it is saved with the game (spec 12), and the creatures ignore it: it is help, not a second character to look after.

## Data

`data/base/companions/<name>.json` (ID `base:companion/<name>`): `name` (a text key), `art` (the creature art it is drawn with), `scale_pct` (its size on screen), `atk_base` and `atk_per_level`
(its attack is `atk_base + atk_per_level * (player level - 1)`), `range_x100` (how far from itself it hits, besides the radius of the creature), `cooldown_ticks` (the wait between two hits),
`speed_x100` (tiles per second times 100) and `follow_x100` (the distance it keeps from the player). The base pack has eight: Orb (Ren), Newton (Sakura), Ember (Daichi), Pip (Haruka), Pot (Marco),
Shade (Yuki), Mort (Lena) and Gloom (Gideon); `tools/make_companions.py` writes them.

## Rules (normative)

The companion has a position, a cooldown and a body of radius 0.25. It starts on the player's position with its cooldown at `cooldown_ticks`. Every tick, **after the player's attack has been
advanced and before the creatures are updated** (spec 03):

1. With `dist` the distance to the player: when `dist` is above 8 tiles it is put on the player's position (this also follows a Threshold Stone); otherwise, when `dist` is above `follow`, it moves toward the player by
   `min(speed * dt, dist - follow)` and its position is resolved against the walls and props as a creature's is, with radius 0.25.
2. The cooldown goes down by one if it is above 0. If it is still above 0, nothing more happens.
3. The target is the living creature with the smallest distance `d` to the companion among those with `d <= range + radius of the creature` (the first in list order on a tie). With no target nothing happens (the cooldown stays at 0, so
   it hits the moment a creature comes in range).
4. It hits: the damage formula (spec 04) with `atk` as above, `power_pct` 100, the creature's `def`, the levels of the player and of the creature, `variance_pm` 1000, no critical hit and no element, and no random number is drawn.
   The cooldown goes to `cooldown_ticks`. A creature at 0 health or less dies as in "Kill" (spec 05): its loot and its experience are the player's.

A hit gives the same `hit` and `die` cues as the player's (spec 14), so the creature is heard, and a floating number. Drawn: the creature art, at `scale_pct`, bobbing a little, sorted with the others by its feet.

## Teamwork

Every hit of the player marks the creature it hit and unmarks every other one (not saved). In step 3, a marked living creature within reach is the target, whatever the distance of the others; otherwise the nearest one is, as
above. So the companion fights what the player fights. Conformance: the scenario `companion_teamwork`.

## Commands

The command `companion_stay` (desktop: `H`; Android: the `Stay` / `Follow` button) switches the companion between **following** and **staying**. While it stays, step 1 does not move it; it still hits what comes in its range.
When the player is more than 8 tiles away the companion is put on the player's position as in step 1 and follows again. The command does nothing without a companion.

The command `companion_recall` (desktop: `G`, an action of the configurable keys; Android: the `Come` button next to `Stay`) calls the companion back: it is put on the player's position at once and follows again, whatever it was doing. It does nothing without a companion. Conformance: the scenarios `companion_recall` and `companion_recall_without`.

## Moments of the bond

A companion may have `moments`, a list of `{bond, text}` (presentation only): when its bond reaches `bond`, the client shows the `text` as a notice, once a game (the story flag `moment_<companion id>_<bond>` remembers it; one moment a frame). In the base pack every companion has three, at bonds 5, 15 and 30 (`tools/make_companions.py`): a small scene in its own manner (Pip shares its lunch, a leaf; Mort spins a bandage of silk).

## The tamed friend

A protagonist with the gift `friend_atk_pct` (spec 18) keeps the last creature it tamed as a **tamed friend**, a second companion: when `tame` succeeds (after everything a kill does), the friend becomes that creature (its definition, at its position, with a cooldown of 50 ticks), in place of the one before. Every tick, after the companion:

1. **Follow.** Farther than 8 tiles from the player it is put on the player's position; else, farther than 1.6 tiles, it moves toward the player by `max(speed_x100 of its creature, 320) / 100 * tick` tiles (never closer than 1.6), and is resolved against the world with the radius of its creature. It never stays.
2. **Hit.** Its cooldown goes down by one; at 0 it hits the nearest living creature whose centre is within `2.0 + its radius` tiles (the first one in the order of the world, of two at the same distance): `damage(atk of its creature * friend_atk_pct / 100, power 100%, the defense of the target, the levels of the player and of the target, variance 1000, no critical)`, and the cooldown is 50 again. A creature it kills is a kill of the player.

It obeys the commands of the companion: `companion_stay` makes it stay or follow with the companion (a friend that stays does not move in step 1 until it is more than 8 tiles away, which also makes it follow again), and `companion_recall` puts it on the player's position, following. Creatures never attack it; it cannot die. A save keeps it (`friend` in the save document, spec 12); a save of a creature the world no longer knows loses it. The checkpoints of the scenarios carry `friend` (`enemy`, `x`, `y`, `stay`) when there is one. The clients draw it with the art of its creature, three quarters of its size, and name it in the journal. Conformance: the scenarios `gift_tame_friend` and `friend_commands`.

## The party

The protagonist's companion is the first of a **party**. The dialogue effect `recruit_companion {companion}` (spec 07; an ID of
`data/base/companions/`) adds a companion to it, last, and makes it the one that follows at once; a companion unknown to the game or
already in the party changes nothing. One companion of the party at a time is **active**: it is the companion of every rule above
(it follows, hits, stays, cares, grows its bond, is drawn). The others wait: they are not in the world.

The command `companion_switch` makes the next companion of the party active (after the last, the first). It is refused, changing
nothing, with fewer than two in the party and while a dialogue is open. **Making a companion active**: the bond of the one that was
active waits with it (each companion of the party has its own bond, which is never lost); the new one is put on the player's position,
following, with its cooldown at its `cooldown_ticks`, its care counter at 0 and the bond that waited for it (0 the first time). The
tamed friend (below) stays as it is. A save keeps the party, the companion that follows and the bonds that wait (`party`, `bonds` and
`companion.id`, spec 12). The checkpoints of a scenario with `companions` (the definitions that may join) carry `companion.id`,
`party` and `bonds`. Desktop: `O` (an action of the configurable keys, `switch`); Android: the `Next` button next to `Stay` and `Come`,
shown when the party has another companion; a notice names the one that follows.

The base pack has four companions that may join (`tools/make_party.py`), the strays of the Guest's cottage, which Old Tam lets its
owner take along (spec 07, "People of the towns"): Biscuit, the dog Odo's caravan left behind (art of the tawny wolf at 55%); Hoot, the
owl of the barn, from level 10 (the night owl, 60%); Sly, the fox of the garden, for three wild berries (the dune fox, 60%); and Cinder,
the ember slime by the anvil, for an ember core (70%; it keeps the Guest warm: care from bond 10). Conformance: the scenario
`party_of_companions` and two save splits of it.

## Bond

Every creature killed by a hit of the companion adds one to its **bond**, before the kill is handled. Its attack is `atk_base + atk_per_level * (player level - 1) + min(bond / 5, 10)`: one more point every five kills,
ten at most. The bond and the stay command are saved with the companion (`stay`, `bond` in `companion` of the save document, spec 12; absent when false and 0).

## Care

A companion may have `care_bond`, `care_ticks` and `care_pct` (all optional, 0 when absent). While its bond is at least `care_bond` and `care_ticks > 0`, every tick of step 1 (after it moves,
before it looks for a target) adds one to a counter; when the counter reaches `care_ticks` it goes back to 0 and, if the player is alive and hurt, the player's health becomes
`min(max_hp, hp + max(1, max_hp * care_pct / 100))`. The counter is not saved and starts at 0. The base pack gives every companion `care_bond` 10, `care_ticks` 600 and `care_pct` 5 (`tools/make_companions.py`):
after ten kills together it heals 5% of the health every ten seconds. Conformance: the scenario `companion_care` (without care, the same fight kills the player).

## Duo strike

A companion may have `duo_bond`, `duo_pct`, `duo_range_x100` and `duo_cooldown_ticks` (all optional, 0 when absent; without `duo_pct`
there is no duo strike). The companion keeps a **duo counter**, 0 at the start. In the player's hits (spec 05), after a hit of the
**power strike** has been dealt to a creature (and after the health drained by the equipment), the companion joins it when all of these
hold: the companion is in the world, its duo counter is 0, its bond is at least `duo_bond`, the creature is still alive, and the creature
is within `duo_range_x100 / 100 + radius of the creature` of the companion. It hits that creature at once: the damage formula (spec 04)
with the attack of the companion (section "Bond"), `power_pct` = `duo_pct`, the creature's `def`, the levels of the player and of the
creature, `variance_pm` 1000, no critical hit, no element, and no random number is drawn; its counter goes to `duo_cooldown_ticks`. So a
strike that hits several creatures brings the duo hit on the first of them only. The hit comes before the status, the stagger (which counts
only the player's damage) and the death of the creature are handled: a creature it kills is the player's kill and adds no bond. In step 1 of
every tick, after it moves and before care, the counter goes down by one if it is above 0. The counter is not saved and goes back to 0 when
the companion that follows changes (section "The party").

The base pack gives every companion of a protagonist `duo_bond` 20, `duo_pct` 300, `duo_range_x100` 400 and `duo_cooldown_ticks` 600
(`tools/make_companions.py`), and the strays of the party the same with `duo_pct` 250 (`tools/make_party.py`): after twenty kills together,
a power strike near the companion brings its hit, three times its attack, every ten seconds. The clients show the duo hit as a number,
like the companion's own. Conformance: the scenario `companion_duo` (the first strike brings the duo hit, the second comes too soon, the
third finds it ready).

## Later

More commands (attack that one), a bond that changes more than its attack, companions found in the world (the gifts of Haruka and Gideon, spec 18, grow into these), more than one at a time, and
a companion that can be hurt.
