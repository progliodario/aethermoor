# 03. Systems order and game loop

Status: **v1 (M2 subset)**.

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

M2 implements 1, 3, 11 and 12; the others are reserved for later milestones.

1. Input to intentions
2. AI to intentions
3. Movement and collisions
4. Skills (cooldowns, costs, hitboxes)
5. Hit detection
6. Damage, healing, status effects
7. Death, loot, XP
8. Triggers, dialogue, quests
9. World time, weather, NPC schedules
10. Spawn/despawn, chunk streaming
11. Animation (advance clip time; choose `idle` or `walk` from speed, mirror from the last horizontal direction)
12. Camera
13. Presentation (render, UI, audio)

Animation rule (M2): the player uses `walk` while the normalized input is non-zero, else `idle`. The clip time of the
new clip restarts when the clip changes. The character is mirrored when the last non-zero horizontal input was negative.
