package io.github.progliodario.aethermoor.core.sim

import io.github.progliodario.aethermoor.core.DamageInput
import io.github.progliodario.aethermoor.core.DerivedStats
import io.github.progliodario.aethermoor.core.Equipment
import io.github.progliodario.aethermoor.core.fnv1a64
import io.github.progliodario.aethermoor.core.hash64
import io.github.progliodario.aethermoor.core.mix64
import io.github.progliodario.aethermoor.core.Offer
import io.github.progliodario.aethermoor.core.Settlement
import io.github.progliodario.aethermoor.core.TimeSample
import io.github.progliodario.aethermoor.core.damage
import io.github.progliodario.aethermoor.core.deriveStream
import io.github.progliodario.aethermoor.core.derivedStats
import io.github.progliodario.aethermoor.core.explore
import io.github.progliodario.aethermoor.core.spawnerEnemyAt
import io.github.progliodario.aethermoor.core.offersFor
import io.github.progliodario.aethermoor.core.personPlacement
import io.github.progliodario.aethermoor.core.rankIndex
import io.github.progliodario.aethermoor.core.regionAt
import io.github.progliodario.aethermoor.core.resolveOffer
import io.github.progliodario.aethermoor.core.sampleTime
import io.github.progliodario.aethermoor.core.seasonIndexOf
import io.github.progliodario.aethermoor.core.settlementContaining
import io.github.progliodario.aethermoor.core.xpGain
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.floor
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt

// The world: map, player, enemies, combat and camera. Spec: docs/spec/02, 03 and 05.
// Keep this file in step with desktop/src/sim/world.cpp: same operations, same order, same random draws.

private const val PLAYER_HIT_IFRAMES = 45

// The parry (spec 05, "Parry"): the window, the wait before the next one, what it does to the attacker, the safety it gives.
private const val PARRY_TICKS = 14

// The companion (spec 10): it never comes farther than this from the player, and its body is this big.
private const val COMPANION_LEASH = 8f
private const val COMPANION_RADIUS = 0.25f
private const val PARRY_COOLDOWN = 70
private const val PARRY_STUN = 60
private const val STAGGER_TICKS = 120 // spec 05, "Stagger"
private const val STAGGER_DAMAGE_PCT = 125L
private const val PLAYER_BURN_PERIOD = 30 // spec 05, "Status effects on the player"
private const val PLAYER_BURN_PCT = 2
private const val PARRY_IFRAMES = 20
private const val RESPAWN_IFRAMES = 90
private const val ATTACK_MOVE_MULT = 0.5f
private const val MAX_LEVEL = 99L
private const val RETURN_ARRIVAL = 0.1f
private const val HIT_FLASH_TICKS = 6
private const val NPC_RADIUS = 0.3f

class Player(var position: Vec2) {
    var moving = false
    var facingLeft = false

    /** Ticks since the current clip started. */
    var clipTick = 0

    // Combat (only meaningful when combat is enabled).
    var facing = Vec2(1f, 0f)
    var hp = 1L
    var level = 1L
    var xp = 0L
    var deaths = 0
    var kills = 0
    var iframes = 0
    var cooldown = 0
    var phase = AttackPhase.NONE
    var phaseTick = 0

    /** Mana in units of 1/6000 of a point (spec 05, "Mana"), and whether the swing in progress is the power strike. Not saved. */
    var mpU = 0L
    var usingStrike = false

    /** The dodge roll (spec 05): ticks left, ticks until the next one, and the direction. Not saved. */
    var dodgeTicks = 0
    var dodgeCooldown = 0

    /** Ticks of the parry window left (spec 05, "Parry") and until the next one. Not saved. */
    var parryTicks = 0
    var parryCooldown = 0

    /** Status effects on the player (spec 05), ticks left; not saved. */
    var burn = 0
    var burnClock = 0
    var chill = 0
    var stun = 0
    var weaken = 0

    /** A meal that fortifies (spec 06, "Fortify"): ticks left, and the attack it adds in percent; not saved. */
    var fortify = 0
    var fortifyPct = 0L

    /** A brew that wards (spec 06, "Ward"): ticks left, and the defense it adds in percent; not saved. */
    var ward = 0
    var wardPct = 0L

    /** A dish that heals over time (spec 06, "Regen"): ticks left, and the health given back every second; not saved. */
    var regen = 0
    var regenAmount = 0L

    /** A brew of haste (spec 06, "Haste"): ticks left, and the speed of walking it adds in percent; not saved. */
    var haste = 0
    var hastePct = 0L

    /** Ticks until an active ability is ready again, by kind (spec 11, "Active abilities"); not saved. */
    val abilityCd = HashMap<String, Int>()

    fun clearStatus() {
        burn = 0
        burnClock = 0
        chill = 0
        stun = 0
        weaken = 0
        fortify = 0
        ward = 0
        regen = 0
        haste = 0
    }

    /** Ticks until the death save is ready again (spec 18). Not saved. */
    var deathSaveCd = 0
    var dodgeDir = Vec2(1f, 0f)
}

class Enemy(val def: EnemyDef, var position: Vec2) {
    val home: Vec2 = position
    var hp: Long = def.hp
    var state = EnemyState.IDLE
    var stateTick = 0

    /** Streamed worlds: the spawner tile this enemy belongs to. */
    var spawnerX = 0
    var spawnerY = 0

    /** Presentation only. */
    var hitFlash = 0

    /** Status effects (spec 05): ticks left; not saved. */
    var burn = 0
    var burnClock = 0
    var chill = 0
    var weaken = 0
    var stun = 0

    /** The stagger bar and the ticks left of being broken (spec 05, "Stagger"); not saved. */
    var stagger = 0L

    /** The last creature the player hit: the companion goes for it first (spec 10, "Teamwork"); not saved. */
    var marked = false
    var broken = 0
    val radius: Float get() = def.radiusX100 / 100f
}

/** Something a client may want to show (numbers floating up from a hit); not part of the contract. */
/** [weak]: the element multiplier of the hit was above 1000 (spec 05, "Elements"). */
/** Something that made a sound (presentation only): [kind] is aggro, attack, hit, hurt or die; [family] the voices of the creature (spec 14). */
data class SimCue(val kind: String, val family: String, val position: Vec2, val crit: Boolean = false, val weak: Boolean = false)

data class DamageEvent(val position: Vec2, val amount: Long, val crit: Boolean, val onPlayer: Boolean, val weak: Boolean = false)

/** Top-left of the view, in tiles. */
data class Camera(val x: Float, val y: Float)

private fun buildCollision(map: TileMap, tileset: Tileset): CollisionWorld {
    val solid = BooleanArray(map.ground.size) { tileset.tiles[map.ground[it]]?.solid ?: false }
    return CollisionWorld(map.width, map.height, solid, map.props.map { Circle(it.x, it.y, it.radius) })
}

private fun axisOrigin(player: Float, view: Float, mapSize: Float): Float {
    if (mapSize <= view) return (mapSize - view) / 2f
    val origin = player - view / 2f
    if (origin < 0f) return 0f
    val maxOrigin = mapSize - view
    return if (origin > maxOrigin) maxOrigin else origin
}

private fun distance(ax: Float, ay: Float, bx: Float, by: Float): Float {
    val dx = bx - ax
    val dy = by - ay
    return sqrt(dx * dx + dy * dy)
}

/**
 * [speedTilesPerS] is used while combat is disabled; with combat the speed comes from the derived stats.
 */
class WorldSim(
    val map: TileMap,
    val tileset: Tileset,
    private val speedTilesPerS: Float,
    val combat: CombatSetup = CombatSetup(),
    /** With a stream the map only gives the size, the spawn and the NPCs; tiles, props and enemies come from the chunks. */
    stream: StreamConfig? = null,
) : StoryHost {
    val chunks: ChunkStore? = stream?.let { ChunkStore(it.params, it.seed, tileset) }
    val collision: CollisionWorld =
        if (chunks != null) CollisionWorld(map.width, map.height, BooleanArray(0), emptyList(), chunks) else buildCollision(map, tileset)
    private val combatRng = deriveStream(combat.seed, "combat")
    private val lootRng = deriveStream(combat.seed, "loot")
    private val spawn: Vec2 = run {
        chunks?.keepAround(chunkOf(floor(map.spawnX).toInt()), chunkOf(floor(map.spawnY).toInt()))
        collision.resolve(Vec2(map.spawnX, map.spawnY))
    }

    val player = Player(spawn)
    var derived: DerivedStats = derivedStats(1, combat.player.base, Equipment())
        private set
    val enemies = ArrayList<Enemy>()
    override val inventory = java.util.TreeMap<String, Long>()
    private val hitSet = ArrayList<Boolean>(List(combat.spawns.size) { false })
    /** Spawner tile -> world tick of the death. */
    private val cleared = java.util.TreeMap<Pair<Int, Int>, Long>(compareBy({ it.first }, { it.second }))

    /** The item ids worn (spec 06). */
    var equippedWeapon: String = combat.startWeapon
        private set
    var equippedArmor: String = combat.startArmor
        private set

    /** The accessory worn (spec 06, "Equipment"); empty: none. */
    var equippedAccessory: String = ""
        private set

    /** The board of a settlement (spec 07, "Guild"): the settlement, the day and its offers. */
    class Board(val settlement: Settlement, val day: Long, val offers: List<Offer>)

    /** A stop of the Threshold Stone list: the stone tile, the name of its settlement and the text key of its region (spec 09). */
    class StoneStop(val x: Int, val y: Int, val place: String, val region: String)

    /** The list of stones offered by a stone being used: [here] is the index of that stone, [fresh] tells it was woken just now. */
    class Travel(val stops: List<StoneStop>, val here: Int, val fresh: Boolean)

    /** The Threshold Stones that were used, in order of waking (spec 09). */
    val stones = ArrayList<Pair<Int, Int>>()

    /** The bestiary (spec 11): creature id -> how many were killed. */
    val bestiary = java.util.TreeMap<String, Int>()

    /** The talents learned (spec 11, "Talents"): talent id -> rank. */
    val talents = java.util.TreeMap<String, Int>()

    /** The talent points not spent yet: a share for every level gained, less the ranks learned. */
    fun talentPoints(): Int = (player.level - 1).toInt() * combat.talentPointsPerLevel - talents.values.sum()

    /** Spends one point on a rank of a talent; false, changing nothing, when it is refused. */
    fun learnTalent(id: String): Boolean {
        if (story.dialogueActive) return false
        val talent = combat.talents.firstOrNull { it.id == id } ?: return false
        if (talentPoints() < 1 || (talents[id] ?: 0) >= talent.maxRank) return false
        if (talent.requiresTalent.isNotEmpty() && (talents[talent.requiresTalent] ?: 0) < talent.requiresRank) return false // a branch of the tree
        talents[id] = (talents[id] ?: 0) + 1
        recomputeDerived()
        player.hp = minOf(player.hp, derived.maxHp)
        return true
    }

    /** The power of an ability of the talents (spec 11, "Abilities"): the percent of every rank learned, summed over the talents of that kind. */
    fun talentPower(stat: String): Long = combat.talents.filter { it.stat == stat }.sumOf { it.pctPerRank * (talents[it.id] ?: 0) }

    /** The counters of spec 11: how many times the player gathered, crafted and parried, and the renown of the regions. */
    val counters = java.util.TreeMap<String, Int>()

    private fun count(name: String) {
        counters[name] = (counters[name] ?: 0) + 1
    }

    var travel: Travel? = null
        private set

    /** The board that is open now, or null. */
    var board: Board? = null
        private set

    /** The shop that is open now (spec 06), or null. */
    var shop: ShopDef? = null
        private set

    /** Settlement people of the active window (spec 09) and their collision circles. */
    private val npcList = ArrayList<NpcDef>()
    private var routineTod = -1 // time of day (permille) the dynamic NPCs were built for
    private val npcCircles = ArrayList<Circle>()

    /** Explored world map cells (spec 09); empty on a fixed map. */
    val explored: MutableSet<Pair<Int, Int>> = java.util.TreeSet<Pair<Int, Int>>(compareBy({ it.second }, { it.first }))

    /** Simulation ticks since the world was created (spec 08). */
    var worldTicks: Long = chunks?.params?.time?.startTick ?: 0L
        private set
    private var windowValid = false
    private var windowX = 0
    private var windowY = 0
    private val events = ArrayList<DamageEvent>()
    private val cues = ArrayList<SimCue>()

    /** The companion (spec 10): where it is, or null when the protagonist has none. */
    var companionPosition: Vec2? = if (combat.companion != null) player.position else null
        private set
    private var companionCooldown = combat.companion?.cooldownTicks ?: 0

    /** The companion was told to stay where it is (spec 10, "Commands"). */
    var companionStaying = false
        private set

    /** The creatures the companion has killed (spec 10, "Bond"). */
    var companionBond = 0
    private var companionCare = 0 // ticks since it last tended the player (spec 10, "Care"); not saved
        private set

    /** Tells the companion to stay where it is, or to follow again; false when there is none. */
    fun companionStay(): Boolean {
        if (combat.companion == null) return false
        companionStaying = !companionStaying
        return true
    }

    /** Calls the companion back (spec 10, "Commands"): it is next to the player at once and follows again; false when there is none. */
    fun companionRecall(): Boolean {
        if (combat.companion == null) return false
        companionPosition = player.position
        companionStaying = false
        return true
    }

    /** Whether the last recipe made came out fine (spec 06, "Quality"); presentation only. */
    var lastCraftFine = false
        private set

    /** The counter that holds the renown of the region where the player stands (spec 07, "Renown"). */
    fun renownKey(): String = "renown:" + regionId()

    /** The region where the player stands; of a world without regions, the one of the setup. */
    fun regionId(): String {
        val store = chunks ?: return combat.region
        return store.params.regions[regionAt(store.params, floor(player.position.x).toInt(), floor(player.position.y).toInt())].id
    }

    /** What the market of the day does to the prices of the open shop, in permille (spec 06, "Market days"): 1000 is a plain day. */
    fun marketPm(): Long {
        val swing = (shop?.marketSwingPm ?: 0).toLong()
        if (swing <= 0L) return 1000L
        val dayTicks = chunks?.params?.time?.dayTicks?.toLong() ?: combat.dayTicks.toLong()
        val day = if (dayTicks > 0L) worldTicks / dayTicks + 1L else 1L
        val h = hash64(fnv1a64("market:" + regionId()) xor combat.seed, day)
        return 1000L - swing + (h % (2L * swing + 1L).toULong()).toLong()
    }

    /** The talent that gives the active ability of [kind] (burst or mend) once it has a rank, or null (spec 11, "Active abilities"). */
    fun abilityTalent(kind: String): TalentDef? = combat.talents.firstOrNull { it.stat == kind && it.hasActive && (talents[it.id] ?: 0) > 0 }

    /** The ticks until the active ability of [kind] is ready again. */
    fun abilityCooldown(kind: String): Int = player.abilityCd[kind] ?: 0

    /** Uses the active ability of [kind]; false, changing nothing, when it is refused. */
    fun useAbility(kind: String): Boolean {
        val p = player
        if (story.dialogueActive || p.stun > 0 || (kind != "burst" && kind != "mend")) return false
        val talent = abilityTalent(kind) ?: return false
        if (abilityCooldown(kind) > 0) return false
        val power = talentPower(kind)
        val full = derived.maxHp
        if (p.mpU < talent.activeMp * 6000L || (kind == "mend" && !(p.hp > 0L && p.hp < full))) return false
        p.mpU -= talent.activeMp * 6000L
        p.abilityCd[kind] = talent.activeCooldown
        if (kind == "mend") {
            p.hp = minOf(full, p.hp + maxOf(1L, full * power / 100))
            cues.add(SimCue("craft", "", p.position))
            return true
        }
        val reach = talent.activeRadiusX100.toFloat() / 100f
        for (enemy in enemies) { // burst: every creature around, in order, with no roll
            if (enemy.state == EnemyState.DEAD) continue
            if (distance(enemy.position.x, enemy.position.y, p.position.x, p.position.y) > reach + enemy.radius) continue
            val amount = damage(
                DamageInput(
                    atk = maxOf(derived.atk, derived.matk) * power / 100,
                    powerPct = 100,
                    defTarget = enemy.def.def,
                    lvlAttacker = p.level,
                    lvlTarget = enemy.def.level,
                    variancePm = 1000,
                    crit = false,
                    critMultPm = 1500,
                ),
            )
            enemy.hp -= amount
            enemy.hitFlash = HIT_FLASH_TICKS
            events.add(DamageEvent(enemy.position, amount, false, false))
            cues.add(SimCue("hit", enemy.def.sound, enemy.position))
            if (enemy.hp <= 0) {
                enemy.hp = 0
                enemy.state = EnemyState.DEAD
                cues.add(SimCue("die", enemy.def.sound, enemy.position))
                onKill(enemy)
            }
        }
        return true
    }

    override fun renownHere(): Long = (counters[renownKey()] ?: 0).toLong()

    override fun questDone() = count(renownKey())

    /** What the renown takes off the prices of the open shop, in permille. */
    fun renownDiscountPm(): Long {
        val open = shop ?: return 0L
        return minOf(open.renownMaxPm.toLong(), renownHere() * open.renownStepPm)
    }

    private val gathered = HashMap<Pair<Int, Int>, Pair<Long, Int>>() // (x100, y100) -> (tick it grows back, times); not saved

    val story = Story(combat.story, this)

    override val level: Long get() = player.level
    override val playerX: Float get() = player.position.x
    override val playerY: Float get() = player.position.y

    init {
        story.dynamicNpcs = npcList
        chunks?.let { store ->
            story.questResolver = { id -> resolveOffer(store.seed, store.params, id)?.let { questFromOffer(it) } }
        }
        collision.dynamicProps = npcCircles
        for (npc in combat.story.npcs) collision.addProp(Circle(npc.x, npc.y, NPC_RADIUS))
        if (combat.enabled) {
            player.level = combat.startLevel.toLong()
            recomputeDerived()
            player.hp = derived.maxHp
            player.mpU = derived.maxMp * 6000L
            for (s in combat.spawns) enemies.add(Enemy(s.def, Vec2(s.x, s.y)))
            inventory.putAll(combat.startInventory)
            syncWindow()
            markExplored()
        }
    }

    private fun markExplored() {
        val store = chunks ?: return
        explore(explored, store.params, floor(player.position.x).toInt(), floor(player.position.y).toInt())
    }

    /** Day, light and weather of the streamed world now (spec 08); null on a fixed map. */
    /** What the rain leaves of the aggro distance, this tick (spec 08, "Rain hides you"). */
    private var rainAggroPm = 1000
    private var nightAggroPm = 1000

    fun time(): TimeSample? = chunks?.let { sampleTime(it.seed, it.params.time, worldTicks) }

    /** The gid at the tile on whichever map is played, 0 when unknown. */
    fun gidAt(x: Int, y: Int): Int = chunks?.gidAt(x, y) ?: map.gidAt(x, y)

    /** Calls [fn] for every prop inside the rectangle (in tiles). */
    fun forEachProp(x0: Float, y0: Float, x1: Float, y1: Float, fn: (Prop) -> Unit) {
        if (chunks != null) {
            chunks.forEachPropIn(x0, y0, x1, y1, fn)
            return
        }
        for (prop in map.props) if (prop.x >= x0 && prop.x <= x1 && prop.y >= y0 && prop.y <= y1) fn(prop)
    }

    private fun rebuildNpcCircles() {
        npcCircles.clear()
        for (npc in npcList) npcCircles.add(Circle(npc.x, npc.y, NPC_RADIUS))
    }

    /** The time of day in permille (spec 08). */
    private fun timeOfDayPm(): Int {
        val dayTicks = chunks?.params?.time?.dayTicks ?: return 0
        return ((worldTicks % dayTicks) * 1000 / dayTicks).toInt()
    }

    /** Rebuilds the dynamic NPCs of the 5 x 5 chunks around chunk ([cx], [cy]) for the time of day (spec 08, Routines). */
    private fun refreshPeople(cx: Int, cy: Int) {
        npcList.clear()
        for (j in cy - ACTIVE_RADIUS..cy + ACTIVE_RADIUS) for (i in cx - ACTIVE_RADIUS..cx + ACTIVE_RADIUS) addChunkPeople(i, j)
        routineTod = timeOfDayPm()
        rebuildNpcCircles()
    }

    private fun addChunkPeople(cx: Int, cy: Int) {
        val store = chunks ?: return
        val chunk = store.find(cx, cy) ?: return
        val tod = timeOfDayPm()
        for (person in chunk.people) {
            val placement = personPlacement(store.params, person, tod) ?: continue // indoors (spec 08)
            npcList.add(
                NpcDef(
                    person.key, person.dialogue, person.variant, placement.x256 / 256f, placement.y256 / 256f, person.name,
                    mapOf("npc" to person.name, "place" to person.place, "region" to person.region, "quirk" to "\$i18n:${person.quirk}"),
                ),
            )
        }
    }

    /** The enemy the spawner on a tile makes (spec 09, "Fauna"). */
    private fun streamEnemyAt(x: Int, y: Int): EnemyDef {
        val store = requireNotNull(chunks) { "not a streamed world" }
        val id = spawnerEnemyAt(store.seed, store.params, x, y)
        return requireNotNull(combat.streamEnemies[id]) { "no enemy $id for the fauna" }
    }

    private fun addChunkEnemies(cx: Int, cy: Int) {
        if (combat.streamEnemies.isEmpty()) return
        val store = chunks ?: return
        val chunk = store.find(cx, cy) ?: return
        for ((sx, sy) in chunk.spawners) {
            val died = cleared[Pair(sx, sy)]
            if (died != null) {
                // A spawner whose enemy has been dead long enough is ready again when its chunk enters the window (spec 08).
                if (worldTicks - died < store.params.spawnerRespawnTicks) continue
                cleared.remove(Pair(sx, sy))
            }
            val enemy = Enemy(streamEnemyAt(sx, sy), Vec2(sx + 0.5f, sy + 0.5f))
            enemy.spawnerX = sx
            enemy.spawnerY = sy
            enemies.add(enemy)
            hitSet.add(false)
        }
    }

    private fun insideWindow(i: Int, j: Int, wx: Int, wy: Int) = max(abs(i - wx), abs(j - wy)) <= ACTIVE_RADIUS

    /** Spec 09, "Streaming": keeps the enemies in step with the 5 x 5 window around the player's chunk. */
    private fun syncWindow() {
        val store = chunks ?: return
        val cx = chunkOf(floor(player.position.x).toInt())
        val cy = chunkOf(floor(player.position.y).toInt())
        if (windowValid && cx == windowX && cy == windowY) return
        store.keepAround(cx, cy)
        if (windowValid) {
            val keptEnemies = ArrayList<Enemy>()
            val keptHits = ArrayList<Boolean>()
            for (i in enemies.indices) {
                val e = enemies[i]
                if (insideWindow(chunkOf(e.spawnerX), chunkOf(e.spawnerY), cx, cy)) {
                    keptEnemies.add(e)
                    keptHits.add(hitSet[i])
                }
            }
            enemies.clear()
            enemies.addAll(keptEnemies)
            hitSet.clear()
            hitSet.addAll(keptHits)
        }
        for (j in cy - ACTIVE_RADIUS..cy + ACTIVE_RADIUS) {
            for (i in cx - ACTIVE_RADIUS..cx + ACTIVE_RADIUS) {
                if (!windowValid || !insideWindow(i, j, windowX, windowY)) {
                    addChunkEnemies(i, j)
                }
            }
        }
        refreshPeople(cx, cy)
        windowValid = true
        windowX = cx
        windowY = cy
    }

    private fun recomputeDerived() {
        derived = derivedStats(
            player.level,
            primaryAtLevel(combat.player, player.level),
            Equipment(
                weaponAtk = combat.items[equippedWeapon]?.weapon?.atk ?: combat.player.weaponAtk,
                weaponMatk = combat.items[equippedWeapon]?.weapon?.matk ?: combat.player.weaponMatk,
                armorDef = combat.items[equippedArmor]?.armor?.def ?: 0L,
                armorMdef = combat.items[equippedArmor]?.armor?.mdef ?: 0L,
            ),
        ).let { it.copy(maxHp = it.maxHp * (100 + combat.echoPct) / 100) } // the echoes of past games (spec 11)
        for (talent in combat.talents) { // the talents, in the order of the data (spec 11)
            val rank = talents[talent.id] ?: 0
            if (rank <= 0) continue
            val pct = 100 + talent.pctPerRank * rank
            derived = when (talent.stat) {
                "attack" -> derived.copy(atk = derived.atk * pct / 100, matk = derived.matk * pct / 100)
                "health" -> derived.copy(maxHp = derived.maxHp * pct / 100)
                "mana" -> derived.copy(maxMp = derived.maxMp * pct / 100)
                "defense" -> derived.copy(def = derived.def * pct / 100, mdef = derived.mdef * pct / 100)
                "magic" -> derived.copy(matk = derived.matk * pct / 100)
                "critical" -> derived.copy(critChancePm = derived.critChancePm * pct / 100)
                "speed" -> derived.copy(moveSpeedX100 = derived.moveSpeedX100 * pct / 100)
                else -> derived
            }
        }
        combat.items[equippedAccessory]?.accessory?.let { a -> // its flat bonuses come last (spec 06)
            derived = derived.copy(
                atk = derived.atk + a.atk, matk = derived.matk + a.matk, def = derived.def + a.def, mdef = derived.mdef + a.mdef,
                maxHp = derived.maxHp + a.maxHp, critChancePm = derived.critChancePm + a.critPm,
            )
        }
    }

    /** Puts the player at (x, y) in tiles, loading the chunks around (developer option, later the Threshold Stones). */
    fun teleport(x: Float, y: Float) {
        player.position = Vec2(x, y)
        chunks?.keepAround(chunkOf(floor(x).toInt()), chunkOf(floor(y).toInt()))
        player.position = collision.resolve(player.position)
        syncWindow()
        markExplored()
    }

    /** The position of the Threshold Stone the player can use, or null (spec 09). */
    fun stoneNear(): Vec2? {
        val store = chunks ?: return null
        val range = store.params.stoneRangeX100 / 100f
        if (store.params.stoneArt.isEmpty()) return null
        val px = player.position.x
        val py = player.position.y
        var best: Vec2? = null
        var bestDistance = range * range
        forEachProp(px - range, py - range, px + range, py + range) { prop ->
            if (prop.art != store.params.stoneArt) return@forEachProp
            val d = (prop.x - px) * (prop.x - px) + (prop.y - py) * (prop.y - py)
            if (d <= bestDistance) {
                bestDistance = d
                best = Vec2(prop.x, prop.y)
            }
        }
        return best
    }

    /** Wakes the stone near the player, restores health and offers the list of stones. Returns false when no stone is near. */
    fun useStone(): Boolean {
        val store = chunks ?: return false
        val stone = stoneNear() ?: return false
        val tile = Pair(floor(stone.x).toInt(), floor(stone.y).toInt())
        val fresh = tile !in stones
        if (fresh) stones.add(tile)
        player.hp = derived.maxHp
        player.mpU = derived.maxMp * 6000L // a stone restores the mana too
        val stops = stones.map { (x, y) ->
            val settlement = settlementContaining(store.seed, store.params, x, y)
            StoneStop(x, y, settlement?.name ?: "", settlement?.let { store.params.regions[it.region].name } ?: "")
        }
        travel = Travel(stops, stones.indexOf(tile), fresh)
        return true
    }

    fun closeTravel() {
        travel = null
    }

    /** Goes to a stone of the open list, one tile in front of it. Returns false, changing nothing, when refused. */
    fun travelTo(index: Int): Boolean {
        val open = travel ?: return false
        if (index < 0 || index >= open.stops.size || index == open.here) return false
        val stop = open.stops[index]
        travel = null
        teleport(stop.x + 0.5f, stop.y + 1.75f)
        return true
    }

    override fun seasonId(): String {
        val store = chunks ?: return ""
        val index = seasonIndexOf(store.params.time, worldTicks / store.params.time.dayTicks + 1)
        return if (index >= 0) store.params.time.seasons[index].id else ""
    }

    override fun todPm(): Int = timeOfDayPm()

    override fun healFull() {
        player.hp = derived.maxHp
        player.mpU = derived.maxMp * 6000L
    }

    override fun openBoard() {
        val store = chunks ?: return
        val settlement = settlementContaining(store.seed, store.params, floor(player.position.x).toInt(), floor(player.position.y).toInt()) ?: return
        val day = worldTicks / store.params.time.dayTicks + 1
        board = Board(settlement, day, offersFor(store.seed, store.params, settlement, day))
    }

    fun closeBoard() {
        board = null
    }

    /** The guild rank (index) of the player (spec 07). */
    fun guildRank(): Int = chunks?.let { rankIndex(it.params.guild, story.guildPoints) } ?: 0

    /** Accepts the offer of a slot of the open board. Returns false, changing nothing, when refused. */
    fun acceptOffer(slot: Int): Boolean {
        val offer = board?.offers?.getOrNull(slot) ?: return false
        if (guildRank() < offer.minRank || offer.id in story.quests) return false
        story.addGeneratedQuest(questFromOffer(offer))
        story.startQuest(offer.id)
        return true
    }

    override fun openShop() {
        val store = chunks
        val base = if (store != null) {
            val region = store.params.regions[regionAt(store.params, floor(player.position.x).toInt(), floor(player.position.y).toInt())]
            ShopDef(region.shopPricePm, region.shopStock, region.shopRenownStepPm, region.shopRenownMaxPm, region.shopMarketSwingPm, region.shopRenownStock)
        } else {
            combat.shop
        }
        // wares for friends of the region (spec 07, "Renown")
        shop = base?.let { b ->
            ShopDef(b.pricePm, b.stock + b.renownStock.filter { renownHere() >= it.second }.map { it.first }, b.renownStepPm, b.renownMaxPm, b.marketSwingPm, b.renownStock)
        }
    }

    fun closeShop() {
        shop = null
    }

    private fun stackLimit(item: ItemDef): Int =
        if (item.stackMax > 0) item.stackMax else if (item.kind == "weapon" || item.kind == "armor" || item.kind == "accessory") 1 else 99

    /** Price of buying an item in the open shop, 0 when it cannot be bought (spec 06). */
    fun buyPrice(itemId: String): Long {
        val item = combat.items[itemId] ?: return 0L
        val open = shop ?: return 0L
        if (item.price <= 0) return 0L
        val today = maxOf(1L, maxOf(1L, item.price * open.pricePm / 1000) * marketPm() / 1000) // the market of the day (spec 06)
        return maxOf(1L, today * (1000 - renownDiscountPm()) / 1000) // the renown (spec 07)
    }

    /** What the shop pays for an item, 0 when it cannot be sold. */
    fun sellPrice(itemId: String): Long {
        val item = combat.items[itemId] ?: return 0L
        return if (item.price <= 0) 0L else maxOf(1L, item.price / 2 * marketPm() / 1000) // the market of the day (spec 06)
    }

    /** Equips a weapon or an armor of the inventory (spec 06). Returns false, changing nothing, when refused. */
    fun equip(itemId: String): Boolean {
        val item = combat.items[itemId] ?: return false
        if ((inventory[itemId] ?: 0L) < 1L) return false
        if (item.weapon != null && item.kind == "weapon" && equippedWeapon != itemId) {
            equippedWeapon = itemId
        } else if (item.armor != null && item.kind == "armor" && equippedArmor != itemId) {
            equippedArmor = itemId
        } else if (item.accessory != null && item.kind == "accessory" && equippedAccessory != itemId) {
            equippedAccessory = itemId
        } else {
            return false
        }
        recomputeDerived()
        player.hp = minOf(player.hp, derived.maxHp)
        return true
    }

    /** Buys one item from the open shop (spec 06). Returns false, changing nothing, when refused. */
    fun buy(itemId: String): Boolean {
        val open = shop ?: return false
        if (itemId !in open.stock) return false
        val item = combat.items[itemId] ?: return false
        val price = buyPrice(itemId)
        if (price <= 0L || story.gold < price || (inventory[itemId] ?: 0L) >= stackLimit(item)) return false
        story.gold -= price
        inventory[itemId] = (inventory[itemId] ?: 0L) + 1L
        return true
    }

    /** Sells one item of the inventory to the open shop (spec 06). Returns false, changing nothing, when refused. */
    fun sell(itemId: String): Boolean {
        if (shop == null) return false
        val owned = inventory[itemId] ?: 0L
        if (owned < 1L || sellPrice(itemId) <= 0L) return false
        if (owned == 1L && (itemId == equippedWeapon || itemId == equippedArmor || itemId == equippedAccessory)) return false
        story.gold += sellPrice(itemId)
        if (owned == 1L) inventory.remove(itemId) else inventory[itemId] = owned - 1L
        return true
    }

    /** Uses one item of the inventory (spec 06). Returns false, changing nothing, when it is refused. */
    fun useItem(itemId: String): Boolean {
        if (story.dialogueActive) return false
        val item = combat.items[itemId] ?: return false
        if ((inventory[itemId] ?: 0L) < 1L) return false
        val heal = item.effects.filter { it.effect == "heal" }.sumOf { it.amount } * combat.gift.healPct / 100
        val mana = item.effects.filter { it.effect == "restore_mp" }.sumOf { it.amount }
        val fortify = item.effects.lastOrNull { it.effect == "fortify" } // spec 06, "Fortify": attack up for a while
        val ward = item.effects.lastOrNull { it.effect == "ward" } // spec 06, "Ward": defense up for a while
        val regen = item.effects.lastOrNull { it.effect == "regen" } // spec 06, "Regen": health back over time
        val haste = item.effects.lastOrNull { it.effect == "haste" } // spec 06, "Haste": faster on foot for a while
        val afflicted = player.burn > 0 || player.chill > 0 || player.stun > 0 || player.weaken > 0
        val cleanse = afflicted && item.effects.any { it.effect == "cleanse" } // spec 06, "Cleanse": the statuses go
        val fullMp = derived.maxMp * 6000L
        if (!((heal > 0L && player.hp < derived.maxHp) || (mana > 0L && player.mpU < fullMp) || fortify != null || ward != null || regen != null || haste != null || cleanse)) return false
        if (fortify != null) {
            player.fortifyPct = fortify.amount
            player.fortify = fortify.ticks
        }
        if (ward != null) {
            player.wardPct = ward.amount
            player.ward = ward.ticks
        }
        if (regen != null) {
            player.regenAmount = regen.amount
            player.regen = regen.ticks
        }
        if (haste != null) {
            player.hastePct = haste.amount
            player.haste = haste.ticks
        }
        if (cleanse) {
            player.burn = 0
            player.burnClock = 0
            player.chill = 0
            player.stun = 0
            player.weaken = 0
        }
        if (heal > 0L) player.hp = minOf(derived.maxHp, player.hp + heal)
        if (mana > 0L) player.mpU = minOf(fullMp, player.mpU + mana * 6000L)
        val left = (inventory[itemId] ?: 0L) - 1L
        if (left == 0L) inventory.remove(itemId) else inventory[itemId] = left
        return true
    }

    /** Events produced since the last call (damage numbers). */
    /** What gathering gave: [node] tells that there was something to gather from; [sound] is plant, wood or stone. */
    class GatherResult(val node: Boolean, val sound: String, val items: List<Pair<String, Long>>)

    // The companion follows the player and hits the nearest creature in range now and then (spec 10).
    private fun updateCompanion() {
        val c = combat.companion ?: return
        var pos = companionPosition ?: player.position
        val p = player
        val dx = p.position.x - pos.x
        val dy = p.position.y - pos.y
        val dist = sqrt(dx * dx + dy * dy)
        val follow = c.followX100.toFloat() / 100f
        if (dist > COMPANION_LEASH) {
            pos = p.position
            companionStaying = false // too far: it comes back and follows again
        } else if (!companionStaying && dist > follow) {
            val step = min(c.speedX100.toFloat() / 100f * TICK_DT, dist - follow)
            pos = collision.resolve(Vec2(pos.x + dx / dist * step, pos.y + dy / dist * step), COMPANION_RADIUS)
        }
        companionPosition = pos
        if (c.careTicks > 0 && companionBond >= c.careBond) { // care (spec 10): it tends the player now and then
            companionCare++
            if (companionCare >= c.careTicks) {
                companionCare = 0
                val full = derived.maxHp
                if (player.hp > 0 && player.hp < full) player.hp = minOf(full, player.hp + maxOf(1L, full * c.carePct / 100))
            }
        }
        if (companionCooldown > 0) companionCooldown--
        if (companionCooldown > 0) return
        var target: Enemy? = null
        var best = 0f
        for (enemy in enemies) {
            if (enemy.state == EnemyState.DEAD) continue
            val d = sqrt((enemy.position.x - pos.x) * (enemy.position.x - pos.x) + (enemy.position.y - pos.y) * (enemy.position.y - pos.y))
            if (d > c.rangeX100.toFloat() / 100f + enemy.radius) continue
            if (enemy.marked) { // the creature the player hit last, when it is in reach, before any other
                target = enemy
                break
            }
            if (target == null || d < best) {
                target = enemy
                best = d
            }
        }
        val hit = target ?: return
        val amount = damage(
            DamageInput(
                atk = (c.atkBase + c.atkPerLevel * (p.level - 1) + minOf(companionBond / 5, 10)) * combat.gift.companionAtkPct / 100, // the bond (spec 10), a gift of command (spec 18)
                powerPct = 100,
                defTarget = hit.def.def,
                lvlAttacker = p.level,
                lvlTarget = hit.def.level,
                variancePm = 1000,
                crit = false,
                critMultPm = 1500,
            ),
        )
        hit.hp -= amount
        hit.hitFlash = HIT_FLASH_TICKS
        events.add(DamageEvent(hit.position, amount, false, false))
        cues.add(SimCue("hit", hit.def.sound, hit.position))
        companionCooldown = c.cooldownTicks
        if (hit.hp <= 0) {
            hit.hp = 0
            hit.state = EnemyState.DEAD
            cues.add(SimCue("die", hit.def.sound, hit.position))
            companionBond += combat.gift.bondGain // a gift of taming makes the bond grow faster (spec 18)
            onKill(hit)
        }
    }

    /** Makes a recipe from the bag (spec 06, "Crafting"). Returns false, changing nothing, when it is refused. */
    /** Whether a prop of [art] is within 2 tiles (plus its radius); an empty art is everywhere (spec 06, "Stations"). */
    fun nearStation(art: String): Boolean {
        if (art.isEmpty()) return true
        val at = player.position
        var found = false
        forEachProp(at.x - 3f, at.y - 3f, at.x + 3f, at.y + 3f) { prop ->
            if (prop.art == art && sqrt((prop.x - at.x) * (prop.x - at.x) + (prop.y - at.y) * (prop.y - at.y)) <= 2f + prop.radius) found = true
        }
        return found
    }

    fun craft(recipeId: String): Boolean {
        if (story.dialogueActive) return false
        val recipe = combat.recipes.firstOrNull { it.id == recipeId } ?: return false
        if (recipe.inputs.any { (item, qty) -> (inventory[item] ?: 0L) < qty }) return false
        if (!nearStation(recipe.station)) return false // cooking needs a fire (spec 06, "Stations")
        for ((item, qty) in recipe.inputs) {
            val left = (inventory[item] ?: 0L) - qty
            if (left == 0L) inventory.remove(item) else inventory[item] = left
        }
        var made = recipe.output
        var qty = recipe.outputQty + titleBonus(gather = false) // the titles of an artisan (spec 11)
        var fine = false
        if (recipe.finePm > 0) { // quality (spec 06): a roll from the seed and the number of things made so far
            val h = hash64(fnv1a64("craft") xor combat.seed, (counters["crafted"] ?: 0).toLong())
            fine = (mix64(h) % 1000uL).toLong() < recipe.finePm + titleFinePm()
        }
        if (fine) {
            if (recipe.fineItem.isNotEmpty()) made = recipe.fineItem else qty++ // the fine piece, or one more of what is made
            count("crafted_fine")
        }
        lastCraftFine = fine
        inventory[made] = (inventory[made] ?: 0L) + qty
        count("crafted")
        cues.add(SimCue("craft", "", player.position))
        return true
    }

    private class Gatherable(val node: GatherNode, val x: Float, val y: Float)

    /** The nearest prop in reach that can be gathered from and has grown back, or null (spec 06, "Gathering"). */
    private fun findGatherable(): Gatherable? {
        if (story.dialogueActive || combat.gatherNodes.isEmpty()) return null
        val p = player
        var best: Gatherable? = null
        var bestD = 0f
        val far = 4.5f // the largest reach plus a prop's radius
        forEachProp(p.position.x - far, p.position.y - far, p.position.x + far, p.position.y + far) { prop ->
            val node = combat.gatherNodes[prop.art] ?: return@forEachProp
            val d = sqrt((prop.x - p.position.x) * (prop.x - p.position.x) + (prop.y - p.position.y) * (prop.y - p.position.y))
            if (d > node.reachX100.toFloat() / 100f + prop.radius) return@forEachProp
            val key = Pair(floor(prop.x * 100f + 0.5f).toInt(), floor(prop.y * 100f + 0.5f).toInt())
            val grown = gathered[key]
            if (grown != null && worldTicks < grown.first) return@forEachProp
            val current = best
            if (current == null || d < bestD || (d == bestD && (prop.x < current.x || (prop.x == current.x && prop.y < current.y)))) {
                best = Gatherable(node, prop.x, prop.y)
                bestD = d
            }
        }
        return best
    }

    /** Whether there is something to gather from near the player (the touch button of the interface). */
    fun gatherNear(): Boolean = findGatherable() != null

    /** Gathers from the nearest prop in reach that can be gathered from; the items found are added to the bag (spec 06, "Gathering"). */
    fun gather(): GatherResult {
        val found = findGatherable() ?: return GatherResult(false, "", emptyList())
        val p = player
        val node = found.node
        val bestX = found.x
        val bestY = found.y
        val key = Pair(floor(bestX * 100f + 0.5f).toInt(), floor(bestY * 100f + 0.5f).toInt())
        val times = gathered[key]?.second ?: 0
        val h = hash64(fnv1a64("gather") xor combat.seed, key.first.toLong(), key.second.toLong(), times.toLong())
        val got = ArrayList<Pair<String, Long>>()
        for ((i, drop) in node.drops.withIndex()) {
            if (mix64(h + (2 * i).toULong()) % 1000uL < drop.weightPm.toULong()) {
                val qty = drop.qtyMin + (mix64(h + (2 * i + 1).toULong()) % (drop.qtyMax - drop.qtyMin + 1).toULong()).toLong() + titleBonus(gather = true) // the titles of a forager (spec 11)
                inventory[drop.item] = (inventory[drop.item] ?: 0L) + qty
                got.add(Pair(drop.item, qty))
            }
        }
        gathered[key] = Pair(worldTicks + node.cooldownTicks, times + 1)
        count("gathered")
        cues.add(SimCue("gather", node.sound, p.position))
        return GatherResult(true, node.sound, got)
    }

    fun takeCues(): List<SimCue> {
        val copy = ArrayList(cues)
        cues.clear()
        return copy
    }

    fun takeEvents(): List<DamageEvent> {
        val copy = ArrayList(events)
        events.clear()
        return copy
    }

    /** One fixed tick (1/60 s) with the raw movement input and the attack input of this tick. */
    /** The mana in points (the floor of mpU / 6000). */
    val mp: Long get() = player.mpU / 6000L

    /** Whether the protagonist has a power strike. */
    val hasStrike: Boolean get() = combat.strike.enabled

    fun tick(rawXIn: Float, rawYIn: Float, attackIn: Boolean = false, dodgeIn: Boolean = false, strikeIn: Boolean = false, parryIn: Boolean = false) {
        worldTicks++
        syncWindow()
        // the rain hides the player (spec 08): creatures notice from a shorter distance
        val store = chunks
        if (store != null) {
            val sample = sampleTime(store.seed, store.params.time, worldTicks)
            rainAggroPm = 1000 - sample.rainPm * store.params.time.rainAggroCutPm / 1000
            nightAggroPm = 1000 - (1000 - sample.lightPm) * store.params.time.nightAggroCutPm / 1000 // the night hides the player too
        } else {
            rainAggroPm = 1000 - combat.rainPm * combat.rainAggroCutPm / 1000
            nightAggroPm = 1000 - (1000 - combat.lightPm) * combat.nightAggroCutPm / 1000
        }
        if (chunks != null && windowValid && timeOfDayPm() != routineTod) refreshPeople(windowX, windowY) // somebody goes home or comes out (spec 08)
        markExplored()
        val frozen = story.dialogueActive
        val rawX = if (frozen) 0f else rawXIn
        val rawY = if (frozen) 0f else rawYIn
        val p = player
        val enabled = combat.enabled
        if (p.iframes > 0) p.iframes--
        if (p.cooldown > 0) p.cooldown--
        if (p.dodgeCooldown > 0) p.dodgeCooldown--
        if (p.parryCooldown > 0) p.parryCooldown--
        if (p.deathSaveCd > 0) p.deathSaveCd--
        for (entry in p.abilityCd.entries) if (entry.value > 0) entry.setValue(entry.value - 1)
        p.mpU = minOf(derived.maxMp * 6000L, p.mpU + derived.mpRegenX100 * combat.gift.mpRegenPct / 100)

        if (p.burn > 0) { // status effects on the player (spec 05)
            p.burn--
            p.burnClock++
            if (p.burnClock % PLAYER_BURN_PERIOD == 0) p.hp = maxOf(1L, p.hp - maxOf(1L, derived.maxHp * PLAYER_BURN_PCT / 100))
        }
        val stunned = p.stun > 0
        if (stunned) p.stun--
        if (enabled && parryIn && !frozen && !stunned && p.parryTicks == 0 && p.parryCooldown == 0 && p.phase == AttackPhase.NONE && p.dodgeTicks == 0) {
            p.parryTicks = PARRY_TICKS + titleParryBonus() // the window opens (spec 05); a guard's titles widen it
            p.parryCooldown = PARRY_COOLDOWN
        }
        // a parry in progress allows no attack and no roll
        val attack = attackIn && !frozen && !stunned && p.parryTicks == 0
        val dodge = dodgeIn && !frozen && !stunned && p.parryTicks == 0
        val strike = strikeIn && !frozen && !stunned && p.parryTicks == 0

        val direction = normalizeInput(rawX, rawY)
        val moving = direction.x != 0f || direction.y != 0f
        if (enabled && dodge && combat.dodge.enabled && p.dodgeTicks == 0 && p.dodgeCooldown == 0 && p.phase == AttackPhase.NONE) {
            // The dodge roll starts (spec 05, "Dodge roll").
            val way = if (moving) direction else p.facing
            val length = sqrt(way.x * way.x + way.y * way.y)
            p.dodgeDir = Vec2(way.x / length, way.y / length)
            p.facing = p.dodgeDir
            if (p.dodgeDir.x != 0f) p.facingLeft = p.dodgeDir.x < 0f
            p.dodgeTicks = combat.dodge.ticks
            p.dodgeCooldown = combat.dodge.cooldown * combat.gift.dodgeCooldownPct / 100
            p.iframes = max(p.iframes, combat.dodge.iframes)
        }
        if (p.dodgeTicks > 0) {
            p.dodgeTicks--
            if (!p.moving) {
                p.moving = true
                p.clipTick = 0
            } else {
                p.clipTick++
            }
            val rollSpeed = derived.moveSpeedX100.toFloat() / 100f * combat.dodge.speedMultX100.toFloat() / 100f
            p.position = collision.step(p.position, p.dodgeDir, rollSpeed)
        } else {
            if (enabled && moving && (p.phase == AttackPhase.NONE || p.phase == AttackPhase.STARTUP)) {
                val length = sqrt(direction.x * direction.x + direction.y * direction.y)
                p.facing = Vec2(direction.x / length, direction.y / length)
            }
            val walkX100 = if (p.haste > 0) derived.moveSpeedX100 * (100 + p.hastePct) / 100 else derived.moveSpeedX100.toLong() // a brew of haste (spec 06)
            var speed = if (enabled) walkX100.toFloat() / 100f else speedTilesPerS
            if (enabled && p.phase != AttackPhase.NONE) speed *= ATTACK_MOVE_MULT
            if (p.chill > 0) speed *= 0.5f
            p.position = collision.step(p.position, direction, speed)

            if (direction.x != 0f) p.facingLeft = direction.x < 0f
            if (moving != p.moving) {
                p.moving = moving
                p.clipTick = 0
            } else {
                p.clipTick++
            }

            if (!enabled) return
            if (p.phase == AttackPhase.NONE && p.cooldown == 0) {
                if (strike && combat.strike.enabled && p.mpU >= combat.strike.mp * 6000L) {
                    p.mpU -= combat.strike.mp * 6000L
                    p.usingStrike = true
                    p.phase = AttackPhase.STARTUP
                    p.phaseTick = 0
                    p.cooldown = combat.strike.skill.cooldown
                    hitSet.replaceAll { false }
                } else if (attack) {
                    p.usingStrike = false
                    p.phase = AttackPhase.STARTUP
                    p.phaseTick = 0
                    p.cooldown = combat.skill.cooldown
                    hitSet.replaceAll { false }
                }
            }
        }
        advanceAttack()
        updateCompanion()
        for (enemy in enemies) {
            updateEnemy(enemy)
            if (enemy.hitFlash > 0) enemy.hitFlash--
        }
        if (p.parryTicks > 0) p.parryTicks--
        if (p.chill > 0) p.chill--
        if (p.weaken > 0) p.weaken--
        if (p.fortify > 0) p.fortify-- // a meal that fortifies (spec 06) wears off
        if (p.ward > 0) p.ward-- // and a brew that wards (spec 06)
        if (p.haste > 0) p.haste-- // a brew of haste (spec 06) wears off
        if (p.regen > 0) { // a dish that heals over time (spec 06): `amount` every second
            p.regen--
            if (p.regen % 60 == 0 && p.hp > 0 && p.hp < derived.maxHp) p.hp = minOf(derived.maxHp, p.hp + p.regenAmount)
        }
    }

    private fun advanceAttack() {
        val p = player
        val s = if (p.usingStrike) combat.strike.skill else combat.skill
        when (p.phase) {
            AttackPhase.STARTUP -> if (++p.phaseTick >= s.startup) {
                p.phase = AttackPhase.ACTIVE
                p.phaseTick = 0
            }
            AttackPhase.ACTIVE -> {
                doHits()
                if (++p.phaseTick >= s.active) {
                    p.phase = AttackPhase.RECOVERY
                    p.phaseTick = 0
                }
            }
            AttackPhase.RECOVERY -> if (++p.phaseTick >= s.recovery) p.phase = AttackPhase.NONE
            AttackPhase.NONE -> Unit
        }
    }

    private fun doHits() {
        val p = player
        val s = if (p.usingStrike) combat.strike.skill else combat.skill
        val cosHalf = cos(s.angleDeg.toDouble() / 2.0 * PI / 180.0).toFloat()
        val whirl = if (p.usingStrike) talentPower("whirl") else 0L // spec 11, "Abilities": the power strike hits all around, and farther
        val reachX100 = s.radiusX100 * (100 + whirl) / 100
        for ((index, enemy) in enemies.withIndex()) {
            if (enemy.state == EnemyState.DEAD || hitSet[index]) continue
            val dx = enemy.position.x - p.position.x
            val dy = enemy.position.y - p.position.y
            val dist = sqrt(dx * dx + dy * dy)
            if (dist > reachX100.toFloat() / 100f + enemy.radius) continue
            if (dist > 0f && whirl == 0L) {
                val dot = (dx * p.facing.x + dy * p.facing.y) / dist
                if (dot < cosHalf) continue
            }
            hitSet[index] = true
            for (other in enemies) other.marked = other === enemy // the companion's next target (spec 10, "Teamwork")
            val variance = 950L + combatRng.nextBounded(101)
            val crit = combatRng.nextBounded(1000) < derived.critChancePm
            val rawAmount = damage(
                DamageInput(
                    atk = ((if (s.magical) derived.matk else derived.atk) * (100 + titleAttackPct() + (if (p.fortify > 0) p.fortifyPct else 0L)) / 100).let { if (p.weaken > 0) it * 75 / 100 else it }, // titles (spec 11), then weaken
                    powerPct = s.powerPct,
                    defTarget = enemy.def.def,
                    elemMultPm = elementMultiplier(enemy.def),
                    lvlAttacker = p.level,
                    lvlTarget = enemy.def.level,
                    variancePm = variance,
                    crit = crit,
                    critMultPm = derived.critMultPm,
                ),
            )
            val amount = if (enemy.broken > 0) rawAmount * STAGGER_DAMAGE_PCT / 100 else rawAmount
            enemy.hp -= amount
            val drain = combat.items[equippedAccessory]?.accessory?.drainPm ?: 0L // an accessory that drains (spec 06)
            if (drain > 0 && p.hp > 0 && p.hp < derived.maxHp) p.hp = minOf(derived.maxHp, p.hp + maxOf(1L, amount * drain / 1000))
            enemy.hitFlash = HIT_FLASH_TICKS
            events.add(DamageEvent(enemy.position, amount, crit, false, weak = elementMultiplier(enemy.def) > 1000))
            cues.add(SimCue("hit", enemy.def.sound, enemy.position, crit, elementMultiplier(enemy.def) > 1000))
            if (enemy.hp > 0) {
                applyStatus(enemy)
                if (enemy.def.staggerPct > 0 && enemy.broken == 0) { // the stagger bar (spec 05, "Stagger")
                    enemy.stagger += amount * (if (p.usingStrike) 2 else 1)
                    if (enemy.stagger >= maxOf(1L, enemy.def.hp * enemy.def.staggerPct / 100)) {
                        enemy.stagger = 0
                        enemy.broken = STAGGER_TICKS
                        enemy.stun = maxOf(enemy.stun, STAGGER_TICKS)
                        cues.add(SimCue("parry", enemy.def.sound, enemy.position)) // the same clang as a parry
                    }
                }
            }
            if (enemy.hp <= 0) {
                enemy.hp = 0
                enemy.state = EnemyState.DEAD
                cues.add(SimCue("die", enemy.def.sound, enemy.position))
                onKill(enemy)
            }
        }
    }

    /** The element multiplier of a hit of the equipped weapon against [target] (spec 05, "Elements"). */
    private fun hitElement(): String {
        val s = if (player.usingStrike) combat.strike.skill else combat.skill
        return if (s.element != "none") s.element else combat.items[equippedWeapon]?.weapon?.element ?: "none"
    }

    private fun elementMultiplier(target: EnemyDef): Long {
        val element = hitElement()
        if (element == "none") return 1000L
        target.weaknessesPm[element]?.let { return it }
        return if (target.element == element) 500L else 1000L
    }

    private fun onKill(enemy: Enemy) {
        if (chunks != null) cleared[Pair(enemy.spawnerX, enemy.spawnerY)] = worldTicks
        val p = player
        p.kills++
        if (enemy.def.id.isNotEmpty()) bestiary[enemy.def.id] = (bestiary[enemy.def.id] ?: 0) + 1
        for (drop in enemy.def.drops) {
            if (lootRng.nextBounded(1000) < drop.weightPm) {
                var quantity = drop.qtyMin
                if (drop.qtyMax > drop.qtyMin) quantity += lootRng.nextBounded(drop.qtyMax - drop.qtyMin + 1)
                inventory[drop.item] = (inventory[drop.item] ?: 0L) + quantity
            }
        }
        grantXp(xpGain(enemy.def.xp, enemy.def.level, p.level) * (100 + titleXpPct()) / 100) // a veteran's titles (spec 11)
        story.onKill(enemy.def.id)
        // A kill gives back health and mana (spec 11, "Abilities").
        val heal = talentPower("kill_heal")
        if (heal > 0 && p.hp > 0 && p.hp < derived.maxHp) p.hp = minOf(derived.maxHp, p.hp + maxOf(1L, derived.maxHp * heal / 100))
        val mana = talentPower("kill_mana")
        if (mana > 0) p.mpU = minOf(derived.maxMp * 6000L, p.mpU + derived.maxMp * 60L * mana)
    }

    /** The ids of the titles whose condition holds, in the order of the data (spec 11). */
    fun earnedTitles(): List<String> = combat.titles.filter { titleProgress(it) >= it.count }.map { it.id }

    /** How far the player is toward a title: the number its kind counts (spec 11, "Titles"). */
    fun titleProgress(t: TitleDef): Long = when (t.kind) {
        "kills" -> player.kills.toLong()
        "kills_of" -> (bestiary[t.enemy] ?: 0).toLong()
        "level" -> player.level
        "species" -> bestiary.size.toLong()
        "quests" -> story.quests.values.count { it.done }.toLong()
        else -> (counters[t.kind] ?: 0).toLong()
    }

    /** What the earned titles add to gathering ([gather] true) or to crafting (spec 11, "Titles with effects"). */
    fun titleBonus(gather: Boolean): Long {
        val earned = earnedTitles().toSet()
        return combat.titles.filter { it.id in earned }.sumOf { if (gather) it.gatherBonus else it.craftBonus }
    }

    /** What the earned titles add to the parry window (ticks) and to the experience of a kill (percent). */
    private fun titleParryBonus(): Int = earnedTitles().toSet().let { earned -> combat.titles.filter { it.id in earned }.sumOf { it.parryBonus } }.toInt()

    private fun titleFinePm(): Long = earnedTitles().toSet().let { earned -> combat.titles.filter { it.id in earned }.sumOf { it.finePm } }

    private fun titleXpPct(): Long = earnedTitles().toSet().let { earned -> combat.titles.filter { it.id in earned }.sumOf { it.xpPct } }

    /** The percent that the earned titles add to the attack of the player's hits (spec 11, "Titles with effects"). */
    fun titleAttackPct(): Long {
        val earned = earnedTitles().toSet()
        return combat.titles.filter { it.id in earned }.sumOf { it.atkPct }
    }

    override fun grantXp(amount: Long) {
        val p = player
        p.xp += amount
        while (p.level < MAX_LEVEL && p.level - 1 < combat.xpTable.size && p.xp >= combat.xpTable[(p.level - 1).toInt()]) {
            p.xp -= combat.xpTable[(p.level - 1).toInt()]
            p.level++
            recomputeDerived()
            p.hp = derived.maxHp
        }
    }

    /** The roll for the status effect of the equipped weapon after a hit that left [enemy] alive (spec 05, "Status effects"). */
    private fun applyStatus(enemy: Enemy) {
        val element = hitElement()
        if (element == "none" || elementMultiplier(enemy.def) == 0L) return
        val (chance, ticks) =
            when (element) {
                "fire" -> Pair(350, 150)
                "water" -> Pair(400, 180)
                "wind" -> Pair(300, 45)
                "earth" -> Pair(300, 75)
                else -> Pair(350, 240) // light, dark
            }
        if (combatRng.nextBounded(1000).toInt() >= chance) return
        when (element) {
            "fire" -> {
                enemy.burn = ticks
                enemy.burnClock = 0
            }
            "water" -> enemy.chill = ticks
            "wind", "earth" -> enemy.stun = ticks
            else -> enemy.weaken = ticks
        }
    }

    private fun updateEnemy(enemy: Enemy) {
        if (enemy.state == EnemyState.DEAD) return
        if (enemy.broken > 0) enemy.broken--
        if (enemy.burn > 0) { // a burn hurts every 30 ticks, whatever the defense
            enemy.burn--
            enemy.burnClock++
            if (enemy.burnClock % 30 == 0) {
                val amount = maxOf(1L, enemy.def.hp * 3 / 100)
                enemy.hp -= amount
                events.add(DamageEvent(enemy.position, amount, false, false))
                if (enemy.hp <= 0) {
                    enemy.hp = 0
                    enemy.state = EnemyState.DEAD
                    cues.add(SimCue("die", enemy.def.sound, enemy.position))
                    onKill(enemy)
                    return
                }
            }
        }
        if (enemy.stun > 0) { // a stunned creature does nothing
            enemy.stun--
            return
        }
        behaveEnemy(enemy)
        if (enemy.chill > 0) enemy.chill--
        if (enemy.weaken > 0) enemy.weaken--
    }

    private fun behaveEnemy(enemy: Enemy) {
        val b = enemy.def.behavior
        val p = player
        val dist = distance(enemy.position.x, enemy.position.y, p.position.x, p.position.y)
        when (enemy.state) {
            EnemyState.IDLE -> if (dist <= (b.aggroX100 * combat.gift.aggroPct / 100 * rainAggroPm / 1000 * nightAggroPm / 1000).toFloat() / 100f) {
                enemy.state = EnemyState.CHASE
                enemy.stateTick = 0
                cues.add(SimCue("aggro", enemy.def.sound, enemy.position))
            }
            EnemyState.CHASE -> {
                if (dist > b.leashX100.toFloat() / 100f) {
                    enemy.state = EnemyState.RETURN
                } else if (dist <= b.attackRangeX100.toFloat() / 100f) {
                    enemy.state = EnemyState.ATTACK
                    enemy.stateTick = 0
                    cues.add(SimCue("attack", enemy.def.sound, enemy.position))
                } else {
                    moveEnemy(enemy, p.position.x, p.position.y)
                }
            }
            EnemyState.ATTACK -> {
                enemy.stateTick++
                if (enemy.stateTick == b.windupTicks && dist <= b.hitRangeX100.toFloat() / 100f && p.iframes == 0) {
                    hurtPlayer(enemy)
                }
                // not when a riposte killed it (spec 11, "Abilities")
                if (enemy.state != EnemyState.DEAD && enemy.stateTick >= b.windupTicks + b.recoveryTicks) {
                    enemy.state = EnemyState.CHASE
                    enemy.stateTick = 0
                }
            }
            EnemyState.RETURN -> {
                if (distance(enemy.position.x, enemy.position.y, enemy.home.x, enemy.home.y) <= RETURN_ARRIVAL) {
                    enemy.state = EnemyState.IDLE
                    enemy.hp = enemy.def.hp
                    enemy.stagger = 0
                } else {
                    moveEnemy(enemy, enemy.home.x, enemy.home.y)
                }
            }
            EnemyState.DEAD -> Unit
        }
    }

    private fun moveEnemy(enemy: Enemy, targetX: Float, targetY: Float) {
        val dx = targetX - enemy.position.x
        val dy = targetY - enemy.position.y
        val dist = sqrt(dx * dx + dy * dy)
        val speed = enemy.def.speedX100.toFloat() / 100f
        val step = (if (enemy.chill > 0) speed / 2f else speed) * TICK_DT
        var x = enemy.position.x
        var y = enemy.position.y
        if (dist > 0f) {
            if (dist <= step) {
                x = targetX
                y = targetY
            } else {
                x += dx / dist * step
                y += dy / dist * step
            }
        }
        enemy.position = collision.resolve(Vec2(x, y), enemy.radius)
    }

    private fun hurtPlayer(enemy: Enemy) {
        if (player.parryTicks > 0) { // parried: no damage, the attacker is stunned and the player is safe for a moment
            enemy.stun = PARRY_STUN
            count("parried")
            player.iframes = maxOf(player.iframes, PARRY_IFRAMES)
            cues.add(SimCue("parry", enemy.def.sound, player.position))
            val riposte = talentPower("riposte")
            if (riposte > 0) { // the parry hits back, with no roll (spec 11, "Abilities")
                val back = damage(
                    DamageInput(
                        atk = maxOf(derived.atk, derived.matk) * riposte / 100,
                        powerPct = 100,
                        defTarget = enemy.def.def,
                        lvlAttacker = player.level,
                        lvlTarget = enemy.def.level,
                        variancePm = 1000,
                        crit = false,
                        critMultPm = 1500,
                    ),
                )
                enemy.hp -= back
                enemy.hitFlash = HIT_FLASH_TICKS
                events.add(DamageEvent(enemy.position, back, false, false))
                if (enemy.hp <= 0) {
                    enemy.hp = 0
                    enemy.state = EnemyState.DEAD
                    cues.add(SimCue("die", enemy.def.sound, enemy.position))
                    onKill(enemy)
                }
            }
            return
        }
        val p = player
        val variance = 950L + combatRng.nextBounded(101)
        val amount = damage(
            DamageInput(
                atk = if (enemy.weaken > 0) enemy.def.atk * 75 / 100 else enemy.def.atk,
                powerPct = 100,
                defTarget = if (player.ward > 0) derived.def * (100 + player.wardPct) / 100 else derived.def, // a brew that wards (spec 06)
                lvlAttacker = enemy.def.level,
                lvlTarget = p.level,
                variancePm = variance,
            ),
        )
        p.hp -= amount
        p.iframes = PLAYER_HIT_IFRAMES
        events.add(DamageEvent(p.position, amount, false, true))
        cues.add(SimCue("hurt", enemy.def.sound, p.position))
        if (p.hp <= 0 && combat.gift.deathSaveTicks > 0 && p.deathSaveCd == 0) { // the death save (spec 18)
            p.hp = 1
            p.deathSaveCd = combat.gift.deathSaveTicks
        }
        if (p.hp <= 0) {
            p.deaths++
            p.hp = derived.maxHp
            p.position = spawn
            p.phase = AttackPhase.NONE
            p.phaseTick = 0
            p.dodgeTicks = 0
            p.dodgeCooldown = 0
            p.parryTicks = 0
            p.parryCooldown = 0
            p.clearStatus()
            p.mpU = derived.maxMp * 6000L
            p.iframes = RESPAWN_IFRAMES
            return
        }
        val element = enemy.def.element // the status of the creature's element (spec 05, "Status effects on the player")
        if (element == "none" || element.isEmpty()) return
        val (chance, ticks) =
            when (element) {
                "fire" -> Pair(350, 150)
                "water" -> Pair(400, 180)
                "wind" -> Pair(300, 45)
                "earth" -> Pair(300, 75)
                else -> Pair(350, 240) // light, dark
            }
        if (combatRng.nextBounded(1000).toInt() >= chance) return
        when (element) {
            "fire" -> {
                p.burn = ticks
                p.burnClock = 0
            }
            "water" -> p.chill = ticks
            "wind", "earth" -> p.stun = ticks
            else -> p.weaken = ticks
        }
    }

    /** Everything that changes while playing (spec 12). */
    fun capture(): SaveState {
        val p = player
        return SaveState(
            x = p.position.x, y = p.position.y, facingX = p.facing.x, facingY = p.facing.y, facingLeft = p.facingLeft,
            moving = p.moving, clipTick = p.clipTick, hp = p.hp, level = p.level, xp = p.xp, deaths = p.deaths,
            kills = p.kills, iframes = p.iframes, cooldown = p.cooldown, phase = p.phase, phaseTick = p.phaseTick,
            hitSet = hitSet.toList(), combatState = combatRng.state, combatInc = combatRng.inc,
            lootState = lootRng.state, lootInc = lootRng.inc,
            enemies = enemies.map {
                SaveEnemy(it.position.x, it.position.y, it.hp, it.state, it.stateTick, if (chunks != null) Pair(it.spawnerX, it.spawnerY) else null)
            },
            cleared = cleared.map { (spawner, died) -> ClearedSpawner(spawner.first, spawner.second, died) },
            worldTicks = worldTicks,
            explored = explored.toList(),
            stones = stones.toList(),
            bestiary = bestiary.toMap(),
            companionStay = companionStaying,
            companionBond = companionBond,
            counters = counters.toMap(),
            talents = talents.toMap(),
            companion = if (combat.companion != null) Triple((companionPosition ?: player.position).x, (companionPosition ?: player.position).y, companionCooldown) else null,
            equippedWeapon = equippedWeapon,
            equippedArmor = equippedArmor,
            equippedAccessory = equippedAccessory,
            inventory = HashMap(inventory), story = story.capture(),
        )
    }

    /** Overwrites the mutable state. On a mismatch with the loaded data it fails and changes nothing. */
    fun restore(s: SaveState): Result<Unit> {
        if (chunks != null) {
            // The saved enemies must be exactly those of the window around the saved position (spec 12).
            val cx = chunkOf(floor(s.x).toInt())
            val cy = chunkOf(floor(s.y).toInt())
            chunks.keepAround(cx, cy)
            val clearedSet = s.cleared.map { Pair(it.x, it.y) }.toSet()
            val inWindow = HashSet<Pair<Int, Int>>()
            for (j in cy - ACTIVE_RADIUS..cy + ACTIVE_RADIUS) {
                for (i in cx - ACTIVE_RADIUS..cx + ACTIVE_RADIUS) inWindow.addAll(chunks.find(i, j)!!.spawners)
            }
            val found = HashSet<Pair<Int, Int>>()
            var valid = s.hitSet.size == s.enemies.size
            for (e in s.enemies) {
                val spawner = e.spawner
                // Every enemy belongs to a spawner of the window; the enemy of a cleared spawner is dead.
                valid = valid && spawner != null && spawner in inWindow && found.add(spawner) &&
                    (spawner !in clearedSet || e.state == EnemyState.DEAD)
            }
            for (spawner in inWindow) valid = valid && (spawner in clearedSet || spawner in found)
            if (!valid) return Result.failure(IllegalArgumentException("the save has different enemies than the generated world"))
        } else if (s.enemies.size != enemies.size || s.hitSet.size != hitSet.size) {
            return Result.failure(IllegalArgumentException("the save has a different number of enemies than the loaded map"))
        }
        if (s.level < 1 || s.level > MAX_LEVEL) return Result.failure(IllegalArgumentException("invalid level in the save"))
        if (!story.restore(s.story)) {
            return Result.failure(IllegalArgumentException("the save refers to a quest or dialogue that does not exist"))
        }
        val p = player
        p.position = Vec2(s.x, s.y)
        p.facing = Vec2(s.facingX, s.facingY)
        p.facingLeft = s.facingLeft
        p.moving = s.moving
        p.clipTick = s.clipTick
        p.level = s.level
        recomputeDerived()
        p.hp = s.hp
        p.xp = s.xp
        p.deaths = s.deaths
        p.kills = s.kills
        p.iframes = s.iframes
        p.cooldown = s.cooldown
        p.deathSaveCd = 0
        p.dodgeTicks = 0 // a roll in progress is not saved (spec 05)
        p.dodgeCooldown = 0
        p.parryTicks = 0
        p.parryCooldown = 0
        p.clearStatus()
        p.mpU = derived.maxMp * 6000L // nor is the mana: a loaded game starts full
        p.usingStrike = false
        p.phase = s.phase
        p.phaseTick = s.phaseTick
        if (chunks != null) {
            enemies.clear()
            for (e in s.enemies) {
                val spawner = requireNotNull(e.spawner)
                val enemy = Enemy(streamEnemyAt(spawner.first, spawner.second), Vec2(spawner.first + 0.5f, spawner.second + 0.5f))
                enemy.spawnerX = spawner.first
                enemy.spawnerY = spawner.second
                enemies.add(enemy)
            }
            hitSet.clear()
            hitSet.addAll(s.hitSet)
            cleared.clear()
            for (c in s.cleared) cleared[Pair(c.x, c.y)] = c.died
            npcList.clear()
            for (j in chunkOf(floor(s.y).toInt()) - ACTIVE_RADIUS..chunkOf(floor(s.y).toInt()) + ACTIVE_RADIUS) {
                for (i in chunkOf(floor(s.x).toInt()) - ACTIVE_RADIUS..chunkOf(floor(s.x).toInt()) + ACTIVE_RADIUS) addChunkPeople(i, j)
            }
            rebuildNpcCircles()
            windowValid = true
            windowX = chunkOf(floor(s.x).toInt())
            windowY = chunkOf(floor(s.y).toInt())
        } else {
            s.hitSet.forEachIndexed { i, hit -> hitSet[i] = hit }
        }
        combatRng.setState(s.combatState, s.combatInc)
        lootRng.setState(s.lootState, s.lootInc)
        for ((i, e) in enemies.withIndex()) {
            e.position = Vec2(s.enemies[i].x, s.enemies[i].y)
            e.hp = s.enemies[i].hp
            e.state = s.enemies[i].state
            e.stateTick = s.enemies[i].stateTick
            e.hitFlash = 0
        }
        inventory.clear()
        inventory.putAll(s.inventory)
        equippedWeapon = s.equippedWeapon ?: combat.startWeapon
        equippedArmor = s.equippedArmor
        equippedAccessory = s.equippedAccessory
        shop = null
        board = null
        travel = null
        stones.clear()
        stones.addAll(s.stones)
        bestiary.clear()
        bestiary.putAll(s.bestiary)
        counters.clear()
        counters.putAll(s.counters)
        talents.clear()
        talents.putAll(s.talents)
        recomputeDerived() // the talents change the derived stats
        combat.companion?.let { c -> // a save without a companion (an older one) puts it next to the player
            val saved = s.companion
            companionPosition = if (saved != null) Vec2(saved.first, saved.second) else player.position
            companionCooldown = saved?.third ?: c.cooldownTicks
            companionStaying = saved != null && s.companionStay
            companionBond = if (saved != null) s.companionBond else 0
        }
        recomputeDerived()
        player.hp = minOf(s.hp, derived.maxHp)
        explored.clear()
        explored.addAll(s.explored)
        markExplored()
        worldTicks = if (s.worldTicks >= 0) s.worldTicks else chunks?.params?.time?.startTick ?: 0L
        if (chunks != null && windowValid) refreshPeople(windowX, windowY) // the people of the saved time of day
        events.clear()
        return Result.success(Unit)
    }

    /** View of [viewW] x [viewH] tiles centered on the player and clamped to the map. */
    fun camera(viewW: Float, viewH: Float): Camera =
        Camera(axisOrigin(player.position.x, viewW, map.width.toFloat()), axisOrigin(player.position.y, viewH, map.height.toFloat()))
}
