package io.github.progliodario.aethermoor.game

import com.badlogic.gdx.ApplicationAdapter
import com.badlogic.gdx.Gdx
import com.badlogic.gdx.graphics.Color
import com.badlogic.gdx.graphics.GL20
import com.badlogic.gdx.graphics.OrthographicCamera
import com.badlogic.gdx.graphics.g2d.BitmapFont
import com.badlogic.gdx.graphics.g2d.SpriteBatch
import com.badlogic.gdx.graphics.glutils.ShapeRenderer
import io.github.progliodario.aethermoor.core.GameInfo
import io.github.progliodario.aethermoor.core.Pack
import io.github.progliodario.aethermoor.core.loadPack
import io.github.progliodario.aethermoor.core.sim.AttackPhase
import io.github.progliodario.aethermoor.core.sim.Enemy
import io.github.progliodario.aethermoor.core.sim.EnemyState
import io.github.progliodario.aethermoor.core.sim.Prop
import io.github.progliodario.aethermoor.core.sim.TICK_DT
import io.github.progliodario.aethermoor.core.sim.TileMap
import io.github.progliodario.aethermoor.core.sim.Tileset
import io.github.progliodario.aethermoor.core.sim.WorldSim
import io.github.progliodario.aethermoor.core.sim.loadCombatSetup
import io.github.progliodario.aethermoor.core.sim.parseTileMap
import io.github.progliodario.aethermoor.core.sim.parseTileset
import io.github.progliodario.aethermoor.core.vector.Clip
import io.github.progliodario.aethermoor.core.vector.Rig
import io.github.progliodario.aethermoor.core.vector.evaluatePose
import io.github.progliodario.aethermoor.core.vector.parseClip
import io.github.progliodario.aethermoor.core.vector.parseRig
import java.util.Locale
import kotlin.math.PI
import kotlin.math.atan2
import kotlin.math.ceil
import kotlin.math.floor
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

/**
 * M3 client: a vector-art character exploring a tile map and fighting slimes, drawn with libGDX.
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
    )

    private class FloatingText(val x: Float, val y: Float, val text: String, val onPlayer: Boolean, val crit: Boolean) {
        var age = 0
    }

    private lateinit var batch: SpriteBatch
    private lateinit var shapes: ShapeRenderer
    private lateinit var font: BitmapFont
    private lateinit var camera: OrthographicCamera
    private lateinit var cache: TextureCache
    private val input = InputController()

    private var assets: Assets? = null
    private var sim: WorldSim? = null
    private var error: String? = null
    private var language = "en"
    private var accumulator = 0f
    private val floating = ArrayList<FloatingText>()

    override fun create() {
        batch = SpriteBatch()
        shapes = ShapeRenderer()
        font = BitmapFont(true) // flipped: the projection has y pointing down
        camera = OrthographicCamera()
        language = if (Locale.getDefault().language == "it") "it" else "en"

        val loaded = loadAssets() ?: return
        assets = loaded
        cache = TextureCache(loaded.pack)
        val combat = loadCombatSetup(loaded.pack, loaded.map, PROTAGONIST_ID, System.nanoTime().toULong())
            .getOrElse {
                error = it.message
                Gdx.app.error(TAG, "Cannot build the combat setup: ${it.message}")
                return
            }
        sim = WorldSim(loaded.map, loaded.tileset, 0f, combat)
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
            Assets(
                pack = pack,
                rig = parseRig(doc("base:art/rig/humanoid")).getOrThrow(),
                idle = parseClip(doc("base:art/clip/humanoid_idle")).getOrThrow(),
                walk = parseClip(doc("base:art/clip/humanoid_walk")).getOrThrow(),
                map = parseTileMap(requireNotNull(pack.readFile("maps/demo.tmj")) { "missing maps/demo.tmj" }).getOrThrow(),
                tileset = parseTileset(doc("base:tileset/overworld")).getOrThrow(),
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

        val frame = input.read()
        accumulator += min(Gdx.graphics.deltaTime, MAX_FRAME_SECONDS)
        var ticks = 0
        while (accumulator >= TICK_DT && ticks < MAX_TICKS_PER_FRAME) {
            world.tick(frame.x, frame.y, frame.attack)
            accumulator -= TICK_DT
            ticks++
        }
        if (ticks == MAX_TICKS_PER_FRAME) accumulator = 0f

        for (e in world.takeEvents()) floating.add(FloatingText(e.position.x, e.position.y, e.amount.toString(), e.onPlayer, e.crit))
        floating.forEach { it.age++ }
        floating.removeAll { it.age > FLOATING_TEXT_FRAMES }

        val tilePx = max(16, (BASE_TILE_PX * Gdx.graphics.density).roundToInt())
        cache.releaseOtherBuckets(tilePx)
        draw(world, data, tilePx)
    }

    private fun draw(world: WorldSim, data: Assets, tilePx: Int) {
        val tile = tilePx.toFloat()
        val k = tile / 32f
        val viewW = Gdx.graphics.width / tile
        val viewH = Gdx.graphics.height / tile
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

        // Props, enemies and the player, sorted by feet y (smaller first; ties keep list order, the player last).
        class Item(val feetY: Float, val prop: Prop?, val enemy: Enemy?)
        val items = ArrayList<Item>()
        for (prop in map.props) {
            if (prop.x >= cam.x - 2f && prop.x <= cam.x + viewW + 2f && prop.y >= cam.y - 1f && prop.y <= cam.y + viewH + 4f) {
                items.add(Item(prop.y, prop, null))
            }
        }
        for (enemy in world.enemies) if (enemy.state != EnemyState.DEAD) items.add(Item(enemy.position.y, null, enemy))
        items.add(Item(world.player.position.y, null, null))
        for (item in items.sortedBy { it.feetY }) {
            when {
                item.prop != null -> drawProp(item.prop, cam.x, cam.y, tilePx, tile, k)
                item.enemy != null -> drawEnemy(item.enemy, cam.x, cam.y, tilePx, tile, k)
                else -> drawPlayer(world, data, cam.x, cam.y, tilePx, k)
            }
        }
        batch.end()

        drawOverlays(world, cam.x, cam.y, tile, k)
        drawTexts(world, data, cam.x, cam.y, tile)
        drawStick()
    }

    private fun drawProp(prop: Prop, camX: Float, camY: Float, tilePx: Int, tile: Float, k: Float) {
        val sprite = cache.get(prop.art, tilePx) ?: return
        val fx = (prop.x - camX) * tile
        val fy = (prop.y - camY) * tile
        batch.draw(sprite.region, fx - sprite.originX * k, fy - sprite.originY * k, sprite.width * k, sprite.height * k)
    }

    private fun drawEnemy(enemy: Enemy, camX: Float, camY: Float, tilePx: Int, tile: Float, k: Float) {
        val sprite = cache.get(enemy.def.art, tilePx) ?: return
        val fx = (enemy.position.x - camX) * tile
        val fy = (enemy.position.y - camY) * tile
        val phase = ((System.currentTimeMillis() / 16 + (enemy.home.x * 37f).toLong()) % 60).toFloat()
        val wave = if (phase < 30f) phase / 30f else (60f - phase) / 30f
        val squash = 0.95f + 0.1f * wave
        if (enemy.hitFlash > 0) batch.setColor(1f, 0.47f, 0.47f, 1f)
        batch.draw(
            sprite.region,
            fx - sprite.originX * k * (2f - squash), fy - sprite.originY * k * squash,
            sprite.width * k * (2f - squash), sprite.height * k * squash,
        )
        batch.setColor(1f, 1f, 1f, 1f)
    }

    private fun drawPlayer(world: WorldSim, data: Assets, camX: Float, camY: Float, tilePx: Int, k: Float) {
        val tile = tilePx.toFloat()
        val player = world.player
        val feetX = (player.position.x - camX) * tile
        val feetY = (player.position.y - camY) * tile
        val clip = if (player.moving) data.walk else data.idle
        val pose = evaluatePose(data.rig, clip, player.clipTick.toFloat(), player.facingLeft).sortedBy { it.z }
        val blink = player.iframes > 0 && (player.iframes / 4) % 2 == 0
        batch.setColor(1f, 1f, 1f, if (blink) 0.47f else 1f)
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
        batch.setColor(1f, 1f, 1f, 1f)
    }

    /** Enemy health bars, the sword swing and the HUD bars (shapes, no textures). */
    private fun drawOverlays(world: WorldSim, camX: Float, camY: Float, tile: Float, k: Float) {
        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        Gdx.gl.glBlendFunc(GL20.GL_SRC_ALPHA, GL20.GL_ONE_MINUS_SRC_ALPHA)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        for (enemy in world.enemies) {
            if (enemy.state == EnemyState.DEAD || enemy.hp >= enemy.def.hp) continue
            val sprite = cache.get(enemy.def.art, max(16, tile.roundToInt())) ?: continue
            val fx = (enemy.position.x - camX) * tile
            val fy = (enemy.position.y - camY) * tile - sprite.height * k - 3f * k
            val barW = 28f * k
            shapes.color = Color(0.08f, 0.08f, 0.08f, 0.8f)
            shapes.rect(fx - barW / 2f, fy, barW, 2f * k)
            shapes.color = Color(0.86f, 0.27f, 0.27f, 1f)
            shapes.rect(fx - barW / 2f, fy, barW * enemy.hp.toFloat() / enemy.def.hp.toFloat(), 2f * k)
        }

        val p = world.player
        if (p.phase == AttackPhase.ACTIVE || p.phase == AttackPhase.RECOVERY) {
            val skill = world.combat.skill
            val radius = skill.radiusX100 / 100f * tile
            val centerDeg = atan2(p.facing.y, p.facing.x) * 180f / PI.toFloat()
            shapes.color = Color(1f, 1f, 1f, if (p.phase == AttackPhase.ACTIVE) 0.35f else 0.12f)
            shapes.arc(
                (p.position.x - camX) * tile, (p.position.y - camY) * tile - 0.5f * tile,
                radius, centerDeg - skill.angleDeg / 2f, skill.angleDeg.toFloat(),
            )
        }

        val density = Gdx.graphics.density
        val barW = 220f * density
        val barH = 16f * density
        val x = 12f * density
        val y = 12f * density
        val hpRatio = (p.hp.toFloat() / world.derived.maxHp.toFloat()).coerceIn(0f, 1f)
        val need = world.combat.xpTable.getOrNull((p.level - 1).toInt()) ?: 0L
        val xpRatio = if (need > 0) (p.xp.toFloat() / need.toFloat()).coerceIn(0f, 1f) else 0f
        shapes.color = Color(0.04f, 0.08f, 0.16f, 0.8f)
        shapes.rect(x - 2f, y - 2f, barW + 4f, barH + 4f)
        shapes.color = Color(0.82f, 0.24f, 0.24f, 1f)
        shapes.rect(x, y, barW * hpRatio, barH)
        shapes.color = Color(0.04f, 0.08f, 0.16f, 0.8f)
        shapes.rect(x, y + barH + 6f, barW, 6f * density)
        shapes.color = Color(0.35f, 0.78f, 0.47f, 1f)
        shapes.rect(x, y + barH + 6f, barW * xpRatio, 6f * density)
        shapes.end()
    }

    private fun drawTexts(world: WorldSim, data: Assets, camX: Float, camY: Float, tile: Float) {
        batch.projectionMatrix = camera.combined
        batch.begin()
        val density = Gdx.graphics.density
        val p = world.player
        font.color = Color.WHITE
        font.draw(batch, "${data.pack.text(language, "\$i18n:ui.hp")} ${p.hp}/${world.derived.maxHp}", 12f * density + 4f, 12f * density + 2f)
        font.draw(batch, data.pack.text(language, "\$i18n:ui.level", mapOf("level" to p.level)), 12f * density, 12f * density + 16f * density + 20f)
        for (f in floating) {
            font.color = when {
                f.onPlayer -> Color(1f, 0.35f, 0.35f, 1f)
                f.crit -> Color(1f, 0.86f, 0.31f, 1f)
                else -> Color.WHITE
            }
            font.draw(batch, f.text, (f.x - camX) * tile - f.text.length * 4f, (f.y - camY) * tile - tile - f.age * 0.6f * density)
        }
        font.color = Color(0.435f, 0.89f, 1f, 1f)
        font.draw(batch, "${info.versionLine()}  ${Gdx.graphics.framesPerSecond} fps", 8f, Gdx.graphics.height - font.lineHeight - 4f)
        batch.end()
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
        private const val PROTAGONIST_ID = "base:protagonist/ren"
        private const val BASE_TILE_PX = 48f
        private const val MAX_TICKS_PER_FRAME = 5
        private const val MAX_FRAME_SECONDS = 0.25f
        private const val FLOATING_TEXT_FRAMES = 50
    }
}
