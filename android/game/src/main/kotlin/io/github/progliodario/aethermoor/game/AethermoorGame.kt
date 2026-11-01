package io.github.progliodario.aethermoor.game

import com.badlogic.gdx.ApplicationAdapter
import com.badlogic.gdx.Gdx
import com.badlogic.gdx.graphics.Color
import com.badlogic.gdx.graphics.GL20
import com.badlogic.gdx.graphics.OrthographicCamera
import com.badlogic.gdx.graphics.g2d.BitmapFont
import com.badlogic.gdx.graphics.g2d.SpriteBatch
import com.badlogic.gdx.graphics.glutils.ShapeRenderer
import io.github.progliodario.aethermoor.core.Equipment
import io.github.progliodario.aethermoor.core.GameInfo
import io.github.progliodario.aethermoor.core.Pack
import io.github.progliodario.aethermoor.core.derivedStats
import io.github.progliodario.aethermoor.core.loadPack
import io.github.progliodario.aethermoor.core.parseProtagonist
import io.github.progliodario.aethermoor.core.sim.Prop
import io.github.progliodario.aethermoor.core.sim.TICK_DT
import io.github.progliodario.aethermoor.core.sim.TileMap
import io.github.progliodario.aethermoor.core.sim.Tileset
import io.github.progliodario.aethermoor.core.sim.WorldSim
import io.github.progliodario.aethermoor.core.sim.parseTileMap
import io.github.progliodario.aethermoor.core.sim.parseTileset
import io.github.progliodario.aethermoor.core.vector.Clip
import io.github.progliodario.aethermoor.core.vector.Rig
import io.github.progliodario.aethermoor.core.vector.evaluatePose
import io.github.progliodario.aethermoor.core.vector.parseClip
import io.github.progliodario.aethermoor.core.vector.parseRig
import kotlin.math.ceil
import kotlin.math.floor
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

/**
 * M2 client: a vector-art character walking around a tile map, drawn with libGDX.
 * Mirrors desktop/src/app/main.cpp (draw order, scale buckets, fixed 60 Hz simulation).
 */
class AethermoorGame(private val info: GameInfo) : ApplicationAdapter() {
    private class Assets(
        val pack: Pack,
        val rig: Rig,
        val idle: Clip,
        val walk: Clip,
        val map: TileMap,
        val tileset: Tileset,
        val speedTilesPerS: Float,
    )

    private lateinit var batch: SpriteBatch
    private lateinit var shapes: ShapeRenderer
    private lateinit var font: BitmapFont
    private lateinit var camera: OrthographicCamera
    private lateinit var cache: TextureCache
    private val input = InputController()

    private var assets: Assets? = null
    private var sim: WorldSim? = null
    private var error: String? = null
    private var accumulator = 0f

    override fun create() {
        batch = SpriteBatch()
        shapes = ShapeRenderer()
        font = BitmapFont().apply { color = Color(0.435f, 0.89f, 1f, 1f) }
        camera = OrthographicCamera()

        val loaded = loadAssets() ?: return
        assets = loaded
        cache = TextureCache(loaded.pack)
        sim = WorldSim(loaded.map, loaded.tileset, loaded.speedTilesPerS)
    }

    private fun loadAssets(): Assets? {
        val errors = ArrayList<String>()
        val pack = loadPack(GdxPackSource(), errors)
        errors.forEach { Gdx.app.error(TAG, it) }
        if (pack == null) {
            error = "pack"
            return null
        }
        return try {
            fun doc(id: String) = requireNotNull(pack.readDocument(id)) { "missing document $id" }
            val protagonist = parseProtagonist(doc("base:protagonist/ren")).getOrThrow()
            val stats = derivedStats(1, protagonist.baseStats, Equipment())
            Assets(
                pack = pack,
                rig = parseRig(doc("base:art/rig/humanoid")).getOrThrow(),
                idle = parseClip(doc("base:art/clip/humanoid_idle")).getOrThrow(),
                walk = parseClip(doc("base:art/clip/humanoid_walk")).getOrThrow(),
                map = parseTileMap(requireNotNull(pack.readFile("maps/demo.tmj")) { "missing maps/demo.tmj" }).getOrThrow(),
                tileset = parseTileset(doc("base:tileset/overworld")).getOrThrow(),
                speedTilesPerS = stats.moveSpeedX100 / 100f,
            )
        } catch (e: IllegalArgumentException) {
            error = e.message
            Gdx.app.error(TAG, "Cannot load game data: ${e.message}")
            null
        } catch (e: IllegalStateException) {
            error = e.message
            Gdx.app.error(TAG, "Cannot load game data: ${e.message}")
            null
        }
    }

    override fun resize(width: Int, height: Int) {
        camera.setToOrtho(true, width.toFloat(), height.toFloat())
        camera.update()
    }

    override fun render() {
        Gdx.gl.glClearColor(0.043f, 0.122f, 0.227f, 1f)
        Gdx.gl.glClear(GL20.GL_COLOR_BUFFER_BIT)
        val world = sim
        val data = assets
        if (world == null || data == null) {
            drawError()
            return
        }

        val (rawX, rawY) = input.read()
        accumulator += min(Gdx.graphics.deltaTime, MAX_FRAME_SECONDS)
        var ticks = 0
        while (accumulator >= TICK_DT && ticks < MAX_TICKS_PER_FRAME) {
            world.tick(rawX, rawY)
            accumulator -= TICK_DT
            ticks++
        }
        if (ticks == MAX_TICKS_PER_FRAME) accumulator = 0f

        val tilePx = max(16, (BASE_TILE_PX * Gdx.graphics.density).roundToInt())
        cache.releaseOtherBuckets(tilePx)
        draw(world, data, tilePx)
    }

    private fun draw(world: WorldSim, data: Assets, tilePx: Int) {
        val tile = tilePx.toFloat()
        val k = tile / 32f
        val width = Gdx.graphics.width
        val height = Gdx.graphics.height
        val viewW = width / tile
        val viewH = height / tile
        val cam = world.camera(viewW, viewH)

        batch.projectionMatrix = camera.combined
        batch.begin()

        val map = world.map
        val x0 = max(0, floor(cam.x).toInt())
        val x1 = min(map.width, ceil(cam.x + viewW).toInt())
        val y0 = max(0, floor(cam.y).toInt())
        val y1 = min(map.height, ceil(cam.y + viewH).toInt())
        for (ty in y0 until y1) {
            for (tx in x0 until x1) {
                val def = data.tileset.tiles[map.gidAt(tx, ty)] ?: continue
                val sprite = cache.get(def.art, tilePx) ?: continue
                val sx0 = ((tx - cam.x) * tile).roundToInt().toFloat()
                val sy0 = ((ty - cam.y) * tile).roundToInt().toFloat()
                val sx1 = ((tx + 1 - cam.x) * tile).roundToInt().toFloat()
                val sy1 = ((ty + 1 - cam.y) * tile).roundToInt().toFloat()
                batch.draw(sprite.region, sx0, sy0, sx1 - sx0, sy1 - sy0)
            }
        }

        // Props and the player, sorted by feet y (smaller first; ties keep map order, the player last).
        val visible = map.props.filter {
            it.x >= cam.x - 2f && it.x <= cam.x + viewW + 2f && it.y >= cam.y - 1f && it.y <= cam.y + viewH + 4f
        }
        val playerY = world.player.position.y
        var playerDrawn = false
        for (prop in visible.sortedBy { it.y }) {
            if (!playerDrawn && prop.y > playerY) {
                drawPlayer(world, data, cam.x, cam.y, tilePx, k)
                playerDrawn = true
            }
            drawProp(prop, cam.x, cam.y, tilePx, tile, k)
        }
        if (!playerDrawn) drawPlayer(world, data, cam.x, cam.y, tilePx, k)

        font.draw(
            batch,
            "${info.versionLine()}  ${Gdx.graphics.framesPerSecond} fps  pos %.2f,%.2f  tile %dpx  textures %d".format(
                world.player.position.x, world.player.position.y, tilePx, cache.size,
            ),
            8f,
            8f + font.lineHeight,
        )
        batch.end()
        drawStick()
    }

    private fun drawProp(prop: Prop, camX: Float, camY: Float, tilePx: Int, tile: Float, k: Float) {
        val sprite = cache.get(prop.art, tilePx) ?: return
        val fx = (prop.x - camX) * tile
        val fy = (prop.y - camY) * tile
        batch.draw(sprite.region, fx - sprite.originX * k, fy - sprite.originY * k, sprite.width * k, sprite.height * k)
    }

    private fun drawPlayer(world: WorldSim, data: Assets, camX: Float, camY: Float, tilePx: Int, k: Float) {
        val tile = tilePx.toFloat()
        val player = world.player
        val feetX = (player.position.x - camX) * tile
        val feetY = (player.position.y - camY) * tile
        val clip = if (player.moving) data.walk else data.idle
        val pose = evaluatePose(data.rig, clip, player.clipTick.toFloat(), player.facingLeft).sortedBy { it.z }
        for (posed in pose) {
            val part = data.rig.parts[posed.partIndex]
            val sprite = cache.get(part.art, tilePx) ?: continue
            val px = feetX + posed.x * k
            val py = feetY + posed.y * k
            val pivotX = sprite.originX * k
            val pivotY = sprite.originY * k
            // Mirroring flips the part about its pivot; the pose already negated positions and rotations.
            batch.draw(
                sprite.region,
                px - pivotX, py - pivotY,
                pivotX, pivotY,
                sprite.width * k, sprite.height * k,
                if (player.facingLeft) -1f else 1f, 1f,
                posed.rotationDeg,
            )
        }
    }

    private fun drawStick() {
        val origin = input.stickOrigin ?: return
        val position = input.stickPosition ?: return
        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        shapes.color = Color(1f, 1f, 1f, 0.18f)
        shapes.circle(origin.first, origin.second, InputController.STICK_RADIUS_DP * Gdx.graphics.density)
        shapes.color = Color(0.435f, 0.89f, 1f, 0.5f)
        shapes.circle(position.first, position.second, 22f * Gdx.graphics.density)
        shapes.end()
    }

    private fun drawError() {
        batch.projectionMatrix = camera.combined
        batch.begin()
        font.draw(batch, "${info.versionLine()}: cannot load the game data (${error ?: "unknown"})", 16f, 32f)
        batch.end()
    }

    override fun dispose() {
        batch.dispose()
        shapes.dispose()
        font.dispose()
        if (::cache.isInitialized) cache.dispose()
    }

    companion object {
        private const val TAG = "Aethermoor"
        private const val BASE_TILE_PX = 48f
        private const val MAX_TICKS_PER_FRAME = 5
        private const val MAX_FRAME_SECONDS = 0.25f
    }
}
