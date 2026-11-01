package io.github.progliodario.aethermoor.core

import kotlinx.serialization.json.Json
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

class WorldParams(
    val id: String,
    val width: Int,
    val height: Int,
    val border: Int,
    val spawnClearRadius: Int,
    val elevation: NoiseSpec,
    val moisture: NoiseSpec,
    val temperature: NoiseSpec,
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
    val tilesPlains: List<Int>,
    val props: Map<String, List<PropOption>>,
    val spawnerEnemy: String,
    val spawnerBiomes: List<String>,
    val spawnerMinDistance: Int,
    val spawnerPer10000: Int,
    val spawnerRespawnTicks: Int,
    val time: TimeParams,
    val npcs: List<WorldNpc>,
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

private fun gidFor(seed: ULong, p: WorldParams, biome: Biome, x: Int, y: Int): Int =
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
    for (y in 0 until p.height) {
        for (x in 0 until p.width) {
            val biome = biomeAt(seed, p, x, y)
            tiles[index++] = gidFor(seed, p, biome, x, y)
            if (!inClearing(p, x, y)) {
                propAt(seed, p, biome, x, y)?.let { props.add(it) }
                if (spawnerAt(seed, p, biome, x, y)) spawners.add(Pair(x, y))
            }
        }
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
    for (y in chunkY * CHUNK_SIZE until (chunkY + 1) * CHUNK_SIZE) {
        for (x in chunkX * CHUNK_SIZE until (chunkX + 1) * CHUNK_SIZE) {
            val biome = biomeAt(seed, p, x, y)
            tiles[index++] = gidFor(seed, p, biome, x, y)
            if (!inClearing(p, x, y)) {
                propAt(seed, p, biome, x, y)?.let { props.add(it) }
                if (spawnerAt(seed, p, biome, x, y)) spawners.add(Pair(x, y))
            }
        }
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
            water = threshold("water"), beach = threshold("beach"), mountain = threshold("mountain"),
            snow = threshold("snow"), desertHeat = threshold("desert_heat"), desertDry = threshold("desert_dry"),
            forestWet = threshold("forest_wet"),
            tileWater = tile("water"), tileBeach = tile("beach"), tileDesert = tile("desert"), tileSnow = tile("snow"),
            tileMountain = tile("mountain"), tileForest = tile("forest"),
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
            npcs = j.getValue("npcs").jsonArray.map {
                val n = it.jsonObject
                WorldNpc(
                    n.getValue("key").jsonPrimitive.content, n.getValue("dialogue").jsonPrimitive.content,
                    n.getValue("variant").jsonPrimitive.content, n.getValue("dx").jsonPrimitive.int, n.getValue("dy").jsonPrimitive.int,
                )
            },
        )
        require(params.tilesPlains.isNotEmpty() && params.width >= 1 && params.height >= 1) { "invalid world parameters" }
        params
    }
