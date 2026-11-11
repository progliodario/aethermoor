package io.github.progliodario.aethermoor.game

import com.badlogic.gdx.Gdx
import com.badlogic.gdx.graphics.Pixmap
import com.badlogic.gdx.graphics.Texture
import com.badlogic.gdx.graphics.g2d.TextureRegion
import io.github.progliodario.aethermoor.core.Pack
import io.github.progliodario.aethermoor.core.vector.parseRecipe
import io.github.progliodario.aethermoor.core.vector.rasterize

/** A baked recipe. Sizes and origin are in art units; the region is flipped for a y-down projection. */
class Sprite(
    val region: TextureRegion,
    val width: Float,
    val height: Float,
    val originX: Float,
    val originY: Float,
    /** The picture looks to the left (spec 13, "Facing"). */
    val facesLeft: Boolean = false,
)

/**
 * Bakes vector recipes into textures at the current scale bucket (spec 13). The pixmaps are kept next to
 * their textures so libGDX can re-create the textures after the OpenGL context is lost.
 */
class TextureCache(private val pack: Pack) {
    private class Entry(val bucket: Int, val sprite: Sprite?, val texture: Texture?, val pixmap: Pixmap?)

    private val entries = HashMap<String, Entry>()

    val size: Int get() = entries.size

    fun get(recipeId: String, tilePx: Int, variant: String? = null): Sprite? {
        val bucket = bucketFor(tilePx)
        val key = "$recipeId|${variant ?: ""}|$bucket"
        entries[key]?.let { return it.sprite }

        var entry = Entry(bucket, null, null, null)
        val text = pack.readDocument(recipeId)
        if (text == null) {
            Gdx.app.error(TAG, "Missing art recipe '$recipeId'")
        } else {
            parseRecipe(text).fold(
                onSuccess = { recipe ->
                    val bitmap = rasterize(recipe, bucket / 32f, variant)
                    val pixmap = Pixmap(bitmap.width, bitmap.height, Pixmap.Format.RGBA8888)
                    pixmap.pixels.clear()
                    pixmap.pixels.put(bitmap.rgba)
                    pixmap.pixels.rewind()
                    val texture = Texture(pixmap)
                    texture.setFilter(Texture.TextureFilter.Linear, Texture.TextureFilter.Linear)
                    val region = TextureRegion(texture)
                    region.flip(false, true)
                    entry = Entry(bucket, Sprite(region, recipe.width, recipe.height, recipe.originX, recipe.originY, recipe.facesLeft), texture, pixmap)
                },
                onFailure = { Gdx.app.error(TAG, "Cannot bake art recipe '$recipeId': ${it.message}") },
            )
        }
        entries[key] = entry
        return entry.sprite
    }

    /** Disposes textures baked for other scale buckets than the one used by [tilePx]. */
    fun releaseOtherBuckets(tilePx: Int) {
        val bucket = bucketFor(tilePx)
        val iterator = entries.entries.iterator()
        while (iterator.hasNext()) {
            val entry = iterator.next().value
            if (entry.bucket != bucket) {
                entry.texture?.dispose()
                entry.pixmap?.dispose()
                iterator.remove()
            }
        }
    }

    fun dispose() {
        for (entry in entries.values) {
            entry.texture?.dispose()
            entry.pixmap?.dispose()
        }
        entries.clear()
    }

    companion object {
        private const val TAG = "TextureCache"
        private val BUCKETS = intArrayOf(32, 48, 64, 96, 128, 192, 256)

        fun bucketFor(tilePx: Int): Int = BUCKETS.firstOrNull { tilePx <= it } ?: BUCKETS.last()
    }
}
