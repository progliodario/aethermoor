# 03. Systems order and game loop

Status: **v1**. The order below is the one of `WorldSim::tick` in C++ and `WorldSim.tick` in Kotlin.

## Fixed time step

The simulation runs at **60 ticks per second**. The frame loop accumulates real time and runs whole ticks:

```
accumulator += min(frame_time, 0.25 s)
while accumulator >= 1/60 and ticks_this_frame < 5: step() ; accumulator -= 1/60
render(alpha = accumulator * 60)
```

If more than five ticks are owed the extra time is dropped (no spiral of death). Rendering may interpolate the
player position with `alpha`.

## Order of work inside a tick

The planned phases are below; the column says what the game does with each one today.

| # | Phase | Status |
|---|---|---|
| 1 | Input to intentions | the movement vector and `attack` of the tick (spec 16); both are zero while a dialogue is open |
| 2 | AI to intentions | each living enemy runs its behavior (spec 05), after the player's attack, at step 6 below |
| 3 | Movement and collisions | the player (spec 02), at half speed during an attack |
| 4 | Skills (cooldowns, costs, hitboxes) | one skill, the sword swing: cooldown, startup, active and recovery frames (spec 05); no costs yet |
| 5 | Hit detection | during the active frames of the swing, enemies in list order (spec 05) |
| 6 | Damage, healing, status effects | damage (spec 04, 05) and healing from items and inns; no status effects yet |
| 7 | Death, loot, XP | loot, XP, level-ups, the quest objectives of the kill (spec 05, 07) |
| 8 | Triggers, dialogue, quests | the story engine is driven by the clients' events (interact, choose), not by the tick |
| 9 | World time, weather, NPC schedules | `world_ticks` grows first thing in every tick, also during dialogues; people are placed again when the time of day changes (spec 08) |
| 10 | Spawn/despawn, chunk streaming | the window of 5 x 5 chunks is updated at the start of the tick, before anything else (spec 09) |
| 11 | Animation | advance the clip time; `idle` or `walk` from the movement; mirror from the last horizontal direction |
| 12 | Camera | follows the player, clamped to the map (for a streamed world, the whole world) |
| 13 | Presentation | render, HUD, panels, sound effects (spec 14; music and ambience are off) |

In the code (`CombatSim.tick` of the reference, `WorldSim::tick` and `WorldSim.tick` of the clients) a tick runs, in this order:

1. chunk streaming and the explored cells (10, spec 09); the clock of the world (9); the travellers (spec 07, "Travellers walk"); the
   quests that collect, the bag counted again (spec 07, "Quests");
2. the dialogue freeze (1): nothing more happens while a dialogue is open;
3. the counters of the player: invulnerability, cooldowns, roll and parry, the death save, the abilities; mana; the status effects on
   the player (spec 05);
4. the parry, the roll or the movement of the player (3), the start of an attack (4), and the animation (11);
5. the attack in progress: hit detection, damage, kills, loot and experience (5, 6, 7);
6. the companion, then the tamed friend (spec 10);
7. every enemy in the order of the list: its statuses and its behavior (2, 6), the march of the creatures of a defense (spec 18);
8. the defense of Gideon's Dungeon (spec 18): its traps, its core, its waves;
9. the lightning of a storm (spec 08, "Lightning");
10. the status effects of the player that wear off, and the regeneration of a dish (spec 06).

The camera and the presentation (12, 13) belong to the client and run once per frame after the ticks.

Animation rule (M2): the player uses `walk` while the normalized input is non-zero, else `idle`. The clip time of the
new clip restarts when the clip changes. The character is mirrored when the last non-zero horizontal input was negative.
