package io.github.progliodario.aethermoor.core

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.long

// World time, light and weather. Spec: docs/spec/08-world-time.md. Reference: tools/reference/worldtime.py.
// Integer arithmetic only: no floating point in this file. Keep it in step with desktop/src/core/worldtime.cpp.

class WeatherKind(val id: String, val weight: Int, val rainPm: Int, val dimPm: Int)

/** A season of the year (spec 08, "Seasons"): [tint] is r, g, b, a laid over the screen; [weights] replace the weather weights of the kinds. */
class Season(val id: String, val days: Int, val tint: List<Int>, val weights: Map<String, Int>, val light: List<Pair<Int, Int>>)

class TimeParams(
    val dayTicks: Int,
    val startTick: Long,
    /** Keyframes (time of day in permille, light in permille). */
    val light: List<Pair<Int, Int>>,
    val periodTicks: Int,
    val fadeTicks: Int,
    val kinds: List<WeatherKind>,
    /** The seasons of the year in order; empty: no seasons. */
    val seasons: List<Season> = emptyList(),
)

class TimeSample(
    val day: Long,
    /** 0 = midnight, 500 = noon. */
    val todPm: Int,
    val lightPm: Int,
    val kind: String,
    val rainPm: Int,
    val dimPm: Int,
    val effectiveLightPm: Int,
    /** Index in [TimeParams.seasons], -1 without seasons. */
    val seasonIndex: Int = -1,
)

/** Index of the season of a day, -1 when the world has no seasons. */
fun seasonIndexOf(p: TimeParams, day: Long): Int {
    if (p.seasons.isEmpty()) return -1
    var d = (day - 1) % p.seasons.sumOf { it.days }
    for ((i, season) in p.seasons.withIndex()) {
        if (d < season.days) return i
        d -= season.days
    }
    return p.seasons.size - 1
}

private fun lightAt(keys: List<Pair<Int, Int>>, tod: Int): Int {
    for (i in 0 until keys.size - 1) {
        val (p0, l0) = keys[i]
        val (p1, l1) = keys[i + 1]
        if (tod in p0..p1) {
            val span = p1 - p0
            val d = tod - p0
            return if (l1 >= l0) l0 + (l1 - l0) * d / span else l0 - (l0 - l1) * d / span
        }
    }
    return keys.last().second
}

private fun kindOf(seed: ULong, p: TimeParams, period: Long): WeatherKind {
    val season = seasonIndexOf(p, period * p.periodTicks / p.dayTicks + 1) // the season of the first tick of the period
    val weights = if (season >= 0) p.seasons[season].weights else emptyMap()
    val total = p.kinds.sumOf { weights[it.id] ?: it.weight }.toULong()
    val roll = (hash64(seed, period, 21) shr 20) % total
    var acc = 0uL
    for (kind in p.kinds) {
        acc += (weights[kind.id] ?: kind.weight).toULong()
        if (roll < acc) return kind
    }
    return p.kinds.last()
}

fun sampleTime(seed: ULong, p: TimeParams, worldTicks: Long): TimeSample {
    val day = worldTicks / p.dayTicks + 1
    val tod = ((worldTicks % p.dayTicks) * 1000 / p.dayTicks).toInt()
    val seasonIndex = seasonIndexOf(p, day)
    val light = lightAt(seasonIndex.takeIf { it >= 0 }?.let { p.seasons[it].light }?.takeIf { it.isNotEmpty() } ?: p.light, tod)
    val period = worldTicks / p.periodTicks
    val cur = kindOf(seed, p, period)
    val prev = kindOf(seed, p, maxOf(period - 1, 0L))
    val since = (worldTicks % p.periodTicks).toInt()
    val rain: Int
    val dim: Int
    if (since >= p.fadeTicks) {
        rain = cur.rainPm
        dim = cur.dimPm
    } else {
        rain = (prev.rainPm * (p.fadeTicks - since) + cur.rainPm * since) / p.fadeTicks
        dim = (prev.dimPm * (p.fadeTicks - since) + cur.dimPm * since) / p.fadeTicks
    }
    return TimeSample(day, tod, light, cur.id, rain, dim, light * (1000 - dim) / 1000, seasonIndex)
}

/** Reads the `time` object of the world parameters. */
fun parseTimeParams(time: JsonObject): TimeParams {
    val weather = time.getValue("weather").jsonObject
    return TimeParams(
        dayTicks = time.getValue("day_ticks").jsonPrimitive.int,
        startTick = time.getValue("start_tick").jsonPrimitive.long,
        light = time.getValue("light").jsonArray.map { Pair(it.jsonArray[0].jsonPrimitive.int, it.jsonArray[1].jsonPrimitive.int) },
        periodTicks = weather.getValue("period_ticks").jsonPrimitive.int,
        fadeTicks = weather.getValue("fade_ticks").jsonPrimitive.int,
        kinds = weather.getValue("kinds").jsonArray.map {
            val k = it.jsonObject
            WeatherKind(
                k.getValue("id").jsonPrimitive.content, k.getValue("weight").jsonPrimitive.int,
                k.getValue("rain_pm").jsonPrimitive.int, k.getValue("dim_pm").jsonPrimitive.int,
            )
        },
        seasons = (time["seasons"] as? JsonArray)?.map {
            val s = it.jsonObject
            Season(
                s.getValue("id").jsonPrimitive.content, s.getValue("days").jsonPrimitive.int,
                s.getValue("tint").jsonArray.map { v -> v.jsonPrimitive.int },
                (s["weights"] as? JsonObject)?.mapValues { (_, v) -> v.jsonPrimitive.int } ?: emptyMap(),
                (s["light"] as? JsonArray)?.map { f -> Pair(f.jsonArray[0].jsonPrimitive.int, f.jsonArray[1].jsonPrimitive.int) } ?: emptyList(),
            )
        } ?: emptyList(),
    )
}
