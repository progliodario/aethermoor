package io.github.progliodario.aethermoor.core

import io.github.progliodario.aethermoor.core.sim.CombatSetup
import io.github.progliodario.aethermoor.core.sim.EnemySpawn
import io.github.progliodario.aethermoor.core.sim.SaveMeta
import io.github.progliodario.aethermoor.core.sim.TileMap
import io.github.progliodario.aethermoor.core.sim.Tileset
import io.github.progliodario.aethermoor.core.sim.WorldSim
import io.github.progliodario.aethermoor.core.sim.loadCombatSetup
import io.github.progliodario.aethermoor.core.sim.parseTileMap
import io.github.progliodario.aethermoor.core.sim.parseTileset
import io.github.progliodario.aethermoor.core.sim.saveFromJson
import io.github.progliodario.aethermoor.core.sim.saveToJson
import java.io.File
import kotlin.math.abs
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

/** Combat, story and saves on the real data (mirror of combat_test.cpp) and the shared scenarios. */
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
    fun thePlayerStartsWithFullHealthDerivedStatsAndTheStartingItems() {
        val sim = WorldSim(map, tileset, 0f, setup)
        assertEquals(1L, sim.player.level)
        assertEquals(sim.derived.maxHp, sim.player.hp)
        assertEquals(6L * 2 + 8 / 2 + 3, sim.derived.atk)
        assertEquals(12, sim.enemies.size)
        assertEquals(1L, sim.inventory["base:item/practice_sword"])
        assertEquals(3L, sim.inventory["base:item/bread"])
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

    @Test
    fun aSaveOfTheRealWorldSurvivesTheRoundTrip() {
        val sim = WorldSim(map, tileset, 0f, setup)
        repeat(200) { sim.tick(1f, 0f, it % 3 == 0) }
        sim.story.interact()
        val meta = SaveMeta("test", 1, "base:protagonist/ren", setup.seed)
        val text = saveToJson(sim.capture(), meta)

        val copy = WorldSim(map, tileset, 0f, setup)
        copy.restore(saveFromJson(text).getOrThrow()).getOrThrow()
        // Same state, so the same future.
        repeat(300) {
            sim.tick(1f, 0f, it % 2 == 0)
            copy.tick(1f, 0f, it % 2 == 0)
        }
        assertEquals(saveToJson(sim.capture(), meta), saveToJson(copy.capture(), meta))
    }

    @Test
    fun aSaveForADifferentWorldIsRefusedWithoutChangingAnything() {
        val sim = WorldSim(map, tileset, 0f, setup)
        val extra = "{\"x\":1,\"y\":1,\"hp\":1,\"state\":\"idle\",\"state_tick\":0},"
        val text = saveToJson(sim.capture(), SaveMeta("test", 1, "x", 0uL)).replace("\"enemies\":[", "\"enemies\":[$extra")
        val state = saveFromJson(text).getOrThrow()
        val before = sim.capture().hp
        assertTrue(sim.restore(state).isFailure)
        assertEquals(before, sim.capture().hp)
        assertTrue(saveFromJson("{\"save_version\": 99}").isFailure)
    }

    // ---------------------------------------------------------------------------- conformance

    private fun suite(name: String): JsonObject =
        Json.parseToJsonElement(File(repoRoot, "tests/conformance/$name.json").readText()).jsonObject

    private fun runSuite(name: String) {
        for (case in suite(name).getValue("cases").jsonArray) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val input = c.getValue("input").jsonObject
            val expect = c.getValue("expect").jsonObject
            val tol = expect.getValue("tol").num()
            val sim = newSim(scenarioFromJson(input))
            for ((index, segment) in input.getValue("script").jsonArray.withIndex()) {
                runSegment(sim, segment.jsonObject)
                assertCheckpoint(sim, expect.getValue("checkpoints").jsonArray[index].jsonObject, tol, "$label checkpoint $index")
            }
        }
    }

    @Test
    fun combatSuite() = runSuite("combat")

    @Test
    fun storySuite() = runSuite("story")

    /** Finishes each scenario from a save written by this client and from one written by the Python reference. */
    @Test
    fun saveSuite() {
        val cases = suite("save").getValue("cases").jsonArray
        assertFalse(cases.isEmpty())
        for (case in cases) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val input = c.getValue("input").jsonObject
            val expect = c.getValue("expect").jsonObject
            val tol = expect.getValue("tol").num()
            val split = input.getValue("split").jsonPrimitive.content.toInt()
            val script = input.getValue("script").jsonArray
            val world = scenarioFromJson(input)

            val first = newSim(world)
            for (i in 0 until split) runSegment(first, script[i].jsonObject)
            val ownText = saveToJson(first.capture(), SaveMeta("test", 1, "test", 0uL))
            val pythonText = JsonObject(input.getValue("save").jsonObject + ("save_version" to JsonPrimitive(1))).toString()

            for ((source, text) in listOf("own save" to ownText, "python save" to pythonText)) {
                val resumed = newSim(world)
                resumed.restore(saveFromJson(text).getOrThrow()).getOrThrow()
                for (i in split until script.size) {
                    runSegment(resumed, script[i].jsonObject)
                    assertCheckpoint(
                        resumed, expect.getValue("checkpoints").jsonArray[i - split].jsonObject, tol,
                        "$label ($source) checkpoint $i",
                    )
                }
            }
        }
    }
}
