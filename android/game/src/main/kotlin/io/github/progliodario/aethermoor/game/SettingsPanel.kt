package io.github.progliodario.aethermoor.game

import com.badlogic.gdx.Gdx
import com.badlogic.gdx.graphics.Color
import com.badlogic.gdx.graphics.GL20
import com.badlogic.gdx.graphics.g2d.BitmapFont
import com.badlogic.gdx.graphics.g2d.SpriteBatch
import com.badlogic.gdx.graphics.glutils.ShapeRenderer
import com.badlogic.gdx.math.Matrix4
import kotlin.math.max
import kotlin.math.min

/**
 * A row of the settings panel (spec 16, "Settings"): a [label], its [value], and what the `-` and `+` buttons do ([change] gets -1
 * or +1); a row without [change] is the title of a group.
 */
class SettingRow(val label: String, val value: String = "", val change: ((Int) -> Unit)? = null)

/**
 * The settings panel of Android (spec 16, "Settings"): a list of rows that scrolls (drag it, or the arrows), with `-` and `+` on every
 * row that can change and a button that closes it. The rows are built anew every frame by the game, so what they show is always true.
 */
class SettingsPanel {
    var open = false

    /** The title of the panel and the label of the button that closes it, in the language of the game. */
    var title = ""
    var done = ""
    private var scroll = 0
    private var minusRects: List<Pair<Int, FloatArray>> = emptyList()
    private var plusRects: List<Pair<Int, FloatArray>> = emptyList()
    private var doneRect: FloatArray? = null
    private var upRect: FloatArray? = null
    private var downRect: FloatArray? = null
    private var panelRect: FloatArray? = null
    private var dragY = -1f
    private var dragRows = 0f
    private var rowH = 1f
    private var visible = 1

    /** Draws the panel with the rows of this frame. */
    fun draw(shapes: ShapeRenderer, batch: SpriteBatch, font: BitmapFont, projection: Matrix4, rows: List<SettingRow>) {
        if (!open) return
        val density = Gdx.graphics.density
        val width = Gdx.graphics.width.toFloat()
        val height = Gdx.graphics.height.toFloat()
        rowH = max(36f * density, font.lineHeight * 1.9f)
        val panelW = min(width - 24f * density, 600f * density)
        val panelH = min(height - 24f * density, 560f * density)
        val panelX = (width - panelW) / 2f
        val panelY = (height - panelH) / 2f
        val top = panelY + 52f * density
        visible = max(1, ((panelY + panelH - 12f * density - top) / rowH).toInt())
        scroll = scroll.coerceIn(0, max(0, rows.size - visible))
        panelRect = floatArrayOf(panelX, panelY, panelW, panelH)
        val button = 40f * density
        doneRect = floatArrayOf(panelX + panelW - 120f * density, panelY + 8f * density, 108f * density, 34f * density)
        upRect = floatArrayOf(panelX + panelW - 120f * density - 8f * density - button, panelY + 8f * density, button, 34f * density)
        downRect = floatArrayOf(panelX + panelW - 120f * density - 16f * density - 2 * button, panelY + 8f * density, button, 34f * density)
        val minus = ArrayList<Pair<Int, FloatArray>>()
        val plus = ArrayList<Pair<Int, FloatArray>>()
        for (i in scroll until min(rows.size, scroll + visible)) {
            if (rows[i].change == null) continue
            val y = top + (i - scroll) * rowH + (rowH - 32f * density) / 2f
            minus.add(i to floatArrayOf(panelX + panelW - 12f * density - 2 * button - 6f * density, y, button, 32f * density))
            plus.add(i to floatArrayOf(panelX + panelW - 12f * density - button, y, button, 32f * density))
        }
        minusRects = minus
        plusRects = plus

        shapes.projectionMatrix = projection
        Gdx.gl.glEnable(GL20.GL_BLEND)
        Gdx.gl.glBlendFunc(GL20.GL_SRC_ALPHA, GL20.GL_ONE_MINUS_SRC_ALPHA)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        shapes.color = Color(0.04f, 0.12f, 0.23f, 0.96f)
        shapes.rect(panelX, panelY, panelW, panelH)
        shapes.color = Color(1f, 0.84f, 0.47f, 1f)
        shapes.rect(panelX, panelY, panelW, 3f * density)
        shapes.color = Color(0.16f, 0.35f, 0.55f, 1f)
        for (r in listOfNotNull(doneRect, upRect, downRect)) shapes.rect(r[0], r[1], r[2], r[3])
        shapes.color = Color(0.2f, 0.26f, 0.36f, 1f)
        for ((_, r) in minus + plus) shapes.rect(r[0], r[1], r[2], r[3])
        if (rows.size > visible) { // where the window is in the list
            val barH = (panelH - 64f * density) * visible / rows.size
            val barY = top + (panelH - 64f * density - barH) * scroll / max(1, rows.size - visible)
            shapes.color = Color(0.43f, 0.6f, 0.8f, 0.7f)
            shapes.rect(panelX + 4f * density, barY, 3f * density, barH)
        }
        shapes.end()

        batch.projectionMatrix = projection
        batch.begin()
        font.color = Color(1f, 0.84f, 0.47f, 1f)
        font.draw(batch, title, panelX + 16f * density, panelY + 14f * density)
        font.color = Color.WHITE
        centered(batch, font, done, requireNotNull(doneRect))
        centered(batch, font, "^", requireNotNull(upRect))
        centered(batch, font, "v", requireNotNull(downRect))
        for (i in scroll until min(rows.size, scroll + visible)) {
            val row = rows[i]
            val y = top + (i - scroll) * rowH + (rowH - font.lineHeight) / 2f
            font.color = if (row.change == null) Color(1f, 0.84f, 0.47f, 1f) else Color(0.92f, 0.96f, 1f, 1f)
            font.draw(batch, row.label, panelX + 16f * density, y)
            if (row.value.isNotEmpty()) {
                font.color = Color(0.435f, 0.89f, 1f, 1f)
                font.draw(batch, row.value, panelX + panelW - 12f * density - 2 * button - 120f * density, y, 104f * density, com.badlogic.gdx.utils.Align.right, false)
            }
        }
        font.color = Color.WHITE
        for ((_, r) in minus) centered(batch, font, "-", r)
        for ((_, r) in plus) centered(batch, font, "+", r)
        batch.end()
    }

    /** Handles the touches while the panel is open: a tap on a button, or a drag that scrolls. Returns false when it is closed. */
    fun touch(rows: List<SettingRow>, back: Boolean): Boolean {
        if (!open) return false
        if (back) {
            open = false
            return true
        }
        val input = Gdx.input
        val x = input.x.toFloat()
        val y = input.y.toFloat()
        if (input.justTouched()) {
            dragY = y
            dragRows = 0f
            tap(rows, x, y)
        } else if (input.isTouched && dragY >= 0f) { // a drag moves the list by rows
            dragRows += (dragY - y) / rowH
            dragY = y
            val whole = dragRows.toInt()
            if (whole != 0) {
                scroll = (scroll + whole).coerceIn(0, max(0, rows.size - visible))
                dragRows -= whole
            }
        } else {
            dragY = -1f
        }
        return true
    }

    private fun tap(rows: List<SettingRow>, x: Float, y: Float) {
        val hit = { r: FloatArray? -> r != null && x >= r[0] && x <= r[0] + r[2] && y >= r[1] && y <= r[1] + r[3] }
        when {
            hit(doneRect) -> open = false
            hit(upRect) -> scroll = max(0, scroll - max(1, visible - 1))
            hit(downRect) -> scroll = min(max(0, rows.size - visible), scroll + max(1, visible - 1))
            !hit(panelRect) -> open = false
            else -> {
                minusRects.firstOrNull { hit(it.second) }?.let { rows.getOrNull(it.first)?.change?.invoke(-1) }
                plusRects.firstOrNull { hit(it.second) }?.let { rows.getOrNull(it.first)?.change?.invoke(1) }
            }
        }
    }

    private fun centered(batch: SpriteBatch, font: BitmapFont, text: String, r: FloatArray) {
        font.draw(batch, text, r[0], r[1] + (r[3] - font.lineHeight) / 2f, r[2], com.badlogic.gdx.utils.Align.center, false)
    }
}
