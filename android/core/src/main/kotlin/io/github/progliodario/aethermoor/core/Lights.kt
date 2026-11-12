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

/**
 * The colour of the hour (spec 08): what the world is multiplied by at night and at twilight (0xRRGGBB), the vignette and
 * the motes.
 */
class Grading(
    val night: Int = 0x5766C7,
    val twilight: Int = 0xFFCC9E,
    val vignettePm: Int = 280,
    val motes: Int = 26,
    val moteDay: Int = 0xFFF6C8,
    val moteNight: Int = 0xC8FF8A,
    /** How dark the long shadows of dawn and dusk are. */
    val shadowPm: Int = 300,
    /** The regions (by id) where the rain falls as snow. */
    val snowRegions: List<String> = emptyList(),
)

/** The grading of the pack (`grading` of base:lights/all); the defaults for what it does not say. */
fun loadGrading(pack: Pack): Grading {
    val defaults = Grading()
    val text = pack.readDocument("base:lights/all") ?: return defaults
    val doc = runCatching { Json.parseToJsonElement(text).jsonObject }.getOrNull() ?: return defaults
    val g = doc["grading"] as? JsonObject ?: return defaults

    fun color(key: String, fallback: Int): Int {
        val value = (g[key] as? kotlinx.serialization.json.JsonPrimitive)?.content ?: return fallback
        return if (value.length == 7 && value[0] == '#') value.substring(1).toIntOrNull(16) ?: fallback else fallback
    }

    fun number(key: String, fallback: Int): Int = (g[key] as? kotlinx.serialization.json.JsonPrimitive)?.intOrNull ?: fallback

    return Grading(
        night = color("night", defaults.night),
        twilight = color("twilight", defaults.twilight),
        vignettePm = number("vignette_pm", defaults.vignettePm),
        motes = number("motes", defaults.motes),
        moteDay = color("mote_day", defaults.moteDay),
        moteNight = color("mote_night", defaults.moteNight),
        shadowPm = number("shadow_pm", defaults.shadowPm),
        snowRegions = (g["snow_regions"] as? kotlinx.serialization.json.JsonArray)
            ?.mapNotNull { (it as? kotlinx.serialization.json.JsonPrimitive)?.content } ?: emptyList(),
    )
}
