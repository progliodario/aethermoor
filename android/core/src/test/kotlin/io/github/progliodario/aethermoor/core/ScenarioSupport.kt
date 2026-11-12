package io.github.progliodario.aethermoor.core

import io.github.progliodario.aethermoor.core.sim.ArmorStats
import io.github.progliodario.aethermoor.core.sim.BehaviorDef
import io.github.progliodario.aethermoor.core.sim.CombatSetup
import io.github.progliodario.aethermoor.core.sim.CompanionDef
import io.github.progliodario.aethermoor.core.sim.DodgeDef
import io.github.progliodario.aethermoor.core.sim.DropDef
import io.github.progliodario.aethermoor.core.sim.EnemyDef
import io.github.progliodario.aethermoor.core.sim.EnemySpawn
import io.github.progliodario.aethermoor.core.sim.GatherDrop
import io.github.progliodario.aethermoor.core.sim.GatherNode
import io.github.progliodario.aethermoor.core.sim.GiftDef
import io.github.progliodario.aethermoor.core.sim.ItemDef
import io.github.progliodario.aethermoor.core.sim.ItemEffect
import io.github.progliodario.aethermoor.core.sim.PlayerSetup
import io.github.progliodario.aethermoor.core.sim.Prop
import io.github.progliodario.aethermoor.core.sim.RecipeDef
import io.github.progliodario.aethermoor.core.sim.ShopDef
import io.github.progliodario.aethermoor.core.sim.SkillDef
import io.github.progliodario.aethermoor.core.sim.StorySetup
import io.github.progliodario.aethermoor.core.sim.StrikeDef
import io.github.progliodario.aethermoor.core.sim.TalentDef
import io.github.progliodario.aethermoor.core.sim.TileDef
import io.github.progliodario.aethermoor.core.sim.TileMap
import io.github.progliodario.aethermoor.core.sim.Tileset
import io.github.progliodario.aethermoor.core.sim.TitleDef
import io.github.progliodario.aethermoor.core.sim.WeaponStats
import io.github.progliodario.aethermoor.core.sim.WorldSim
import io.github.progliodario.aethermoor.core.sim.accessoryOf
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

internal class ScenarioWorld(val map: TileMap, val tileset: Tileset, val combat: CombatSetup, val startGold: Long = 0L)

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
        element = d["element"]?.jsonPrimitive?.content ?: "none",
        staggerPct = d["stagger_pct"]?.jsonPrimitive?.long ?: 40L,
        sound = d["sound"]?.jsonPrimitive?.content ?: "",
        weaknessesPm = d["weaknesses_pm"]?.jsonObject?.mapValues { it.value.jsonPrimitive.long } ?: emptyMap(),
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
    val gatherProps = input["gather_props"]?.jsonArray?.map { g ->
        val o = g.jsonObject
        Prop(o.getValue("art").jsonPrimitive.content, o.getValue("x").num(), o.getValue("y").num(), o.getValue("radius").num())
    } ?: emptyList()
    val map = TileMap(rows[0].length, rows.size, "", ground, start[0].num(), start[1].num(), gatherProps)
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
            s["kind"]?.jsonPrimitive?.content == "magical",
            s["element"]?.jsonPrimitive?.content ?: "none",
        ),
        echoPct = input["echo_pct"]?.jsonPrimitive?.int ?: 0,
        rainPm = input["weather"]?.jsonObject?.get("rain_pm")?.jsonPrimitive?.int ?: 0,
        rainAggroCutPm = input["weather"]?.jsonObject?.get("rain_aggro_cut_pm")?.jsonPrimitive?.int ?: 0,
        gift = input["gift"]?.jsonObject?.let { g ->
            fun pct(key: String, neutral: Int) = g[key]?.jsonPrimitive?.int ?: neutral
            GiftDef(pct("mp_regen_pct", 100), pct("aggro_pct", 100), pct("heal_pct", 100), pct("dodge_cooldown_pct", 100), pct("death_save_ticks", 0))
        } ?: GiftDef(),
        strike = input["strike"]?.jsonObject?.let { d ->
            StrikeDef(
                enabled = true,
                mp = d.long("mp"),
                skill = SkillDef(
                    d.getValue("startup").jsonPrimitive.int, d.getValue("active").jsonPrimitive.int,
                    d.getValue("recovery").jsonPrimitive.int, d.getValue("cooldown").jsonPrimitive.int,
                    d.long("power_pct"), d.getValue("radius_x100").jsonPrimitive.int, d.getValue("angle_deg").jsonPrimitive.int,
                    d["kind"]?.jsonPrimitive?.content == "magical",
                    d["element"]?.jsonPrimitive?.content ?: "none",
                ),
            )
        } ?: StrikeDef(),
        dodge = input["dodge"]?.jsonObject?.let { d ->
            DodgeDef(
                enabled = true,
                ticks = d.getValue("ticks").jsonPrimitive.int,
                speedMultX100 = d.getValue("speed_mult_x100").jsonPrimitive.int,
                iframes = d.getValue("iframes").jsonPrimitive.int,
                cooldown = d.getValue("cooldown").jsonPrimitive.int,
            )
        } ?: DodgeDef(),
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
        companion = input["companion"]?.jsonObject?.let { c ->
            CompanionDef(
                atkBase = c.long("atk_base"), atkPerLevel = c.long("atk_per_level"), rangeX100 = c.getValue("range_x100").jsonPrimitive.int,
                cooldownTicks = c.getValue("cooldown_ticks").jsonPrimitive.int, speedX100 = c.getValue("speed_x100").jsonPrimitive.int,
                followX100 = c.getValue("follow_x100").jsonPrimitive.int,
                careBond = c["care_bond"]?.jsonPrimitive?.int ?: 0, careTicks = c["care_ticks"]?.jsonPrimitive?.int ?: 0,
                carePct = c["care_pct"]?.jsonPrimitive?.int ?: 0,
            )
        },
        talents = input["talents"]?.jsonArray?.map { t ->
            val o = t.jsonObject
            TalentDef(
                o.getValue("id").jsonPrimitive.content, o.getValue("name").jsonPrimitive.content, o.getValue("stat").jsonPrimitive.content,
                o.long("pct_per_rank"), o.getValue("max_rank").jsonPrimitive.int,
                o["requires"]?.jsonObject?.getValue("talent")?.jsonPrimitive?.content ?: "", o["requires"]?.jsonObject?.getValue("rank")?.jsonPrimitive?.int ?: 0,
            )
        } ?: emptyList(),
        talentPointsPerLevel = input["talent_points_per_level"]?.jsonPrimitive?.int ?: 1,
        titles = input["titles"]?.jsonArray?.map { t ->
            val o = t.jsonObject
            TitleDef(
                o.getValue("id").jsonPrimitive.content, o.getValue("name").jsonPrimitive.content, o.getValue("kind").jsonPrimitive.content,
                o.long("count"), o["enemy"]?.jsonPrimitive?.content ?: "", o["atk_pct"]?.jsonPrimitive?.long ?: 0L,
                o["gather_bonus"]?.jsonPrimitive?.long ?: 0L, o["craft_bonus"]?.jsonPrimitive?.long ?: 0L,
                o["parry_bonus"]?.jsonPrimitive?.long ?: 0L, o["xp_pct"]?.jsonPrimitive?.long ?: 0L,
            )
        } ?: emptyList(),
        recipes = input["recipes"]?.jsonArray?.map { r ->
            val o = r.jsonObject
            RecipeDef(
                o.getValue("id").jsonPrimitive.content, o.getValue("output").jsonObject.getValue("item").jsonPrimitive.content, o.getValue("output").jsonObject.long("qty"),
                o.getValue("inputs").jsonArray.map { i -> Pair(i.jsonObject.getValue("item").jsonPrimitive.content, i.jsonObject.long("qty")) },
                o["station"]?.jsonPrimitive?.content ?: "",
            )
        } ?: emptyList(),
        gatherNodes = input["gather_nodes"]?.jsonArray?.associate { n ->
            val o = n.jsonObject
            o.getValue("prop").jsonPrimitive.content to GatherNode(
                o.getValue("sound").jsonPrimitive.content, o.getValue("cooldown_ticks").jsonPrimitive.int, o.getValue("reach_x100").jsonPrimitive.int,
                o.getValue("drops").jsonArray.map { d -> val x = d.jsonObject; GatherDrop(x.getValue("item").jsonPrimitive.content, x.long("qty_min"), x.long("qty_max"), x.long("weight_pm")) },
            )
        } ?: emptyMap(),
        items = input["items"]?.jsonObject?.mapValues { (_, def) ->
            val d = def.jsonObject
            ItemDef(
                effects = d["effects"]?.jsonArray?.map {
                    ItemEffect(
                        it.jsonObject.getValue("effect").jsonPrimitive.content, it.jsonObject["amount"]?.jsonPrimitive?.long ?: 0L,
                        it.jsonObject["ticks"]?.jsonPrimitive?.int ?: 0,
                    )
                } ?: emptyList(),
                kind = d["kind"]?.jsonPrimitive?.content ?: "",
                price = d["price"]?.jsonPrimitive?.long ?: 0L,
                stackMax = d["stack_max"]?.jsonPrimitive?.int ?: 0,
                weapon = d["weapon"]?.jsonObject?.let { WeaponStats(it.long("atk"), it.long("matk"), it["element"]?.jsonPrimitive?.content ?: "none") },
                armor = d["armor"]?.jsonObject?.let { ArmorStats(it.long("def"), it.long("mdef")) },
                accessory = d["accessory"]?.jsonObject?.let { accessoryOf(it) },
            )
        } ?: emptyMap(),
        startWeapon = input["equipped"]?.jsonObject?.get("weapon")?.jsonPrimitive?.content ?: "",
        startArmor = input["equipped"]?.jsonObject?.get("armor")?.jsonPrimitive?.content ?: "",
        shop = input["shop"]?.jsonObject?.let { shop ->
            ShopDef(shop.getValue("price_pm").jsonPrimitive.int, shop.getValue("stock").jsonArray.map { it.jsonPrimitive.content })
        },
    )
    return ScenarioWorld(map, tileset, combat, input["start_gold"]?.jsonPrimitive?.long ?: 0L)
}

internal fun newSim(world: ScenarioWorld) =
    WorldSim(world.map, world.tileset, 0f, world.combat).also { it.story.gold = world.startGold }

/** Runs the story commands of a script segment, then its ticks. */
internal fun runSegment(sim: WorldSim, segment: JsonObject) {
    val move = segment.getValue("move").jsonArray
    val attack = segment.getValue("attack").jsonPrimitive.boolean
    val dodge = segment["dodge"]?.jsonPrimitive?.boolean ?: false
    val strike = segment["strike"]?.jsonPrimitive?.boolean ?: false
    val parry = segment["parry"]?.jsonPrimitive?.boolean ?: false
    for (command in segment["do"]?.jsonArray ?: JsonArray(emptyList())) {
        val cmd = command.jsonObject
        when (cmd.getValue("cmd").jsonPrimitive.content) {
            "start_quest" -> sim.story.startQuest(cmd.getValue("quest").jsonPrimitive.content)
            "use" -> sim.useItem(cmd.getValue("item").jsonPrimitive.content)
            "gather" -> sim.gather()
            "talent" -> sim.learnTalent(cmd.getValue("talent").jsonPrimitive.content)
            "companion_stay" -> sim.companionStay()
            "craft" -> sim.craft(cmd.getValue("recipe").jsonPrimitive.content)
            "equip" -> sim.equip(cmd.getValue("item").jsonPrimitive.content)
            "buy" -> sim.buy(cmd.getValue("item").jsonPrimitive.content)
            "sell" -> sim.sell(cmd.getValue("item").jsonPrimitive.content)
            "open_shop" -> sim.openShop()
            "close_shop" -> sim.closeShop()
            "interact" -> sim.story.interact()
            "advance" -> sim.story.advance()
            "choose" -> sim.story.choose(cmd.getValue("index").jsonPrimitive.int)
        }
    }
    repeat(segment.getValue("ticks").jsonPrimitive.int) { sim.tick(move[0].num(), move[1].num(), attack, dodge, strike, parry) }
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
    want["talents"]?.jsonObject?.let { wt ->
        assertEquals(wt.mapValues { it.value.jsonPrimitive.int }, sim.talents.toMap(), "$at talents")
        assertEquals(want.getValue("talent_points").jsonPrimitive.int, sim.talentPoints(), "$at talent points")
        assertEquals(want.long("max_hp"), sim.derived.maxHp, "$at max hp")
        assertEquals(want.long("max_mp"), sim.derived.maxMp, "$at max mp")
        assertEquals(want.long("matk"), sim.derived.matk, "$at matk")
        assertEquals(want.long("crit_chance_pm"), sim.derived.critChancePm, "$at crit")
        assertEquals(want.long("move_speed_x100"), sim.derived.moveSpeedX100, "$at speed")
    }
    want["companion"]?.jsonObject?.let { wc ->
        val pos = sim.companionPosition ?: error("$at no companion")
        assertNear(wc.getValue("x").num(), pos.x, tol, "$at companion x")
        assertNear(wc.getValue("y").num(), pos.y, tol, "$at companion y")
        assertEquals(wc.getValue("stay").jsonPrimitive.boolean, sim.companionStaying, "$at companion stay")
        assertEquals(wc.getValue("bond").jsonPrimitive.int, sim.companionBond, "$at companion bond")
    }
    want["bestiary"]?.jsonObject?.let { b ->
        assertEquals(b.size, sim.bestiary.size, "$at bestiary size")
        for ((id, count) in b) assertEquals(count.jsonPrimitive.int, sim.bestiary[id], "$at bestiary $id")
        assertEquals(want.getValue("counters").jsonObject.mapValues { it.value.jsonPrimitive.int }, sim.counters.toMap(), "$at counters")
        assertEquals(want.getValue("titles").jsonArray.map { it.jsonPrimitive.content }, sim.earnedTitles(), "$at titles")
    }
    want["equipped"]?.jsonObject?.let {
        assertEquals(it.getValue("weapon").jsonPrimitive.content, sim.equippedWeapon, "$at equipped weapon")
        assertEquals(it.getValue("armor").jsonPrimitive.content, sim.equippedArmor, "$at equipped armor")
        assertEquals(it["accessory"]?.jsonPrimitive?.content ?: "", sim.equippedAccessory, "$at equipped accessory")
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
    ws["guild_points"]?.let { assertEquals(it.jsonPrimitive.long, story.guildPoints, "$at guild points") }
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
