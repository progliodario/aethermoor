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

- `duration_ms` (1 to 4000): the length of the sound. `volume_pm` (0 to 1000): the master volume. IDs are `base:audio/sfx/<name>`.
- A layer has a `wave` (`sine`, `square`, `saw`, `triangle` or `noise`), a start and an end frequency in Hz (the pitch glides from
  one to the other), a volume in permille, an `attack_ms` (a linear fade in) and a `decay_ms` (a linear fade out that starts
  when the attack ends). `duty_pm` (square only, default 500) is the share of the cycle that is high.

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
5. The layer sample is `w * envelope * layer volume_pm / 1000`.

Clients compare with a tolerance: the conformance probes allow a difference of 2 in the 16 bit value, 1 percent in the loudness.

## Mixing

A client keeps a small number of voices (16 on the desktop, 10 on Android). Playing a sound starts a voice at sample 0; a voice
ends after its last sample; when all voices are busy the oldest one is cut. The voices are summed and clamped. Sounds are
rendered once at the first use and kept (they are short). A muted game plays nothing.

## What plays when

| Sound | When |
|---|---|
| `swing` | the player starts an attack |
| `hit` / `crit` | the player damages a creature (a critical hit) |
| `hurt` | a creature damages the player |
| `dodge` | the player starts a dodge roll |
| `level_up` | the level grows |
| `pickup` | something is added to the bag |
| `coin` | gold is added |
| `open` / `close` | a panel (bag, map, journal) opens or closes |
| `confirm` | a menu choice is confirmed (a dialogue line moves on) |

A pack can add sounds and a later version will let data choose the sound of an event; for now the table is in the clients.
