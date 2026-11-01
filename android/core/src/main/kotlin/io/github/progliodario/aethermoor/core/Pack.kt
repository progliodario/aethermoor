package io.github.progliodario.aethermoor.core

import java.io.File
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.longOrNull

// Content pack loading (manifest, localization tables, numeric tables).
// Spec: docs/spec/00-conventions.md and docs/spec/17-localization.md.

/** Highest data_format_version this client understands (project.json: data_format_version). */
const val SUPPORTED_DATA_FORMAT_VERSION = 1

private const val I18N_PREFIX = "\$i18n:"

/** Where pack files come from: a folder on a JVM, or Android assets (implemented in the game module). */
interface PackSource {
    /** Relative paths (forward slashes) of all `.json` files below [dir], recursive. Empty if missing. */
    fun listJson(dir: String): List<String>

    /** Text of the file at [path], or null if it cannot be read. */
    fun readText(path: String): String?
}

class FileSystemPackSource(private val root: File) : PackSource {
    override fun listJson(dir: String): List<String> {
        val base = File(root, dir)
        if (!base.isDirectory) return emptyList()
        return base.walkTopDown()
            .filter { it.isFile && it.extension == "json" }
            .map { it.relativeTo(root).path.replace(File.separatorChar, '/') }
            .sorted()
            .toList()
    }

    override fun readText(path: String): String? {
        val file = File(root, path)
        return if (file.isFile) file.readText(Charsets.UTF_8) else null
    }
}

data class PackManifest(
    val id: String,
    val nameKey: String,
    val version: String,
    val dataFormatVersion: Int,
    val languages: List<String>,
    val requiresFeatures: List<String>,
)

data class IntTable(val startLevel: Long, val values: List<Long>)

class Pack(
    val manifest: PackManifest,
    val strings: Map<String, Map<String, String>>,
    val intTables: Map<String, IntTable>,
) {
    /** Raw message for [key] in [lang], falling back to "en", then to the key itself. */
    fun message(lang: String, key: String): String =
        strings[lang]?.get(key) ?: strings["en"]?.get(key) ?: key

    /** Resolves "$i18n:key" (or a bare key) and formats it with [args]. */
    fun text(lang: String, reference: String, args: Map<String, Any> = emptyMap()): String {
        val key = reference.removePrefix(I18N_PREFIX)
        return formatMessage(message(lang, key), lang, args)
    }

    /** XP needed to go from [level] to level + 1, from table "base:table/xp"; 0 if out of range. */
    fun xpToNext(level: Long): Long {
        val table = intTables["base:table/xp"] ?: return 0
        val index = level - table.startLevel
        if (index < 0 || index >= table.values.size) return 0
        return table.values[index.toInt()]
    }
}

private fun parseJson(path: String, source: PackSource, errors: MutableList<String>): JsonElement? {
    val text = source.readText(path)
    if (text == null) {
        errors.add("$path: cannot open file")
        return null
    }
    return try {
        Json.parseToJsonElement(text)
    } catch (e: IllegalArgumentException) {
        errors.add("$path: invalid JSON")
        null
    }
}

private fun JsonObject.string(key: String): String = (this[key] as? JsonPrimitive)?.contentOrNull ?: ""

private fun JsonObject.stringList(key: String): List<String> =
    (this[key] as? JsonArray)?.mapNotNull { (it as? JsonPrimitive)?.takeIf { p -> p.isString }?.content } ?: emptyList()

/**
 * Loads the pack found at the root of [source]. Problems are appended to [errors]; on a fatal problem
 * (missing or invalid manifest, unsupported format) the result is null. Never throws for bad data.
 */
fun loadPack(source: PackSource, errors: MutableList<String>): Pack? {
    val manifestJson = parseJson("pack.json", source, errors) as? JsonObject
    if (manifestJson == null) {
        errors.add("pack.json: missing or not an object")
        return null
    }
    val manifest = PackManifest(
        id = manifestJson.string("id"),
        nameKey = manifestJson.string("name"),
        version = manifestJson.string("version"),
        dataFormatVersion = (manifestJson["data_format_version"] as? JsonPrimitive)?.longOrNull?.toInt() ?: 0,
        languages = manifestJson.stringList("languages"),
        requiresFeatures = manifestJson.stringList("requires_features"),
    )
    if (manifest.id.isEmpty() || manifest.version.isEmpty() || manifest.languages.isEmpty()) {
        errors.add("pack.json: id, version and languages are required")
        return null
    }
    if (manifest.dataFormatVersion < 1 || manifest.dataFormatVersion > SUPPORTED_DATA_FORMAT_VERSION) {
        errors.add("pack.json: unsupported data_format_version ${manifest.dataFormatVersion}")
        return null
    }

    val strings = HashMap<String, MutableMap<String, String>>()
    for (lang in manifest.languages) {
        val table = strings.getOrPut(lang) { HashMap() }
        for (file in source.listJson("i18n/$lang")) {
            val json = parseJson(file, source, errors) as? JsonObject ?: continue
            for ((key, value) in json) {
                if (key == "\$schema") continue
                val primitive = value as? JsonPrimitive
                if (primitive == null || !primitive.isString) {
                    errors.add("$file: value of '$key' is not a string")
                    continue
                }
                if (table.containsKey(key)) {
                    errors.add("$file: duplicate key '$key'")
                } else {
                    table[key] = primitive.content
                }
            }
        }
    }

    val intTables = HashMap<String, IntTable>()
    for (file in source.listJson("tables")) {
        val json = parseJson(file, source, errors) as? JsonObject ?: continue
        if (json.string("kind") != "int_list") continue
        val values = (json["values"] as? JsonArray)?.mapNotNull { (it as? JsonPrimitive)?.longOrNull } ?: emptyList()
        val start = (json["start_level"] as? JsonPrimitive)?.longOrNull ?: 0L
        intTables[json.string("id")] = IntTable(start, values)
    }

    return Pack(manifest, strings, intTables)
}
