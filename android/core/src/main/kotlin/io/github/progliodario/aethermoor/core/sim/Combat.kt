package io.github.progliodario.aethermoor.core.sim

import io.github.progliodario.aethermoor.core.Primary

// Combat data structures. Spec: docs/spec/05-combat-v1.md. Reference: tools/reference/combat.py.

data class SkillDef(
    val startup: Int = 6,
    val active: Int = 4,
    val recovery: Int = 10,
    val cooldown: Int = 24,
    val powerPct: Long = 100,
    val radiusX100: Int = 160,
    val angleDeg: Int = 110,
    /** Hits with matk instead of atk (spec 05, "Damage kind"). */
    val magical: Boolean = false,
    /** The element of its hits; none: the element of the weapon (spec 05, "Elements"). */
    val element: String = "none",
)

/** The dodge roll (spec 05, "Dodge roll"): from a skill of type "movement"; [enabled] is false when the protagonist has none. */
data class DodgeDef(
    val enabled: Boolean = false,
    val ticks: Int = 12,
    val speedMultX100: Int = 260,
    val iframes: Int = 14,
    val cooldown: Int = 40,
)

/** The power strike (spec 05, "Mana"): the second skill with a hitbox; [enabled] is false when the protagonist has none. */
data class StrikeDef(val enabled: Boolean = false, val skill: SkillDef = SkillDef(), val mp: Long = 10)

/** The rules of a gift (spec 18, "Gift rules"): percentages (100 is neutral) and the ticks of the death save (0: none). */
data class GiftDef(
    val mpRegenPct: Int = 100,
    val aggroPct: Int = 100,
    val healPct: Int = 100,
    val dodgeCooldownPct: Int = 100,
    val deathSaveTicks: Int = 0,
    /** The attack of the companion, in percent (a gift of command), and what a kill of the companion adds to its bond (a gift of taming). */
    val companionAtkPct: Int = 100,
    val bondGain: Int = 1,
    /**
     * Taming (spec 18): a creature at [tameHpPct] percent of its health or less, within [tameRangeX100], can be tamed, and the bond of the
     * companion grows by [tameBond]; 0 percent: the protagonist cannot tame.
     */
    val tameHpPct: Int = 0,
    val tameRangeX100: Int = 0,
    val tameBond: Int = 0,
    /** The pocket of Yuki: the chance in permille that an item used stays in the bag. */
    val pocketKeepPm: Int = 0,
    /** Above 0 a tamed creature stays as the tamed friend (spec 10), hitting with this percent of its attack. */
    val friendAtkPct: Int = 0,
)

/** [pick]: one of a list (spec 05, "Loot"): the item or one of these, drawn when it drops. */
data class DropDef(val item: String, val qtyMin: Long, val qtyMax: Long, val weightPm: Long, val pick: List<String> = emptyList())

data class BehaviorDef(
    val aggroX100: Int = 600,
    val leashX100: Int = 900,
    val attackRangeX100: Int = 120,
    val hitRangeX100: Int = 150,
    val windupTicks: Int = 18,
    val recoveryTicks: Int = 30,
    /** The behavior document, e.g. base:behavior/guardian (presentation: the guardian bar). */
    val id: String = "",
)

data class EnemyDef(
    val id: String = "",
    val art: String = "",
    val level: Long = 1,
    val hp: Long = 1,
    val atk: Long = 0,
    val def: Long = 0,
    val xp: Long = 0,
    val radiusX100: Int = 35,
    val speedX100: Int = 250,
    val drops: List<DropDef> = emptyList(),
    val behavior: BehaviorDef = BehaviorDef(),
    /** The elements (spec 05, "Elements"): the creature's own, and its weaknesses and resistances in permille. */
    val element: String = "none",
    /** The share of the health that fills the stagger bar; 0: never (spec 05, "Stagger"). */
    val staggerPct: Long = 40,
    val weaknessesPm: Map<String, Long> = emptyMap(),
    /** The family of voices of the creature (spec 14). */
    val sound: String = "",
    /** More of every plain drop in a season (spec 05, "Loot"): season -> how many more. */
    val seasonBonus: Map<String, Int> = emptyMap(),
)

data class EnemySpawn(val def: EnemyDef, val x: Float, val y: Float)

data class PlayerSetup(
    val base: Primary = Primary(),
    val growthPm: Primary = Primary(),
    val weaponAtk: Long = 0,
    val weaponMatk: Long = 0,
)

/** One effect of using an item (spec 06): "heal" with an [amount]. */
/** [ticks]: how long it lasts (fortify, spec 06). */
class ItemEffect(val effect: String, val amount: Long, val ticks: Int = 0)

/** An item of the pack (spec 06): its effects when used, its price and, for equipment, its statistics. */
class ItemDef(
    val effects: List<ItemEffect> = emptyList(),
    val kind: String = "",
    val price: Long = 0,
    /** 0: the default of the kind. */
    val stackMax: Int = 0,
    val weapon: WeaponStats? = null,
    val armor: ArmorStats? = null,
    /** An accessory (spec 06, "Equipment"): flat bonuses while it is worn. */
    val accessory: AccessoryStats? = null,
    /** A rune (spec 06, "Runes"): engraved on the worn weapon at its station. */
    val rune: RuneStats? = null,
    /** An affix (spec 06, "Affixes"): the flat bonuses of a weapon or an armor while it is worn, like an accessory's. */
    val affix: AccessoryStats? = null,
    /** How strong the affix comes out when the piece is found on a creature (spec 06, "Rolled affixes"): (min, max) percent; null: never rolled. */
    val affixRoll: Pair<Int, Int>? = null,
    /** A piece of furniture (spec 06, "Furniture"): placed on a spot of the home. */
    val furniture: FurnitureStats? = null,
    /** Tempers the affix of a worn piece next to this station (spec 06, "Tempering"); empty: anywhere; null: not a tempering item. */
    val temperStation: String? = null,
)

/** [element]: the element the weapon hits with, "none" to keep its own; [station]: the art of the prop it is engraved next to, empty: anywhere. */
class RuneStats(val element: String = "none", val atk: Long = 0, val matk: Long = 0, val station: String = "")

/** What a piece of furniture adds while it stands in the home, like a title (spec 11, "Titles with effects"); [art] is how it is drawn. */
class FurnitureStats(
    val art: String = "",
    val atkPct: Long = 0,
    val gatherBonus: Long = 0,
    val craftBonus: Long = 0,
    val parryBonus: Long = 0,
    val xpPct: Long = 0,
    val finePm: Long = 0,
)

/** The `rune` block of an item. */
fun runeOf(o: kotlinx.serialization.json.JsonObject): RuneStats {
    fun n(k: String) = (o[k] as? kotlinx.serialization.json.JsonPrimitive)?.content?.toLongOrNull() ?: 0L
    fun s(k: String, d: String) = (o[k] as? kotlinx.serialization.json.JsonPrimitive)?.content ?: d
    return RuneStats(s("element", "none"), n("atk"), n("matk"), s("station", ""))
}

/** The `furniture` block of an item. */
fun furnitureOf(o: kotlinx.serialization.json.JsonObject): FurnitureStats {
    fun n(k: String) = (o[k] as? kotlinx.serialization.json.JsonPrimitive)?.content?.toLongOrNull() ?: 0L
    val art = (o["art"] as? kotlinx.serialization.json.JsonPrimitive)?.content ?: ""
    return FurnitureStats(art, n("atk_pct"), n("gather_bonus"), n("craft_bonus"), n("parry_bonus"), n("xp_pct"), n("fine_pm"))
}

class WeaponStats(val atk: Long, val matk: Long, val element: String = "none")

class ArmorStats(val def: Long, val mdef: Long)

class AccessoryStats(
    val atk: Long = 0,
    val matk: Long = 0,
    val def: Long = 0,
    val mdef: Long = 0,
    val maxHp: Long = 0,
    val critPm: Long = 0,
    /** The share of the damage of every hit given back to the player, in permille. */
    val drainPm: Long = 0,
) {
    /** Every bonus times [pct] percent, field by field (spec 06, "Rolled affixes"). */
    fun scaled(pct: Long): AccessoryStats = AccessoryStats(
        atk * pct / 100,
        matk * pct / 100,
        def * pct / 100,
        mdef * pct / 100,
        maxHp * pct / 100,
        critPm * pct / 100,
        drainPm * pct / 100,
    )
}

/** The bonuses of an accessory document (`accessory` of an item). */
fun accessoryOf(o: kotlinx.serialization.json.JsonObject): AccessoryStats {
    fun n(k: String) = (o[k] as? kotlinx.serialization.json.JsonPrimitive)?.content?.toLongOrNull() ?: 0L
    return AccessoryStats(n("atk"), n("matk"), n("def"), n("mdef"), n("max_hp"), n("crit_pm"), n("drain_pm"))
}

/** What a shop sells: prices in permille of the base price. */
/** [renownStepPm]: what every quest finished in the region takes off the prices, up to [renownMaxPm] (spec 07, "Renown"). */
/** [marketSwingPm]: how far the prices swing with the day (spec 06, "Market days"); [renownStock]: item and renown, sold only to somebody that well known. */
class ShopDef(
    val pricePm: Int,
    val stock: List<String>,
    val renownStepPm: Int = 0,
    val renownMaxPm: Int = 0,
    val marketSwingPm: Int = 0,
    val renownStock: List<Pair<String, Int>> = emptyList(),
    /** The glut (spec 06, "Glut"): what every one of an item sold the same day takes off its price, and the least it pays, in permille. */
    val glutStepPm: Int = 0,
    val glutFloorPm: Int = 1000,
)

/** Farming (spec 06, "Farming"): what a seed grows into, how much and in how many ticks. */
class FarmCrop(val seed: String, val crop: String, val qtyMin: Long, val qtyMax: Long, val growTicks: Long)

/** The plot prop, its reach and the crops in the order of the data (a bare plot takes the first seed the bag holds). */
/** [seasonGrowPm]: the growing of a seed sown in each season, in permille (spec 06, "Seasons on the plots"). */
class FarmingDef(val plot: String, val reachX100: Int, val crops: List<FarmCrop>, val rainGrowCutPm: Int = 0, val seasonGrowPm: Map<String, Int> = emptyMap())

/** A companion that follows the player and fights (spec 10). [name] is an $i18n: key, [art] the creature art it is drawn with. */
class CompanionDef(
    val id: String = "",
    val name: String = "",
    val art: String = "",
    val scalePct: Int = 100,
    val atkBase: Long = 0,
    val atkPerLevel: Long = 0,
    val rangeX100: Int = 300,
    val cooldownTicks: Int = 60,
    val speedX100: Int = 320,
    val followX100: Int = 220,
    /** Care (spec 10): from [careBond] on, every [careTicks] (0: never) it heals the player by [carePct] of the maximum health. */
    val careBond: Int = 0,
    val careTicks: Int = 0,
    val carePct: Int = 0,
    /** Moments of the bond (spec 10): at this bond the companion shows a line, once a game ($i18n: keys). Presentation. */
    val moments: List<Pair<Int, String>> = emptyList(),
)

/** A crafting recipe (spec 06, "Crafting"). */
/** [station]: the art of the prop it must be made next to (spec 06, "Stations"); empty: anywhere. */
/** [finePm]: the chance in permille that it comes out fine (spec 06, "Quality"), 0: never; [fineItem]: what a fine one gives instead of the output (empty: one more of it). */
class RecipeDef(
    val id: String,
    val output: String,
    val outputQty: Long,
    val inputs: List<Pair<String, Long>>,
    val station: String = "",
    val finePm: Long = 0,
    val fineItem: String = "",
    /** The story flag that teaches it (spec 06, "Recipe book"); empty: always known. */
    val requiresFlag: String = "",
)

/** A title (spec 11): earned when its condition holds. [kind]: kills, kills_of, level, species or quests; [enemy] for kills_of only. */
/**
 * A talent (spec 11, "Talents"): every rank multiplies a kind of stat. [stat]: attack, health, mana, defense, magic, critical or speed;
 * or an ability (spec 11, "Abilities"): riposte, kill_heal, kill_mana or whirl, whose power is [pctPerRank] times the rank.
 */
class TalentDef(
    val id: String,
    val name: String,
    val stat: String,
    val pctPerRank: Long,
    val maxRank: Int,
    val requiresTalent: String = "",
    val requiresRank: Int = 0,
    /** An active ability (spec 11, "Active abilities"; stat burst or mend): used on command, for mana, then it waits; a burst reaches [activeRadiusX100]. */
    val hasActive: Boolean = false,
    val activeMp: Long = 0,
    val activeCooldown: Int = 0,
    val activeRadiusX100: Int = 0,
)

class TitleDef(
    val id: String,
    val name: String,
    val kind: String,
    val count: Long,
    val enemy: String = "",
    val atkPct: Long = 0,
    /** One more of every drop gathered, and more of the output of every recipe, while the title is earned. */
    val gatherBonus: Long = 0,
    val craftBonus: Long = 0,
    /** Ticks added to the parry window, and percent more experience from a kill. */
    val parryBonus: Long = 0,
    val xpPct: Long = 0,
    /** Permille added to the chance of a fine piece (spec 06, "Quality"). */
    val finePm: Long = 0,
)

/** A prop that can be gathered from (spec 06, "Gathering"). */
class GatherDrop(val item: String, val qtyMin: Long, val qtyMax: Long, val weightPm: Long)

/** [sound]: plant, wood, stone or water, the sound of gathering. */
/** [seasonBonus]: more of every drop found in a season (spec 06, "Seasons of the gathering"). */
class GatherNode(val sound: String, val cooldownTicks: Int, val reachX100: Int, val drops: List<GatherDrop>, val seasonBonus: Map<String, Int> = emptyMap())

class CombatSetup(
    val enabled: Boolean = false,
    val player: PlayerSetup = PlayerSetup(),
    val skill: SkillDef = SkillDef(),
    val spawns: List<EnemySpawn> = emptyList(),
    /** table[level - 1] = XP to go from `level` to `level + 1`. */
    val xpTable: List<Long> = emptyList(),
    val seed: ULong = 0uL,
    val startLevel: Int = 1,
    val story: StorySetup = StorySetup(),
    /** Items owned in a new game. */
    val startInventory: Map<String, Long> = emptyMap(),
    /** The enemies of the fauna of a streamed world, by ID. */
    val streamEnemies: Map<String, EnemyDef> = emptyMap(),
    /** The props that can be gathered from, by art ID (spec 06, "Gathering"). */
    val gatherNodes: Map<String, GatherNode> = emptyMap(),
    /** The plots and the crops (spec 06, "Farming"); null: no farming. */
    val farming: FarmingDef? = null,
    /** The chest prop and its reach (spec 06, "Chests"); empty: no chests. */
    val chestArt: String = "",
    val chestReachX100: Int = 200,
    /** The furniture spot prop and its reach (spec 06, "Furniture"); empty: no furniture. */
    val homeSpot: String = "",
    val homeReachX100: Int = 200,
    /** Crafting recipes, in the order of the data (spec 06, "Crafting"). */
    val recipes: List<RecipeDef> = emptyList(),
    /** The companion of the protagonist (spec 10), or null. */
    val companion: CompanionDef? = null,
    /** The titles that can be earned (spec 11), in order of rank. */
    val titles: List<TitleDef> = emptyList(),
    /** Items with a `use` block, by item ID (spec 06). */
    val items: Map<String, ItemDef> = emptyMap(),
    /** The weapon and the armor worn in a new game (item ids, or empty). */
    val startWeapon: String = "",
    val startArmor: String = "",
    /** The shop of fixed maps and scenarios (streamed worlds use their regions). */
    val shop: ShopDef? = null,
    /** The dodge roll of the protagonist (spec 05). */
    val dodge: DodgeDef = DodgeDef(),
    /** The power strike of the protagonist (spec 05). */
    val strike: StrikeDef = StrikeDef(),
    /** The gift rules of the protagonist (spec 18). */
    val gift: GiftDef = GiftDef(),
    /** The rain of a world without a clock (the conformance scenarios; spec 08, "Rain hides you"). */
    val rainPm: Int = 0,
    val rainAggroCutPm: Int = 0,
    /** How much full rain slows the creatures (spec 08, "Rain slows"). */
    val rainSlowPm: Int = 0,
    /** The same for the night (spec 08, "The night hides you"). */
    val lightPm: Int = 1000,
    val nightAggroCutPm: Int = 0,
    /** The wind of a world without a clock, and how much a full wind speeds the player (spec 08, "Wind"). */
    val windPm: Int = 0,
    val windHastePm: Int = 0,
    /** The fog of a world without a clock, and how much a full fog shortens the aggro distance (spec 08, "Fog"). */
    val fogPm: Int = 0,
    val fogAggroCutPm: Int = 0,
    /** The goods of the season of a world without a clock (spec 06, "Goods of the season"). */
    val seasonStock: List<String> = emptyList(),

    /** What the season of a world without a clock does to the creatures (spec 08, "Seasons and the creatures"). */
    val seasonSlowPm: Int = 0,
    val seasonAggroCutPm: Int = 0,
    /** The lightning of a storm of a world without a clock (spec 08, "Lightning"). */
    val lightningTicks: Int = 0,
    val lightningPct: Int = 0,
    val lightningRangeX100: Int = 0,
    /** The tags (spec 11, "Tags"): earned like titles, one worn at a time; in the order of the data. */
    val tags: List<TitleDef> = emptyList(),
    /** Percent added to the maximum health, from the profile of past games (spec 11, "Echoes"). */
    var echoPct: Int = 0,
    /** The talents that can be learned, in the order of the data (spec 11, "Talents"), and the points a level gives. */
    val talents: List<TalentDef> = emptyList(),
    val talentPointsPerLevel: Int = 1,
    /** The region of a world without regions: the renown is counted by region (spec 07, "Renown"). */
    val region: String = "",
    /** The season of a world without a clock (spec 06, "Seasons on the plots"); empty: none. */
    val season: String = "",
    /** The length of a day of a world without a clock, for the market (spec 06, "Market days"); 0: always day 1. */
    val dayTicks: Int = 0,
    /** The shops of other regions of a world without regions, by region (spec 06, "Goods from afar"). */
    val farShops: Map<String, ShopDef> = emptyMap(),
)

enum class AttackPhase { NONE, STARTUP, ACTIVE, RECOVERY }

enum class EnemyState(val id: String) { IDLE("idle"), CHASE("chase"), ATTACK("attack"), RETURN("return"), DEAD("dead") }

/** Primary stats at [level] (spec 05): base + growth_pm * (level - 1) / 1000. */
fun primaryAtLevel(setup: PlayerSetup, level: Long): Primary {
    fun stat(base: Long, growthPm: Long) = base + growthPm * (level - 1) / 1000
    val b = setup.base
    val g = setup.growthPm
    return Primary(
        stat(b.str, g.str),
        stat(b.vit, g.vit),
        stat(b.dex, g.dex),
        stat(b.agi, g.agi),
        stat(b.int, g.int),
        stat(b.wis, g.wis),
        stat(b.luk, g.luk),
    )
}
