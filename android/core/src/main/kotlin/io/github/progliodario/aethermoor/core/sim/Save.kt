package io.github.progliodario.aethermoor.core.sim

import io.github.progliodario.aethermoor.core.vector.f
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.float
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.long
import kotlinx.serialization.json.put

// Save files. Spec: docs/spec/12-save-format.md. Schema: schemas/save.schema.json.
// Keep this file in step with desktop/src/sim/save.cpp.

const val SAVE_VERSION = 1

/** A spawner whose enemy was killed, with the world tick of the death. */
class ClearedSpawner(val x: Int, val y: Int, val died: Long)

class SaveEnemy(
    val x: Float,
    val y: Float,
    val hp: Long,
    val state: EnemyState,
    val stateTick: Int,
    /** Streamed worlds only: the spawner tile of the enemy. */
    val spawner: Pair<Int, Int>? = null,
)

/** Everything that changes while playing. */
data class SaveState(
    val x: Float,
    val y: Float,
    val facingX: Float,
    val facingY: Float,
    val facingLeft: Boolean,
    val moving: Boolean,
    val clipTick: Int,
    val hp: Long,
    val level: Long,
    val xp: Long,
    val deaths: Int,
    val kills: Int,
    val iframes: Int,
    val cooldown: Int,
    val phase: AttackPhase,
    val phaseTick: Int,
    val hitSet: List<Boolean>,
    val combatState: ULong,
    val combatInc: ULong,
    val lootState: ULong,
    val lootInc: ULong,
    val enemies: List<SaveEnemy>,
    /** Streamed worlds only: the spawners whose enemy was killed. */
    val cleared: List<ClearedSpawner> = emptyList(),
    /** -1: not in the save (a new game starts at the world's start tick). */
    val worldTicks: Long = -1,
    /** Streamed worlds only: explored world map cells. */
    val explored: List<Pair<Int, Int>> = emptyList(),
    /** Streamed worlds only: tiles of the Threshold Stones that were used, in order. */
    val stones: List<Pair<Int, Int>> = emptyList(),
    /** The bestiary (spec 11): creature id -> kills. */
    val bestiary: Map<String, Int> = emptyMap(),
    /** The counters of spec 11: gathered, crafted, parried. */
    val counters: Map<String, Int> = emptyMap(),
    /** The companion (spec 10): x, y and cooldown; null: no companion in the save. */
    val companion: Triple<Float, Float, Int>? = null,
    /** The item ids worn (spec 06); null: not in the save (the starting weapon, no armor). */
    val equippedWeapon: String? = null,
    val equippedArmor: String = "",
    val inventory: Map<String, Long>,
    val story: StoryState,
)

class SaveMeta(
    val gameVersion: String,
    val dataFormatVersion: Int,
    val protagonist: String,
    val seed: ULong,
    /** "world" (generated from the seed) or "demo" (the hand-made map). */
    val map: String = "",
)

/** The seed and map name of a save, read without building a world (to rebuild the same world first). */
class SavePeek(val seed: ULong, val map: String, val level: Int = 1, val gold: Long = 0)

fun savePeek(text: String): Result<SavePeek> =
    runCatching {
        val j = Json.parseToJsonElement(text).jsonObject
        val player = j["player"] as? JsonObject
        val story = j["story"] as? JsonObject
        SavePeek(
            parseHex64(j.getValue("seed")), (j["map"] as? JsonPrimitive)?.content ?: "",
            (player?.get("level") as? JsonPrimitive)?.int ?: 1, (story?.get("gold") as? JsonPrimitive)?.long ?: 0L,
        )
    }

private fun hex64(value: ULong) = "0x" + value.toString(16).padStart(16, '0')

private fun parseHex64(element: JsonElement): ULong = element.jsonPrimitive.content.removePrefix("0x").toULong(16)

private fun phaseName(phase: AttackPhase) = phase.name.lowercase()

private fun parsePhase(name: String): AttackPhase = AttackPhase.valueOf(name.uppercase())

private fun parseEnemyState(name: String): EnemyState =
    EnemyState.values().firstOrNull { it.id == name } ?: throw IllegalArgumentException("unknown enemy state $name")

fun saveToJson(s: SaveState, meta: SaveMeta): String {
    val root = buildJsonObject {
        put("save_version", SAVE_VERSION)
        put("game_version", meta.gameVersion)
        put("data_format_version", meta.dataFormatVersion)
        put("protagonist", meta.protagonist)
        put("seed", hex64(meta.seed))
        put("map", meta.map)
        put(
            "player",
            buildJsonObject {
                put("x", s.x)
                put("y", s.y)
                put("facing", JsonArray(listOf(JsonPrimitive(s.facingX), JsonPrimitive(s.facingY))))
                put("facing_left", s.facingLeft)
                put("moving", s.moving)
                put("clip_tick", s.clipTick)
                put("hp", s.hp)
                put("level", s.level)
                put("xp", s.xp)
                put("deaths", s.deaths)
                put("kills", s.kills)
                put("iframes", s.iframes)
                put("cooldown", s.cooldown)
                put("phase", phaseName(s.phase))
                put("phase_tick", s.phaseTick)
                put("hit_set", JsonArray(s.hitSet.map { JsonPrimitive(it) }))
            },
        )
        put(
            "rng",
            buildJsonObject {
                put("combat", buildJsonObject { put("state", hex64(s.combatState)); put("inc", hex64(s.combatInc)) })
                put("loot", buildJsonObject { put("state", hex64(s.lootState)); put("inc", hex64(s.lootInc)) })
            },
        )
        put(
            "enemies",
            JsonArray(
                s.enemies.map {
                    buildJsonObject {
                        put("x", it.x)
                        put("y", it.y)
                        put("hp", it.hp)
                        put("state", it.state.id)
                        put("state_tick", it.stateTick)
                        it.spawner?.let { spawner -> put("spawner", JsonArray(listOf(JsonPrimitive(spawner.first), JsonPrimitive(spawner.second)))) }
                    }
                },
            ),
        )
        if (meta.map == "world") {
            put(
                "cleared_spawners",
                JsonArray(s.cleared.map { JsonArray(listOf(JsonPrimitive(it.x), JsonPrimitive(it.y), JsonPrimitive(it.died))) }),
            )
        }
        put("world_ticks", s.worldTicks)
        put("equipped", buildJsonObject { put("weapon", s.equippedWeapon ?: ""); put("armor", s.equippedArmor) })
        if (s.counters.isNotEmpty()) put("counters", buildJsonObject { for ((name, count) in s.counters) put(name, count) })
        if (s.bestiary.isNotEmpty()) put("bestiary", buildJsonObject { for ((id, count) in s.bestiary) put(id, count) })
        s.companion?.let { c -> put("companion", buildJsonObject { put("x", c.first); put("y", c.second); put("cooldown", c.third) }) }
        if (meta.map == "world") {
            put("explored", JsonArray(s.explored.map { JsonArray(listOf(JsonPrimitive(it.first), JsonPrimitive(it.second))) }))
            put("stones", JsonArray(s.stones.map { JsonArray(listOf(JsonPrimitive(it.first), JsonPrimitive(it.second))) }))
        }
        put("inventory", buildJsonObject { for ((item, quantity) in s.inventory) put(item, quantity) })
        put(
            "story",
            buildJsonObject {
                put("flags", buildJsonObject { for ((flag, value) in s.story.flags) put(flag, value) })
                put("gold", s.story.gold)
                put("guild_points", s.story.guildPoints)
                put(
                    "quests",
                    buildJsonObject {
                        for ((id, q) in s.story.quests) {
                            put(
                                id,
                                buildJsonObject {
                                    put("stage", q.stage)
                                    put("progress", JsonArray(q.progress.map { JsonPrimitive(it) }))
                                    put("done", q.done)
                                },
                            )
                        }
                    },
                )
                if (s.story.dialogueActive) {
                    put(
                        "dialogue",
                        buildJsonObject {
                            put("id", s.story.dialogueId)
                            put("node", s.story.node)
                            if (s.story.dialogueArgs.isNotEmpty()) put("args", buildJsonObject { for ((k, v) in s.story.dialogueArgs) put(k, v) })
                        },
                    )
                } else {
                    put("dialogue", JsonNull)
                }
            },
        )
    }
    return root.toString() + "\n"
}

/** Parses a save document; the failure carries the reason (invalid JSON, missing field, newer save_version). */
fun saveFromJson(text: String): Result<SaveState> =
    runCatching {
        val j = Json.parseToJsonElement(text).jsonObject
        require(j.getValue("save_version").jsonPrimitive.int <= SAVE_VERSION) { "this save was written by a newer version of the game" }
        val p = j.getValue("player").jsonObject
        val rng = j.getValue("rng").jsonObject
        val combat = rng.getValue("combat").jsonObject
        val loot = rng.getValue("loot").jsonObject
        val storyElement = j.getValue("story")
        val story =
            if (storyElement is JsonNull) {
                StoryState(emptyMap(), 0, emptyMap(), false, "", "")
            } else {
                val st = storyElement.jsonObject
                val dialogue = st.getValue("dialogue")
                StoryState(
                    flags = st.getValue("flags").jsonObject.mapValues { it.value.jsonPrimitive.boolean },
                    gold = st.getValue("gold").jsonPrimitive.long,
                    guildPoints = st["guild_points"]?.jsonPrimitive?.long ?: 0L,
                    quests = st.getValue("quests").jsonObject.mapValues { (_, value) ->
                        val q = value.jsonObject
                        QuestProgress(
                            q.getValue("stage").jsonPrimitive.content,
                            LongArray(q.getValue("progress").jsonArray.size) { q.getValue("progress").jsonArray[it].jsonPrimitive.long },
                            q.getValue("done").jsonPrimitive.boolean,
                        )
                    },
                    dialogueActive = dialogue !is JsonNull,
                    dialogueId = if (dialogue is JsonNull) "" else dialogue.jsonObject.getValue("id").jsonPrimitive.content,
                    node = if (dialogue is JsonNull) "" else dialogue.jsonObject.getValue("node").jsonPrimitive.content,
                    dialogueArgs = if (dialogue is JsonNull) emptyMap() else (dialogue.jsonObject["args"] as? JsonObject)?.mapValues { it.value.jsonPrimitive.content } ?: emptyMap(),
                )
            }
        SaveState(
            x = p.getValue("x").f(),
            y = p.getValue("y").f(),
            facingX = p.getValue("facing").jsonArray[0].f(),
            facingY = p.getValue("facing").jsonArray[1].f(),
            facingLeft = p.getValue("facing_left").jsonPrimitive.boolean,
            moving = p.getValue("moving").jsonPrimitive.boolean,
            clipTick = p.getValue("clip_tick").jsonPrimitive.int,
            hp = p.getValue("hp").jsonPrimitive.long,
            level = p.getValue("level").jsonPrimitive.long,
            xp = p.getValue("xp").jsonPrimitive.long,
            deaths = p.getValue("deaths").jsonPrimitive.int,
            kills = p.getValue("kills").jsonPrimitive.int,
            iframes = p.getValue("iframes").jsonPrimitive.int,
            cooldown = p.getValue("cooldown").jsonPrimitive.int,
            phase = parsePhase(p.getValue("phase").jsonPrimitive.content),
            phaseTick = p.getValue("phase_tick").jsonPrimitive.int,
            hitSet = p.getValue("hit_set").jsonArray.map { it.jsonPrimitive.boolean },
            combatState = parseHex64(combat.getValue("state")),
            combatInc = parseHex64(combat.getValue("inc")),
            lootState = parseHex64(loot.getValue("state")),
            lootInc = parseHex64(loot.getValue("inc")),
            enemies = j.getValue("enemies").jsonArray.map {
                val e = it.jsonObject
                SaveEnemy(
                    e.getValue("x").f(), e.getValue("y").f(), e.getValue("hp").jsonPrimitive.long,
                    parseEnemyState(e.getValue("state").jsonPrimitive.content), e.getValue("state_tick").jsonPrimitive.int,
                    e["spawner"]?.jsonArray?.let { sp -> Pair(sp[0].jsonPrimitive.int, sp[1].jsonPrimitive.int) },
                )
            },
            cleared = (j["cleared_spawners"] as? JsonArray)?.map { c ->
                val a = c.jsonArray
                ClearedSpawner(a[0].jsonPrimitive.int, a[1].jsonPrimitive.int, if (a.size > 2) a[2].jsonPrimitive.long else 0L)
            } ?: emptyList(),
            worldTicks = j["world_ticks"]?.jsonPrimitive?.long ?: -1L,
            equippedWeapon = (j["equipped"] as? JsonObject)?.let { (it["weapon"] as? JsonPrimitive)?.content ?: "" },
            equippedArmor = (j["equipped"] as? JsonObject)?.let { (it["armor"] as? JsonPrimitive)?.content } ?: "",
            explored = (j["explored"] as? JsonArray)?.map { c -> Pair(c.jsonArray[0].jsonPrimitive.int, c.jsonArray[1].jsonPrimitive.int) }
                ?: emptyList(),
            companion = (j["companion"] as? JsonObject)?.let { c -> Triple(c.getValue("x").jsonPrimitive.float, c.getValue("y").jsonPrimitive.float, c.getValue("cooldown").jsonPrimitive.int) },
            counters = (j["counters"] as? JsonObject)?.mapValues { it.value.jsonPrimitive.int } ?: emptyMap(),
            bestiary = (j["bestiary"] as? JsonObject)?.mapValues { it.value.jsonPrimitive.int } ?: emptyMap(),
            stones = (j["stones"] as? JsonArray)?.map { c -> Pair(c.jsonArray[0].jsonPrimitive.int, c.jsonArray[1].jsonPrimitive.int) }
                ?: emptyList(),
            inventory = j.getValue("inventory").jsonObject.mapValues { it.value.jsonPrimitive.long },
            story = story,
        )
    }
