package io.github.progliodario.aethermoor.core.sim

import io.github.progliodario.aethermoor.core.TravellerWalk
import io.github.progliodario.aethermoor.core.vector.f
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

// Tile maps (Tiled TMJ subset) and tilesets. Spec: docs/spec/02-entities-and-movement.md.

/**
 * [surface]: what the ground sounds like under the feet (spec 14). [blend]: the rank of a soft ground (spec 13, "Ground
 * blending"); 0: hard edges.
 */
data class TileDef(val art: String, val solid: Boolean, val surface: String = "grass", val blend: Int = 0)

data class Tileset(val id: String, val tiles: Map<Int, TileDef>)

/** A solid circular prop; [x], [y] are the feet position in tiles. */
data class Prop(val art: String, val x: Float, val y: Float, val radius: Float)

/** An enemy spawner: [enemy] is the enemy ID, [x], [y] the feet position in tiles. */
data class SpawnPoint(val enemy: String, val x: Float, val y: Float)

/** An NPC placed on the map: [x], [y] is the feet position in tiles. */
data class NpcPoint(
    val key: String,
    val dialogue: String,
    val variant: String,
    val x: Float,
    val y: Float,
    val whenJson: String = "",
    /** A traveller (spec 07, "Travellers"): its stops in tiles. */
    val route: List<Pair<Float, Float>> = emptyList(),
    /** And how it walks between them (spec 07, "Travellers walk"). */
    val walk: TravellerWalk = TravellerWalk(),
)

class TileMap(
    val width: Int,
    val height: Int,
    val tilesetId: String,
    /** width * height gids, row-major. */
    val ground: IntArray,
    val spawnX: Float,
    val spawnY: Float,
    val props: List<Prop>,
    val spawners: List<SpawnPoint> = emptyList(),
    val npcs: List<NpcPoint> = emptyList(),
) {
    /** The gid at the cell, 0 when out of range. */
    fun gidAt(x: Int, y: Int): Int = if (x < 0 || y < 0 || x >= width || y >= height) 0 else ground[y * width + x]
}

private fun property(obj: JsonObject, name: String): JsonElement? =
    obj["properties"]?.jsonArray?.firstOrNull { (it.jsonObject["name"] as? JsonPrimitive)?.contentOrNull == name }
        ?.jsonObject?.get("value")

fun parseTileset(jsonText: String): Result<Tileset> =
    runCatching {
        val j = Json.parseToJsonElement(jsonText).jsonObject
        val tiles = HashMap<Int, TileDef>()
        for (tile in j.getValue("tiles").jsonArray) {
            val t = tile.jsonObject
            tiles[t.getValue("gid").jsonPrimitive.int] =
                TileDef(
                    t.getValue("art").jsonPrimitive.content,
                    t.getValue("solid").jsonPrimitive.boolean,
                    t["surface"]?.jsonPrimitive?.content ?: "grass",
                    t["blend"]?.jsonPrimitive?.int ?: 0,
                )
        }
        Tileset((j["id"] as? JsonPrimitive)?.contentOrNull ?: "", tiles)
    }

fun parseTileMap(tmjText: String): Result<TileMap> =
    runCatching {
        val j = Json.parseToJsonElement(tmjText).jsonObject
        val width = j.getValue("width").jsonPrimitive.int
        val height = j.getValue("height").jsonPrimitive.int
        val tileSize = j.getValue("tilewidth").f()
        val tilesetId = propertyText(j, "tileset")
        var ground: IntArray? = null
        val objects = MapObjects()
        for (layerElement in j.getValue("layers").jsonArray) {
            val layer = layerElement.jsonObject
            val type = fieldText(layer, "type")
            val name = fieldText(layer, "name")
            if (type == "tilelayer" && name == "ground") {
                val data = layer.getValue("data").jsonArray
                ground = IntArray(data.size) { data[it].jsonPrimitive.int }
            } else if (type == "objectgroup" && name == "objects") {
                for (objectElement in layer.getValue("objects").jsonArray) objects.add(objectElement.jsonObject, tileSize)
            }
        }
        require(width > 0 && height > 0 && ground != null && ground.size == width * height) {
            "ground layer missing or its size does not match width * height"
        }
        require(objects.hasSpawn) { "map has no spawn_player object" }
        TileMap(width, height, tilesetId, ground, objects.spawnX, objects.spawnY, objects.props, objects.spawners, objects.npcs)
    }

/** A text field of a Tiled object or layer: empty when it is not there. */
private fun fieldText(obj: JsonObject, key: String): String = (obj[key] as? JsonPrimitive)?.contentOrNull ?: ""

/** A text of the custom properties of a Tiled object: empty when it is not there. */
private fun propertyText(obj: JsonObject, name: String): String = property(obj, name)?.jsonPrimitive?.content ?: ""

/** What the object layer of a map holds: the start of the player, the props, the spawners and the people. */
private class MapObjects {
    var spawnX = 0f
    var spawnY = 0f
    var hasSpawn = false
    val props = ArrayList<Prop>()
    val spawners = ArrayList<SpawnPoint>()
    val npcs = ArrayList<NpcPoint>()

    fun add(obj: JsonObject, tileSize: Float) {
        val x = obj.getValue("x").f() / tileSize
        val y = obj.getValue("y").f() / tileSize
        when (fieldText(obj, "type")) {
            "spawn_player" -> {
                spawnX = x
                spawnY = y
                hasSpawn = true
            }
            "prop" -> props.add(Prop(art = propertyText(obj, "art"), x = x, y = y, radius = property(obj, "radius")?.f() ?: 0.3f))
            "enemy_spawner" -> spawners.add(SpawnPoint(propertyText(obj, "enemy"), x, y))
            "npc" -> npcs.add(NpcPoint(key = propertyText(obj, "key"), dialogue = propertyText(obj, "dialogue"), variant = propertyText(obj, "variant"), x = x, y = y))
        }
    }
}
