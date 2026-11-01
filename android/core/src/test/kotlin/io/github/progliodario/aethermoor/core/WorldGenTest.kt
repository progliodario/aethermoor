package io.github.progliodario.aethermoor.core

import io.github.progliodario.aethermoor.core.sim.makeTileMap
import java.io.File
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.long
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class WorldGenTest {
    private val repoRoot = File(System.getProperty("aether.repoRoot") ?: error("aether.repoRoot is not set"))

    private fun hex(text: String): ULong = text.removePrefix("0x").toULong(16)

    @Test
    fun worldgenSuite() {
        val doc = Json.parseToJsonElement(File(repoRoot, "tests/conformance/worldgen.json").readText()).jsonObject
        val cases = doc.getValue("cases").jsonArray
        assertFalse(cases.isEmpty())
        for (case in cases) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val input = c.getValue("input").jsonObject
            val want = c.getValue("expect").jsonObject
            val params = parseWorldParams(input.getValue("params").toString()).getOrThrow()
            val world = generateWorld(hex(input.getValue("seed").jsonPrimitive.content), params)

            assertEquals(want.getValue("tile_count").jsonPrimitive.long, world.tiles.size.toLong(), "$label tiles")
            for (probe in want.getValue("probes").jsonArray) {
                val p = probe.jsonArray
                val x = p[0].jsonPrimitive.content.toInt()
                val y = p[1].jsonPrimitive.content.toInt()
                assertEquals(p[2].jsonPrimitive.content.toInt(), world.tiles[y * world.width + x], "$label probe $x,$y")
            }
            for (row in want.getValue("row_digests").jsonArray) {
                val r = row.jsonArray
                val y = r[0].jsonPrimitive.content.toInt()
                assertEquals(hex(r[1].jsonPrimitive.content), digestTileRow(world.tiles, world.width, y), "$label row $y")
            }
            assertEquals(want.getValue("prop_count").jsonPrimitive.long, world.props.size.toLong(), "$label props")
            assertEquals(hex(want.getValue("prop_digest").jsonPrimitive.content), digestProps(world.props), "$label prop digest")
            assertEquals(want.getValue("spawner_count").jsonPrimitive.long, world.spawners.size.toLong(), "$label spawners")
            assertEquals(hex(want.getValue("spawner_digest").jsonPrimitive.content), digestSpawners(world.spawners), "$label spawner digest")
            val spawn = want.getValue("spawn").jsonArray
            assertEquals(spawn[0].jsonPrimitive.content.toInt(), world.spawnX256, "$label spawn x")
            assertEquals(spawn[1].jsonPrimitive.content.toInt(), world.spawnY256, "$label spawn y")
            val npcs = want.getValue("npcs").jsonArray
            assertEquals(npcs.size, world.npcs.size, "$label npc count")
            for ((i, n) in npcs.withIndex()) {
                assertEquals(n.jsonArray[0].jsonPrimitive.content, world.npcs[i].key, "$label npc $i key")
                assertEquals(n.jsonArray[1].jsonPrimitive.content.toInt(), world.npcs[i].x256, "$label npc $i x")
                assertEquals(n.jsonArray[2].jsonPrimitive.content.toInt(), world.npcs[i].y256, "$label npc $i y")
            }
            val histogram = world.tiles.groupBy { it }.mapValues { it.value.size.toLong() }
            val wantHistogram = want.getValue("gid_histogram").jsonObject
            assertEquals(wantHistogram.size, histogram.size, "$label histogram size")
            for ((gid, count) in wantHistogram) assertEquals(count.jsonPrimitive.long, histogram[gid.toInt()], "$label gid $gid")
        }
    }

    @Test
    fun worldgenChunksSuite() {
        val doc = Json.parseToJsonElement(File(repoRoot, "tests/conformance/worldgen_chunks.json").readText()).jsonObject
        for (case in doc.getValue("cases").jsonArray) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val input = c.getValue("input").jsonObject
            assertEquals(CHUNK_SIZE, input.getValue("chunk_size").jsonPrimitive.content.toInt(), "$label chunk size")
            val params = parseWorldParams(input.getValue("params").toString()).getOrThrow()
            val seed = hex(input.getValue("seed").jsonPrimitive.content)
            for (entry in c.getValue("expect").jsonObject.getValue("chunks").jsonArray) {
                val want = entry.jsonObject
                val at = want.getValue("chunk").jsonArray
                val cx = at[0].jsonPrimitive.content.toInt()
                val cy = at[1].jsonPrimitive.content.toInt()
                val name = "$label chunk $cx,$cy"
                val chunk = generateChunk(seed, params, cx, cy)
                assertEquals(CHUNK_SIZE * CHUNK_SIZE, chunk.tiles.size, name)
                for (probe in want.getValue("probes").jsonArray) {
                    val p = probe.jsonArray
                    val x = p[0].jsonPrimitive.content.toInt()
                    val y = p[1].jsonPrimitive.content.toInt()
                    assertEquals(p[2].jsonPrimitive.content.toInt(), chunk.tiles[y * CHUNK_SIZE + x], "$name probe $x,$y")
                }
                assertEquals(hex(want.getValue("tile_digest").jsonPrimitive.content), digestTiles(chunk.tiles), "$name tiles")
                assertEquals(want.getValue("prop_count").jsonPrimitive.long, chunk.props.size.toLong(), "$name props")
                assertEquals(hex(want.getValue("prop_digest").jsonPrimitive.content), digestProps(chunk.props), "$name prop digest")
                assertEquals(want.getValue("spawner_count").jsonPrimitive.long, chunk.spawners.size.toLong(), "$name spawners")
                assertEquals(hex(want.getValue("spawner_digest").jsonPrimitive.content), digestSpawners(chunk.spawners), "$name spawner digest")
                val histogram = chunk.tiles.groupBy { it }.mapValues { it.value.size.toLong() }
                val wantHistogram = want.getValue("gid_histogram").jsonObject
                assertEquals(wantHistogram.size, histogram.size, "$name histogram size")
                for ((gid, count) in wantHistogram) assertEquals(count.jsonPrimitive.long, histogram[gid.toInt()], "$name gid $gid")
            }
        }
    }

    @Test
    fun chunksAreTheRestrictionOfTheWorld() {
        val doc = Json.parseToJsonElement(File(repoRoot, "tests/conformance/worldgen.json").readText()).jsonObject
        val input = doc.getValue("cases").jsonArray[1].jsonObject.getValue("input").jsonObject // 80 x 72 tiles, border 2
        val params = parseWorldParams(input.getValue("params").toString()).getOrThrow()
        val seed = hex(input.getValue("seed").jsonPrimitive.content)
        val world = generateWorld(seed, params)
        var props = 0
        var spawners = 0
        for (cy in -1..3) {
            for (cx in -1..3) {
                val chunk = generateChunk(seed, params, cx, cy)
                for (i in chunk.tiles.indices) {
                    val x = cx * CHUNK_SIZE + i % CHUNK_SIZE
                    val y = cy * CHUNK_SIZE + i / CHUNK_SIZE
                    val inside = x in 0 until params.width && y in 0 until params.height
                    assertEquals(if (inside) world.tiles[y * params.width + x] else params.tileWater, chunk.tiles[i], "tile $x,$y")
                }
                props += chunk.props.size
                spawners += chunk.spawners.size
            }
        }
        assertEquals(world.props.size, props)
        assertEquals(world.spawners.size, spawners)
    }

    @Test
    fun theOverworldIsGeneratedFromTheContentPackAndIsDeterministic() {
        val pack = loadBasePack(repoRoot)
        val params = parseWorldParams(requireNotNull(pack.readDocument("base:world/overworld"))).getOrThrow()
        assertEquals(512, params.width)
        val world = generateWorld(42uL, params)
        val map = makeTileMap(world, params)
        assertEquals(512 * 512, map.ground.size)
        assertTrue(map.props.size > 1000)
        assertTrue(map.spawners.size > 20)
        assertEquals(1, map.npcs.size)
        assertEquals("guild_clerk_mira", map.npcs[0].key)
        val gid = map.gidAt(map.width / 2, map.height / 2)
        assertTrue(gid == 1 || gid == 2)
        assertTrue(generateWorld(42uL, params).tiles.contentEquals(world.tiles))
        assertFalse(generateWorld(43uL, params).tiles.contentEquals(world.tiles))
    }
}
