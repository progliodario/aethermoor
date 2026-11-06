package io.github.progliodario.aethermoor.core.audio

import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.floor
import kotlin.math.ln
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

// Sound effect synthesizer. Spec: docs/spec/14-audio.md (normative algorithm). Schema: schemas/sfx_recipe.schema.json.
// Headless: it produces 16 bit samples; playing them is the job of the game module.

const val SAMPLE_RATE = 22050

enum class Wave { SINE, SQUARE, SAW, TRIANGLE, NOISE }

data class SfxLayer(
    val wave: Wave,
    val freqStart: Int,
    val freqEnd: Int,
    val volumePm: Int,
    val dutyPm: Int,
    val attackMs: Int,
    val decayMs: Int,
)

data class SfxRecipe(val id: String, val durationMs: Int, val volumePm: Int, val layers: List<SfxLayer>)

private fun parseWave(name: String): Wave =
    when (name) {
        "sine" -> Wave.SINE
        "square" -> Wave.SQUARE
        "saw" -> Wave.SAW
        "triangle" -> Wave.TRIANGLE
        "noise" -> Wave.NOISE
        else -> throw IllegalArgumentException("unknown wave $name")
    }

/** Parses a sound effect recipe from JSON text; the failure carries the reason. */
fun parseSfx(jsonText: String): Result<SfxRecipe> =
    runCatching {
        val j = Json.parseToJsonElement(jsonText).jsonObject
        val layers = j.getValue("layers").jsonArray.map { element ->
            val l = element.jsonObject
            SfxLayer(
                wave = parseWave(l.getValue("wave").jsonPrimitive.content),
                freqStart = l.getValue("freq_start").jsonPrimitive.int,
                freqEnd = l.getValue("freq_end").jsonPrimitive.int,
                volumePm = l.getValue("volume_pm").jsonPrimitive.int,
                dutyPm = l["duty_pm"]?.jsonPrimitive?.int ?: 500,
                attackMs = l.getValue("attack_ms").jsonPrimitive.int,
                decayMs = max(1, l.getValue("decay_ms").jsonPrimitive.int),
            )
        }
        SfxRecipe(
            id = j["id"]?.jsonPrimitive?.content ?: "",
            durationMs = j.getValue("duration_ms").jsonPrimitive.int,
            volumePm = j.getValue("volume_pm").jsonPrimitive.int,
            layers = layers,
        )
    }

private fun xorshift(start: Int): Int {
    var s = start
    s = s xor (s shl 13)
    s = s xor (s ushr 17)
    s = s xor (s shl 5)
    return s
}

/** Renders a recipe to mono samples at [SAMPLE_RATE]. */
fun synthesize(recipe: SfxRecipe): ShortArray {
    val n = max(0, recipe.durationMs * SAMPLE_RATE / 1000)
    val master = recipe.volumePm / 1000.0
    val mix = DoubleArray(n)
    for (layer in recipe.layers) {
        val fs = layer.freqStart.toDouble()
        val fe = layer.freqEnd.toDouble()
        val ratioLog = ln(fe / fs)
        val attack = layer.attackMs.toDouble()
        val decay = layer.decayMs.toDouble()
        val volume = layer.volumePm / 1000.0
        var phase = 0.0
        var state = 2463534242L.toInt()
        var held = 0.0
        var wrapped = true
        for (i in 0 until n) {
            val t = i.toDouble() / n.toDouble()
            val freq = if (layer.freqStart == layer.freqEnd) fs else fs * exp(t * ratioLog)
            val w =
                when (layer.wave) {
                    Wave.SINE -> sin(2.0 * Math.PI * phase)
                    Wave.SQUARE -> if (phase * 1000.0 < layer.dutyPm.toDouble()) 1.0 else -1.0
                    Wave.SAW -> 2.0 * phase - 1.0
                    Wave.TRIANGLE -> 4.0 * abs(phase - 0.5) - 1.0
                    Wave.NOISE -> {
                        if (wrapped) {
                            state = xorshift(state)
                            held = state.toDouble() / 2147483648.0
                        }
                        held
                    }
                }
            phase += freq / SAMPLE_RATE.toDouble()
            wrapped = phase >= 1.0
            if (wrapped) phase -= 1.0
            val ms = i.toDouble() * 1000.0 / SAMPLE_RATE.toDouble()
            val env = if (ms < attack) ms / attack else max(0.0, 1.0 - (ms - attack) / decay)
            mix[i] += w * env * volume
        }
    }
    return ShortArray(n) { i ->
        val x = max(-1.0, min(1.0, mix[i] * master))
        floor(x * 32767.0 + 0.5).toInt().toShort()
    }
}
