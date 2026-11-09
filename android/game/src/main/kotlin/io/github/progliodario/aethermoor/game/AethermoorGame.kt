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
import io.github.progliodario.aethermoor.core.MAP_CELL
import io.github.progliodario.aethermoor.core.Pack
import io.github.progliodario.aethermoor.core.WorldParams
import io.github.progliodario.aethermoor.core.biomeCode
import io.github.progliodario.aethermoor.core.biomeCodeAt
import io.github.progliodario.aethermoor.core.regionAt
import io.github.progliodario.aethermoor.core.settlementContaining
import io.github.progliodario.aethermoor.core.audio.MusicContext
import io.github.progliodario.aethermoor.core.audio.MusicDirector
import io.github.progliodario.aethermoor.core.audio.PanelsOpen
import io.github.progliodario.aethermoor.core.audio.PlayerSound
import io.github.progliodario.aethermoor.core.audio.SoundCue
import io.github.progliodario.aethermoor.core.audio.SoundDirector
import io.github.progliodario.aethermoor.core.audio.SoundSnapshot
import io.github.progliodario.aethermoor.core.audio.ambienceGains
import io.github.progliodario.aethermoor.core.settlementMarker
import io.github.progliodario.aethermoor.core.worldEnemyIds
import io.github.progliodario.aethermoor.core.loadPack
import io.github.progliodario.aethermoor.core.parseProtagonist
import io.github.progliodario.aethermoor.core.loadWorldParams
import io.github.progliodario.aethermoor.core.sim.AttackPhase
import io.github.progliodario.aethermoor.core.sim.Enemy
import io.github.progliodario.aethermoor.core.sim.EnemyState
import io.github.progliodario.aethermoor.core.sim.NpcDef
import io.github.progliodario.aethermoor.core.sim.Prop
import io.github.progliodario.aethermoor.core.sim.QuestStage
import io.github.progliodario.aethermoor.core.sim.SaveMeta
import io.github.progliodario.aethermoor.core.sim.StreamConfig
import io.github.progliodario.aethermoor.core.sim.saveFromJson
import io.github.progliodario.aethermoor.core.sim.saveToJson
import io.github.progliodario.aethermoor.core.sim.TICK_DT
import io.github.progliodario.aethermoor.core.sim.TileMap
import io.github.progliodario.aethermoor.core.sim.Tileset
import io.github.progliodario.aethermoor.core.sim.ObjectiveKind
import io.github.progliodario.aethermoor.core.sim.WorldSim
import io.github.progliodario.aethermoor.core.sim.loadCombatSetup
import io.github.progliodario.aethermoor.core.sim.questFromOffer
import io.github.progliodario.aethermoor.core.sim.makeStreamMap
import io.github.progliodario.aethermoor.core.sim.parseTileset
import io.github.progliodario.aethermoor.core.sim.savePeek
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
import kotlin.math.sin
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

/**
 * Client: a vector-art character exploring the generated world, fighting and talking, drawn with libGDX.
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
        val worldParams: WorldParams,
    )

    private class SlotSummary(val used: Boolean, val level: Int, val gold: Long)

    private class FloatingText(val x: Float, val y: Float, val text: String, val onPlayer: Boolean, val crit: Boolean) {
        var age = 0
    }

    private lateinit var batch: SpriteBatch
    private lateinit var shapes: ShapeRenderer
    private lateinit var font: BitmapFont
    private val sound = SoundBoard()
    private val soundDirector = SoundDirector()
    private var musicDirector: MusicDirector? = null
    private var place = "wild"
    private var placeFrame = -1000L
    private var soundFrame = 0L
    private var dialogueLines = 0L
    private var lastLine = ""
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
    private var lastArgs: Map<String, String> = emptyMap()
    private var showInventory = false
    private var shopCursor = 0
    private var shopSell = false
    private var shopRowRects: List<FloatArray> = emptyList()
    private var shopBuyTab: FloatArray? = null
    private var shopSellTab: FloatArray? = null
    private var boardCursor = 0
    private var travelCursor = 0
    private var travelRowRects: List<FloatArray> = emptyList()
    private var boardRowRects: List<FloatArray> = emptyList()
    private var bagCursor = 0
    private var bagRowRects: List<FloatArray> = emptyList()
    private var bagRect: FloatArray? = null
    private var showMap = false
    private var showJournal = false
    private var showCraft = false // the crafting panel (spec 06, "Crafting")
    private var craftCursor = 0
    private var craftPanel: FloatArray? = null
    private var craftRowRects: List<FloatArray> = emptyList()
    private var craftRect: FloatArray? = null
    private var journalScroll = 0
    private var journalRect: FloatArray? = null
    private var journalPanel: FloatArray? = null
    private var languageRect: FloatArray? = null
    private var soundRect: FloatArray? = null
    private val volumes = intArrayOf(1000, 800, 500, 500) // master, effects, ambience, music in permille (spec 16, "Settings")
    private var mapRect: FloatArray? = null
    private var protagonistId = PROTAGONIST_ID // who is played in this game (spec 18), kept in the folder of the slot
    private var playerVariant: String? = null // palette variant of the player's art
    private var hasAnalyze = true // the protagonist has Ren's Analyze
    private var chooserSlot = 0 // the game being started on the screen where a protagonist is chosen, 0: not choosing
    private var chooserCursor = 0
    private var chooserIds: List<String> = emptyList()
    private var chooserRowRects: List<FloatArray> = emptyList()
    private var analyzeFrames = 0 // frames left of the Analyze panel (Z or its button), 0: hidden
    private var analyzeRect: FloatArray? = null
    private var showMinimap = true // N shows or hides the small map in the corner; a tap on it opens the world map
    private var miniRect: FloatArray? = null
    private var miniCodes = ByteArray(0) // biome codes of the sampled tiles around the player, -1 where unexplored
    private var miniOx = 0
    private var miniOy = 0
    private var mapPick = -1 // the place the view last jumped to (Next), in order of distance
    private var lastRegion = -1 // the region the player was in, to say the name when it changes
    private var hasGoal = false // a place of the world marked on the map (not saved); the HUD shows its direction and distance
    private var goalX = 0f // in tiles
    private var goalY = 0f
    private var mapLevel = -1 // the zoom of the world map; -1: frame what was explored when it is drawn next (spec 09, "The map view")
    private var mapCx = 0f // the map cell at the center of the view
    private var mapCy = 0f
    private var mapCellPx = 1f // pixels per cell as drawn (to turn a drag into cells)
    private var mapViewCells = 1f // cells across the view as drawn (the size of a key step)
    private var mapPinch = 0f // distance between two fingers, 0 when not pinching
    private var mapTouchOnButton = false
    private var mapButtons: List<MapButton> = emptyList()
    private val mapCodes = HashMap<Pair<Int, Int>, Int>()
    private val mapDetail = HashMap<Triple<Int, Int, Int>, ByteArray>() // biome codes of the sampled tiles of a cell (x, y, n): n x n, row by row
    private val mapMarkers = HashMap<Pair<Int, Int>, io.github.progliodario.aethermoor.core.Settlement?>()
    private var message = ""
    private var messageFrames = 0
    private var sinceAutosave = 0f
    private var seed = 0uL
    private var currentSlot = 0

    /** The games on the title screen (spec 12, "Slots"); null once a game is running. */
    private var titleSlots: List<SlotSummary>? = null
    private var titleCursor = 0
    private var titlePendingDelete = -1
    private var titleNotice = ""
    private var titleRowRects: List<FloatArray> = emptyList()
    private var titleCrossRects: List<FloatArray> = emptyList()

    override fun create() {
        batch = SpriteBatch()
        shapes = ShapeRenderer()
        font = BitmapFont(true) // flipped: the projection has y pointing down
        font.data.setScale(max(1f, Gdx.graphics.density * 0.9f))
        camera = OrthographicCamera()
        language = savedLanguage() ?: if (Locale.getDefault().language == "it") "it" else "en"

        val loaded = loadAssets() ?: return
        assets = loaded
        cache = TextureCache(loaded.pack)
        sound.open(loaded.pack)
        loadVolumes()
        migrateLegacySaves()
        titleSlots = readSlots()
        Gdx.input.setCatchKey(Input.Keys.BACK, true) // Back leaves a game for the title screen (spec 12, "Slots")
    }

    /** Saves the game and goes back to the title screen; the world is built again when a game is chosen. */
    private fun returnToTitle() {
        sim?.let { saveGame(it) }
        sim = null
        titleCursor = (currentSlot - 1).coerceIn(0, SLOT_COUNT - 1)
        titlePendingDelete = -1
        titleNotice = ""
        showInventory = false
        showMap = false
        showJournal = false
        showCraft = false
        accumulator = 0f
        sinceAutosave = 0f
        message = ""
        messageFrames = 0
        floating.clear()
        mapCodes.clear()
        mapDetail.clear()
        hasGoal = false
        lastRegion = -1
        miniCodes = ByteArray(0)
        mapMarkers.clear()
        titleSlots = readSlots()
    }

    /** Back (or Esc with no panel open) comes out of a game; with a panel open, Back closes it. Returns true when the game was left. */
    private fun handleBack(world: WorldSim): Boolean {
        val back = Gdx.input.isKeyJustPressed(Input.Keys.BACK)
        val escape = Gdx.input.isKeyJustPressed(Input.Keys.ESCAPE)
        if (!back && !escape) return false
        val panelOpen = showInventory || showMap || showJournal || showCraft || world.shop != null || world.board != null || world.travel != null
        if (panelOpen) {
            if (back) {
                showInventory = false
                showMap = false
                showJournal = false
                showCraft = false
                world.closeShop()
                world.closeBoard()
                world.closeTravel()
            }
            return false // Esc is handled by the panel itself
        }
        returnToTitle()
        return true
    }

    /** Builds the world of a game (spec 12, "Slots") and continues its autosave. */
    private fun startGame(slot: Int) {
        val loaded = assets ?: return
        currentSlot = slot
        protagonistId = keptProtagonist(slot) ?: PROTAGONIST_ID
        val protagonistDef = loaded.pack.readDocument(protagonistId)?.let { parseProtagonist(it).getOrNull() }
        playerVariant = protagonistDef?.artVariant?.ifEmpty { null }
        hasAnalyze = protagonistDef?.startingSkills?.contains("base:skill/ren/analyze") ?: true
        loadGoal() // the goal marked in this game
        titleSlots = null
        seed = chooseSeed()
        val combat = loadCombatSetup(loaded.pack, loaded.map, protagonistId, seed, worldEnemyIds(loaded.worldParams), loaded.worldParams.enemyHpPct, loaded.worldParams.enemyAtkPct)
            .getOrElse {
                error = it.message
                Gdx.app.error(TAG, "Cannot build the combat setup: ${it.message}")
                return
            }
        val world = WorldSim(loaded.map, loaded.tileset, 0f, combat, StreamConfig(loaded.worldParams, seed))
        sim = world
        loadAutosave(world, loaded.pack)
    }

    /** The seed of the last session of this game on the generated world (so the same world comes back), else a new one. */
    private fun chooseSeed(): ULong {
        val file = saveFile()
        if (file.exists()) {
            val peek = savePeek(file.readString("UTF-8")).getOrNull()
            if (peek != null && peek.map == MAP_WORLD) return peek.seed
        }
        return System.nanoTime().toULong()
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
            val worldParams = loadWorldParams(pack, "base:world/overworld").getOrThrow()
            Assets(
                pack = pack,
                rig = parseRig(doc("base:art/rig/humanoid")).getOrThrow(),
                idle = parseClip(doc("base:art/clip/humanoid_idle")).getOrThrow(),
                walk = parseClip(doc("base:art/clip/humanoid_walk")).getOrThrow(),
                map = makeStreamMap(worldParams),
                tileset = parseTileset(doc("base:tileset/overworld")).getOrThrow(),
                worldParams = worldParams,
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

    private fun saveFile() = slotFile(currentSlot)

    private fun slotFile(slot: Int) = Gdx.files.local("saves/slot$slot/auto.json")

    /** The goal is kept with the game: a file `goal.txt` ("x y" in tiles) in the folder of the slot, removed when the goal is. */
    private fun goalFile() = Gdx.files.local("saves/slot$currentSlot/goal.txt")

    private fun saveGoal() {
        runCatching {
            if (hasGoal) goalFile().writeString("${goalX.toLong()} ${goalY.toLong()}\n", false) else goalFile().delete()
        }
    }

    private fun loadGoal() {
        hasGoal = false
        runCatching {
            val file = goalFile()
            if (file.exists()) {
                val parts = file.readString().trim().split(' ')
                if (parts.size == 2) {
                    goalX = parts[0].toLong().toFloat()
                    goalY = parts[1].toLong().toFloat()
                    hasGoal = true
                }
            }
        }
    }

    /** Saves written before slots existed become the first game. */
    private fun migrateLegacySaves() {
        try {
            val legacy = Gdx.files.local("saves/auto.json")
            if (!legacy.exists() || slotFile(1).exists()) return
            slotFile(1).parent().mkdirs()
            legacy.moveTo(slotFile(1))
            val quick = Gdx.files.local("saves/quick.json")
            if (quick.exists()) quick.moveTo(Gdx.files.local("saves/slot1/quick.json"))
        } catch (e: com.badlogic.gdx.utils.GdxRuntimeException) {
            Gdx.app.error(TAG, "Cannot move the old save: ${e.message}")
        }
    }

    /** What the title screen shows of each game: read from the autosave without building the world. */
    private fun readSlots(): List<SlotSummary> =
        (1..SLOT_COUNT).map { slot ->
            val peek = try {
                val file = slotFile(slot)
                if (file.exists()) savePeek(file.readString("UTF-8")).getOrNull() else null
            } catch (e: com.badlogic.gdx.utils.GdxRuntimeException) {
                null
            }
            if (peek == null) SlotSummary(false, 1, 0L) else SlotSummary(true, peek.level, peek.gold)
        }

    private fun deleteSlot(slot: Int) {
        try {
            for (name in listOf("auto.json", "auto.json.tmp", "quick.json", "quick.json.tmp")) {
                val file = Gdx.files.local("saves/slot$slot/$name")
                if (file.exists()) file.delete()
            }
        } catch (e: com.badlogic.gdx.utils.GdxRuntimeException) {
            Gdx.app.error(TAG, "Cannot delete the game: ${e.message}")
        }
    }

    /** Writes the autosave (a temporary file first, then a move over the old save). */
    private fun saveGame(world: WorldSim) {
        try {
            val temp = Gdx.files.local("saves/slot$currentSlot/auto.json.tmp")
            temp.writeString(saveToJson(world.capture(), SaveMeta(info.version, 1, protagonistId, seed, MAP_WORLD)), false, "UTF-8")
            temp.moveTo(saveFile())
        } catch (e: com.badlogic.gdx.utils.GdxRuntimeException) {
            Gdx.app.error(TAG, "Cannot write the save: ${e.message}")
        }
    }

    private fun loadAutosave(world: WorldSim, pack: Pack) {
        val file = saveFile()
        if (!file.exists()) return
        val text = file.readString("UTF-8")
        val peek = savePeek(text).getOrNull()
        if (peek == null || peek.map != MAP_WORLD || peek.seed != seed) return // another map: start a fresh run
        val result = saveFromJson(text).mapCatching { world.restore(it).getOrThrow() }
        if (result.isSuccess) {
            showNotice(pack.text(language, "\$i18n:ui.loaded"))
        } else {
            Gdx.app.error(TAG, "Cannot load the save: ${result.exceptionOrNull()?.message}")
        }
    }

    // ------------------------------------------------------------------------------------ settings

    private fun settingsFile() = Gdx.files.local("settings.json")

    /** The language the player chose (spec 16), if any. */
    private fun savedLanguage(): String? =
        try {
            val file = settingsFile()
            val text = if (file.exists()) file.readString("UTF-8") else ""
            when {
                !text.contains("\"language\"") -> null
                text.contains("\"it\"") -> "it"
                text.contains("\"en\"") -> "en"
                else -> null
            }
        } catch (e: com.badlogic.gdx.utils.GdxRuntimeException) {
            null
        }

    private val volumeKeys = arrayOf("volume_master_pm", "volume_effects_pm", "volume_ambience_pm", "volume_music_pm")

    /** Reads the volumes of the settings file (the defaults stay for what is missing) and gives them to the sound board. */
    private fun loadVolumes() {
        try {
            val file = settingsFile()
            val text = if (file.exists()) file.readString("UTF-8") else ""
            for ((i, key) in volumeKeys.withIndex()) {
                Regex("\"$key\"\\s*:\\s*(\\d+)").find(text)?.groupValues?.get(1)?.toIntOrNull()?.let { volumes[i] = it.coerceIn(0, 1000) }
            }
        } catch (e: com.badlogic.gdx.utils.GdxRuntimeException) {
            Gdx.app.error(TAG, "Cannot read the settings: ${e.message}")
        }
        sound.setVolumes(volumes[0], volumes[1], volumes[2], volumes[3])
    }

    /** Writes the language and the volumes to the settings file. */
    private fun writeSettings() {
        try {
            val volumeText = volumeKeys.indices.joinToString(",\n") { "  \"${volumeKeys[it]}\": ${volumes[it]}" }
            settingsFile().writeString("{\n  \"language\": \"$language\",\n$volumeText\n}\n", false, "UTF-8")
        } catch (e: com.badlogic.gdx.utils.GdxRuntimeException) {
            Gdx.app.error(TAG, "Cannot write the settings: ${e.message}")
        }
    }

    /** The sound button: the whole volume goes 100, 60, 30, 0 percent and round again. */
    private fun cycleVolume() {
        volumes[0] = when {
            volumes[0] > 600 -> 600
            volumes[0] > 300 -> 300
            volumes[0] > 0 -> 0
            else -> 1000
        }
        sound.setVolumes(volumes[0], volumes[1], volumes[2], volumes[3])
        writeSettings()
        sound.playEvent("pickup")
    }

    private fun toggleLanguage(data: Assets) {
        language = if (language == "it") "en" else "it"
        writeSettings()
        showNotice(data.pack.text(language, "\$i18n:ui.language_set"))
    }

    /** Uses the item under the bag cursor (spec 06) and tells what happened. */
    private fun useSelectedItem(world: WorldSim) {
        val pack = assets?.pack ?: return
        val items = world.inventory.keys.toList()
        if (items.isEmpty()) return
        val itemId = items[bagCursor.coerceIn(0, items.size - 1)]
        val name = pack.text(language, "\$i18n:${itemId.substringAfter(':').replace('/', '.')}.name", mapOf("count" to 1L))
        val kind = world.combat.items[itemId]?.kind
        if ((kind == "weapon" || kind == "armor") && world.equip(itemId)) {
            showNotice(pack.text(language, "\$i18n:ui.item_equipped", mapOf("item" to name)))
        } else if (kind != "weapon" && kind != "armor" && world.useItem(itemId)) {
            showNotice(pack.text(language, "\$i18n:ui.item_used", mapOf("item" to name)))
            bagCursor = bagCursor.coerceIn(0, max(world.inventory.size - 1, 0))
        } else {
            showNotice(pack.text(language, "\$i18n:ui.item_unchanged"))
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
        val slots = titleSlots
        if (world == null && data != null && slots != null) {
            // the title and the chooser have the music of the title and no ambience
            sound.musicRules?.let { sound.setMusic(it.title, listOf("base")) }
            sound.setAmbience(emptyMap())
            sound.frame()
            if (chooserSlot > 0) {
                handleChooserInput(data)
                if (chooserSlot > 0) drawChooser(data)
                return
            }
            if (Gdx.input.isKeyJustPressed(Input.Keys.BACK) || Gdx.input.isKeyJustPressed(Input.Keys.ESCAPE)) {
                Gdx.app.exit() // Back on the title screen closes the game
                return
            }
            handleTitleInput(data, slots)
            titleSlots?.let { drawTitle(data, it) } // null when a game was just chosen
            return
        }
        if (world == null || data == null) {
            drawError()
            return
        }

        if (handleBack(world)) return
        handleStoryInput(world)
        val frame = input.read()
        if (showInventory || showMap || showJournal || showCraft || world.shop != null || world.board != null || world.travel != null) {
            accumulator = 0f // the bag, the map, the journal, the shop, the board and the stones pause the game
        } else {
            accumulator += min(Gdx.graphics.deltaTime, MAX_FRAME_SECONDS)
            var ticks = 0
            while (accumulator >= TICK_DT && ticks < MAX_TICKS_PER_FRAME) {
                world.tick(frame.x, frame.y, frame.attack, frame.dodge, frame.strike, frame.parry)
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

        for (e in world.takeEvents()) {
            floating.add(FloatingText(e.position.x, e.position.y, e.amount.toString() + if (e.weak) "!" else "", e.onPlayer, e.crit))
        }
        playChangeSounds(world)
        floating.forEach { it.age++ }
        floating.removeAll { it.age > FLOATING_TEXT_FRAMES }

        val tilePx = max(16, (BASE_TILE_PX * Gdx.graphics.density).roundToInt())
        cache.releaseOtherBuckets(tilePx)
        draw(world, data, tilePx)
    }

    /** The sounds: a snapshot of the game for the director (spec 14, "What plays when"). */
    private fun playChangeSounds(world: WorldSim) {
        val hero = world.player
        val view = world.story.dialogueView()
        if (view.active && !view.isChoice && view.text != lastLine) dialogueLines++
        lastLine = if (view.active) view.text else ""
        val ground = world.tileset.tiles[world.gidAt(floor(hero.position.x).toInt(), floor(hero.position.y).toInt())]
        val store = world.chunks
        val moment = world.time()
        val region = if (store != null) store.params.regions[regionAt(store.params, floor(hero.position.x).toInt(), floor(hero.position.y).toInt())].id else ""
        val snapshot = SoundSnapshot(
            frame = ++soundFrame,
            player = PlayerSound(
                hp = hero.hp, maxHp = world.derived.maxHp, level = hero.level,
                phase = if (hero.phase == AttackPhase.NONE) 0 else 1, strike = hero.usingStrike,
                dodge = hero.dodgeTicks > 0, moving = hero.moving,
                x = hero.position.x.toDouble(), y = hero.position.y.toDouble(),
                surface = ground?.surface ?: "grass", saveCd = hero.deathSaveCd.toLong(),
            ),
            cues = world.takeCues().map { SoundCue(it.kind, it.family, it.position.x.toDouble(), it.position.y.toDouble(), it.crit, it.weak) },
            items = world.inventory.values.sum(),
            gold = world.story.gold,
            mp = hero.mpU,
            weapon = world.equippedWeapon,
            armor = world.equippedArmor,
            panels = PanelsOpen(
                bag = showInventory, map = showMap, journal = showJournal || showCraft,
                shop = world.shop != null, board = world.board != null, travel = world.travel != null,
            ),
            dialogue = view.active,
            line = dialogueLines,
            cursor = (bagCursor + shopCursor + boardCursor + travelCursor + choiceIndex).toLong(),
            questsStarted = world.story.quests.size.toLong(),
            questsDone = world.story.quests.values.count { it.done }.toLong(),
            stones = world.stones.size.toLong(),
            region = region,
            todPm = moment?.todPm ?: 500,
            rainPm = moment?.rainPm ?: 0,
        )
        for (event in soundDirector.update(snapshot)) sound.playEvent(event.event, event.volumePm)
        sound.ambienceRules?.let { sound.setAmbience(ambienceGains(snapshot.region, snapshot.todPm, snapshot.rainPm, it)) }
        if (musicDirector == null) musicDirector = sound.musicRules?.let { MusicDirector(it) }
        musicDirector?.let { director ->
            // the music: the piece of the place, the hour and the quest, and its layers
            if (store != null && snapshot.frame - placeFrame >= 30) {
                placeFrame = snapshot.frame
                val here = settlementContaining(store.seed, store.params, floor(hero.position.x).toInt(), floor(hero.position.y).toInt())
                place = if (here == null) "wild" else if (here.kind == "dungeon") "dungeon" else "settlement"
            }
            val mood = MusicContext(
                frame = snapshot.frame,
                region = snapshot.region,
                todPm = snapshot.todPm,
                place = if (store != null) place else "wild",
                quests = world.story.quests.filterValues { !it.done }.keys.toList(),
                lowHp = hero.hp > 0 && hero.hp * 4 < world.derived.maxHp,
                cues = snapshot.cues,
                x = snapshot.player.x,
                y = snapshot.player.y,
            )
            val choice = director.update(mood)
            sound.setMusic(choice.piece, choice.layers)
        }
        sound.frame()
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
                val def = data.tileset.tiles[world.gidAt(tx, ty)] ?: continue
                val sprite = cache.get(def.art, tilePx) ?: continue
                val sx0 = ((tx - cam.x) * tile).roundToInt().toFloat()
                val sy0 = ((ty - cam.y) * tile).roundToInt().toFloat()
                val sx1 = ((tx + 1 - cam.x) * tile).roundToInt().toFloat()
                val sy1 = ((ty + 1 - cam.y) * tile).roundToInt().toFloat()
                batch.draw(sprite.region, sx0, sy0, sx1 - sx0, sy1 - sy0)
            }
        }

        // Props, enemies and the player, sorted by feet y (smaller first; ties keep list order, the player last).
        class Item(val feetY: Float, val prop: Prop?, val enemy: Enemy?, val npc: NpcDef? = null, val companion: Boolean = false)
        val items = ArrayList<Item>()
        world.forEachProp(cam.x - 2f, cam.y - 1f, cam.x + viewW + 2f, cam.y + viewH + 4f) { prop -> items.add(Item(prop.y, prop, null)) }
        for (enemy in world.enemies) if (enemy.state != EnemyState.DEAD) items.add(Item(enemy.position.y, null, enemy))
        for (npc in world.story.setup.npcs + world.story.dynamicNpcs) items.add(Item(npc.y, null, null, npc))
        items.add(Item(world.player.position.y, null, null))
        world.companionPosition?.let { items.add(Item(it.y, null, null, null, true)) }
        for (item in items.sortedBy { it.feetY }) {
            when {
                item.prop != null -> drawProp(item.prop, cam.x, cam.y, tilePx, tile, k)
                item.enemy != null -> drawEnemy(item.enemy, cam.x, cam.y, tilePx, tile, k)
                item.npc != null -> drawNpc(world, data, item.npc, cam.x, cam.y, tilePx, k)
                item.companion -> drawCompanion(world, cam.x, cam.y, tilePx, tile, k)
                else -> drawPlayer(world, data, cam.x, cam.y, tilePx, k)
            }
        }
        batch.end()

        drawAtmosphere(world)
        drawOverlays(world, cam.x, cam.y, tile, k)
        drawGoalArrow(world, cam.x, cam.y, tile)
        drawMinimap(world)
        drawTexts(world, data, cam.x, cam.y, tile)
        drawStory(world, data)
        drawDodgeButton(world, data)
        drawStrikeButton(world, data)
        drawParryButton(world, data)
        drawCraft(world, data)
        drawAnalyze(world, data)
        drawStick()
    }

    private fun drawProp(prop: Prop, camX: Float, camY: Float, tilePx: Int, tile: Float, k: Float) {
        val sprite = cache.get(prop.art, tilePx) ?: return
        val fx = (prop.x - camX) * tile
        val fy = (prop.y - camY) * tile
        batch.draw(sprite.region, fx - sprite.originX * k, fy - sprite.originY * k, sprite.width * k, sprite.height * k)
    }

    /** The companion (spec 10), drawn with the art of its creature, a little smaller, bobbing. */
    private fun drawCompanion(world: WorldSim, camX: Float, camY: Float, tilePx: Int, tile: Float, k: Float) {
        val def = world.combat.companion ?: return
        val at = world.companionPosition ?: return
        val sprite = cache.get(def.art, tilePx) ?: return
        val s = k * def.scalePct / 100f
        val bob = sin(System.currentTimeMillis() / 160f) * 2f * k
        val fx = (at.x - camX) * tile
        val fy = (at.y - camY) * tile + bob
        batch.draw(sprite.region, fx - sprite.originX * s, fy - sprite.originY * s, sprite.width * s, sprite.height * s)
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
            data, player.moving, player.facingLeft, player.clipTick, blink, playerVariant,
            (player.position.x - camX) * tile, (player.position.y - camY) * tile, tilePx, k,
        )
    }

    /** A dialogue text with its arguments (spec 07): values that start with "$i18n:" are text keys resolved with the plain ones. */
    private fun dialogueText(pack: Pack, reference: String, args: Map<String, String>): String {
        val plain = args.filterValues { !it.startsWith("\$i18n:") }
        val all = HashMap<String, Any>(plain)
        for ((key, value) in args) if (value.startsWith("\$i18n:")) all[key] = pack.text(language, value, plain)
        return pack.text(language, reference, all)
    }

    /** The name shown for a speaker: "npc" is the NPC being talked to, any other one has a text. */
    private fun speakerName(pack: Pack, speaker: String, args: Map<String, String>): String =
        if (speaker == "npc") args["npc"] ?: "" else pack.text(language, "\$i18n:speaker.$speaker")

    private fun drawNpc(world: WorldSim, data: Assets, npc: NpcDef, camX: Float, camY: Float, tilePx: Int, k: Float) {
        val tile = tilePx.toFloat()
        if (npc.name.isNotEmpty() && npc === world.story.npcInRange()) {
            layout.setText(font, npc.name)
            font.color = Color(1f, 0.84f, 0.47f, 1f)
            font.draw(batch, npc.name, (npc.x - camX) * tile - layout.width / 2f, (npc.y - camY) * tile - 2.4f * tile)
            font.color = Color.WHITE
        }
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
    /** Night and weather over the world (spec 08). Presentation only. */
    private fun drawAtmosphere(world: WorldSim) {
        val time = world.time() ?: return
        val w = Gdx.graphics.width.toFloat()
        val h = Gdx.graphics.height.toFloat()
        val dark = 1000 - time.effectiveLightPm
        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        Gdx.gl.glBlendFunc(GL20.GL_SRC_ALPHA, GL20.GL_ONE_MINUS_SRC_ALPHA)
        if (dark > 0) {
            shapes.begin(ShapeRenderer.ShapeType.Filled)
            shapes.color = Color(0.03f, 0.055f, 0.17f, dark * 0.69f / 1000f)
            shapes.rect(0f, 0f, w, h)
            shapes.end()
        }
        val params = world.chunks?.params
        if (params != null && time.seasonIndex >= 0) { // the tint of the season (spec 08)
            val tint = params.time.seasons[time.seasonIndex].tint
            if (tint[3] > 0) {
                shapes.begin(ShapeRenderer.ShapeType.Filled)
                shapes.color = Color(tint[0] / 255f, tint[1] / 255f, tint[2] / 255f, tint[3] / 255f)
                shapes.rect(0f, 0f, w, h)
                shapes.end()
            }
        }
        if (time.rainPm > 0) {
            val density = Gdx.graphics.density
            val now = System.currentTimeMillis()
            val drops = 160 * time.rainPm / 1000
            shapes.begin(ShapeRenderer.ShapeType.Line)
            shapes.color = Color(0.67f, 0.745f, 0.9f, 0.6f)
            for (i in 0 until drops) {
                val x = ((i * 7919L + now / 5) % w.toLong()).toFloat()
                val y = ((now / 2 + i * 977L) % h.toLong()).toFloat()
                shapes.line(x, y, x - 3f * density, y + 12f * density)
            }
            shapes.end()
        }
    }


    /** A panel with a soft shadow, a border in the accent color, a body that fades from lighter to darker, a light line under the top edge and a stripe of the accent color on top. Call it inside a Filled batch. */
    private fun drawPanel(x: Float, y: Float, w: Float, h: Float, accent: Color, alpha: Float) {
        val density = Gdx.graphics.density
        shapes.color = Color(0f, 0f, 0f, 0.35f)
        shapes.rect(x + 3f * density, y + 4f * density, w, h)
        shapes.color = Color(0.016f, 0.04f, 0.094f, 1f)
        shapes.rect(x - 2f * density, y - 2f * density, w + 4f * density, h + 4f * density)
        shapes.color = Color(accent.r / 2f, accent.g / 2f, accent.b / 2f, 1f)
        shapes.rect(x - density, y - density, w + 2f * density, h + 2f * density)
        val strips = maxOf(1, (h / (4f * density)).toInt())
        for (i in 0 until strips) {
            val t = i.toFloat() / strips.toFloat()
            shapes.color = Color(0.086f + (0.031f - 0.086f) * t, 0.188f + (0.078f - 0.188f) * t, 0.345f + (0.172f - 0.345f) * t, alpha)
            shapes.rect(x, y + h * t, w, h / strips + 0.5f)
        }
        shapes.color = Color(1f, 1f, 1f, 0.16f)
        shapes.rect(x, y + 3f * density, w, density)
        shapes.color = accent
        shapes.rect(x, y, w, 3f * density)
        shapes.color = Color(accent.r / 2f + 0.16f, accent.g / 2f + 0.16f, accent.b / 2f + 0.16f, 0.8f)
        for (cx in floatArrayOf(x + 5f * density, x + w - 8f * density)) {
            for (cy in floatArrayOf(y + 6f * density, y + h - 9f * density)) shapes.rect(cx, cy, 3f * density, 3f * density)
        }
    }

    /** A bar with a dark frame, a fill that is lighter on the top half and darker on the bottom, a gloss line and ticks. Call it inside a Filled batch. */
    private fun drawBar(x: Float, y: Float, w: Float, h: Float, ratio: Float, color: Color) {
        shapes.color = Color(0.016f, 0.04f, 0.094f, 0.92f)
        shapes.rect(x - 2f, y - 2f, w + 4f, h + 4f)
        shapes.color = Color(0.27f, 0.35f, 0.47f, 0.8f)
        shapes.rect(x - 1f, y - 1f, w + 2f, h + 2f)
        shapes.color = Color(0.047f, 0.086f, 0.157f, 1f)
        shapes.rect(x, y, w, h)
        val fw = w * ratio.coerceIn(0f, 1f)
        if (fw > 0f) {
            shapes.color = Color((color.r + 0.16f).coerceAtMost(1f), (color.g + 0.16f).coerceAtMost(1f), (color.b + 0.16f).coerceAtMost(1f), 1f)
            shapes.rect(x, y, fw, h * 0.55f)
            shapes.color = Color((color.r - 0.18f).coerceAtLeast(0f), (color.g - 0.18f).coerceAtLeast(0f), (color.b - 0.18f).coerceAtLeast(0f), 1f)
            shapes.rect(x, y + h * 0.55f, fw, h * 0.45f)
            shapes.color = Color(1f, 1f, 1f, 0.27f)
            shapes.rect(x, y + 1f, fw, maxOf(1f, h * 0.14f))
            shapes.color = Color(1f, 1f, 1f, 0.35f)
            shapes.rect(x + fw - 1f, y, 1f, h)
        }
        shapes.color = Color(0f, 0f, 0f, 0.27f)
        for (i in 1..9) shapes.rect(x + w * i / 10f, y + h * 0.7f, 1f, h * 0.3f)
    }

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
            // The stagger bar (spec 05, "Stagger") under the health: yellow while it fills, white and emptying while the creature is broken.
            val need = max(1L, enemy.def.hp * enemy.def.staggerPct / 100)
            val stagger = if (enemy.broken > 0) enemy.broken / 120f else enemy.stagger.toFloat() / need.toFloat()
            if (enemy.def.staggerPct > 0 && stagger > 0f) {
                shapes.color = Color(0.08f, 0.08f, 0.08f, 0.8f)
                shapes.rect(fx - barW / 2f, fy + 2.5f * k, barW, 1f * k)
                shapes.color = if (enemy.broken > 0) Color.WHITE else Color(1f, 0.82f, 0.31f, 1f)
                shapes.rect(fx - barW / 2f, fy + 2.5f * k, barW * minOf(stagger, 1f), 1f * k)
            }
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
        val mpRatio = (world.mp.toFloat() / maxOf(world.derived.maxMp, 1L).toFloat()).coerceIn(0f, 1f)
        val below = 10f * density // the mana bar sits between the health bar and the experience bar
        drawBar(x, y + barH + 4f, barW, 7f * density, mpRatio, Color(0.31f, 0.55f, 1f, 1f))
        drawBar(x, y, barW, barH, hpRatio, Color(0.82f, 0.24f, 0.24f, 1f))
        drawBar(x, y + barH + 6f + below, barW, 6f * density, xpRatio, Color(0.35f, 0.78f, 0.47f, 1f))
        // The two abilities next to the bars: a square that fills while the cooldown runs and is lit when the ability is ready
        // (green: the dodge roll, blue: the power strike, which also needs enough mana).
        val pip = 15f * density
        var pipX = x + barW + 8f * density
        fun drawPip(ready: Float, lit: Boolean, color: Color) {
            shapes.color = Color(0.04f, 0.08f, 0.16f, 0.85f)
            shapes.rect(pipX - 1f, y - 1f, pip + 2f, pip + 2f)
            val filled = ready.coerceIn(0f, 1f)
            shapes.color = if (lit) color else Color(0.35f, 0.39f, 0.47f, 1f)
            shapes.rect(pipX, y + pip * (1f - filled), pip, pip * filled)
            pipX += pip + 6f * density
        }
        val combatSetup = world.combat
        if (combatSetup.dodge.enabled) drawPip(1f - p.dodgeCooldown.toFloat() / maxOf(combatSetup.dodge.cooldown, 1), p.dodgeCooldown == 0, Color(0.35f, 0.86f, 0.47f, 1f))
        if (combatSetup.gift.deathSaveTicks > 0) { // the Eternal Aegis: lit when the death save is ready
            drawPip(1f - p.deathSaveCd.toFloat() / combatSetup.gift.deathSaveTicks, p.deathSaveCd == 0, Color(1f, 0.84f, 0.35f, 1f))
        }
        if (combatSetup.strike.enabled) {
            val strikeCooldown = combatSetup.strike.skill.cooldown
            drawPip(1f - minOf(p.cooldown, strikeCooldown).toFloat() / maxOf(strikeCooldown, 1), p.cooldown == 0 && world.mp >= combatSetup.strike.mp, Color(0.39f, 0.63f, 1f, 1f))
        }
        shapes.end()
    }

    /** The name of the season of the time sample (spec 08), empty without seasons. */
    private fun seasonName(world: WorldSim, time: io.github.progliodario.aethermoor.core.TimeSample): String {
        val params = world.chunks?.params ?: return ""
        if (time.seasonIndex < 0) return ""
        return assets?.pack?.text(language, "\$i18n:season.${params.time.seasons[time.seasonIndex].id}") ?: ""
    }

    private fun drawTexts(world: WorldSim, data: Assets, camX: Float, camY: Float, tile: Float) {
        batch.projectionMatrix = camera.combined
        batch.begin()
        val density = Gdx.graphics.density
        val p = world.player
        font.color = Color.WHITE
        font.draw(batch, "${data.pack.text(language, "\$i18n:ui.hp")} ${p.hp}/${world.derived.maxHp}", 12f * density + 4f, 12f * density + 2f)
        font.draw(batch, data.pack.text(language, "\$i18n:ui.level", mapOf("level" to p.level)), 12f * density, 12f * density + 16f * density + 20f + 10f * density)
        // The status effects on the player (spec 05), one word each, under the level.
        val status = listOf(p.burn to "burn", p.chill to "chill", p.stun to "stun", p.weaken to "weaken")
            .filter { it.first > 0 }.joinToString("  ") { data.pack.text(language, "\$i18n:ui.status_${it.second}") }
        if (status.isNotEmpty()) {
            font.color = Color(1f, 0.59f, 0.35f, 1f)
            font.draw(batch, status, 12f * density, 12f * density + 16f * density + 20f + 10f * density + font.lineHeight * 1.2f)
            font.color = Color.WHITE
        }
        world.time()?.let { time ->
            val hour = time.todPm * 24 / 1000
            val minute = time.todPm * 1440 / 1000 % 60
            val clock = data.pack.text(
                language, "\$i18n:ui.clock",
                mapOf("day" to time.day, "time" to "%02d:%02d".format(hour, minute), "season" to seasonName(world, time)),
            )
            layout.setText(font, clock)
            hudText(clock, Gdx.graphics.width - layout.width - 12f * density, 12f * density + 2f)
            world.chunks?.let { store ->
                val regionIndex = regionAt(store.params, floor(p.position.x).toInt(), floor(p.position.y).toInt())
                val name = data.pack.text(language, store.params.regions[regionIndex].name)
                if (lastRegion >= 0 && regionIndex != lastRegion) showNotice(data.pack.text(language, "\$i18n:ui.region_enter", mapOf("region" to name)))
                lastRegion = regionIndex
                font.color = Color(1f, 0.84f, 0.47f, 1f)
                layout.setText(font, name)
                hudText(name, Gdx.graphics.width - layout.width - 12f * density, 12f * density + 2f + font.lineHeight * 1.2f)
                font.color = Color.WHITE
            }
        }
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

    /** What the open shop lists: (item id, price), what it sells or what the player can sell (spec 06). */
    private fun shopEntries(world: WorldSim): List<Pair<String, Long>> {
        val shop = world.shop ?: return emptyList()
        return if (!shopSell) {
            shop.stock.map { Pair(it, world.buyPrice(it)) }
        } else {
            world.inventory.keys.filter { world.sellPrice(it) > 0L }.map { Pair(it, world.sellPrice(it)) }
        }
    }

    private fun shopConfirm(world: WorldSim) {
        val pack = assets?.pack ?: return
        val entries = shopEntries(world)
        if (entries.isEmpty()) return
        val itemId = entries[shopCursor.coerceIn(0, entries.size - 1)].first
        val name = pack.text(language, "\$i18n:${itemId.substringAfter(':').replace('/', '.')}.name", mapOf("count" to 1L))
        val done = if (shopSell) world.sell(itemId) else world.buy(itemId)
        if (done) {
            showNotice(pack.text(language, if (shopSell) "\$i18n:ui.sold" else "\$i18n:ui.bought", mapOf("item" to name)))
            shopCursor = shopCursor.coerceIn(0, max(shopEntries(world).size - 1, 0))
        } else {
            showNotice(pack.text(language, "\$i18n:ui.cannot_do"))
        }
    }

    private fun handleShopInput(world: WorldSim) {
        val input = Gdx.input
        val count = shopEntries(world).size
        if (input.isKeyJustPressed(Input.Keys.ESCAPE)) {
            world.closeShop()
        } else if (input.isKeyJustPressed(Input.Keys.UP) || input.isKeyJustPressed(Input.Keys.W)) {
            if (count > 0) shopCursor = (shopCursor.coerceIn(0, count - 1) + count - 1) % count
        } else if (input.isKeyJustPressed(Input.Keys.DOWN) || input.isKeyJustPressed(Input.Keys.S)) {
            if (count > 0) shopCursor = (shopCursor.coerceIn(0, count - 1) + 1) % count
        } else if (input.isKeyJustPressed(Input.Keys.TAB)) {
            shopSell = !shopSell
            shopCursor = 0
        } else if (input.isKeyJustPressed(Input.Keys.E) || input.isKeyJustPressed(Input.Keys.ENTER) || input.isKeyJustPressed(Input.Keys.SPACE)) {
            shopConfirm(world)
        } else if (input.justTouched()) {
            // The tabs switch between buying and selling; a row is selected by a tap and confirmed by a second one; elsewhere closes.
            val x = input.x.toFloat()
            val y = input.y.toFloat()
            fun hit(r: FloatArray?) = r != null && x >= r[0] && x <= r[0] + r[2] && y >= r[1] && y <= r[1] + r[3]
            val row = shopRowRects.indexOfFirst { hit(it) }
            if (hit(shopBuyTab)) {
                shopSell = false
                shopCursor = 0
            } else if (hit(shopSellTab)) {
                shopSell = true
                shopCursor = 0
            } else if (row < 0) {
                world.closeShop()
            } else if (row == shopCursor) {
                shopConfirm(world)
            } else {
                shopCursor = row
            }
        }
    }

    /** The guild board (spec 07, "Guild"): the slot under the cursor is accepted or refused with a notice. */
    private fun boardConfirm(world: WorldSim) {
        val pack = assets?.pack ?: return
        val board = world.board ?: return
        if (board.offers.isEmpty()) return
        val slot = boardCursor.coerceIn(0, board.offers.size - 1)
        val quest = questFromOffer(board.offers[slot])
        if (world.acceptOffer(slot)) {
            showNotice(pack.text(language, "\$i18n:ui.quest_accepted", mapOf("quest" to dialogueText(pack, quest.name, quest.args))))
        } else {
            showNotice(pack.text(language, "\$i18n:ui.cannot_do"))
        }
    }

    private fun handleBoardInput(world: WorldSim) {
        val input = Gdx.input
        val count = world.board?.offers?.size ?: 0
        if (input.isKeyJustPressed(Input.Keys.ESCAPE)) {
            world.closeBoard()
        } else if (input.isKeyJustPressed(Input.Keys.UP) || input.isKeyJustPressed(Input.Keys.W)) {
            if (count > 0) boardCursor = (boardCursor.coerceIn(0, count - 1) + count - 1) % count
        } else if (input.isKeyJustPressed(Input.Keys.DOWN) || input.isKeyJustPressed(Input.Keys.S)) {
            if (count > 0) boardCursor = (boardCursor.coerceIn(0, count - 1) + 1) % count
        } else if (input.isKeyJustPressed(Input.Keys.E) || input.isKeyJustPressed(Input.Keys.ENTER) || input.isKeyJustPressed(Input.Keys.SPACE)) {
            boardConfirm(world)
        } else if (input.justTouched()) {
            // A tap selects an offer, a second tap on it accepts it; a tap elsewhere closes the board.
            val x = input.x.toFloat()
            val y = input.y.toFloat()
            val row = boardRowRects.indexOfFirst { x >= it[0] && x <= it[0] + it[2] && y >= it[1] && y <= it[1] + it[3] }
            if (row < 0) {
                world.closeBoard()
            } else if (row == boardCursor) {
                boardConfirm(world)
            } else {
                boardCursor = row
            }
        }
    }

    /** Talks to the NPC in range or, with none, wakes the Threshold Stone near the player (spec 09). */
    private fun interact(world: WorldSim) {
        val story = world.story
        if (!story.dialogueView().active && story.npcInRange() == null && world.useStone()) {
            val travel = world.travel
            travelCursor = if (travel != null && travel.here == 0 && travel.stops.size > 1) 1 else 0
        } else if (story.npcInRange() == null && !story.dialogueView().active) { // a prop to gather from (spec 06, "Gathering")
            val pack = assets?.pack ?: return
            val found = world.gather()
            if (found.node) {
                val list = found.items.joinToString(", ") { (item, qty) ->
                    pack.text(language, "\$i18n:${item.substringAfter(':').replace('/', '.')}.name", mapOf("count" to qty)) + " x$qty"
                }
                showNotice(if (list.isEmpty()) pack.text(language, "\$i18n:ui.gather_nothing") else pack.text(language, "\$i18n:ui.gathered", mapOf("items" to list)))
            }
        } else {
            story.interact()
        }
    }

    private fun canInteract(world: WorldSim) = world.story.npcInRange() != null || world.stoneNear() != null || world.gatherNear()

    private fun travelConfirm(world: WorldSim) {
        val pack = assets?.pack ?: return
        val travel = world.travel ?: return
        if (travel.stops.isEmpty()) return
        val stop = travel.stops[travelCursor.coerceIn(0, travel.stops.size - 1)]
        if (world.travelTo(travelCursor)) {
            showNotice(pack.text(language, "\$i18n:ui.traveled", mapOf("place" to stop.place)))
        } else {
            showNotice(pack.text(language, "\$i18n:ui.cannot_do"))
        }
    }

    private fun handleTravelInput(world: WorldSim) {
        val input = Gdx.input
        val count = world.travel?.stops?.size ?: 0
        if (input.isKeyJustPressed(Input.Keys.ESCAPE)) {
            world.closeTravel()
        } else if (input.isKeyJustPressed(Input.Keys.UP) || input.isKeyJustPressed(Input.Keys.W)) {
            if (count > 0) travelCursor = (travelCursor.coerceIn(0, count - 1) + count - 1) % count
        } else if (input.isKeyJustPressed(Input.Keys.DOWN) || input.isKeyJustPressed(Input.Keys.S)) {
            if (count > 0) travelCursor = (travelCursor.coerceIn(0, count - 1) + 1) % count
        } else if (input.isKeyJustPressed(Input.Keys.E) || input.isKeyJustPressed(Input.Keys.ENTER) || input.isKeyJustPressed(Input.Keys.SPACE)) {
            travelConfirm(world)
        } else if (input.justTouched()) {
            // A tap selects a stone, a second tap on it travels there; a tap elsewhere closes the list.
            val x = input.x.toFloat()
            val y = input.y.toFloat()
            val row = travelRowRects.indexOfFirst { x >= it[0] && x <= it[0] + it[2] && y >= it[1] && y <= it[1] + it[3] }
            if (row < 0) {
                world.closeTravel()
            } else if (row == travelCursor) {
                travelConfirm(world)
            } else {
                travelCursor = row
            }
        }
    }

    private fun handleStoryInput(world: WorldSim) {
        val story = world.story
        val input = Gdx.input
        val view = story.dialogueView()
        if (world.travel != null) {
            handleTravelInput(world)
            return
        }
        if (world.board != null) {
            handleBoardInput(world)
            return
        }
        if (world.shop != null) {
            handleShopInput(world)
            return
        }
        if (input.isKeyJustPressed(Input.Keys.F2)) {
            assets?.let { toggleLanguage(it) }
            return
        }
        if (showCraft) {
            val recipes = world.combat.recipes
            if (input.isKeyJustPressed(Input.Keys.C) || input.isKeyJustPressed(Input.Keys.ESCAPE)) {
                showCraft = false
            } else if (input.isKeyJustPressed(Input.Keys.UP) || input.isKeyJustPressed(Input.Keys.W)) {
                if (recipes.isNotEmpty()) craftCursor = (craftCursor + recipes.size - 1) % recipes.size
            } else if (input.isKeyJustPressed(Input.Keys.DOWN) || input.isKeyJustPressed(Input.Keys.S)) {
                if (recipes.isNotEmpty()) craftCursor = (craftCursor + 1) % recipes.size
            } else if (input.isKeyJustPressed(Input.Keys.E) || input.isKeyJustPressed(Input.Keys.ENTER)) {
                craftSelected(world)
            } else if (input.justTouched()) {
                val x = input.x.toFloat()
                val y = input.y.toFloat()
                val panel = craftPanel
                if (panel == null || x < panel[0] || x > panel[0] + panel[2] || y < panel[1] || y > panel[1] + panel[3]) {
                    showCraft = false
                } else {
                    val row = craftRowRects.indexOfFirst { r -> x >= r[0] && x <= r[0] + r[2] && y >= r[1] && y <= r[1] + r[3] }
                    if (row >= 0) {
                        craftCursor = row
                        craftSelected(world)
                    }
                }
            }
            return
        }
        if (input.isKeyJustPressed(Input.Keys.C) && !showMap) {
            showCraft = true
            craftCursor = 0
            return
        }
        if (showJournal) {
            if (input.isKeyJustPressed(Input.Keys.Q) || input.isKeyJustPressed(Input.Keys.ESCAPE)) {
                showJournal = false
                showCraft = false
            } else if (input.isKeyJustPressed(Input.Keys.UP) || input.isKeyJustPressed(Input.Keys.W)) {
                journalScroll = max(journalScroll - 1, 0)
            } else if (input.isKeyJustPressed(Input.Keys.DOWN) || input.isKeyJustPressed(Input.Keys.S)) {
                journalScroll++ // clamped when drawn
            } else if (input.justTouched()) {
                // A tap on the upper half of the panel scrolls up, on the lower half down, outside it closes the journal.
                val x = input.x.toFloat()
                val y = input.y.toFloat()
                val panel = journalPanel
                if (panel == null || x < panel[0] || x > panel[0] + panel[2] || y < panel[1] || y > panel[1] + panel[3]) {
                    showJournal = false
                    showCraft = false
                } else if (y < panel[1] + panel[3] / 2f) {
                    journalScroll = max(journalScroll - 3, 0)
                } else {
                    journalScroll += 3
                }
            }
            return
        }
        if (showMap) {
            handleMapInput(world)
            return
        }
        if (showInventory) {
            val count = world.inventory.size
            if (input.isKeyJustPressed(Input.Keys.I) || input.isKeyJustPressed(Input.Keys.ESCAPE)) {
                showInventory = false
            } else if (input.isKeyJustPressed(Input.Keys.UP) || input.isKeyJustPressed(Input.Keys.W)) {
                if (count > 0) bagCursor = (bagCursor.coerceIn(0, count - 1) + count - 1) % count
            } else if (input.isKeyJustPressed(Input.Keys.DOWN) || input.isKeyJustPressed(Input.Keys.S)) {
                if (count > 0) bagCursor = (bagCursor.coerceIn(0, count - 1) + 1) % count
            } else if (input.isKeyJustPressed(Input.Keys.E) || input.isKeyJustPressed(Input.Keys.ENTER) || input.isKeyJustPressed(Input.Keys.SPACE)) {
                useSelectedItem(world)
            } else if (input.justTouched()) {
                // Tapping a row selects it, tapping the selected row uses it, tapping elsewhere closes the bag.
                val x = input.x.toFloat()
                val y = input.y.toFloat()
                val row = bagRowRects.indexOfFirst { x >= it[0] && x <= it[0] + it[2] && y >= it[1] && y <= it[1] + it[3] }
                if (row < 0) {
                    showInventory = false
                } else if (row == bagCursor) {
                    useSelectedItem(world)
                } else {
                    bagCursor = row
                }
            }
            return
        }
        if (input.isKeyJustPressed(Input.Keys.M) && world.chunks != null) {
            showMap = true
            mapLevel = -1
            mapPick = -1
            return
        }
        if (input.isKeyJustPressed(Input.Keys.N)) {
            showMinimap = !showMinimap
            return
        }
        if (input.isKeyJustPressed(Input.Keys.Z) && hasAnalyze) {
            analyzeFrames = if (analyzeFrames > 0) 0 else 360
            return
        }
        if (input.isKeyJustPressed(Input.Keys.I)) {
            showInventory = true
            return
        }
        if (input.isKeyJustPressed(Input.Keys.Q)) {
            showJournal = true
            journalScroll = 0
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
            if (view.active && view.isChoice) story.choose(choiceIndex) else interact(world)
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
                val analyze = analyzeRect
                if (analyze != null && x >= analyze[0] && x <= analyze[0] + analyze[2] && y >= analyze[1] && y <= analyze[1] + analyze[3]) {
                    analyzeFrames = if (analyzeFrames > 0) 0 else 360 // Analyze: six seconds, or again to hide
                    return
                }
                val mini = miniRect
                if (mini != null && world.chunks != null && x >= mini[0] && x <= mini[0] + mini[2] && y >= mini[1] && y <= mini[1] + mini[3]) {
                    showMap = true // a tap on the small map opens the world map
                    mapLevel = -1
                    mapPick = -1
                    mapTouchOnButton = true
                    return
                }
                val map = mapRect
                if (map != null && world.chunks != null && x >= map[0] && x <= map[0] + map[2] && y >= map[1] && y <= map[1] + map[3]) {
                    showMap = true
                    mapLevel = -1
                    mapPick = -1
                    mapTouchOnButton = true // the touch that opened the map does not drag it
                    return
                }
                val journal = journalRect
                if (journal != null && x >= journal[0] && x <= journal[0] + journal[2] && y >= journal[1] && y <= journal[1] + journal[3]) {
                    showJournal = true
                    journalScroll = 0
                    return
                }
                val craftButton = craftRect
                if (craftButton != null && x >= craftButton[0] && x <= craftButton[0] + craftButton[2] && y >= craftButton[1] && y <= craftButton[1] + craftButton[3]) {
                    showCraft = true
                    craftCursor = 0
                    return
                }
                val snd = soundRect
                if (snd != null && x >= snd[0] && x <= snd[0] + snd[2] && y >= snd[1] && y <= snd[1] + snd[3]) {
                    cycleVolume()
                    return
                }
                val lang = languageRect
                if (lang != null && x >= lang[0] && x <= lang[0] + lang[2] && y >= lang[1] && y <= lang[1] + lang[3]) {
                    assets?.let { toggleLanguage(it) }
                    return
                }
                val bag = bagRect
                if (bag != null && x >= bag[0] && x <= bag[0] + bag[2] && y >= bag[1] && y <= bag[1] + bag[3]) {
                    showInventory = true
                    return
                }
                val rect = talkRect
                if (rect != null && canInteract(world) &&
                    x >= rect[0] && x <= rect[0] + rect[2] && y >= rect[1] && y <= rect[1] + rect[3]
                ) {
                    interact(world)
                    choiceIndex = 0
                }
            }
        }
        this.input.attackExcludedRect = talkRect.takeIf { !story.dialogueView().active && canInteract(world) }
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
            lastArgs = view.args
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
                    heading = speakerName(data.pack, lastSpeaker, lastArgs)
                    layout.setText(font, dialogueText(data.pack, lastText, lastArgs), Color.WHITE, boxW - 24f * density, 0, true)
                    questionHeight = layout.height + font.lineHeight * 1.5f + 8f * density
                    boxH += questionHeight
                }
            } else {
                heading = speakerName(data.pack, view.speaker, view.args)
                layout.setText(font, dialogueText(data.pack, view.text, view.args), Color.WHITE, boxW - 24f * density, 0, true)
                boxH = layout.height + font.lineHeight * 1.5f + 24f * density
            }
        }
        val boxY = height - boxH - margin

        // Talk button for touch screens.
        val canTalk = !view.active && canInteract(world)
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
            drawPanel(margin, boxY, boxW, boxH, Color(0.435f, 0.89f, 1f, 1f), 0.92f)
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
        // Gold and the quest tracker, top right, below the clock and the name of the region (which are right-aligned in the corner).
        var y = 12f * density + font.lineHeight * 2.6f
        val x = width - 300f * density
        font.color = Color(1f, 0.84f, 0.47f, 1f)
        hudText(data.pack.text(language, "\$i18n:ui.gold", mapOf("gold" to story.gold)), x, y)
        y += font.lineHeight * 1.3f
        if (world.chunks != null) {
            val px = world.player.position.x
            val py = world.player.position.y
            font.color = Color(0.67f, 0.75f, 0.82f, 1f)
            hudText(data.pack.text(language, "\$i18n:ui.coords", mapOf("x" to floor(px).toInt(), "y" to floor(py).toInt())), x, y)
            y += font.lineHeight * 1.2f
            if (hasGoal) {
                font.color = Color(0.35f, 1f, 0.47f, 1f)
                hudText(goalText(px, py, data), x, y)
                y += font.lineHeight * 1.2f
            }
            y += 4f * density
        }
        for ((questId, progress) in story.quests) {
            if (progress.done) continue
            val def = story.questDef(questId) ?: continue
            val stage: QuestStage = def.stages.firstOrNull { it.id == progress.stage } ?: continue
            font.color = Color(0.435f, 0.89f, 1f, 1f)
            hudText(dialogueText(data.pack, def.name, def.args), x, y)
            y += font.lineHeight * 1.2f
            font.color = Color(0.92f, 0.96f, 1f, 1f)
            layout.setText(font, dialogueText(data.pack, stage.journal, def.args), font.color, 280f * density, 0, true)
            font.draw(batch, layout, x, y)
            y += layout.height + 4f * density
            for ((i, objective) in stage.objectives.withIndex()) {
                if (objective.kind == ObjectiveKind.TALK) continue
                hudText("  ${progress.progress[i]}/${objective.count}", x, y)
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
                    layout.setText(font, dialogueText(data.pack, lastText, lastArgs), font.color, boxW - 24f * density, 0, true)
                    font.draw(batch, layout, margin + 12f * density, ty + font.lineHeight * 1.5f)
                    ty += questionHeight
                }
                for ((i, choice) in view.choices.withIndex()) {
                    font.color = if (i == choiceIndex) Color(0.435f, 0.89f, 1f, 1f) else Color.WHITE
                    font.draw(
                        batch, "${i + 1}. ${dialogueText(data.pack, choice, view.args)}",
                        margin + 12f * density, ty + (font.lineHeight * 1.5f - font.lineHeight) / 2f,
                    )
                    ty += font.lineHeight * 1.5f
                }
            } else {
                font.color = Color(1f, 0.84f, 0.47f, 1f)
                font.draw(batch, heading, margin + 12f * density, ty)
                ty += font.lineHeight * 1.5f
                font.color = Color(0.92f, 0.96f, 1f, 1f)
                layout.setText(font, dialogueText(data.pack, view.text, view.args), font.color, boxW - 24f * density, 0, true)
                font.draw(batch, layout, margin + 12f * density, ty)
            }
        }
        font.color = Color.WHITE
        batch.end()
        drawBagAndNotice(world, data)
        drawWorldMap(world, data)
        drawShop(world, data)
        drawBoard(world, data)
        drawJournal(world, data)
        drawTravel(world, data)
    }

    /** The first row to draw of a long list: the rows that fit on the screen, with the cursor kept near the middle. */
    private fun listWindow(total: Int, cursor: Int, maxRows: Int): Int = if (total <= maxRows) 0 else (cursor - maxRows / 2).coerceIn(0, total - maxRows)

    /** The shop (spec 06): buy / sell tabs, the entries with their price and the gold. */
    private fun drawShop(world: WorldSim, data: Assets) {
        if (world.shop == null) {
            shopRowRects = emptyList()
            return
        }
        val density = Gdx.graphics.density
        val width = Gdx.graphics.width.toFloat()
        val height = Gdx.graphics.height.toFloat()
        val entries = shopEntries(world)
        val rowH = font.lineHeight * 1.5f
        val panelW = min(width - 40f, 460f * density)
        val cursor = shopCursor.coerceIn(0, max(entries.size - 1, 0))
        val maxRows = max(3, ((height - 150f * density) / rowH).toInt()) // a long list scrolls with the cursor
        val visible = min(entries.size, maxRows)
        val first = listWindow(entries.size, cursor, maxRows)
        val panelH = 96f * density + rowH * max(visible, 1)
        val panelX = (width - panelW) / 2f
        val panelY = (height - panelH) / 2f
        val tabY = panelY + 10f * density
        val tabW = 110f * density
        val tabH = 30f * density
        shopBuyTab = floatArrayOf(panelX + 12f * density, tabY, tabW, tabH)
        shopSellTab = floatArrayOf(panelX + 24f * density + tabW, tabY, tabW, tabH)
        val firstRowY = tabY + tabH + 12f * density
        shopRowRects = entries.indices.map { if (it in first until first + visible) floatArrayOf(panelX, firstRowY + (it - first) * rowH, panelW, rowH) else OFF_SCREEN }

        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        drawPanel(panelX, panelY, panelW, panelH, Color(1f, 0.84f, 0.47f, 1f), 0.96f)
        for ((i, tab) in listOf(shopBuyTab, shopSellTab).withIndex()) {
            val active = (i == 1) == shopSell
            shapes.color = if (active) Color(0.16f, 0.35f, 0.55f, 1f) else Color(0.08f, 0.16f, 0.28f, 1f)
            shapes.rect(tab!![0], tab[1], tab[2], tab[3])
        }
        if (entries.isNotEmpty()) {
            shapes.color = Color(0.16f, 0.35f, 0.55f, 1f)
            shapes.rect(panelX + 6f * density, firstRowY + (cursor - first) * rowH - 2f * density, panelW - 12f * density, rowH)
        }
        shapes.end()

        batch.projectionMatrix = camera.combined
        batch.begin()
        font.color = Color.WHITE
        font.draw(batch, data.pack.text(language, "\$i18n:ui.shop_buy"), shopBuyTab!![0] + 10f * density, tabY + (tabH - font.lineHeight) / 2f)
        font.draw(batch, data.pack.text(language, "\$i18n:ui.shop_sell"), shopSellTab!![0] + 10f * density, tabY + (tabH - font.lineHeight) / 2f)
        font.color = Color(1f, 0.84f, 0.47f, 1f)
        val gold = data.pack.text(language, "\$i18n:ui.gold", mapOf("gold" to world.story.gold))
        layout.setText(font, gold)
        font.draw(batch, gold, panelX + panelW - layout.width - 14f * density, tabY + (tabH - font.lineHeight) / 2f)
        if (entries.isEmpty()) {
            font.color = Color(0.92f, 0.96f, 1f, 1f)
            font.draw(batch, data.pack.text(language, "\$i18n:ui.shop_empty"), panelX + 16f * density, firstRowY)
        }
        for ((i, entry) in entries.withIndex()) {
            if (i < first || i >= first + visible) continue
            val key = entry.first.substringAfter(':').replace('/', '.')
            val name = data.pack.text(language, "\$i18n:$key.name", mapOf("count" to 1L))
            font.color = if (i == cursor) Color.WHITE else Color(0.92f, 0.96f, 1f, 1f)
            font.draw(batch, (if (i == cursor) "> " else "  ") + name, panelX + 14f * density, firstRowY + (i - first) * rowH)
            font.color = Color(1f, 0.84f, 0.47f, 1f)
            val price = entry.second.toString()
            layout.setText(font, price)
            font.draw(batch, price, panelX + panelW - layout.width - 14f * density, firstRowY + (i - first) * rowH)
        }
        batch.end()
    }

    /** The list of Threshold Stones (spec 09): the places whose stone was woken, with the region of each. */
    private fun drawTravel(world: WorldSim, data: Assets) {
        val travel = world.travel
        if (travel == null) {
            travelRowRects = emptyList()
            return
        }
        val density = Gdx.graphics.density
        val width = Gdx.graphics.width.toFloat()
        val height = Gdx.graphics.height.toFloat()
        val rowH = font.lineHeight * 2.6f
        val panelW = min(width - 40f, 560f * density)
        val cursor = travelCursor.coerceIn(0, max(travel.stops.size - 1, 0))
        val maxRows = max(2, ((height - 170f * density) / rowH).toInt()) // a long list scrolls with the cursor
        val visible = min(travel.stops.size, maxRows)
        val first = listWindow(travel.stops.size, cursor, maxRows)
        val panelH = 96f * density + rowH * max(visible, 1)
        val panelX = (width - panelW) / 2f
        val panelY = (height - panelH) / 2f
        val firstRowY = panelY + 64f * density
        travelRowRects = travel.stops.indices.map { if (it in first until first + visible) floatArrayOf(panelX, firstRowY + (it - first) * rowH, panelW, rowH) else OFF_SCREEN }

        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        drawPanel(panelX, panelY, panelW, panelH, Color(0.435f, 0.89f, 1f, 1f), 0.96f)
        shapes.color = Color(0.16f, 0.35f, 0.55f, 1f)
        shapes.rect(panelX + 6f * density, firstRowY + (cursor - first) * rowH - 2f * density, panelW - 12f * density, rowH)
        shapes.end()

        batch.projectionMatrix = camera.combined
        batch.begin()
        font.color = Color(0.435f, 0.89f, 1f, 1f)
        font.draw(batch, data.pack.text(language, "\$i18n:ui.travel"), panelX + 14f * density, panelY + 12f * density)
        font.color = Color(1f, 0.84f, 0.47f, 1f)
        font.draw(
            batch, data.pack.text(language, if (travel.fresh) "\$i18n:ui.stone_awake" else "\$i18n:ui.stone_rest"),
            panelX + 14f * density, panelY + 12f * density + font.lineHeight * 1.5f,
        )
        for ((i, stop) in travel.stops.withIndex()) {
            if (i < first || i >= first + visible) continue
            val here = i == travel.here
            val rowY = firstRowY + (i - first) * rowH
            font.color = if (here) Color(0.51f, 0.55f, 0.63f, 1f) else Color.WHITE
            val tag = if (here) "  (" + data.pack.text(language, "\$i18n:ui.travel_here") + ")" else ""
            font.draw(batch, (if (i == cursor) "> " else "  ") + stop.place + tag, panelX + 14f * density, rowY)
            font.color = Color(0.67f, 0.78f, 0.9f, 1f)
            font.draw(batch, data.pack.text(language, stop.region), panelX + 30f * density, rowY + font.lineHeight * 1.2f)
        }
        font.color = Color(0.67f, 0.78f, 0.9f, 1f)
        font.draw(batch, data.pack.text(language, "\$i18n:ui.travel_hint"), panelX + 14f * density, panelY + panelH - font.lineHeight * 1.6f)
        font.color = Color.WHITE
        batch.end()
    }

    /** The journal entries (spec 07, "Journal"): (text, kind) with kind 0 section title, 1 quest name, 2 text, 3 finished quest. */
    private fun journalEntries(world: WorldSim, data: Assets): List<Pair<String, Int>> {
        val story = world.story
        val entries = ArrayList<Pair<String, Int>>()
        if (story.quests.isEmpty()) {
            entries.add(Pair(data.pack.text(language, "\$i18n:ui.journal_empty"), 2))
        }
        if (story.quests.values.any { !it.done }) {
            entries.add(Pair(data.pack.text(language, "\$i18n:ui.journal_active"), 0))
            for ((questId, progress) in story.quests) {
                if (progress.done) continue
                val def = story.questDef(questId) ?: continue
                val stage = def.stages.firstOrNull { it.id == progress.stage } ?: continue
                entries.add(Pair(dialogueText(data.pack, def.name, def.args), 1))
                entries.add(Pair(dialogueText(data.pack, stage.journal, def.args), 2))
                for ((i, objective) in stage.objectives.withIndex()) {
                    if (objective.kind != ObjectiveKind.TALK) entries.add(Pair("${progress.progress[i]}/${objective.count}", 2))
                }
            }
        }
        if (story.quests.values.any { it.done }) {
            entries.add(Pair(data.pack.text(language, "\$i18n:ui.journal_done"), 0))
            for ((questId, progress) in story.quests) {
                if (!progress.done) continue
                val def = story.questDef(questId) ?: continue
                entries.add(Pair(dialogueText(data.pack, def.name, def.args), 3))
            }
        }
        // Titles and bestiary (spec 11): the titles earned (the last one counts), then every creature killed with its count.
        val earned = world.earnedTitles()
        if (world.combat.titles.isNotEmpty()) {
            entries.add(Pair("", 2))
            entries.add(Pair("${data.pack.text(language, "\$i18n:ui.journal_titles")} ${earned.size}/${world.combat.titles.size}", 0))
            for (title in world.combat.titles) {
                val have = title.id in earned
                entries.add(Pair(if (have) data.pack.text(language, title.name) else "???", if (have) 1 else 3))
            }
        }
        if (world.bestiary.isNotEmpty()) {
            entries.add(Pair("", 2))
            entries.add(Pair("${data.pack.text(language, "\$i18n:ui.journal_bestiary")} ${world.bestiary.size}", 0))
            for ((id, count) in world.bestiary) {
                entries.add(Pair("  ${data.pack.text(language, "\$i18n:enemy.${id.substringAfterLast('/')}.name")}  x$count", 2))
            }
        }
        return entries
    }

    /** The journal and language buttons, and the journal panel (the quests in progress, then the finished ones). */
    private fun drawJournal(world: WorldSim, data: Assets) {
        val density = Gdx.graphics.density
        val width = Gdx.graphics.width.toFloat()
        val height = Gdx.graphics.height.toFloat()
        val journalButton = floatArrayOf(12f * density, 114f * density, 96f * density, 34f * density)
        val languageButton = floatArrayOf(12f * density + 104f * density, 114f * density, 96f * density, 34f * density)
        val soundButton = floatArrayOf(12f * density + 208f * density, 114f * density, 80f * density, 34f * density)
        journalRect = journalButton
        languageRect = languageButton
        soundRect = soundButton
        val panelW = min(width - 40f, 560f * density)
        val panelH = min(height - 40f, 480f * density)
        val panelX = (width - panelW) / 2f
        val panelY = (height - panelH) / 2f
        journalPanel = if (showJournal) floatArrayOf(panelX, panelY, panelW, panelH) else null

        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        shapes.color = Color(0.04f, 0.12f, 0.23f, 0.8f)
        shapes.rect(journalButton[0], journalButton[1], journalButton[2], journalButton[3])
        shapes.rect(languageButton[0], languageButton[1], languageButton[2], languageButton[3])
        shapes.rect(soundButton[0], soundButton[1], soundButton[2], soundButton[3])
        if (showJournal) {
            shapes.color = Color(0.04f, 0.12f, 0.23f, 0.96f)
            shapes.rect(panelX, panelY, panelW, panelH)
            shapes.color = Color(1f, 0.84f, 0.47f, 1f)
            shapes.rect(panelX, panelY, panelW, 3f * density)
        }
        shapes.end()

        batch.projectionMatrix = camera.combined
        batch.begin()
        font.color = Color.WHITE
        font.draw(batch, data.pack.text(language, "\$i18n:ui.journal"), journalButton[0] + 8f * density, journalButton[1] + (journalButton[3] - font.lineHeight) / 2f)
        font.draw(batch, language.uppercase(Locale.ROOT), languageButton[0] + 8f * density, languageButton[1] + (languageButton[3] - font.lineHeight) / 2f)
        font.draw(batch, "${volumes[0] / 10}%", soundButton[0] + 8f * density, soundButton[1] + (soundButton[3] - font.lineHeight) / 2f)
        if (showJournal) {
            font.color = Color(1f, 0.84f, 0.47f, 1f)
            font.draw(batch, data.pack.text(language, "\$i18n:ui.journal"), panelX + 16f * density, panelY + 12f * density)
            val entries = journalEntries(world, data)
            journalScroll = journalScroll.coerceIn(0, max(entries.size - 1, 0))
            var ty = panelY + 12f * density + font.lineHeight * 1.8f
            val limit = panelY + panelH - font.lineHeight * 2.2f
            for (i in journalScroll until entries.size) {
                val (text, kind) = entries[i]
                font.color = when (kind) {
                    0 -> Color(1f, 0.84f, 0.47f, 1f)
                    1 -> Color(0.435f, 0.89f, 1f, 1f)
                    3 -> Color(0.51f, 0.55f, 0.63f, 1f)
                    else -> Color(0.92f, 0.96f, 1f, 1f)
                }
                layout.setText(font, text, font.color, panelW - 32f * density, 0, true)
                if (ty + layout.height > limit) break
                font.draw(batch, layout, panelX + 16f * density, ty)
                ty += layout.height + font.lineHeight * 0.4f
            }
            font.color = Color(0.67f, 0.78f, 0.9f, 1f)
            font.draw(batch, data.pack.text(language, "\$i18n:ui.journal_hint"), panelX + 16f * density, panelY + panelH - font.lineHeight * 1.5f)
            font.color = Color.WHITE
        }
        batch.end()
    }

    /** The guild board (spec 07, "Guild"): rank, points and the offers of the day with their reward. */
    private fun drawBoard(world: WorldSim, data: Assets) {
        val board = world.board
        val store = world.chunks
        if (board == null || store == null) {
            boardRowRects = emptyList()
            return
        }
        val density = Gdx.graphics.density
        val width = Gdx.graphics.width.toFloat()
        val height = Gdx.graphics.height.toFloat()
        val guild = store.params.guild
        val rank = world.guildRank()
        fun letter(index: Int) = guild.ranks[index].id.uppercase(Locale.ROOT)
        val rowH = font.lineHeight * 3.4f
        val panelW = min(width - 40f, 640f * density)
        val panelH = 92f * density + rowH * max(board.offers.size, 1)
        val panelX = (width - panelW) / 2f
        val panelY = (height - panelH) / 2f
        val firstRowY = panelY + 64f * density
        boardRowRects = board.offers.indices.map { floatArrayOf(panelX, firstRowY + it * rowH, panelW, rowH) }
        val cursor = boardCursor.coerceIn(0, max(board.offers.size - 1, 0))

        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        shapes.color = Color(0.04f, 0.12f, 0.23f, 0.96f)
        shapes.rect(panelX, panelY, panelW, panelH)
        shapes.color = Color(0.435f, 0.89f, 1f, 1f)
        shapes.rect(panelX, panelY, panelW, 3f * density)
        if (board.offers.isNotEmpty()) {
            shapes.color = Color(0.16f, 0.35f, 0.55f, 1f)
            shapes.rect(panelX + 6f * density, firstRowY + cursor * rowH - 2f * density, panelW - 12f * density, rowH)
        }
        shapes.end()

        batch.projectionMatrix = camera.combined
        batch.begin()
        font.color = Color(0.435f, 0.89f, 1f, 1f)
        font.draw(batch, data.pack.text(language, "\$i18n:ui.board") + " - " + board.settlement.name, panelX + 14f * density, panelY + 12f * density)
        font.color = Color(1f, 0.84f, 0.47f, 1f)
        val status = data.pack.text(language, "\$i18n:ui.rank", mapOf("rank" to letter(rank))) + "  " +
            data.pack.text(language, "\$i18n:ui.guild_points", mapOf("points" to world.story.guildPoints))
        font.draw(batch, status, panelX + 14f * density, panelY + 12f * density + font.lineHeight * 1.5f)
        for ((i, offer) in board.offers.withIndex()) {
            val quest = questFromOffer(offer)
            val locked = rank < offer.minRank
            val taken = offer.id in world.story.quests
            var name = dialogueText(data.pack, quest.name, quest.args)
            if (taken) {
                name += "  (" + data.pack.text(language, "\$i18n:ui.board_taken") + ")"
            } else if (locked) {
                name += "  (" + data.pack.text(language, "\$i18n:ui.board_locked", mapOf("rank" to letter(offer.minRank))) + ")"
            }
            val rowY = firstRowY + i * rowH
            font.color = if (locked) Color(0.51f, 0.55f, 0.63f, 1f) else Color.WHITE
            font.draw(batch, (if (i == cursor) "> " else "  ") + name, panelX + 14f * density, rowY)
            font.color = Color(0.67f, 0.78f, 0.9f, 1f)
            layout.setText(font, dialogueText(data.pack, quest.stages.first().journal, quest.args), font.color, panelW - 48f * density, 0, true)
            font.draw(batch, layout, panelX + 30f * density, rowY + font.lineHeight * 1.1f)
            font.color = Color(1f, 0.84f, 0.47f, 1f)
            val reward = data.pack.text(
                language, "\$i18n:ui.board_reward",
                mapOf("gold" to offer.gold, "xp" to offer.xp, "points" to offer.points),
            )
            font.draw(batch, reward, panelX + 30f * density, rowY + font.lineHeight * 2.2f)
        }
        font.color = Color(0.67f, 0.78f, 0.9f, 1f)
        font.draw(batch, data.pack.text(language, "\$i18n:ui.board_hint"), panelX + 14f * density, panelY + panelH - font.lineHeight * 1.6f)
        font.color = Color.WHITE
        batch.end()
    }

    /** The settlement shown on a world map cell, computed once per cell. */
    private fun markerAt(store: io.github.progliodario.aethermoor.core.sim.ChunkStore, x: Int, y: Int): io.github.progliodario.aethermoor.core.Settlement? {
        val key = Pair(x, y)
        if (!mapMarkers.containsKey(key)) mapMarkers[key] = settlementMarker(store.seed, store.params, x, y)
        return mapMarkers[key]
    }

    /** A square window onto the world map (spec 09, "The map view"): `cell` pixels per map cell, centered on cell (cx, cy). */
    private class MapView(val x: Float, val y: Float, val side: Float, val cell: Float, val cx: Float, val cy: Float) {
        fun toX(cellX: Float) = x + side / 2f + (cellX - cx) * cell
        fun toY(cellY: Float) = y + side / 2f + (cellY - cy) * cell
    }

    /** A button of the map: its rectangle in pixels and what it does (0 zoom in, 1 zoom out, 2 find the player, 3 show all, 4 close). */
    private class MapButton(val rect: FloatArray, val action: Int, val label: String)

    /** Frames the explored cells with a margin of one cell: the biggest zoom at which they all fit, centered on them. */
    private fun mapFit(world: WorldSim, columns: Int, rows: Int, side: Float) {
        var minX = columns
        var minY = rows
        var maxX = 0
        var maxY = 0
        for ((x, y) in world.explored) {
            minX = min(minX, x)
            minY = min(minY, y)
            maxX = max(maxX, x)
            maxY = max(maxY, y)
        }
        if (minX > maxX) {
            minX = (world.player.position.x / MAP_CELL).toInt()
            maxX = minX
            minY = (world.player.position.y / MAP_CELL).toInt()
            maxY = minY
        }
        val span = (max(maxX - minX, maxY - minY) + 3).toFloat()
        val base = side / max(columns, rows)
        var level = 0
        while (level < MAP_MAX_LEVEL && span * base * (1 shl (level + 1)) <= side) level++
        mapLevel = level
        mapCx = (minX + maxX + 1) / 2f
        mapCy = (minY + maxY + 1) / 2f
    }

    private fun mapPan(store: io.github.progliodario.aethermoor.core.sim.ChunkStore, dxCells: Float, dyCells: Float) {
        val columns = (store.params.width + MAP_CELL - 1) / MAP_CELL
        val rows = (store.params.height + MAP_CELL - 1) / MAP_CELL
        mapCx = (mapCx + dxCells).coerceIn(0f, columns.toFloat())
        mapCy = (mapCy + dyCells).coerceIn(0f, rows.toFloat())
    }

    private fun mapZoom(delta: Int) {
        if (mapLevel >= 0) mapLevel = (mapLevel + delta).coerceIn(0, MAP_MAX_LEVEL)
    }

    /** The keys, the buttons, the drag and the pinch of the open world map (spec 16). */
    private fun handleMapInput(world: WorldSim) {
        val store = world.chunks ?: return
        val input = Gdx.input
        if (input.isKeyJustPressed(Input.Keys.M) || input.isKeyJustPressed(Input.Keys.ESCAPE)) {
            showMap = false
            return
        }
        val step = mapViewCells / 6f
        if (input.isKeyJustPressed(Input.Keys.PLUS) || input.isKeyJustPressed(Input.Keys.EQUALS)) mapZoom(1)
        if (input.isKeyJustPressed(Input.Keys.MINUS)) mapZoom(-1)
        if (input.isKeyJustPressed(Input.Keys.UP) || input.isKeyJustPressed(Input.Keys.W)) mapPan(store, 0f, -step)
        if (input.isKeyJustPressed(Input.Keys.DOWN) || input.isKeyJustPressed(Input.Keys.S)) mapPan(store, 0f, step)
        if (input.isKeyJustPressed(Input.Keys.LEFT) || input.isKeyJustPressed(Input.Keys.A)) mapPan(store, -step, 0f)
        if (input.isKeyJustPressed(Input.Keys.RIGHT) || input.isKeyJustPressed(Input.Keys.D)) mapPan(store, step, 0f)
        if (input.isKeyJustPressed(Input.Keys.C)) mapCenterOnPlayer(world)
        if (input.isKeyJustPressed(Input.Keys.TAB)) mapNextPlace(world)
        if (input.isKeyJustPressed(Input.Keys.P)) setGoal(world, mapCx, mapCy)
        if (input.isKeyJustPressed(Input.Keys.X)) {
            hasGoal = false
            saveGoal()
        }
        if (input.isKeyJustPressed(Input.Keys.NUM_0) || input.isKeyJustPressed(Input.Keys.HOME)) mapLevel = -1

        if (input.justTouched()) {
            val x = input.x.toFloat()
            val y = input.y.toFloat()
            val button = mapButtons.firstOrNull { x >= it.rect[0] && x <= it.rect[0] + it.rect[2] && y >= it.rect[1] && y <= it.rect[1] + it.rect[3] }
            mapTouchOnButton = button != null
            mapPinch = 0f
            when (button?.action) {
                0 -> mapZoom(1)
                1 -> mapZoom(-1)
                2 -> mapCenterOnPlayer(world)
                3 -> mapLevel = -1
                4 -> showMap = false
                5 -> if (hasGoal) {
                    hasGoal = false
                    saveGoal()
                } else {
                    setGoal(world, mapCx, mapCy)
                }
                6 -> mapNextPlace(world)
            }
            return
        }
        if (mapTouchOnButton) {
            if (!input.isTouched) mapTouchOnButton = false
            return
        }
        if (input.isTouched(0) && input.isTouched(1)) {
            // Pinch: the zoom goes up a level when the fingers spread by half, down a level when they close by a third.
            val dx = (input.getX(0) - input.getX(1)).toFloat()
            val dy = (input.getY(0) - input.getY(1)).toFloat()
            val distance = kotlin.math.sqrt(dx * dx + dy * dy)
            if (mapPinch <= 0f) {
                mapPinch = distance
            } else if (distance > mapPinch * 1.5f) {
                mapZoom(1)
                mapPinch = distance
            } else if (distance < mapPinch * 0.67f) {
                mapZoom(-1)
                mapPinch = distance
            }
        } else if (input.isTouched(0)) {
            mapPinch = 0f
            mapPan(store, -input.deltaX / mapCellPx, -input.deltaY / mapCellPx) // dragging moves the map under the finger
        } else {
            mapPinch = 0f
        }
    }

    /** The direction (eight points of the compass) and the distance in tiles to the goal. */
    private fun goalText(px: Float, py: Float, data: Assets): String {
        val dx = goalX - px
        val dy = goalY - py
        val distance = kotlin.math.sqrt(dx * dx + dy * dy).roundToInt()
        if (distance < 6) return data.pack.text(language, "\$i18n:ui.goal_here")
        val index = ((atan2(dy, dx) / (PI.toFloat() / 4f)).roundToInt() + 8) % 8 // 0 east, 2 south: y points down
        val dir = data.pack.text(language, "\$i18n:ui.dir_" + GOAL_DIRECTIONS[index])
        return data.pack.text(language, "\$i18n:ui.goal", mapOf("dir" to dir, "dist" to distance))
    }

    /** Marks the goal at a map position (in cells), inside the world. */
    private fun setGoal(world: WorldSim, cellX: Float, cellY: Float) {
        val params = world.chunks?.params ?: return
        goalX = (cellX * MAP_CELL).coerceIn(0f, (params.width - 1).toFloat())
        goalY = (cellY * MAP_CELL).coerceIn(0f, (params.height - 1).toFloat())
        hasGoal = true
        saveGoal()
        showNotice(assets?.pack?.text(language, "\$i18n:ui.goal_set") ?: "")
    }

    /**
     * A small map of the land around the player in a corner (spec 09, "The map view"): 40 x 40 samples 16 tiles apart (640 tiles across),
     * only where the land was explored, with the player in the middle, the woken stones and the goal.
     */
    private fun drawMinimap(world: WorldSim) {
        val store = world.chunks ?: return
        miniRect = null
        if (!showMinimap || showMap || world.story.dialogueActive) return
        val n = 40
        val step = 16
        val params = store.params
        val playerX = floor(world.player.position.x).toInt()
        val playerY = floor(world.player.position.y).toInt()
        val ox = (playerX / step) * step - n / 2 * step
        val oy = (playerY / step) * step - n / 2 * step
        if (miniCodes.size != n * n || miniOx != ox || miniOy != oy) { // sampled again every 16 tiles walked
            miniCodes = ByteArray(n * n) { k ->
                val tx = ox + (k % n) * step + step / 2
                val ty = oy + (k / n) * step + step / 2
                if (tx < 0 || ty < 0 || tx >= params.width || ty >= params.height || Pair(tx / MAP_CELL, ty / MAP_CELL) !in world.explored) {
                    (-1).toByte()
                } else {
                    biomeCodeAt(store.seed, params, tx, ty).toByte()
                }
            }
            miniOx = ox
            miniOy = oy
        }
        val density = Gdx.graphics.density
        val cell = 3f * density
        val side = cell * n
        val x0 = 12f * density
        val y0 = 156f * density
        miniRect = floatArrayOf(x0, y0, side, side)
        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        Gdx.gl.glBlendFunc(GL20.GL_SRC_ALPHA, GL20.GL_ONE_MINUS_SRC_ALPHA)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        shapes.color = Color(0.08f, 0.14f, 0.26f, 0.9f)
        shapes.rect(x0 - 2f, y0 - 2f, side + 4f, side + 4f)
        shapes.color = Color(0.03f, 0.06f, 0.13f, 0.8f)
        shapes.rect(x0, y0, side, side)
        for (k in 0 until n * n) {
            val code = miniCodes[k].toInt()
            if (code < 0) continue
            val c = MAP_COLORS[code]
            shapes.color = Color(c.r, c.g, c.b, 0.92f)
            shapes.rect(x0 + (k % n) * cell, y0 + (k / n) * cell, ceil(cell), ceil(cell))
        }
        fun place(tileX: Float, tileY: Float, clamp: Boolean, size: Float, color: Color) {
            var sx = x0 + (tileX - ox) / step * cell
            var sy = y0 + (tileY - oy) / step * cell
            val inside = sx >= x0 && sy >= y0 && sx <= x0 + side && sy <= y0 + side
            if (!inside && !clamp) return
            sx = sx.coerceIn(x0 + size, x0 + side - size)
            sy = sy.coerceIn(y0 + size, y0 + side - size)
            shapes.color = Color(0.08f, 0.08f, 0.12f, 1f)
            shapes.rect(sx - size / 2f - 1f, sy - size / 2f - 1f, size + 2f, size + 2f)
            shapes.color = color
            shapes.rect(sx - size / 2f, sy - size / 2f, size, size)
        }
        for ((stoneX, stoneY) in world.stones) place(stoneX.toFloat(), stoneY.toFloat(), false, 4f * density, Color(0.55f, 1f, 0.92f, 1f))
        if (hasGoal) place(goalX, goalY, true, 5f * density, Color(0.35f, 1f, 0.47f, 1f))
        place(world.player.position.x, world.player.position.y, false, 5f * density, Color(1f, 0.2f, 0.2f, 1f))
        shapes.end()
    }

    private fun itemName(data: Assets, item: String, count: Long): String =
        data.pack.text(language, "\$i18n:${item.substringAfter(':').replace('/', '.')}.name", mapOf("count" to count))

    private fun craftSelected(world: WorldSim) {
        val data = assets ?: return
        val pack = data.pack
        val recipe = world.combat.recipes.getOrNull(craftCursor) ?: return
        if (world.craft(recipe.id)) {
            showNotice(pack.text(language, "\$i18n:ui.crafted", mapOf("item" to itemName(data, recipe.output, recipe.outputQty))))
        } else {
            showNotice(pack.text(language, "\$i18n:ui.cannot_craft"))
        }
    }

    /** The crafting panel and its button (spec 06, "Crafting"): the recipes with what the bag has of each ingredient; a tap on a row makes it. */
    private fun drawCraft(world: WorldSim, data: Assets) {
        val density = Gdx.graphics.density
        val width = Gdx.graphics.width.toFloat()
        val height = Gdx.graphics.height.toFloat()
        val button = floatArrayOf(12f * density + 296f * density, 114f * density, 96f * density, 34f * density)
        craftRect = if (showCraft || world.story.dialogueActive || showMap || showInventory || showJournal) null else button
        val recipes = world.combat.recipes
        if (!showCraft) {
            craftPanel = null
            craftRowRects = emptyList()
            if (craftRect == null || recipes.isEmpty()) {
                craftRect = null
                return
            }
            shapes.projectionMatrix = camera.combined
            Gdx.gl.glEnable(GL20.GL_BLEND)
            shapes.begin(ShapeRenderer.ShapeType.Filled)
            shapes.color = Color(0.04f, 0.12f, 0.23f, 0.8f)
            shapes.rect(button[0], button[1], button[2], button[3])
            shapes.end()
            batch.projectionMatrix = camera.combined
            batch.begin()
            font.color = Color.WHITE
            font.draw(batch, data.pack.text(language, "\$i18n:ui.craft"), button[0] + 8f * density, button[1] + (button[3] - font.lineHeight) / 2f)
            batch.end()
            return
        }
        val rowH = font.lineHeight * 2.8f
        val panelW = min(width - 40f, 680f * density)
        val panelH = min(height - 40f, 90f * density + rowH * max(recipes.size, 1))
        val panelX = (width - panelW) / 2f
        val panelY = (height - panelH) / 2f
        craftPanel = floatArrayOf(panelX, panelY, panelW, panelH)
        val firstRowY = panelY + 52f * density
        craftRowRects = recipes.indices.map { floatArrayOf(panelX, firstRowY + it * rowH, panelW, rowH) }
        craftCursor = craftCursor.coerceIn(0, max(recipes.size - 1, 0))
        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        drawPanel(panelX, panelY, panelW, panelH, Color(1f, 0.84f, 0.47f, 1f), 0.96f)
        for ((i, r) in craftRowRects.withIndex()) {
            if (r[1] + r[3] > panelY + panelH - 24f * density) break
            if (i == craftCursor) {
                shapes.color = Color(0.16f, 0.35f, 0.55f, 1f)
                shapes.rect(r[0] + 6f * density, r[1], r[2] - 12f * density, r[3] - 2f * density)
            }
        }
        shapes.end()
        batch.projectionMatrix = camera.combined
        batch.begin()
        font.color = Color(1f, 0.84f, 0.47f, 1f)
        font.draw(batch, data.pack.text(language, "\$i18n:ui.craft"), panelX + 16f * density, panelY + 12f * density)
        for ((i, recipe) in recipes.withIndex()) {
            val r = craftRowRects[i]
            if (r[1] + r[3] > panelY + panelH - 24f * density) break
            var can = true
            val needs = recipe.inputs.joinToString(", ") { (item, qty) ->
                val have = world.inventory[item] ?: 0L
                if (have < qty) can = false
                "${itemName(data, item, qty)} $have/$qty"
            }
            font.color = if (can) Color(0.6f, 1f, 0.67f, 1f) else Color(0.7f, 0.6f, 0.6f, 1f)
            font.draw(batch, "${itemName(data, recipe.output, recipe.outputQty)} x${recipe.outputQty}", r[0] + 16f * density, r[1] + 2f * density)
            font.color = Color(0.67f, 0.75f, 0.85f, 1f)
            font.draw(batch, needs, r[0] + 16f * density, r[1] + 2f * density + font.lineHeight * 1.2f)
        }
        font.color = Color(0.67f, 0.78f, 0.9f, 1f)
        font.draw(batch, data.pack.text(language, "\$i18n:ui.craft_hint"), panelX + 16f * density, panelY + panelH - font.lineHeight * 1.5f)
        font.color = Color.WHITE
        batch.end()
    }

    /** The parry button, above the power strike button: held, it opens the parry window (spec 05, "Parry"); a touch on it is never an attack. */
    private fun drawParryButton(world: WorldSim, data: Assets) {
        val density = Gdx.graphics.density
        val size = 64f * density
        val rect = floatArrayOf(
            Gdx.graphics.width - 84f * density - 24f * density + (84f * density - size) / 2f,
            Gdx.graphics.height - 84f * density - 24f * density - 12f * density - 72f * density - 12f * density - size, size, size,
        )
        val visible = world.combat.enabled && !world.story.dialogueActive && !showMap && !showInventory && !showJournal && !showCraft
        input.parryRect = rect.takeIf { visible }
        if (!visible) return
        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        Gdx.gl.glBlendFunc(GL20.GL_SRC_ALPHA, GL20.GL_ONE_MINUS_SRC_ALPHA)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        shapes.color = Color(0.04f, 0.12f, 0.23f, 0.7f)
        shapes.rect(rect[0], rect[1], rect[2], rect[3])
        shapes.end()
        batch.projectionMatrix = camera.combined
        batch.begin()
        val label = data.pack.text(language, "\$i18n:ui.parry")
        layout.setText(font, label)
        font.color = Color.WHITE
        font.draw(batch, label, rect[0] + (size - layout.width) / 2f, rect[1] + (size - font.lineHeight) / 2f)
        batch.end()
    }

    /** The power strike button, above the dodge button: held, it strikes while there is mana (spec 05, "Mana"); a touch on it is never an attack. */
    private fun drawStrikeButton(world: WorldSim, data: Assets) {
        val density = Gdx.graphics.density
        val size = 72f * density
        val rect = floatArrayOf(
            Gdx.graphics.width - 84f * density - 24f * density + (84f * density - size) / 2f,
            Gdx.graphics.height - 84f * density - 24f * density - 12f * density - size, size, size,
        )
        val visible = world.hasStrike && !world.story.dialogueActive && !showMap && !showInventory && !showJournal && !showCraft
        input.strikeRect = rect.takeIf { visible }
        if (!visible) return
        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        Gdx.gl.glBlendFunc(GL20.GL_SRC_ALPHA, GL20.GL_ONE_MINUS_SRC_ALPHA)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        shapes.color = Color(0.04f, 0.12f, 0.23f, 0.7f)
        shapes.rect(rect[0], rect[1], rect[2], rect[3])
        shapes.end()
        batch.projectionMatrix = camera.combined
        batch.begin()
        val label = data.pack.text(language, "\$i18n:ui.strike")
        layout.setText(font, label)
        font.color = Color.WHITE
        font.draw(batch, label, rect[0] + (size - layout.width) / 2f, rect[1] + (size - font.lineHeight) / 2f)
        batch.end()
    }

    /** The dodge button, bottom right: held, it rolls (spec 05, "Dodge roll"); a touch on it is never an attack. */
    private fun drawDodgeButton(world: WorldSim, data: Assets) {
        val density = Gdx.graphics.density
        val size = 84f * density
        val rect = floatArrayOf(Gdx.graphics.width - size - 24f * density, Gdx.graphics.height - size - 24f * density, size, size)
        val visible = !world.story.dialogueActive && !showMap && !showInventory && !showJournal && !showCraft
        input.dodgeRect = rect.takeIf { visible }
        if (!visible) return
        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        Gdx.gl.glBlendFunc(GL20.GL_SRC_ALPHA, GL20.GL_ONE_MINUS_SRC_ALPHA)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        shapes.color = Color(0.04f, 0.12f, 0.23f, 0.7f)
        shapes.rect(rect[0], rect[1], rect[2], rect[3])
        shapes.end()
        batch.projectionMatrix = camera.combined
        batch.begin()
        val label = data.pack.text(language, "\$i18n:ui.dodge")
        layout.setText(font, label)
        font.color = Color.WHITE
        font.draw(batch, label, rect[0] + (size - layout.width) / 2f, rect[1] + (size - font.lineHeight) / 2f)
        batch.end()
    }

    /**
     * Ren's Analyze, the eye of the system (key Z, or its button next to the dodge button): the nearest living creature within 10 tiles, with its
     * level, health, attack, defense and what it can drop (with the chance), in a panel at the top center for a few seconds. Presentation only.
     */
    private fun drawAnalyze(world: WorldSim, data: Assets) {
        val density = Gdx.graphics.density
        val size = 64f * density
        val button = floatArrayOf(Gdx.graphics.width - 84f * density - 24f * density - size - 12f * density, Gdx.graphics.height - size - 24f * density, size, size)
        val buttonVisible = hasAnalyze && !world.story.dialogueActive && !showMap && !showInventory && !showJournal && !showCraft
        analyzeRect = button.takeIf { buttonVisible }
        input.analyzeRect = analyzeRect
        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        Gdx.gl.glBlendFunc(GL20.GL_SRC_ALPHA, GL20.GL_ONE_MINUS_SRC_ALPHA)
        val lines = ArrayList<String>()
        if (analyzeFrames > 0 && buttonVisible) {
            analyzeFrames--
            val px = world.player.position.x
            val py = world.player.position.y
            val target = world.enemies.filter { it.state != EnemyState.DEAD }
                .filter { (it.position.x - px) * (it.position.x - px) + (it.position.y - py) * (it.position.y - py) < 100f }
                .minByOrNull { (it.position.x - px) * (it.position.x - px) + (it.position.y - py) * (it.position.y - py) }
            if (target == null) {
                lines.add(data.pack.text(language, "\$i18n:ui.analyze_none"))
            } else {
                val def = target.def
                val last = def.id.substringAfterLast('/')
                lines.add(data.pack.text(language, "\$i18n:ui.analyze_title", mapOf("name" to data.pack.text(language, "\$i18n:enemy.$last.name"), "level" to def.level)))
                lines.add(data.pack.text(language, "\$i18n:ui.analyze_stats", mapOf("hp" to target.hp, "max" to def.hp, "atk" to def.atk, "def" to def.def)))
                val items = def.drops.joinToString(", ") {
                    data.pack.text(language, "\$i18n:item.${it.item.substringAfterLast('/')}.name", mapOf("count" to 1)) + " " + (it.weightPm / 10) + "%"
                }
                if (items.isNotEmpty()) lines.add(data.pack.text(language, "\$i18n:ui.analyze_drops", mapOf("items" to items)))
            }
        }
        var panelW = 0f
        for (line in lines) {
            layout.setText(font, line)
            panelW = max(panelW, layout.width)
        }
        panelW += 24f * density
        val panelH = lines.size * font.lineHeight * 1.3f + 16f * density
        val panelX = (Gdx.graphics.width - panelW) / 2f
        val panelY = 12f * density
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        if (buttonVisible) {
            shapes.color = Color(0.04f, 0.12f, 0.23f, 0.7f)
            shapes.rect(button[0], button[1], button[2], button[3])
        }
        if (lines.isNotEmpty()) {
            shapes.color = Color(0.435f, 0.89f, 1f, 1f)
            shapes.rect(panelX - 2f, panelY - 2f, panelW + 4f, panelH + 4f)
            shapes.color = Color(0.043f, 0.12f, 0.227f, 0.92f)
            shapes.rect(panelX, panelY, panelW, panelH)
        }
        shapes.end()
        batch.projectionMatrix = camera.combined
        batch.begin()
        if (buttonVisible) {
            val label = data.pack.text(language, "\$i18n:ui.analyze_btn")
            layout.setText(font, label)
            font.color = Color.WHITE
            font.draw(batch, label, button[0] + (size - layout.width) / 2f, button[1] + (size - font.lineHeight) / 2f)
        }
        for ((i, line) in lines.withIndex()) {
            font.color = if (i == 0) Color(1f, 0.84f, 0.47f, 1f) else Color(0.92f, 0.96f, 1f, 1f)
            font.draw(batch, line, panelX + 12f * density, panelY + 8f * density + i * font.lineHeight * 1.3f)
        }
        font.color = Color.WHITE
        batch.end()
    }

    /** Text over the world with a dark edge, in the current color of the font. */
    private fun hudText(text: String, x: Float, y: Float) = mapText(text, x, y, Color(font.color))

    /** An arrow around the player, toward the goal, when it is far (spec 09, "The map view"). */
    private fun drawGoalArrow(world: WorldSim, camX: Float, camY: Float, tile: Float) {
        if (!hasGoal || world.chunks == null || showMap) return
        val ddx = goalX - world.player.position.x
        val ddy = goalY - world.player.position.y
        val dist = kotlin.math.sqrt(ddx * ddx + ddy * ddy)
        if (dist <= 12f) return
        val ux = ddx / dist
        val uy = ddy / dist
        val ox = (world.player.position.x - camX) * tile
        val oy = (world.player.position.y - camY) * tile - 0.6f * tile
        val tipX = ox + ux * 2.7f * tile
        val tipY = oy + uy * 2.7f * tile
        val baseX = ox + ux * 1.9f * tile
        val baseY = oy + uy * 1.9f * tile
        val barb = 0.4f * tile
        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        Gdx.gl.glBlendFunc(GL20.GL_SRC_ALPHA, GL20.GL_ONE_MINUS_SRC_ALPHA)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        for (pass in 0..1) { // a dark edge first, then the arrow
            shapes.color = if (pass == 0) Color(0f, 0f, 0f, 0.9f) else Color(0.35f, 1f, 0.47f, 0.95f)
            val width = (if (pass == 0) 4f else 2.5f) * Gdx.graphics.density
            shapes.rectLine(baseX, baseY, tipX, tipY, width)
            for (angle in floatArrayOf(2.6f, -2.6f)) {
                val bx = (ux * kotlin.math.cos(angle) - uy * kotlin.math.sin(angle)) * barb
                val by = (ux * kotlin.math.sin(angle) + uy * kotlin.math.cos(angle)) * barb
                shapes.rectLine(tipX, tipY, tipX + bx, tipY + by, width)
            }
        }
        shapes.end()
    }

    /** Moves the view to the next place found (settlements, dungeons, lairs), nearest to the player first, and says its name. */
    private fun mapNextPlace(world: WorldSim) {
        val store = world.chunks ?: return
        val px = world.player.position.x
        val py = world.player.position.y
        val places = world.explored.mapNotNull { (x, y) -> markerAt(store, x, y) }
            .sortedWith(compareBy({ (it.px - px) * (it.px - px) + (it.py - py) * (it.py - py) }, { it.name }))
        if (places.isEmpty()) return
        mapPick = (mapPick + 1) % places.size
        val place = places[mapPick]
        mapCx = place.px.toFloat() / MAP_CELL
        mapCy = place.py.toFloat() / MAP_CELL
        showNotice(place.name)
    }

    /** Text on the map with a dark edge, so that it reads on pale cells too. */
    private fun mapText(text: String, x: Float, y: Float, color: Color) {
        font.color = Color(0f, 0f, 0f, 0.9f)
        font.draw(batch, text, x + 1f, y + 1f)
        font.color = color
        font.draw(batch, text, x, y)
    }

    private fun mapCenterOnPlayer(world: WorldSim) {
        mapCx = world.player.position.x / MAP_CELL
        mapCy = world.player.position.y / MAP_CELL
    }

    /** The map button and, when open, the world map: explored cells by biome, the places that were found and the player (spec 09). */
    private fun drawWorldMap(world: WorldSim, data: Assets) {
        val store = world.chunks ?: return
        val density = Gdx.graphics.density
        val width = Gdx.graphics.width.toFloat()
        val height = Gdx.graphics.height.toFloat()
        val button = floatArrayOf(12f * density + 104f * density, 74f * density, 96f * density, 34f * density)
        mapRect = button

        // Geometry of the view: a square, with the keys, the position and the buttons beside it (wide screens) or under it.
        val landscape = width > height
        val columns = (store.params.width + MAP_CELL - 1) / MAP_CELL
        val rows = (store.params.height + MAP_CELL - 1) / MAP_CELL
        var view: MapView? = null
        val buttons = ArrayList<MapButton>()
        var panelX = 0f
        var panelY = 0f
        var panelW = 0f
        if (showMap) {
            val side = if (landscape) min(width * 0.55f, height * 0.8f) else min(width * 0.92f, height * 0.58f)
            val vx = if (landscape) 24f * density else (width - side) / 2f
            val vy = if (landscape) (height - side) / 2f + 10f * density else 64f * density
            if (mapLevel < 0) mapFit(world, columns, rows, side)
            val cell = side / max(columns, rows) * (1 shl mapLevel)
            view = MapView(vx, vy, side, cell, mapCx, mapCy)
            mapCellPx = cell
            mapViewCells = side / cell
            panelX = if (landscape) vx + side + 20f * density else vx
            panelY = if (landscape) vy else vy + side + 8f * density
            panelW = if (landscape) width - panelX - 16f * density else side
        }

        // The text under (or beside) the view, measured first because the buttons come after it.
        val help = data.pack.text(language, "\$i18n:ui.map_help_touch")
        val where = data.pack.text(
            language, "\$i18n:ui.map_pos",
            mapOf("x" to floor(world.player.position.x).toInt(), "y" to floor(world.player.position.y).toInt(), "zoom" to (1 shl max(mapLevel, 0))),
        )
        var buttonsY = 0f
        if (view != null) {
            layout.setText(font, help, Color.WHITE, panelW, 0, true)
            val helpH = layout.height
            val legendY = panelY + helpH + font.lineHeight * 2.2f
            buttonsY = legendY + font.lineHeight * 1.8f
            val size = 48f * density
            val gap = 8f * density
            val labels = listOf("+" to 0, "-" to 1, data.pack.text(language, "\$i18n:ui.map_btn_you") to 2, data.pack.text(language, "\$i18n:ui.map_btn_all") to 3, data.pack.text(language, "\$i18n:ui.map_btn_goal") to 5, data.pack.text(language, "\$i18n:ui.map_btn_next") to 6, "X" to 4)
            var bx = panelX
            var by = buttonsY
            for ((label, action) in labels) {
                layout.setText(font, label)
                val w = max(size, layout.width + 20f * density)
                if (bx + w > panelX + panelW && bx > panelX) {
                    bx = panelX
                    by += size + gap
                }
                buttons.add(MapButton(floatArrayOf(bx, by, w, size), action, label))
                bx += w + gap
            }
        }
        mapButtons = buttons

        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        Gdx.gl.glBlendFunc(GL20.GL_SRC_ALPHA, GL20.GL_ONE_MINUS_SRC_ALPHA)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        shapes.color = Color(0.04f, 0.12f, 0.23f, 0.8f)
        shapes.rect(button[0], button[1], button[2], button[3])
        val shown = ArrayList<Pair<io.github.progliodario.aethermoor.core.Settlement, FloatArray>>() // each marker with its box (x, y, w, h)
        if (view != null) {
            val v = view
            fun clipped(x: Float, y: Float, w: Float, h: Float) {
                val x0 = max(x, v.x)
                val y0 = max(y, v.y)
                val x1 = min(x + w, v.x + v.side)
                val y1 = min(y + h, v.y + v.side)
                if (x1 > x0 && y1 > y0) shapes.rect(x0, y0, x1 - x0, y1 - y0)
            }
            shapes.color = Color(0.016f, 0.04f, 0.094f, 0.92f)
            shapes.rect(0f, 0f, width, height)
            shapes.color = Color(0.16f, 0.27f, 0.43f, 1f)
            shapes.rect(v.x - 3f, v.y - 3f, v.side + 6f, v.side + 6f)
            shapes.color = Color(0.024f, 0.047f, 0.11f, 1f)
            shapes.rect(v.x, v.y, v.side, v.side) // beyond the edge of the world
            shapes.color = Color(0.08f, 0.14f, 0.26f, 1f)
            clipped(v.toX(0f), v.toY(0f), v.cell * columns, v.cell * rows) // the world, still unexplored
            // A cell is drawn as a grid of n x n sampled tiles (n = 1, 2, 4, 8, 16 from level 1), so that the squares stay about
            // 4 or 5 pixels whatever the zoom: the shape of coasts, mountains and deserts shows when the map is zoomed in.
            val n = if (mapLevel <= 0) 1 else 1 shl mapLevel
            if (mapDetail.size > 6000) mapDetail.clear()
            for ((x, y) in world.explored) {
                val sx = v.toX(x.toFloat())
                val sy = v.toY(y.toFloat())
                if (sx > v.x + v.side || sy > v.y + v.side || sx + v.cell < v.x || sy + v.cell < v.y) continue
                if (n == 1) {
                    val code = mapCodes.getOrPut(Pair(x, y)) { biomeCode(store.seed, store.params, x, y) }
                    shapes.color = MAP_COLORS[code]
                    clipped(sx, sy, ceil(v.cell), ceil(v.cell))
                    continue
                }
                val codes = mapDetail.getOrPut(Triple(x, y, n)) {
                    ByteArray(n * n) { k ->
                        val i = k % n
                        val j = k / n
                        biomeCodeAt(store.seed, store.params, x * MAP_CELL + (2 * i + 1) * MAP_CELL / (2 * n), y * MAP_CELL + (2 * j + 1) * MAP_CELL / (2 * n)).toByte()
                    }
                }
                val sub = v.cell / n
                for (j in 0 until n) {
                    for (i in 0 until n) {
                        shapes.color = MAP_COLORS[codes[j * n + i].toInt()]
                        clipped(sx + sub * i, sy + sub * j, ceil(sub), ceil(sub))
                    }
                }
            }
            val boost = 1f + 0.4f * mapLevel
            for ((x, y) in world.explored) {
                val mx = v.toX(x + 0.5f)
                val my = v.toY(y + 0.5f)
                if (mx < v.x || my < v.y || mx > v.x + v.side || my > v.y + v.side) continue
                val marker = markerAt(store, x, y) ?: continue
                val place = marker.kind == "town" || marker.kind == "village" || marker.kind == "hamlet"
                val size = (if (marker.kind == "town") 7f else if (marker.kind == "village") 5f else 4f) * density * boost
                shapes.color = Color(0.08f, 0.08f, 0.12f, 1f)
                clipped(mx - size / 2f - 1f, my - size / 2f - 1f, size + 2f, size + 2f)
                shapes.color = if (place) Color(1f, 0.92f, 0.59f, 1f) else Color(0.8f, 0.47f, 1f, 1f)
                clipped(mx - size / 2f, my - size / 2f, size, size)
                shown.add(Pair(marker, floatArrayOf(mx - size / 2f - 1f, my - size / 2f - 1f, size + 2f, size + 2f)))
            }
            // The Threshold Stones that were woken: small pale squares.
            for ((stoneX, stoneY) in world.stones) {
                val sx = v.toX(stoneX.toFloat() / MAP_CELL)
                val sy = v.toY(stoneY.toFloat() / MAP_CELL)
                val ss = 5f * density
                shapes.color = Color(0.08f, 0.08f, 0.12f, 1f)
                clipped(sx - ss / 2f - 1f, sy - ss / 2f - 1f, ss + 2f, ss + 2f)
                shapes.color = Color(0.55f, 1f, 0.92f, 1f)
                clipped(sx - ss / 2f, sy - ss / 2f, ss, ss)
            }
            // The player: a red square with a white edge, kept on the edge of the view when it is out of it.
            val px = v.toX(world.player.position.x / MAP_CELL)
            val py = v.toY(world.player.position.y / MAP_CELL)
            val margin = 8f * density
            val off = px < v.x || py < v.y || px > v.x + v.side || py > v.y + v.side
            val dx = px.coerceIn(v.x + margin, v.x + v.side - margin)
            val dy = py.coerceIn(v.y + margin, v.y + v.side - margin)
            val pulse = 1f + 0.25f * kotlin.math.sin(System.nanoTime() / 1.8e8f)
            val ps = 7f * density * pulse
            shapes.color = Color.WHITE
            shapes.rect(dx - ps / 2f - 2f, dy - ps / 2f - 2f, ps + 4f, ps + 4f)
            shapes.color = if (off) Color(1f, 0.59f, 0.16f, 1f) else Color(1f, 0.2f, 0.2f, 1f)
            shapes.rect(dx - ps / 2f, dy - ps / 2f, ps, ps)
            if (hasGoal) { // the goal: a green square, and a line from the player, both kept inside the view
                val gx = v.toX(goalX / MAP_CELL).coerceIn(v.x + margin, v.x + v.side - margin)
                val gy = v.toY(goalY / MAP_CELL).coerceIn(v.y + margin, v.y + v.side - margin)
                shapes.color = Color(0.35f, 1f, 0.47f, 0.8f)
                shapes.rectLine(dx, dy, gx, gy, 2f * density)
                shapes.color = Color(0.08f, 0.08f, 0.12f, 1f)
                shapes.rect(gx - 5f * density - 2f, gy - 5f * density - 2f, 10f * density + 4f, 10f * density + 4f)
                shapes.color = Color(0.35f, 1f, 0.47f, 1f)
                shapes.rect(gx - 5f * density, gy - 5f * density, 10f * density, 10f * density)
            }
            // The legend: what the colors mean.
            var lx = panelX
            for (b in buttons) {
                shapes.color = Color(0.04f, 0.12f, 0.23f, 0.9f)
                shapes.rect(b.rect[0], b.rect[1], b.rect[2], b.rect[3])
            }
            val legendY = buttonsY - font.lineHeight * 1.8f
            val squares = listOf(Color(1f, 0.2f, 0.2f, 1f), Color(1f, 0.92f, 0.59f, 1f), Color(0.8f, 0.47f, 1f, 1f), Color(0.55f, 1f, 0.92f, 1f), Color(0.35f, 1f, 0.47f, 1f))
            val keys = listOf("\$i18n:ui.map_key_you", "\$i18n:ui.map_key_place", "\$i18n:ui.map_key_site", "\$i18n:ui.map_key_stone", "\$i18n:ui.map_key_goal")
            for (i in squares.indices) {
                shapes.color = squares[i]
                shapes.rect(lx, legendY + font.lineHeight * 0.15f, font.lineHeight * 0.7f, font.lineHeight * 0.7f)
                layout.setText(font, data.pack.text(language, keys[i]))
                lx += font.lineHeight + layout.width + 14f * density
            }
        }
        shapes.end()
        batch.projectionMatrix = camera.combined
        batch.begin()
        font.color = Color.WHITE
        font.draw(batch, data.pack.text(language, "\$i18n:ui.map_hint"), button[0] + 8f * density, button[1] + (button[3] - font.lineHeight) / 2f)
        if (view != null) {
            val v = view
            font.draw(batch, data.pack.text(language, "\$i18n:ui.map"), v.x, v.y - 30f * density)
            // A name goes to the first free side of its marker (right, left, below, above): in the view, over no other marker or name.
            // Towns first, then villages, the other sites, hamlets (from level 3).
            val order = shown.filter { it.first.kind != "hamlet" || mapLevel >= 3 }
                .sortedBy { (marker, _) -> when (marker.kind) { "town" -> 0; "village" -> 1; "hamlet" -> 3; else -> 2 } }
            val obstacles = ArrayList<FloatArray>()
            for ((_, box) in shown) obstacles.add(box)
            val lineH = font.lineHeight
            fun free(c: FloatArray, own: FloatArray?): Boolean =
                c[0] >= v.x && c[0] + c[2] <= v.x + v.side && c[1] >= v.y && c[1] + c[3] <= v.y + v.side &&
                    obstacles.none { it !== own && c[0] < it[0] + it[2] && it[0] < c[0] + c[2] && c[1] < it[1] + it[3] && it[1] < c[1] + c[3] }
            for ((marker, m) in order) {
                layout.setText(font, marker.name)
                val w = layout.width
                val cx = m[0] + m[2] / 2f
                val spot = listOf(
                    floatArrayOf(m[0] + m[2] + 3f * density, m[1] + m[3] / 2f - lineH / 2f, w, lineH),
                    floatArrayOf(m[0] - 3f * density - w, m[1] + m[3] / 2f - lineH / 2f, w, lineH),
                    floatArrayOf(cx - w / 2f, m[1] + m[3] + 2f * density, w, lineH),
                    floatArrayOf(cx - w / 2f, m[1] - 2f * density - lineH, w, lineH),
                ).firstOrNull { free(it, m) } ?: continue
                obstacles.add(spot)
                mapText(marker.name, spot[0], spot[1], Color.WHITE)
            }
            for (region in store.params.regions) {
                val rx = (region.xPm.toLong() * store.params.width / 1000).toInt() / MAP_CELL
                val ry = (region.yPm.toLong() * store.params.height / 1000).toInt() / MAP_CELL
                if (Pair(rx, ry) !in world.explored) continue
                val name = data.pack.text(language, region.name)
                layout.setText(font, name)
                val w = layout.width
                val cx = v.toX(rx.toFloat())
                val cy = v.toY(ry.toFloat())
                // In gold, below the center of the region, or above it, or on it.
                val spot = listOf(
                    floatArrayOf(cx - w / 2f, cy + 14f * density, w, lineH),
                    floatArrayOf(cx - w / 2f, cy - 14f * density - lineH, w, lineH),
                    floatArrayOf(cx - w / 2f, cy - lineH / 2f, w, lineH),
                ).firstOrNull { free(it, null) } ?: continue
                obstacles.add(spot)
                mapText(name, spot[0], spot[1], Color(1f, 0.84f, 0.47f, 1f))
            }
            font.color = Color(0.59f, 0.78f, 1f, 1f)
            layout.setText(font, help, font.color, panelW, 0, true)
            font.draw(batch, layout, panelX, panelY)
            font.color = Color.WHITE
            font.draw(batch, where, panelX, panelY + layout.height + font.lineHeight * 0.6f)
            // The words of the legend, after the squares drawn above.
            var lx = panelX
            val legendY = buttonsY - font.lineHeight * 1.8f
            val keys = listOf("\$i18n:ui.map_key_you", "\$i18n:ui.map_key_place", "\$i18n:ui.map_key_site", "\$i18n:ui.map_key_stone", "\$i18n:ui.map_key_goal")
            font.color = Color(0.86f, 0.86f, 0.9f, 1f)
            for (key in keys) {
                val label = data.pack.text(language, key)
                layout.setText(font, label)
                font.draw(batch, label, lx + font.lineHeight, legendY)
                lx += font.lineHeight + layout.width + 14f * density
            }
            font.color = Color.WHITE
            for (b in buttons) {
                layout.setText(font, b.label)
                font.draw(batch, b.label, b.rect[0] + (b.rect[2] - layout.width) / 2f, b.rect[1] + (b.rect[3] - font.lineHeight) / 2f)
            }
        }
        batch.end()
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
        val listCursor = bagCursor.coerceIn(0, max(items.size - 1, 0))
        val maxRows = max(3, ((height - 140f * density) / rowH).toInt() - 2) // a long list scrolls with the cursor
        val visible = min(items.size, maxRows)
        val first = listWindow(items.size, listCursor, maxRows)
        val panelH = 56f * density + rowH * max(visible, 1) + rowH * 2f
        val panelX = (width - panelW) / 2f
        val panelY = (height - panelH) / 2f
        val firstRowY = panelY + 14f * density + rowH + 6f * density
        bagRowRects = if (showInventory) items.indices.map { if (it in first until first + visible) floatArrayOf(panelX, firstRowY + (it - first) * rowH, panelW, rowH) else OFF_SCREEN } else emptyList()

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
            val cursor = bagCursor.coerceIn(0, max(items.size - 1, 0))
            var selectedKey = ""
            for ((index, entry) in items.withIndex()) {
                if (index < first || index >= first + visible) continue
                val (itemId, quantity) = entry
                // "base:item/slime_gel" -> text key "item.slime_gel.name"
                val key = itemId.substringAfter(':').replace('/', '.')
                val name = data.pack.text(language, "\$i18n:$key.name", mapOf("count" to quantity))
                val worn = if (itemId == world.equippedWeapon || itemId == world.equippedArmor) "  " + data.pack.text(language, "\$i18n:ui.worn") else ""
                if (index == cursor) {
                    selectedKey = key
                    font.color = Color.WHITE
                    font.draw(batch, ">  $name  x$quantity$worn", panelX + 16f * density, ty)
                    font.color = Color(0.92f, 0.96f, 1f, 1f)
                } else {
                    font.draw(batch, "    $name  x$quantity$worn", panelX + 16f * density, ty)
                }
                ty += rowH
            }
            if (selectedKey.isNotEmpty()) {
                font.color = Color(0.67f, 0.78f, 0.9f, 1f)
                font.draw(batch, data.pack.text(language, "\$i18n:$selectedKey.desc"), panelX + 16f * density, ty + 6f * density)
                font.draw(batch, data.pack.text(language, "\$i18n:ui.bag_use_hint"), panelX + 16f * density, ty + 6f * density + rowH)
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

    /** The title screen (spec 12, "Slots"): a tap or Enter on a game plays it, the cross or D deletes it after a second confirmation. */
    private fun handleTitleInput(data: Assets, slots: List<SlotSummary>) {
        val input = Gdx.input
        if (input.isKeyJustPressed(Input.Keys.UP) || input.isKeyJustPressed(Input.Keys.W)) {
            titleCursor = (titleCursor + SLOT_COUNT - 1) % SLOT_COUNT
            titlePendingDelete = -1
            titleNotice = ""
        } else if (input.isKeyJustPressed(Input.Keys.DOWN) || input.isKeyJustPressed(Input.Keys.S)) {
            titleCursor = (titleCursor + 1) % SLOT_COUNT
            titlePendingDelete = -1
            titleNotice = ""
        } else if (input.isKeyJustPressed(Input.Keys.ENTER) || input.isKeyJustPressed(Input.Keys.E) || input.isKeyJustPressed(Input.Keys.SPACE)) {
            selectSlot(titleCursor + 1)
        } else if (input.isKeyJustPressed(Input.Keys.D) || input.isKeyJustPressed(Input.Keys.FORWARD_DEL)) {
            deleteOrAsk(data, slots, titleCursor)
        } else if (input.justTouched()) {
            val x = input.x.toFloat()
            val y = input.y.toFloat()
            fun inside(r: FloatArray) = r.size == 4 && x >= r[0] && x <= r[0] + r[2] && y >= r[1] && y <= r[1] + r[3]
            val cross = titleCrossRects.indexOfFirst { inside(it) }
            val row = titleRowRects.indexOfFirst { inside(it) }
            if (cross >= 0) {
                titleCursor = cross
                deleteOrAsk(data, slots, cross)
            } else if (row >= 0) {
                selectSlot(row + 1)
            }
        }
    }

    private fun protagonistFile(slot: Int) = Gdx.files.local("saves/slot$slot/protagonist.txt")

    /** The protagonist kept in the folder of a game, if it still exists in the pack. */
    private fun keptProtagonist(slot: Int): String? {
        val file = protagonistFile(slot)
        if (!file.exists()) return null
        val id = file.readString("UTF-8").trim()
        return id.takeIf { assets?.pack?.documentPaths?.containsKey(it) == true }
    }

    /** The protagonists that can be chosen: Ren first, the others in the order of their IDs. */
    private fun availableProtagonists(pack: Pack): List<String> =
        pack.documentPaths.keys.filter { it.startsWith("base:protagonist/") }
            .filter { id -> pack.readDocument(id)?.let { parseProtagonist(it).getOrNull()?.initiallyAvailable } ?: false }
            .sortedWith(compareBy({ it != PROTAGONIST_ID }, { it }))

    /** A tap on a game: a game that exists (or has a protagonist) is played; a new one first asks who to be (spec 18). */
    private fun selectSlot(slot: Int) {
        val loaded = assets ?: return
        if (protagonistFile(slot).exists() || slotFile(slot).exists()) {
            startGame(slot)
            return
        }
        val ids = availableProtagonists(loaded.pack)
        if (ids.size <= 1) {
            startGame(slot)
            return
        }
        chooserIds = ids
        chooserCursor = 0
        chooserSlot = slot
    }

    /** The screen where a protagonist is chosen: a tap on a name selects it, a tap on the selected one (or Enter) confirms, Back returns to the games. */
    private fun handleChooserInput(data: Assets) {
        val input = Gdx.input
        if (input.isKeyJustPressed(Input.Keys.BACK) || input.isKeyJustPressed(Input.Keys.ESCAPE)) {
            chooserSlot = 0
            return
        }
        val count = chooserIds.size
        if (input.isKeyJustPressed(Input.Keys.UP) || input.isKeyJustPressed(Input.Keys.W)) {
            chooserCursor = (chooserCursor + count - 1) % count
        } else if (input.isKeyJustPressed(Input.Keys.DOWN) || input.isKeyJustPressed(Input.Keys.S)) {
            chooserCursor = (chooserCursor + 1) % count
        } else if (input.isKeyJustPressed(Input.Keys.ENTER) || input.isKeyJustPressed(Input.Keys.E) || input.isKeyJustPressed(Input.Keys.SPACE)) {
            confirmProtagonist()
        } else if (input.justTouched()) {
            val x = input.x.toFloat()
            val y = input.y.toFloat()
            val row = chooserRowRects.indexOfFirst { x >= it[0] && x <= it[0] + it[2] && y >= it[1] && y <= it[1] + it[3] }
            if (row == chooserCursor) confirmProtagonist() else if (row >= 0) chooserCursor = row
        }
    }

    private fun confirmProtagonist() {
        val slot = chooserSlot
        val id = chooserIds.getOrNull(chooserCursor) ?: return
        runCatching { protagonistFile(slot).writeString(id + "\n", false, "UTF-8") }
        chooserSlot = 0
        startGame(slot)
    }

    private fun protagonistKey(id: String, what: String) = "\$i18n:protagonist.${id.substringAfterLast('/')}.$what"

    private fun drawChooser(data: Assets) {
        val density = Gdx.graphics.density
        val width = Gdx.graphics.width.toFloat()
        val height = Gdx.graphics.height.toFloat()
        val rowH = 44f * density
        val gap = 6f * density
        val rowsTop = 64f * density
        val rects = ArrayList<FloatArray>()
        shapes.projectionMatrix = camera.combined
        Gdx.gl.glEnable(GL20.GL_BLEND)
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        shapes.color = Color(0.043f, 0.122f, 0.227f, 1f)
        shapes.rect(0f, 0f, width, height)
        for (i in chooserIds.indices) {
            val rowY = rowsTop + i * (rowH + gap)
            rects.add(floatArrayOf(20f * density, rowY, width - 40f * density, rowH))
            shapes.color = if (i == chooserCursor) Color(0.118f, 0.275f, 0.47f, 1f) else Color(0.078f, 0.196f, 0.353f, 1f)
            shapes.rect(20f * density, rowY, width - 40f * density, rowH)
            if (i == chooserCursor) {
                shapes.color = Color(1f, 0.84f, 0.47f, 1f)
                shapes.rect(20f * density, rowY, width - 40f * density, 3f)
            }
        }
        chooserRowRects = rects
        shapes.end()
        batch.projectionMatrix = camera.combined
        batch.begin()
        font.color = Color(1f, 0.84f, 0.47f, 1f)
        font.draw(batch, data.pack.text(language, "\$i18n:ui.protagonist_choose"), 20f * density, 20f * density)
        for (i in chooserIds.indices) {
            font.color = if (i == chooserCursor) Color.WHITE else Color(0.78f, 0.84f, 0.9f, 1f)
            font.draw(batch, "${i + 1}. " + data.pack.text(language, protagonistKey(chooserIds[i], "name")), 32f * density, rowsTop + i * (rowH + gap) + (rowH - font.lineHeight) / 2f)
        }
        var ty = rowsTop + chooserIds.size * (rowH + gap) + 14f * density
        val id = chooserIds[chooserCursor]
        val textW = width - 40f * density
        fun paragraph(text: String, color: Color) {
            font.color = color
            layout.setText(font, text, color, textW, 0, true)
            font.draw(batch, layout, 20f * density, ty)
            ty += layout.height + 8f * density
        }
        paragraph(data.pack.text(language, protagonistKey(id, "tagline")), Color(0.67f, 0.78f, 0.9f, 1f))
        paragraph(data.pack.text(language, "\$i18n:ui.protagonist_gift"), Color(1f, 0.84f, 0.47f, 1f))
        paragraph(data.pack.text(language, protagonistKey(id, "gift")), Color(0.92f, 0.96f, 1f, 1f))
        paragraph(data.pack.text(language, "\$i18n:ui.protagonist_story"), Color(1f, 0.84f, 0.47f, 1f))
        paragraph(data.pack.text(language, protagonistKey(id, "story")), Color(0.92f, 0.96f, 1f, 1f))
        font.color = Color(0.67f, 0.78f, 0.9f, 1f)
        font.draw(batch, data.pack.text(language, "\$i18n:ui.protagonist_hint_touch"), 20f * density, height - 36f * density)
        font.color = Color.WHITE
        batch.end()
    }

    /** First call on a used game asks to confirm; a second call on the same game deletes its files. */
    private fun deleteOrAsk(data: Assets, slots: List<SlotSummary>, index: Int) {
        if (!slots[index].used) return
        val args = mapOf<String, Any>("slot" to index + 1)
        if (titlePendingDelete == index) {
            deleteSlot(index + 1)
            titlePendingDelete = -1
            titleSlots = readSlots()
            titleNotice = data.pack.text(language, "\$i18n:ui.slot_deleted", args)
        } else {
            titlePendingDelete = index
            titleNotice = data.pack.text(language, "\$i18n:ui.slot_delete_touch", args)
        }
    }

    private fun drawTitle(data: Assets, slots: List<SlotSummary>) {
        val density = Gdx.graphics.density
        val width = Gdx.graphics.width.toFloat()
        val height = Gdx.graphics.height.toFloat()
        val panelW = min(width - 40f, 560f * density)
        val panelX = (width - panelW) / 2f
        val rowH = 56f * density
        val gap = 8f * density
        val top = height * 0.32f
        val rows = ArrayList<FloatArray>()
        val crosses = ArrayList<FloatArray>()
        for (i in slots.indices) {
            val rowY = top + i * (rowH + gap)
            rows.add(floatArrayOf(panelX, rowY, panelW, rowH))
            crosses.add(if (slots[i].used) floatArrayOf(panelX + panelW - rowH, rowY, rowH, rowH) else floatArrayOf())
        }
        titleRowRects = rows
        titleCrossRects = crosses

        shapes.projectionMatrix = camera.combined
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        for (i in slots.indices) {
            val r = rows[i]
            shapes.color = if (i == titleCursor) Color(0.118f, 0.275f, 0.47f, 1f) else Color(0.078f, 0.196f, 0.353f, 1f)
            shapes.rect(r[0], r[1], r[2], r[3])
            if (i == titleCursor) {
                shapes.color = Color(1f, 0.84f, 0.47f, 1f)
                shapes.rect(r[0], r[1], r[2], 3f * density)
            }
            if (slots[i].used) {
                val c = crosses[i]
                shapes.color = if (titlePendingDelete == i) Color(0.7f, 0.2f, 0.2f, 1f) else Color(0.12f, 0.16f, 0.28f, 1f)
                shapes.rect(c[0] + 6f * density, c[1] + 6f * density, c[2] - 12f * density, c[3] - 12f * density)
            }
        }
        shapes.end()

        batch.projectionMatrix = camera.combined
        batch.begin()
        val baseScale = font.data.scaleX
        font.data.setScale(baseScale * 2f)
        val name = data.pack.text(language, "\$i18n:game.title")
        layout.setText(font, name)
        font.color = Color(1f, 0.84f, 0.47f, 1f)
        font.draw(batch, name, (width - layout.width) / 2f, height * 0.08f)
        font.data.setScale(baseScale)
        val choose = data.pack.text(language, "\$i18n:ui.title_choose")
        layout.setText(font, choose)
        font.color = Color(0.67f, 0.78f, 0.9f, 1f)
        font.draw(batch, choose, (width - layout.width) / 2f, height * 0.08f + 56f * density)
        for (i in slots.indices) {
            val r = rows[i]
            val slot = slots[i]
            val key = if (slot.used) "\$i18n:ui.slot_used" else "\$i18n:ui.slot_empty"
            val line = data.pack.text(language, key, mapOf("slot" to i + 1, "level" to slot.level, "gold" to slot.gold))
            font.color = if (slot.used) Color(0.92f, 0.96f, 1f, 1f) else Color(0.59f, 0.67f, 0.78f, 1f)
            font.draw(batch, line, r[0] + 16f * density, r[1] + (r[3] - font.lineHeight) / 2f)
            if (slot.used) {
                val c = crosses[i]
                font.color = Color.WHITE
                font.draw(batch, "x", c[0] + (c[2] - font.spaceXadvance) / 2f, c[1] + (c[3] - font.lineHeight) / 2f)
            }
        }
        if (titleNotice.isNotEmpty()) {
            font.color = Color(1f, 0.84f, 0.47f, 1f)
            font.draw(batch, titleNotice, panelX, top + SLOT_COUNT * (rowH + gap) + 8f * density)
        }
        font.color = Color(0.67f, 0.78f, 0.9f, 1f)
        font.draw(batch, data.pack.text(language, "\$i18n:ui.title_hint_touch"), panelX, height - font.lineHeight * 2.4f)
        font.color = Color.WHITE
        batch.end()
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
        sound.dispose()
    }

    companion object {
        private const val TAG = "Aethermoor"
        private const val PROTAGONIST_ID = "base:protagonist/ren"
        private const val MAP_WORLD = "world"
        private const val SLOT_COUNT = 3
        private const val BASE_TILE_PX = 48f

        /** Colors of the world map by biome code: water, beach, mountain, snow, desert, forest, plains. */
        private val MAP_COLORS = arrayOf(
            Color(0.235f, 0.431f, 0.745f, 1f), Color(0.871f, 0.808f, 0.588f, 1f), Color(0.51f, 0.51f, 0.549f, 1f),
            Color(0.922f, 0.941f, 0.961f, 1f), Color(0.871f, 0.808f, 0.588f, 1f), Color(0.235f, 0.51f, 0.275f, 1f),
            Color(0.431f, 0.706f, 0.353f, 1f),
        )
        /** The rectangle of a list row that is not on the screen: no tap can hit it. */
        private val OFF_SCREEN = floatArrayOf(-1f, -1f, 0f, 0f)
        private const val MAX_TICKS_PER_FRAME = 5
        private const val MAP_MAX_LEVEL = 4
        private val GOAL_DIRECTIONS = arrayOf("e", "se", "s", "sw", "w", "nw", "n", "ne")
        private const val MAX_FRAME_SECONDS = 0.25f
        private const val FLOATING_TEXT_FRAMES = 50
        private const val AUTOSAVE_SECONDS = 30f
    }
}
