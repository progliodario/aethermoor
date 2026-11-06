package io.github.progliodario.aethermoor.game

import com.badlogic.gdx.Gdx
import com.badlogic.gdx.audio.AudioDevice
import io.github.progliodario.aethermoor.core.Pack
import io.github.progliodario.aethermoor.core.audio.SAMPLE_RATE
import io.github.progliodario.aethermoor.core.audio.parseSfx
import io.github.progliodario.aethermoor.core.audio.synthesize

/**
 * Plays the sound effects of the pack (spec 14): synthesizes them once, mixes up to 10 voices on a thread and writes them to the
 * audio device of libGDX (a streaming `AudioTrack`). If there is no device the board stays silent.
 */
class SoundBoard {
    private class Voice(val samples: ShortArray, val started: Long) {
        var position = 0
    }

    private val sounds = HashMap<String, ShortArray>()
    private val voices = ArrayList<Voice>()
    private var counter = 0L
    private var device: AudioDevice? = null
    private var thread: Thread? = null

    @Volatile
    private var running = false

    @Volatile
    var muted = false
        set(value) {
            field = value
            if (value) synchronized(voices) { voices.clear() }
        }

    fun open(pack: Pack, names: List<String>) {
        for (name in names) {
            val text = pack.readDocument("base:audio/sfx/$name") ?: continue
            parseSfx(text).getOrNull()?.let { sounds[name] = synthesize(it) }
        }
        device = runCatching { Gdx.audio.newAudioDevice(SAMPLE_RATE, true) }.getOrNull() ?: return
        running = true
        thread = Thread({ mixLoop() }, "aethermoor-audio").apply {
            isDaemon = true
            priority = Thread.MAX_PRIORITY
            start()
        }
    }

    fun play(name: String) {
        if (device == null || muted) return
        val samples = sounds[name] ?: return
        synchronized(voices) {
            if (voices.size >= MAX_VOICES) voices.minByOrNull { it.started }?.let { voices.remove(it) }
            voices.add(Voice(samples, ++counter))
        }
    }

    private fun mixLoop() {
        val buffer = ShortArray(CHUNK)
        while (running) {
            synchronized(voices) {
                for (i in 0 until CHUNK) {
                    var sum = 0
                    for (voice in voices) {
                        if (voice.position < voice.samples.size) sum += voice.samples[voice.position++]
                    }
                    buffer[i] = sum.coerceIn(-32767, 32767).toShort()
                }
                voices.removeAll { it.position >= it.samples.size }
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
    }
}
