package io.github.progliodario.aethermoor.core

import io.github.progliodario.aethermoor.core.sim.ChunkStore
import io.github.progliodario.aethermoor.core.sim.StreamConfig
import io.github.progliodario.aethermoor.core.sim.WorldSim
import io.github.progliodario.aethermoor.core.sim.loadCombatSetup
import io.github.progliodario.aethermoor.core.sim.makeStreamMap
import io.github.progliodario.aethermoor.core.sim.parseTileset
import io.github.progliodario.aethermoor.core.vector.QUALITY_LEVELS
import io.github.progliodario.aethermoor.core.vector.parseRecipe
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import java.io.File
import kotlin.math.ceil
import kotlin.math.max

/**
 * The budgets of the simulation on the JVM (docs/design/performance.md; item C4.2 of the operating program). The budgets are wide: they
 * catch a change that makes the generation of the world or a tick many times slower, not a few percent. The numbers go to
 * `build/performance.txt`, which the CI prints.
 */
class PerformanceTest {
    private val repoRoot = File(System.getProperty("aether.repoRoot") ?: error("aether.repoRoot is not set"))

    @Test
    fun theWorldAndTheTicksStayWithinTheirBudgets() {
        val pack = loadBasePack(repoRoot)
        val params = loadWorldParams(pack, "base:world/overworld").getOrThrow()
        val tileset = parseTileset(requireNotNull(pack.readDocument("base:tileset/overworld"))).getOrThrow()

        // the chunks: windows of 5 x 5 chunks far from each other, so that every chunk is generated anew
        val store = ChunkStore(params, 42uL, tileset)
        repeat(WARM_UP_WINDOWS) { store.keepAround(100 + it * 5, 60) }
        val chunkStart = System.nanoTime()
        repeat(WINDOWS) { store.keepAround(160 + it * 5, 80) }
        val chunkMs = (System.nanoTime() - chunkStart) / 1e6 / (WINDOWS * CHUNKS_PER_WINDOW)

        // the ticks: the player walks east through the streamed world for ten seconds
        val map = makeStreamMap(params)
        val setup = loadCombatSetup(pack, map, "base:protagonist/ren", 42uL, worldEnemyIds(params)).getOrThrow()
        val sim = WorldSim(map, tileset, 0f, setup, StreamConfig(params, 42uL))
        repeat(WARM_UP_TICKS) { sim.tick(1f, 0f, false) }
        val tickStart = System.nanoTime()
        repeat(TICKS) { sim.tick(1f, 0f, false) }
        val tickMs = (System.nanoTime() - tickStart) / 1e6 / TICKS

        val line = "jvm: %.3f ms a chunk (%d chunks), %.3f ms a tick (%d ticks walking)".format(chunkMs, WINDOWS * CHUNKS_PER_WINDOW, tickMs, TICKS)
        println(line)
        File("build").mkdirs()
        File("build/performance.txt").writeText(line + "\n")
        assertTrue(chunkMs < CHUNK_BUDGET_MS, "a chunk takes $chunkMs ms, the budget is $CHUNK_BUDGET_MS")
        assertTrue(tickMs < TICK_BUDGET_MS, "a tick takes $tickMs ms, the budget is $TICK_BUDGET_MS")
    }

    /**
     * The memory budget of the quality levels (spec 13, "Quality"): every recipe of the art of the pack, baked once at the largest bucket
     * of a level (four bytes a pixel, the size the rasterizer gives), fits in the budget of that level. Android keeps a copy of every
     * picture on the CPU for a lost context (risk R6), so it uses twice the bytes counted here.
     */
    @Test
    fun allTheArtBakedOnceAtTheLargestBucketOfALevelFitsItsBudget() {
        val pack = loadBasePack(repoRoot)
        val recipes = pack.documentPaths.filter { (_, path) ->
            path.startsWith("art/") && !path.startsWith("art/rigs/") && !path.startsWith("art/clips/")
        }.keys.mapNotNull { id -> pack.readDocument(id)?.let { parseRecipe(it).getOrNull() } }
        assertTrue(recipes.size > 100, "only ${recipes.size} recipes of art")
        for (level in QUALITY_LEVELS) {
            val scale = level.bucketCap / 32f
            val bytes = recipes.sumOf { r -> max(1, ceil(r.width * scale).toInt()).toLong() * max(1, ceil(r.height * scale).toInt()) * 4L }
            val mib = bytes / (1024 * 1024)
            println("quality ${level.id}: $mib MiB of ${recipes.size} recipes")
            assertTrue(bytes <= level.textureBudgetMib * 1024L * 1024L, "quality ${level.id}: $mib MiB, the budget is ${level.textureBudgetMib}")
        }
    }

    private companion object {
        const val WARM_UP_WINDOWS = 4
        const val WINDOWS = 12
        const val CHUNKS_PER_WINDOW = 25
        const val WARM_UP_TICKS = 120
        const val TICKS = 600

        /** Wide budgets (docs/design/performance.md): a frame of 60 Hz is 16.7 ms. */
        const val CHUNK_BUDGET_MS = 25.0
        const val TICK_BUDGET_MS = 4.0
    }
}
