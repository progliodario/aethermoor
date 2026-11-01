package io.github.progliodario.aethermoor.core

import kotlin.math.abs
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

// World generation. Spec: docs/spec/09-worldgen.md. Reference: tools/reference/worldgen.py.
// Integer arithmetic only: no floating point in this file. Keep it in step with desktop/src/core/worldgen.cpp.

data class NoiseSpec(val salt: Int, val scale: Int, val octaves: Int)

data class PropOption(val art: String, val radiusX100: Int, val perMille: Int)

data class WorldNpc(val key: String, val dialogue: String, val variant: String, val dx: Int, val dy: Int)

class Region(val id: String, /** An $i18n: key. */ val name: String, val xPm: Int, val yPm: Int, val danger: Int)

class SettlementKind(val id: String, val weight: Int, val stamps: List<String>)

/** What a character of a stamp means (spec 09, "Settlements"); [tile] 0 keeps the terrain. */
class StampEntry(val tile: Int, val prop: String, val radiusX100: Int, val npc: String)

class Stamp(val w: Int, val h: Int, val anchorX: Int, val anchorY: Int, val rows: List<String>, val legend: Map<Char, StampEntry>)

/** A settlement: [x], [y] is the top-left tile of its footprint, [px], [py] the site point (the anchor of the stamp). */
class Settlement(
    val x: Int,
    val y: Int,
    val px: Int,
    val py: Int,
    val w: Int,
    val h: Int,
    val stamp: String,
    val kind: String,
    val name: String,
    val region: Int,
)

class WorldParams(
    val id: String,
    val width: Int,
    val height: Int,
    val border: Int,
    val spawnClearRadius: Int,
    val elevation: NoiseSpec,
    val moisture: NoiseSpec,
    val temperature: NoiseSpec,
    /** Rivers and roads: places where a field is near its middle value (spec 09). */
    val river: NoiseSpec,
    val riverHalfWidth: Int,
    val fordSalt: Int,
    val fordScale: Int,
    val fordMin: Int,
    val road: NoiseSpec,
    val roadHalfWidth: Int,
    val water: Int,
    val beach: Int,
    val mountain: Int,
    val snow: Int,
    val desertHeat: Int,
    val desertDry: Int,
    val forestWet: Int,
    val tileWater: Int,
    val tileBeach: Int,
    val tileDesert: Int,
    val tileSnow: Int,
    val tileMountain: Int,
    val tileForest: Int,
    val tileRiver: Int,
    val tileFord: Int,
    val tileRoad: Int,
    val tileBridge: Int,
    val tilesPlains: List<Int>,
    val props: Map<String, List<PropOption>>,
    val spawnerEnemy: String,
    val spawnerBiomes: List<String>,
    val spawnerMinDistance: Int,
    val spawnerPer10000: Int,
    val spawnerRespawnTicks: Int,
    val time: TimeParams,
    val npcs: List<WorldNpc>,
    val regions: List<Region>,
    val settlementPerMille: Int,
    val settlementKinds: List<SettlementKind>,
    val namesStart: List<String>,
    val namesMid: List<String>,
    val namesEnd: List<String>,
    /** By id, resolved by the loader. */
    val stamps: Map<String, Stamp>,
)

/** A prop standing on the world; [x256], [y256] are the feet position in 1/256 tile. */
class GenProp(val art: String, val radiusX100: Int, val x256: Int, val y256: Int)

class GenNpc(val key: String, val dialogue: String, val variant: String, val x256: Int, val y256: Int)

class GeneratedWorld(
    val width: Int,
    val height: Int,
    /** Row-major gids. */
    val tiles: IntArray,
    val props: List<GenProp>,
    val spawners: List<Pair<Int, Int>>,
    val spawnX256: Int,
    val spawnY256: Int,
    val npcs: List<GenNpc>,
)

private enum class Biome(val id: String) { WATER("water"), BEACH("beach"), MOUNTAIN("mountain"), SNOW("snow"), DESERT("desert"), FOREST("forest"), PLAINS("plains") }

private fun coord(tile: Int, scale: Int): Long = (tile.toLong() shl 16) / scale

private fun field(seed: ULong, spec: NoiseSpec, x: Int, y: Int): Long =
    fbm2(hash64(seed, spec.salt.toLong()), coord(x, spec.scale), coord(y, spec.scale), spec.octaves)

private fun inClearing(p: WorldParams, x: Int, y: Int): Boolean {
    val dx = (x - p.width / 2).toLong()
    val dy = (y - p.height / 2).toLong()
    return dx * dx + dy * dy < p.spawnClearRadius.toLong() * p.spawnClearRadius
}

private fun biomeAt(seed: ULong, p: WorldParams, x: Int, y: Int): Biome {
    if (x < p.border || y < p.border || x >= p.width - p.border || y >= p.height - p.border) return Biome.WATER
    if (inClearing(p, x, y)) return Biome.PLAINS
    val e = field(seed, p.elevation, x, y)
    if (e < p.water) return Biome.WATER
    if (e < p.beach) return Biome.BEACH
    if (e >= p.mountain) return Biome.MOUNTAIN
    val temperature = field(seed, p.temperature, x, y)
    if (temperature < p.snow) return Biome.SNOW
    val moisture = field(seed, p.moisture, x, y)
    if (temperature >= p.desertHeat && moisture < p.desertDry) return Biome.DESERT
    if (moisture >= p.forestWet) return Biome.FOREST
    return Biome.PLAINS
}

/** Site cell side in tiles (spec 09, "Settlements"). */
const val SITE_CELL = 256

/** Index of the region of the tile: the nearest center. */
fun regionAt(p: WorldParams, x: Int, y: Int): Int {
    var best = 0
    var bestDistance = -1L
    for ((i, region) in p.regions.withIndex()) {
        val dx = x - region.xPm.toLong() * p.width / 1000
        val dy = y - region.yPm.toLong() * p.height / 1000
        val d = dx * dx + dy * dy
        if (bestDistance < 0 || d < bestDistance) {
            best = i
            bestDistance = d
        }
    }
    return best
}

/** The settlement of each site cell, computed on demand. */
private class Sites(private val seed: ULong, private val p: WorldParams) {
    private val cells = HashMap<Long, Settlement?>()

    fun site(sx: Int, sy: Int): Settlement? {
        val key = (sx.toLong() shl 32) or (sy.toLong() and 0xFFFFFFFFL)
        if (!cells.containsKey(key)) cells[key] = compute(sx, sy)
        return cells[key]
    }

    /** Null outside every footprint; else the legend entry of the tile's character (itself null when it has none). */
    class Hit(val entry: StampEntry?)

    fun at(x: Int, y: Int): Hit? {
        val s = site(x shr 8, y shr 8) ?: return null
        val lx = x - s.x
        val ly = y - s.y
        if (lx < 0 || ly < 0 || lx >= s.w || ly >= s.h) return null
        val stamp = p.stamps.getValue(s.stamp)
        return Hit(stamp.legend[stamp.rows[ly][lx]])
    }

    private fun compute(sx: Int, sy: Int): Settlement? {
        val h = hash64(seed, sx.toLong(), sy.toLong(), 41)
        if ((h shr 40) % 1000uL >= p.settlementPerMille.toULong()) return null
        val px = sx * SITE_CELL + 40 + ((h shr 8) % 176uL).toInt()
        val py = sy * SITE_CELL + 40 + ((h shr 24) % 176uL).toInt()
        val k = hash64(seed, sx.toLong(), sy.toLong(), 42)
        val total = p.settlementKinds.sumOf { it.weight }.toULong()
        val roll = (k shr 20) % total
        var acc = 0uL
        var chosen = p.settlementKinds.last()
        for (kind in p.settlementKinds) {
            acc += kind.weight.toULong()
            if (roll < acc) {
                chosen = kind
                break
            }
        }
        val stampId = chosen.stamps[((k shr 40) % chosen.stamps.size.toULong()).toInt()]
        val stamp = p.stamps.getValue(stampId)
        val ox = px - stamp.anchorX
        val oy = py - stamp.anchorY
        val keepOut = (p.spawnClearRadius + 48).toLong()
        val dx = (px - p.width / 2).toLong()
        val dy = (py - p.height / 2).toLong()
        if (dx * dx + dy * dy < keepOut * keepOut) return null
        val points = listOf(
            Pair(px, py), Pair(ox, oy), Pair(ox + stamp.w - 1, oy), Pair(ox, oy + stamp.h - 1), Pair(ox + stamp.w - 1, oy + stamp.h - 1),
        )
        for ((x, y) in points) {
            val biome = biomeAt(seed, p, x, y)
            if (biome != Biome.PLAINS && biome != Biome.FOREST) return null
        }
        val n = hash64(seed, sx.toLong(), sy.toLong(), 43)
        val name = p.namesStart[(n % p.namesStart.size.toULong()).toInt()] +
            p.namesMid[((n shr 16) % p.namesMid.size.toULong()).toInt()] +
            p.namesEnd[((n shr 32) % p.namesEnd.size.toULong()).toInt()]
        return Settlement(ox, oy, px, py, stamp.w, stamp.h, stampId, chosen.id, name, regionAt(p, px, py))
    }
}

fun settlementSite(seed: ULong, p: WorldParams, siteX: Int, siteY: Int): Settlement? = Sites(seed, p).site(siteX, siteY)

/** The settlements of the site cells sx0..sx1, sy0..sy1 (inclusive), row-major. */
fun settlementsIn(seed: ULong, p: WorldParams, sx0: Int, sy0: Int, sx1: Int, sy1: Int): List<Settlement> {
    val sites = Sites(seed, p)
    val found = ArrayList<Settlement>()
    for (sy in sy0..sy1) for (sx in sx0..sx1) sites.site(sx, sy)?.let { found.add(it) }
    return found
}

/** The settlement shown on the world map cell: the one whose site point lies in the cell. */
fun settlementMarker(seed: ULong, p: WorldParams, cellX: Int, cellY: Int): Settlement? {
    val perSite = SITE_CELL / MAP_CELL
    val s = Sites(seed, p).site(cellX / perSite, cellY / perSite) ?: return null
    return if (s.px / MAP_CELL == cellX && s.py / MAP_CELL == cellY) s else null
}

/** Appends tile (x, y) and its prop or spawner. Settlements replace everything under their footprint. */
private fun emitTile(
    seed: ULong,
    p: WorldParams,
    sites: Sites,
    x: Int,
    y: Int,
    tiles: IntArray,
    index: Int,
    props: MutableList<GenProp>,
    spawners: MutableList<Pair<Int, Int>>,
) {
    val biome = biomeAt(seed, p, x, y)
    val hit = sites.at(x, y)
    if (hit != null) {
        val entry = hit.entry
        tiles[index] = if (entry != null && entry.tile != 0) entry.tile else gidFor(seed, p, biome, x, y, Overlay.NONE)
        if (entry != null && entry.prop.isNotEmpty()) props.add(GenProp(entry.prop, entry.radiusX100, x * 256 + 128, y * 256 + 192))
        return
    }
    val overlay = overlayAt(seed, p, biome, x, y)
    tiles[index] = gidFor(seed, p, biome, x, y, overlay)
    if (overlay == Overlay.NONE && !inClearing(p, x, y)) {
        propAt(seed, p, biome, x, y)?.let { props.add(it) }
        if (spawnerAt(seed, p, biome, x, y)) spawners.add(Pair(x, y))
    }
}

private enum class Overlay { NONE, RIVER, FORD, ROAD, BRIDGE }

private const val MID = 32768L

/** Spec 09, "Rivers and roads": only on land tiles outside the spawn clearing. */
private fun overlayAt(seed: ULong, p: WorldParams, biome: Biome, x: Int, y: Int): Overlay {
    if (biome == Biome.WATER || biome == Biome.MOUNTAIN || inClearing(p, x, y)) return Overlay.NONE
    val isRiver = abs(field(seed, p.river, x, y) - MID) < p.riverHalfWidth
    val isRoad = abs(field(seed, p.road, x, y) - MID) < p.roadHalfWidth
    if (isRiver) {
        if (isRoad) return Overlay.BRIDGE
        val scale = p.fordScale.toLong()
        val ford = noise2(hash64(seed, p.fordSalt.toLong()), (x.toLong() shl 16) / scale, (y.toLong() shl 16) / scale) >= p.fordMin
        return if (ford) Overlay.FORD else Overlay.RIVER
    }
    return if (isRoad) Overlay.ROAD else Overlay.NONE
}

private fun gidFor(seed: ULong, p: WorldParams, biome: Biome, x: Int, y: Int, overlay: Overlay): Int =
    when (overlay) {
        Overlay.RIVER -> p.tileRiver
        Overlay.FORD -> p.tileFord
        Overlay.ROAD -> p.tileRoad
        Overlay.BRIDGE -> p.tileBridge
        Overlay.NONE -> baseGid(seed, p, biome, x, y)
    }

private fun baseGid(seed: ULong, p: WorldParams, biome: Biome, x: Int, y: Int): Int =
    when (biome) {
        Biome.WATER -> p.tileWater
        Biome.BEACH -> p.tileBeach
        Biome.MOUNTAIN -> p.tileMountain
        Biome.SNOW -> p.tileSnow
        Biome.DESERT -> p.tileDesert
        Biome.FOREST -> p.tileForest
        Biome.PLAINS -> p.tilesPlains[((hash64(seed, x.toLong(), y.toLong(), 5) shr 40) % p.tilesPlains.size.toULong()).toInt()]
    }

private fun propAt(seed: ULong, p: WorldParams, biome: Biome, x: Int, y: Int): GenProp? {
    val options = p.props[biome.id] ?: return null
    if (options.isEmpty()) return null
    val h = hash64(seed, x.toLong(), y.toLong(), 7)
    val roll = ((h shr 20) % 1000uL).toLong()
    var total = 0L
    for (option in options) {
        total += option.perMille
        if (roll < total) {
            return GenProp(
                option.art, option.radiusX100,
                x * 256 + 48 + ((h shr 8) and 0x7FuL).toInt(),
                y * 256 + 128 + ((h shr 16) and 0x7FuL).toInt(),
            )
        }
    }
    return null
}

private fun spawnerAt(seed: ULong, p: WorldParams, biome: Biome, x: Int, y: Int): Boolean {
    if (biome.id !in p.spawnerBiomes) return false
    val dx = (x - p.width / 2).toLong()
    val dy = (y - p.height / 2).toLong()
    if (dx * dx + dy * dy < p.spawnerMinDistance.toLong() * p.spawnerMinDistance) return false
    return (hash64(seed, x.toLong(), y.toLong(), 11) shr 20) % 10000uL < p.spawnerPer10000.toULong()
}

fun generateWorld(seed: ULong, p: WorldParams): GeneratedWorld {
    val tiles = IntArray(p.width * p.height)
    val props = ArrayList<GenProp>()
    val spawners = ArrayList<Pair<Int, Int>>()
    var index = 0
    val sites = Sites(seed, p)
    for (y in 0 until p.height) {
        for (x in 0 until p.width) emitTile(seed, p, sites, x, y, tiles, index++, props, spawners)
    }
    val cx = p.width / 2
    val cy = p.height / 2
    return GeneratedWorld(
        p.width, p.height, tiles, props, spawners, cx * 256 + 128, cy * 256 + 128,
        p.npcs.map { GenNpc(it.key, it.dialogue, it.variant, (cx + it.dx) * 256 + 128, (cy + it.dy) * 256 + 128) },
    )
}

/** Side of a chunk in tiles: chunk (cx, cy) starts at tile (cx * CHUNK_SIZE, cy * CHUNK_SIZE). */
const val CHUNK_SIZE = 32

class GeneratedChunk(
    /** CHUNK_SIZE * CHUNK_SIZE gids, row-major. */
    val tiles: IntArray,
    /** In scan order inside the chunk. */
    val props: List<GenProp>,
    /** Absolute tile coordinates, in scan order. */
    val spawners: List<Pair<Int, Int>>,
)

/** Exactly the restriction of [generateWorld] to the window. Any chunk coordinates are valid: tiles outside the world are water. */
fun generateChunk(seed: ULong, p: WorldParams, chunkX: Int, chunkY: Int): GeneratedChunk {
    val tiles = IntArray(CHUNK_SIZE * CHUNK_SIZE)
    val props = ArrayList<GenProp>()
    val spawners = ArrayList<Pair<Int, Int>>()
    var index = 0
    val sites = Sites(seed, p)
    for (y in chunkY * CHUNK_SIZE until (chunkY + 1) * CHUNK_SIZE) {
        for (x in chunkX * CHUNK_SIZE until (chunkX + 1) * CHUNK_SIZE) emitTile(seed, p, sites, x, y, tiles, index++, props, spawners)
    }
    return GeneratedChunk(tiles, props, spawners)
}

/** Side of a world map cell in tiles (spec 09, "Exploration and the world map"). */
const val MAP_CELL = 128

/** Biome code of a cell: 0 water, 1 beach, 2 mountain, 3 snow, 4 desert, 5 forest, 6 plains. */
fun biomeCode(seed: ULong, p: WorldParams, cellX: Int, cellY: Int): Int =
    biomeAt(seed, p, cellX * MAP_CELL + MAP_CELL / 2, cellY * MAP_CELL + MAP_CELL / 2).ordinal

/** Marks the cell of the tile and its eight neighbours inside the world as explored. */
fun explore(cells: MutableSet<Pair<Int, Int>>, p: WorldParams, tileX: Int, tileY: Int) {
    val columns = (p.width + MAP_CELL - 1) / MAP_CELL
    val rows = (p.height + MAP_CELL - 1) / MAP_CELL
    val cx = tileX / MAP_CELL
    val cy = tileY / MAP_CELL
    for (y in cy - 1..cy + 1) {
        for (x in cx - 1..cx + 1) {
            if (x in 0 until columns && y in 0 until rows) cells.add(Pair(x, y))
        }
    }
}

fun digestCells(cells: Set<Pair<Int, Int>>): ULong {
    var h = 0uL
    for ((x, y) in cells.sortedWith(compareBy({ it.second }, { it.first }))) h = hash64(h, x.toLong(), y.toLong())
    return h
}

// Digests used by the conformance vectors.

fun digestTiles(tiles: IntArray): ULong {
    var h = 0uL
    for (gid in tiles) h = hash64(h, gid.toLong())
    return h
}

fun digestTileRow(tiles: IntArray, width: Int, row: Int): ULong {
    var h = 0uL
    for (x in 0 until width) h = hash64(h, tiles[row * width + x].toLong())
    return h
}

fun digestProps(props: List<GenProp>): ULong {
    var h = 0uL
    for (p in props) {
        val packed = p.radiusX100.toLong() * 4294967296L + (fnv1a64(p.art) shr 32).toLong()
        h = hash64(h, p.x256.toLong(), p.y256.toLong(), packed)
    }
    return h
}

fun digestSpawners(spawners: List<Pair<Int, Int>>): ULong {
    var h = 0uL
    for ((x, y) in spawners) h = hash64(h, x.toLong(), y.toLong())
    return h
}

// ------------------------------------------------------------------------------------ parsing

private fun noiseSpec(o: JsonObject) =
    NoiseSpec(o.getValue("salt").jsonPrimitive.int, o.getValue("scale").jsonPrimitive.int, o.getValue("octaves").jsonPrimitive.int)

private fun names(key: String, j: JsonObject): List<String> =
    j.getValue("settlements").jsonObject.getValue("names").jsonObject.getValue(key).jsonArray.map { it.jsonPrimitive.content }

private fun parseStamp(d: JsonObject): Stamp {
    val w = d.getValue("w").jsonPrimitive.int
    val h = d.getValue("h").jsonPrimitive.int
    val rows = d.getValue("rows").jsonArray.map { it.jsonPrimitive.content }
    require(rows.size == h && rows.all { it.length == w }) { "stamp rows do not match w and h" }
    val anchor = d.getValue("anchor").jsonArray
    val legend = d.getValue("legend").jsonObject.entries.associate { (key, value) ->
        val e = value.jsonObject
        key[0] to StampEntry(
            e["tile"]?.jsonPrimitive?.int ?: 0, e["prop"]?.jsonPrimitive?.content ?: "",
            e["radius_x100"]?.jsonPrimitive?.int ?: 0, e["npc"]?.jsonPrimitive?.content ?: "",
        )
    }
    return Stamp(w, h, anchor[0].jsonPrimitive.int, anchor[1].jsonPrimitive.int, rows, legend)
}

/** Reads the world document [worldId] of the pack and resolves the stamps of its settlements from the pack too. */
fun loadWorldParams(pack: Pack, worldId: String): Result<WorldParams> =
    runCatching {
        val j = Json.parseToJsonElement(requireNotNull(pack.readDocument(worldId)) { "missing world $worldId" }).jsonObject
        val defs = HashMap<String, JsonElement>()
        for (kind in j.getValue("settlements").jsonObject.getValue("kinds").jsonArray) {
            for (stamp in kind.jsonObject.getValue("stamps").jsonArray) {
                val id = stamp.jsonPrimitive.content
                defs[id] = Json.parseToJsonElement(requireNotNull(pack.readDocument(id)) { "missing stamp $id" })
            }
        }
        parseWorldParams(JsonObject(j + ("stamp_defs" to JsonObject(defs))).toString()).getOrThrow()
    }

fun parseWorldParams(jsonText: String): Result<WorldParams> =
    runCatching {
        val j = Json.parseToJsonElement(jsonText).jsonObject
        val t = j.getValue("thresholds").jsonObject
        val tiles = j.getValue("tiles").jsonObject
        val s = j.getValue("spawners").jsonObject
        fun threshold(key: String) = t.getValue(key).jsonPrimitive.int
        fun tile(key: String) = tiles.getValue(key).jsonPrimitive.int
        val params = WorldParams(
            id = j["id"]?.jsonPrimitive?.content ?: "",
            width = j.getValue("width").jsonPrimitive.int,
            height = j.getValue("height").jsonPrimitive.int,
            border = j.getValue("border").jsonPrimitive.int,
            spawnClearRadius = j.getValue("spawn_clear_radius").jsonPrimitive.int,
            elevation = noiseSpec(j.getValue("elevation").jsonObject),
            moisture = noiseSpec(j.getValue("moisture").jsonObject),
            temperature = noiseSpec(j.getValue("temperature").jsonObject),
            river = noiseSpec(j.getValue("river").jsonObject),
            riverHalfWidth = j.getValue("river").jsonObject.getValue("half_width").jsonPrimitive.int,
            fordSalt = j.getValue("river").jsonObject.getValue("ford_salt").jsonPrimitive.int,
            fordScale = j.getValue("river").jsonObject.getValue("ford_scale").jsonPrimitive.int,
            fordMin = j.getValue("river").jsonObject.getValue("ford_min").jsonPrimitive.int,
            road = noiseSpec(j.getValue("road").jsonObject),
            roadHalfWidth = j.getValue("road").jsonObject.getValue("half_width").jsonPrimitive.int,
            water = threshold("water"), beach = threshold("beach"), mountain = threshold("mountain"),
            snow = threshold("snow"), desertHeat = threshold("desert_heat"), desertDry = threshold("desert_dry"),
            forestWet = threshold("forest_wet"),
            tileWater = tile("water"), tileBeach = tile("beach"), tileDesert = tile("desert"), tileSnow = tile("snow"),
            tileMountain = tile("mountain"), tileForest = tile("forest"),
            tileRiver = tile("river"), tileFord = tile("ford"), tileRoad = tile("road"), tileBridge = tile("bridge"),
            tilesPlains = tiles.getValue("plains").jsonArray.map { it.jsonPrimitive.int },
            props = j.getValue("props").jsonObject.mapValues { (_, options) ->
                options.jsonArray.map {
                    val o = it.jsonObject
                    PropOption(o.getValue("art").jsonPrimitive.content, o.getValue("radius_x100").jsonPrimitive.int, o.getValue("per_mille").jsonPrimitive.int)
                }
            },
            spawnerEnemy = s.getValue("enemy").jsonPrimitive.content,
            spawnerBiomes = s.getValue("biomes").jsonArray.map { it.jsonPrimitive.content },
            spawnerMinDistance = s.getValue("min_distance").jsonPrimitive.int,
            spawnerPer10000 = s.getValue("per_10000").jsonPrimitive.int,
            spawnerRespawnTicks = s.getValue("respawn_ticks").jsonPrimitive.int,
            time = parseTimeParams(j.getValue("time").jsonObject),
            regions = j.getValue("regions").jsonArray.map {
                val r = it.jsonObject
                Region(
                    r.getValue("id").jsonPrimitive.content, r.getValue("name").jsonPrimitive.content,
                    r.getValue("x_pm").jsonPrimitive.int, r.getValue("y_pm").jsonPrimitive.int, r.getValue("danger").jsonPrimitive.int,
                )
            },
            settlementPerMille = j.getValue("settlements").jsonObject.getValue("per_mille").jsonPrimitive.int,
            settlementKinds = j.getValue("settlements").jsonObject.getValue("kinds").jsonArray.map {
                val k = it.jsonObject
                SettlementKind(
                    k.getValue("id").jsonPrimitive.content, k.getValue("weight").jsonPrimitive.int,
                    k.getValue("stamps").jsonArray.map { stamp -> stamp.jsonPrimitive.content },
                )
            },
            namesStart = names("start", j),
            namesMid = names("mid", j),
            namesEnd = names("end", j),
            stamps = (j["stamp_defs"]?.jsonObject ?: JsonObject(emptyMap())).mapValues { (_, def) -> parseStamp(def.jsonObject) },
            npcs = j.getValue("npcs").jsonArray.map {
                val n = it.jsonObject
                WorldNpc(
                    n.getValue("key").jsonPrimitive.content, n.getValue("dialogue").jsonPrimitive.content,
                    n.getValue("variant").jsonPrimitive.content, n.getValue("dx").jsonPrimitive.int, n.getValue("dy").jsonPrimitive.int,
                )
            },
        )
        require(params.tilesPlains.isNotEmpty() && params.width >= 1 && params.height >= 1 && params.fordScale >= 1) { "invalid world parameters" }
        params
    }
