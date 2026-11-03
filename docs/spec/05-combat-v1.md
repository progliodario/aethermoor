# 05. Combat v1

Status: **v1 (M3 slice)**. Reference: `tools/reference/combat.py`. Conformance suite: `combat` (scenarios).
Formulas are in `04-stats-and-combat.md`. Not in v1: mana skills, dodge, parry, status effects, stagger, projectiles,
companions, bosses.

## Data used

- **Skill** (`schemas/skill.schema.json`): `timing {startup, active, recovery}` in ticks, `cooldown_ticks`,
  `damage {kind, element, power_pct}` and `hitbox {shape: "arc", radius_x100, angle_deg}`.
- **Enemy** (`schemas/enemy.schema.json`): `level`, `stats {hp, atk, def, mdef, speed_x100}`, `xp`, `radius_x100`,
  `drops`, `behavior` and `art`.
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

1. `iframes` and `cooldown` decrease by 1 when positive.
2. Movement input is normalized (spec 02). When it is non-zero and the attack phase is `none` or `startup`, `facing`
   becomes the unit vector of the input. Movement runs with the speed multiplied by 0.5 while the attack phase is not `none`.
3. **Attack start**: if the attack input is held, the phase is `none` and `cooldown == 0`: phase `startup`,
   `phase_tick = 0`, `cooldown = cooldown_ticks`, the set of enemies already hit is cleared.
4. **Attack phases**, in the same tick:
   - `startup`: `phase_tick++`; when `phase_tick >= startup` the phase becomes `active` (tick 0).
   - `active`: first run the hit test, then `phase_tick++`; when `phase_tick >= active` the phase becomes `recovery`.
   - `recovery`: `phase_tick++`; when `phase_tick >= recovery` the phase becomes `none`.
5. Enemies update in list order.

## Hit test (active ticks)

For every living enemy not yet hit in this swing, in list order: `d` = distance between centers. It is hit when
`d <= radius_skill + radius_enemy` and, if `d > 0`, `dot(facing, (enemy - player) / d) >= cos(angle_deg / 2)`.
A hit applies the damage formula with the player's `atk`, the skill `power_pct`, the enemy `def`, element and
penetration neutral (1000 / 0), levels of both sides, the drawn variance and crit, `buff_mod = 1000`.

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

Damage numbers, enemy health bars, a squash animation for slimes and the HUD (HP, level, XP) are drawn by each client
from the simulation state and from the events it emits.
