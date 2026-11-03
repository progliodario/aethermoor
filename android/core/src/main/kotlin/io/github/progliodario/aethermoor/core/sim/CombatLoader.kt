package io.github.progliodario.aethermoor.core.sim

import io.github.progliodario.aethermoor.core.Pack
import io.github.progliodario.aethermoor.core.parseProtagonist
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.long

// Builds the combat setup of a protagonist on a map from the content pack (spec 05, "Data used").

private fun document(pack: Pack, id: String): JsonObject {
    val text = requireNotNull(pack.readDocument(id)) { "missing document $id" }
    return Json.parseToJsonElement(text).jsonObject
}

/** One enemy document with its behavior (used by streamed worlds, which have no spawner list). */
fun loadEnemyDef(pack: Pack, id: String): Result<EnemyDef> = runCatching { loadEnemy(pack, id) }

private fun loadEnemy(pack: Pack, id: String): EnemyDef {
    val enemy = document(pack, id)
    val stats = enemy.getValue("stats").jsonObject
    val behavior = document(pack, enemy.getValue("behavior").jsonPrimitive.content)
    return EnemyDef(
        id = id,
        art = enemy.getValue("art").jsonPrimitive.content,
        level = enemy.getValue("level").jsonPrimitive.long,
        hp = stats.getValue("hp").jsonPrimitive.long,
        atk = stats.getValue("atk").jsonPrimitive.long,
        def = stats.getValue("def").jsonPrimitive.long,
        xp = enemy.getValue("xp").jsonPrimitive.long,
        radiusX100 = enemy.getValue("radius_x100").jsonPrimitive.int,
        speedX100 = stats.getValue("speed_x100").jsonPrimitive.int,
        drops = enemy["drops"]?.jsonArray?.map {
            val d = it.jsonObject
            DropDef(
                d.getValue("item").jsonPrimitive.content,
                d.getValue("qty_min").jsonPrimitive.long,
                d.getValue("qty_max").jsonPrimitive.long,
                d.getValue("weight_pm").jsonPrimitive.long,
            )
        } ?: emptyList(),
        behavior = BehaviorDef(
            aggroX100 = behavior.getValue("aggro_x100").jsonPrimitive.int,
            leashX100 = behavior.getValue("leash_x100").jsonPrimitive.int,
            attackRangeX100 = behavior.getValue("attack_range_x100").jsonPrimitive.int,
            hitRangeX100 = behavior.getValue("hit_range_x100").jsonPrimitive.int,
            windupTicks = behavior.getValue("windup_ticks").jsonPrimitive.int,
            recoveryTicks = behavior.getValue("recovery_ticks").jsonPrimitive.int,
        ),
    )
}

/**
 * Reads the protagonist, its first weapon and first skill with a hitbox, the enemies named by the map spawners
 * (with their behaviors) and the XP table.
 */
fun loadCombatSetup(
    pack: Pack,
    map: TileMap,
    protagonistId: String,
    seed: ULong,
    /** The enemies of the fauna of a streamed world, if the map is one. */
    streamEnemyIds: Collection<String> = emptyList(),
    /** The difficulty of the world (spec 04): health and attack of the streamed creatures, in percent. */
    enemyHpPct: Int = 100,
    enemyAtkPct: Int = 100,
): Result<CombatSetup> =
    runCatching {
        val protagonist = parseProtagonist(requireNotNull(pack.readDocument(protagonistId)) { "missing $protagonistId" }).getOrThrow()

        var weaponAtk = 0L
        var weaponMatk = 0L
        var startWeapon = ""
        for (itemId in protagonist.startingItems) {
            val item = document(pack, itemId)
            if (item.getValue("kind").jsonPrimitive.content == "weapon") {
                val weapon = item.getValue("weapon").jsonObject
                weaponAtk = weapon.getValue("atk").jsonPrimitive.long
                weaponMatk = weapon.getValue("matk").jsonPrimitive.long
                startWeapon = itemId
                break
            }
        }

        var skill: SkillDef? = null
        for (skillId in protagonist.startingSkills) {
            val s = document(pack, skillId)
            val hitbox = s["hitbox"]?.jsonObject ?: continue
            val timing = s.getValue("timing").jsonObject
            skill = SkillDef(
                startup = timing.getValue("startup").jsonPrimitive.int,
                active = timing.getValue("active").jsonPrimitive.int,
                recovery = timing.getValue("recovery").jsonPrimitive.int,
                cooldown = s.getValue("cooldown_ticks").jsonPrimitive.int,
                powerPct = s.getValue("damage").jsonObject.getValue("power_pct").jsonPrimitive.long,
                radiusX100 = hitbox.getValue("radius_x100").jsonPrimitive.int,
                angleDeg = hitbox.getValue("angle_deg").jsonPrimitive.int,
            )
            break
        }
        requireNotNull(skill) { "the protagonist has no skill with a hitbox" }

        val enemies = HashMap<String, EnemyDef>()
        val spawns = map.spawners.map { spawn ->
            EnemySpawn(enemies.getOrPut(spawn.enemy) { loadEnemy(pack, spawn.enemy) }, spawn.x, spawn.y)
        }

        // Story: every quest and dialogue document of the pack, and the NPCs of the map.
        val quests = HashMap<String, QuestDef>()
        val dialogues = HashMap<String, DialogueDef>()
        for ((id, path) in pack.documentPaths) {
            val text = requireNotNull(pack.readFile(path)) { "cannot read $id" }
            if (path.startsWith("quests/")) {
                quests[id] = parseQuest(text).getOrThrow()
            } else if (path.startsWith("dialogues/")) {
                dialogues[id] = parseDialogue(text).getOrThrow()
            }
        }
        val npcs = map.npcs.map { NpcDef(it.key, it.dialogue, it.variant, it.x, it.y) }

        // Items that can be used (spec 06).
        val items = HashMap<String, ItemDef>()
        for ((id, path) in pack.documentPaths) {
            if (!path.startsWith("items/")) continue
            val doc = document(pack, id)
            items[id] = ItemDef(
                effects = doc["use"]?.jsonObject?.getValue("effects")?.jsonArray?.map {
                    val o = it.jsonObject
                    ItemEffect(o.getValue("effect").jsonPrimitive.content, o["amount"]?.jsonPrimitive?.long ?: 0L)
                } ?: emptyList(),
                kind = doc.getValue("kind").jsonPrimitive.content,
                price = doc.getValue("price").jsonPrimitive.long,
                stackMax = doc["stack_max"]?.jsonPrimitive?.int ?: 0,
                weapon = doc["weapon"]?.jsonObject?.let { WeaponStats(it.getValue("atk").jsonPrimitive.long, it.getValue("matk").jsonPrimitive.long) },
                armor = doc["armor"]?.jsonObject?.let { ArmorStats(it.getValue("def").jsonPrimitive.long, it.getValue("mdef").jsonPrimitive.long) },
            )
        }

        CombatSetup(
            enabled = true,
            player = PlayerSetup(protagonist.baseStats, protagonist.growthPm, weaponAtk, weaponMatk),
            skill = skill,
            spawns = spawns,
            xpTable = pack.intTables["base:table/xp"]?.values ?: emptyList(),
            seed = seed,
            story = StorySetup(quests, dialogues, npcs),
            startInventory = protagonist.startingInventory,
            streamEnemies = streamEnemyIds.toSet().associateWith {
                val def = loadEnemy(pack, it)
                def.copy(hp = maxOf(1L, def.hp * enemyHpPct / 100), atk = def.atk * enemyAtkPct / 100)
            },
            items = items,
            startWeapon = startWeapon,
        )
    }
