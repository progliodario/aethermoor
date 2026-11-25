package io.github.progliodario.aethermoor.core.sim

import io.github.progliodario.aethermoor.core.CHUNK_SIZE
import io.github.progliodario.aethermoor.core.GenPerson
import io.github.progliodario.aethermoor.core.GeneratedChunk
import io.github.progliodario.aethermoor.core.WorldParams
import io.github.progliodario.aethermoor.core.generateChunk
import java.util.concurrent.Callable
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.Future
import kotlin.math.abs
import kotlin.math.floor
import kotlin.math.max

// The chunks of a streamed world that are loaded right now. Spec: docs/spec/09-worldgen.md ("Streaming").
// Keep this file in step with desktop/src/sim/chunk_store.cpp.

/** Chunks around the player's chunk (Chebyshev distance) that are active: a 5 x 5 window. */
const val ACTIVE_RADIUS = 2

/** Loaded chunks farther than this are dropped (the extra ring avoids regenerating at a border). */
const val KEEP_RADIUS = 3

/** Chunk of a tile coordinate (floor division, also for negative tiles). */
fun chunkOf(tile: Int): Int = tile shr 5

/** A streamed world: its parameters and seed (spec 09, "Streaming"). */
class StreamConfig(val params: WorldParams, val seed: ULong)

class Chunk(
    val cx: Int,
    val cy: Int,
    /** CHUNK_SIZE * CHUNK_SIZE gids, row-major. */
    val tiles: IntArray,
    /** Same layout. */
    val solid: BooleanArray,
    /** Feet positions in tiles. */
    val props: List<Prop>,
    /** Absolute tile coordinates, in scan order. */
    val spawners: List<Pair<Int, Int>>,
    /** Settlement NPCs, in scan order. */
    val people: List<GenPerson>,
)

/**
 * The thread that generates chunks ahead of time (spec 09, "Streaming"; item C4.1), one for the whole app: a daemon of low priority, so it
 * never keeps the app alive and never takes the time of a frame.
 */
private val PREFETCH: ExecutorService by lazy {
    Executors.newSingleThreadExecutor { task ->
        Thread(task, "aether-chunks").apply {
            isDaemon = true
            priority = Thread.MIN_PRIORITY
        }
    }
}

/** A chunk asked of the thread of [PREFETCH]. */
private class Ahead(val cx: Int, val cy: Int, val future: Future<GeneratedChunk>)

class ChunkStore(val params: WorldParams, val seed: ULong, private val tileset: Tileset) {
    private val chunks = HashMap<Long, Chunk>()
    private val ahead = HashMap<Long, Ahead>()
    private var prefetching = false

    val loaded: Int get() = chunks.size

    /** How many chunks [keepAround] took from the thread (for the tests). */
    var prefetchedTaken = 0
        private set

    private fun key(cx: Int, cy: Int): Long = (cx.toLong() shl 32) or (cy.toLong() and 0xFFFFFFFFL)

    /**
     * Generates ahead of time, on a thread, the ring of chunks just outside the window (spec 09, "Streaming"; item C4.1). [keepAround]
     * takes a chunk from it when it is ready and generates it at once when it is not: the chunks the simulation sees, and the tick in
     * which it sees them, are the same with or without the thread. The thread only runs [generateChunk], which shares nothing.
     */
    fun startPrefetch() {
        prefetching = true
    }

    /** Waits until the thread has generated every chunk asked of it (for the tests). */
    fun awaitPrefetched() {
        for (a in ahead.values) runCatching { a.future.get() }
    }

    private fun generated(cx: Int, cy: Int): GeneratedChunk {
        val asked = ahead.remove(key(cx, cy))
        if (asked != null && asked.future.isDone && !asked.future.isCancelled) {
            val ready = runCatching { asked.future.get() }.getOrNull()
            if (ready != null) {
                prefetchedTaken++
                return ready
            }
        }
        asked?.future?.cancel(false) // not done yet: made at once here
        return generateChunk(seed, params, cx, cy)
    }

    /** Asks the thread for the ring just outside the window around (cx, cy), and forgets what is asked farther away. */
    private fun askRing(cx: Int, cy: Int) {
        if (!prefetching) return
        val far = ahead.values.filter { max(abs(it.cx - cx), abs(it.cy - cy)) > KEEP_RADIUS }
        for (a in far) {
            a.future.cancel(false)
            ahead.remove(key(a.cx, a.cy))
        }
        val ring = ACTIVE_RADIUS + 1
        for (j in cy - ring..cy + ring) {
            for (i in cx - ring..cx + ring) {
                val k = key(i, j)
                if (max(abs(i - cx), abs(j - cy)) != ring || chunks.containsKey(k) || ahead.containsKey(k)) continue
                ahead[k] = Ahead(i, j, PREFETCH.submit(Callable { generateChunk(seed, params, i, j) }))
            }
        }
    }

    private fun load(cx: Int, cy: Int): Chunk =
        chunks.getOrPut(key(cx, cy)) {
            val generated = generated(cx, cy)
            Chunk(
                cx,
                cy,
                generated.tiles,
                BooleanArray(generated.tiles.size) { tileset.tiles[generated.tiles[it]]?.solid ?: false },
                generated.props.map { Prop(it.art, it.x256 / 256f, it.y256 / 256f, it.radiusX100 / 100f) },
                generated.spawners,
                generated.people,
            )
        }

    /** Loads the chunks within [ACTIVE_RADIUS] of (cx, cy) and drops those beyond [KEEP_RADIUS]. */
    fun keepAround(cx: Int, cy: Int) {
        for (j in cy - ACTIVE_RADIUS..cy + ACTIVE_RADIUS) {
            for (i in cx - ACTIVE_RADIUS..cx + ACTIVE_RADIUS) load(i, j)
        }
        chunks.values.removeAll { max(abs(it.cx - cx), abs(it.cy - cy)) > KEEP_RADIUS }
        askRing(cx, cy)
    }

    fun find(cx: Int, cy: Int): Chunk? = chunks[key(cx, cy)]

    /** The gid at the tile, 0 when its chunk is not loaded. */
    fun gidAt(x: Int, y: Int): Int {
        val chunk = find(chunkOf(x), chunkOf(y)) ?: return 0
        return chunk.tiles[(y and 31) * CHUNK_SIZE + (x and 31)]
    }

    /** Tiles of chunks that are not loaded are solid. */
    fun isSolid(x: Int, y: Int): Boolean {
        val chunk = find(chunkOf(x), chunkOf(y)) ?: return true
        return chunk.solid[(y and 31) * CHUNK_SIZE + (x and 31)]
    }

    /** Calls [fn] for every prop of the chunk of (x, y) and its eight neighbours. */
    fun forEachPropNear(x: Float, y: Float, fn: (Prop) -> Unit) {
        val cx = chunkOf(floor(x).toInt())
        val cy = chunkOf(floor(y).toInt())
        for (j in cy - 1..cy + 1) {
            for (i in cx - 1..cx + 1) find(i, j)?.props?.forEach(fn)
        }
    }

    /** Calls [fn] for every prop of the loaded chunks inside the rectangle (in tiles). */
    fun forEachPropIn(x0: Float, y0: Float, x1: Float, y1: Float, fn: (Prop) -> Unit) {
        val cx0 = chunkOf(floor(x0).toInt())
        val cx1 = chunkOf(floor(x1).toInt())
        val cy0 = chunkOf(floor(y0).toInt())
        val cy1 = chunkOf(floor(y1).toInt())
        for (j in cy0..cy1) {
            for (i in cx0..cx1) {
                find(i, j)?.props?.forEach { if (it.x >= x0 && it.x <= x1 && it.y >= y0 && it.y <= y1) fn(it) }
            }
        }
    }
}
