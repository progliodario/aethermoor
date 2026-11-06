package io.github.progliodario.aethermoor.core

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class GameInfoTest {
    @Test
    fun versionLineCombinesNameAndVersion() {
        assertEquals("Aethermoor 0.0.1", GameInfo("Aethermoor", "0.0.1").versionLine())
    }

    @Test
    fun noFeatureIsGatedYet() {
        assertTrue(supportedFeatures.isEmpty())
    }

    @Test
    fun placeholdersAreReplaced() {
        assertEquals("Versione 0.0.1", formatPlaceholders("Versione {version}", mapOf("version" to "0.0.1")))
    }

    @Test
    fun unknownPlaceholdersAreKept() {
        assertEquals("Hi {who}", formatPlaceholders("Hi {who}", mapOf("version" to "1")))
    }
}
