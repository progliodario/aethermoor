package io.github.progliodario.aethermoor.core.audio

import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.floor
import kotlin.math.hypot
import kotlin.math.ln
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow
import kotlin.math.sin
import kotlin.math.sqrt
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

// Music: pieces of a few tracks on layers, rendered to seamless loops, and the director that chooses the piece and the layers.
// Spec: docs/spec/14-audio.md ("Music", normative). Headless.

data class MusicPatch(
    val wave: Wave,
    val attackMs: Int,
    val decayMs: Int,
    val sustainPm: Int,
    val releaseMs: Int,
    val dutyPm: Int = 500,
    val detuneCents: Int = 0,
    val glidePm: Int = 1000,
    val amDhz: Int = 0,
    val amDepthPm: Int = 0,
)

/** [layer]: base, tension, combat or boss. [bars]: one string of 16 steps per bar; it repeats when shorter than the piece. */
class MusicTrack(val layer: String, val patch: MusicPatch, val volumePm: Int, val bars: List<String>)

class MusicPiece(val id: String, val tempoBpm: Int, val bars: Int, val volumePm: Int, val tracks: List<MusicTrack>)

private const val STEPS_PER_BAR = 16
private const val FIGHT_FRAMES = 420L
private const val BOSS_FRAMES = 600L
private const val FIGHT_RANGE_TILES = 10.0

private fun waveOf(name: String): Wave =
    when (name) {
        "sine" -> Wave.SINE
        "square" -> Wave.SQUARE
        "saw" -> Wave.SAW
        "triangle" -> Wave.TRIANGLE
        "noise" -> Wave.NOISE
        else -> throw IllegalArgumentException("unknown wave $name")
    }

/** Parses a piece of music; the failure carries the reason. */
fun parseMusic(jsonText: String): Result<MusicPiece> =
    runCatching {
        val j = Json.parseToJsonElement(jsonText).jsonObject
        val tracks = j.getValue("tracks").jsonArray.map { element ->
            val t = element.jsonObject
            val p = t.getValue("patch").jsonObject
            val bars = t.getValue("bars").jsonArray.map { it.jsonPrimitive.content }
            require(bars.isNotEmpty()) { "a track without bars" }
            MusicTrack(
                layer = t.getValue("layer").jsonPrimitive.content,
                patch = MusicPatch(
                    wave = waveOf(p.getValue("wave").jsonPrimitive.content),
                    attackMs = p.getValue("attack_ms").jsonPrimitive.int,
                    decayMs = p.getValue("decay_ms").jsonPrimitive.int,
                    sustainPm = p.getValue("sustain_pm").jsonPrimitive.int,
                    releaseMs = p.getValue("release_ms").jsonPrimitive.int,
                    dutyPm = p["duty_pm"]?.jsonPrimitive?.int ?: 500,
                    detuneCents = p["detune_cents"]?.jsonPrimitive?.int ?: 0,
                    glidePm = p["glide_pm"]?.jsonPrimitive?.int ?: 1000,
                    amDhz = p["am_dhz"]?.jsonPrimitive?.int ?: 0,
                    amDepthPm = p["am_depth_pm"]?.jsonPrimitive?.int ?: 0,
                ),
                volumePm = t.getValue("volume_pm").jsonPrimitive.int,
                bars = bars,
            )
        }
        MusicPiece(
            id = j["id"]?.jsonPrimitive?.content ?: "",
            tempoBpm = j.getValue("tempo_bpm").jsonPrimitive.int,
            bars = j.getValue("bars").jsonPrimitive.int,
            volumePm = j.getValue("volume_pm").jsonPrimitive.int,
            tracks = tracks,
        )
    }

/** `C4`, `F#3`, `Bb2`: the pitch in Hz (A4 = 440). */
private fun noteFrequency(name: String): Double {
    var semitone =
        when (name[0]) {
            'C' -> 0
            'D' -> 2
            'E' -> 4
            'F' -> 5
            'G' -> 7
            'A' -> 9
            else -> 11
        }
    var i = 1
    while (i < name.length && (name[i] == '#' || name[i] == 'b')) {
        semitone += if (name[i] == '#') 1 else -1
        i++
    }
    val octave = name.substring(i).toInt()
    val midi = 12 * (octave + 1) + semitone
    return 440.0 * 2.0.pow((midi - 69) / 12.0)
}

private class NoteEvent(val first: Int, var length: Int, val chord: List<String>)

private fun eventsOf(track: MusicTrack, bars: Int): List<NoteEvent> {
    val tokens = ArrayList<String>()
    for (bar in 0 until bars) tokens.addAll(track.bars[bar % track.bars.size].trim().split(Regex("\\s+")))
    val notes = ArrayList<NoteEvent>()
    for ((step, token) in tokens.withIndex()) {
        if (token == "-" && notes.isNotEmpty() && notes.last().first + notes.last().length == step) {
            notes.last().length++
        } else if (token != "." && token != "-") {
            notes.add(NoteEvent(step, 1, token.split("+")))
        }
    }
    return notes
}

private fun xorshift32(start: Int): Int {
    var s = start
    s = s xor (s shl 13)
    s = s xor (s ushr 17)
    s = s xor (s shl 5)
    return s
}

/** One note of a patch: [length] samples held, then the release; [total] samples in all. */
private fun voice(patch: MusicPatch, freq: Double, length: Int, total: Int, stateSeed: Int): DoubleArray {
    val attack = max(1.0, patch.attackMs.toDouble())
    val decay = max(1.0, patch.decayMs.toDouble())
    val sustain = patch.sustainPm / 1000.0
    val release = max(1.0, patch.releaseMs.toDouble())
    val amHz = patch.amDhz / 10.0
    val amDepth = patch.amDepthPm / 1000.0
    val lengthMs = length.toDouble() * 1000.0 / SAMPLE_RATE.toDouble()
    val out = DoubleArray(total)
    val ratios =
        if (patch.detuneCents == 0) doubleArrayOf(1.0)
        else doubleArrayOf(2.0.pow(patch.detuneCents / 1200.0), 2.0.pow(-patch.detuneCents / 1200.0))
    val g = patch.glidePm / 1000.0
    val lg = if (patch.glidePm != 1000) ln(g) else 0.0
    val noteSeconds = length.toDouble() / SAMPLE_RATE.toDouble()
    for (ratio in ratios) {
        val f = freq * ratio
        var state = if (stateSeed != 0) stateSeed else 1
        var held = 0.0
        var prevCycle = -1.0
        for (i in 0 until total) {
            val t = i.toDouble() / SAMPLE_RATE.toDouble()
            val phaseTotal =
                if (patch.glidePm != 1000 && length > 0) {
                    if (i <= length) f * noteSeconds / lg * (g.pow(min(i, length).toDouble() / length.toDouble()) - 1.0)
                    else f * noteSeconds / lg * (g - 1.0) + f * g * (t - noteSeconds)
                } else {
                    f * t
                }
            val phase = phaseTotal - floor(phaseTotal)
            val w =
                when (patch.wave) {
                    Wave.SINE -> sin(2.0 * Math.PI * phase)
                    Wave.SQUARE -> if (phase * 1000.0 < patch.dutyPm.toDouble()) 1.0 else -1.0
                    Wave.SAW -> 2.0 * phase - 1.0
                    Wave.TRIANGLE -> 4.0 * abs(phase - 0.5) - 1.0
                    Wave.NOISE -> {
                        val cycle = floor(phaseTotal)
                        if (cycle != prevCycle) {
                            state = xorshift32(state)
                            held = state.toDouble() / 2147483648.0
                            prevCycle = cycle
                        }
                        held
                    }
                }
            val ms = i.toDouble() * 1000.0 / SAMPLE_RATE.toDouble()
            val heldMs = min(ms, lengthMs)
            var level =
                if (heldMs < attack) heldMs / attack
                else if (heldMs < attack + decay) 1.0 - (1.0 - sustain) * (heldMs - attack) / decay
                else sustain
            if (i >= length) level *= max(0.0, 1.0 - (ms - lengthMs) / release)
            val gain = if (amDepth > 0.0) 1.0 - amDepth * (0.5 - 0.5 * cos(2.0 * Math.PI * amHz * t)) else 1.0
            out[i] += w * level * gain / ratios.size.toDouble()
        }
    }
    return out
}

/** Renders every layer of a piece to mono samples at [SAMPLE_RATE]. All layers have the same length: the loop. */
fun renderMusic(piece: MusicPiece): Map<String, ShortArray> {
    val stepSamples = SAMPLE_RATE.toDouble() * 60.0 / (piece.tempoBpm.toDouble() * 4.0)
    val n = floor((piece.bars * STEPS_PER_BAR).toDouble() * stepSamples).toInt()
    val master = piece.volumePm / 1000.0
    val mixes = LinkedHashMap<String, DoubleArray>()
    for (track in piece.tracks) {
        val buf = mixes.getOrPut(track.layer) { DoubleArray(n) }
        val volume = track.volumePm / 1000.0
        val releaseSamples = (track.patch.releaseMs.toDouble() * SAMPLE_RATE / 1000.0).toInt()
        for ((index, note) in eventsOf(track, piece.bars).withIndex()) {
            val start = floor(note.first.toDouble() * stepSamples).toInt()
            val held = floor((note.first + note.length).toDouble() * stepSamples).toInt() - start
            val total = held + releaseSamples
            val seed = ((2463534242L + 2654435761L * index) and 0xFFFFFFFFL).toInt()
            val scale = volume / sqrt(note.chord.size.toDouble())
            for (name in note.chord) {
                val samples = voice(track.patch, noteFrequency(name), held, total, seed)
                for (i in 0 until total) buf[(start + i) % n] += samples[i] * scale
            }
        }
    }
    return mixes.mapValues { (_, buf) ->
        ShortArray(buf.size) { i -> floor(max(-1.0, min(1.0, buf[i] * master)) * 32767.0 + 0.5).toInt().toShort() }
    }
}

/** What the music director is told each frame. [screen]: title, game or dead. [place]: wild, settlement or dungeon. */
class MusicContext(
    val frame: Long,
    val screen: String = "game",
    val region: String = "",
    val todPm: Int = 500,
    val place: String = "wild",
    val quests: List<String> = emptyList(),
    val lowHp: Boolean = false,
    val cues: List<SoundCue> = emptyList(),
    val x: Double = 0.0,
    val y: Double = 0.0,
)

/** [night] empty: the same as [day]. */
class MusicChoiceRule(val day: String, val night: String = "")

class MusicRules(
    val title: String,
    val dead: String,
    val defaultRegion: String,
    /** Quest ID and piece; the first active one wins. */
    val quests: List<Pair<String, String>>,
    val places: Map<String, MusicChoiceRule>,
    val regions: Map<String, MusicChoiceRule>,
)

/** Parses the rules that choose the piece; the failure carries the reason. */
fun parseMusicRules(jsonText: String): Result<MusicRules> =
    runCatching {
        val j = Json.parseToJsonElement(jsonText).jsonObject
        fun choice(e: kotlinx.serialization.json.JsonElement): MusicChoiceRule {
            val o = e.jsonObject
            return MusicChoiceRule(o.getValue("day").jsonPrimitive.content, o["night"]?.jsonPrimitive?.content ?: "")
        }
        MusicRules(
            title = j.getValue("title").jsonPrimitive.content,
            dead = j.getValue("dead").jsonPrimitive.content,
            defaultRegion = j.getValue("default_region").jsonPrimitive.content,
            quests = j.getValue("quests").jsonArray.map {
                Pair(it.jsonObject.getValue("quest").jsonPrimitive.content, it.jsonObject.getValue("piece").jsonPrimitive.content)
            },
            places = j.getValue("places").jsonObject.mapValues { choice(it.value) },
            regions = j.getValue("regions").jsonObject.mapValues { choice(it.value) },
        )
    }

/** [layers] are in the order base, tension, combat, boss. */
class MusicChoice(val piece: String, val layers: List<String>)

class MusicDirector(private val rules: MusicRules) {
    private var lastFight = -1_000_000_000L
    private var lastBoss = -1_000_000_000L

    fun update(ctx: MusicContext): MusicChoice {
        for (cue in ctx.cues) {
            if (cue.kind == "gather") continue
            val near = hypot(cue.x - ctx.x, cue.y - ctx.y) <= FIGHT_RANGE_TILES
            if (cue.kind == "hit" || cue.kind == "hurt" || near) {
                lastFight = ctx.frame
                val big = cue.family == "king" || cue.family == "matron" || cue.family == "alpha" || cue.family == "knight"
                if (big && cue.kind != "die") lastBoss = ctx.frame
            }
        }
        val fight = ctx.frame - lastFight < FIGHT_FRAMES
        val boss = ctx.frame - lastBoss < BOSS_FRAMES
        val layers = arrayListOf("base")
        if (ctx.lowHp) layers.add("tension")
        if (fight || boss) layers.add("combat")
        if (boss) layers.add("boss")
        return MusicChoice(pieceFor(ctx), layers)
    }

    private fun pieceFor(ctx: MusicContext): String {
        if (ctx.screen == "title") return rules.title
        if (ctx.screen == "dead") return rules.dead
        for ((quest, piece) in rules.quests) {
            if (quest in ctx.quests && ctx.place != "dungeon") return piece
        }
        val day = ctx.todPm in 250..750
        rules.places[ctx.place]?.let { return if (day || it.night.isEmpty()) it.day else it.night }
        val region = rules.regions[ctx.region] ?: rules.regions[rules.defaultRegion] ?: return ""
        return if (day) region.day else region.night
    }
}
