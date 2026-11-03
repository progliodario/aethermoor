package io.github.progliodario.aethermoor.core.sim

import io.github.progliodario.aethermoor.core.DamageInput
import io.github.progliodario.aethermoor.core.DerivedStats
import io.github.progliodario.aethermoor.core.Equipment
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
import io.github.progliodario.aethermoor.core.settlementContaining
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

    /** The item ids worn (spec 06). */
    var equippedWeapon: String = combat.startWeapon
        private set
    var equippedArmor: String = combat.startArmor
        private set

    /** The board of a settlement (spec 07, "Guild"): the settlement, the day and its offers. */
    class Board(val settlement: Settlement, val day: Long, val offers: List<Offer>)

    /** A stop of the Threshold Stone list: the stone tile, the name of its settlement and the text key of its region (spec 09). */
    class StoneStop(val x: Int, val y: Int, val place: String, val region: String)

    /** The list of stones offered by a stone being used: [here] is the index of that stone, [fresh] tells it was woken just now. */
    class Travel(val stops: List<StoneStop>, val here: Int, val fresh: Boolean)

    /** The Threshold Stones that were used, in order of waking (spec 09). */
    val stones = ArrayList<Pair<Int, Int>>()

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
        )
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

    override fun healFull() {
        player.hp = derived.maxHp
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
        shop = if (store != null) {
            val region = store.params.regions[regionAt(store.params, floor(player.position.x).toInt(), floor(player.position.y).toInt())]
            ShopDef(region.shopPricePm, region.shopStock)
        } else {
            combat.shop
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
        return if (item.price <= 0) 0L else maxOf(1L, item.price * open.pricePm / 1000)
    }

    /** What the shop pays for an item, 0 when it cannot be sold. */
    fun sellPrice(itemId: String): Long {
        val item = combat.items[itemId] ?: return 0L
        return if (item.price <= 0) 0L else maxOf(1L, item.price / 2)
    }

    /** Equips a weapon or an armor of the inventory (spec 06). Returns false, changing nothing, when refused. */
    fun equip(itemId: String): Boolean {
        val item = combat.items[itemId] ?: return false
        if ((inventory[itemId] ?: 0L) < 1L) return false
        if (item.weapon != null && item.kind == "weapon" && equippedWeapon != itemId) {
            equippedWeapon = itemId
        } else if (item.armor != null && item.kind == "armor" && equippedArmor != itemId) {
            equippedArmor = itemId
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
        if (owned == 1L && (itemId == equippedWeapon || itemId == equippedArmor)) return false
        story.gold += sellPrice(itemId)
        if (owned == 1L) inventory.remove(itemId) else inventory[itemId] = owned - 1L
        return true
    }

    /** Uses one item of the inventory (spec 06). Returns false, changing nothing, when it is refused. */
    fun useItem(itemId: String): Boolean {
        if (story.dialogueActive) return false
        val item = combat.items[itemId] ?: return false
        if ((inventory[itemId] ?: 0L) < 1L) return false
        val heal = item.effects.filter { it.effect == "heal" }.sumOf { it.amount }
        if (heal <= 0L || player.hp >= derived.maxHp) return false
        player.hp = minOf(derived.maxHp, player.hp + heal)
        val left = (inventory[itemId] ?: 0L) - 1L
        if (left == 0L) inventory.remove(itemId) else inventory[itemId] = left
        return true
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
        if (chunks != null && windowValid && timeOfDayPm() != routineTod) refreshPeople(windowX, windowY) // somebody goes home or comes out (spec 08)
        markExplored()
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
            explored = explored.toList(),
            stones = stones.toList(),
            equippedWeapon = equippedWeapon,
            equippedArmor = equippedArmor,
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
        shop = null
        board = null
        travel = null
        stones.clear()
        stones.addAll(s.stones)
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
