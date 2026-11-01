package io.github.progliodario.aethermoor.core

// Gameplay formulas. Spec: docs/spec/04-stats-and-combat.md. Reference: tools/reference/rules.py.
// Integer math only; every division is a floor division of non-negative values.

data class Primary(
    val str: Long = 0,
    val vit: Long = 0,
    val dex: Long = 0,
    val agi: Long = 0,
    val int: Long = 0,
    val wis: Long = 0,
    val luk: Long = 0,
)

data class Equipment(
    val hp: Long = 0,
    val mp: Long = 0,
    val weaponAtk: Long = 0,
    val weaponMatk: Long = 0,
    val armorDef: Long = 0,
    val armorMdef: Long = 0,
)

data class DerivedStats(
    val maxHp: Long,
    val maxMp: Long,
    val atk: Long,
    val matk: Long,
    val def: Long,
    val mdef: Long,
    val moveSpeedX100: Long,
    val attackSpeedPm: Long,
    val critChancePm: Long,
    val critMultPm: Long,
    val statusResistPm: Long,
    val mpRegenX100: Long,
)

fun derivedStats(level: Long, p: Primary, eq: Equipment): DerivedStats =
    DerivedStats(
        maxHp = 50 + p.vit * 12 + level * 8 + eq.hp,
        maxMp = 20 + p.wis * 8 + p.int * 3 + level * 3 + eq.mp,
        atk = p.str * 2 + p.dex / 2 + eq.weaponAtk,
        matk = p.int * 2 + p.wis / 2 + eq.weaponMatk,
        def = p.vit * 12 / 10 + eq.armorDef,
        mdef = p.wis * 12 / 10 + eq.armorMdef,
        moveSpeedX100 = 400 * (1000 + minOf(p.agi * 2, 400L)) / 1000,
        attackSpeedPm = minOf(1000 + p.agi * 4 + p.dex * 2, 2000L),
        critChancePm = minOf(50 + p.luk * 15 + p.dex * 10, 600L),
        critMultPm = minOf(1500 + p.luk * 3, 2500L),
        statusResistPm = minOf(p.wis * 3 + p.luk, 750L),
        mpRegenX100 = 50 + p.wis * 5,
    )

data class DamageInput(
    val atk: Long,
    val powerPct: Long = 100,
    val defTarget: Long = 0,
    val elemMultPm: Long = 1000,
    val penPm: Long = 0,
    val lvlAttacker: Long = 1,
    val lvlTarget: Long = 1,
    val variancePm: Long = 1000,
    val crit: Boolean = false,
    val critMultPm: Long = 1500,
    val buffModPm: Long = 1000,
)

fun damage(input: DamageInput): Long {
    val raw = input.atk * input.powerPct / 100
    val elem = raw * input.elemMultPm / 1000
    val defEff = input.defTarget * (1000 - input.penPm) / 1000
    val mitigated = elem * 100 / (100 + defEff)
    val lvlMod = clampLong(1000 + 30 * (input.lvlAttacker - input.lvlTarget), 700, 1300)
    var x = mitigated * lvlMod / 1000
    x = x * input.variancePm / 1000
    x = x * (if (input.crit) input.critMultPm else 1000L) / 1000
    x = x * input.buffModPm / 1000
    return maxOf(1L, x)
}

fun xpGain(enemyXp: Long, lvlEnemy: Long, lvlPlayer: Long): Long {
    val factor = clampLong(1000 + 100 * (lvlEnemy - lvlPlayer), 100, 1500)
    return enemyXp * factor / 1000
}
