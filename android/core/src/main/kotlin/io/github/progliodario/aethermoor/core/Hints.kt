package io.github.progliodario.aethermoor.core

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

// The hints of the first minutes (spec 16, "Hints"): data/base/hints.json. Presentation only.

/**
 * A hint, shown once a game (the story flag `hint_<id>` remembers it) when [whenKind] is true: start, quest, enemy_near, gather,
 * hurt, stone, talent_points, night, companion or renown. [text] is an $i18n: key for a keyboard, [textTouch] one for a touch screen.
 */
class HintDef(
    val id: String,
    val whenKind: String,
    val text: String,
    val textTouch: String,
    /** The text for a game controller (spec 16, "The last device"); [text] when the hint has none. */
    val textPad: String = text,
)

/** A line of the credits (spec 16, "Credits"): an $i18n: key or a text shown as it is; [heading] marks the title of a section. */
class CreditLine(val text: String, val heading: Boolean)

/** The credits of the pack, the lines in order; none when it has no table or the table is broken. */
fun loadCredits(pack: Pack): List<CreditLine> {
    val text = pack.readDocument("base:credits/all") ?: return emptyList()
    val doc = runCatching { Json.parseToJsonElement(text).jsonObject }.getOrNull() ?: return emptyList()
    val sections = runCatching { doc.getValue("sections").jsonArray }.getOrNull() ?: return emptyList()
    return sections.flatMap { element ->
        val s = element as? JsonObject ?: return@flatMap emptyList()
        listOf(CreditLine(s["heading"]?.jsonPrimitive?.content ?: "", true)) +
            (runCatching { s.getValue("lines").jsonArray }.getOrNull() ?: emptyList()).map { CreditLine(it.jsonPrimitive.content, false) }
    }
}

/** The hints of the pack in the order of the data; none when it has no table or the table is broken. */
fun loadHints(pack: Pack): List<HintDef> {
    val text = pack.readDocument("base:hints/all") ?: return emptyList()
    val doc = runCatching { Json.parseToJsonElement(text).jsonObject }.getOrNull() ?: return emptyList()
    val hints = runCatching { doc.getValue("hints").jsonArray }.getOrNull() ?: return emptyList()
    return hints.mapNotNull { element ->
        val h = element as? JsonObject ?: return@mapNotNull null
        val id = h["id"]?.jsonPrimitive?.content ?: return@mapNotNull null
        val key = h["text"]?.jsonPrimitive?.content ?: return@mapNotNull null
        HintDef(id, h["when"]?.jsonPrimitive?.content ?: "", key, h["text_touch"]?.jsonPrimitive?.content ?: key, h["text_pad"]?.jsonPrimitive?.content ?: key)
    }
}
