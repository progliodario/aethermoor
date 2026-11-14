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
    val startingInventory: Map<String, Long> = emptyMap(),
    /** Palette variant of the character art ("" for the default). */
    val artVariant: String = "",
    val initiallyAvailable: Boolean = true,
    /** The ID of the companion that follows this protagonist (spec 10), or empty. */
    val companion: String = "",
    /** The gift rules (spec 18). */
    val gift: io.github.progliodario.aethermoor.core.sim.GiftDef = io.github.progliodario.aethermoor.core.sim.GiftDef(),
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
            startingInventory = j["starting_items"]?.jsonArray?.associate {
                it.jsonObject.getValue("item").jsonPrimitive.content to it.jsonObject.getValue("qty").jsonPrimitive.long
            } ?: emptyMap(),
            artVariant = (j["art_variant"] as? JsonPrimitive)?.contentOrNull ?: "",
            companion = (j["companion"] as? JsonPrimitive)?.contentOrNull ?: "",
            gift = j["gift_rules"]?.jsonObject?.let { g ->
                fun pct(key: String, neutral: Int) = (g[key] as? JsonPrimitive)?.contentOrNull?.toIntOrNull() ?: neutral
                io.github.progliodario.aethermoor.core.sim.GiftDef(
                    pct("mp_regen_pct", 100), pct("aggro_pct", 100), pct("heal_pct", 100), pct("dodge_cooldown_pct", 100), pct("death_save_ticks", 0),
                    pct("companion_atk_pct", 100), pct("bond_gain", 1),
                )
            } ?: io.github.progliodario.aethermoor.core.sim.GiftDef(),
            initiallyAvailable = (j["initially_available"] as? JsonPrimitive)?.contentOrNull?.toBooleanStrictOrNull() ?: true,
        )
    }
