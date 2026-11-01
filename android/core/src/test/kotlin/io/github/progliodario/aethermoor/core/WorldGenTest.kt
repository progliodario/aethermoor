package io.github.progliodario.aethermoor.core

import io.github.progliodario.aethermoor.core.sim.ACTIVE_RADIUS
import io.github.progliodario.aethermoor.core.sim.SaveMeta
import io.github.progliodario.aethermoor.core.sim.StreamConfig
import io.github.progliodario.aethermoor.core.sim.WorldSim
import io.github.progliodario.aethermoor.core.sim.chunkOf
import io.github.progliodario.aethermoor.core.sim.loadCombatSetup
import io.github.progliodario.aethermoor.core.sim.makeStreamMap
import io.github.progliodario.aethermoor.core.sim.parseTileset
import io.github.progliodario.aethermoor.core.sim.saveFromJson
import io.github.progliodario.aethermoor.core.sim.saveToJson
import java.io.File
import kotlin.math.abs
import kotlin.math.floor
import kotlin.math.max
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.int
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
    fun chunkWindowSuite() {
        val doc = Json.parseToJsonElement(File(repoRoot, "tests/conformance/chunk_window.json").readText()).jsonObject
        for (case in doc.getValue("cases").jsonArray) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val input = c.getValue("input").jsonObject
            val params = parseWorldParams(input.getValue("params").toString()).getOrThrow()
            val seed = hex(input.getValue("seed").jsonPrimitive.content)
            val after = c.getValue("expect").jsonObject.getValue("after").jsonArray

            // The enemy list of spec 09 ("Streaming"): spawner tiles with a dead flag.
            class Entry(val x: Int, val y: Int, var dead: Boolean)
            var enemies = ArrayList<Entry>()
            val cleared = HashMap<Pair<Int, Int>, Long>() // spawner tile -> world tick of the death
            var now = params.time.startTick
            var curX = input.getValue("start").jsonArray[0].jsonPrimitive.int
            var curY = input.getValue("start").jsonArray[1].jsonPrimitive.int
            fun enter(cx: Int, cy: Int) {
                for ((x, y) in generateChunk(seed, params, cx, cy).spawners) {
                    val died = cleared[Pair(x, y)]
                    if (died != null) {
                        if (now - died < params.spawnerRespawnTicks) continue
                        cleared.remove(Pair(x, y))
                    }
                    enemies.add(Entry(x, y, false))
                }
            }
            fun inside(i: Int, j: Int, wx: Int, wy: Int) = max(abs(i - wx), abs(j - wy)) <= 2
            fun digest(): ULong {
                var h = 0uL
                for (e in enemies) h = hash64(h, e.x.toLong(), e.y.toLong(), if (e.dead) 1L else 0L)
                return h
            }
            for (j in curY - 2..curY + 2) for (i in curX - 2..curX + 2) enter(i, j)
            assertEquals(after[0].jsonObject.getValue("count").jsonPrimitive.int, enemies.size, "$label start")
            assertEquals(hex(after[0].jsonObject.getValue("digest").jsonPrimitive.content), digest(), "$label start digest")
            for ((index, step) in input.getValue("steps").jsonArray.withIndex()) {
                val s = step.jsonArray
                if (s[0].jsonPrimitive.content == "move") {
                    val nx = s[1].jsonPrimitive.int
                    val ny = s[2].jsonPrimitive.int
                    enemies = ArrayList(enemies.filter { inside(it.x shr 5, it.y shr 5, nx, ny) })
                    for (j in ny - 2..ny + 2) for (i in nx - 2..nx + 2) if (!inside(i, j, curX, curY)) enter(i, j)
                    curX = nx
                    curY = ny
                } else if (s[0].jsonPrimitive.content == "wait") {
                    now += s[1].jsonPrimitive.long
                } else {
                    val e = enemies[s[1].jsonPrimitive.int]
                    e.dead = true
                    cleared[Pair(e.x, e.y)] = now
                }
                val want = after[index + 1].jsonObject
                assertEquals(want.getValue("count").jsonPrimitive.int, enemies.size, "$label step ${index + 1}")
                assertEquals(hex(want.getValue("digest").jsonPrimitive.content), digest(), "$label step ${index + 1} digest")
            }
        }
    }

    @Test
    fun settlementsSuite() {
        val doc = Json.parseToJsonElement(File(repoRoot, "tests/conformance/settlements.json").readText()).jsonObject
        for (case in doc.getValue("cases").jsonArray) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val input = c.getValue("input").jsonObject
            val want = c.getValue("expect").jsonObject
            val params = parseWorldParams(input.getValue("params").toString()).getOrThrow()
            val seed = hex(input.getValue("seed").jsonPrimitive.content)
            val block = input.getValue("block").jsonArray.map { it.jsonPrimitive.int }
            val found = settlementsIn(seed, params, block[0], block[1], block[2], block[3])
            assertEquals(want.getValue("count").jsonPrimitive.int, found.size, "$label count")
            for ((i, s) in want.getValue("settlements").jsonArray.withIndex()) {
                val e = s.jsonArray
                val got = found[i]
                val name = "$label settlement $i"
                assertEquals(e[0].jsonPrimitive.int, got.x, "$name x")
                assertEquals(e[1].jsonPrimitive.int, got.y, "$name y")
                assertEquals(e[2].jsonPrimitive.int, got.px, "$name px")
                assertEquals(e[3].jsonPrimitive.int, got.py, "$name py")
                assertEquals(e[4].jsonPrimitive.content, got.kind, "$name kind")
                assertEquals(e[5].jsonPrimitive.content, got.stamp, "$name stamp")
                assertEquals(e[6].jsonPrimitive.content, got.name, "$name name")
                assertEquals(e[7].jsonPrimitive.int, got.region, "$name region")
            }
            for (sample in want.getValue("regions").jsonArray) {
                val s = sample.jsonArray
                assertEquals(s[2].jsonPrimitive.int, regionAt(params, s[0].jsonPrimitive.int, s[1].jsonPrimitive.int), "$label region")
            }
            for (marker in want.getValue("markers").jsonArray) {
                val m = marker.jsonArray
                val s = settlementMarker(seed, params, m[0].jsonPrimitive.int, m[1].jsonPrimitive.int)
                assertEquals(m[2].jsonPrimitive.content, s?.name, "$label marker ${m[0]},${m[1]}")
            }
        }
    }

    @Test
    fun worldmapSuite() {
        val doc = Json.parseToJsonElement(File(repoRoot, "tests/conformance/worldmap.json").readText()).jsonObject
        for (case in doc.getValue("cases").jsonArray) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val input = c.getValue("input").jsonObject
            val want = c.getValue("expect").jsonObject
            assertEquals(MAP_CELL, input.getValue("cell").jsonPrimitive.int, "$label cell")
            val params = parseWorldParams(input.getValue("params").toString()).getOrThrow()
            val seed = hex(input.getValue("seed").jsonPrimitive.content)
            val cells = HashSet<Pair<Int, Int>>()
            for (position in input.getValue("positions").jsonArray) {
                explore(cells, params, position.jsonArray[0].jsonPrimitive.int, position.jsonArray[1].jsonPrimitive.int)
            }
            assertEquals(want.getValue("explored_count").jsonPrimitive.int, cells.size, "$label explored")
            assertEquals(hex(want.getValue("explored_digest").jsonPrimitive.content), digestCells(cells), "$label digest")
            for (sample in want.getValue("biomes").jsonArray) {
                val s = sample.jsonArray
                val cx = s[0].jsonPrimitive.int
                val cy = s[1].jsonPrimitive.int
                assertEquals(s[2].jsonPrimitive.int, biomeCode(seed, params, cx, cy), "$label cell $cx,$cy")
            }
        }
    }

    @Test
    fun worldtimeSuite() {
        val doc = Json.parseToJsonElement(File(repoRoot, "tests/conformance/worldtime.json").readText()).jsonObject
        for (case in doc.getValue("cases").jsonArray) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val input = c.getValue("input").jsonObject
            val params = parseTimeParams(input.getValue("time").jsonObject)
            val seed = hex(input.getValue("seed").jsonPrimitive.content)
            for (sample in c.getValue("expect").jsonObject.getValue("samples").jsonArray) {
                val want = sample.jsonObject
                val ticks = want.getValue("ticks").jsonPrimitive.long
                val got = sampleTime(seed, params, ticks)
                val name = "$label ticks $ticks"
                assertEquals(want.getValue("day").jsonPrimitive.long, got.day, "$name day")
                assertEquals(want.getValue("tod_pm").jsonPrimitive.int, got.todPm, "$name tod")
                assertEquals(want.getValue("light_pm").jsonPrimitive.int, got.lightPm, "$name light")
                assertEquals(want.getValue("kind").jsonPrimitive.content, got.kind, "$name kind")
                assertEquals(want.getValue("rain_pm").jsonPrimitive.int, got.rainPm, "$name rain")
                assertEquals(want.getValue("dim_pm").jsonPrimitive.int, got.dimPm, "$name dim")
                assertEquals(want.getValue("effective_light_pm").jsonPrimitive.int, got.effectiveLightPm, "$name effective light")
            }
        }
    }

    @Test
    fun theOverworldIsStreamedFromTheContentPackAndIsPlayable() {
        val pack = loadBasePack(repoRoot)
        val params = loadWorldParams(pack, "base:world/overworld").getOrThrow()
        assertEquals(8, params.regions.size)
        assertEquals(3, params.stamps.size)
        assertEquals(16384, params.width)
        val map = makeStreamMap(params)
        assertEquals(0, map.ground.size)
        assertEquals(1, map.npcs.size)
        assertEquals("guild_clerk_mira", map.npcs[0].key)
        val setup = loadCombatSetup(pack, map, "base:protagonist/ren", 42uL, params.spawnerEnemy).getOrThrow()
        val tileset = parseTileset(requireNotNull(pack.readDocument("base:tileset/overworld"))).getOrThrow()
        val sim = WorldSim(map, tileset, 0f, setup, StreamConfig(params, 42uL))
        val store = requireNotNull(sim.chunks)
        assertTrue(store.loaded >= 25)

        // The spawn clearing is walkable plains, and Mira stands next to it.
        val gid = sim.gidAt(map.width / 2, map.height / 2)
        assertTrue(gid == 1 || gid == 2)
        repeat(120) { sim.tick(0f, 0f, false) }
        assertTrue(sim.story.npcInRange() != null)
        assertEquals(params.time.startTick + 120, sim.worldTicks) // the world clock runs with the ticks
        assertEquals((sim.worldTicks * 1000 / params.time.dayTicks).toInt(), sim.time()?.todPm)
        assertEquals(9, sim.explored.size) // the cell of the spawn and its neighbours

        // The enemies are exactly those of the spawners in the 5 x 5 chunks around the player, whichever chunk that is.
        fun checkWindow() {
            val pcx = chunkOf(floor(sim.player.position.x).toInt())
            val pcy = chunkOf(floor(sim.player.position.y).toInt())
            val expected = HashSet<Pair<Int, Int>>()
            for (j in pcy - ACTIVE_RADIUS..pcy + ACTIVE_RADIUS) {
                for (i in pcx - ACTIVE_RADIUS..pcx + ACTIVE_RADIUS) expected.addAll(generateChunk(42uL, params, i, j).spawners)
            }
            val found = HashSet<Pair<Int, Int>>()
            for (e in sim.enemies) assertTrue(found.add(Pair(e.spawnerX, e.spawnerY)))
            assertEquals(expected, found)
            assertTrue(store.loaded <= 49)
        }
        checkWindow()

        // The spawn is at the left edge of its chunk: a few steps to the left enter the next chunk and the window moves.
        repeat(90) { sim.tick(-1f, 0f, false) }
        assertEquals(map.width / 2 / 32 - 1, chunkOf(floor(sim.player.position.x).toInt()))
        checkWindow()

        // Saving and loading into a fresh world of the same seed gives the same enemies.
        val state = sim.capture()
        assertEquals(sim.enemies.size, state.enemies.size)
        val json = saveToJson(state, SaveMeta("test", 1, "base:protagonist/ren", 42uL, "world"))
        val reread = saveFromJson(json).getOrThrow()
        val fresh = WorldSim(map, tileset, 0f, setup, StreamConfig(params, 42uL))
        fresh.restore(reread).getOrThrow()
        assertEquals(sim.enemies.size, fresh.enemies.size)
        assertEquals(sim.player.position.x, fresh.player.position.x)
        assertEquals(sim.worldTicks, fresh.worldTicks)
        assertEquals(sim.explored.toList(), fresh.explored.toList())
    }
}
