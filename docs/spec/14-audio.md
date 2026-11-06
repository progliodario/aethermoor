# 14. Audio (sound effects)

Sounds are not recorded: they are **synthesized** from small recipes in the pack, the same way the art is drawn from recipes. Both
clients run the same algorithm, so a sound is the same everywhere. This first version covers sound effects; music, ambience and
the mixer settings come later (plan `docs/plan/04-grafica-audio-ui-input.md`, section 2).

Audio is presentation only: nothing in the simulation depends on it, so it has no effect on saves or on the vectors of the
rules. The synthesizer is headless (no device code) and is tested with the conformance suite `audio`.

## Recipe format (`schemas/sfx_recipe.schema.json`)

```json
{ "id": "base:audio/sfx/hit", "duration_ms": 150, "volume_pm": 800,
  "layers": [ {"wave": "noise", "freq_start": 3000, "freq_end": 400, "volume_pm": 700, "attack_ms": 1, "decay_ms": 120},
              {"wave": "square", "freq_start": 220, "freq_end": 70, "volume_pm": 500, "duty_pm": 500, "attack_ms": 0, "decay_ms": 100} ] }
```

- `duration_ms` (1 to 12000): the length of the sound. `volume_pm` (0 to 1000): the master volume. IDs are `base:audio/sfx/<name>`.
- `loop` (optional, default false): the sound is meant to repeat for ever (ambience). A loop has no envelope: the attack and the
  decay are ignored. The length is its period, so a layer's `am_dhz` should fit a whole number of times in it to avoid a click.
- A layer has a `wave` (`sine`, `square`, `saw`, `triangle` or `noise`), a start and an end frequency in Hz (the pitch glides from
  one to the other), a volume in permille, an `attack_ms` (a linear fade in) and a `decay_ms` (a linear fade out that starts
  when the attack ends). `duty_pm` (square only, default 500) is the share of the cycle that is high. `am_dhz` (in tenths of a hertz) and
  `am_depth_pm` give the layer a slow swell, an amplitude modulation: gusts of wind, waves, the pulse of crickets.

## Synthesis (normative)

Fixed output: **22050 Hz**, mono, signed 16 bit. All arithmetic is in IEEE double precision.

For a sound of `n = duration_ms * 22050 / 1000` samples (integer division), the sample `i` (0 to n - 1) is the sum over the
layers of the layer sample, times `volume_pm / 1000`, clamped to [-1, 1], then `floor(x * 32767 + 0.5)`.

For one layer, with `t = i / n` and `ms = i * 1000 / 22050`:

1. The frequency is `f = freq_start` when the two frequencies are equal, else `freq_start * exp(t * ln(freq_end / freq_start))`.
2. The wave value `w` is taken from the phase `p` (in [0, 1), starting at 0) *before* the phase advances:
   `sine`: `sin(2 pi p)`; `square`: `1` when `p * 1000 < duty_pm`, else `-1`; `saw`: `2 p - 1`; `triangle`: `4 |p - 0.5| - 1`;
   `noise`: a held value that is renewed whenever the phase has wrapped since the previous sample (and at the first sample): the
   state `s` of a 32 bit xorshift (initial value 2463534242; `s ^= s << 13; s ^= s >> 17; s ^= s << 5`, all modulo 2^32) steps once and
   the value is `s` read as a signed 32 bit integer divided by 2^31. So the frequency of a noise layer is how fast it changes.
3. The phase advances: `p += f / 22050`; when `p >= 1`, one is subtracted and the wrap is remembered for the next sample.
4. The envelope is `ms / attack_ms` while `ms < attack_ms`, else `max(0, 1 - (ms - attack_ms) / decay_ms)` (`decay_ms` is at least 1).
5. The modulation is `1 - depth * (0.5 - 0.5 cos(2 pi * (am_dhz / 10) * (i / 22050)))` (so it starts at 1) when `am_depth_pm` is above 0, else `1`.
6. The layer sample is `w * envelope * layer volume_pm / 1000 * modulation`. In a looping recipe the envelope is `1`.

Clients compare with a tolerance: the conformance probes allow a difference of 2 in the 16 bit value, 1 percent in the loudness.

## Mixing

A client keeps a small number of voices (16 on the desktop, 10 on Android). Playing a sound starts a voice at sample 0 at a
gain; a voice ends after its last sample; when all voices are busy the oldest one is cut. The voices and the loops are summed
and clamped. Every sound the pack mentions is rendered once, when the game starts, and kept. A muted game plays nothing.

**Loops** (the ambience) play for ever from a voice of their own with a gain that moves toward its target at a rate of one
over a second and a half, so they fade in and out.

## Events and the table of sounds

The game never names a sound directly: it names an **event** (`swing`, `step.grass`, `enemy.wolf.hit`, `ui.open.bag`...) and the
pack says what to play, in `data/base/audio/events.json` (schema `audio_events`):

- `events`: each event has `sounds` (short names of sound effects, played **in turn**: the first time the first, the second time
  the second...), `volume_pm`, and an optional `cooldown` in frames during which the same event does not play again.
- `ambience`: which loops play where (see below).

A client plays an event at `event volume_pm * volume of the call / 1000` permille. Unknown events are ignored. Adding a sound
to the game is data only, unless a new situation has to be noticed.

## The director (normative)

The **director** looks at the game once per frame and says which events happened. It has no randomness, so it is the same in
both clients and is tested with the conformance suite `audio_director`. Its input is a **snapshot**:

| Field | Meaning |
|---|---|
| `frame` | frame counter |
| `player` | `hp`, `max_hp`, `level`, `phase` (0 when no attack is going on), `strike` (the attack is the power strike), `dodge` (a roll is going on), `moving`, `x`, `y` (tiles), `surface` (the sound of the tile under the feet: `grass`, `dirt`, `sand`, `snow`, `stone`, `wood`, `water`, `moss`, `ash`), `save_cd` (ticks until the death save is ready again) |
| `cues` | what the creatures did this frame, from the simulation: `kind` (`hit` the player hurt it, `hurt` it hurt the player, `die`, `aggro` it noticed the player, `attack` it began an attack), `family` (its `sound` in the enemy data), `x`, `y`, and for `hit` the flags `crit` and `weak` |
| `items`, `gold`, `mp`, `weapon`, `armor` | how many things are in the bag, the gold, the mana, the equipped items |
| `panels` | `bag`, `map`, `journal`, `shop`, `board`, `travel`: which are open |
| `dialogue`, `line`, `cursor` | a dialogue is open; a counter that grows with every line spoken; the sum of the cursors of the menus |
| `quests_started`, `quests_done`, `stones` | counts of quests known and done, and of Threshold Stones woken |
| `region`, `tod_pm`, `rain_pm` | the ID of the region (empty without a streamed world), the time of day (0 midnight, 500 noon), the rain (0 to 1000) |

The output is a list of events with a volume in permille. For each frame, in this order:

1. **Cues**: for each, with `d` the distance to the player in tiles, the volume is `clamp(1000 - floor(d * 70 + 0.5), 0, 1000)`.
   `hurt` gives `player.hurt` (always full). Any other kind gives `enemy.<family>.<kind>` at that volume, unless it is below 60.
   A `hit` also gives `crit` and `weak` when flagged.
2. From the second frame on, comparing with the previous snapshot: `power` or `swing` when `phase` leaves 0; `dodge` when the roll
   starts; `level_up`; `player.death` when `hp` falls to 0; `death_save` when `save_cd` grows; `step.<surface>` (volume 700) for each
   0.85 tiles walked while `moving` (the walked distance resets when not moving); `heartbeat` (800) every 70 frames while `hp * 4 < max_hp` and
   alive (the first at once).
3. The bag, by the change of `items` and `gold` (the first that fits): gold up and items down with the shop open `shop.sell`; gold down and
   items up `shop.buy`; gold up `coin`; items up `pickup`; items down and `hp` up `use.heal`; items down and `mp` up `use.mana`; items down
   with no shop open `use.other`. A change of `weapon` gives `equip.weapon`, of `armor` `equip.armor`.
4. Panels: `ui.open.<panel>` and `ui.close.<panel>` when one changes (in the order bag, map, journal, shop, board, travel);
   `dialogue.open` and `dialogue.close`, or `dialogue.next` when `line` changes with the dialogue open; `ui.move` when `cursor` changes
   while a dialogue or a panel is open.
5. The story and the world: `quest.accept`, `quest.complete`, `stone.wake` when the counts grow; `region.enter` when `region` changes;
   `rain.start` and `rain.stop` when the rain begins or ends; `thunder` when `rain_pm >= 700` and `frame % 1200 == 600`; `dawn` when the time of
   day crosses 250 upward, `nightfall` when it crosses 750.

## Ambience (normative)

The `ambience` section of the table says, for each region, which loops belong to it, with a gain in permille and a moment (`always`,
`day` or `night`; it is day from 250 to 750). The gains for a place and a moment are, in this order: the entries of the region that fit the moment
(the largest gain when a loop is listed twice); then, when `rain_pm > 0`, the light rain loop at `min(1000, rain_pm)` and the heavy
rain loop at `min(1000, max(0, rain_pm - 500) * 2)` when above zero, and the loops in `rain.silences` (the birds, the crickets) go to 0.
Loops at 0 are left out. The client sets these as the targets of its loops every frame.
