# 10. Companions

Status: **v1.1 (a follower that fights, the stay command and a bond that grows with its kills; several companions at once come later)**. Reference: `CombatSim._update_companion` in `tools/reference/combat.py`.
Schema: `schemas/companion.schema.json`. Conformance: the scenarios `companion_fights`, `companion_follows`, `companion_stays` and `companion_bond` (the checkpoints carry `companion`: position, `stay`, `bond`) of the suite `combat`.

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

## Commands

The command `companion_stay` (desktop: `H`; Android: the `Stay` / `Follow` button) switches the companion between **following** and **staying**. While it stays, step 1 does not move it; it still hits what comes in its range.
When the player is more than 8 tiles away the companion is put on the player's position as in step 1 and follows again. The command does nothing without a companion.

## Bond

Every creature killed by a hit of the companion adds one to its **bond**, before the kill is handled. Its attack is `atk_base + atk_per_level * (player level - 1) + min(bond / 5, 10)`: one more point every five kills,
ten at most. The bond and the stay command are saved with the companion (`stay`, `bond` in `companion` of the save document, spec 12; absent when false and 0).

## Later

More commands (attack that one), a bond that changes more than its attack, companions found in the world (the gifts of Haruka and Gideon, spec 18, grow into these), more than one at a time, and
a companion that can be hurt.
