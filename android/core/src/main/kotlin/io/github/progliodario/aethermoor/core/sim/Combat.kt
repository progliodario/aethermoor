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

class WeaponStats(val atk: Long, val matk: Long)

class ArmorStats(val def: Long, val mdef: Long)

/** What a shop sells: prices in permille of the base price. */
class ShopDef(val pricePm: Int, val stock: List<String>)

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
    /** Items with a `use` block, by item ID (spec 06). */
    val items: Map<String, ItemDef> = emptyMap(),
    /** The weapon and the armor worn in a new game (item ids, or empty). */
    val startWeapon: String = "",
    val startArmor: String = "",
    /** The shop of fixed maps and scenarios (streamed worlds use their regions). */
    val shop: ShopDef? = null,
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
