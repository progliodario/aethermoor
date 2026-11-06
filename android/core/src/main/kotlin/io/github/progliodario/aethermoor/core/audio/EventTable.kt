package io.github.progliodario.aethermoor.core.audio

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

// The table that says which sounds play for an event, and what loops where (data/base/audio/events.json, spec 14).

class EventSounds(
    /** Short names (`swing_a` is `base:audio/sfx/swing_a`); played in turn. */
    val sounds: List<String>,
    val volumePm: Int,
    /** Frames during which the event does not play again. */
    val cooldown: Int,
)

class EventTable(val events: Map<String, EventSounds>, val ambience: AmbienceRules) {
    /** Every sound name the table mentions. */
    fun allSounds(): List<String> {
        val names = LinkedHashSet<String>()
        events.values.forEach { names.addAll(it.sounds) }
        names.add(ambience.rainLight)
        names.add(ambience.rainHeavy)
        ambience.regions.values.forEach { entries -> entries.forEach { names.add(it.sound) } }
        return names.toList()
    }
}

/** Parses the event table; the failure carries the reason. */
fun parseEventTable(jsonText: String): Result<EventTable> =
    runCatching {
        val j = Json.parseToJsonElement(jsonText).jsonObject
        val events = j.getValue("events").jsonObject.mapValues { (_, value) ->
            val e = value.jsonObject
            EventSounds(
                sounds = e.getValue("sounds").jsonArray.map { it.jsonPrimitive.content },
                volumePm = e.getValue("volume_pm").jsonPrimitive.int,
                cooldown = e["cooldown"]?.jsonPrimitive?.int ?: 0,
            )
        }
        val amb = j.getValue("ambience").jsonObject
        val rain = amb.getValue("rain").jsonObject
        val rules = AmbienceRules(
            rainLight = rain.getValue("light").jsonPrimitive.content,
            rainHeavy = rain.getValue("heavy").jsonPrimitive.content,
            silences = rain["silences"]?.jsonArray?.map { it.jsonPrimitive.content } ?: emptyList(),
            regions = amb.getValue("regions").jsonObject.mapValues { (_, entries) ->
                entries.jsonArray.map {
                    val o = it.jsonObject
                    AmbienceEntry(
                        sound = o.getValue("sound").jsonPrimitive.content,
                        gainPm = o.getValue("gain_pm").jsonPrimitive.int,
                        `when` = o["when"]?.jsonPrimitive?.content ?: "always",
                    )
                }
            },
        )
        EventTable(events, rules)
    }
