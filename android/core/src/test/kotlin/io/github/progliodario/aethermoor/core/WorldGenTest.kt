package io.github.progliodario.aethermoor.core

import io.github.progliodario.aethermoor.core.sim.ACTIVE_RADIUS
import io.github.progliodario.aethermoor.core.sim.Effect
import io.github.progliodario.aethermoor.core.sim.SaveMeta
import io.github.progliodario.aethermoor.core.sim.StreamConfig
import io.github.progliodario.aethermoor.core.sim.WorldSim
import io.github.progliodario.aethermoor.core.sim.chunkOf
import io.github.progliodario.aethermoor.core.sim.loadCombatSetup
import io.github.progliodario.aethermoor.core.sim.makeStreamMap
import io.github.progliodario.aethermoor.core.sim.parseTileset
import io.github.progliodario.aethermoor.core.sim.questFromOffer
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
                val people = want.getValue("people").jsonArray
                assertEquals(people.size, chunk.people.size, "$name people")
                for ((i, entry) in people.withIndex()) {
                    val e = entry.jsonArray
                    val got = chunk.people[i]
                    val who = "$name person $i"
                    assertEquals(e[0].jsonPrimitive.content, got.key, "$who key")
                    assertEquals(e[1].jsonPrimitive.content, got.role, "$who role")
                    assertEquals(e[2].jsonPrimitive.int, got.x256, "$who x")
                    assertEquals(e[3].jsonPrimitive.int, got.y256, "$who y")
                    assertEquals(e[4].jsonPrimitive.content, got.name, "$who name")
                    assertEquals(e[5].jsonPrimitive.content, got.variant, "$who variant")
                    assertEquals(e[6].jsonPrimitive.content, got.tone, "$who tone")
                    assertEquals(e[7].jsonPrimitive.content, got.dialogue, "$who dialogue")
                    assertEquals(e[8].jsonPrimitive.content, got.place, "$who place")
                    assertEquals(e[9].jsonPrimitive.content, got.region, "$who region")
                    assertEquals(e[10].jsonPrimitive.content, got.quirk, "$who quirk")
                    assertEquals(e[11].jsonPrimitive.int, got.plazaX256, "$who plaza x")
                    assertEquals(e[12].jsonPrimitive.int, got.plazaY256, "$who plaza y")
                }
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
    fun routinesSuite() {
        val doc = Json.parseToJsonElement(File(repoRoot, "tests/conformance/routines.json").readText()).jsonObject
        for (case in doc.getValue("cases").jsonArray) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val input = c.getValue("input").jsonObject
            val params = parseWorldParams(input.getValue("params").toString()).getOrThrow()
            val seed = hex(input.getValue("seed").jsonPrimitive.content)
            val people = input.getValue("chunks").jsonArray.flatMap { chunk ->
                generateChunk(seed, params, chunk.jsonArray[0].jsonPrimitive.int, chunk.jsonArray[1].jsonPrimitive.int).people
            }
            val times = input.getValue("times").jsonArray
            val present = c.getValue("expect").jsonObject.getValue("present").jsonArray
            assertEquals(present.size, times.size, "$label times")
            for ((t, time) in times.withIndex()) {
                val tod = time.jsonPrimitive.int
                val got = people.mapNotNull { person ->
                    personPlacement(params, person, tod)?.let { "${person.key}|${it.state}|${it.x256}|${it.y256}" }
                }
                val want = present[t].jsonArray.map { row ->
                    val r = row.jsonArray
                    "${r[0].jsonPrimitive.content}|${r[1].jsonPrimitive.content}|${r[2].jsonPrimitive.int}|${r[3].jsonPrimitive.int}"
                }
                assertEquals(want, got, "$label time of day $tod")
            }
        }
    }

    @Test
    fun faunaSuite() {
        val doc = Json.parseToJsonElement(File(repoRoot, "tests/conformance/fauna.json").readText()).jsonObject
        for (case in doc.getValue("cases").jsonArray) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val input = c.getValue("input").jsonObject
            val params = parseWorldParams(input.getValue("params").toString()).getOrThrow()
            val seed = hex(input.getValue("seed").jsonPrimitive.content)
            val tiles = input.getValue("tiles").jsonArray
            val want = c.getValue("expect").jsonObject.getValue("spawners").jsonArray
            assertEquals(want.size, tiles.size, "$label count")
            for ((i, tile) in tiles.withIndex()) {
                val x = tile.jsonArray[0].jsonPrimitive.int
                val y = tile.jsonArray[1].jsonPrimitive.int
                val e = want[i].jsonArray
                val who = "$label spawner $x,$y"
                assertEquals(e[2].jsonPrimitive.int, regionAt(params, x, y), "$who region")
                assertEquals(e[3].jsonPrimitive.content, spawnerEnemyAt(seed, params, x, y), "$who enemy")
                assertEquals(e[4].jsonPrimitive.content, if (stampSpawnerAt(seed, params, x, y) != null) "" else faunaAt(seed, params, x, y).drop, "$who drop")
            }
        }
    }

    @Test
    fun guildSuite() {
        val doc = Json.parseToJsonElement(File(repoRoot, "tests/conformance/guild.json").readText()).jsonObject
        for (case in doc.getValue("cases").jsonArray) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val input = c.getValue("input").jsonObject
            val want = c.getValue("expect").jsonObject
            val params = parseWorldParams(input.getValue("params").toString()).getOrThrow()
            val seed = hex(input.getValue("seed").jsonPrimitive.content)
            for (rank in want.getValue("ranks").jsonArray) {
                val r = rank.jsonArray
                assertEquals(r[1].jsonPrimitive.int, rankIndex(params.guild, r[0].jsonPrimitive.long), "$label rank of ${r[0]}")
            }
            var index = 0
            for (site in input.getValue("sites").jsonArray) {
                val settlement = requireNotNull(settlementSite(seed, params, site.jsonArray[0].jsonPrimitive.int, site.jsonArray[1].jsonPrimitive.int))
                for (day in input.getValue("days").jsonArray) {
                    for (offer in offersFor(seed, params, settlement, day.jsonPrimitive.long)) {
                        val e = want.getValue("offers").jsonArray[index].jsonArray
                        val who = "$label offer $index"
                        assertEquals(e[0].jsonPrimitive.content, offer.id, "$who id")
                        assertEquals(e[1].jsonPrimitive.int, offer.minRank, "$who min rank")
                        assertEquals(e[2].jsonPrimitive.content, offer.template, "$who template")
                        assertEquals(e[3].jsonPrimitive.content, offer.type, "$who type")
                        assertEquals(e[4].jsonPrimitive.content, offer.target, "$who target")
                        assertEquals(e[5].jsonPrimitive.int, offer.count, "$who count")
                        assertEquals(e[6].jsonPrimitive.long, offer.gold, "$who gold")
                        assertEquals(e[7].jsonPrimitive.long, offer.xp, "$who xp")
                        assertEquals(e[8].jsonPrimitive.long, offer.points, "$who points")
                        assertEquals(e[9].jsonPrimitive.content, offer.place, "$who place")
                        assertEquals(e[10].jsonPrimitive.content, offer.tone, "$who tone")
                        val quest = questFromOffer(offer)
                        val q = want.getValue("quests").jsonArray[index].jsonObject
                        assertEquals(q.getValue("id").jsonPrimitive.content, quest.id, "$who quest id")
                        assertEquals(q.getValue("name").jsonPrimitive.content, quest.name, "$who quest name")
                        val stage = q.getValue("stages").jsonArray[0].jsonObject
                        assertEquals(stage.getValue("journal").jsonPrimitive.content, quest.stages[0].journal, "$who journal")
                        assertEquals(stage.getValue("objectives").jsonArray[0].jsonObject.getValue("count").jsonPrimitive.long, quest.stages[0].objectives[0].count, "$who objective")
                        for ((key, value) in q.getValue("args").jsonObject) assertEquals(value.jsonPrimitive.content, quest.args[key], "$who arg $key")
                        assertEquals(q.getValue("rewards").jsonArray[1].jsonObject.getValue("amount").jsonPrimitive.long, (quest.rewards[1] as Effect.AddGold).amount, "$who reward gold")
                        assertEquals(q.getValue("rewards").jsonArray[2].jsonObject.getValue("amount").jsonPrimitive.long, (quest.rewards[2] as Effect.AddGuildPoints).amount, "$who reward points")
                        assertEquals(offer.gold, resolveOffer(seed, params, offer.id)?.gold, "$who rebuild")
                        index++
                    }
                }
            }
            assertEquals(want.getValue("offers").jsonArray.size, index, "$label offers")
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
                assertEquals(want.getValue("season").jsonPrimitive.content, if (got.seasonIndex >= 0) params.seasons[got.seasonIndex].id else "", "$name season")
            }
        }
    }

    @Test
    fun theOverworldIsStreamedFromTheContentPackAndIsPlayable() {
        val pack = loadBasePack(repoRoot)
        val params = loadWorldParams(pack, "base:world/overworld").getOrThrow()
        assertEquals(8, params.regions.size)
        assertEquals(23, params.stamps.size)
        assertEquals(72, params.homeRadius)
        assertEquals(16384, params.width)
        val map = makeStreamMap(params)
        assertEquals(0, map.ground.size)
        assertEquals(1, map.npcs.size)
        assertEquals("guild_clerk_mira", map.npcs[0].key)
        val setup = loadCombatSetup(pack, map, "base:protagonist/ren", 42uL, worldEnemyIds(params)).getOrThrow()
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

        // The home village has people: walk up to its elder and talk (spec 07 and 09).
        sim.teleport(8228.5f, 8234.5f)
        sim.tick(0f, 0f, false)
        assertTrue(sim.story.dynamicNpcs.isNotEmpty())
        val elder = requireNotNull(sim.story.npcInRange())
        assertTrue(elder.name.isNotEmpty())
        assertTrue(elder.dialogue.startsWith("base:dialogue/role/"))
        assertTrue(elder.args.containsKey("place"))
        sim.story.interact()
        assertTrue(sim.story.dialogueActive)
        val spoken = sim.story.dialogueView()
        assertEquals("npc", spoken.speaker)
        assertEquals(elder.name, spoken.args["npc"])
        sim.story.advance() // the elder has a menu (errand, news, goodbye): pick goodbye (the last choice)
        sim.story.choose(sim.story.dialogueView().choices.size - 1)
        assertFalse(sim.story.dialogueActive)
        sim.teleport(map.width / 2 + 0.5f, map.height / 2 + 0.5f) // back to the spawn
        sim.tick(0f, 0f, false)
        checkWindow()

        // The shopkeeper of the home village sells the wares of Verdalis (spec 06): open the shop from the dialogue, buy, equip.
        sim.teleport(8236.5f, 8229.5f)
        sim.tick(0f, 0f, false)
        assertTrue(sim.story.npcInRange() != null)
        sim.story.interact()
        assertTrue(sim.story.dialogueActive)
        sim.story.advance()
        sim.story.choose(0) // "show me your wares"
        assertFalse(sim.story.dialogueActive)
        assertTrue(sim.shop != null)
        assertFalse(sim.buy("base:item/iron_sword")) // no gold yet
        sim.story.gold = 1000
        val attackBefore = sim.derived.atk
        assertTrue(sim.buy("base:item/iron_sword"))
        assertEquals(1000 - sim.buyPrice("base:item/iron_sword"), sim.story.gold)
        assertFalse(sim.buy("base:item/iron_sword")) // one is the limit for a weapon
        assertFalse(sim.buy("base:item/steel_sword")) // not sold in Verdalis
        assertTrue(sim.equip("base:item/iron_sword"))
        assertTrue(sim.derived.atk > attackBefore)
        assertFalse(sim.sell("base:item/iron_sword")) // the last copy of a worn item stays
        sim.closeShop()
        assertTrue(sim.shop == null)
        sim.teleport(map.width / 2 + 0.5f, map.height / 2 + 0.5f)
        sim.tick(0f, 0f, false)
        checkWindow()

        // The guild board of a town (spec 07, "Guild"): talk to a clerk, see the offers, accept one and keep it across a save.
        run {
            val clerkTown = settlementsIn(42uL, params, 0, 0, 63, 63).first { s -> s.slots.values.any { it.second == "guild_clerk" } }
            val clerkTile = clerkTown.slots.entries.first { it.value.second == "guild_clerk" }.key
            sim.teleport(clerkTile.first + 0.5f, clerkTile.second + 1.4f)
            sim.tick(0f, 0f, false)
            assertTrue(requireNotNull(sim.story.npcInRange()).dialogue.contains("guild_clerk"))
            sim.story.interact()
            sim.story.advance()
            sim.story.choose(0) // "show me the board"
            assertFalse(sim.story.dialogueActive)
            val board = requireNotNull(sim.board)
            assertEquals(params.guild.offersPerDay, board.offers.size)
            assertEquals(0, sim.guildRank())
            assertTrue(sim.acceptOffer(0))
            assertFalse(sim.acceptOffer(0)) // already taken
            assertFalse(sim.acceptOffer(3)) // needs a higher rank
            val questId = board.offers[0].id
            assertTrue(questId in sim.story.quests)
            val reloaded = WorldSim(map, tileset, 0f, setup, StreamConfig(params, 42uL))
            reloaded.restore(saveFromJson(saveToJson(sim.capture(), SaveMeta("test", 1, "base:protagonist/ren", 42uL, "world"))).getOrThrow()).getOrThrow()
            assertTrue(questId in reloaded.story.quests)
            sim.closeBoard()
            sim.teleport(map.width / 2 + 0.5f, map.height / 2 + 0.5f)
            sim.tick(0f, 0f, false)
            checkWindow()
        }

        // Threshold Stones (spec 09): wake the stone of the home village and the one of a town, then travel between them.
        run {
            fun stoneOf(s: Settlement): Pair<Float, Float> {
                for (cy in s.y / 32..(s.y + s.h - 1) / 32) {
                    for (cx in s.x / 32..(s.x + s.w - 1) / 32) {
                        for (prop in generateChunk(42uL, params, cx, cy).props) {
                            val tx = prop.x256 / 256
                            val ty = prop.y256 / 256
                            if (prop.art == params.stoneArt && tx >= s.x && tx < s.x + s.w && ty >= s.y && ty < s.y + s.h) {
                                return Pair(prop.x256 / 256f, prop.y256 / 256f)
                            }
                        }
                    }
                }
                return Pair(-1f, -1f)
            }
            sim.teleport(8230.5f, 8232.7f)
            sim.tick(0f, 0f, false)
            assertTrue(sim.stoneNear() != null)
            assertTrue(sim.useStone())
            val first = requireNotNull(sim.travel)
            assertTrue(first.fresh)
            assertEquals(1, first.stops.size)
            assertEquals(0, first.here)
            assertTrue(first.stops[0].place.isNotEmpty())
            assertFalse(sim.travelTo(0)) // never to the stone in use
            sim.closeTravel()
            assertTrue(sim.useStone()) // the second time the stone is not new
            assertFalse(requireNotNull(sim.travel).fresh)
            sim.closeTravel()

            val town = settlementsIn(42uL, params, 0, 0, 63, 63).first { it.kind == "town" }
            val stone = stoneOf(town)
            assertTrue(stone.first > 0f)
            sim.teleport(stone.first, stone.second + 0.9f)
            sim.tick(0f, 0f, false)
            assertTrue(sim.useStone())
            val second = requireNotNull(sim.travel)
            assertTrue(second.fresh)
            assertEquals(2, second.stops.size)
            assertEquals(1, second.here)
            assertEquals(town.name, second.stops[1].place)
            assertTrue(sim.travelTo(0))
            assertTrue(sim.travel == null)
            assertTrue(abs(sim.player.position.x - 8230.5f) < 1f)
            assertTrue(abs(sim.player.position.y - 8232.75f) < 1f)
            assertEquals(2, sim.stones.size)
            val saved = saveFromJson(saveToJson(sim.capture(), SaveMeta("test", 1, "base:protagonist/ren", 42uL, "world"))).getOrThrow()
            assertEquals(sim.stones.toList(), saved.stones)
            sim.teleport(map.width / 2 + 0.5f, map.height / 2 + 0.5f)
            sim.tick(0f, 0f, false)
            checkWindow()
        }

        // Routines (spec 08): the shopkeeper of the home village is at the counter by day and indoors at night.
        run {
            sim.teleport(8236.5f, 8229.5f)
            sim.tick(0f, 0f, false)
            val dayTicks = params.time.dayTicks.toLong()
            fun atTimeOfDay(todPm: Int) {
                val state = sim.capture()
                sim.restore(state.copy(worldTicks = (state.worldTicks / dayTicks) * dayTicks + dayTicks * todPm / 1000)).getOrThrow()
            }
            atTimeOfDay(500)
            assertTrue(sim.story.npcInRange() != null)
            atTimeOfDay(100)
            assertTrue(sim.story.npcInRange() == null)
            atTimeOfDay(500)
            assertTrue(sim.story.npcInRange() != null)
            sim.teleport(map.width / 2 + 0.5f, map.height / 2 + 0.5f)
            sim.tick(0f, 0f, false)
            checkWindow()
        }

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
        assertEquals("base:item/iron_sword", fresh.equippedWeapon)
        assertEquals(sim.derived.atk, fresh.derived.atk)
        assertEquals(sim.explored.toList(), fresh.explored.toList())
    }
}
