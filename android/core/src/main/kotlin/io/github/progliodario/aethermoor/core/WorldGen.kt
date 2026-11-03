package io.github.progliodario.aethermoor.core

import kotlin.math.abs
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
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

/** An enemy of the fauna of a region (spec 09, "Fauna"): what a spawner makes and what it drops. */
class FaunaEntry(val enemy: String, val drop: String, val weight: Int)

class Region(val id: String, /** An $i18n: key. */ val name: String, val xPm: Int, val yPm: Int, val danger: Int, /** The voice of the people of the region. */ val tone: String,
    /** What the shops of the region sell (spec 06): prices in permille and the stock. */
    val shopPricePm: Int,
    val shopStock: List<String>,
    /** The enemies of the spawners of the region, by weight. */
    val fauna: List<FaunaEntry>,
    /** Pull on the fields of the terrain near its center (spec 09, "Regions"). */
    val biasElevation: Int = 0,
    val biasTemperature: Int = 0,
    val biasMoisture: Int = 0,
    /** Ground tiles by biome, instead of the ones of the world. */
    val ground: Map<String, List<Int>> = emptyMap(),
    /** Random props by biome, instead of the ones of the world. */
    val props: Map<String, List<PropOption>> = emptyMap(),
)

class SettlementKind(val id: String, val weight: Int, val stamps: List<String>)

/** What a character of a stamp means (spec 09, "Settlements"); [tile] 0 keeps the terrain. */
class StampEntry(val tile: Int, val prop: String, val radiusX100: Int, val npc: String, val spawner: String = "")

/** A hand-placed site with a fixed stamp, such as a dungeon (spec 09, "Landmarks"). */
class Landmark(val id: String, val name: String, val stamp: String, val kind: String, val dx: Int, val dy: Int)

class Stamp(
    val w: Int,
    val h: Int,
    val anchorX: Int,
    val anchorY: Int,
    val rows: List<String>,
    val legend: Map<Char, StampEntry>,
    /** Gathering tiles relative to the stamp (spec 08, Routines). */
    val spots: List<Pair<Int, Int>> = emptyList(),
)

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
    /** The cell of the site. */
    val sx: Int,
    val sy: Int,
    /** NPC slots by tile: (index in scan order of the stamp, role). */
    val slots: Map<Pair<Int, Int>, Pair<Int, String>>,
    /** Gathering tiles of the stamp, in the world. */
    val spots: List<Pair<Int, Int>> = emptyList(),
)

/** An NPC of a settlement (spec 09, "Settlement people"). */
class GenPerson(
    val key: String,
    val role: String,
    val x256: Int,
    val y256: Int,
    val name: String,
    val variant: String,
    val tone: String,
    val dialogue: String,
    val place: String,
    /** A text key. */
    val region: String,
    /** A text key. */
    val quirk: String,
    /** Gathering spot (spec 08), -1 when the stamp has none. */
    val plazaX256: Int = -1,
    val plazaY256: Int = -1,
)

/** A rank of the guild (spec 07, "Guild"). */
class GuildRank(val id: String, val points: Int)

class GuildTemplate(
    val id: String,
    /** "kill" or "collect". */
    val type: String,
    /** An enemy or item ID. */
    val target: String,
    val countMin: Int,
    val countMax: Int,
    val goldBase: Int,
    val goldPer: Int,
    val xpBase: Int,
    val xpPer: Int,
    val pointsBase: Int,
    val pointsPer: Int,
)

class GuildParams(val offersPerDay: Int, val ranks: List<GuildRank>, val templates: List<GuildTemplate>)

/** An offer of the board of a settlement. [id] is `board:<sx>:<sy>:<day>:<slot>`. */
class Offer(
    val id: String,
    val slot: Int,
    val minRank: Int,
    val template: String,
    val type: String,
    val target: String,
    val count: Int,
    val gold: Long,
    val xp: Long,
    val points: Long,
    val place: String,
    val tone: String,
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
    val spawnerBiomes: List<String>,
    val spawnerMinDistance: Int,
    val spawnerPer10000: Int,
    val spawnerRespawnTicks: Int,
    val time: TimeParams,
    val npcs: List<WorldNpc>,
    val guild: GuildParams,
    val landmarks: List<Landmark>,
    /** Daily routines by role: keyframes (from permille, state) with state work, plaza or away (spec 08). */
    val routines: Map<String, List<Pair<Int, String>>>,
    /** The prop that is a Threshold Stone and how near the player must be to use it, in 1/100 tile (spec 09). */
    val stoneArt: String,
    val stoneRangeX100: Int,
    /** Tiles over which the biases of the regions are blended (spec 09, "Regions"); 0: no biases. */
    val regionBlend: Int,

    /** Difficulty (spec 04): health and attack of the creatures of the streamed world, in percent. */
    val enemyHpPct: Int,
    val enemyAtkPct: Int,

    /** Tiles of plains around the footprint of a landmark (spec 09); 0: none. */
    val landmarkClearing: Int,

    /** The home meadow and village (spec 09); [homeRadius] 0: none. */
    val homeRadius: Int,
    val homeStamp: String,
    val homeDx: Int,
    val homeDy: Int,
    val regions: List<Region>,
    val settlementPerMille: Int,
    val settlementKinds: List<SettlementKind>,
    val namesStart: List<String>,
    val namesMid: List<String>,
    val namesEnd: List<String>,
    /** Dialogue id of a settlement NPC with {role} and {tone}. */
    val settlementDialogue: String,
    val variants: List<String>,
    val quirks: List<String>,
    val peopleStart: List<String>,
    val peopleEnd: List<String>,
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
    val people: List<GenPerson> = emptyList(),
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

/** Inside the clearing of a landmark: its footprint grown by `landmarkClearing` tiles (spec 09, "Landmarks"). */
private fun inLandmarkClearing(p: WorldParams, x: Int, y: Int): Boolean {
    val r = p.landmarkClearing
    if (r <= 0) return false
    for (landmark in p.landmarks) {
        val px = p.width / 2 + landmark.dx
        val py = p.height / 2 + landmark.dy
        if ((px shr 8) != (x shr 8) || (py shr 8) != (y shr 8)) continue
        val stamp = p.stamps.getValue(landmark.stamp)
        val x0 = px - stamp.anchorX - r
        val y0 = py - stamp.anchorY - r
        if (x >= x0 && x < x0 + stamp.w + 2 * r && y >= y0 && y < y0 + stamp.h + 2 * r) return true
    }
    return false
}

private fun biomeAt(seed: ULong, p: WorldParams, x: Int, y: Int): Biome {
    val biome = naturalBiomeAt(seed, p, x, y)
    if ((biome == Biome.WATER || biome == Biome.MOUNTAIN) && x >= p.border && y >= p.border && x < p.width - p.border &&
        y < p.height - p.border && inLandmarkClearing(p, x, y)
    ) {
        return Biome.PLAINS
    }
    return biome
}

/** The pull of the regions on the elevation, temperature and moisture fields at a tile (spec 09, "Regions"): a weighted mean of their biases, shifted to be positive before the division. */
private fun regionBias(p: WorldParams, x: Int, y: Int): LongArray {
    val bias = LongArray(3)
    if (p.regionBlend <= 0) return bias
    val shift = 32768L
    val reach2 = p.regionBlend.toLong() * p.regionBlend
    var total = 0L
    var sumE = 0L
    var sumT = 0L
    var sumM = 0L
    for (r in p.regions) {
        val dx = x - r.xPm.toLong() * p.width / 1000
        val dy = y - r.yPm.toLong() * p.height / 1000
        val weight = reach2 - (dx * dx + dy * dy)
        if (weight <= 0L) continue
        total += weight
        sumE += (r.biasElevation + shift) * weight
        sumT += (r.biasTemperature + shift) * weight
        sumM += (r.biasMoisture + shift) * weight
    }
    if (total == 0L) return bias
    bias[0] = sumE / total - shift
    bias[1] = sumT / total - shift
    bias[2] = sumM / total - shift
    return bias
}

private fun naturalBiomeAt(seed: ULong, p: WorldParams, x: Int, y: Int): Biome {
    if (x < p.border || y < p.border || x >= p.width - p.border || y >= p.height - p.border) return Biome.WATER
    if (inClearing(p, x, y)) return Biome.PLAINS
    if (p.homeRadius > 0) {
        val dx = (x - p.width / 2).toLong()
        val dy = (y - p.height / 2).toLong()
        if (dx * dx + dy * dy < p.homeRadius.toLong() * p.homeRadius) return Biome.PLAINS // the home meadow
    }
    val bias = regionBias(p, x, y)
    val e = field(seed, p.elevation, x, y) + bias[0]
    if (e < p.water) return Biome.WATER
    if (e < p.beach) return Biome.BEACH
    if (e >= p.mountain) return Biome.MOUNTAIN
    val temperature = field(seed, p.temperature, x, y) + bias[1]
    if (temperature < p.snow) return Biome.SNOW
    val moisture = field(seed, p.moisture, x, y) + bias[2]
    if (temperature >= p.desertHeat && moisture < p.desertDry) return Biome.DESERT
    if (moisture >= p.forestWet) return Biome.FOREST
    return Biome.PLAINS
}

/** Site cell side in tiles (spec 09, "Settlements"). */
const val SITE_CELL = 256

/** Index of the region of the tile: the nearest center. */
/** The enemy that the stamp under the tile names for a spawner there (dungeons), if any. */
fun stampSpawnerAt(seed: ULong, p: WorldParams, x: Int, y: Int): String? =
    Sites(seed, p).at(x, y)?.entry?.spawner?.takeIf { it.isNotEmpty() }

/** The enemy of the spawner on the tile: the one of its stamp, else a pick of the fauna of its region (spec 09). */
fun spawnerEnemyAt(seed: ULong, p: WorldParams, x: Int, y: Int): String = stampSpawnerAt(seed, p, x, y) ?: faunaAt(seed, p, x, y).enemy

/** Every enemy a spawner of the world can make (fauna of the regions and spawners of the stamps), sorted. */
fun worldEnemyIds(p: WorldParams): List<String> {
    val ids = sortedSetOf<String>()
    for (region in p.regions) for (entry in region.fauna) ids.add(entry.enemy)
    for (stamp in p.stamps.values) for (entry in stamp.legend.values) if (entry.spawner.isNotEmpty()) ids.add(entry.spawner)
    return ids.toList()
}

/** The entry that [r] falls on when the entries share the sum of the weights as slots, in order. */
fun pickFauna(entries: List<FaunaEntry>, r: ULong): FaunaEntry {
    var rest = r % entries.sumOf { it.weight }.toULong()
    for (entry in entries) {
        if (rest < entry.weight.toULong()) return entry
        rest -= entry.weight.toULong()
    }
    return entries.last()
}

/** The fauna entry of the spawner on tile (x, y): a weighted pick among the fauna of its region (spec 09). */
fun faunaAt(seed: ULong, p: WorldParams, x: Int, y: Int): FaunaEntry =
    pickFauna(p.regions[regionAt(p, x, y)].fauna, hash64(seed, x.toLong(), y.toLong(), 12L) shr 20)

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
    class Hit(val entry: StampEntry?, val settlement: Settlement)

    fun at(x: Int, y: Int): Hit? {
        val s = site(x shr 8, y shr 8) ?: return null
        val lx = x - s.x
        val ly = y - s.y
        if (lx < 0 || ly < 0 || lx >= s.w || ly >= s.h) return null
        val stamp = p.stamps.getValue(s.stamp)
        return Hit(stamp.legend[stamp.rows[ly][lx]], s)
    }

    /** The home village: fixed position, stamp and kind near the spawn (spec 09, "The home village"). */
    private fun home(sx: Int, sy: Int, px: Int, py: Int): Settlement {
        val stamp = p.stamps.getValue(p.homeStamp)
        val n = hash64(seed, sx.toLong(), sy.toLong(), 43)
        val name = p.namesStart[(n % p.namesStart.size.toULong()).toInt()] +
            p.namesMid[((n shr 16) % p.namesMid.size.toULong()).toInt()] +
            p.namesEnd[((n shr 32) % p.namesEnd.size.toULong()).toInt()]
        val kind = p.settlementKinds.firstOrNull { p.homeStamp in it.stamps }?.id ?: "village"
        return withSlots(px - stamp.anchorX, py - stamp.anchorY, px, py, stamp, p.homeStamp, kind, name, sx, sy)
    }

    /** Builds the settlement with the NPC slots of its stamp (the characters with an npc role, in scan order). */
    private fun withSlots(x: Int, y: Int, px: Int, py: Int, stamp: Stamp, stampId: String, kind: String, name: String, sx: Int, sy: Int): Settlement {
        val slots = LinkedHashMap<Pair<Int, Int>, Pair<Int, String>>()
        for ((ly, row) in stamp.rows.withIndex()) {
            for ((lx, ch) in row.withIndex()) {
                val entry = stamp.legend[ch]
                if (entry != null && entry.npc.isNotEmpty()) slots[Pair(x + lx, y + ly)] = Pair(slots.size, entry.npc)
            }
        }
        return Settlement(x, y, px, py, stamp.w, stamp.h, stampId, kind, name, regionAt(p, px, py), sx, sy, slots, stamp.spots.map { Pair(x + it.first, y + it.second) })
    }

    private fun compute(sx: Int, sy: Int): Settlement? {
        if (p.homeRadius > 0) {
            val hx = p.width / 2 + p.homeDx
            val hy = p.height / 2 + p.homeDy
            if ((hx shr 8) == sx && (hy shr 8) == sy) return home(sx, sy, hx, hy)
        }
        for (landmark in p.landmarks) {
            val lx = p.width / 2 + landmark.dx
            val ly = p.height / 2 + landmark.dy
            if ((lx shr 8) == sx && (ly shr 8) == sy) {
                val stamp = p.stamps.getValue(landmark.stamp)
                return withSlots(lx - stamp.anchorX, ly - stamp.anchorY, lx, ly, stamp, landmark.stamp, landmark.kind, landmark.name, sx, sy)
            }
        }
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
        return withSlots(ox, oy, px, py, stamp, stampId, chosen.id, name, sx, sy)
    }
}

/** The NPC standing on the slot tile (x, y) of the settlement (spec 09, "Settlement people"). */
fun personAt(seed: ULong, p: WorldParams, s: Settlement, x: Int, y: Int): GenPerson {
    val (index, role) = s.slots.getValue(Pair(x, y))
    val h = hash64(seed, s.sx.toLong(), s.sy.toLong(), 100L + index)
    val region = p.regions[s.region]
    return GenPerson(
        key = "settle:${s.sx}:${s.sy}:$index",
        role = role,
        x256 = x * 256 + 128,
        y256 = y * 256 + 160,
        name = p.peopleStart[(h % p.peopleStart.size.toULong()).toInt()] + p.peopleEnd[((h shr 16) % p.peopleEnd.size.toULong()).toInt()],
        variant = p.variants[((h shr 32) % p.variants.size.toULong()).toInt()],
        tone = region.tone,
        dialogue = p.settlementDialogue.replace("{role}", role).replace("{tone}", region.tone),
        place = s.name,
        region = region.name,
        quirk = p.quirks[(hash64(seed, s.sx.toLong(), s.sy.toLong(), 44) % p.quirks.size.toULong()).toInt()],
        plazaX256 = if (s.spots.isEmpty()) -1 else s.spots[index % s.spots.size].first * 256 + 128,
        plazaY256 = if (s.spots.isEmpty()) -1 else s.spots[index % s.spots.size].second * 256 + 160,
    )
}

/** Where a person is at a time of day (spec 08, "Routines"): [state] is work or plaza. */
class Placement(val state: String, val x256: Int, val y256: Int)

/** The placement of a person at a time of day in permille, or null while the person is away indoors. */
fun personPlacement(p: WorldParams, person: GenPerson, todPm: Int): Placement? {
    var state = "work"
    val frames = p.routines[person.role]
    if (!frames.isNullOrEmpty()) {
        state = frames.first().second
        for ((fromPm, frameState) in frames) if (fromPm <= todPm) state = frameState
    }
    if (state == "away") return null
    if (state == "plaza" && person.plazaX256 >= 0) return Placement("plaza", person.plazaX256, person.plazaY256)
    return Placement("work", person.x256, person.y256)
}

/** Index of the rank of a member with that many guild points. */
fun rankIndex(guild: GuildParams, points: Long): Int {
    var index = 0
    for ((i, rank) in guild.ranks.withIndex()) if (points >= rank.points) index = i
    return index
}

/** The offers on the board of a settlement on a day (spec 07, "Guild"). */
fun offersFor(seed: ULong, p: WorldParams, s: Settlement, day: Long): List<Offer> =
    (0 until p.guild.offersPerDay).map { slot ->
        val h = hash64(hash64(seed, s.sx.toLong(), s.sy.toLong(), 200L + slot), day, slot.toLong())
        val t = p.guild.templates[((h shr 16) % p.guild.templates.size.toULong()).toInt()]
        val span = (t.countMax - t.countMin + 1).toULong()
        val count = t.countMin + ((h shr 32) % span).toInt()
        val tier = (slot + 1).toLong()
        var target = t.target
        if (target == "\$fauna" || target == "\$drop") { // what lives around the town (spec 07, "Guild")
            val entry = pickFauna(p.regions[s.region].fauna, h shr 48)
            target = if (target == "\$fauna") entry.enemy else entry.drop
        }
        Offer(
            id = "board:${s.sx}:${s.sy}:$day:$slot",
            slot = slot,
            minRank = minOf(slot, p.guild.ranks.size - 1),
            template = t.id,
            type = t.type,
            target = target,
            count = count,
            gold = (t.goldBase + count.toLong() * t.goldPer) * tier,
            xp = (t.xpBase + count.toLong() * t.xpPer) * tier,
            points = (t.pointsBase + count.toLong() * t.pointsPer) * tier,
            place = s.name,
            tone = p.regions[s.region].tone,
        )
    }

/** The offer a generated quest id names, or null when the world cannot rebuild it. */
fun resolveOffer(seed: ULong, p: WorldParams, questId: String): Offer? {
    val parts = questId.split(":")
    if (parts.size != 5 || parts[0] != "board") return null
    val sx = parts[1].toIntOrNull() ?: return null
    val sy = parts[2].toIntOrNull() ?: return null
    val day = parts[3].toLongOrNull() ?: return null
    val slot = parts[4].toIntOrNull() ?: return null
    val settlement = settlementSite(seed, p, sx, sy) ?: return null
    return offersFor(seed, p, settlement, day).firstOrNull { it.slot == slot }
}

fun settlementSite(seed: ULong, p: WorldParams, siteX: Int, siteY: Int): Settlement? = Sites(seed, p).site(siteX, siteY)

/** The settlement whose footprint contains the tile, if any (looks at the site cell of the tile and its neighbours). */
fun settlementContaining(seed: ULong, p: WorldParams, x: Int, y: Int): Settlement? {
    for (dy in -1..1) {
        for (dx in -1..1) {
            val sx = (x shr 8) + dx
            val sy = (y shr 8) + dy
            if (sx < 0 || sy < 0) continue
            val s = settlementSite(seed, p, sx, sy) ?: continue
            if (x >= s.x && x < s.x + s.w && y >= s.y && y < s.y + s.h) return s
        }
    }
    return null
}

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
    people: MutableList<GenPerson>,
) {
    val biome = biomeAt(seed, p, x, y)
    val hit = sites.at(x, y)
    if (hit != null) {
        val entry = hit.entry
        tiles[index] = if (entry != null && entry.tile != 0) entry.tile else gidFor(seed, p, biome, x, y, Overlay.NONE)
        if (entry != null && entry.prop.isNotEmpty()) props.add(GenProp(entry.prop, entry.radiusX100, x * 256 + 128, y * 256 + 192))
        if (entry != null && entry.npc.isNotEmpty()) people.add(personAt(seed, p, hit.settlement, x, y))
        if (entry != null && entry.spawner.isNotEmpty()) spawners.add(Pair(x, y))
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

private fun baseGid(seed: ULong, p: WorldParams, biome: Biome, x: Int, y: Int): Int {
    val ground = p.regions[regionAt(p, x, y)].ground[biome.id] // the ground of the region (spec 09, "Regions")
    if (!ground.isNullOrEmpty()) return ground[((hash64(seed, x.toLong(), y.toLong(), 5) shr 40) % ground.size.toULong()).toInt()]
    return when (biome) {
        Biome.WATER -> p.tileWater
        Biome.BEACH -> p.tileBeach
        Biome.MOUNTAIN -> p.tileMountain
        Biome.SNOW -> p.tileSnow
        Biome.DESERT -> p.tileDesert
        Biome.FOREST -> p.tileForest
        Biome.PLAINS -> p.tilesPlains[((hash64(seed, x.toLong(), y.toLong(), 5) shr 40) % p.tilesPlains.size.toULong()).toInt()]
    }
}

private fun propAt(seed: ULong, p: WorldParams, biome: Biome, x: Int, y: Int): GenProp? {
    val options = p.regions[regionAt(p, x, y)].props[biome.id]?.takeIf { it.isNotEmpty() } ?: p.props[biome.id] ?: return null
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
    val people = ArrayList<GenPerson>()
    var index = 0
    val sites = Sites(seed, p)
    for (y in 0 until p.height) {
        for (x in 0 until p.width) emitTile(seed, p, sites, x, y, tiles, index++, props, spawners, people)
    }
    val cx = p.width / 2
    val cy = p.height / 2
    return GeneratedWorld(
        p.width, p.height, tiles, props, spawners, cx * 256 + 128, cy * 256 + 128,
        p.npcs.map { GenNpc(it.key, it.dialogue, it.variant, (cx + it.dx) * 256 + 128, (cy + it.dy) * 256 + 128) },
        people,
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
    /** Settlement NPCs, in scan order. */
    val people: List<GenPerson> = emptyList(),
)

/** Exactly the restriction of [generateWorld] to the window. Any chunk coordinates are valid: tiles outside the world are water. */
fun generateChunk(seed: ULong, p: WorldParams, chunkX: Int, chunkY: Int): GeneratedChunk {
    val tiles = IntArray(CHUNK_SIZE * CHUNK_SIZE)
    val props = ArrayList<GenProp>()
    val spawners = ArrayList<Pair<Int, Int>>()
    val people = ArrayList<GenPerson>()
    var index = 0
    val sites = Sites(seed, p)
    for (y in chunkY * CHUNK_SIZE until (chunkY + 1) * CHUNK_SIZE) {
        for (x in chunkX * CHUNK_SIZE until (chunkX + 1) * CHUNK_SIZE) emitTile(seed, p, sites, x, y, tiles, index++, props, spawners, people)
    }
    return GeneratedChunk(tiles, props, spawners, people)
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
            e["spawner"]?.jsonPrimitive?.content ?: "",
        )
    }
    val spots = (d["spots"] as? JsonArray)?.map { s -> Pair(s.jsonArray[0].jsonPrimitive.int, s.jsonArray[1].jsonPrimitive.int) } ?: emptyList()
    return Stamp(w, h, anchor[0].jsonPrimitive.int, anchor[1].jsonPrimitive.int, rows, legend, spots)
}

/** Reads the world document [worldId] of the pack and resolves the stamps of its settlements from the pack too. */
fun loadWorldParams(pack: Pack, worldId: String): Result<WorldParams> =
    runCatching {
        val j = Json.parseToJsonElement(requireNotNull(pack.readDocument(worldId)) { "missing world $worldId" }).jsonObject
        val defs = HashMap<String, JsonElement>()
        j["home"]?.jsonObject?.getValue("stamp")?.jsonPrimitive?.content?.let { id ->
            defs[id] = Json.parseToJsonElement(requireNotNull(pack.readDocument(id)) { "missing stamp $id" })
        }
        for (landmark in (j["landmarks"] as? JsonArray) ?: JsonArray(emptyList())) {
            val id = landmark.jsonObject.getValue("stamp").jsonPrimitive.content
            defs[id] = Json.parseToJsonElement(requireNotNull(pack.readDocument(id)) { "missing stamp $id" })
        }
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
            spawnerBiomes = s.getValue("biomes").jsonArray.map { it.jsonPrimitive.content },
            spawnerMinDistance = s.getValue("min_distance").jsonPrimitive.int,
            spawnerPer10000 = s.getValue("per_10000").jsonPrimitive.int,
            spawnerRespawnTicks = s.getValue("respawn_ticks").jsonPrimitive.int,
            time = parseTimeParams(j.getValue("time").jsonObject),
            routines = (j["routines"] as? JsonObject)?.getValue("roles")?.jsonObject?.mapValues { (_, frames) ->
                frames.jsonArray.map { f -> Pair(f.jsonArray[0].jsonPrimitive.int, f.jsonArray[1].jsonPrimitive.content) }
            } ?: emptyMap(),
            stoneArt = j.getValue("stones").jsonObject.getValue("art").jsonPrimitive.content,
            stoneRangeX100 = j.getValue("stones").jsonObject.getValue("range_x100").jsonPrimitive.int,
            landmarks = (j["landmarks"] as? JsonArray)?.map {
                val l = it.jsonObject
                Landmark(
                    l.getValue("id").jsonPrimitive.content, l.getValue("name").jsonPrimitive.content, l.getValue("stamp").jsonPrimitive.content,
                    l.getValue("kind").jsonPrimitive.content, l.getValue("dx").jsonPrimitive.int, l.getValue("dy").jsonPrimitive.int,
                )
            } ?: emptyList(),
            guild = j.getValue("guild").jsonObject.let { g ->
                GuildParams(
                    g.getValue("offers_per_day").jsonPrimitive.int,
                    g.getValue("ranks").jsonArray.map { GuildRank(it.jsonObject.getValue("id").jsonPrimitive.content, it.jsonObject.getValue("points").jsonPrimitive.int) },
                    g.getValue("templates").jsonArray.map {
                        val t = it.jsonObject
                        GuildTemplate(
                            t.getValue("id").jsonPrimitive.content, t.getValue("type").jsonPrimitive.content, t.getValue("target").jsonPrimitive.content,
                            t.getValue("count_min").jsonPrimitive.int, t.getValue("count_max").jsonPrimitive.int,
                            t.getValue("gold_base").jsonPrimitive.int, t.getValue("gold_per").jsonPrimitive.int,
                            t.getValue("xp_base").jsonPrimitive.int, t.getValue("xp_per").jsonPrimitive.int,
                            t.getValue("points_base").jsonPrimitive.int, t.getValue("points_per").jsonPrimitive.int,
                        )
                    },
                )
            },
            regionBlend = j["region_blend"]?.jsonPrimitive?.int ?: 0,
            enemyHpPct = j["difficulty"]?.jsonObject?.get("enemy_hp_pct")?.jsonPrimitive?.int ?: 100,
            enemyAtkPct = j["difficulty"]?.jsonObject?.get("enemy_atk_pct")?.jsonPrimitive?.int ?: 100,
            landmarkClearing = j["landmark_clearing"]?.jsonPrimitive?.int ?: 0,
            homeRadius = j["home"]?.jsonObject?.getValue("radius")?.jsonPrimitive?.int ?: 0,
            homeStamp = j["home"]?.jsonObject?.getValue("stamp")?.jsonPrimitive?.content ?: "",
            homeDx = j["home"]?.jsonObject?.getValue("dx")?.jsonPrimitive?.int ?: 0,
            homeDy = j["home"]?.jsonObject?.getValue("dy")?.jsonPrimitive?.int ?: 0,
            regions = j.getValue("regions").jsonArray.map {
                val r = it.jsonObject
                Region(
                    r.getValue("id").jsonPrimitive.content, r.getValue("name").jsonPrimitive.content,
                    r.getValue("x_pm").jsonPrimitive.int, r.getValue("y_pm").jsonPrimitive.int, r.getValue("danger").jsonPrimitive.int,
                    r.getValue("tone").jsonPrimitive.content,
                    r.getValue("shop").jsonObject.getValue("price_pm").jsonPrimitive.int,
                    r.getValue("shop").jsonObject.getValue("stock").jsonArray.map { it.jsonPrimitive.content },
                    r.getValue("fauna").jsonArray.map { f ->
                        val e = f.jsonObject
                        FaunaEntry(e.getValue("enemy").jsonPrimitive.content, e.getValue("drop").jsonPrimitive.content, e.getValue("weight").jsonPrimitive.int)
                    }.also { list -> require(list.isNotEmpty() && list.all { it.weight >= 1 }) { "a region needs fauna with positive weights" } },
                    biasElevation = r["bias"]?.jsonObject?.get("elevation")?.jsonPrimitive?.int ?: 0,
                    biasTemperature = r["bias"]?.jsonObject?.get("temperature")?.jsonPrimitive?.int ?: 0,
                    biasMoisture = r["bias"]?.jsonObject?.get("moisture")?.jsonPrimitive?.int ?: 0,
                    ground = r["ground"]?.jsonObject?.mapValues { (_, gids) -> gids.jsonArray.map { gid -> gid.jsonPrimitive.int } } ?: emptyMap(),
                    props = r["props"]?.jsonObject?.mapValues { (_, options) ->
                        options.jsonArray.map { o ->
                            val option = o.jsonObject
                            PropOption(option.getValue("art").jsonPrimitive.content, option.getValue("radius_x100").jsonPrimitive.int, option.getValue("per_mille").jsonPrimitive.int)
                        }
                    } ?: emptyMap(),
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
            settlementDialogue = j.getValue("settlements").jsonObject.getValue("dialogue").jsonPrimitive.content,
            variants = j.getValue("settlements").jsonObject.getValue("variants").jsonArray.map { it.jsonPrimitive.content },
            quirks = j.getValue("settlements").jsonObject.getValue("quirks").jsonArray.map { it.jsonPrimitive.content },
            peopleStart = j.getValue("settlements").jsonObject.getValue("people").jsonObject.getValue("start").jsonArray.map { it.jsonPrimitive.content },
            peopleEnd = j.getValue("settlements").jsonObject.getValue("people").jsonObject.getValue("end").jsonArray.map { it.jsonPrimitive.content },
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
