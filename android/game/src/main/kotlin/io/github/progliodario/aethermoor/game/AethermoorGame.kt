package io.github.progliodario.aethermoor.game

import com.badlogic.gdx.ApplicationAdapter
import com.badlogic.gdx.Gdx
import com.badlogic.gdx.Input
import com.badlogic.gdx.graphics.Color
import com.badlogic.gdx.graphics.GL20
import com.badlogic.gdx.graphics.OrthographicCamera
import com.badlogic.gdx.graphics.g2d.BitmapFont
import com.badlogic.gdx.graphics.g2d.GlyphLayout
import com.badlogic.gdx.graphics.g2d.SpriteBatch
import com.badlogic.gdx.graphics.glutils.ShapeRenderer
import io.github.progliodario.aethermoor.core.GameInfo
import io.github.progliodario.aethermoor.core.Pack
import io.github.progliodario.aethermoor.core.loadPack
import io.github.progliodario.aethermoor.core.sim.AttackPhase
import io.github.progliodario.aethermoor.core.sim.Enemy
import io.github.progliodario.aethermoor.core.sim.EnemyState
import io.github.progliodario.aethermoor.core.sim.NpcDef
import io.github.progliodario.aethermoor.core.sim.Prop
import io.github.progliodario.aethermoor.core.sim.QuestStage
import io.github.progliodario.aethermoor.core.sim.SaveMeta
import io.github.progliodario.aethermoor.core.sim.saveFromJson
import io.github.progliodario.aethermoor.core.sim.saveToJson
import io.github.progliodario.aethermoor.core.sim.TICK_DT
import io.github.progliodario.aethermoor.core.sim.TileMap
import io.github.progliodario.aethermoor.core.sim.Tileset
import io.github.progliodario.aethermoor.core.sim.ObjectiveKind
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
    private val layout = GlyphLayout()
    private var choiceIndex = 0
    private var choiceRects: List<FloatArray> = emptyList()
    private var talkRect: FloatArray? = null
    private var lastSpeaker = ""
    private var lastText = ""
    private var showInventory = false
    private var bagRect: FloatArray? = null
    private var message = ""
    private var messageFrames = 0
    private var sinceAutosave = 0f
    private var seed = 0uL

    override fun create() {
        batch = SpriteBatch()
        shapes = ShapeRenderer()
        font = BitmapFont(true) // flipped: the projection has y pointing down
        font.data.setScale(max(1f, Gdx.graphics.density * 0.9f))
        camera = OrthographicCamera()
        language = if (Locale.getDefault().language == "it") "it" else "en"

        val loaded = loadAssets() ?: return
        assets = loaded
        cache = TextureCache(loaded.pack)
        seed = System.nanoTime().toULong()
        val combat = loadCombatSetup(loaded.pack, loaded.map, PROTAGONIST_ID, seed)
            .getOrElse {
                error = it.message
                Gdx.app.error(TAG, "Cannot build the combat setup: ${it.message}")
                return
            }
        val world = WorldSim(loaded.map, loaded.tileset, 0f, combat)
        sim = world
        loadAutosave(world, loaded.pack)
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

    // ------------------------------------------------------------------------------------ saves

    private fun saveFile() = Gdx.files.local("saves/auto.json")

    /** Writes the autosave (a temporary file first, then a move over the old save). */
    private fun saveGame(world: WorldSim) {
        try {
            val temp = Gdx.files.local("saves/auto.json.tmp")
            temp.writeString(saveToJson(world.capture(), SaveMeta(info.version, 1, PROTAGONIST_ID, seed)), false, "UTF-8")
            temp.moveTo(saveFile())
        } catch (e: com.badlogic.gdx.utils.GdxRuntimeException) {
            Gdx.app.error(TAG, "Cannot write the save: ${e.message}")
        }
    }

    private fun loadAutosave(world: WorldSim, pack: Pack) {
        val file = saveFile()
        if (!file.exists()) return
        val result = saveFromJson(file.readString("UTF-8")).mapCatching { world.restore(it).getOrThrow() }
        if (result.isSuccess) {
            showNotice(pack.text(language, "\$i18n:ui.loaded"))
        } else {
            Gdx.app.error(TAG, "Cannot load the save: ${result.exceptionOrNull()?.message}")
        }
    }

    private fun showNotice(text: String) {
        message = text
        messageFrames = 150
    }

    override fun pause() {
        sim?.let { saveGame(it) }
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

        handleStoryInput(world)
        val frame = input.read()
        if (showInventory) {
            accumulator = 0f // the bag pauses the game
        } else {
            accumulator += min(Gdx.graphics.deltaTime, MAX_FRAME_SECONDS)
            var ticks = 0
            while (accumulator >= TICK_DT && ticks < MAX_TICKS_PER_FRAME) {
                world.tick(frame.x, frame.y, frame.attack)
                accumulator -= TICK_DT
                ticks++
            }
            if (ticks == MAX_TICKS_PER_FRAME) accumulator = 0f
        }
        if (messageFrames > 0) messageFrames--
        sinceAutosave += Gdx.graphics.deltaTime
        if (sinceAutosave >= AUTOSAVE_SECONDS) {
            sinceAutosave = 0f
            saveGame(world)
        }

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
        class Item(val feetY: Float, val prop: Prop?, val enemy: Enemy?, val npc: NpcDef? = null)
        val items = ArrayList<Item>()
        for (prop in map.props) {
            if (prop.x >= cam.x - 2f && prop.x <= cam.x + viewW + 2f && prop.y >= cam.y - 1f && prop.y <= cam.y + viewH + 4f) {
                items.add(Item(prop.y, prop, null))
            }
        }
        for (enemy in world.enemies) if (enemy.state != EnemyState.DEAD) items.add(Item(enemy.position.y, null, enemy))
        for (npc in world.story.setup.npcs) items.add(Item(npc.y, null, null, npc))
        items.add(Item(world.player.position.y, null, null))
        for (item in items.sortedBy { it.feetY }) {
            when {
                item.prop != null -> drawProp(item.prop, cam.x, cam.y, tilePx, tile, k)
                item.enemy != null -> drawEnemy(item.enemy, cam.x, cam.y, tilePx, tile, k)
                item.npc != null -> drawNpc(world, data, item.npc, cam.x, cam.y, tilePx, k)
                else -> drawPlayer(world, data, cam.x, cam.y, tilePx, k)
            }
        }
        batch.end()

        drawOverlays(world, cam.x, cam.y, tile, k)
        drawTexts(world, data, cam.x, cam.y, tile)
        drawStory(world, data)
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
        val blink = player.iframes > 0 && (player.iframes / 4) % 2 == 0
        drawCharacter(
            data, player.moving, player.facingLeft, player.clipTick, blink, null,
            (player.position.x - camX) * tile, (player.position.y - camY) * tile, tilePx, k,
        )
    }

    private fun drawNpc(world: WorldSim, data: Assets, npc: NpcDef, camX: Float, camY: Float, tilePx: Int, k: Float) {
        val tile = tilePx.toFloat()
        drawCharacter(
            data, false, world.player.position.x < npc.x, (System.currentTimeMillis() / 16).toInt(), false,
            npc.variant.ifEmpty { null }, (npc.x - camX) * tile, (npc.y - camY) * tile, tilePx, k,
        )
    }

    private fun drawCharacter(
        data: Assets, moving: Boolean, facingLeft: Boolean, clipTick: Int, blink: Boolean, variant: String?,
        feetX: Float, feetY: Float, tilePx: Int, k: Float,
    ) {
        val clip = if (moving) data.walk else data.idle
        val pose = evaluatePose(data.rig, clip, clipTick.toFloat(), facingLeft).sortedBy { it.z }
        batch.setColor(1f, 1f, 1f, if (blink) 0.47f else 1f)
        for (posed in pose) {
            val part = data.rig.parts[posed.partIndex]
            val sprite = cache.get(part.art, tilePx, variant) ?: continue
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
                if (facingLeft) -1f else 1f, 1f,
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

    // ------------------------------------------------------------------------------------ story

    private fun handleStoryInput(world: WorldSim) {
        val story = world.story
        val input = Gdx.input
        val view = story.dialogueView()
        if (showInventory) {
            if (input.isKeyJustPressed(Input.Keys.I) || input.isKeyJustPressed(Input.Keys.ESCAPE) || input.justTouched()) showInventory = false
            return
        }
        if (input.isKeyJustPressed(Input.Keys.I)) {
            showInventory = true
            return
        }
        val confirm = input.isKeyJustPressed(Input.Keys.E) || input.isKeyJustPressed(Input.Keys.ENTER) ||
            (view.active && input.isKeyJustPressed(Input.Keys.SPACE))
        if (view.active && view.isChoice) {
            val count = view.choices.size
            if (count > 0) {
                if (input.isKeyJustPressed(Input.Keys.UP) || input.isKeyJustPressed(Input.Keys.W)) {
                    choiceIndex = (choiceIndex + count - 1) % count
                }
                if (input.isKeyJustPressed(Input.Keys.DOWN) || input.isKeyJustPressed(Input.Keys.S)) {
                    choiceIndex = (choiceIndex + 1) % count
                }
                for (n in 0 until min(count, 9)) {
                    if (input.isKeyJustPressed(Input.Keys.NUM_1 + n)) {
                        story.choose(n)
                        choiceIndex = 0
                        return
                    }
                }
            }
        }
        if (confirm) {
            if (view.active && view.isChoice) story.choose(choiceIndex) else story.interact()
            choiceIndex = 0
            return
        }
        if (input.justTouched()) {
            val x = input.x.toFloat()
            val y = input.y.toFloat()
            if (view.active) {
                if (view.isChoice) {
                    val row = choiceRects.indexOfFirst { x >= it[0] && x <= it[0] + it[2] && y >= it[1] && y <= it[1] + it[3] }
                    if (row >= 0) story.choose(row)
                } else {
                    story.advance()
                }
                choiceIndex = 0
            } else {
                val bag = bagRect
                if (bag != null && x >= bag[0] && x <= bag[0] + bag[2] && y >= bag[1] && y <= bag[1] + bag[3]) {
                    showInventory = true
                    return
                }
                val rect = talkRect
                if (rect != null && story.npcInRange() != null &&
                    x >= rect[0] && x <= rect[0] + rect[2] && y >= rect[1] && y <= rect[1] + rect[3]
                ) {
                    story.interact()
                    choiceIndex = 0
                }
            }
        }
        this.input.attackExcludedRect = talkRect.takeIf { !story.dialogueView().active && story.npcInRange() != null }
    }

    /** Quest tracker, gold, the talk button and the dialogue box. */
    private fun drawStory(world: WorldSim, data: Assets) {
        val story = world.story
        val density = Gdx.graphics.density
        val width = Gdx.graphics.width.toFloat()
        val height = Gdx.graphics.height.toFloat()
        val view = story.dialogueView()
        if (view.active && !view.isChoice) {
            lastSpeaker = view.speaker
            lastText = view.text
        } else if (!view.active) {
            lastText = ""
        }

        // Layout of the dialogue box (computed first so the shapes pass can draw it).
        val margin = 16f * density
        val boxW = width - 2f * margin
        var boxH = 0f
        var heading = ""
        var questionHeight = 0f
        if (view.active) {
            if (view.isChoice) {
                boxH = view.choices.size * (font.lineHeight * 1.5f) + 24f * density
                if (lastText.isNotEmpty()) {
                    heading = data.pack.text(language, "\$i18n:speaker.$lastSpeaker")
                    layout.setText(font, data.pack.text(language, lastText), Color.WHITE, boxW - 24f * density, 0, true)
                    questionHeight = layout.height + font.lineHeight * 1.5f + 8f * density
                    boxH += questionHeight
                }
            } else {
                heading = data.pack.text(language, "\$i18n:speaker.${view.speaker}")
                layout.setText(font, data.pack.text(language, view.text), Color.WHITE, boxW - 24f * density, 0, true)
                boxH = layout.height + font.lineHeight * 1.5f + 24f * density
            }
        }
        val boxY = height - boxH - margin

        // Talk button for touch screens.
        val canTalk = !view.active && story.npcInRange() != null
        val button = floatArrayOf(width - 150f * density, height / 2f - 40f * density, 130f * density, 60f * density)
        talkRect = button

        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        if (canTalk) {
            shapes.color = Color(0.04f, 0.12f, 0.23f, 0.85f)
            shapes.rect(button[0], button[1], button[2], button[3])
        }
        if (view.active) {
            shapes.color = Color(0.04f, 0.12f, 0.23f, 0.92f)
            shapes.rect(margin, boxY, boxW, boxH)
            shapes.color = Color(0.435f, 0.89f, 1f, 1f)
            shapes.rect(margin, boxY, boxW, 3f * density)
            if (view.isChoice) {
                val rowH = font.lineHeight * 1.5f
                choiceRects = view.choices.indices.map { i -> floatArrayOf(margin, boxY + 12f * density + questionHeight + i * rowH, boxW, rowH) }
                if (choiceIndex in view.choices.indices) {
                    shapes.color = Color(0.435f, 0.89f, 1f, 0.25f)
                    val r = choiceRects[choiceIndex]
                    shapes.rect(r[0], r[1], r[2], r[3])
                }
            }
        }
        shapes.end()

        batch.projectionMatrix = camera.combined
        batch.begin()
        // Gold and the quest tracker, top right.
        var y = 12f * density
        val x = width - 300f * density
        font.color = Color(1f, 0.84f, 0.47f, 1f)
        font.draw(batch, data.pack.text(language, "\$i18n:ui.gold", mapOf("gold" to story.gold)), x, y)
        y += font.lineHeight * 1.3f
        for ((questId, progress) in story.quests) {
            if (progress.done) continue
            val def = story.setup.quests.getValue(questId)
            val stage: QuestStage = def.stages.firstOrNull { it.id == progress.stage } ?: continue
            font.color = Color(0.435f, 0.89f, 1f, 1f)
            font.draw(batch, data.pack.text(language, def.name), x, y)
            y += font.lineHeight * 1.2f
            font.color = Color(0.92f, 0.96f, 1f, 1f)
            layout.setText(font, data.pack.text(language, stage.journal), font.color, 280f * density, 0, true)
            font.draw(batch, layout, x, y)
            y += layout.height + 4f * density
            for ((i, objective) in stage.objectives.withIndex()) {
                if (objective.kind == ObjectiveKind.TALK) continue
                font.draw(batch, "  ${progress.progress[i]}/${objective.count}", x, y)
                y += font.lineHeight * 1.2f
            }
            y += 6f * density
        }

        if (canTalk) {
            font.color = Color.WHITE
            font.draw(
                batch, data.pack.text(language, "\$i18n:ui.interact"),
                button[0] + 12f * density, button[1] + button[3] / 2f - font.lineHeight / 2f,
            )
        }

        if (view.active) {
            var ty = boxY + 12f * density
            if (view.isChoice) {
                if (lastText.isNotEmpty()) {
                    font.color = Color(1f, 0.84f, 0.47f, 1f)
                    font.draw(batch, heading, margin + 12f * density, ty)
                    font.color = Color(0.92f, 0.96f, 1f, 1f)
                    layout.setText(font, data.pack.text(language, lastText), font.color, boxW - 24f * density, 0, true)
                    font.draw(batch, layout, margin + 12f * density, ty + font.lineHeight * 1.5f)
                    ty += questionHeight
                }
                for ((i, choice) in view.choices.withIndex()) {
                    font.color = if (i == choiceIndex) Color(0.435f, 0.89f, 1f, 1f) else Color.WHITE
                    font.draw(
                        batch, "${i + 1}. ${data.pack.text(language, choice)}",
                        margin + 12f * density, ty + (font.lineHeight * 1.5f - font.lineHeight) / 2f,
                    )
                    ty += font.lineHeight * 1.5f
                }
            } else {
                font.color = Color(1f, 0.84f, 0.47f, 1f)
                font.draw(batch, heading, margin + 12f * density, ty)
                ty += font.lineHeight * 1.5f
                font.color = Color(0.92f, 0.96f, 1f, 1f)
                layout.setText(font, data.pack.text(language, view.text), font.color, boxW - 24f * density, 0, true)
                font.draw(batch, layout, margin + 12f * density, ty)
            }
        }
        font.color = Color.WHITE
        batch.end()
        drawBagAndNotice(world, data)
    }

    /** The bag button, the inventory panel and short notices. */
    private fun drawBagAndNotice(world: WorldSim, data: Assets) {
        val density = Gdx.graphics.density
        val width = Gdx.graphics.width.toFloat()
        val height = Gdx.graphics.height.toFloat()
        val button = floatArrayOf(12f * density, 74f * density, 96f * density, 34f * density)
        bagRect = button
        val items = world.inventory.entries.toList()
        val rowH = font.lineHeight * 1.5f
        val panelW = min(width - 40f, 420f * density)
        val panelH = 56f * density + rowH * max(items.size, 1)
        val panelX = (width - panelW) / 2f
        val panelY = (height - panelH) / 2f

        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        shapes.color = Color(0.04f, 0.12f, 0.23f, 0.8f)
        shapes.rect(button[0], button[1], button[2], button[3])
        if (showInventory) {
            shapes.color = Color(0.04f, 0.12f, 0.23f, 0.95f)
            shapes.rect(panelX, panelY, panelW, panelH)
            shapes.color = Color(0.435f, 0.89f, 1f, 1f)
            shapes.rect(panelX, panelY, panelW, 3f * density)
        }
        shapes.end()

        batch.projectionMatrix = camera.combined
        batch.begin()
        font.color = Color.WHITE
        font.draw(batch, data.pack.text(language, "\$i18n:ui.bag_hint"), button[0] + 8f * density, button[1] + (button[3] - font.lineHeight) / 2f)
        if (showInventory) {
            font.color = Color(1f, 0.84f, 0.47f, 1f)
            font.draw(batch, data.pack.text(language, "\$i18n:ui.inventory"), panelX + 16f * density, panelY + 14f * density)
            var ty = panelY + 14f * density + rowH + 6f * density
            font.color = Color(0.92f, 0.96f, 1f, 1f)
            if (items.isEmpty()) font.draw(batch, data.pack.text(language, "\$i18n:ui.empty_bag"), panelX + 16f * density, ty)
            for ((itemId, quantity) in items) {
                // "base:item/slime_gel" -> text key "item.slime_gel.name"
                val key = itemId.substringAfter(':').replace('/', '.')
                val name = data.pack.text(language, "\$i18n:$key.name", mapOf("count" to quantity))
                font.draw(batch, "$name  x$quantity", panelX + 16f * density, ty)
                ty += rowH
            }
        }
        if (messageFrames > 0 && message.isNotEmpty()) {
            font.color = Color.WHITE
            font.draw(batch, message, 12f * density, height - 40f * density)
        }
        font.color = Color.WHITE
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
        private const val AUTOSAVE_SECONDS = 30f
    }
}
