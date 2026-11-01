# 01. Numerics

Status: **v1**. Reference: `tools/reference/numerics.py`. Conformance suites: `rng`, `hash`, `noise`.

All algorithms below are integer-only. Python integers are unbounded and are masked explicitly; C++ and Kotlin rely on native unsigned/two's-complement 64-bit wrap-around (`uint64_t` in C++, `ULong` in Kotlin).

## Integer arithmetic

- `div_floor(a, b)`: floor division (rounds toward negative infinity), `b != 0`. C++ `/` truncates toward zero and must not be used for values that can be negative; Kotlin uses `Math.floorDiv`.
- `>>` on signed values is an **arithmetic** shift (floor). C++20 guarantees this.
- `clamp(v, lo, hi)`.
- Intermediate products use 64-bit signed integers. A formula must never overflow `int64`; specs bound their inputs.

## Fixed point Q16.16

A Q16.16 value is a 64-bit signed integer holding `value * 65536`. `ONE = 65536`.

- `mulq(a, b) = (a * b) >> 16`.
- Coordinates passed to noise are Q16.16 `int64` values and may be negative.

## SplitMix64

```
GOLDEN = 0x9E3779B97F4A7C15
mix64(z): z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9
          z = (z ^ (z >> 27)) * 0x94D049BB133111EB
          return z ^ (z >> 31)                       (all mod 2^64)
next():   state += GOLDEN ; return mix64(state)
```

Known answer: seed 0 gives `0xE220A8397B1DCDAF`, `0x6E789E6AA1B965F4`.

## FNV-1a 64

Offset `0xCBF29CE484222325`, prime `0x100000001B3`, over the UTF-8 bytes.

## Coordinate hash

```
hash64(seed, a, b = 0, c = 0):
    h = seed
    for v in (a, b, c):                 # v is a signed 64-bit integer, taken as its two's complement
        h = mix64(h + GOLDEN + v)       # mod 2^64
    return h
```

## PCG32 (XSH-RR)

State and increment are 64-bit. Multiplier `6364136223846793005`.

```
seed(init_state, init_seq):  state = 0 ; inc = (init_seq << 1) | 1
                             next_u32() ; state += init_state ; next_u32()
next_u32():  old = state ; state = old * MULT + inc
             xorshifted = ((old >> 18) ^ old) >> 27     (as uint32)
             rot = old >> 59
             return rotr32(xorshifted, rot)
next_bounded(bound):  threshold = (2^32 - bound) mod bound ; loop r = next_u32() until r >= threshold ; return r mod bound
```

Known answer: `seed(42, 54)` produces `0xA15C02B7, 0x7B47F409, 0xBA1D3330, 0x83D2F293, 0xBFA4784B, 0xCBED606E`.

### Named streams

`derive_stream(master_seed, name)`: `h = fnv1a64(utf8(name))`, then `PCG32(init_state = mix64(master_seed ^ h), init_seq = h)`.

Standard stream names: `world`, `combat`, `loot`, `quest`, `weather`, `cosmetic`, `ai`. Only `world`-derived data must be identical across platforms (see ADR 0005); other streams are still reproducible for tests.

## Value noise

```
lattice(seed, xi, yi)   = hash64(seed, xi, yi) >> 48                    # 0..65535
fade(t)                 = mulq(mulq(t, t), 3*ONE - 2*t)                 # smoothstep, t in 0..65535
lerp(a, b, t)           = a + mulq(b - a, t)
noise2(seed, x, y):     xi = x >> 16 ; yi = y >> 16 ; xf = x & 0xFFFF ; yf = y & 0xFFFF
                        u = fade(xf) ; v = fade(yf)
                        lerp(lerp(L(xi,yi), L(xi+1,yi), u), lerp(L(xi,yi+1), L(xi+1,yi+1), u), v)
fbm2(seed, x, y, octaves): amp = 32768 ; total = norm = 0
                        for o in 0..octaves-1:
                            n = noise2(hash64(seed, o), x * 2^o, y * 2^o)
                            total += mulq(n, amp) ; norm += amp ; amp >>= 1
                        return (total << 16) / norm   (floor)
```

Both functions return values in `0..65535`.

## What is forbidden

In world generation: `float`, `double`, `sin`, `cos`, `pow`, `exp`, `sqrt`, and any library RNG. Compile flags: MSVC `/fp:strict`, GCC/Clang `-ffp-contract=off`, never `-ffast-math`.
