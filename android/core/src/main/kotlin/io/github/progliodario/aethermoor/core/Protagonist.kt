package io.github.progliodario.aethermoor.core

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.long

// Protagonist definitions (schemas/protagonist.schema.json). Only the fields used so far are read.

data class ProtagonistDef(
    val id: String,
    val nameKey: String,
    val baseStats: Primary,
    val growthPm: Primary,
    val startingItems: List<String>,
    val startingSkills: List<String>,
)

fun parseProtagonist(jsonText: String): Result<ProtagonistDef> =
    runCatching {
        val j = Json.parseToJsonElement(jsonText).jsonObject
        val s = j.getValue("base_stats").jsonObject
        fun stat(key: String) = s.getValue(key).jsonPrimitive.long
        val g = j.getValue("growth_pm").jsonObject
        fun growth(key: String) = g.getValue(key).jsonPrimitive.long
        ProtagonistDef(
            id = j.getValue("id").jsonPrimitive.content,
            nameKey = (j["name"] as? JsonPrimitive)?.contentOrNull ?: "",
            baseStats = Primary(stat("str"), stat("vit"), stat("dex"), stat("agi"), stat("int"), stat("wis"), stat("luk")),
            growthPm = Primary(growth("str"), growth("vit"), growth("dex"), growth("agi"), growth("int"), growth("wis"), growth("luk")),
            startingItems = j["starting_items"]?.jsonArray?.map { it.jsonObject.getValue("item").jsonPrimitive.content } ?: emptyList(),
            startingSkills = j.getValue("starting_skills").jsonArray.map { it.jsonPrimitive.content },
        )
    }
