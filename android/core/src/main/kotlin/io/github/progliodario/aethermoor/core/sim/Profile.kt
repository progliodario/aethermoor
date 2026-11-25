package io.github.progliodario.aethermoor.core.sim

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

// The profile: what is kept across games in `profile.json` next to the settings (the best count of every creature killed and
// every title ever earned). Spec: docs/spec/12-save-format.md ("Profile"). Headless.

/** [lives]: the games that were reincarnated (spec 11, "Reincarnation"); [heirloom]: gold that waits for the next new game ("Heirloom"), [heirloomItem] the weapon that waits too (empty: none). */
class Profile(
    val bestiary: Map<String, Int> = emptyMap(),
    val titles: List<String> = emptyList(),
    val lives: Int = 0,
    val heirloom: Long = 0,
    val heirloomItem: String = "",
)

/** The profile in a text; a missing or broken text gives an empty profile, and entries that make no sense are left out. */
fun parseProfile(text: String?): Profile {
    if (text.isNullOrEmpty()) return Profile()
    val doc = runCatching { Json.parseToJsonElement(text) }.getOrNull() as? JsonObject ?: return Profile()
    val version = doc["profile_version"] as? JsonPrimitive ?: return Profile()
    if (version.isString || version.content.toLongOrNull() != 1L) return Profile()
    val lives = numberOf(doc["lives"])?.takeIf { it >= 0 }?.toInt() ?: 0
    val heirloom = numberOf(doc["heirloom"])?.takeIf { it >= 0 } ?: 0L
    val item = textOf(doc["heirloom_item"]) ?: ""
    return Profile(parseBestiary(doc["bestiary"] as? JsonObject), parseTitles(doc["titles"] as? JsonArray), lives, heirloom, item)
}

/** A number of the profile (not a text): null when it is not one. */
private fun numberOf(element: JsonElement?): Long? = (element as? JsonPrimitive)?.takeIf { !it.isString }?.content?.toLongOrNull()

/** A text of the profile: null when it is not one. */
private fun textOf(element: JsonElement?): String? = (element as? JsonPrimitive)?.takeIf { it.isString }?.content

/** The creatures and their counts, in the order of their names; a count below 1 or not a number is dropped. */
private fun parseBestiary(bestiary: JsonObject?): java.util.TreeMap<String, Int> {
    val out = java.util.TreeMap<String, Int>()
    bestiary?.forEach { (name, count) ->
        val n = numberOf(count)
        if (n != null && n >= 1) out[name] = n.toInt()
    }
    return out
}

/** The titles, once each, in their order; what is not a text is dropped. */
private fun parseTitles(titles: JsonArray?): ArrayList<String> {
    val out = ArrayList<String>()
    titles?.forEach { title ->
        val s = textOf(title)
        if (s != null && s !in out) out.add(s)
    }
    return out
}

/** The profile after a game reports its bestiary and titles: the best count of every creature, every title ever earned. */
fun mergeProfile(profile: Profile, bestiary: Map<String, Int>, titles: List<String>): Profile {
    val merged = java.util.TreeMap(profile.bestiary)
    for ((name, count) in bestiary) if (count >= 1) merged[name] = maxOf(merged[name] ?: 0, count)
    val outTitles = ArrayList(profile.titles)
    for (title in titles) if (title !in outTitles) outTitles.add(title)
    return Profile(merged, outTitles, profile.lives, profile.heirloom, profile.heirloomItem)
}

/**
 * The profile after a game of [level] with [gold] and [weapon] in hand is reincarnated: one more past life, half of the gold kept for the next new game,
 * and the weapon too (it replaces one already waiting; an empty one keeps it); null when the level is below 10.
 */
fun reincarnate(profile: Profile, level: Long, gold: Long = 0, weapon: String = ""): Profile? =
    if (level < 10) {
        null
    } else {
        Profile(profile.bestiary, profile.titles, profile.lives + 1, profile.heirloom + maxOf(0L, gold) * 50 / 100, weapon.ifEmpty { profile.heirloomItem })
    }

/** A new game takes the heirloom: the gold it starts with (the weapon is [Profile.heirloomItem], read before), and the profile with nothing left waiting. */
fun claimHeirloom(profile: Profile): Pair<Long, Profile> = Pair(profile.heirloom, Profile(profile.bestiary, profile.titles, profile.lives, 0, ""))

/** The percent of maximum health that the profile gives to every game: one for each title (up to 15), three for each past life (up to 10). */
fun profileEchoPct(profile: Profile, deeds: Int = 0): Int = minOf(profile.titles.size, 15) + 3 * minOf(profile.lives, 10) + maxOf(0, deeds)

fun profileToJson(profile: Profile): String =
    buildJsonObject {
        put("profile_version", 1)
        put("bestiary", buildJsonObject { for ((name, count) in profile.bestiary) put(name, count) })
        put("titles", JsonArray(profile.titles.map { JsonPrimitive(it) }))
        put("lives", profile.lives)
        put("heirloom", profile.heirloom)
        if (profile.heirloomItem.isNotEmpty()) put("heirloom_item", profile.heirloomItem)
    }.toString()

/** A deed (spec 11, "Deeds"): a fact about all the games, read from the profile. [kind] is `kills`, `kinds`, `titles` or `lives` (with [count]),
 *  `defeated` (every creature of [list]) or `earned` (every title of [list]); [name] and [text] are for the clients. */
class DeedDef(
    val id: String,
    val kind: String,
    val count: Long = 0,
    val list: List<String> = emptyList(),
    val name: String = "",
    val text: String = "",
    /** The gift every new game finds once the deed is done (spec 11, "Gifts of the deeds"); empty: none. */
    val rewardItem: String = "",
    val rewardQty: Long = 0,
)

/** The deeds of a text: the array, or the object of `data/base/deeds.json` with its `deeds`; a broken text has none. */
fun parseDeeds(text: String?): List<DeedDef> {
    if (text.isNullOrEmpty()) return emptyList()
    val doc = runCatching { Json.parseToJsonElement(text) }.getOrNull() ?: return emptyList()
    val list = (doc as? JsonArray) ?: ((doc as? JsonObject)?.get("deeds") as? JsonArray) ?: return emptyList()
    return list.mapNotNull { element ->
        val d = element as? JsonObject ?: return@mapNotNull null
        val id = (d["id"] as? JsonPrimitive)?.takeIf { it.isString }?.content ?: return@mapNotNull null
        fun str(key: String) = (d[key] as? JsonPrimitive)?.takeIf { it.isString }?.content ?: ""
        val count = (d["count"] as? JsonPrimitive)?.takeIf { !it.isString }?.content?.toLongOrNull() ?: 0L
        val names = listOf("enemies", "titles").flatMap { key ->
            (d[key] as? JsonArray)?.mapNotNull { (it as? JsonPrimitive)?.takeIf { p -> p.isString }?.content } ?: emptyList()
        }
        val reward = d["reward"] as? JsonObject
        val rewardItem = (reward?.get("item") as? JsonPrimitive)?.takeIf { it.isString }?.content ?: ""
        val rewardQty = (reward?.get("qty") as? JsonPrimitive)?.takeIf { !it.isString }?.content?.toLongOrNull() ?: 0L
        DeedDef(id, str("kind"), count, names, str("name"), str("text"), rewardItem, rewardQty)
    }
}

/** The deeds the profile has done, in the order of [defs]; a kind the rules do not know is never done. */
fun profileDeeds(profile: Profile, defs: List<DeedDef>): List<String> =
    defs.filter { deed ->
        when (deed.kind) {
            "kills" -> profile.bestiary.values.sumOf { it.toLong() } >= deed.count
            "kinds" -> profile.bestiary.size.toLong() >= deed.count
            "titles" -> profile.titles.size.toLong() >= deed.count
            "lives" -> profile.lives.toLong() >= deed.count
            "defeated" -> deed.list.all { (profile.bestiary[it] ?: 0) >= 1 }
            "earned" -> deed.list.all { it in profile.titles }
            else -> false
        }
    }.map { it.id }

/** The gifts of the deeds done, which every new game finds in its bag (spec 11, "Gifts of the deeds"): item -> quantity, in item order. */
fun profileDeedGifts(profile: Profile, defs: List<DeedDef>): Map<String, Long> {
    val done = profileDeeds(profile, defs).toSet()
    val gifts = java.util.TreeMap<String, Long>()
    for (deed in defs) {
        if (deed.id in done && deed.rewardItem.isNotEmpty() && deed.rewardQty > 0) gifts[deed.rewardItem] = (gifts[deed.rewardItem] ?: 0L) + deed.rewardQty
    }
    return gifts
}
