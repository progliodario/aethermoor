package io.github.progliodario.aethermoor.core

import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.long

// World time, light and weather. Spec: docs/spec/08-world-time.md. Reference: tools/reference/worldtime.py.
// Integer arithmetic only: no floating point in this file. Keep it in step with desktop/src/core/worldtime.cpp.

class WeatherKind(val id: String, val weight: Int, val rainPm: Int, val dimPm: Int)

class TimeParams(
    val dayTicks: Int,
    val startTick: Long,
    /** Keyframes (time of day in permille, light in permille). */
    val light: List<Pair<Int, Int>>,
    val periodTicks: Int,
    val fadeTicks: Int,
    val kinds: List<WeatherKind>,
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
)

private fun lightAt(p: TimeParams, tod: Int): Int {
    val keys = p.light
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
    val total = p.kinds.sumOf { it.weight }.toULong()
    val roll = (hash64(seed, period, 21) shr 20) % total
    var acc = 0uL
    for (kind in p.kinds) {
        acc += kind.weight.toULong()
        if (roll < acc) return kind
    }
    return p.kinds.last()
}

fun sampleTime(seed: ULong, p: TimeParams, worldTicks: Long): TimeSample {
    val day = worldTicks / p.dayTicks + 1
    val tod = ((worldTicks % p.dayTicks) * 1000 / p.dayTicks).toInt()
    val light = lightAt(p, tod)
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
    return TimeSample(day, tod, light, cur.id, rain, dim, light * (1000 - dim) / 1000)
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
    )
}
