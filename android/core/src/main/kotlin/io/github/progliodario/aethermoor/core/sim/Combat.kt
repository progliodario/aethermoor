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
)

data class DropDef(val item: String, val qtyMin: Long, val qtyMax: Long, val weightPm: Long)

data class BehaviorDef(
    val aggroX100: Int = 600,
    val leashX100: Int = 900,
    val attackRangeX100: Int = 120,
    val hitRangeX100: Int = 150,
    val windupTicks: Int = 18,
    val recoveryTicks: Int = 30,
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
)

data class EnemySpawn(val def: EnemyDef, val x: Float, val y: Float)

data class PlayerSetup(
    val base: Primary = Primary(),
    val growthPm: Primary = Primary(),
    val weaponAtk: Long = 0,
    val weaponMatk: Long = 0,
)

/** One effect of using an item (spec 06): "heal" with an [amount]. */
class ItemEffect(val effect: String, val amount: Long)

/** An item of the pack (spec 06): its effects when used, its price and, for equipment, its statistics. */
class ItemDef(
    val effects: List<ItemEffect> = emptyList(),
    val kind: String = "",
    val price: Long = 0,
    /** 0: the default of the kind. */
    val stackMax: Int = 0,
    val weapon: WeaponStats? = null,
    val armor: ArmorStats? = null,
)

class WeaponStats(val atk: Long, val matk: Long, val element: String = "none")

class ArmorStats(val def: Long, val mdef: Long)

/** What a shop sells: prices in permille of the base price. */
class ShopDef(val pricePm: Int, val stock: List<String>)

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
)

/** A crafting recipe (spec 06, "Crafting"). */
class RecipeDef(val id: String, val output: String, val outputQty: Long, val inputs: List<Pair<String, Long>>)

/** A title (spec 11): earned when its condition holds. [kind]: kills, kills_of, level, species or quests; [enemy] for kills_of only. */
/** A talent (spec 11, "Talents"): every rank multiplies a kind of stat. [stat]: attack, health, mana or defense. */
class TalentDef(val id: String, val name: String, val stat: String, val pctPerRank: Long, val maxRank: Int)

class TitleDef(val id: String, val name: String, val kind: String, val count: Long, val enemy: String = "", val atkPct: Long = 0)

/** A prop that can be gathered from (spec 06, "Gathering"). */
class GatherDrop(val item: String, val qtyMin: Long, val qtyMax: Long, val weightPm: Long)

/** [sound]: plant, wood or stone, the sound of gathering. */
class GatherNode(val sound: String, val cooldownTicks: Int, val reachX100: Int, val drops: List<GatherDrop>)

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
    /** Percent added to the maximum health, from the profile of past games (spec 11, "Echoes"). */
    var echoPct: Int = 0,
    /** The talents that can be learned, in the order of the data (spec 11, "Talents"), and the points a level gives. */
    val talents: List<TalentDef> = emptyList(),
    val talentPointsPerLevel: Int = 1,
)

enum class AttackPhase { NONE, STARTUP, ACTIVE, RECOVERY }

enum class EnemyState(val id: String) { IDLE("idle"), CHASE("chase"), ATTACK("attack"), RETURN("return"), DEAD("dead") }

/** Primary stats at [level] (spec 05): base + growth_pm * (level - 1) / 1000. */
fun primaryAtLevel(setup: PlayerSetup, level: Long): Primary {
    fun stat(base: Long, growthPm: Long) = base + growthPm * (level - 1) / 1000
    val b = setup.base
    val g = setup.growthPm
    return Primary(
        stat(b.str, g.str), stat(b.vit, g.vit), stat(b.dex, g.dex), stat(b.agi, g.agi),
        stat(b.int, g.int), stat(b.wis, g.wis), stat(b.luk, g.luk),
    )
}
