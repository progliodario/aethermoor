# 08. World time, weather and respawn

Status: **v1 (M5c)**. Reference: `tools/reference/worldtime.py` and `ChunkWindow` in `tools/reference/worldgen.py`.
Conformance suites: `worldtime` and `chunk_window`. Parameters: the `time` object and `spawners.respawn_ticks` of
`data/base/worlds/overworld.json` (`schemas/world.schema.json`). All math is integer (spec 01). NPC schedules, seasons and the effect of
the weather on gameplay come later; v1 weather is presentation only.

## World time

`world_ticks` counts simulation ticks (60 per second) since the world was created. A new game starts at `time.start_tick`. It grows by one at the start of
every tick of the simulation (also during dialogues), before the window of chunks is updated and is stored in the save (`world_ticks`).

```
day_ticks = time.day_ticks                                  # 72000 = 20 minutes
day       = world_ticks / day_ticks + 1                     # integer division, the first day is 1
tod_pm    = (world_ticks % day_ticks) * 1000 / day_ticks    # time of day in permille, 0 = midnight, 500 = noon
```

Clients show the clock as hours and minutes: `hour = tod_pm * 24 / 1000`, `minute = (tod_pm * 1440 / 1000) % 60` (integer division).

## Light

`time.light` is a list of keyframes `[tod_pm, light_pm]` in increasing `tod_pm`, the first at 0 and the last at 1000 (`light_pm` 0 = black,
1000 = full daylight). The light at `tod_pm` interpolates linearly between the two keyframes `(p0, l0)` and `(p1, l1)` that contain it
(`p0 <= tod_pm <= p1`, the first such pair), rounding toward zero in the part that is added or subtracted, so that it is the same on every platform:

```
d = tod_pm - p0, span = p1 - p0
light_pm = l0 + (l1 - l0) * d / span          if l1 >= l0
light_pm = l0 - (l0 - l1) * d / span          otherwise
```

## Weather

Weather is a function of the world seed and the world time. Time is split in periods of `time.weather.period_ticks`; period `p = world_ticks / period_ticks`.
Each kind in `time.weather.kinds` has `weight`, `rain_pm` (0..1000) and `dim_pm` (0..1000, how much it darkens the day). The kind of period `p` is
picked with `roll = (hash64(seed, p, 21) >> 20) % total_weight` over the cumulative weights, in list order.

During the first `time.weather.fade_ticks` of a period the weather fades from the previous period's kind (`max(p - 1, 0)`) to the current one:

```
t = world_ticks % period_ticks
if t >= fade_ticks: rain_pm = cur.rain_pm, dim_pm = cur.dim_pm
else: rain_pm = (prev.rain_pm * (fade_ticks - t) + cur.rain_pm * t) / fade_ticks     (same for dim_pm)
```

The effective light is `light_pm * (1000 - dim_pm) / 1000`. Clients darken the screen in proportion to `1000 - effective light` (night colors come from
the client's art direction, not from data yet) and draw rain with density `rain_pm`.

Conformance suite `worldtime`: for a list of `world_ticks` (also huge ones) and seeds, `day`, `tod_pm`, `light_pm`, the kind id of the period, `rain_pm`, `dim_pm`
and the effective light.

## Respawn

When an enemy is killed, its spawner is *cleared* and remembers the world tick of the death. A cleared spawner whose enemy has been dead for at least
`spawners.respawn_ticks` of world time is **ready**. Readiness is only evaluated when the chunk of the spawner **enters** the active window (spec 09,
"Streaming"): a ready spawner is removed from the cleared set and creates a new enemy like any other; a cleared spawner that is not ready creates none.
Nothing respawns in front of the player, and an enemy killed in a chunk that stays active stays dead until the player has gone away and come back.

`chunk_window` scripts have a `wait` step (advance the world time) and kills record the current time; see spec 09.

## Save

`world_ticks` (integer) at the top level of the save, and `cleared_spawners` entries `[x, y, died_tick]`. A save without `world_ticks` starts at
`time.start_tick`; an entry with two numbers has `died_tick` 0 (ready as soon as the world time allows).
