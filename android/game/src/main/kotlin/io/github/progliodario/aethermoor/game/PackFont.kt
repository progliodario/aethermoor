package io.github.progliodario.aethermoor.game

import com.badlogic.gdx.Gdx
import com.badlogic.gdx.graphics.Pixmap
import com.badlogic.gdx.graphics.Texture
import com.badlogic.gdx.graphics.g2d.BitmapFont
import com.badlogic.gdx.graphics.g2d.TextureRegion
import io.github.progliodario.aethermoor.core.FontDef
import io.github.progliodario.aethermoor.core.Pack
import io.github.progliodario.aethermoor.core.loadFont
import io.github.progliodario.aethermoor.core.vector.Layer
import io.github.progliodario.aethermoor.core.vector.Paint
import io.github.progliodario.aethermoor.core.vector.Recipe
import io.github.progliodario.aethermoor.core.vector.Shape
import io.github.progliodario.aethermoor.core.vector.StrokeStyle
import io.github.progliodario.aethermoor.core.vector.rasterize
import kotlin.math.ceil
import kotlin.math.max
import kotlin.math.roundToInt

/**
 * The font of the pack as a libGDX font (spec 13, "Font"): every glyph is baked with the rasterizer of the art recipes,
 * white, into one texture, at the size of this screen. The font is flipped (the projection has y pointing down) and a
 * text is drawn with the top of its capitals at the y it is given, as the font this replaces.
 */
class PackFont private constructor(val font: BitmapFont, private val atlas: Pixmap, private val texture: Texture) {
    fun dispose() {
        font.dispose()
        texture.dispose()
        atlas.dispose()
    }

    companion object {
        private const val TAG = "PackFont"
        private const val COLUMNS = 16
        private const val PAD = 2

        /** Null when the pack has no font or it cannot be baked: the caller keeps the font it has. */
        fun build(pack: Pack, capPixels: Float): PackFont? {
            val def = loadFont(pack) ?: return null
            return runCatching { bake(def, capPixels) }
                .onFailure { Gdx.app.error(TAG, "cannot bake the font of the pack: ${it.message}") }
                .getOrNull()
        }

        private fun powerOfTwo(value: Int): Int {
            var size = 64
            while (size < value) size *= 2
            return size
        }

        private fun bake(def: FontDef, capPixels: Float): PackFont {
            val scale = max(1f, capPixels / def.capHeight) // pixels for each font unit
            val glyphW = ceil(def.cellW * scale).toInt()
            val glyphH = ceil(def.cellH * scale).toInt()
            val drawn = def.glyphs.entries.filter { it.value.path.isNotEmpty() && it.key <= 0xFFFF }.sortedBy { it.key }
            val rows = (drawn.size + COLUMNS - 1) / COLUMNS
            val atlasW = powerOfTwo(COLUMNS * (glyphW + PAD))
            val atlasH = powerOfTwo(max(1, rows) * (glyphH + PAD))
            val atlas = Pixmap(atlasW, atlasH, Pixmap.Format.RGBA8888)
            atlas.setBlending(Pixmap.Blending.None)
            atlas.setColor(0f, 0f, 0f, 0f)
            atlas.fill()
            val pixels = atlas.pixels

            val data = BitmapFont.BitmapFontData()
            data.flipped = true
            data.lineHeight = def.line * scale
            data.capHeight = def.capHeight * scale
            data.xHeight = def.xHeight * scale
            data.ascent = -def.capTop * scale // the room above the capitals, inside the picture of a glyph
            data.descent = 2f * scale
            data.down = data.lineHeight

            // a pen that is never thinner than a pixel and a bit, or small text fades
            val stroke = max(def.stroke, 1.15f / scale)
            val place = HashMap<Int, Int>()
            for ((index, entry) in drawn.withIndex()) {
                val recipe = Recipe(
                    id = "", width = def.cellW, height = def.cellH, originX = 0f, originY = 0f,
                    palette = emptyMap(), variants = emptyMap(),
                    layers = listOf(Layer(Shape.Path(entry.value.path), Paint.None, StrokeStyle("#FFFFFF", stroke), 1f)),
                )
                val bitmap = rasterize(recipe, scale)
                val x0 = (index % COLUMNS) * (glyphW + PAD)
                val y0 = (index / COLUMNS) * (glyphH + PAD)
                for (y in 0 until bitmap.height) {
                    pixels.position(((y0 + y) * atlasW + x0) * 4)
                    pixels.put(bitmap.rgba, y * bitmap.width * 4, bitmap.width * 4)
                }
                place[entry.key] = index
            }
            pixels.position(0)

            for ((code, glyph) in def.glyphs) {
                if (code > 0xFFFF) continue
                val out = BitmapFont.Glyph()
                out.id = code
                out.page = 0
                out.xadvance = (glyph.width * scale).roundToInt()
                val index = place[code]
                if (index != null) {
                    out.srcX = (index % COLUMNS) * (glyphW + PAD)
                    out.srcY = (index / COLUMNS) * (glyphH + PAD)
                    out.width = glyphW
                    out.height = glyphH
                    out.xoffset = -((def.cellW - glyph.width) / 2f * scale).roundToInt() // the cell is centred on the width
                    out.yoffset = 0
                }
                data.setGlyph(code, out)
            }
            data.missingGlyph = data.getGlyph('?')
            data.getGlyph(' ')?.let { data.spaceXadvance = it.xadvance.toFloat() }

            val texture = Texture(atlas)
            texture.setFilter(Texture.TextureFilter.Linear, Texture.TextureFilter.Linear)
            val font = BitmapFont(data, TextureRegion(texture), true)
            return PackFont(font, atlas, texture)
        }
    }
}
