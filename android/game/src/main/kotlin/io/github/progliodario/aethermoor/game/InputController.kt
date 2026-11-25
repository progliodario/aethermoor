package io.github.progliodario.aethermoor.game

import com.badlogic.gdx.Gdx
import com.badlogic.gdx.Input
import kotlin.math.sqrt

/** Input of one frame: raw movement vector (the simulation normalizes it) and the attack button. */
data class FrameInput(val x: Float, val y: Float, val attack: Boolean, val dodge: Boolean = false, val strike: Boolean = false, val parry: Boolean = false)

/**
 * Input (spec 16): WASD/arrow keys and J/Space to attack, and on touch screens a floating stick on the left half
 * (the first touch is the origin; dragging up to [STICK_RADIUS_DP] gives a vector of length 1) and an attack
 * button: any touch on the right half; a controller ([GamePad]) as the gamepad of the desktop.
 */
class InputController {
    private var stickPointer = -1

    /** Screen rectangle (x, y, w, h in pixels, y down) whose touches never count as the attack button. */
    var attackExcludedRect: FloatArray? = null

    /** Screen rectangle of the dodge button (x, y, w, h in pixels, y down); a touch on it is a dodge, never an attack. */
    var dodgeRect: FloatArray? = null

    /** Screen rectangle of the Analyze button; a touch on it is never an attack. */
    var analyzeRect: FloatArray? = null

    /** Screen rectangle of the power strike button; a touch on it is a strike, never an attack. */
    var strikeRect: FloatArray? = null

    /** Screen rectangle of the parry button; a touch on it is a parry, never an attack. */
    var parryRect: FloatArray? = null
    private var originX = 0f
    private var originY = 0f

    /** Stick origin and current position in screen pixels (y down), or null when no stick is active. */
    var stickOrigin: Pair<Float, Float>? = null
        private set
    var stickPosition: Pair<Float, Float>? = null
        private set

    /** Input for this frame: the keyboard first, then the stick of the touches, then the controller ([pad]; spec 16). */
    fun read(pad: GamePad): FrameInput {
        val input = Gdx.input
        val touch = readStick() // every frame: it follows the finger of the stick
        val (x, y) = firstMoving(keyVector(input), touch, Pair(pad.stickX, pad.stickY))
        return FrameInput(
            x,
            y,
            attack = pad.attack || anyKey(input, Input.Keys.SPACE, Input.Keys.J) || touchAttack(input),
            dodge = pad.dodge || anyKey(input, Input.Keys.L, Input.Keys.SHIFT_LEFT) || touching(input, dodgeRect),
            strike = pad.strike || anyKey(input, Input.Keys.K) || touching(input, strikeRect),
            parry = pad.parry || anyKey(input, Input.Keys.U) || touching(input, parryRect),
        )
    }

    /** The movement of the keys: WASD or the arrows. */
    private fun keyVector(input: Input): Pair<Float, Float> {
        var x = 0f
        var y = 0f
        if (anyKey(input, Input.Keys.A, Input.Keys.LEFT)) x -= 1f
        if (anyKey(input, Input.Keys.D, Input.Keys.RIGHT)) x += 1f
        if (anyKey(input, Input.Keys.W, Input.Keys.UP)) y -= 1f
        if (anyKey(input, Input.Keys.S, Input.Keys.DOWN)) y += 1f
        return Pair(x, y)
    }

    private fun firstMoving(vararg vectors: Pair<Float, Float>): Pair<Float, Float> = vectors.firstOrNull { it.first != 0f || it.second != 0f } ?: Pair(0f, 0f)

    private fun anyKey(input: Input, vararg keys: Int): Boolean = keys.any { input.isKeyPressed(it) }

    /** A touch on the right half of the screen, but on a button: the attack. */
    private fun touchAttack(input: Input): Boolean = (0 until MAX_POINTERS).any {
        input.isTouched(it) && input.getX(it) >= Gdx.graphics.width / 2 && !inExcludedRect(input.getX(it), input.getY(it))
    }

    private fun touching(input: Input, rect: FloatArray?): Boolean = (0 until MAX_POINTERS).any { input.isTouched(it) && inRect(rect, input.getX(it), input.getY(it)) }

    private fun inExcludedRect(x: Int, y: Int): Boolean = inRect(attackExcludedRect, x, y) || inRect(dodgeRect, x, y) || inRect(analyzeRect, x, y) || inRect(strikeRect, x, y) || inRect(parryRect, x, y)

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
