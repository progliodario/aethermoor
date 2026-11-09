package io.github.progliodario.aethermoor.core.sim

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

// The save bundle: the files of a slot packed into one `.aethersave` text, to move a game between devices.
// Spec: docs/spec/12-save-format.md ("Export and import"). Headless.

private val BUNDLE_FILES = listOf("auto.json", "quick.json", "protagonist.txt", "goal.txt")

fun isBundleFile(name: String): Boolean = name in BUNDLE_FILES

/** Packs the files of a slot (those with an allowed name; the others are left out). */
fun exportBundle(files: Map<String, String>, gameVersion: String): String =
    buildJsonObject {
        put("aethersave", 1)
        put("game_version", gameVersion)
        put("files", buildJsonObject { for (name in BUNDLE_FILES) files[name]?.let { put(name, it) } })
    }.toString()

private fun JsonPrimitive.isInteger(): Boolean = !isString && content.toLongOrNull() != null

/** The files of a bundle, or null when it is not a valid one. */
fun importBundle(text: String): Map<String, String>? {
    val doc = runCatching { Json.parseToJsonElement(text) }.getOrNull() as? JsonObject ?: return null
    val format = doc["aethersave"] as? JsonPrimitive ?: return null
    if (!format.isInteger() || format.content.toLong() != 1L) return null
    val filesObject = doc["files"] as? JsonObject ?: return null
    val out = LinkedHashMap<String, String>()
    for ((name, content) in filesObject) {
        val primitive = content as? JsonPrimitive ?: return null
        if (!isBundleFile(name) || !primitive.isString) return null
        out[name] = primitive.content
    }
    var hasSave = false
    for (name in listOf("auto.json", "quick.json")) {
        val saveText = out[name] ?: continue
        hasSave = true
        val save = runCatching { Json.parseToJsonElement(saveText) }.getOrNull() as? JsonObject ?: return null
        val version = save["save_version"] as? JsonPrimitive ?: return null
        if (!version.isInteger()) return null
    }
    return if (hasSave) out else null
}
