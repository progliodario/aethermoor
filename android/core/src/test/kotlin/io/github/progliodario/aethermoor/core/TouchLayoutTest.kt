package io.github.progliodario.aethermoor.core

import org.junit.jupiter.api.Assertions.assertArrayEquals
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

/** The layout of the touch buttons (spec 16, "The layout of the buttons"): it survives the settings file and a turn of the phone. */
class TouchLayoutTest {
    private val dodge = floatArrayOf(900f, 1700f, 160f, 160f)

    @Test
    fun aButtonNotMovedIsWhereItIsByDefault() {
        assertArrayEquals(dodge, TouchLayout().place("dodge", dodge, 1080f, 1920f))
    }

    @Test
    fun aMovedAndResizedButtonSurvivesTheSettingsFile() {
        val layout = TouchLayout().moved("dodge", -108f, -192f, 1080f, 1920f).resized("dodge", 20).resized("parry", -100)
        val text = "{\n  \"language\": \"it\",\n  \"touch_layout\": ${layout.toJson()},\n  \"volume_master_pm\": 1000\n}\n"
        val read = TouchLayout.fromSettings(text)
        assertEquals(TouchButton(-100, -100, 120), read.of("dodge"))
        assertEquals(TouchButton(0, 0, TouchLayout.MIN_SIZE_PCT), read.of("parry"))
        assertEquals(TouchButton(), read.of("strike"))
    }

    @Test
    fun theButtonKeepsItsPlaceInPermilleWhenThePhoneTurns() {
        val layout = TouchLayout().moved("dodge", -108f, 0f, 1080f, 1920f) // a tenth of the width to the left
        val portrait = layout.place("dodge", dodge, 1080f, 1920f)
        assertEquals(900f - 108f, portrait[0], 0.5f)
        val landscape = layout.place("dodge", floatArrayOf(1660f, 900f, 160f, 160f), 1920f, 1080f)
        assertEquals(1660f - 192f, landscape[0], 0.5f) // a tenth of the new width
    }

    @Test
    fun aButtonStaysOnTheScreen() {
        val layout = TouchLayout().moved("dodge", 5000f, 5000f, 1080f, 1920f)
        val r = layout.place("dodge", dodge, 1080f, 1920f)
        assertEquals(1080f - 160f, r[0], 0.01f)
        assertEquals(1920f - 160f, r[1], 0.01f)
    }

    @Test
    fun aBrokenLayoutIsTheLayoutByDefault() {
        assertEquals(TouchButton(), TouchLayout.fromSettings("{\"touch_layout\": {\"dodge\": [1, \"x\", 3]}}").of("dodge"))
        assertEquals(TouchButton(), TouchLayout.fromSettings("not json").of("dodge"))
        assertEquals(TouchButton(), TouchLayout.fromSettings(null).of("dodge"))
    }
}
