package io.github.progliodario.aethermoor.core.sim

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

data class TileDef(val art: String, val solid: Boolean)

data class Tileset(val id: String, val tiles: Map<Int, TileDef>)

/** A solid circular prop; [x], [y] are the feet position in tiles. */
data class Prop(val art: String, val x: Float, val y: Float, val radius: Float)

/** An enemy spawner: [enemy] is the enemy ID, [x], [y] the feet position in tiles. */
data class SpawnPoint(val enemy: String, val x: Float, val y: Float)

/** An NPC placed on the map: [x], [y] is the feet position in tiles. */
data class NpcPoint(val key: String, val dialogue: String, val variant: String, val x: Float, val y: Float)

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
                TileDef(t.getValue("art").jsonPrimitive.content, t.getValue("solid").jsonPrimitive.boolean)
        }
        Tileset((j["id"] as? JsonPrimitive)?.contentOrNull ?: "", tiles)
    }

fun parseTileMap(tmjText: String): Result<TileMap> =
    runCatching {
        val j = Json.parseToJsonElement(tmjText).jsonObject
        val width = j.getValue("width").jsonPrimitive.int
        val height = j.getValue("height").jsonPrimitive.int
        val tileSize = j.getValue("tilewidth").f()
        val tilesetId = property(j, "tileset")?.jsonPrimitive?.content ?: ""
        var ground: IntArray? = null
        var spawnX = 0f
        var spawnY = 0f
        var hasSpawn = false
        val props = ArrayList<Prop>()
        val spawners = ArrayList<SpawnPoint>()
        val npcs = ArrayList<NpcPoint>()
        for (layerElement in j.getValue("layers").jsonArray) {
            val layer = layerElement.jsonObject
            val type = (layer["type"] as? JsonPrimitive)?.contentOrNull ?: ""
            val name = (layer["name"] as? JsonPrimitive)?.contentOrNull ?: ""
            if (type == "tilelayer" && name == "ground") {
                val data = layer.getValue("data").jsonArray
                ground = IntArray(data.size) { data[it].jsonPrimitive.int }
            } else if (type == "objectgroup" && name == "objects") {
                for (objectElement in layer.getValue("objects").jsonArray) {
                    val obj = objectElement.jsonObject
                    val kind = (obj["type"] as? JsonPrimitive)?.contentOrNull ?: ""
                    val x = obj.getValue("x").f() / tileSize
                    val y = obj.getValue("y").f() / tileSize
                    if (kind == "spawn_player") {
                        spawnX = x
                        spawnY = y
                        hasSpawn = true
                    } else if (kind == "prop") {
                        props.add(
                            Prop(
                                art = property(obj, "art")?.jsonPrimitive?.content ?: "",
                                x = x,
                                y = y,
                                radius = property(obj, "radius")?.f() ?: 0.3f,
                            ),
                        )
                    } else if (kind == "enemy_spawner") {
                        spawners.add(SpawnPoint(property(obj, "enemy")?.jsonPrimitive?.content ?: "", x, y))
                    } else if (kind == "npc") {
                        npcs.add(
                            NpcPoint(
                                key = property(obj, "key")?.jsonPrimitive?.content ?: "",
                                dialogue = property(obj, "dialogue")?.jsonPrimitive?.content ?: "",
                                variant = property(obj, "variant")?.jsonPrimitive?.content ?: "",
                                x = x,
                                y = y,
                            ),
                        )
                    }
                }
            }
        }
        require(width > 0 && height > 0 && ground != null && ground.size == width * height) {
            "ground layer missing or its size does not match width * height"
        }
        require(hasSpawn) { "map has no spawn_player object" }
        TileMap(width, height, tilesetId, ground, spawnX, spawnY, props, spawners, npcs)
    }
