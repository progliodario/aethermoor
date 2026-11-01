package io.github.progliodario.aethermoor.core

import io.github.progliodario.aethermoor.core.sim.PLAYER_RADIUS
import io.github.progliodario.aethermoor.core.sim.TileMap
import io.github.progliodario.aethermoor.core.sim.Tileset
import io.github.progliodario.aethermoor.core.sim.WorldSim
import io.github.progliodario.aethermoor.core.sim.parseTileMap
import io.github.progliodario.aethermoor.core.sim.parseTileset
import io.github.progliodario.aethermoor.core.vector.evaluatePose
import io.github.progliodario.aethermoor.core.vector.parseClip
import io.github.progliodario.aethermoor.core.vector.parseRecipe
import io.github.progliodario.aethermoor.core.vector.parseRig
import io.github.progliodario.aethermoor.core.vector.rasterize
import java.io.File
import kotlin.math.abs
import kotlin.math.sqrt
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

/** Tests for tile maps, the world simulation and the rig, on the real demo data (mirror of sim_test.cpp). */
class WorldTest {
    private val repoRoot = File(System.getProperty("aether.repoRoot") ?: error("aether.repoRoot is not set"))
    private val pack = loadBasePack(repoRoot)
    private val map: TileMap = parseTileMap(requireNotNull(pack.readFile("maps/demo.tmj"))).getOrThrow()
    private val tileset: Tileset = parseTileset(requireNotNull(pack.readDocument("base:tileset/overworld"))).getOrThrow()

    private fun assertNear(expected: Float, actual: Float, tol: Float, message: String = "") {
        assertTrue(abs(expected - actual) <= tol, "$message expected $expected, got $actual")
    }

    @Test
    fun demoMapLoads() {
        assertEquals(40, map.width)
        assertEquals(30, map.height)
        assertEquals("base:tileset/overworld", map.tilesetId)
        assertEquals(1200, map.ground.size)
        assertNear(5.5f, map.spawnX, 0.0001f)
        assertNear(15.5f, map.spawnY, 0.0001f)
        assertTrue(map.props.isNotEmpty())
        assertEquals(14, tileset.tiles.size)
        assertEquals(5, map.gidAt(0, 0))
        assertEquals(0, map.gidAt(-1, 0))
    }

    @Test
    fun everyArtRecipeReferencedByTheDemoMapCanBeBaked() {
        val ids = tileset.tiles.values.map { it.art } + map.props.map { it.art }
        for (id in ids) {
            val recipe = parseRecipe(requireNotNull(pack.readDocument(id)) { "missing $id" }).getOrThrow()
            val bitmap = rasterize(recipe, 1f)
            assertTrue(bitmap.width > 0, id)
            var opaque = 0
            for (i in 3 until bitmap.rgba.size step 4) if (bitmap.rgba[i].toInt() != 0) opaque++
            assertTrue(opaque > 0, "$id renders nothing")
        }
    }

    @Test
    fun playerWalksIsBlockedByWallsAndKeepsConstantSpeedOnDiagonals() {
        val sim = WorldSim(map, tileset, 4f)
        val start = sim.player.position
        repeat(30) { sim.tick(1f, 0f) }
        assertNear(2f, sim.player.position.x - start.x, 0.01f, "walk right")
        assertTrue(sim.player.moving)
        assertFalse(sim.player.facingLeft)

        val diagonal = WorldSim(map, tileset, 4f)
        diagonal.tick(1f, 1f)
        val dx = diagonal.player.position.x - map.spawnX
        val dy = diagonal.player.position.y - map.spawnY
        assertNear(4f / 60f, sqrt(dx * dx + dy * dy), 0.0005f, "diagonal speed")

        val wall = WorldSim(map, tileset, 4f)
        repeat(400) { wall.tick(-1f, 0f) }
        assertNear(1f + PLAYER_RADIUS, wall.player.position.x, 0.01f, "wall")
        assertTrue(wall.player.facingLeft)
    }

    @Test
    fun animationStateFollowsMovement() {
        val sim = WorldSim(map, tileset, 4f)
        assertFalse(sim.player.moving)
        sim.tick(0f, 0f)
        sim.tick(0f, 0f)
        assertEquals(2, sim.player.clipTick)
        sim.tick(0f, -1f)
        assertTrue(sim.player.moving)
        assertEquals(0, sim.player.clipTick)
        sim.tick(0f, -1f)
        assertEquals(1, sim.player.clipTick)
    }

    @Test
    fun cameraIsClampedToTheMapAndCenteredWhenTheMapIsSmallerThanTheView() {
        val sim = WorldSim(map, tileset, 4f)
        assertNear(0f, sim.camera(20f, 12f).x, 0.0001f, "near edge")
        val huge = sim.camera(60f, 40f)
        assertNear(-10f, huge.x, 0.0001f, "centered x")
        assertNear(-5f, huge.y, 0.0001f, "centered y")
    }

    @Test
    fun rigOfTheDemoCharacterMirrorsCleanly() {
        val rig = parseRig(requireNotNull(pack.readDocument("base:art/rig/humanoid"))).getOrThrow()
        val walk = parseClip(requireNotNull(pack.readDocument("base:art/clip/humanoid_walk"))).getOrThrow()
        assertEquals(7, rig.parts.size)
        val pose = evaluatePose(rig, walk, 0f, false)
        val mirrored = evaluatePose(rig, walk, 0f, true)
        assertEquals(rig.parts.size, pose.size)
        for (i in pose.indices) {
            assertNear(-pose[i].x, mirrored[i].x, 0.0001f)
            assertNear(pose[i].y, mirrored[i].y, 0.0001f)
            assertNear(-pose[i].rotationDeg, mirrored[i].rotationDeg, 0.0001f)
        }
        assertNotNull(pack.readDocument("base:art/char/ren/head"))
    }
}
