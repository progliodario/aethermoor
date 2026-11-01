"""Integer and fixed-point numerics (docs/spec/01-numerics.md).

Everything here uses integers only. Python integers are unbounded, so every 64-bit result is
masked explicitly; the C++ and Kotlin clients rely on native wrap-around instead.
"""
from __future__ import annotations

M32 = (1 << 32) - 1
M64 = (1 << 64) - 1
GOLDEN = 0x9E3779B97F4A7C15
ONE = 1 << 16  # 1.0 in Q16.16


def div_floor(a: int, b: int) -> int:
    """Floor division (rounds toward negative infinity). b must not be 0."""
    return a // b


def mulq(a: int, b: int) -> int:
    """Q16.16 multiplication, floor rounding (arithmetic shift)."""
    return (a * b) >> 16


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


# ---------------------------------------------------------------------------------------------
# SplitMix64, FNV-1a, coordinate hash
# ---------------------------------------------------------------------------------------------

def mix64(z: int) -> int:
    """SplitMix64 finalizer."""
    z &= M64
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & M64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & M64
    return z ^ (z >> 31)


class SplitMix64:
    def __init__(self, seed: int) -> None:
        self.state = seed & M64

    def next(self) -> int:
        self.state = (self.state + GOLDEN) & M64
        return mix64(self.state)


def fnv1a64(data: bytes) -> int:
    h = 0xCBF29CE484222325
    for byte in data:
        h ^= byte
        h = (h * 0x100000001B3) & M64
    return h


def hash64(seed: int, a: int, b: int = 0, c: int = 0) -> int:
    """Stateless hash of a seed and up to three signed 64-bit integers."""
    h = seed & M64
    for v in (a, b, c):
        h = mix64((h + GOLDEN + (v & M64)) & M64)
    return h


# ---------------------------------------------------------------------------------------------
# PCG32 (XSH-RR)
# ---------------------------------------------------------------------------------------------

class Pcg32:
    MULT = 6364136223846793005

    def __init__(self, init_state: int, init_seq: int) -> None:
        self.state = 0
        self.inc = ((init_seq << 1) | 1) & M64
        self.next_u32()
        self.state = (self.state + init_state) & M64
        self.next_u32()

    def next_u32(self) -> int:
        old = self.state
        self.state = (old * self.MULT + self.inc) & M64
        xorshifted = (((old >> 18) ^ old) >> 27) & M32
        rot = old >> 59
        return ((xorshifted >> rot) | (xorshifted << ((-rot) & 31))) & M32

    def next_bounded(self, bound: int) -> int:
        """Uniform value in [0, bound) by rejection sampling. bound must be in 1..2^32-1."""
        threshold = ((1 << 32) - bound) % bound
        while True:
            r = self.next_u32()
            if r >= threshold:
                return r % bound


def derive_stream(master_seed: int, name: str) -> Pcg32:
    """Named random stream derived from a master seed (spec 01, section RNG)."""
    h = fnv1a64(name.encode("utf-8"))
    return Pcg32(mix64((master_seed ^ h) & M64), h)


# ---------------------------------------------------------------------------------------------
# Value noise in Q16.16 (coordinates are Q16.16 integers, possibly negative, 64-bit)
# ---------------------------------------------------------------------------------------------

def lattice(seed: int, xi: int, yi: int) -> int:
    """Pseudo-random lattice value in 0..65535."""
    return hash64(seed, xi, yi) >> 48


def fade(t: int) -> int:
    """Smoothstep 3t^2 - 2t^3 in Q16.16 for t in 0..65535."""
    return mulq(mulq(t, t), 3 * ONE - 2 * t)


def lerp(a: int, b: int, t: int) -> int:
    return a + mulq(b - a, t)


def noise2(seed: int, x: int, y: int) -> int:
    """2D value noise, result in 0..65535."""
    xi, yi = x >> 16, y >> 16
    xf, yf = x & 0xFFFF, y & 0xFFFF
    u, v = fade(xf), fade(yf)
    a = lattice(seed, xi, yi)
    b = lattice(seed, xi + 1, yi)
    c = lattice(seed, xi, yi + 1)
    d = lattice(seed, xi + 1, yi + 1)
    return lerp(lerp(a, b, u), lerp(c, d, u), v)


def fbm2(seed: int, x: int, y: int, octaves: int) -> int:
    """Fractal noise: octaves doubling in frequency, halving in amplitude. Result in 0..65535."""
    total = 0
    norm = 0
    amp = ONE >> 1
    for octave in range(octaves):
        n = noise2(hash64(seed, octave), x * (1 << octave), y * (1 << octave))
        total += mulq(n, amp)
        norm += amp
        amp >>= 1
    return (total << 16) // norm
