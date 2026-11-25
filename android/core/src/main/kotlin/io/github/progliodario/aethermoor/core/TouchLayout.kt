package io.github.progliodario.aethermoor.core

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.intOrNull
import kotlin.math.max
import kotlin.math.roundToInt

/**
 * One button of the touch layout (spec 16, "The layout of the buttons"): how far it is moved from where it is by default, in permille of
 * the width and of the height of the screen (so that it keeps its place when the phone turns), and its size in percent.
 */
data class TouchButton(val dxPm: Int = 0, val dyPm: Int = 0, val sizePct: Int = 100)

/**
 * The layout of the touch buttons of Android, kept in the settings file as `"touch_layout": {"dodge": [dx_pm, dy_pm, size_pct], ...}`
 * (spec 16). Presentation only: a button that is not in it is where it is by default. Headless: the game draws the buttons with [place].
 */
class TouchLayout(val buttons: Map<String, TouchButton> = emptyMap()) {
    fun of(id: String): TouchButton = buttons[id] ?: TouchButton()

    /**
     * The rectangle (x, y, w, h, in pixels, y down) of the button [id] whose rectangle by default is [r], on a screen of [width] x [height]:
     * moved, resized around its centre and kept inside the screen.
     */
    fun place(id: String, r: FloatArray, width: Float, height: Float): FloatArray {
        val b = of(id)
        val w = r[2] * b.sizePct / 100f
        val h = r[3] * b.sizePct / 100f
        val cx = r[0] + r[2] / 2f + b.dxPm * width / 1000f
        val cy = r[1] + r[3] / 2f + b.dyPm * height / 1000f
        val x = (cx - w / 2f).coerceIn(0f, max(0f, width - w))
        val y = (cy - h / 2f).coerceIn(0f, max(0f, height - h))
        return floatArrayOf(x, y, w, h)
    }

    /** The layout with the button [id] moved by [dx] x [dy] pixels on a screen of [width] x [height]. */
    fun moved(id: String, dx: Float, dy: Float, width: Float, height: Float): TouchLayout {
        val b = of(id)
        val moved = b.copy(
            dxPm = (b.dxPm + (dx * 1000f / max(1f, width)).roundToInt()).coerceIn(-MAX_MOVE_PM, MAX_MOVE_PM),
            dyPm = (b.dyPm + (dy * 1000f / max(1f, height)).roundToInt()).coerceIn(-MAX_MOVE_PM, MAX_MOVE_PM),
        )
        return TouchLayout(buttons + (id to moved))
    }

    /** The layout with the button [id] larger (a positive [stepPct]) or smaller, between [MIN_SIZE_PCT] and [MAX_SIZE_PCT]. */
    fun resized(id: String, stepPct: Int): TouchLayout {
        val b = of(id)
        return TouchLayout(buttons + (id to b.copy(sizePct = (b.sizePct + stepPct).coerceIn(MIN_SIZE_PCT, MAX_SIZE_PCT))))
    }

    /** The value of `touch_layout` in the settings file: the buttons that are not where they are by default, in the order of [BUTTONS]. */
    fun toJson(): String = BUTTONS.filter { of(it) != TouchButton() }
        .joinToString(", ", "{", "}") { id -> of(id).let { "\"$id\": [${it.dxPm}, ${it.dyPm}, ${it.sizePct}]" } }

    companion object {
        /** The buttons that can be moved: the dodge, the power strike, the parry and Analyze. */
        val BUTTONS = listOf("dodge", "strike", "parry", "analyze")
        const val MIN_SIZE_PCT = 60
        const val MAX_SIZE_PCT = 160
        const val MAX_MOVE_PM = 1000

        /** The layout in the text of the settings file; an empty layout when it has none or it makes no sense. */
        fun fromSettings(text: String?): TouchLayout {
            val doc = text?.let { runCatching { Json.parseToJsonElement(it) }.getOrNull() } as? JsonObject ?: return TouchLayout()
            val layout = doc["touch_layout"] as? JsonObject ?: return TouchLayout()
            return TouchLayout(BUTTONS.mapNotNull { id -> parseButton(layout[id] as? JsonArray)?.let { id to it } }.toMap())
        }

        /** A button of the layout, `[dx_pm, dy_pm, size_pct]`; null when it is not three integers. */
        private fun parseButton(entry: JsonArray?): TouchButton? {
            val values = entry?.mapNotNull { (it as? JsonPrimitive)?.intOrNull } ?: return null
            if (entry.size != 3 || values.size != 3) return null
            return TouchButton(
                values[0].coerceIn(-MAX_MOVE_PM, MAX_MOVE_PM),
                values[1].coerceIn(-MAX_MOVE_PM, MAX_MOVE_PM),
                values[2].coerceIn(MIN_SIZE_PCT, MAX_SIZE_PCT),
            )
        }
    }
}
