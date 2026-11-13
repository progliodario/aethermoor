package io.github.progliodario.aethermoor.core

import io.github.progliodario.aethermoor.core.audio.parseSfx
import io.github.progliodario.aethermoor.core.audio.synthesize
import io.github.progliodario.aethermoor.core.sim.CollisionWorld
import io.github.progliodario.aethermoor.core.sim.Circle
import io.github.progliodario.aethermoor.core.sim.Vec2
import io.github.progliodario.aethermoor.core.sim.normalizeInput
import io.github.progliodario.aethermoor.core.vector.evaluatePose
import io.github.progliodario.aethermoor.core.vector.parseClip
import io.github.progliodario.aethermoor.core.vector.parseRecipe
import io.github.progliodario.aethermoor.core.vector.parseRig
import io.github.progliodario.aethermoor.core.vector.rasterize
import java.io.File
import kotlin.math.abs
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.double
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

/** Conformance suites added in M2: rig_pose, movement, raster. */
class ConformanceM2Test {
    private val repoRoot = File(System.getProperty("aether.repoRoot") ?: error("aether.repoRoot is not set"))

    private fun suite(name: String): JsonArray {
        val doc = Json.parseToJsonElement(File(repoRoot, "tests/conformance/$name.json").readText()).jsonObject
        assertEquals(name, doc.getValue("suite").jsonPrimitive.content)
        return doc.getValue("cases").jsonArray
    }

    private fun JsonElement.num(): Float = jsonPrimitive.double.toFloat()

    private fun assertNear(expected: Float, actual: Float, tol: Float, message: String) {
        assertTrue(abs(expected - actual) <= tol, "$message: expected $expected, got $actual (tol $tol)")
    }

    @Test
    fun rigPoseSuite() {
        for (case in suite("rig_pose")) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val input = c.getValue("input").jsonObject
            val expect = c.getValue("expect").jsonObject
            val rig = parseRig(input.getValue("rig").toString()).getOrThrow()
            val clip = parseClip(input.getValue("clip").toString()).getOrThrow()
            val pose = evaluatePose(rig, clip, input.getValue("tick").num(), input.getValue("mirror").jsonPrimitive.boolean, input["side"]?.jsonPrimitive?.boolean ?: false)
            val parts = expect.getValue("parts").jsonArray
            val tol = expect.getValue("tol").num()
            assertEquals(parts.size, pose.size, label)
            for (i in pose.indices) {
                val p = parts[i].jsonObject
                assertEquals(p.getValue("part").jsonPrimitive.content, rig.parts[pose[i].partIndex].id, "$label[$i] part")
                assertNear(p.getValue("x").num(), pose[i].x, tol, "$label[$i] x")
                assertNear(p.getValue("y").num(), pose[i].y, tol, "$label[$i] y")
                assertNear(p.getValue("rot").num(), pose[i].rotationDeg, tol, "$label[$i] rot")
                assertEquals(p.getValue("z").jsonPrimitive.int, pose[i].z, "$label[$i] z")
            }
        }
    }

    @Test
    fun movementSuite() {
        for (case in suite("movement")) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val input = c.getValue("input").jsonObject
            val expect = c.getValue("expect").jsonObject
            if (input.getValue("op").jsonPrimitive.content == "normalize_input") {
                val v = normalizeInput(input.getValue("x").num(), input.getValue("y").num())
                val tol = expect.getValue("tol").num()
                assertNear(expect.getValue("x").num(), v.x, tol, "$label x")
                assertNear(expect.getValue("y").num(), v.y, tol, "$label y")
                continue
            }
            val rows = input.getValue("grid").jsonArray.map { it.jsonPrimitive.content }
            val solid = BooleanArray(rows.size * rows[0].length) { rows[it / rows[0].length][it % rows[0].length] == '#' }
            val props = input.getValue("props").jsonArray.map { Circle(it.jsonArray[0].num(), it.jsonArray[1].num(), it.jsonArray[2].num()) }
            val world = CollisionWorld(rows[0].length, rows.size, solid, props)
            var position = Vec2(input.getValue("start").jsonArray[0].num(), input.getValue("start").jsonArray[1].num())
            val speed = input.getValue("speed").num()
            val tol = expect.getValue("tol").num()
            for ((segment, step) in input.getValue("script").jsonArray.withIndex()) {
                val s = step.jsonArray
                val direction = normalizeInput(s[0].num(), s[1].num())
                repeat(s[2].jsonPrimitive.int) { position = world.step(position, direction, speed) }
                val wanted = expect.getValue("positions").jsonArray[segment].jsonArray
                assertNear(wanted[0].num(), position.x, tol, "$label seg $segment x")
                assertNear(wanted[1].num(), position.y, tol, "$label seg $segment y")
            }
        }
    }

    @Test
    fun audioSuite() {
        for (case in suite("audio")) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val expect = c.getValue("expect").jsonObject
            val recipe = parseSfx(c.getValue("input").jsonObject.getValue("recipe").toString()).getOrThrow()
            val samples = synthesize(recipe)
            assertEquals(expect.getValue("samples").jsonPrimitive.int, samples.size, "$label samples")
            val peak = samples.maxOf { abs(it.toInt()) }
            assertTrue(abs(peak - expect.getValue("peak").jsonPrimitive.int) <= 2, "$label peak $peak")
            val mean = samples.sumOf { abs(it.toInt()).toDouble() } / samples.size
            val wanted = expect.getValue("mean_abs").jsonPrimitive.double
            assertTrue(abs(mean - wanted) <= maxOf(2.0, wanted * 0.01), "$label mean $mean expected $wanted")
            for (probeElement in expect.getValue("probes").jsonArray) {
                val probe = probeElement.jsonObject
                val i = probe.getValue("i").jsonPrimitive.int
                val value = probe.getValue("value").jsonPrimitive.int
                assertTrue(abs(samples[i].toInt() - value) <= 2, "$label sample $i: expected $value, got ${samples[i]}")
            }
        }
    }

    @Test
    fun rasterSuite() {
        for (case in suite("raster")) {
            val c = case.jsonObject
            val label = c.getValue("name").jsonPrimitive.content
            val input = c.getValue("input").jsonObject
            val expect = c.getValue("expect").jsonObject
            val recipe = parseRecipe(input.getValue("recipe").toString()).getOrThrow()
            val variantElement = input.getValue("variant")
            val variant = if (variantElement is JsonNull) null else variantElement.jsonPrimitive.content
            val bitmap = rasterize(recipe, input.getValue("scale").num(), variant)
            assertEquals(expect.getValue("width").jsonPrimitive.int, bitmap.width, "$label width")
            assertEquals(expect.getValue("height").jsonPrimitive.int, bitmap.height, "$label height")
            for (probeElement in expect.getValue("probes").jsonArray) {
                val probe = probeElement.jsonObject
                val x = probe.getValue("x").jsonPrimitive.int
                val y = probe.getValue("y").jsonPrimitive.int
                val tol = probe.getValue("tol").jsonPrimitive.int
                for (channel in 0 until 4) {
                    val wanted = probe.getValue("rgba").jsonArray[channel].jsonPrimitive.int
                    val actual = bitmap.channel(x, y, channel)
                    assertTrue(abs(actual - wanted) <= tol, "$label probe ($x,$y) channel $channel: expected $wanted, got $actual")
                }
            }
            expect["sum_alpha"]?.let { area ->
                var sum = 0.0
                for (i in 3 until bitmap.rgba.size step 4) sum += (bitmap.rgba[i].toInt() and 0xFF) / 255.0
                val wanted = area.jsonObject.getValue("value").jsonPrimitive.double
                val relTol = area.jsonObject.getValue("rel_tol").jsonPrimitive.double
                assertTrue(abs(sum - wanted) <= wanted * relTol, "$label area $sum expected $wanted")
            }
        }
    }
}
