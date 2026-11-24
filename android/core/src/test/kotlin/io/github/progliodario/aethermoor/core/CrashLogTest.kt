package io.github.progliodario.aethermoor.core

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import java.io.File

/** The crash log (spec 12, "The crash log"): only the last messages stay, and an error forced here writes the file. */
class CrashLogTest {
    @Test
    fun anErrorWritesTheLastMessagesAndTheError() {
        val log = CrashLog(3)
        for (i in 1..5) log.note("message $i")
        assertEquals(listOf("message 3", "message 4", "message 5"), log.lines())
        val file = File.createTempFile("aether_crash_log_test", ".txt")
        try {
            val error = runCatching { error("forced error") }.exceptionOrNull()
            assertTrue(log.write(file, "0.0.0-test", error?.message ?: ""))
            val written = file.readText()
            assertEquals(log.text("0.0.0-test", "forced error"), written)
            assertTrue(written.contains("error: forced error"))
            assertTrue(written.contains("message 5"))
            assertFalse(written.contains("message 2"))
        } finally {
            file.delete()
        }
    }
}
