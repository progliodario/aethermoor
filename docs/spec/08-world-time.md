# 08. World time, weather and respawn

Status: **v1.2 (M5c day, night and weather, then seasons and the routines of the people)**. Reference: `tools/reference/worldtime.py` and `ChunkWindow` in `tools/reference/worldgen.py`.
Conformance suites: `worldtime` and `chunk_window`. Parameters: the `time` object and `spawners.respawn_ticks` of
`data/base/worlds/overworld.json` (`schemas/world.schema.json`). All math is integer (spec 01). Seasons and routines are described below; the effect of
the weather on gameplay comes later and weather is presentation only.

## World time

`world_ticks` counts simulation ticks (60 per second) since the world was created. A new game starts at `time.start_tick`. It grows by one at the start of
every tick of the simulation (also during dialogues), before the window of chunks is updated and is stored in the save (`world_ticks`).

```
day_ticks = time.day_ticks                                  # 72000 = 20 minutes
day       = world_ticks / day_ticks + 1                     # integer division, the first day is 1
tod_pm    = (world_ticks % day_ticks) * 1000 / day_ticks    # time of day in permille, 0 = midnight, 500 = noon
```

Clients show the clock as hours and minutes: `hour = tod_pm * 24 / 1000`, `minute = (tod_pm * 1440 / 1000) % 60` (integer division).

## Seasons

`time.seasons` lists the seasons of the year in order, each with `id`, `days`, `tint` (`[r, g, b, a]`, the colour the clients lay over the screen: art direction), and optionally `weights` and `light`.
A year lasts the sum of the `days`, and then the seasons repeat. The **season of a day** is found by `d = (day - 1) mod year_days`, taking the first season whose cumulative days exceed `d`.
A world without `time.seasons` has no seasons (the season is empty, the light and weights below are the global ones).

## Light

`time.light` (or `light` of the season of the day, if it has one: summers have longer days and winters shorter ones) is a list of keyframes `[tod_pm, light_pm]` in increasing `tod_pm`, the first at 0 and the last at 1000 (`light_pm` 0 = black,
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
picked with `roll = (hash64(seed, p, 21) >> 20) % total_weight` over the cumulative weights, in list order. The weight of a kind is `weights[kind.id]` of the season of the day
that contains the first tick of the period (`p * period_ticks`) when that season lists it, else the `weight` of the kind.

During the first `time.weather.fade_ticks` of a period the weather fades from the previous period's kind (`max(p - 1, 0)`) to the current one:

```
t = world_ticks % period_ticks
if t >= fade_ticks: rain_pm = cur.rain_pm, dim_pm = cur.dim_pm
else: rain_pm = (prev.rain_pm * (fade_ticks - t) + cur.rain_pm * t) / fade_ticks     (same for dim_pm)
```

The effective light is `light_pm * (1000 - dim_pm) / 1000`. Clients darken the screen in proportion to `1000 - effective light` (night colors come from
the client's art direction, not from data yet) and draw rain with density `rain_pm`.

Conformance suite `worldtime`: for a list of `world_ticks` (also huge ones and the edges of the seasons) and seeds, `day`, `tod_pm`, `light_pm`, the kind id of the period, `rain_pm`, `dim_pm`,
the effective light and the season id.

## Routines

Settlement people (spec 09) follow a daily routine by **role**. `routines.roles` (world data) maps a role to keyframes `[from_pm, state]` in increasing `from_pm`, the first at 0; the
**state** at a time of day `tod_pm` is the one of the last keyframe with `from_pm <= tod_pm`. A role with no routine is always `work`. States:

- `work`: the person stands on its slot tile (spec 09);
- `plaza`: the person stands on its **gathering spot**, `plaza_x256 = x * 256 + 128`, `plaza_y256 = y * 256 + 160` of the tile `spots[index % count]` of the stamp (`index` is the slot index of the
  person and `spots` the `spots` of the stamp, tiles relative to it, placed with the settlement). A settlement without spots keeps its people at `work`;
- `away`: the person is indoors and does not exist: it cannot be talked to, drawn or collided with (a shopkeeper away means a closed shop).

An NPC exists iff its chunk is in the active window **and** its state is not `away` at the current time of day. There is no walking: at a change of state the person is where the new state says.
Clients re-evaluate the people when the permille of the day changes and when the window moves; the list of dynamic NPCs is always in the order chunks (row-major) then slots (scan order).
Conformance suite `routines`: who is present, with state and position, in the chunks of a few settlements at times across the day.

## Respawn

When an enemy is killed, its spawner is *cleared* and remembers the world tick of the death. A cleared spawner whose enemy has been dead for at least
`spawners.respawn_ticks` of world time is **ready**. Readiness is only evaluated when the chunk of the spawner **enters** the active window (spec 09,
"Streaming"): a ready spawner is removed from the cleared set and creates a new enemy like any other; a cleared spawner that is not ready creates none.
Nothing respawns in front of the player, and an enemy killed in a chunk that stays active stays dead until the player has gone away and come back.

`chunk_window` scripts have a `wait` step (advance the world time) and kills record the current time; see spec 09.

## Save

`world_ticks` (integer) at the top level of the save, and `cleared_spawners` entries `[x, y, died_tick]`. A save without `world_ticks` starts at
`time.start_tick`; an entry with two numbers has `died_tick` 0 (ready as soon as the world time allows).

## The colour of the hour

Presentation only, the same on both clients, with the colours of `grading` in `data/base/lights.json` (art direction; a pack
without it uses the defaults in brackets). With `n = (1000 - effective_light_pm) / 1000` (the night) and
`w = clamp(1 - |light_pm - 550| / 350, 0, 1)` (dawn and dusk: the sun is neither up nor down):

1. the world is **multiplied** by the colour between white and `night` [`#5766C7`] at `n`: the night is blue, not grey, and
   colours keep their hue;
2. then by the colour between white and `twilight` [`#FFCC9E`] at `0.75 * w`: the warm light of dawn and dusk;
3. the lights of the next section are **added** over it (they light what the night darkened);
4. `motes` [26] small lights drift over the world: dust in the sun by day (`mote_day`, faint), fireflies by night
   (`mote_night`, blinking), none while it rains;
5. the edges of the screen are darkened by up to `vignette_pm` [280] permille (a vignette), under the interface.

The tint of the season is laid over as before.

## Lights

`data/base/lights.json` (ID `base:lights/all`, schema `lights`) lists the props that shine at night: `art`, `radius_x100` (tiles), `color`, `strength_pm` and `flicker_pm`. When it is not full daylight, both clients draw
over the darkness a soft glow of that colour around every such prop in view, as bright as `strength_pm * (1000 - effective_light_pm) / 1000`, wavering by up to half of `flicker_pm`. The base pack lights the lamps, the campfires,
the Threshold Stones and the anvils. Presentation only: nothing of it is in the simulation or in the vectors.
