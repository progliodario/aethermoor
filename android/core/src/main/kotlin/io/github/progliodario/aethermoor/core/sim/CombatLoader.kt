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

/** The companion of a protagonist (spec 10), or null when there is none. */
private fun loadCompanion(pack: Pack, id: String): CompanionDef? {
    if (id.isEmpty()) return null
    val text = pack.readDocument(id) ?: return null
    val c = Json.parseToJsonElement(text).jsonObject
    return CompanionDef(
        id = id,
        name = c["name"]?.jsonPrimitive?.content ?: "",
        art = c["art"]?.jsonPrimitive?.content ?: "",
        scalePct = c["scale_pct"]?.jsonPrimitive?.int ?: 100,
        atkBase = c.getValue("atk_base").jsonPrimitive.long,
        atkPerLevel = c.getValue("atk_per_level").jsonPrimitive.long,
        rangeX100 = c.getValue("range_x100").jsonPrimitive.int,
        cooldownTicks = c.getValue("cooldown_ticks").jsonPrimitive.int,
        speedX100 = c.getValue("speed_x100").jsonPrimitive.int,
        followX100 = c.getValue("follow_x100").jsonPrimitive.int,
    )
}

/** The titles (spec 11); none when the pack has no table. */
private fun loadTitles(pack: Pack): List<TitleDef> {
    val text = pack.readDocument("base:titles/all") ?: return emptyList()
    val titles = Json.parseToJsonElement(text).jsonObject["titles"]?.jsonArray ?: return emptyList()
    return titles.map { element ->
        val t = element.jsonObject
        TitleDef(
            id = t.getValue("id").jsonPrimitive.content,
            name = t.getValue("name").jsonPrimitive.content,
            kind = t.getValue("kind").jsonPrimitive.content,
            count = t.getValue("count").jsonPrimitive.long,
            enemy = t["enemy"]?.jsonPrimitive?.content ?: "",
            atkPct = t["atk_pct"]?.jsonPrimitive?.long ?: 0L,
        )
    }
}

/** The crafting recipes (spec 06, "Crafting"); none when the pack has no table. */
private fun loadRecipes(pack: Pack): List<RecipeDef> {
    val text = pack.readDocument("base:recipes/all") ?: return emptyList()
    val recipes = Json.parseToJsonElement(text).jsonObject["recipes"]?.jsonArray ?: return emptyList()
    return recipes.map { element ->
        val r = element.jsonObject
        val output = r.getValue("output").jsonObject
        RecipeDef(
            id = r.getValue("id").jsonPrimitive.content,
            output = output.getValue("item").jsonPrimitive.content,
            outputQty = output.getValue("qty").jsonPrimitive.long,
            inputs = r.getValue("inputs").jsonArray.map { Pair(it.jsonObject.getValue("item").jsonPrimitive.content, it.jsonObject.getValue("qty").jsonPrimitive.long) },
        )
    }
}

/** The props that can be gathered from (spec 06, "Gathering"); none when the pack has no table. */
private fun loadGatherNodes(pack: Pack): Map<String, GatherNode> {
    val text = pack.readDocument("base:gathering/nodes") ?: return emptyMap()
    val nodes = Json.parseToJsonElement(text).jsonObject["nodes"]?.jsonArray ?: return emptyMap()
    return nodes.associate { element ->
        val n = element.jsonObject
        n.getValue("prop").jsonPrimitive.content to GatherNode(
            sound = n["sound"]?.jsonPrimitive?.content ?: "plant",
            cooldownTicks = n.getValue("cooldown_ticks").jsonPrimitive.int,
            reachX100 = n.getValue("reach_x100").jsonPrimitive.int,
            drops = n.getValue("drops").jsonArray.map {
                val d = it.jsonObject
                GatherDrop(d.getValue("item").jsonPrimitive.content, d.getValue("qty_min").jsonPrimitive.long, d.getValue("qty_max").jsonPrimitive.long, d.getValue("weight_pm").jsonPrimitive.long)
            },
        )
    }
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
        element = enemy["element"]?.jsonPrimitive?.content ?: "none",
        staggerPct = enemy["stagger_pct"]?.jsonPrimitive?.long ?: 40L,
        sound = enemy["sound"]?.jsonPrimitive?.content ?: "",
        weaknessesPm = enemy["weaknesses_pm"]?.jsonObject?.mapValues { it.value.jsonPrimitive.long } ?: emptyMap(),
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
                magical = s.getValue("damage").jsonObject.getValue("kind").jsonPrimitive.content == "magical",
                element = s.getValue("damage").jsonObject["element"]?.jsonPrimitive?.content ?: "none",
            )
            break
        }
        requireNotNull(skill) { "the protagonist has no skill with a hitbox" }
        var strike = StrikeDef()
        var hitboxSkills = 0
        for (skillId in protagonist.startingSkills) { // the power strike: the second skill with a hitbox
            val s = document(pack, skillId)
            val hitbox = s["hitbox"]?.jsonObject ?: continue
            if (++hitboxSkills != 2) continue
            val timing = s.getValue("timing").jsonObject
            strike = StrikeDef(
                enabled = true,
                mp = s.getValue("cost").jsonObject.getValue("mp").jsonPrimitive.long,
                skill = SkillDef(
                    startup = timing.getValue("startup").jsonPrimitive.int,
                    active = timing.getValue("active").jsonPrimitive.int,
                    recovery = timing.getValue("recovery").jsonPrimitive.int,
                    cooldown = s.getValue("cooldown_ticks").jsonPrimitive.int,
                    powerPct = s.getValue("damage").jsonObject.getValue("power_pct").jsonPrimitive.long,
                    radiusX100 = hitbox.getValue("radius_x100").jsonPrimitive.int,
                    angleDeg = hitbox.getValue("angle_deg").jsonPrimitive.int,
                    magical = s.getValue("damage").jsonObject.getValue("kind").jsonPrimitive.content == "magical",
                element = s.getValue("damage").jsonObject["element"]?.jsonPrimitive?.content ?: "none",
                ),
            )
            break
        }
        var dodge = DodgeDef()
        for (skillId in protagonist.startingSkills) { // the dodge roll: a skill with a `movement` block
            val s = document(pack, skillId)
            val movement = s["movement"]?.jsonObject ?: continue
            dodge = DodgeDef(
                enabled = true,
                ticks = s.getValue("timing").jsonObject.getValue("active").jsonPrimitive.int,
                speedMultX100 = movement.getValue("speed_mult_x100").jsonPrimitive.int,
                iframes = movement.getValue("iframes").jsonPrimitive.int,
                cooldown = s.getValue("cooldown_ticks").jsonPrimitive.int,
            )
            break
        }

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
                weapon = doc["weapon"]?.jsonObject?.let {
                    WeaponStats(it.getValue("atk").jsonPrimitive.long, it.getValue("matk").jsonPrimitive.long, it["element"]?.jsonPrimitive?.content ?: "none")
                },
                armor = doc["armor"]?.jsonObject?.let { ArmorStats(it.getValue("def").jsonPrimitive.long, it.getValue("mdef").jsonPrimitive.long) },
            )
        }

        CombatSetup(
            enabled = true,
            player = PlayerSetup(protagonist.baseStats, protagonist.growthPm, weaponAtk, weaponMatk),
            skill = skill,
            dodge = dodge,
            strike = strike,
            gift = protagonist.gift,
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
            gatherNodes = loadGatherNodes(pack),
            recipes = loadRecipes(pack),
            titles = loadTitles(pack),
            companion = loadCompanion(pack, protagonist.companion),
            startWeapon = startWeapon,
        )
    }
