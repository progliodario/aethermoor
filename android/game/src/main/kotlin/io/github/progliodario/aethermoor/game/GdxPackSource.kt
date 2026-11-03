package io.github.progliodario.aethermoor.game

import com.badlogic.gdx.Gdx
import com.badlogic.gdx.files.FileHandle
import io.github.progliodario.aethermoor.core.PackSource

/** Reads the shared content pack from the app assets (`assets/<root>/...`, bundled from `data/`). */
class GdxPackSource(private val root: String = "base") : PackSource {
    override fun listJson(dir: String): List<String> {
        val start = Gdx.files.internal(if (dir.isEmpty()) root else "$root/$dir")
        if (!start.exists() || !start.isDirectory) return emptyList()
        val out = ArrayList<String>()

        fun walk(handle: FileHandle, relative: String) {
            for (child in handle.list()) {
                val childRelative = if (relative.isEmpty()) child.name() else "$relative/${child.name()}"
                if (child.isDirectory) walk(child, childRelative) else if (child.extension() == "json") out.add(childRelative)
            }
        }
        walk(start, dir)
        return out.sorted()
    }

    override fun readText(path: String): String? {
        val handle = Gdx.files.internal("$root/$path")
        return if (handle.exists() && !handle.isDirectory) handle.readString("UTF-8") else null
    }
}
