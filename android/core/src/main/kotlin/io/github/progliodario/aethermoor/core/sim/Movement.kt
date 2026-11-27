package io.github.progliodario.aethermoor.core.sim

import kotlin.math.floor
import kotlin.math.min
import kotlin.math.sqrt

// Player movement and collision. Spec: docs/spec/02-entities-and-movement.md.
// Reference: tools/reference/movement.py. Same operations and order as desktop/src/sim/movement.cpp (float32).

const val TICK_DT: Float = 1f / 60f
const val INPUT_DEADZONE: Float = 0.15f
const val PLAYER_RADIUS: Float = 0.3f

data class Vec2(val x: Float = 0f, val y: Float = 0f)

data class Circle(val x: Float, val y: Float, val radius: Float)

/** How many times [CollisionWorld.resolve] pushes a body out of what it overlaps, at most (spec 02, "Collisions"). */
private const val RESOLVE_PASSES = 4

/** Dead zone, then clamp to the unit circle. */
fun normalizeInput(x: Float, y: Float): Vec2 {
    val length = sqrt(x * x + y * y)
    if (length < INPUT_DEADZONE) return Vec2(0f, 0f)
    if (length > 1f) return Vec2(x / length, y / length)
    return Vec2(x, y)
}

private fun clampf(v: Float, lo: Float, hi: Float) = if (v < lo) {
    lo
} else if (v > hi) {
    hi
} else {
    v
}

/** A body being pushed out of what it overlaps, one piece at a time (spec 02, "Collisions"). */
private class Pushed(var x: Float, var y: Float, private val r: Float) {
    /** Pushes the body out of a solid cell; says whether it moved. */
    fun outOfTile(tx: Int, ty: Int): Boolean {
        val cx = clampf(x, tx.toFloat(), (tx + 1).toFloat())
        val cy = clampf(y, ty.toFloat(), (ty + 1).toFloat())
        val dx = x - cx
        val dy = y - cy
        val d2 = dx * dx + dy * dy
        if (d2 >= r * r) return false
        if (d2 > 0f) {
            val d = sqrt(d2)
            val k = (r - d) / d
            x += dx * k
            y += dy * k
            return true
        }
        // The body sits exactly on the corner: it leaves by the nearest side.
        val left = x - tx.toFloat()
        val right = (tx + 1).toFloat() - x
        val top = y - ty.toFloat()
        val bottom = (ty + 1).toFloat() - y
        val m = min(min(left, right), min(top, bottom))
        if (m == left) {
            x = tx.toFloat() - r
        } else if (m == right) {
            x = (tx + 1).toFloat() + r
        } else if (m == top) {
            y = ty.toFloat() - r
        } else {
            y = (ty + 1).toFloat() + r
        }
        return true
    }

    /** Pushes the body out of a prop circle; says whether it moved. */
    fun outOfCircle(cx: Float, cy: Float, radius: Float): Boolean {
        if (radius <= 0f) return false // a prop of radius 0 is a mark on the ground (a trap): it blocks nothing (spec 02)
        val dx = x - cx
        val dy = y - cy
        val d2 = dx * dx + dy * dy
        val md = r + radius
        if (d2 >= md * md) return false
        if (d2 > 0f) {
            val d = sqrt(d2)
            val k = (md - d) / d
            x += dx * k
            y += dy * k
        } else {
            x = cx + md
        }
        return true
    }
}

class CollisionWorld(
    val width: Int,
    val height: Int,
    private val solid: BooleanArray,
    props: List<Circle>,
    /** A streamed world: tiles and props come from the loaded chunks (an unloaded tile is solid). */
    private val chunks: ChunkStore? = null,
) {
    private val props = props.toMutableList()

    fun addProp(prop: Circle) {
        props.add(prop)
    }

    /** Circles that come and go with the world (settlement people); owned by the caller. */
    var dynamicProps: List<Circle> = emptyList()

    /** Cells outside the map are solid. */
    fun isSolid(tx: Int, ty: Int): Boolean {
        if (chunks != null) return chunks.isSolid(tx, ty)
        if (tx < 0 || ty < 0 || tx >= width || ty >= height) return true
        return solid[ty * width + tx]
    }

    /** Pushes (x, y) out of solid tiles and prop circles (spec: resolve). */
    fun resolve(start: Vec2, radius: Float = PLAYER_RADIUS): Vec2 {
        val body = Pushed(start.x, start.y, radius)
        var moved = true
        var pass = 0
        while (moved && pass < RESOLVE_PASSES) { // until nothing pushes, at most RESOLVE_PASSES times
            pass++
            moved = pushOutOfTiles(body, radius)
            for (prop in props) moved = body.outOfCircle(prop.x, prop.y, prop.radius) || moved
            for (prop in dynamicProps) moved = body.outOfCircle(prop.x, prop.y, prop.radius) || moved
            chunks?.forEachPropNear(body.x, body.y) { moved = body.outOfCircle(it.x, it.y, it.radius) || moved }
        }
        return Vec2(body.x, body.y)
    }

    /** Pushes the body out of the solid cells it overlaps; says whether it moved. */
    private fun pushOutOfTiles(body: Pushed, radius: Float): Boolean {
        var moved = false
        val ty0 = floor(body.y - radius).toInt()
        val ty1 = floor(body.y + radius).toInt()
        val tx0 = floor(body.x - radius).toInt()
        val tx1 = floor(body.x + radius).toInt()
        for (ty in ty0..ty1) {
            for (tx in tx0..tx1) {
                if (isSolid(tx, ty)) moved = body.outOfTile(tx, ty) || moved
            }
        }
        return moved
    }

    /** One tick of movement: X axis, resolve, Y axis, resolve. */
    fun step(position: Vec2, direction: Vec2, speedTilesPerS: Float, radius: Float = PLAYER_RADIUS): Vec2 {
        val movedX = resolve(Vec2(position.x + direction.x * speedTilesPerS * TICK_DT, position.y), radius)
        return resolve(Vec2(movedX.x, movedX.y + direction.y * speedTilesPerS * TICK_DT), radius)
    }
}
