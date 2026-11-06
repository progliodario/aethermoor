package io.github.progliodario.aethermoor.game

import com.badlogic.gdx.Gdx
import com.badlogic.gdx.audio.AudioDevice
import io.github.progliodario.aethermoor.core.Pack
import io.github.progliodario.aethermoor.core.audio.AmbienceRules
import io.github.progliodario.aethermoor.core.audio.EventTable
import io.github.progliodario.aethermoor.core.audio.MusicRules
import io.github.progliodario.aethermoor.core.audio.parseMusic
import io.github.progliodario.aethermoor.core.audio.parseMusicRules
import io.github.progliodario.aethermoor.core.audio.renderMusic
import io.github.progliodario.aethermoor.core.audio.SAMPLE_RATE
import io.github.progliodario.aethermoor.core.audio.parseEventTable
import io.github.progliodario.aethermoor.core.audio.parseSfx
import io.github.progliodario.aethermoor.core.audio.synthesize

/**
 * Plays the sounds of the pack (spec 14): renders them once, mixes up to 10 voices of sound effects and the looping ambience on a
 * thread, and writes them to the audio device of libGDX (a streaming `AudioTrack`). If there is no table or no device the board
 * stays silent.
 */
class SoundBoard {
    private class Voice(val samples: ShortArray, val gain: Float, val started: Long) {
        var position = 0
    }

    /** A piece of music that is heard: its layers (all of the same length), how loud it is and which layers are on. */
    private class MusicLoop(val piece: String, val layers: Map<String, ShortArray>) {
        var position = 0
        var gain = 0f
        var target = 1f
        val layerGain = HashMap<String, Float>()
    }

    private class Loop(val samples: ShortArray) {
        var position = 0
        var gain = 0f
        var target = 0f
    }

    private val sounds = java.util.concurrent.ConcurrentHashMap<String, ShortArray>()
    private val played = HashMap<String, Int>()
    private val cooldown = HashMap<String, Int>()
    private val voices = ArrayList<Voice>()
    private val loops = HashMap<String, Loop>()
    private var table: EventTable? = null
    private var pack: Pack? = null
    private val music = ArrayList<MusicLoop>() // the pieces that are heard, the newest last
    private var musicWanted = ""
    private var musicRendering = ""
    private var musicLayers: List<String> = listOf("base")

    @Volatile
    private var musicDone: MusicLoop? = null

    /** The rules that choose the piece, or null when the pack has none. */
    var musicRules: MusicRules? = null
        private set
    private var counter = 0L
    @Volatile
    private var device: AudioDevice? = null
    private var thread: Thread? = null

    @Volatile
    private var running = false

    @Volatile
    var muted = false
        set(value) {
            field = value
            if (value) {
                synchronized(voices) {
                    voices.clear()
                    loops.values.forEach { it.target = 0f }
                    music.forEach { it.target = 0f }
                }
                musicWanted = ""
            }
        }

    val ambienceRules: AmbienceRules? get() = table?.ambience

    fun open(pack: Pack) {
        val text = pack.readDocument("base:audio/events") ?: return
        val events = parseEventTable(text).getOrNull() ?: return
        table = events
        this.pack = pack
        musicRules = pack.readDocument("base:audio/music_rules")?.let { parseMusicRules(it).getOrNull() }
        // Rendering the sounds takes a moment: do it on the audio thread, which starts playing once they are ready.
        running = true
        thread = Thread({
            for (name in events.allSounds()) {
                val doc = pack.readDocument("base:audio/sfx/$name") ?: continue
                parseSfx(doc).getOrNull()?.let { sounds[name] = synthesize(it) }
            }
            device = runCatching { Gdx.audio.newAudioDevice(SAMPLE_RATE, true) }.getOrNull()
            if (device != null) mixLoop()
        }, "aethermoor-audio").apply {
            isDaemon = true
            priority = Thread.MAX_PRIORITY
            start()
        }
    }

    /** Plays the sound of an event (`swing`, `step.grass`, `enemy.wolf.hit`...), [volumePm] loud. */
    fun playEvent(event: String, volumePm: Int = 1000) {
        if (device == null || muted) return
        val entry = table?.events?.get(event) ?: return
        if ((cooldown[event] ?: 0) > 0) return
        cooldown[event] = entry.cooldown
        val n = played[event] ?: 0
        played[event] = n + 1
        val samples = sounds[entry.sounds[n % entry.sounds.size]] ?: return
        val gain = entry.volumePm * volumePm / 1.0e6f
        synchronized(voices) {
            if (voices.size >= MAX_VOICES) voices.minByOrNull { it.started }?.let { voices.remove(it) }
            voices.add(Voice(samples, gain, ++counter))
        }
    }

    /** The loops that should be heard, with their gain in permille; the others fade out. */
    fun setAmbience(gains: Map<String, Int>) {
        synchronized(voices) {
            loops.values.forEach { it.target = 0f }
            if (muted) return
            for ((name, gain) in gains) {
                val samples = sounds[name] ?: continue
                loops.getOrPut(name) { Loop(samples) }.target = gain / 1000f
            }
        }
    }

    /**
     * The music: the piece that should play and the layers that are on. A new piece is rendered in the background and then takes
     * over with a crossfade; the layers fade in and out.
     */
    fun setMusic(piece: String, layers: List<String>) {
        musicLayers = layers
        if (device == null || muted || piece.isEmpty() || piece == musicWanted) return
        musicWanted = piece
    }

    private fun updateMusic() {
        val done = musicDone
        if (done != null) {
            musicDone = null
            synchronized(voices) {
                music.forEach { it.target = 0f }
                music.add(done)
            }
            musicRendering = ""
        }
        val newest = music.lastOrNull()?.piece ?: ""
        if (musicWanted.isNotEmpty() && musicWanted != newest && musicWanted != musicRendering) {
            val text = pack?.readDocument("base:audio/music/$musicWanted")
            if (text == null) {
                musicWanted = ""
            } else {
                val name = musicWanted
                musicRendering = name
                Thread({
                    parseMusic(text).getOrNull()?.let { musicDone = MusicLoop(name, renderMusic(it)) }
                }, "aethermoor-music").apply { isDaemon = true; start() }
            }
        }
    }

    /** Call once per frame: counts down the cooldowns and starts the rendering of the music. */
    fun frame() {
        updateMusic()
        for (key in cooldown.keys.toList()) cooldown[key] = maxOf(0, (cooldown[key] ?: 0) - 1)
    }

    private fun mixLoop() {
        val buffer = ShortArray(CHUNK)
        val fadeStep = 1f / (1.5f * SAMPLE_RATE)
        val musicFade = 1f / (2.5f * SAMPLE_RATE)
        while (running) {
            synchronized(voices) {
                for (i in 0 until CHUNK) {
                    var sum = 0f
                    for (voice in voices) {
                        if (voice.position < voice.samples.size) sum += voice.samples[voice.position++] * voice.gain
                    }
                    for (loop in loops.values) {
                        if (loop.gain == 0f && loop.target == 0f) continue
                        loop.gain += (loop.target - loop.gain).coerceIn(-fadeStep, fadeStep)
                        sum += loop.samples[loop.position] * loop.gain
                        loop.position = (loop.position + 1) % loop.samples.size
                    }
                    for (piece in music) {
                        piece.gain += (piece.target - piece.gain).coerceIn(-musicFade, musicFade)
                        val newest = piece === music.last()
                        for ((layer, samples) in piece.layers) {
                            val on = newest && layer in musicLayers
                            val layerGain = piece.layerGain.getOrDefault(layer, 0f)
                            val next = layerGain + ((if (on) 1f else 0f) - layerGain).coerceIn(-fadeStep, fadeStep)
                            piece.layerGain[layer] = next
                            if (next > 0f && piece.gain > 0f) sum += samples[piece.position % samples.size] * piece.gain * next * MUSIC_BUS
                        }
                        piece.position++
                    }
                    buffer[i] = sum.coerceIn(-32767f, 32767f).toInt().toShort()
                }
                voices.removeAll { it.position >= it.samples.size }
                music.removeAll { it.target == 0f && it.gain <= 0f }
            }
            runCatching { device?.writeSamples(buffer, 0, CHUNK) }.onFailure { running = false }
        }
    }

    fun dispose() {
        running = false
        thread?.join(200)
        device?.dispose()
        device = null
    }

    private companion object {
        const val MAX_VOICES = 10
        const val CHUNK = 512
        const val MUSIC_BUS = 0.5f
    }
}
