package io.github.progliodario.aethermoor.core.sim

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

// The profile: what is kept across games in `profile.json` next to the settings (the best count of every creature killed and
// every title ever earned). Spec: docs/spec/12-save-format.md ("Profile"). Headless.

class Profile(val bestiary: Map<String, Int> = emptyMap(), val titles: List<String> = emptyList())

/** The profile in a text; a missing or broken text gives an empty profile, and entries that make no sense are left out. */
fun parseProfile(text: String?): Profile {
    if (text.isNullOrEmpty()) return Profile()
    val doc = runCatching { Json.parseToJsonElement(text) }.getOrNull() as? JsonObject ?: return Profile()
    val version = doc["profile_version"] as? JsonPrimitive ?: return Profile()
    if (version.isString || version.content.toLongOrNull() != 1L) return Profile()
    val bestiary = java.util.TreeMap<String, Int>()
    (doc["bestiary"] as? JsonObject)?.forEach { (name, count) ->
        val n = (count as? JsonPrimitive)?.takeIf { !it.isString }?.content?.toLongOrNull()
        if (n != null && n >= 1) bestiary[name] = n.toInt()
    }
    val titles = ArrayList<String>()
    (doc["titles"] as? JsonArray)?.forEach { title ->
        val s = (title as? JsonPrimitive)?.takeIf { it.isString }?.content
        if (s != null && s !in titles) titles.add(s)
    }
    return Profile(bestiary, titles)
}

/** The profile after a game reports its bestiary and titles: the best count of every creature, every title ever earned. */
fun mergeProfile(profile: Profile, bestiary: Map<String, Int>, titles: List<String>): Profile {
    val merged = java.util.TreeMap(profile.bestiary)
    for ((name, count) in bestiary) if (count >= 1) merged[name] = maxOf(merged[name] ?: 0, count)
    val outTitles = ArrayList(profile.titles)
    for (title in titles) if (title !in outTitles) outTitles.add(title)
    return Profile(merged, outTitles)
}

fun profileToJson(profile: Profile): String =
    buildJsonObject {
        put("profile_version", 1)
        put("bestiary", buildJsonObject { for ((name, count) in profile.bestiary) put(name, count) })
        put("titles", JsonArray(profile.titles.map { JsonPrimitive(it) }))
    }.toString()
