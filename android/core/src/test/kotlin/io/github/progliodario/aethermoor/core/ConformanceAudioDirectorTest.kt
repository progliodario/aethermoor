package io.github.progliodario.aethermoor.core

import io.github.progliodario.aethermoor.core.audio.AmbienceEntry
import io.github.progliodario.aethermoor.core.audio.AmbienceRules
import io.github.progliodario.aethermoor.core.audio.PanelsOpen
import io.github.progliodario.aethermoor.core.audio.PlayerSound
import io.github.progliodario.aethermoor.core.audio.SoundCue
import io.github.progliodario.aethermoor.core.audio.SoundDirector
import io.github.progliodario.aethermoor.core.audio.SoundSnapshot
import io.github.progliodario.aethermoor.core.audio.ambienceGains
import java.io.File
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.double
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.long
import kotlinx.serialization.json.JsonPrimitive
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

/** The conformance suites of the sound director and of the ambience (spec 14). */
class ConformanceAudioDirectorTest {
    private val repoRoot = File(System.getProperty("aether.repoRoot") ?: error("aether.repoRoot is not set"))

    private fun suite(name: String): JsonArray {
        val doc = Json.parseToJsonElement(File(repoRoot, "tests/conformance/$name.json").readText()).jsonObject
        assertEquals(name, doc.getValue("suite").jsonPrimitive.content)
        return doc.getValue("cases").jsonArray
    }

    private fun JsonObject.bool(key: String) = getValue(key).jsonPrimitive.boolean

    private fun JsonObject.long(key: String) = getValue(key).jsonPrimitive.long

    private fun snapshotOf(j: JsonObject): SoundSnapshot {
        val p = j.getValue("player").jsonObject
        val panels = j.getValue("panels").jsonObject
        return SoundSnapshot(
            frame = j.long("frame"),
            player = PlayerSound(
                hp = p.long("hp"), maxHp = p.long("max_hp"), level = p.long("level"), phase = p.getValue("phase").jsonPrimitive.int,
                strike = p.bool("strike"), dodge = p.bool("dodge"), moving = p.bool("moving"),
                x = p.getValue("x").jsonPrimitive.double, y = p.getValue("y").jsonPrimitive.double,
                surface = p.getValue("surface").jsonPrimitive.content, saveCd = p.long("save_cd"),
            ),
            cues = j.getValue("cues").jsonArray.map {
                val c = it.jsonObject
                SoundCue(
                    kind = c.getValue("kind").jsonPrimitive.content, family = c.getValue("family").jsonPrimitive.content,
                    x = c.getValue("x").jsonPrimitive.double, y = c.getValue("y").jsonPrimitive.double,
                    crit = c["crit"]?.jsonPrimitive?.boolean ?: false, weak = c["weak"]?.jsonPrimitive?.boolean ?: false,
                )
            },
            items = j.long("items"), gold = j.long("gold"), mp = j.long("mp"),
            weapon = j.getValue("weapon").jsonPrimitive.content, armor = j.getValue("armor").jsonPrimitive.content,
            panels = PanelsOpen(
                bag = panels.bool("bag"), map = panels.bool("map"), journal = panels.bool("journal"),
                shop = panels.bool("shop"), board = panels.bool("board"), travel = panels.bool("travel"),
            ),
            dialogue = j.bool("dialogue"), line = j.long("line"), cursor = j.long("cursor"),
            questsStarted = j.long("quests_started"), questsDone = j.long("quests_done"), stones = j.long("stones"),
            region = j.getValue("region").jsonPrimitive.content, todPm = j.getValue("tod_pm").jsonPrimitive.int,
            rainPm = j.getValue("rain_pm").jsonPrimitive.int,
        )
    }

    /** A patch over the previous snapshot (see tools/conformance_audio.py): the cues of a frame are not kept. */
    private fun applyPatch(previous: JsonObject, patch: JsonObject, index: Int): JsonObject {
        val out = LinkedHashMap<String, JsonElement>(previous)
        out["cues"] = JsonArray(emptyList())
        out["frame"] = JsonPrimitive(index)
        for ((key, value) in patch) {
            if ((key == "player" || key == "panels") && value is JsonObject) {
                val merged = LinkedHashMap<String, JsonElement>(previous.getValue(key).jsonObject)
                merged.putAll(value)
                out[key] = JsonObject(merged)
            } else {
                out[key] = value
            }
        }
        return JsonObject(out)
    }

    @Test
    fun directorSuite() {
        for (case in suite("audio_director")) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val director = SoundDirector()
            var snapshot = c.getValue("input").jsonObject.getValue("base").jsonObject
            c.getValue("input").jsonObject.getValue("patches").jsonArray.forEachIndexed { index, patch ->
                snapshot = applyPatch(snapshot, patch.jsonObject, index)
                val got = director.update(snapshotOf(snapshot))
                val wanted = c.getValue("expect").jsonObject.getValue("events").jsonArray[index].jsonArray
                assertEquals(wanted.size, got.size, "$label frame $index: ${got.map { it.event }}")
                wanted.forEachIndexed { i, w ->
                    assertEquals(w.jsonObject.getValue("event").jsonPrimitive.content, got[i].event, "$label frame $index")
                    assertEquals(w.jsonObject.getValue("volume_pm").jsonPrimitive.int, got[i].volumePm, "$label frame $index")
                }
            }
        }
    }

    @Test
    fun ambienceSuite() {
        for (case in suite("audio_ambience")) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val input = c.getValue("input").jsonObject
            val r = input.getValue("rules").jsonObject
            val rain = r.getValue("rain").jsonObject
            val rules = AmbienceRules(
                rainLight = rain.getValue("light").jsonPrimitive.content,
                rainHeavy = rain.getValue("heavy").jsonPrimitive.content,
                silences = rain.getValue("silences").jsonArray.map { it.jsonPrimitive.content },
                regions = r.getValue("regions").jsonObject.mapValues { (_, entries) ->
                    entries.jsonArray.map {
                        val o = it.jsonObject
                        AmbienceEntry(o.getValue("sound").jsonPrimitive.content, o.getValue("gain_pm").jsonPrimitive.int, o["when"]?.jsonPrimitive?.content ?: "always")
                    }
                },
            )
            val got = ambienceGains(input.getValue("region").jsonPrimitive.content, input.getValue("tod_pm").jsonPrimitive.int, input.getValue("rain_pm").jsonPrimitive.int, rules)
            val wanted = c.getValue("expect").jsonObject.getValue("gains").jsonObject.mapValues { it.value.jsonPrimitive.int }
            assertEquals(wanted, got, label)
        }
    }
}
