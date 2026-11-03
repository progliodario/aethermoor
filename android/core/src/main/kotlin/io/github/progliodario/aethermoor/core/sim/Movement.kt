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

/** Dead zone, then clamp to the unit circle. */
fun normalizeInput(x: Float, y: Float): Vec2 {
    val length = sqrt(x * x + y * y)
    if (length < INPUT_DEADZONE) return Vec2(0f, 0f)
    if (length > 1f) return Vec2(x / length, y / length)
    return Vec2(x, y)
}

private fun clampf(v: Float, lo: Float, hi: Float) = if (v < lo) lo else if (v > hi) hi else v

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
        var x = start.x
        var y = start.y
        val r = radius
        for (iteration in 0 until 4) {
            var moved = false
            val ty0 = floor(y - r).toInt()
            val ty1 = floor(y + r).toInt()
            val tx0 = floor(x - r).toInt()
            val tx1 = floor(x + r).toInt()
            for (ty in ty0..ty1) {
                for (tx in tx0..tx1) {
                    if (!isSolid(tx, ty)) continue
                    val cx = clampf(x, tx.toFloat(), (tx + 1).toFloat())
                    val cy = clampf(y, ty.toFloat(), (ty + 1).toFloat())
                    val dx = x - cx
                    val dy = y - cy
                    val d2 = dx * dx + dy * dy
                    if (d2 < r * r) {
                        if (d2 > 0f) {
                            val d = sqrt(d2)
                            val k = (r - d) / d
                            x += dx * k
                            y += dy * k
                        } else {
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
                        }
                        moved = true
                    }
                }
            }
            fun pushOut(cx: Float, cy: Float, radius: Float) {
                val dx = x - cx
                val dy = y - cy
                val d2 = dx * dx + dy * dy
                val md = r + radius
                if (d2 < md * md) {
                    if (d2 > 0f) {
                        val d = sqrt(d2)
                        val k = (md - d) / d
                        x += dx * k
                        y += dy * k
                    } else {
                        x = cx + md
                    }
                    moved = true
                }
            }
            for (prop in props) pushOut(prop.x, prop.y, prop.radius)
            for (prop in dynamicProps) pushOut(prop.x, prop.y, prop.radius)
            chunks?.forEachPropNear(x, y) { pushOut(it.x, it.y, it.radius) }
            if (!moved) break
        }
        return Vec2(x, y)
    }

    /** One tick of movement: X axis, resolve, Y axis, resolve. */
    fun step(position: Vec2, direction: Vec2, speedTilesPerS: Float, radius: Float = PLAYER_RADIUS): Vec2 {
        val movedX = resolve(Vec2(position.x + direction.x * speedTilesPerS * TICK_DT, position.y), radius)
        return resolve(Vec2(movedX.x, movedX.y + direction.y * speedTilesPerS * TICK_DT), radius)
    }
}
