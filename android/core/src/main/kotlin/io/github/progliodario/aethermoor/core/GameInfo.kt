package io.github.progliodario.aethermoor.core

/** Name and version of the game. The values come from project.json via the app build. */
data class GameInfo(val name: String, val version: String) {
    /** "<name> <version>", for titles and logs. */
    fun versionLine(): String = "$name $version"
}
