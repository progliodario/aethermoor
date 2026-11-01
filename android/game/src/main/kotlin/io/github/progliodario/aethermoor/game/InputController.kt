package io.github.progliodario.aethermoor.game

import com.badlogic.gdx.Gdx
import com.badlogic.gdx.Input
import kotlin.math.sqrt

/**
 * Movement input (spec 16): WASD/arrow keys, and a floating touch stick. The first touch on the left half of
 * the screen is the stick origin; dragging up to [STICK_RADIUS_DP] from it gives a vector of length 1.
 */
class InputController {
    private var stickPointer = -1
    private var originX = 0f
    private var originY = 0f

    /** Stick origin and current position in screen pixels (y down), or null when no stick is active. */
    var stickOrigin: Pair<Float, Float>? = null
        private set
    var stickPosition: Pair<Float, Float>? = null
        private set

    /** Raw movement vector for this frame; the simulation normalizes it. */
    fun read(): Pair<Float, Float> {
        var x = 0f
        var y = 0f
        val input = Gdx.input
        if (input.isKeyPressed(Input.Keys.A) || input.isKeyPressed(Input.Keys.LEFT)) x -= 1f
        if (input.isKeyPressed(Input.Keys.D) || input.isKeyPressed(Input.Keys.RIGHT)) x += 1f
        if (input.isKeyPressed(Input.Keys.W) || input.isKeyPressed(Input.Keys.UP)) y -= 1f
        if (input.isKeyPressed(Input.Keys.S) || input.isKeyPressed(Input.Keys.DOWN)) y += 1f

        val touch = readStick()
        if (x == 0f && y == 0f) {
            x = touch.first
            y = touch.second
        }
        return Pair(x, y)
    }

    private fun readStick(): Pair<Float, Float> {
        val input = Gdx.input
        val radius = STICK_RADIUS_DP * Gdx.graphics.density
        if (stickPointer >= 0 && !input.isTouched(stickPointer)) {
            stickPointer = -1
            stickOrigin = null
            stickPosition = null
        }
        if (stickPointer < 0) {
            for (pointer in 0 until MAX_POINTERS) {
                if (input.isTouched(pointer) && input.getX(pointer) < Gdx.graphics.width / 2) {
                    stickPointer = pointer
                    originX = input.getX(pointer).toFloat()
                    originY = input.getY(pointer).toFloat()
                    break
                }
            }
        }
        if (stickPointer < 0) return Pair(0f, 0f)

        val dx = input.getX(stickPointer) - originX
        val dy = input.getY(stickPointer) - originY
        val length = sqrt(dx * dx + dy * dy)
        stickOrigin = Pair(originX, originY)
        stickPosition = Pair(input.getX(stickPointer).toFloat(), input.getY(stickPointer).toFloat())
        val scale = if (length > radius) radius / length else 1f
        return Pair(dx * scale / radius, dy * scale / radius)
    }

    companion object {
        const val STICK_RADIUS_DP = 64f
        private const val MAX_POINTERS = 5
    }
}
