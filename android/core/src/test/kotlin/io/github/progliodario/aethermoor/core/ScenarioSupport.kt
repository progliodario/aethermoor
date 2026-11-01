package io.github.progliodario.aethermoor.core

import io.github.progliodario.aethermoor.core.sim.BehaviorDef
import io.github.progliodario.aethermoor.core.sim.CombatSetup
import io.github.progliodario.aethermoor.core.sim.DropDef
import io.github.progliodario.aethermoor.core.sim.EnemyDef
import io.github.progliodario.aethermoor.core.sim.EnemySpawn
import io.github.progliodario.aethermoor.core.sim.ItemDef
import io.github.progliodario.aethermoor.core.sim.ItemEffect
import io.github.progliodario.aethermoor.core.sim.PlayerSetup
import io.github.progliodario.aethermoor.core.sim.SkillDef
import io.github.progliodario.aethermoor.core.sim.StorySetup
import io.github.progliodario.aethermoor.core.sim.TileDef
import io.github.progliodario.aethermoor.core.sim.TileMap
import io.github.progliodario.aethermoor.core.sim.Tileset
import io.github.progliodario.aethermoor.core.sim.WorldSim
import io.github.progliodario.aethermoor.core.sim.parseStorySetup
import kotlin.math.abs
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

// Shared helpers of the scenario-based conformance tests (suites combat, story and save).

internal class ScenarioWorld(val map: TileMap, val tileset: Tileset, val combat: CombatSetup)

internal fun JsonElement.num(): Float = jsonPrimitive.double.toFloat()

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

/** The world described by a scenario input (see tools/conformance_m3.py). */
internal fun scenarioFromJson(input: JsonObject): ScenarioWorld {
    val player = input.getValue("player").jsonObject
    val rows = input.getValue("grid").jsonArray.map { it.jsonPrimitive.content }
    val ground = IntArray(rows.size * rows[0].length) { if (rows[it / rows[0].length][it % rows[0].length] == '#') 5 else 1 }
    val start = player.getValue("start").jsonArray
    val map = TileMap(rows[0].length, rows.size, "", ground, start[0].num(), start[1].num(), emptyList())
    val tileset = Tileset("", mapOf(1 to TileDef("floor", false), 5 to TileDef("wall", true)))
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
        startInventory = input["inventory"]?.jsonObject?.mapValues { it.value.jsonPrimitive.long } ?: emptyMap(),
        items = input["items"]?.jsonObject?.mapValues { (_, def) ->
            ItemDef(
                def.jsonObject.getValue("effects").jsonArray.map {
                    ItemEffect(it.jsonObject.getValue("effect").jsonPrimitive.content, it.jsonObject.getValue("amount").jsonPrimitive.long)
                },
            )
        } ?: emptyMap(),
    )
    return ScenarioWorld(map, tileset, combat)
}

internal fun newSim(world: ScenarioWorld) = WorldSim(world.map, world.tileset, 0f, world.combat)

/** Runs the story commands of a script segment, then its ticks. */
internal fun runSegment(sim: WorldSim, segment: JsonObject) {
    val move = segment.getValue("move").jsonArray
    val attack = segment.getValue("attack").jsonPrimitive.boolean
    for (command in segment["do"]?.jsonArray ?: JsonArray(emptyList())) {
        val cmd = command.jsonObject
        when (cmd.getValue("cmd").jsonPrimitive.content) {
            "use" -> sim.useItem(cmd.getValue("item").jsonPrimitive.content)
            "interact" -> sim.story.interact()
            "advance" -> sim.story.advance()
            "choose" -> sim.story.choose(cmd.getValue("index").jsonPrimitive.int)
        }
    }
    repeat(segment.getValue("ticks").jsonPrimitive.int) { sim.tick(move[0].num(), move[1].num(), attack) }
}

private fun assertNear(wanted: Float, actual: Float, tol: Float, message: String) {
    assertTrue(abs(wanted - actual) <= tol, "$message: expected $wanted, got $actual")
}

internal fun assertCheckpoint(sim: WorldSim, want: JsonObject, tol: Float, at: String) {
    val wantPlayer = want.getValue("player").jsonObject
    assertEquals(wantPlayer.long("hp"), sim.player.hp, "$at hp")
    assertEquals(wantPlayer.long("level"), sim.player.level, "$at level")
    assertEquals(wantPlayer.long("xp"), sim.player.xp, "$at xp")
    assertEquals(wantPlayer.getValue("deaths").jsonPrimitive.int, sim.player.deaths, "$at deaths")
    assertNear(wantPlayer.getValue("x").num(), sim.player.position.x, tol, "$at x")
    assertNear(wantPlayer.getValue("y").num(), sim.player.position.y, tol, "$at y")
    assertEquals(want.getValue("kills").jsonPrimitive.int, sim.player.kills, "$at kills")
    val wantEnemies = want.getValue("enemies").jsonArray
    assertEquals(wantEnemies.size, sim.enemies.size, "$at enemy count")
    for ((i, enemy) in sim.enemies.withIndex()) {
        val we = wantEnemies[i].jsonObject
        assertEquals(we.long("hp"), enemy.hp, "$at enemy $i hp")
        assertEquals(we.getValue("state").jsonPrimitive.content, enemy.state.id, "$at enemy $i state")
        assertNear(we.getValue("x").num(), enemy.position.x, tol, "$at enemy $i x")
        assertNear(we.getValue("y").num(), enemy.position.y, tol, "$at enemy $i y")
    }
    val wantInventory = want.getValue("inventory").jsonObject
    assertEquals(wantInventory.size, sim.inventory.size, "$at inventory size")
    for ((item, quantity) in wantInventory) {
        assertEquals(quantity.jsonPrimitive.long, sim.inventory[item], "$at inventory $item")
    }
    want["story"]?.jsonObject?.let { assertStory(it, sim, at) }
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
