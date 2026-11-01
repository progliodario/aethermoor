package io.github.progliodario.aethermoor.core

import io.github.progliodario.aethermoor.core.sim.CombatSetup
import io.github.progliodario.aethermoor.core.sim.StorySetup
import io.github.progliodario.aethermoor.core.sim.parseStorySetup
import io.github.progliodario.aethermoor.core.sim.EnemyDef
import io.github.progliodario.aethermoor.core.sim.BehaviorDef
import io.github.progliodario.aethermoor.core.sim.DropDef
import io.github.progliodario.aethermoor.core.sim.EnemySpawn
import io.github.progliodario.aethermoor.core.sim.PlayerSetup
import io.github.progliodario.aethermoor.core.sim.SkillDef
import io.github.progliodario.aethermoor.core.sim.TileMap
import io.github.progliodario.aethermoor.core.sim.Tileset
import io.github.progliodario.aethermoor.core.sim.TileDef
import io.github.progliodario.aethermoor.core.sim.WorldSim
import io.github.progliodario.aethermoor.core.sim.loadCombatSetup
import io.github.progliodario.aethermoor.core.sim.parseTileMap
import io.github.progliodario.aethermoor.core.sim.parseTileset
import java.io.File
import kotlin.math.abs
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.double
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.long
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

/** Combat on the real data (mirror of combat_test.cpp) and the shared combat scenarios (suite "combat"). */
class CombatTest {
    private val repoRoot = File(System.getProperty("aether.repoRoot") ?: error("aether.repoRoot is not set"))
    private val pack = loadBasePack(repoRoot)
    private val map: TileMap = parseTileMap(requireNotNull(pack.readFile("maps/demo.tmj"))).getOrThrow()
    private val tileset: Tileset = parseTileset(requireNotNull(pack.readDocument("base:tileset/overworld"))).getOrThrow()
    private val setup: CombatSetup = loadCombatSetup(pack, map, "base:protagonist/ren", 7uL).getOrThrow()

    @Test
    fun combatSetupIsBuiltFromTheContentPack() {
        assertEquals(12, map.spawners.size)
        assertEquals(12, setup.spawns.size)
        assertEquals("base:enemy/slime_green", setup.spawns[0].def.id)
        assertEquals(28L, setup.spawns[0].def.hp)
        assertEquals(1, setup.spawns[0].def.drops.size)
        assertEquals(18, setup.spawns[0].def.behavior.windupTicks)
        assertEquals(6, setup.skill.startup)
        assertEquals(110, setup.skill.angleDeg)
        assertEquals(3L, setup.player.weaponAtk)
        assertEquals(9L, setup.player.base.luk)
        assertEquals(98, setup.xpTable.size)
    }

    @Test
    fun thePlayerStartsWithFullHealthAndDerivedStats() {
        val sim = WorldSim(map, tileset, 0f, setup)
        assertEquals(1L, sim.player.level)
        assertEquals(sim.derived.maxHp, sim.player.hp)
        assertEquals(6L * 2 + 8 / 2 + 3, sim.derived.atk)
        assertEquals(12, sim.enemies.size)
    }

    @Test
    fun aSwingAgainstNothingChangesNothing() {
        val sim = WorldSim(map, tileset, 0f, setup)
        repeat(100) { sim.tick(0f, 0f, true) }
        assertEquals(0, sim.player.kills)
        assertEquals(sim.derived.maxHp, sim.player.hp)
        assertTrue(sim.takeEvents().isEmpty())
    }

    @Test
    fun anEnemyThatReachesThePlayerHurtsItAndRespawnRestoresHealth() {
        val base = setup.spawns[0]
        val deadly = EnemySpawn(base.def.copy(atk = 100000), map.spawnX + 1f, map.spawnY)
        val custom = CombatSetup(true, setup.player, setup.skill, listOf(deadly), setup.xpTable, setup.seed, setup.startLevel)
        val sim = WorldSim(map, tileset, 0f, custom)
        repeat(120) { sim.tick(0f, 0f, false) }
        assertTrue(sim.player.deaths >= 1)
        assertTrue(sim.player.hp > 0)
        assertTrue(abs(sim.player.position.x - map.spawnX) < 0.01f)
    }

    @Test
    fun talkingToTheGuildClerkWithTheRealDataStartsHerQuest() {
        val nearMira = TileMap(map.width, map.height, map.tilesetId, map.ground, 8.5f, 15.4f, map.props, map.spawners, map.npcs)
        val sim = WorldSim(nearMira, tileset, 0f, setup)
        assertTrue(sim.story.npcInRange() != null)
        sim.story.interact()
        assertEquals("\$i18n:dlg.mira.offer", sim.story.dialogueView().text)
        sim.story.advance()
        assertTrue(sim.story.dialogueView().isChoice)
        assertEquals(2, sim.story.dialogueView().choices.size)
        sim.story.choose(0)
        sim.story.advance()
        assertFalse(sim.story.dialogueActive)
        assertTrue("base:quest/guild/slime_extermination" in sim.story.quests)

        // Talking again shows the "busy" line, and while the dialogue is open the player does not move.
        sim.story.interact()
        assertEquals("\$i18n:dlg.mira.busy", sim.story.dialogueView().text)
        val before = sim.player.position
        repeat(30) { sim.tick(1f, 0f, true) }
        assertEquals(before, sim.player.position)
    }

    // ---------------------------------------------------------------------------- conformance

    private fun JsonElement.num(): Float = jsonPrimitive.double.toFloat()

    private fun JsonObject.long(key: String) = getValue(key).jsonPrimitive.long

    private fun primary(s: JsonObject) =
        Primary(s.long("str"), s.long("vit"), s.long("dex"), s.long("agi"), s.long("int"), s.long("wis"), s.long("luk"))

    private fun enemyDef(d: JsonObject): EnemyDef {
        val b = d.getValue("behavior").jsonObject
        return EnemyDef(
            id = (d["id"] as? JsonPrimitive)?.content ?: "",
            hp = d.long("hp"), atk = d.long("atk"), def = d.long("def"), level = d.long("level"), xp = d.long("xp"),
            radiusX100 = d.getValue("radius_x100").jsonPrimitive.int, speedX100 = d.getValue("speed_x100").jsonPrimitive.int,
            drops = d.getValue("drops").jsonArray.map {
                val o = it.jsonObject
                DropDef(o.getValue("item").jsonPrimitive.content, o.long("qty_min"), o.long("qty_max"), o.long("weight_pm"))
            },
            behavior = BehaviorDef(
                b.getValue("aggro_x100").jsonPrimitive.int, b.getValue("leash_x100").jsonPrimitive.int,
                b.getValue("attack_range_x100").jsonPrimitive.int, b.getValue("hit_range_x100").jsonPrimitive.int,
                b.getValue("windup_ticks").jsonPrimitive.int, b.getValue("recovery_ticks").jsonPrimitive.int,
            ),
        )
    }

    private fun assertStory(ws: JsonObject, sim: WorldSim, at: String) {
        val story = sim.story
        assertEquals(ws.long("gold"), story.gold, "$at gold")
        val wantFlags = ws.getValue("flags").jsonObject
        assertEquals(wantFlags.size, story.flags.size, "$at flags size")
        for ((flag, value) in wantFlags) assertEquals(value.jsonPrimitive.boolean, story.flags[flag], "$at flag $flag")
        val wantQuests = ws.getValue("quests").jsonObject
        assertEquals(wantQuests.size, story.quests.size, "$at quests size")
        for ((questId, wq) in wantQuests) {
            val q = story.quests.getValue(questId)
            val w = wq.jsonObject
            assertEquals(w.getValue("stage").jsonPrimitive.content, q.stage, "$at $questId stage")
            assertEquals(w.getValue("done").jsonPrimitive.boolean, q.done, "$at $questId done")
            assertEquals(w.getValue("progress").jsonArray.map { it.jsonPrimitive.long }, q.progress.toList(), "$at $questId progress")
        }
        val view = story.dialogueView()
        val wd = ws.getValue("dialogue")
        if (wd is JsonNull) {
            assertFalse(view.active, "$at dialogue should be closed")
        } else {
            val d = wd.jsonObject
            assertTrue(view.active, "$at dialogue should be open")
            assertEquals(d.getValue("type").jsonPrimitive.content == "choice", view.isChoice, "$at dialogue type")
            if (view.isChoice) {
                assertEquals(d.getValue("choices").jsonArray.map { it.jsonPrimitive.content }, view.choices, "$at choices")
            } else {
                assertEquals(d.getValue("speaker").jsonPrimitive.content, view.speaker, "$at speaker")
                assertEquals(d.getValue("text").jsonPrimitive.content, view.text, "$at text")
            }
        }
    }

    @Test
    fun combatSuite() = runSuite("combat")

    @Test
    fun storySuite() = runSuite("story")

    private fun runSuite(suiteName: String) {
        val doc = Json.parseToJsonElement(File(repoRoot, "tests/conformance/$suiteName.json").readText()).jsonObject
        for (case in doc.getValue("cases").jsonArray) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val input = c.getValue("input").jsonObject
            val player = input.getValue("player").jsonObject
            val rows = input.getValue("grid").jsonArray.map { it.jsonPrimitive.content }
            val ground = IntArray(rows.size * rows[0].length) { if (rows[it / rows[0].length][it % rows[0].length] == '#') 5 else 1 }
            val start = player.getValue("start").jsonArray
            val gridMap = TileMap(rows[0].length, rows.size, "", ground, start[0].num(), start[1].num(), emptyList())
            val gridTileset = Tileset("", mapOf(1 to TileDef("floor", false), 5 to TileDef("wall", true)))

            val s = input.getValue("skill").jsonObject
            val combat = CombatSetup(
                enabled = true,
                player = PlayerSetup(
                    primary(player.getValue("base_stats").jsonObject), primary(player.getValue("growth_pm").jsonObject),
                    player.long("weapon_atk"), player.long("weapon_matk"),
                ),
                skill = SkillDef(
                    s.getValue("startup").jsonPrimitive.int, s.getValue("active").jsonPrimitive.int,
                    s.getValue("recovery").jsonPrimitive.int, s.getValue("cooldown").jsonPrimitive.int,
                    s.long("power_pct"), s.getValue("radius_x100").jsonPrimitive.int, s.getValue("angle_deg").jsonPrimitive.int,
                ),
                spawns = input.getValue("enemies").jsonArray.map {
                    val e = it.jsonObject
                    val pos = e.getValue("pos").jsonArray
                    EnemySpawn(enemyDef(e.getValue("def").jsonObject), pos[0].num(), pos[1].num())
                },
                xpTable = input.getValue("xp_table").jsonArray.map { it.jsonPrimitive.long },
                seed = input.getValue("seed").jsonPrimitive.content.removePrefix("0x").toULong(16),
                startLevel = player.getValue("level").jsonPrimitive.int,
                story = input["story"]?.let { parseStorySetup(it) } ?: StorySetup(),
            )

            val sim = WorldSim(gridMap, gridTileset, 0f, combat)
            val expect = c.getValue("expect").jsonObject
            val tol = expect.getValue("tol").num()
            for ((index, segment) in input.getValue("script").jsonArray.withIndex()) {
                val seg = segment.jsonObject
                val move = seg.getValue("move").jsonArray
                val attack = seg.getValue("attack").jsonPrimitive.boolean
                for (command in seg["do"]?.jsonArray ?: JsonArray(emptyList())) {
                    val cmd = command.jsonObject
                    when (cmd.getValue("cmd").jsonPrimitive.content) {
                        "interact" -> sim.story.interact()
                        "advance" -> sim.story.advance()
                        "choose" -> sim.story.choose(cmd.getValue("index").jsonPrimitive.int)
                    }
                }
                repeat(seg.getValue("ticks").jsonPrimitive.int) { sim.tick(move[0].num(), move[1].num(), attack) }

                val want = expect.getValue("checkpoints").jsonArray[index].jsonObject
                val wantPlayer = want.getValue("player").jsonObject
                val at = "$label checkpoint $index"
                assertEquals(wantPlayer.long("hp"), sim.player.hp, "$at hp")
                assertEquals(wantPlayer.long("level"), sim.player.level, "$at level")
                assertEquals(wantPlayer.long("xp"), sim.player.xp, "$at xp")
                assertEquals(wantPlayer.getValue("deaths").jsonPrimitive.int, sim.player.deaths, "$at deaths")
                assertTrue(abs(wantPlayer.getValue("x").num() - sim.player.position.x) <= tol, "$at x")
                assertTrue(abs(wantPlayer.getValue("y").num() - sim.player.position.y) <= tol, "$at y")
                assertEquals(want.getValue("kills").jsonPrimitive.int, sim.player.kills, "$at kills")
                val wantEnemies: JsonArray = want.getValue("enemies").jsonArray
                assertEquals(wantEnemies.size, sim.enemies.size, "$at enemy count")
                for ((i, enemy) in sim.enemies.withIndex()) {
                    val we = wantEnemies[i].jsonObject
                    assertEquals(we.long("hp"), enemy.hp, "$at enemy $i hp")
                    assertEquals(we.getValue("state").jsonPrimitive.content, enemy.state.id, "$at enemy $i state")
                    assertTrue(abs(we.getValue("x").num() - enemy.position.x) <= tol, "$at enemy $i x")
                    assertTrue(abs(we.getValue("y").num() - enemy.position.y) <= tol, "$at enemy $i y")
                }
                val wantInventory = want.getValue("inventory").jsonObject
                assertEquals(wantInventory.size, sim.inventory.size, "$at inventory size")
                for ((item, quantity) in wantInventory) {
                    assertEquals(quantity.jsonPrimitive.long, sim.inventory[item], "$at inventory $item")
                }
                want["story"]?.jsonObject?.let { ws -> assertStory(ws, sim, at) }
            }
        }
        assertFalse(doc.getValue("cases").jsonArray.isEmpty())
    }
}
