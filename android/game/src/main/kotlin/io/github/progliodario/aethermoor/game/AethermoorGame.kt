package io.github.progliodario.aethermoor.game

import com.badlogic.gdx.ApplicationAdapter
import com.badlogic.gdx.Gdx
import com.badlogic.gdx.graphics.Color
import com.badlogic.gdx.graphics.GL20
import com.badlogic.gdx.graphics.g2d.BitmapFont
import com.badlogic.gdx.graphics.g2d.SpriteBatch
import com.badlogic.gdx.utils.JsonReader
import com.badlogic.gdx.utils.ScreenUtils
import io.github.progliodario.aethermoor.core.GameInfo
import io.github.progliodario.aethermoor.core.formatPlaceholders
import java.util.Locale

/**
 * M0 skeleton: clears the screen and shows the localized title, version and notice read from the
 * shared data pack (assets/base/i18n/<lang>/core.json).
 */
class AethermoorGame(private val info: GameInfo) : ApplicationAdapter() {
    private lateinit var batch: SpriteBatch
    private lateinit var font: BitmapFont
    private var lines: List<String> = emptyList()

    override fun create() {
        batch = SpriteBatch()
        font = BitmapFont().apply {
            data.setScale(3f)
            color = Color(0.435f, 0.89f, 1f, 1f)
        }
        lines = loadLines()
    }

    override fun render() {
        ScreenUtils.clear(0.043f, 0.122f, 0.227f, 1f)
        Gdx.gl.glClear(GL20.GL_COLOR_BUFFER_BIT)
        val margin = 32f
        var y = Gdx.graphics.height - margin
        batch.begin()
        for (line in lines) {
            font.draw(batch, line, margin, y)
            y -= font.lineHeight * 1.4f
        }
        batch.end()
    }

    override fun dispose() {
        batch.dispose()
        font.dispose()
    }

    private fun loadLines(): List<String> {
        val language = if (Locale.getDefault().language == "it") "it" else "en"
        val strings = JsonReader().parse(Gdx.files.internal("base/i18n/$language/core.json"))
        fun text(key: String): String = strings.getString(key, key)
        return listOf(
            text("game.title"),
            text("game.subtitle"),
            formatPlaceholders(text("ui.version"), mapOf("version" to info.version)),
            text("ui.m0_notice"),
        )
    }
}
