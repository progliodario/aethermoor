package io.github.progliodario.aethermoor.core

import java.io.File

/**
 * The crash log (spec 12, "The crash log"): the last messages of the game and the error that stopped it, written as a text file in the
 * folder of the saves. Nothing leaves the device. The same in C++ (desktop/src/data/crash_log.hpp).
 */
class CrashLog(private val keep: Int = 40) {
    private val kept = ArrayDeque<String>()

    /** The messages kept, the oldest first. */
    @Synchronized
    fun lines(): List<String> = kept.toList()

    /** A message of the game (a notice shown, a step of the start); only the last [keep] stay. */
    @Synchronized
    fun note(line: String) {
        kept.addLast(line)
        while (kept.size > keep) kept.removeFirst()
    }

    /** The text of the file: the version, the error, then the last messages, the oldest first. */
    @Synchronized
    fun text(version: String, error: String): String = buildString {
        append("Aethermoor ").append(version).append('\n')
        append("error: ").append(error).append("\n\nlast messages:\n")
        for (line in kept) append("  ").append(line).append('\n')
    }

    /** Writes the file; false when it cannot be written. */
    fun write(file: File, version: String, error: String): Boolean = runCatching { file.writeText(text(version, error)) }.isSuccess
}
