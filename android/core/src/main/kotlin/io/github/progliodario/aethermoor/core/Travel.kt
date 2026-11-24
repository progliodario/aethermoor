package io.github.progliodario.aethermoor.core

import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.long
import kotlin.math.floor
import kotlin.math.min
import kotlin.math.sqrt

// Travellers walk (spec 07, "Travellers walk"): where a traveller is at a tick of the day. Integer arithmetic in 1/256 of a tile;
// the same in tools/reference/story.py (traveller_position) and in desktop/src/core/travel.hpp.

/**
 * How a traveller walks between its stops: it arrives by [arrivePm] of the day, leaves at [departPm], and walks [speedX256] / 256 of a
 * tile per tick. A speed of 0: it stands at its stop all day.
 */
data class TravellerWalk(val arrivePm: Int = 0, val departPm: Int = 1000, val speedX256: Long = 0L)

/** Reads the `walk` of a traveller (spec 07, "Travellers walk"); null: it does not walk. */
fun parseTravellerWalk(walk: JsonObject?): TravellerWalk {
    if (walk == null) return TravellerWalk()
    fun value(key: String) = walk.getValue(key).jsonPrimitive.long
    return TravellerWalk(value("arrive_pm").toInt(), value("depart_pm").toInt(), value("speed_x256"))
}

/** The integer square root of [v], rounded down (0 for v <= 0); the correction makes it exact on every platform. */
fun isqrt64(v: Long): Long {
    if (v <= 0L) return 0L
    var r = sqrt(v.toDouble()).toLong()
    while (r > 0L && r * r > v) r--
    while ((r + 1) * (r + 1) <= v) r++
    return r
}

/** A position in tiles as an integer of 1/256 of a tile: floor(v * 256 + 0.5). */
fun toX256(v: Float): Long = floor(v.toDouble() * 256.0 + 0.5).toLong()

/**
 * Where a traveller with [route] is on [day] at the tick [tick] of a day of [dayTicks] ticks (spec 07, "Travellers walk"): at its stop of
 * the day, or on its way in from the stop before or out toward the stop after, never past the middle.
 */
fun travellerPosition(route: List<Pair<Float, Float>>, walk: TravellerWalk, day: Long, tick: Long, dayTicks: Long): Pair<Float, Float> {
    val n = route.size.toLong()
    val s = Math.floorMod(day - 1, n)
    val here = route[s.toInt()]
    if (walk.speedX256 <= 0L || dayTicks <= 0L || n < 2L) return here
    val arrive = dayTicks * walk.arrivePm / 1000
    val depart = dayTicks * walk.departPm / 1000
    // still on its way in from the stop of the day before, or on its way out toward the stop of the day after
    val (otherIndex, walked) = when {
        tick < arrive -> Pair((s - 1 + n) % n, walk.speedX256 * (arrive - tick))
        tick >= depart -> Pair((s + 1) % n, walk.speedX256 * (tick - depart))
        else -> Pair(s, 0L)
    }
    val other = route[otherIndex.toInt()]
    val hx = toX256(here.first)
    val hy = toX256(here.second)
    val dx = toX256(other.first) - hx
    val dy = toX256(other.second) - hy
    val length = isqrt64(dx * dx + dy * dy)
    if (walked <= 0L || length == 0L) return here
    val w = min(walked, length / 2)
    return Pair((hx + dx * w / length).toFloat() / 256f, (hy + dy * w / length).toFloat() / 256f)
}
