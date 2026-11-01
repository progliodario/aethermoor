package io.github.progliodario.aethermoor.core.sim

import io.github.progliodario.aethermoor.core.DamageInput
import io.github.progliodario.aethermoor.core.DerivedStats
import io.github.progliodario.aethermoor.core.Equipment
import io.github.progliodario.aethermoor.core.damage
import io.github.progliodario.aethermoor.core.deriveStream
import io.github.progliodario.aethermoor.core.derivedStats
import io.github.progliodario.aethermoor.core.xpGain
import kotlin.math.PI
import kotlin.math.cos
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
) : StoryHost {
    val collision: CollisionWorld = buildCollision(map, tileset)
    private val combatRng = deriveStream(combat.seed, "combat")
    private val lootRng = deriveStream(combat.seed, "loot")
    private val spawn: Vec2 = collision.resolve(Vec2(map.spawnX, map.spawnY))

    val player = Player(spawn)
    var derived: DerivedStats = derivedStats(1, combat.player.base, Equipment())
        private set
    val enemies = ArrayList<Enemy>()
    override val inventory = java.util.TreeMap<String, Long>()
    private val hitSet = BooleanArray(combat.spawns.size)
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
        }
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
            hitSet.fill(false)
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

    /** View of [viewW] x [viewH] tiles centered on the player and clamped to the map. */
    fun camera(viewW: Float, viewH: Float): Camera =
        Camera(axisOrigin(player.position.x, viewW, map.width.toFloat()), axisOrigin(player.position.y, viewH, map.height.toFloat()))
}
