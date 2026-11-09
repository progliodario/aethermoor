# 05. Combat v1

Status: **v1.2 (M3 slice: attack, dodge roll, mana and the power strike)**. Reference: `tools/reference/combat.py`. Conformance suite: `combat` (scenarios).
Formulas are in `04-stats-and-combat.md`. The **dodge roll** (below) is in v1.1, **mana and a second attack skill** in v1.2. Not yet: parry, status effects, stagger, projectiles,
companions, mana for items and equipment.

## Data used

- **Skill** (`schemas/skill.schema.json`): `timing {startup, active, recovery}` in ticks, `cooldown_ticks`,
  `damage {kind, element, power_pct}` and `hitbox {shape: "arc", radius_x100, angle_deg}`.
- **Damage kind**: `damage.kind` of an attack skill is `physical` (the default) or `magical`. A magical skill hits with `matk` (spec 04) instead of `atk`; the target's defense is `def` in both cases
  (the `mdef` of creatures is not read yet). In scenarios, the skill objects take `"kind": "magical"`.
- **Second attack skill**: the second skill of `starting_skills` that has a `hitbox` is the **power strike**, with the same fields as the first (`timing`, `cooldown_ticks`, `damage.power_pct`, `hitbox`) and a `cost.mp`. In scenarios it is the object
  `strike {startup, active, recovery, cooldown, power_pct, radius_x100, angle_deg, mp}`; without it the game has no power strike.
- **Dodge skill** (a skill of `type: "movement"` with a `movement` block): `timing.active` is the length of the roll in ticks, `cooldown_ticks`, and
  `movement {speed_mult_x100, iframes}`. A protagonist whose `starting_skills` hold none cannot dodge. In scenarios it is the object `dodge {ticks, speed_mult_x100, iframes, cooldown}`.
- **Enemy** (`schemas/enemy.schema.json`): `level`, `stats {hp, atk, def, mdef, speed_x100}`, `xp`, `radius_x100`,
  `drops`, `behavior` and `art`, and for the elements `element` (default `none`) and `weaknesses_pm` (see "Elements").
- **Behavior** (`schemas/behavior.schema.json`): v1 has one kind, `melee_chaser` (the base pack has six sets of numbers for it: `melee_chaser_basic`, the shy `skittish`, the far-seeing `stalker`, the heavy `brute`, the long-reaching `lunger` and the post-bound `guardian`), with `aggro_x100`, `leash_x100`,
  `attack_range_x100`, `hit_range_x100`, `windup_ticks`, `recovery_ticks`. More kinds (and the full declarative state
  graph) come later; a kind is a closed behavior implemented by the engine and tuned by data.
- **Map**: objects of `type: "enemy_spawner"` with property `enemy` (enemy ID) at the enemy's feet. One enemy per
  spawner, no respawn in v1.
- **Player**: base stats, `growth_pm` and the weapon of the first `starting_items` entry of kind `weapon`
  (`weapon.atk`, `weapon.matk`). Level `L` primary stats are `base + growth_pm * (L - 1) / 1000` (floor).

## Random streams

`combat` and `loot` are derived from the world seed (`derive_stream`, spec 01). Draw order is part of the contract:

- player hit on an enemy: `variance = 950 + combat.next_bounded(101)`, then `crit = combat.next_bounded(1000) < crit_chance_pm`;
- enemy hit on the player: `variance = 950 + combat.next_bounded(101)`; enemies never crit;
- kill: for each drop in data order, `loot.next_bounded(1000) < weight_pm`; on success, if `qty_max > qty_min`
  the quantity is `qty_min + loot.next_bounded(qty_max - qty_min + 1)`, else `qty_min`.

## Player state per tick (in this order)

1. `iframes`, `cooldown` and `dodge_cooldown` decrease by 1 when positive.
1a. **Mana**: `mp_u = min(max_mp * 6000, mp_u + mp_regen_x100)` (see "Mana").
1b. **Dodge start** (see "Dodge roll"). While a dodge is in progress, steps 2 and 3 are replaced by the roll movement and the attack phase stays `none`.
2. Movement input is normalized (spec 02). When it is non-zero and the attack phase is `none` or `startup`, `facing`
   becomes the unit vector of the input. Movement runs with the speed multiplied by 0.5 while the attack phase is not `none`.
3. **Attack start**: first, if the strike input is held, the game has a power strike, the phase is `none`, `cooldown == 0` and `mp_u >= mp * 6000`: `mp_u -= mp * 6000`,
   the current skill becomes the strike, phase `startup`, `phase_tick = 0`, `cooldown = cooldown` of the strike, the set of enemies already hit is cleared. Otherwise, if the attack input is held, the phase is `none` and `cooldown == 0`:
   the current skill becomes the basic attack, phase `startup`, `phase_tick = 0`, `cooldown = cooldown_ticks`, the set is cleared (a strike that is refused falls through to the attack of the same tick).
4. **Attack phases**, in the same tick (with the timing, radius, angle and power of the current skill):
   - `startup`: `phase_tick++`; when `phase_tick >= startup` the phase becomes `active` (tick 0).
   - `active`: first run the hit test, then `phase_tick++`; when `phase_tick >= active` the phase becomes `recovery`.
   - `recovery`: `phase_tick++`; when `phase_tick >= recovery` the phase becomes `none`.
5. Enemies update in list order.

## Mana

`mp_u` is the mana in units of 1/6000 of a point (so that the regeneration is exact in integers at 60 ticks per second): `mp_regen_x100` units are added every tick, which is `mp_regen_x100 / 100` points per second.
It is capped at `max_mp * 6000` (spec 04) and starts full in a new game; the points shown are `mp_u / 6000` (floor). Equipment or a level-up that change `max_mp` do not refill it; a death, a Threshold Stone and a bed at an inn (the dialogue effect `heal_full`) fill it. Using an item never costs mana
(no item has a mana cost yet). **Not saved** (spec 12): a loaded game starts with full mana, and a swing in progress when it is saved continues as a basic attack.

The **power strike** (`base:skill/ren/power_strike`): the same arc as the slash but wider and longer, power 230 percent, a startup of 10, an active window of 4 and a recovery of 16 ticks, a cooldown of 90 ticks (shared with the
attack: both wait for the same `cooldown`) and a cost of 10 mana. With the starting stats Ren has 100 mana and regenerates about 0.85 per second, so a strike is possible about ten times in a row and then once every twelve seconds.

## Dodge roll

The dodge is a short roll in a direction, with invulnerability. State per player: `dodge_ticks` (ticks of the roll left), `dodge_cooldown` and `dodge_dir` (a unit vector). None of them is saved
(spec 12): loading a game, or a death, ends a roll and clears the cooldown.

- **Start**, in step 1b of the tick, when the `dodge` input is held, the player can dodge (the game has a dodge skill, no dialogue is open), `dodge_ticks == 0`, `dodge_cooldown == 0` and the attack phase is `none`:
  `dodge_dir` is the normalized movement input when it is non-zero, else `facing`; `facing` becomes `dodge_dir` (and `facing_left` follows its horizontal sign);
  `dodge_ticks = ticks` (`timing.active`), `dodge_cooldown = cooldown`, `iframes = max(iframes, iframes_of_the_dodge)`. The dodge wins over an attack input of the same tick.
- **While `dodge_ticks > 0`** (including the start tick): movement and attack inputs are ignored; the player moves along `dodge_dir` with speed `move_speed * speed_mult_x100 / 100` (the usual step and
  collision of spec 02); `dodge_ticks--`; the player counts as moving for the clip (`walk`). The attack phase does not advance (it is `none`). Enemies update as always: their hit needs `iframes == 0` (see "Hurting the player"), so the
  roll avoids a blow that lands while `iframes` lasts. `iframes` counts down as usual.
- **Base pack**: `base:skill/common/dodge`: a roll of 12 ticks (0.2 s) at 2.6 times the speed (about two tiles), 14 ticks of invulnerability, a cooldown of 40 ticks (counted from the start, so a new roll is possible 0.67 s later).
- Not in v1.1: stamina or mana cost, rolling out of an attack recovery, a perfect-dodge bonus. The conformance scenarios are `dodge_roll`, `dodge_cooldown` and `dodge_iframes`.

## Hit test (active ticks)

For every living enemy not yet hit in this swing, in list order: `d` = distance between centers. It is hit when
`d <= radius_skill + radius_enemy` and, if `d > 0`, `dot(facing, (enemy - player) / d) >= cos(angle_deg / 2)`.
A hit applies the damage formula with the player's `atk`, the skill `power_pct`, the enemy `def`, the element
multiplier of the hit ("Elements" below), penetration neutral (0), levels of both sides, the drawn variance and crit,
`buff_mod = 1000`.

## Elements

A hit has an **element**: the one of the equipped weapon (`weapon.element` of the item, default `none`; the weapon
the protagonist starts with counts when nothing else is equipped, and has none). The skills have no element yet.
The element multiplier `elem_mult_pm` of the damage formula (spec 04) is, for an enemy:

1. the value of `weaknesses_pm` for the element of the hit, when the enemy lists it (`1500` is a weakness, `500` a
   resistance, `0` immunity); else
2. `500` when the element of the hit is the enemy's own `element` and is not `none`; else
3. `1000`.

A hit of element `none` is always `1000`. The numbers of the floating texts do not change; a client may mark a hit with a
multiplier above 1000 (the desktop and Android clients add an exclamation mark).

## Status effects

A hit with a weapon that has an element (see "Elements") may leave a **status effect** on the creature that it did not kill, unless the creature is
immune to that element (the multiplier of the hit is 0). After the damage is applied, one roll `next_bounded(1000)` of the `combat` stream is drawn;
the status is applied when it is below the chance of the element. The effects last a number of ticks, are not saved, and a new one of the same kind
restarts the count:

| Element | Status | Chance (permille) | Ticks | What it does |
|---|---|---|---|---|
| fire | burn | 350 | 150 | every 30 ticks, `max(1, hp * 3 / 100)` damage (its maximum health), whatever the defense; it can kill |
| water | chill | 400 | 180 | the creature moves at half speed |
| wind | stun | 300 | 45 | the creature does nothing |
| earth | stun | 300 | 75 | the creature does nothing |
| light, dark | weaken | 350 | 240 | its attacks do 75 percent of their `atk` |

At the start of an enemy's update: a burn counts down one tick and, on every 30th tick since it began, hurts (a kill follows the rules of "Kill");
then a stunned creature counts down one tick and does nothing else; otherwise the creature acts as in "Enemy states"; at the end its chill and weaken
count down. The parry and the status effects of the player's attacks on the player come later.

## Kill

HP below 1 means dead (state `dead`, HP 0). Then, in order: loot, then
`xp += xp_gain(enemy.xp, enemy.level, player.level)`, then while the level is below 99, the table has an entry for the
level and `xp >= table[level - 1]`: `xp -= table[level - 1]`, `level++`, derived stats are recomputed and HP is restored
to the new maximum.

## Enemy states

Computed with `dist` = distance to the player at the start of the enemy's update.

| State | Behavior |
|---|---|
| `idle` | `dist <= aggro` becomes `chase` |
| `chase` | `dist > leash` becomes `return`; `dist <= attack_range` becomes `attack` (`t = 0`); else move toward the player |
| `attack` | `t++`; when `t == windup` and `dist <= hit_range` and the player's `iframes == 0`: hurt the player; when `t >= windup + recovery` back to `chase` |
| `return` | if the distance to the home position is `<= 0.1`: `idle` and full HP; else move toward home |
| `dead` | nothing |

Moving: `step = speed * dt`; if the target is closer than `step` the enemy lands on it, otherwise it advances `step` along the
direction; then it is pushed out of walls and props using its own radius (spec 02, `resolve`).

## Hurting the player

Damage formula with the enemy `atk`, power 100, the player's `def`, levels, drawn variance, no crit. Then `hp -= damage`
and `iframes = 45`. If `hp <= 0`: `deaths++`, `hp = max_hp`, position = spawn, attack phase `none`, `iframes = 90`.

## Presentation (not in the contract)

Two small squares next to the bars show the abilities: they fill while the cooldown of the dodge (`dodge_cooldown`) or of the power strike (`cooldown`, shared with the attack) runs and light up when the ability can be used (the strike also needs its mana).

Damage numbers, enemy health bars, a squash animation for slimes and the HUD (HP, level, XP) are drawn by each client
from the simulation state and from the events it emits.
