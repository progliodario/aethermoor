package io.github.progliodario.aethermoor.core.audio

import kotlin.math.floor
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min

// The sound director: from a snapshot of the game each frame, the sound events to play, and the gain of the looping ambience of
// a place. Spec: docs/spec/14-audio.md ("What plays when"). Headless and free of randomness.

/** Something a creature did this frame (the simulation reports it): [kind] is hit, hurt, die, aggro or attack. */
data class SoundCue(
    val kind: String,
    val family: String,
    val x: Double,
    val y: Double,
    val crit: Boolean = false,
    val weak: Boolean = false,
)

data class PlayerSound(
    val hp: Long = 1,
    val maxHp: Long = 1,
    val level: Long = 1,
    /** 0 none, otherwise startup, active or recovery of an attack. */
    val phase: Int = 0,
    val strike: Boolean = false,
    val dodge: Boolean = false,
    val moving: Boolean = false,
    val x: Double = 0.0,
    val y: Double = 0.0,
    val surface: String = "grass",
    val saveCd: Long = 0,
)

data class PanelsOpen(
    val bag: Boolean = false,
    val map: Boolean = false,
    val journal: Boolean = false,
    val shop: Boolean = false,
    val board: Boolean = false,
    val travel: Boolean = false,
) {
    fun any() = bag || map || journal || shop || board || travel
}

data class SoundSnapshot(
    val frame: Long = 0,
    val player: PlayerSound = PlayerSound(),
    val cues: List<SoundCue> = emptyList(),
    /** How many things are in the bag. */
    val items: Long = 0,
    val gold: Long = 0,
    val mp: Long = 0,
    val weapon: String = "",
    val armor: String = "",
    val panels: PanelsOpen = PanelsOpen(),
    val dialogue: Boolean = false,
    /** Grows with every line of dialogue. */
    val line: Long = 0,
    /** The sum of the cursors of the menus. */
    val cursor: Long = 0,
    val questsStarted: Long = 0,
    val questsDone: Long = 0,
    val stones: Long = 0,
    val region: String = "",
    val todPm: Int = 0,
    val rainPm: Int = 0,
)

data class SoundEvent(val event: String, val volumePm: Int = 1000)

class SoundDirector {
    private var prev: SoundSnapshot? = null
    private var walked = 0.0
    private var sinceHeartbeat = HEARTBEAT_FRAMES

    /** One frame: the events to play. */
    fun update(s: SoundSnapshot): List<SoundEvent> {
        val out = ArrayList<SoundEvent>()
        fun emit(event: String, volume: Int = 1000) {
            out.add(SoundEvent(event, volume))
        }
        val p = s.player

        // What the creatures did this frame.
        for (cue in s.cues) {
            val dist = hypot(cue.x - p.x, cue.y - p.y)
            val volume = max(0, min(1000, 1000 - floor(dist * FALLOFF_PM_PER_TILE + 0.5).toInt()))
            if (cue.kind == "hurt") {
                emit("player.hurt")
            } else if (cue.kind == "parry") {
                emit("player.parry")
            } else if (volume >= MIN_AUDIBLE_PM) {
                emit("enemy.${cue.family}.${cue.kind}", volume)
            }
            if (cue.kind == "hit") {
                if (cue.crit) emit("crit")
                if (cue.weak) emit("weak")
            }
        }

        val before = prev
        if (before != null) {
            val pp = before.player
            // The player.
            if (p.phase != 0 && pp.phase == 0) emit(if (p.strike) "power" else "swing")
            if (p.dodge && !pp.dodge) emit("dodge")
            if (p.level > pp.level) emit("level_up")
            if (p.hp <= 0 && pp.hp > 0) emit("player.death")
            if (p.saveCd > pp.saveCd) emit("death_save")
            if (p.moving) {
                walked += hypot(p.x - pp.x, p.y - pp.y)
                if (walked >= STRIDE_TILES) {
                    walked -= STRIDE_TILES
                    emit("step.${p.surface}", 700)
                }
            } else {
                walked = 0.0
            }
            if (p.hp > 0 && p.hp * 4 < p.maxHp) {
                sinceHeartbeat++
                if (sinceHeartbeat >= HEARTBEAT_FRAMES) {
                    sinceHeartbeat = 0
                    emit("heartbeat", 800)
                }
            } else {
                sinceHeartbeat = HEARTBEAT_FRAMES
            }
            // The bag.
            val dItems = s.items - before.items
            val dGold = s.gold - before.gold
            val dHp = p.hp - pp.hp
            val shop = s.panels.shop
            when {
                dGold > 0 && dItems < 0 && shop -> emit("shop.sell")
                dGold < 0 && dItems > 0 -> emit("shop.buy")
                dGold > 0 -> emit("coin")
                dItems > 0 -> emit("pickup")
                dItems < 0 && dHp > 0 -> emit("use.heal")
                dItems < 0 && s.mp > before.mp -> emit("use.mana")
                dItems < 0 && !shop -> emit("use.other")
            }
            if (s.weapon != before.weapon) emit("equip.weapon")
            if (s.armor != before.armor) emit("equip.armor")
            // Panels, the cursor, the dialogue.
            fun panel(name: String, now: Boolean, was: Boolean) {
                if (now != was) emit("ui.${if (now) "open" else "close"}.$name")
            }
            panel("bag", s.panels.bag, before.panels.bag)
            panel("map", s.panels.map, before.panels.map)
            panel("journal", s.panels.journal, before.panels.journal)
            panel("shop", s.panels.shop, before.panels.shop)
            panel("board", s.panels.board, before.panels.board)
            panel("travel", s.panels.travel, before.panels.travel)
            if (s.dialogue != before.dialogue) {
                emit(if (s.dialogue) "dialogue.open" else "dialogue.close")
            } else if (s.dialogue && s.line != before.line) {
                emit("dialogue.next")
            }
            if (s.cursor != before.cursor && (s.dialogue || s.panels.any())) emit("ui.move")
            // The story and the world.
            if (s.questsStarted > before.questsStarted) emit("quest.accept")
            if (s.questsDone > before.questsDone) emit("quest.complete")
            if (s.stones > before.stones) emit("stone.wake")
            if (s.region != before.region) emit("region.enter")
            if (before.rainPm == 0 && s.rainPm > 0) {
                emit("rain.start")
            } else if (s.rainPm == 0 && before.rainPm > 0) {
                emit("rain.stop")
            }
            if (s.rainPm >= 700 && s.frame % THUNDER_PERIOD == THUNDER_AT) emit("thunder")
            if (before.todPm < 250 && s.todPm >= 250) emit("dawn")
            if (before.todPm < 750 && s.todPm >= 750) emit("nightfall")
        }
        prev = s
        return out
    }

    private companion object {
        const val STRIDE_TILES = 0.85
        const val HEARTBEAT_FRAMES = 70
        const val THUNDER_PERIOD = 1200L
        const val THUNDER_AT = 600L
        const val MIN_AUDIBLE_PM = 60
        const val FALLOFF_PM_PER_TILE = 70.0
    }
}

data class AmbienceEntry(val sound: String, val gainPm: Int, val `when`: String = "always")

class AmbienceRules(
    val rainLight: String,
    val rainHeavy: String,
    val silences: List<String>,
    val regions: Map<String, List<AmbienceEntry>>,
)

/** The gain (permille) of every looping sound for a place and a moment; silent loops are left out. */
fun ambienceGains(region: String, todPm: Int, rainPm: Int, rules: AmbienceRules): Map<String, Int> {
    val gains = LinkedHashMap<String, Int>()
    val day = todPm in 250..750
    for (entry in rules.regions[region] ?: emptyList()) {
        if ((entry.`when` == "day" && !day) || (entry.`when` == "night" && day)) continue
        gains[entry.sound] = max(gains[entry.sound] ?: 0, entry.gainPm)
    }
    if (rainPm > 0) {
        gains[rules.rainLight] = min(1000, rainPm)
        val heavy = max(0, rainPm - 500) * 2
        if (heavy > 0) gains[rules.rainHeavy] = min(1000, heavy)
        for (sound in gains.keys.toList()) {
            if (sound in rules.silences) gains[sound] = 0
        }
    }
    return gains.filterValues { it > 0 }
}
