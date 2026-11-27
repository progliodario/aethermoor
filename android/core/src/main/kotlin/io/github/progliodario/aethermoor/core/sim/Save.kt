package io.github.progliodario.aethermoor.core.sim

import io.github.progliodario.aethermoor.core.vector.f
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonObjectBuilder
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
    /** The talents learned (spec 11): talent id -> rank. */
    val talents: Map<String, Int> = emptyMap(),
    /** The sown plots (spec 06, "Farming"), in order. */
    val plots: List<PlotSave> = emptyList(),
    /** What the chests hold (spec 06, "Chests"). */
    val chest: Map<String, Long> = emptyMap(),
    /** The runes engraved on the weapons (spec 06, "Runes"): weapon item -> rune item. */
    val runes: Map<String, String> = emptyMap(),
    /** The rolled affixes of the pieces found (spec 06, "Rolled affixes"): item -> percent. */
    val rolls: Map<String, Long> = emptyMap(),
    /** The furniture of the home (spec 06, "Furniture"), in order of the spots. */
    val furniture: List<FurnitureSave> = emptyList(),
    /** The tag worn (spec 11, "Tags"); empty: none. */
    val tag: String = "",
    /** The companion (spec 10): x, y and cooldown; null: no companion in the save. */
    val companion: Triple<Float, Float, Int>? = null,
    /** The companion was told to stay, and the creatures it has killed (spec 10). */
    val companionStay: Boolean = false,
    val companionBond: Int = 0,
    /** The party (spec 10, "The party"): the companion that follows and the party, when not the ones of the start; the bonds that wait. */
    val companionId: String = "",
    val party: List<String> = emptyList(),
    val bonds: Map<String, Int> = emptyMap(),
    /** The rules of the game (spec 04); 100 everywhere when the save has none. */
    val rules: Rules = Rules(),
    /** The tamed friend (spec 10): its creature, where it is and its cooldown; null: none. */
    val tamedFriend: FriendSave? = null,
    /** The item ids worn (spec 06); null: not in the save (the starting weapon, no armor). */
    val equippedWeapon: String? = null,
    val equippedArmor: String = "",
    /** The accessory worn (spec 06); empty: none, and then not written. */
    val equippedAccessory: String = "",
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
/** [weapon]: the weapon in hand, for the heirloom of a reincarnation (spec 11). */
class SavePeek(val seed: ULong, val map: String, val level: Int = 1, val gold: Long = 0, val weapon: String = "")

/** A sown plot (spec 06, "Farming"): where (hundredths of a tile), the seed and the tick it is ripe. */
class PlotSave(val x: Int, val y: Int, val seed: String, val ripe: Long)

/** A piece of furniture on the spot at (x100, y100). */
class FurnitureSave(val x: Int, val y: Int, val item: String)

/** What a save keeps of the tamed friend (spec 10, "The tamed friend"). */
class FriendSave(val enemy: String, val x: Float, val y: Float, val cooldown: Int, val stay: Boolean = false)

fun savePeek(text: String): Result<SavePeek> =
    runCatching {
        val j = Json.parseToJsonElement(text).jsonObject
        val player = j["player"] as? JsonObject
        val story = j["story"] as? JsonObject
        val equipped = j["equipped"] as? JsonObject
        SavePeek(
            parseHex64(j.getValue("seed")),
            (j["map"] as? JsonPrimitive)?.content ?: "",
            (player?.get("level") as? JsonPrimitive)?.int ?: 1,
            (story?.get("gold") as? JsonPrimitive)?.long ?: 0L,
            (equipped?.get("weapon") as? JsonPrimitive)?.takeIf { it.isString }?.content ?: "",
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
        put("player", playerJson(s))
        put("rng", rngJson(s))
        put("enemies", enemiesJson(s))
        if (meta.map == "world") put("cleared_spawners", clearedJson(s))
        put("world_ticks", s.worldTicks)
        put("equipped", equippedJson(s))
        putStores(s, this)
        putTallies(s, this)
        putFriendAndCompanion(s, this)
        if (meta.map == "world") putExplored(s, this)
        put("inventory", buildJsonObject { for ((item, quantity) in s.inventory) put(item, quantity) })
        put("story", storyJson(s))
    }
    return root.toString() + "\n"
}

/** The player of the save (spec 12). */
private fun playerJson(s: SaveState): JsonObject =
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
    }

/** The two random generators the save carries. */
private fun rngJson(s: SaveState): JsonObject =
    buildJsonObject {
        put(
            "combat",
            buildJsonObject {
                put("state", hex64(s.combatState))
                put("inc", hex64(s.combatInc))
            },
        )
        put(
            "loot",
            buildJsonObject {
                put("state", hex64(s.lootState))
                put("inc", hex64(s.lootInc))
            },
        )
    }

private fun enemiesJson(s: SaveState): JsonArray =
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
    )

private fun clearedJson(s: SaveState): JsonArray =
    JsonArray(s.cleared.map { JsonArray(listOf(JsonPrimitive(it.x), JsonPrimitive(it.y), JsonPrimitive(it.died))) })

private fun equippedJson(s: SaveState): JsonObject =
    buildJsonObject {
        put("weapon", s.equippedWeapon ?: "")
        put("armor", s.equippedArmor)
        if (s.equippedAccessory.isNotEmpty()) put("accessory", s.equippedAccessory)
    }

/** What only some saves have: a chest, the plots, the rolls, the runes, the home, the talents, the counters, the bestiary. */
private fun putStores(s: SaveState, root: JsonObjectBuilder) {
    if (s.chest.isNotEmpty()) root.put("chest", buildJsonObject { for ((item, qty) in s.chest.toSortedMap()) put(item, qty) })
    if (s.plots.isNotEmpty()) {
        root.put(
            "plots",
            JsonArray(s.plots.map { p -> JsonArray(listOf(JsonPrimitive(p.x), JsonPrimitive(p.y), JsonPrimitive(p.seed), JsonPrimitive(p.ripe))) }),
        )
    }
    if (s.rolls.isNotEmpty()) root.put("rolls", buildJsonObject { for ((item, pct) in s.rolls.toSortedMap()) put(item, pct) })
    if (s.runes.isNotEmpty()) root.put("runes", buildJsonObject { for ((weapon, rune) in s.runes.toSortedMap()) put(weapon, rune) })
    if (s.tag.isNotEmpty()) root.put("tag", s.tag)
    if (s.furniture.isNotEmpty()) {
        root.put(
            "furniture",
            JsonArray(s.furniture.map { f -> JsonArray(listOf(JsonPrimitive(f.x), JsonPrimitive(f.y), JsonPrimitive(f.item))) }),
        )
    }
}

/** The tallies of a save: the talents, the counters of the world and the bestiary. */
private fun putTallies(s: SaveState, root: JsonObjectBuilder) {
    if (s.talents.isNotEmpty()) root.put("talents", buildJsonObject { for ((id, rank) in s.talents) put(id, rank) })
    if (s.counters.isNotEmpty()) root.put("counters", buildJsonObject { for ((name, count) in s.counters) put(name, count) })
    if (s.bestiary.isNotEmpty()) root.put("bestiary", buildJsonObject { for ((id, count) in s.bestiary) put(id, count) })
}

/** The tamed friend, the companion, the party, the bonds and the rules of the game (spec 10, spec 04). */
private fun putFriendAndCompanion(s: SaveState, root: JsonObjectBuilder) {
    s.tamedFriend?.let { f ->
        root.put(
            "friend",
            buildJsonObject {
                put("enemy", f.enemy)
                put("x", f.x)
                put("y", f.y)
                put("cooldown", f.cooldown)
                if (f.stay) put("stay", true)
            },
        )
    }
    s.companion?.let { c ->
        root.put(
            "companion",
            buildJsonObject {
                put("x", c.first)
                put("y", c.second)
                put("cooldown", c.third)
                if (s.companionStay) put("stay", true)
                if (s.companionBond > 0) put("bond", s.companionBond)
                if (s.companionId.isNotEmpty()) put("id", s.companionId)
            },
        )
    }
    if (s.party.isNotEmpty()) root.put("party", JsonArray(s.party.map { JsonPrimitive(it) })) // spec 10, "The party"
    if (s.bonds.isNotEmpty()) root.put("bonds", JsonObject(s.bonds.mapValues { JsonPrimitive(it.value) }))
    if (!s.rules.isDefault) root.put("rules", rulesJson(s.rules)) // the rules of the game (spec 04): only those that are not 100
}

/** What a streamed world has: the explored tiles and the stones of the world map. */
private fun putExplored(s: SaveState, root: JsonObjectBuilder) {
    root.put("explored", JsonArray(s.explored.map { JsonArray(listOf(JsonPrimitive(it.first), JsonPrimitive(it.second))) }))
    root.put("stones", JsonArray(s.stones.map { JsonArray(listOf(JsonPrimitive(it.first), JsonPrimitive(it.second))) }))
}

/** The story of the save: flags, gold, guild points, quests, and the dialogue open, if any. */
private fun storyJson(s: SaveState): JsonObject =
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
                            if (q.day > 0L) put("day", q.day) // a timed quest (spec 07, "Timed quests")
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
    }

/** The story of a save; empty when the document has none. */
private fun storyOf(element: JsonElement): StoryState {
    if (element is JsonNull) return StoryState(emptyMap(), 0, emptyMap(), false, "", "")
    val st = element.jsonObject
    val dialogue = st.getValue("dialogue")
    return StoryState(
        flags = st.getValue("flags").jsonObject.mapValues { it.value.jsonPrimitive.boolean },
        gold = st.getValue("gold").jsonPrimitive.long,
        guildPoints = st["guild_points"]?.jsonPrimitive?.long ?: 0L,
        quests = st.getValue("quests").jsonObject.mapValues { (_, value) -> questProgressOf(value) },
        dialogueActive = dialogue !is JsonNull,
        dialogueId = if (dialogue is JsonNull) "" else dialogue.jsonObject.getValue("id").jsonPrimitive.content,
        node = if (dialogue is JsonNull) "" else dialogue.jsonObject.getValue("node").jsonPrimitive.content,
        dialogueArgs = if (dialogue is JsonNull) emptyMap() else (dialogue.jsonObject["args"] as? JsonObject)?.mapValues { it.value.jsonPrimitive.content } ?: emptyMap(),
    )
}

private fun questProgressOf(value: JsonElement): QuestProgress {
    val q = value.jsonObject
    val progress = q.getValue("progress").jsonArray
    return QuestProgress(
        q.getValue("stage").jsonPrimitive.content,
        LongArray(progress.size) { progress[it].jsonPrimitive.long },
        q.getValue("done").jsonPrimitive.boolean,
        q["day"]?.jsonPrimitive?.long ?: 0L,
    )
}

private fun enemiesOf(array: JsonArray): List<SaveEnemy> =
    array.map {
        val e = it.jsonObject
        SaveEnemy(
            e.getValue("x").f(),
            e.getValue("y").f(),
            e.getValue("hp").jsonPrimitive.long,
            parseEnemyState(e.getValue("state").jsonPrimitive.content),
            e.getValue("state_tick").jsonPrimitive.int,
            e["spawner"]?.jsonArray?.let { sp -> Pair(sp[0].jsonPrimitive.int, sp[1].jsonPrimitive.int) },
        )
    }

/** The spawners whose enemy was killed, with the tick of the death. */
private fun clearedOf(j: JsonObject): List<ClearedSpawner> =
    (j["cleared_spawners"] as? JsonArray)?.map { c ->
        val a = c.jsonArray
        ClearedSpawner(a[0].jsonPrimitive.int, a[1].jsonPrimitive.int, if (a.size > 2) a[2].jsonPrimitive.long else 0L)
    } ?: emptyList()

private fun plotsOf(j: JsonObject): List<PlotSave> =
    j.optArr("plots")?.map { p ->
        val a = p.jsonArray
        PlotSave(a[0].jsonPrimitive.int, a[1].jsonPrimitive.int, a[2].jsonPrimitive.content, a[3].jsonPrimitive.long)
    } ?: emptyList()

private fun furnitureSavesOf(j: JsonObject): List<FurnitureSave> =
    j.optArr("furniture")?.map { f ->
        val a = f.jsonArray
        FurnitureSave(a[0].jsonPrimitive.int, a[1].jsonPrimitive.int, a[2].jsonPrimitive.content)
    } ?: emptyList()

private fun partyOf(j: JsonObject): List<String> = j.optArr("party")?.map { it.jsonPrimitive.content } ?: emptyList()

private fun friendOf(j: JsonObject): FriendSave? =
    j.optObj("friend")?.let { f ->
        FriendSave(
            f.getValue("enemy").jsonPrimitive.content,
            f.getValue("x").jsonPrimitive.float,
            f.getValue("y").jsonPrimitive.float,
            f.getValue("cooldown").jsonPrimitive.int,
            f.optFlag("stay"),
        )
    }

// The fields a save may not have: the value of a save of an older version, and the default of this one.
private fun JsonObject?.optObj(key: String): JsonObject? = this?.get(key) as? JsonObject

private fun JsonObject?.optArr(key: String): JsonArray? = this?.get(key) as? JsonArray

private fun JsonObject?.optStr(key: String): String = (this?.get(key) as? JsonPrimitive)?.content ?: ""

private fun JsonObject?.optFlag(key: String): Boolean = optStr(key) == "true"

private fun JsonObject?.optInt(key: String): Int = (this?.get(key) as? JsonPrimitive)?.content?.toIntOrNull() ?: 0

private fun JsonArray?.optPairs(): List<Pair<Int, Int>> =
    this?.map { Pair(it.jsonArray[0].jsonPrimitive.int, it.jsonArray[1].jsonPrimitive.int) } ?: emptyList()

private fun JsonObject?.optIntMap(): Map<String, Int> = this?.mapValues { it.value.jsonPrimitive.int } ?: emptyMap()

private fun JsonObject?.optLongMap(): Map<String, Long> = this?.mapValues { it.value.jsonPrimitive.long } ?: emptyMap()

private fun JsonObject?.optStrMap(): Map<String, String> = this?.mapValues { it.value.jsonPrimitive.content } ?: emptyMap()

/** Parses a save document; the failure carries the reason (invalid JSON, missing field, newer save_version). */
fun saveFromJson(text: String): Result<SaveState> =
    runCatching {
        val j = Json.parseToJsonElement(text).jsonObject
        require(j.getValue("save_version").jsonPrimitive.int <= SAVE_VERSION) { "this save was written by a newer version of the game" }
        val p = j.getValue("player").jsonObject
        val rng = j.getValue("rng").jsonObject
        val combat = rng.getValue("combat").jsonObject
        val loot = rng.getValue("loot").jsonObject
        val equipped = j.optObj("equipped")
        val companion = j.optObj("companion")
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
            enemies = enemiesOf(j.getValue("enemies").jsonArray),
            cleared = clearedOf(j),
            worldTicks = j["world_ticks"]?.jsonPrimitive?.long ?: -1L,
            equippedWeapon = equipped.optStr("weapon"),
            equippedArmor = equipped.optStr("armor"),
            equippedAccessory = equipped.optStr("accessory"),
            explored = j.optArr("explored").optPairs(),
            companion = companion?.let { Triple(it.getValue("x").jsonPrimitive.float, it.getValue("y").jsonPrimitive.float, it.getValue("cooldown").jsonPrimitive.int) },
            talents = j.optObj("talents").optIntMap(),
            chest = j.optObj("chest").optLongMap(),
            plots = plotsOf(j),
            tag = j.optStr("tag"),
            runes = j.optObj("runes").optStrMap(),
            rolls = j.optObj("rolls").optLongMap(),
            furniture = furnitureSavesOf(j),
            counters = j.optObj("counters").optIntMap(),
            companionStay = companion.optFlag("stay"),
            companionBond = companion.optInt("bond"),
            companionId = companion.optStr("id"),
            party = partyOf(j),
            bonds = j.optObj("bonds").optIntMap(),
            rules = parseRules(j.optObj("rules")),
            tamedFriend = friendOf(j),
            bestiary = j.optObj("bestiary").optIntMap(),
            stones = j.optArr("stones").optPairs(),
            inventory = j.getValue("inventory").jsonObject.mapValues { it.value.jsonPrimitive.long },
            story = storyOf(j.getValue("story")),
        )
    }

/** The rules of the game of a save or a scenario (spec 04): 100 for what is not given, every value kept within the bounds. */
fun parseRules(j: JsonObject?): Rules =
    if (j == null) Rules() else Rules(Rule.entries.map { (j[it.key] as? JsonPrimitive)?.content?.toIntOrNull() ?: 100 }).clamped()

/** The rules of the game as the save writes them: only those that are not 100. */
fun rulesJson(r: Rules): JsonObject = JsonObject(Rule.entries.filter { r[it] != 100 }.associate { it.key to JsonPrimitive(r[it]) })
