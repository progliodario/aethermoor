package io.github.progliodario.aethermoor.core

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.floatOrNull
import kotlinx.serialization.json.jsonObject

// The font of the interface (spec 13, "Font"): data/base/fonts/aether.json. Presentation only.

/** [width]: what the glyph takes in a line of text, in font units; [path]: its strokes in the cell (empty: a space). */
class FontGlyph(val width: Float, val path: String)

/**
 * The cell every glyph is drawn in ([cellW] x [cellH] font units), where the capitals are in it ([capTop], [capHeight]),
 * the height of the lower case ([xHeight]), the distance between two lines ([line]), the width of the pen ([stroke]) and
 * the glyphs by Unicode code point.
 */
class FontDef(
    val cellW: Float,
    val cellH: Float,
    val capTop: Float,
    val capHeight: Float,
    val xHeight: Float,
    val line: Float,
    val stroke: Float,
    val glyphs: Map<Int, FontGlyph>,
)

/** The font of the pack; null when the pack has none or it is broken. */
fun loadFont(pack: Pack): FontDef? {
    val text = pack.readDocument("base:font/aether") ?: return null
    val doc = runCatching { Json.parseToJsonElement(text).jsonObject }.getOrNull() ?: return null
    val table = doc["glyphs"] as? JsonObject ?: return null

    fun number(from: JsonObject?, key: String, fallback: Float): Float = (from?.get(key) as? JsonPrimitive)?.floatOrNull ?: fallback

    val cell = doc["cell"] as? JsonObject
    val cellW = number(cell, "w", 8f)
    val glyphs = HashMap<Int, FontGlyph>()
    for ((key, value) in table) {
        val glyph = value as? JsonObject ?: continue
        if (key.isEmpty()) continue
        val path = (glyph["d"] as? JsonPrimitive)?.takeIf { it.isString }?.content ?: ""
        glyphs[key.codePointAt(0)] = FontGlyph(number(glyph, "w", cellW), path)
    }
    if (glyphs.isEmpty()) return null
    return FontDef(
        cellW = cellW,
        cellH = number(cell, "h", 11f),
        capTop = number(cell, "cap_top", 2.5f),
        capHeight = number(cell, "cap_height", 6f),
        xHeight = number(cell, "x_height", 4f),
        line = number(cell, "line", 9.8f),
        stroke = number(doc, "stroke", 0.95f),
        glyphs = glyphs,
    )
}
