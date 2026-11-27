package io.github.progliodario.aethermoor.game

import com.badlogic.gdx.Gdx
import com.badlogic.gdx.graphics.GL20
import com.badlogic.gdx.graphics.Pixmap
import com.badlogic.gdx.graphics.Texture
import com.badlogic.gdx.graphics.g2d.TextureRegion
import com.badlogic.gdx.graphics.glutils.PixmapTextureData
import com.badlogic.gdx.utils.BufferUtils
import io.github.progliodario.aethermoor.core.Pack
import io.github.progliodario.aethermoor.core.vector.parseRecipe
import io.github.progliodario.aethermoor.core.vector.rasterize
import kotlin.math.max
import kotlin.math.min

/**
 * A baked recipe. Sizes and origin are in art units; the region is flipped for a y-down projection and points into the
 * atlas of its bucket, so that the pictures of a frame share one texture and one batch (spec 13, "Atlases and batches").
 */
class Sprite(
    val region: TextureRegion,
    val width: Float,
    val height: Float,
    val originX: Float,
    val originY: Float,
    /** The picture looks to the left (spec 13, "Facing"). */
    val facesLeft: Boolean = false,
    /** How far the top moves in the wind, in art units (spec 13, "Sway"). */
    val sway: Float = 0f,
) {
    /** The coordinates inside the picture, [fx] and [fy] from 0 to 1, for the calls that take the coordinates themselves. */
    fun u(fx: Float): Float = region.u + fx * (region.u2 - region.u)

    fun v(fy: Float): Float = region.v + fy * (region.v2 - region.v)
}

/**
 * Bakes vector recipes into textures at the current scale bucket (spec 13). The pictures of a bucket are laid in one or
 * more atlases of shelves, so that a frame of ground, props and figures is a handful of batches instead of one call for
 * each picture. The atlases are managed, from the pixmaps kept next to them, so that libGDX loads them again by itself
 * after the OpenGL context is lost (a pause of the app, risk R6 of the roadmap).
 */
class TextureCache(private val pack: Pack) {
    private class Entry(val bucket: Int, val variant: String?, val sprite: Sprite?)

    /** A texture of pictures laid side by side in shelves, with a pixel of gap around each. */
    private class Page(val bucket: Int, val size: Int) {
        val pixmap = Pixmap(size, size, Pixmap.Format.RGBA8888).apply {
            setBlending(Pixmap.Blending.None)
            setColor(0f, 0f, 0f, 0f)
            fill()
        }

        // managed (kept pixmap, not disposed by the texture): libGDX loads it again when the OpenGL context is lost (risk R6)
        val texture = Texture(PixmapTextureData(pixmap, null, false, false, true)).apply {
            setFilter(Texture.TextureFilter.Linear, Texture.TextureFilter.Linear)
        }

        var x = 0
        var y = 0
        var shelf = 0

        // the part of the pixmap that still has to reach the GPU, sent at a moment when no batch is open
        var dirtyX0 = Int.MAX_VALUE
        var dirtyY0 = Int.MAX_VALUE
        var dirtyX1 = -1
        var dirtyY1 = -1

        fun dirty(x0: Int, y0: Int, x1: Int, y1: Int) {
            dirtyX0 = min(dirtyX0, x0)
            dirtyY0 = min(dirtyY0, y0)
            dirtyX1 = max(dirtyX1, x1)
            dirtyY1 = max(dirtyY1, y1)
        }

        val hasDirty: Boolean get() = dirtyX1 > dirtyX0 && dirtyY1 > dirtyY0

        /** Takes a slot for a picture [width] by [height], moving to the next shelf or answering false when it is full. */
        fun take(width: Int, height: Int): Boolean {
            if (x + width > size) { // the shelf is full: the next one
                x = 0
                y += shelf + GAP
                shelf = 0
            }
            if (y + height > size) return false
            x += width + GAP
            shelf = max(shelf, height)
            return true
        }
    }

    // by recipe id; the id is read as it is, and an id has one entry for each bucket and variant that was asked
    private val entries = HashMap<String, ArrayList<Entry>>()
    private val pages = ArrayList<Page>()

    val size: Int get() = entries.values.sumOf { it.size }

    private var budgetNanos = -1L

    /** The largest bucket the textures are baked at, from the quality of the graphics (spec 13, "Quality"); a larger tile is drawn from it, scaled. */
    var bucketCap = 256
    private var spentNanos = 0L

    /**
     * How long [get] may still spend baking before this is called again, in milliseconds: once it is spent, a recipe that
     * is not baked yet is not drawn (null) and appears in one of the next frames, so that a frame never waits for many
     * pictures at once. A negative budget is no limit (the default).
     */
    /** The bucket [get] uses for [tilePx]: a caller that resolves many pictures at once asks for it once. */
    fun bucketForTile(tilePx: Int): Int = min(bucketFor(tilePx), bucketCap)

    fun setBudget(milliseconds: Int) {
        budgetNanos = if (milliseconds < 0) -1L else milliseconds * 1_000_000L
        spentNanos = 0L
    }

    fun get(recipeId: String, tilePx: Int, variant: String? = null): Sprite? {
        val bucket = min(bucketFor(tilePx), bucketCap)
        entries[recipeId]?.let { list ->
            for (entry in list) {
                if (entry.bucket == bucket && entry.variant == variant) return entry.sprite
            }
        }
        if (budgetNanos >= 0 && spentNanos > budgetNanos) return null // not this frame: the picture appears in one of the next
        val bakeStart = System.nanoTime()

        var sprite: Sprite? = null
        val text = pack.readDocument(recipeId)
        if (text == null) {
            Gdx.app.error(TAG, "Missing art recipe '$recipeId'")
        } else {
            parseRecipe(text).fold(
                onSuccess = { recipe ->
                    val bitmap = rasterize(recipe, bucket / 32f, variant)
                    val page = pageFor(bucket, bitmap.width, bitmap.height)
                    if (page == null) {
                        Gdx.app.error(TAG, "No room in the atlas of bucket $bucket for '$recipeId'")
                    } else {
                        val slotX = page.x
                        val slotY = page.y
                        put(page, bitmap, slotX, slotY)
                        val region = TextureRegion(page.texture, slotX, slotY, bitmap.width, bitmap.height)
                        region.flip(false, true)
                        sprite = Sprite(region, recipe.width, recipe.height, recipe.originX, recipe.originY, recipe.facesLeft, recipe.sway)
                    }
                },
                onFailure = { Gdx.app.error(TAG, "Cannot bake art recipe '$recipeId': ${it.message}") },
            )
        }
        entries.getOrPut(recipeId) { ArrayList(2) }.add(Entry(bucket, variant, sprite))
        spentNanos += System.nanoTime() - bakeStart
        return sprite
    }

    /** The page of [bucket] with room for a picture, a new one if none has it; the slot is taken. */
    private fun pageFor(bucket: Int, width: Int, height: Int): Page? {
        for (page in pages) {
            if (page.bucket == bucket && page.take(width, height)) return page
        }
        val size = pageSize(bucket)
        if (width > size || height > size) return null
        val page = Page(bucket, size)
        if (!page.take(width, height)) return null
        pages.add(page)
        return page
    }

    /**
     * Writes the picture into the pixmap of the page (kept for a lost context) and marks the part that has to reach the
     * GPU. The upload waits for [flushUploads]: a picture baked while a batch is open cannot bind its atlas, which would
     * leave the batch drawing the wrong texture (spec 13, "Atlases and batches").
     */
    private fun put(page: Page, bitmap: io.github.progliodario.aethermoor.core.vector.Bitmap, x: Int, y: Int) {
        val pixels = page.pixmap.pixels
        val rowBytes = bitmap.width * 4
        for (row in 0 until bitmap.height) {
            pixels.position(((y + row) * page.size + x) * 4)
            pixels.put(bitmap.rgba, row * rowBytes, rowBytes)
        }
        pixels.position(0)
        page.dirty(x, y, x + bitmap.width, y + bitmap.height)
    }

    /** Sends to the GPU the pictures baked since the last call. Call it with no batch open (the start of a frame). */
    fun flushUploads() {
        for (page in pages) {
            if (!page.hasDirty) continue
            val width = page.dirtyX1 - page.dirtyX0
            val height = page.dirtyY1 - page.dirtyY0
            val rowBytes = width * 4
            val upload = BufferUtils.newByteBuffer(rowBytes * height)
            val pixels = page.pixmap.pixels
            val row = ByteArray(rowBytes)
            for (y in 0 until height) {
                pixels.position(((page.dirtyY0 + y) * page.size + page.dirtyX0) * 4)
                pixels.get(row, 0, rowBytes)
                upload.put(row, 0, rowBytes)
            }
            pixels.position(0)
            upload.flip()
            page.texture.bind()
            Gdx.gl.glTexSubImage2D(GL20.GL_TEXTURE_2D, 0, page.dirtyX0, page.dirtyY0, width, height, GL20.GL_RGBA, GL20.GL_UNSIGNED_BYTE, upload)
            page.dirtyX0 = Int.MAX_VALUE
            page.dirtyY0 = Int.MAX_VALUE
            page.dirtyX1 = -1
            page.dirtyY1 = -1
        }
    }

    /** Disposes the atlases baked for other scale buckets than the one used by [tilePx]. */
    fun releaseOtherBuckets(tilePx: Int) {
        val bucket = min(bucketFor(tilePx), bucketCap)
        val iterator = entries.entries.iterator()
        while (iterator.hasNext()) {
            val list = iterator.next().value
            list.removeAll { it.bucket != bucket }
            if (list.isEmpty()) iterator.remove()
        }
        val pageIterator = pages.iterator()
        while (pageIterator.hasNext()) {
            val page = pageIterator.next()
            if (page.bucket != bucket) {
                page.texture.dispose()
                page.pixmap.dispose()
                pageIterator.remove()
            }
        }
    }

    fun dispose() {
        for (page in pages) {
            page.texture.dispose()
            page.pixmap.dispose()
        }
        pages.clear()
        entries.clear()
    }

    companion object {
        private const val TAG = "TextureCache"
        private const val GAP = 1
        private val BUCKETS = intArrayOf(32, 48, 64, 80, 96, 128, 192, 256)

        fun bucketFor(tilePx: Int): Int = BUCKETS.firstOrNull { tilePx <= it } ?: BUCKETS.last()

        /** The side of a page: big enough for the art of a level, small enough for the memory of a phone. */
        private fun pageSize(bucket: Int): Int = if (bucket <= 64) 1024 else 2048
    }
}
