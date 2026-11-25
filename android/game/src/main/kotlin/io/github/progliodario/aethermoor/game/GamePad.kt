package io.github.progliodario.aethermoor.game

import com.badlogic.gdx.Input
import com.badlogic.gdx.controllers.Controller
import com.badlogic.gdx.controllers.ControllerMapping
import com.badlogic.gdx.controllers.Controllers

/** Where the player is, for the buttons of a controller (spec 16, "Android", the row Controller). */
enum class PadContext {
    /** Walking and fighting: no panel and no dialogue. */
    PLAY,

    /** A dialogue is shown; the game goes on. */
    DIALOGUE,

    /** A panel or a list is open (bag, map, journal, crafting, shop, chest, board, stones) or the chooser of the protagonist. */
    PANEL,

    /** The title screen, with the list of the games. */
    MENU,
}

/**
 * A game controller on Android (spec 16, "Android", the row Controller), with the buttons of the gamepad of the desktop: the left stick
 * moves; `A` (south) attacks and confirms; `X` (west) talks and confirms; `RB` is the power strike; `LB` the parry; `B` (east) rolls in
 * the game and closes a panel; `Y` (north) switches buy and sell in a shop; the D-pad moves in lists and choices. The buttons of the
 * panels reach the game as the keys it already reads for a physical keyboard ([keys]), so every panel works with a controller as it
 * works with a keyboard; the buttons of the fight are read by [InputController.read].
 */
class GamePad {
    private var held: Set<Int> = emptySet()
    private var before: Set<Int> = emptySet()
    private var wrapper: PadInput? = null

    /** The left stick, -1 to 1 each (y down); 0 when there is no controller. The simulation applies the dead zone (spec 02). */
    var stickX = 0f
        private set
    var stickY = 0f
        private set

    /** The buttons of the fight, held in this frame (only in [PadContext.PLAY] and, but for `A`, in [PadContext.DIALOGUE]). */
    var attack = false
        private set
    var dodge = false
        private set
    var strike = false
        private set
    var parry = false
        private set

    /** Reads the first connected controller, once a frame, before the input of the frame is handled. */
    fun update(context: PadContext) {
        before = held
        val pad = firstController()
        if (pad == null) {
            held = emptySet()
            stickX = 0f
            stickY = 0f
            attack = false
            dodge = false
            strike = false
            parry = false
            return
        }
        val m = pad.mapping
        held = keysOf(pad, m, context)
        val fighting = context == PadContext.PLAY || context == PadContext.DIALOGUE
        stickX = if (fighting) axis(pad, m.axisLeftX) else 0f
        stickY = if (fighting) axis(pad, m.axisLeftY) else 0f
        attack = context == PadContext.PLAY && down(pad, m.buttonA) // in a dialogue `A` confirms instead
        dodge = fighting && down(pad, m.buttonB)
        strike = fighting && down(pad, m.buttonR1)
        parry = fighting && down(pad, m.buttonL1)
    }

    /** The input of the frame as the game reads it: the keyboard and the touches of [base], and the buttons of the controller as keys. */
    fun keys(base: Input): Input {
        val current = wrapper
        if (current != null && current.base === base) return current
        return PadInput(base, this).also { wrapper = it }
    }

    internal fun isKeyPressed(key: Int): Boolean = key in held

    internal fun isKeyJustPressed(key: Int): Boolean = key in held && key !in before

    /** The keys of the buttons of the panels, for the context: what a keyboard would press for the same action. */
    private fun keysOf(pad: Controller, m: ControllerMapping, context: PadContext): Set<Int> {
        val keys = HashSet<Int>()
        fun press(button: Int, key: Int) {
            if (down(pad, button)) keys += key
        }
        press(m.buttonX, Input.Keys.E) // talks next to a person, confirms everywhere
        if (context == PadContext.PLAY) return keys
        press(m.buttonA, Input.Keys.ENTER)
        press(m.buttonDpadUp, Input.Keys.UP)
        press(m.buttonDpadDown, Input.Keys.DOWN)
        if (context == PadContext.DIALOGUE) return keys
        press(m.buttonDpadLeft, Input.Keys.LEFT)
        press(m.buttonDpadRight, Input.Keys.RIGHT)
        if (context == PadContext.PANEL) { // on the title screen Esc would leave the app: B does nothing there
            press(m.buttonB, Input.Keys.ESCAPE)
            press(m.buttonY, Input.Keys.TAB)
        }
        return keys
    }

    private fun firstController(): Controller? = runCatching { Controllers.getControllers().firstOrNull { it.isConnected } }.getOrNull()

    private fun down(pad: Controller, button: Int): Boolean = button != ControllerMapping.UNDEFINED && pad.getButton(button)

    private fun axis(pad: Controller, code: Int): Float = if (code == ControllerMapping.UNDEFINED) 0f else pad.getAxis(code).coerceIn(-1f, 1f)
}

/** [base] (the keyboard and the touches) with the buttons of [pad] pressed as keys. */
class PadInput(val base: Input, private val pad: GamePad) : Input by base {
    override fun isKeyPressed(key: Int): Boolean = base.isKeyPressed(key) || pad.isKeyPressed(key)

    override fun isKeyJustPressed(key: Int): Boolean = base.isKeyJustPressed(key) || pad.isKeyJustPressed(key)
}
