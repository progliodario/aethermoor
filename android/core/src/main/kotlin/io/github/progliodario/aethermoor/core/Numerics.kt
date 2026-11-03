package io.github.progliodario.aethermoor.core

// Integer and fixed-point numerics. Spec: docs/spec/01-numerics.md
// Reference: tools/reference/numerics.py. No floating point anywhere in this file.

/** 1.0 in Q16.16. */
const val ONE: Long = 1L shl 16

/** SplitMix64 / hash increment. */
val GOLDEN: ULong = 0x9E3779B97F4A7C15uL

/** Floor division (rounds toward negative infinity). */
fun divFloor(a: Long, b: Long): Long = Math.floorDiv(a, b)

fun clampLong(value: Long, low: Long, high: Long): Long =
    if (value < low) low else if (value > high) high else value

/** Q16.16 multiplication with floor rounding (arithmetic shift). */
fun mulq(a: Long, b: Long): Long = (a * b) shr 16

fun mix64(input: ULong): ULong {
    var z = input
    z = (z xor (z shr 30)) * 0xBF58476D1CE4E5B9uL
    z = (z xor (z shr 27)) * 0x94D049BB133111EBuL
    return z xor (z shr 31)
}

class SplitMix64(seed: ULong) {
    private var state: ULong = seed

    fun next(): ULong {
        state += GOLDEN
        return mix64(state)
    }
}

fun fnv1a64(text: String): ULong {
    var h = 0xCBF29CE484222325uL
    for (byte in text.toByteArray(Charsets.UTF_8)) {
        h = h xor (byte.toInt() and 0xFF).toULong()
        h *= 0x100000001B3uL
    }
    return h
}

/** Stateless hash of a seed and up to three signed 64-bit integers. */
fun hash64(seed: ULong, a: Long, b: Long = 0, c: Long = 0): ULong {
    var h = seed
    for (v in longArrayOf(a, b, c)) {
        h = mix64(h + GOLDEN + v.toULong())
    }
    return h
}

/** PCG32 (XSH-RR). Values are returned as non-negative [Long]s in 0..2^32-1. */
class Pcg32(initState: ULong, initSeq: ULong) {
    /** State and increment, for saves: the generator continues exactly where it stopped. */
    var state: ULong = 0uL
        private set
    var inc: ULong = (initSeq shl 1) or 1uL
        private set

    fun setState(newState: ULong, newInc: ULong) {
        state = newState
        inc = newInc
    }

    init {
        nextU32()
        state += initState
        nextU32()
    }

    fun nextU32(): Long {
        val old = state
        state = old * 6364136223846793005uL + inc
        val xorshifted = (((old shr 18) xor old) shr 27).toUInt()
        val rot = (old shr 59).toInt()
        val result = (xorshifted shr rot) or (xorshifted shl ((32 - rot) and 31))
        return result.toLong()
    }

    /** Uniform value in [0, bound) by rejection sampling; bound in 1..2^32-1. */
    fun nextBounded(bound: Long): Long {
        val threshold = (0x1_0000_0000L - bound) % bound
        while (true) {
            val r = nextU32()
            if (r >= threshold) return r % bound
        }
    }
}

/** Named random stream derived from a master seed ("world", "combat", "loot", ...). */
fun deriveStream(masterSeed: ULong, name: String): Pcg32 {
    val h = fnv1a64(name)
    return Pcg32(mix64(masterSeed xor h), h)
}

// Value noise in Q16.16. Coordinates are Q16.16 integers (may be negative). Results: 0..65535.

fun lattice(seed: ULong, xi: Long, yi: Long): Long = (hash64(seed, xi, yi) shr 48).toLong()

fun fade(t: Long): Long = mulq(mulq(t, t), 3 * ONE - 2 * t)

fun lerpQ(a: Long, b: Long, t: Long): Long = a + mulq(b - a, t)

fun noise2(seed: ULong, x: Long, y: Long): Long {
    val xi = x shr 16
    val yi = y shr 16
    val xf = x and 0xFFFFL
    val yf = y and 0xFFFFL
    val u = fade(xf)
    val v = fade(yf)
    val a = lattice(seed, xi, yi)
    val b = lattice(seed, xi + 1, yi)
    val c = lattice(seed, xi, yi + 1)
    val d = lattice(seed, xi + 1, yi + 1)
    return lerpQ(lerpQ(a, b, u), lerpQ(c, d, u), v)
}

fun fbm2(seed: ULong, x: Long, y: Long, octaves: Int): Long {
    var total = 0L
    var norm = 0L
    var amp = ONE shr 1
    for (octave in 0 until octaves) {
        val scale = 1L shl octave
        val n = noise2(hash64(seed, octave.toLong()), x * scale, y * scale)
        total += mulq(n, amp)
        norm += amp
        amp = amp shr 1
    }
    return divFloor(total shl 16, norm)
}
