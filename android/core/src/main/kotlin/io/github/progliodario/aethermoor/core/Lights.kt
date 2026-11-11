package io.github.progliodario.aethermoor.core

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.int
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

// The props that shine at night (spec 08, "Lights"): data/base/lights.json. Presentation only.

/** [radius] in tiles; [r], [g], [b] 0..255; [strengthPm] how bright at full night; [flickerPm] how much it wavers. */
class LightDef(val art: String, val radius: Float, val r: Int, val g: Int, val b: Int, val strengthPm: Int, val flickerPm: Int)

/** The lights of the pack; none when it has no table or the table is broken. */
fun loadLights(pack: Pack): List<LightDef> {
    val text = pack.readDocument("base:lights/all") ?: return emptyList()
    val doc = runCatching { Json.parseToJsonElement(text).jsonObject }.getOrNull() ?: return emptyList()
    val lights = runCatching { doc.getValue("lights").jsonArray }.getOrNull() ?: return emptyList()
    return lights.mapNotNull { element ->
        val l = element as? JsonObject ?: return@mapNotNull null
        val color = l["color"]?.jsonPrimitive?.content ?: "#FFC870"
        val rgb = if (color.length == 7) color.substring(1).toInt(16) else 0xFFC870
        LightDef(
            art = l["art"]?.jsonPrimitive?.content ?: return@mapNotNull null,
            radius = (l["radius_x100"]?.jsonPrimitive?.int ?: 350) / 100f,
            r = (rgb shr 16) and 0xFF,
            g = (rgb shr 8) and 0xFF,
            b = rgb and 0xFF,
            strengthPm = l["strength_pm"]?.jsonPrimitive?.intOrNull ?: 600,
            flickerPm = l["flicker_pm"]?.jsonPrimitive?.intOrNull ?: 0,
        )
    }
}
