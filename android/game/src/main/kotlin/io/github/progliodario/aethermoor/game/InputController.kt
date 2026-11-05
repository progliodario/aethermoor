package io.github.progliodario.aethermoor.game

import com.badlogic.gdx.Gdx
import com.badlogic.gdx.Input
import kotlin.math.sqrt

/** Input of one frame: raw movement vector (the simulation normalizes it) and the attack button. */
data class FrameInput(val x: Float, val y: Float, val attack: Boolean, val dodge: Boolean = false)

/**
 * Input (spec 16): WASD/arrow keys and J/Space to attack, and on touch screens a floating stick on the left half
 * (the first touch is the origin; dragging up to [STICK_RADIUS_DP] gives a vector of length 1) and an attack
 * button: any touch on the right half.
 */
class InputController {
    private var stickPointer = -1

    /** Screen rectangle (x, y, w, h in pixels, y down) whose touches never count as the attack button. */
    var attackExcludedRect: FloatArray? = null

    /** Screen rectangle of the dodge button (x, y, w, h in pixels, y down); a touch on it is a dodge, never an attack. */
    var dodgeRect: FloatArray? = null
    private var originX = 0f
    private var originY = 0f

    /** Stick origin and current position in screen pixels (y down), or null when no stick is active. */
    var stickOrigin: Pair<Float, Float>? = null
        private set
    var stickPosition: Pair<Float, Float>? = null
        private set

    /** Input for this frame. */
    fun read(): FrameInput {
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
        val attack = input.isKeyPressed(Input.Keys.SPACE) || input.isKeyPressed(Input.Keys.J) ||
            (0 until MAX_POINTERS).any {
                input.isTouched(it) && input.getX(it) >= Gdx.graphics.width / 2 && !inExcludedRect(input.getX(it), input.getY(it))
            }
        val dodge = input.isKeyPressed(Input.Keys.L) || input.isKeyPressed(Input.Keys.SHIFT_LEFT) ||
            (0 until MAX_POINTERS).any { input.isTouched(it) && inRect(dodgeRect, input.getX(it), input.getY(it)) }
        return FrameInput(x, y, attack, dodge)
    }

    private fun inExcludedRect(x: Int, y: Int): Boolean = inRect(attackExcludedRect, x, y) || inRect(dodgeRect, x, y)

    private fun inRect(r: FloatArray?, x: Int, y: Int): Boolean {
        if (r == null) return false
        return x >= r[0] && x <= r[0] + r[2] && y >= r[1] && y <= r[1] + r[3]
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
