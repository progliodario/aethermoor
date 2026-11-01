package io.github.progliodario.aethermoor.core.sim

// The M2 world: map, player, animation state and camera. Spec: docs/spec/02 and docs/spec/03.

data class Player(
    val position: Vec2,
    val moving: Boolean = false,
    val facingLeft: Boolean = false,
    /** Ticks since the current clip started. */
    val clipTick: Int = 0,
)

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

class WorldSim(val map: TileMap, val tileset: Tileset, private val speedTilesPerS: Float) {
    val collision: CollisionWorld = buildCollision(map, tileset)

    var player: Player = Player(collision.resolve(Vec2(map.spawnX, map.spawnY)))
        private set

    /** One fixed tick (1/60 s) with the raw movement input of this tick. */
    fun tick(rawX: Float, rawY: Float) {
        val direction = normalizeInput(rawX, rawY)
        val moving = direction.x != 0f || direction.y != 0f
        val position = collision.step(player.position, direction, speedTilesPerS)
        val facingLeft = if (direction.x != 0f) direction.x < 0f else player.facingLeft
        val clipTick = if (moving != player.moving) 0 else player.clipTick + 1
        player = Player(position, moving, facingLeft, clipTick)
    }

    /** View of [viewW] x [viewH] tiles centered on the player and clamped to the map. */
    fun camera(viewW: Float, viewH: Float): Camera =
        Camera(axisOrigin(player.position.x, viewW, map.width.toFloat()), axisOrigin(player.position.y, viewH, map.height.toFloat()))
}
