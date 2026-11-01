package io.github.progliodario.aethermoor.core.sim

import io.github.progliodario.aethermoor.core.DamageInput
import io.github.progliodario.aethermoor.core.DerivedStats
import io.github.progliodario.aethermoor.core.Equipment
import io.github.progliodario.aethermoor.core.TimeSample
import io.github.progliodario.aethermoor.core.damage
import io.github.progliodario.aethermoor.core.deriveStream
import io.github.progliodario.aethermoor.core.derivedStats
import io.github.progliodario.aethermoor.core.sampleTime
import io.github.progliodario.aethermoor.core.xpGain
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.floor
import kotlin.math.max
import kotlin.math.sqrt

// The world: map, player, enemies, combat and camera. Spec: docs/spec/02, 03 and 05.
// Keep this file in step with desktop/src/sim/world.cpp: same operations, same order, same random draws.

private const val PLAYER_HIT_IFRAMES = 45
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
    val radius: Float get() = def.radiusX100 / 100f
}

/** Something a client may want to show (numbers floating up from a hit); not part of the contract. */
data class DamageEvent(val position: Vec2, val amount: Long, val crit: Boolean, val onPlayer: Boolean)

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

    /** Simulation ticks since the world was created (spec 08). */
    var worldTicks: Long = chunks?.params?.time?.startTick ?: 0L
        private set
    private var windowValid = false
    private var windowX = 0
    private var windowY = 0
    private val events = ArrayList<DamageEvent>()

    val story = Story(combat.story, this)

    override val level: Long get() = player.level
    override val playerX: Float get() = player.position.x
    override val playerY: Float get() = player.position.y

    init {
        for (npc in combat.story.npcs) collision.addProp(Circle(npc.x, npc.y, NPC_RADIUS))
        if (combat.enabled) {
            player.level = combat.startLevel.toLong()
            recomputeDerived()
            player.hp = derived.maxHp
            for (s in combat.spawns) enemies.add(Enemy(s.def, Vec2(s.x, s.y)))
            inventory.putAll(combat.startInventory)
            syncWindow()
        }
    }

    /** Day, light and weather of the streamed world now (spec 08); null on a fixed map. */
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

    private fun addChunkEnemies(cx: Int, cy: Int) {
        val def = combat.streamEnemy ?: return
        val store = chunks ?: return
        val chunk = store.find(cx, cy) ?: return
        for ((sx, sy) in chunk.spawners) {
            val died = cleared[Pair(sx, sy)]
            if (died != null) {
                // A spawner whose enemy has been dead long enough is ready again when its chunk enters the window (spec 08).
                if (worldTicks - died < store.params.spawnerRespawnTicks) continue
                cleared.remove(Pair(sx, sy))
            }
            val enemy = Enemy(def, Vec2(sx + 0.5f, sy + 0.5f))
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
                if (!windowValid || !insideWindow(i, j, windowX, windowY)) addChunkEnemies(i, j)
            }
        }
        windowValid = true
        windowX = cx
        windowY = cy
    }

    private fun recomputeDerived() {
        derived = derivedStats(
            player.level,
            primaryAtLevel(combat.player, player.level),
            Equipment(weaponAtk = combat.player.weaponAtk, weaponMatk = combat.player.weaponMatk),
        )
    }

    /** Events produced since the last call (damage numbers). */
    fun takeEvents(): List<DamageEvent> {
        val copy = ArrayList(events)
        events.clear()
        return copy
    }

    /** One fixed tick (1/60 s) with the raw movement input and the attack input of this tick. */
    fun tick(rawXIn: Float, rawYIn: Float, attackIn: Boolean = false) {
        worldTicks++
        syncWindow()
        val frozen = story.dialogueActive
        val rawX = if (frozen) 0f else rawXIn
        val rawY = if (frozen) 0f else rawYIn
        val attack = attackIn && !frozen
        val p = player
        val enabled = combat.enabled
        if (p.iframes > 0) p.iframes--
        if (p.cooldown > 0) p.cooldown--

        val direction = normalizeInput(rawX, rawY)
        val moving = direction.x != 0f || direction.y != 0f
        if (enabled && moving && (p.phase == AttackPhase.NONE || p.phase == AttackPhase.STARTUP)) {
            val length = sqrt(direction.x * direction.x + direction.y * direction.y)
            p.facing = Vec2(direction.x / length, direction.y / length)
        }
        var speed = if (enabled) derived.moveSpeedX100.toFloat() / 100f else speedTilesPerS
        if (enabled && p.phase != AttackPhase.NONE) speed *= ATTACK_MOVE_MULT
        p.position = collision.step(p.position, direction, speed)

        if (direction.x != 0f) p.facingLeft = direction.x < 0f
        if (moving != p.moving) {
            p.moving = moving
            p.clipTick = 0
        } else {
            p.clipTick++
        }

        if (!enabled) return
        if (attack && p.phase == AttackPhase.NONE && p.cooldown == 0) {
            p.phase = AttackPhase.STARTUP
            p.phaseTick = 0
            p.cooldown = combat.skill.cooldown
            hitSet.replaceAll { false }
        }
        advanceAttack()
        for (enemy in enemies) {
            updateEnemy(enemy)
            if (enemy.hitFlash > 0) enemy.hitFlash--
        }
    }

    private fun advanceAttack() {
        val p = player
        val s = combat.skill
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
        val s = combat.skill
        val cosHalf = cos(s.angleDeg.toDouble() / 2.0 * PI / 180.0).toFloat()
        for ((index, enemy) in enemies.withIndex()) {
            if (enemy.state == EnemyState.DEAD || hitSet[index]) continue
            val dx = enemy.position.x - p.position.x
            val dy = enemy.position.y - p.position.y
            val dist = sqrt(dx * dx + dy * dy)
            if (dist > s.radiusX100.toFloat() / 100f + enemy.radius) continue
            if (dist > 0f) {
                val dot = (dx * p.facing.x + dy * p.facing.y) / dist
                if (dot < cosHalf) continue
            }
            hitSet[index] = true
            val variance = 950L + combatRng.nextBounded(101)
            val crit = combatRng.nextBounded(1000) < derived.critChancePm
            val amount = damage(
                DamageInput(
                    atk = derived.atk,
                    powerPct = s.powerPct,
                    defTarget = enemy.def.def,
                    lvlAttacker = p.level,
                    lvlTarget = enemy.def.level,
                    variancePm = variance,
                    crit = crit,
                    critMultPm = derived.critMultPm,
                ),
            )
            enemy.hp -= amount
            enemy.hitFlash = HIT_FLASH_TICKS
            events.add(DamageEvent(enemy.position, amount, crit, false))
            if (enemy.hp <= 0) {
                enemy.hp = 0
                enemy.state = EnemyState.DEAD
                onKill(enemy)
            }
        }
    }

    private fun onKill(enemy: Enemy) {
        if (chunks != null) cleared[Pair(enemy.spawnerX, enemy.spawnerY)] = worldTicks
        val p = player
        p.kills++
        for (drop in enemy.def.drops) {
            if (lootRng.nextBounded(1000) < drop.weightPm) {
                var quantity = drop.qtyMin
                if (drop.qtyMax > drop.qtyMin) quantity += lootRng.nextBounded(drop.qtyMax - drop.qtyMin + 1)
                inventory[drop.item] = (inventory[drop.item] ?: 0L) + quantity
            }
        }
        grantXp(xpGain(enemy.def.xp, enemy.def.level, p.level))
        story.onKill(enemy.def.id)
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

    private fun updateEnemy(enemy: Enemy) {
        if (enemy.state == EnemyState.DEAD) return
        val b = enemy.def.behavior
        val p = player
        val dist = distance(enemy.position.x, enemy.position.y, p.position.x, p.position.y)
        when (enemy.state) {
            EnemyState.IDLE -> if (dist <= b.aggroX100.toFloat() / 100f) {
                enemy.state = EnemyState.CHASE
                enemy.stateTick = 0
            }
            EnemyState.CHASE -> {
                if (dist > b.leashX100.toFloat() / 100f) {
                    enemy.state = EnemyState.RETURN
                } else if (dist <= b.attackRangeX100.toFloat() / 100f) {
                    enemy.state = EnemyState.ATTACK
                    enemy.stateTick = 0
                } else {
                    moveEnemy(enemy, p.position.x, p.position.y)
                }
            }
            EnemyState.ATTACK -> {
                enemy.stateTick++
                if (enemy.stateTick == b.windupTicks && dist <= b.hitRangeX100.toFloat() / 100f && p.iframes == 0) {
                    hurtPlayer(enemy)
                }
                if (enemy.stateTick >= b.windupTicks + b.recoveryTicks) {
                    enemy.state = EnemyState.CHASE
                    enemy.stateTick = 0
                }
            }
            EnemyState.RETURN -> {
                if (distance(enemy.position.x, enemy.position.y, enemy.home.x, enemy.home.y) <= RETURN_ARRIVAL) {
                    enemy.state = EnemyState.IDLE
                    enemy.hp = enemy.def.hp
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
        val step = (enemy.def.speedX100.toFloat() / 100f) * TICK_DT
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
        val p = player
        val variance = 950L + combatRng.nextBounded(101)
        val amount = damage(
            DamageInput(
                atk = enemy.def.atk,
                powerPct = 100,
                defTarget = derived.def,
                lvlAttacker = enemy.def.level,
                lvlTarget = p.level,
                variancePm = variance,
            ),
        )
        p.hp -= amount
        p.iframes = PLAYER_HIT_IFRAMES
        events.add(DamageEvent(p.position, amount, false, true))
        if (p.hp <= 0) {
            p.deaths++
            p.hp = derived.maxHp
            p.position = spawn
            p.phase = AttackPhase.NONE
            p.phaseTick = 0
            p.iframes = RESPAWN_IFRAMES
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
        p.phase = s.phase
        p.phaseTick = s.phaseTick
        if (chunks != null) {
            val def = requireNotNull(combat.streamEnemy) { "streamed world without an enemy" }
            enemies.clear()
            for (e in s.enemies) {
                val spawner = requireNotNull(e.spawner)
                val enemy = Enemy(def, Vec2(spawner.first + 0.5f, spawner.second + 0.5f))
                enemy.spawnerX = spawner.first
                enemy.spawnerY = spawner.second
                enemies.add(enemy)
            }
            hitSet.clear()
            hitSet.addAll(s.hitSet)
            cleared.clear()
            for (c in s.cleared) cleared[Pair(c.x, c.y)] = c.died
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
        worldTicks = if (s.worldTicks >= 0) s.worldTicks else chunks?.params?.time?.startTick ?: 0L
        events.clear()
        return Result.success(Unit)
    }

    /** View of [viewW] x [viewH] tiles centered on the player and clamped to the map. */
    fun camera(viewW: Float, viewH: Float): Camera =
        Camera(axisOrigin(player.position.x, viewW, map.width.toFloat()), axisOrigin(player.position.y, viewH, map.height.toFloat()))
}
