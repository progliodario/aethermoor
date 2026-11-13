package io.github.progliodario.aethermoor.core.vector

import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

// Animation rigs and clips. Spec: docs/spec/13-vector-art.md. Schemas: rig, clip.

data class RigPart(
    val id: String,
    /** Empty for the root part. */
    val parent: String,
    val offsetX: Float,
    val offsetY: Float,
    val z: Int,
    val art: String,
    /** The recipe when the figure is seen from behind (spec 13); the same as [art] if not given. */
    val artBack: String = art,
    /** The draw order when seen from behind; the same as [z] if not given. */
    val zBack: Int = z,
    /** Seen from the side (spec 13): the recipe, the draw order and the joint; each the same as from the front if not given. */
    val artSide: String = art,
    val zSide: Int = z,
    val offsetSideX: Float = offsetX,
    val offsetSideY: Float = offsetY,
)

/** Parts are listed parents first. */
data class Rig(val id: String, val parts: List<RigPart>)

data class RotKey(val tick: Float, val degrees: Float)

data class PosKey(val tick: Float, val x: Float, val y: Float)

data class Track(val rot: List<RotKey>, val pos: List<PosKey>)

data class Clip(val id: String, val rig: String, val loop: Boolean, val lengthTicks: Int, val tracks: Map<String, Track>)

/** World placement of a part, in art units relative to the rig origin. */
data class PosedPart(val partIndex: Int, val x: Float, val y: Float, val rotationDeg: Float, val z: Int)

fun parseRig(jsonText: String): Result<Rig> =
    runCatching {
        val j = Json.parseToJsonElement(jsonText).jsonObject
        val parts = j.getValue("parts").jsonArray.map { element ->
            val p = element.jsonObject
            val parent = p.getValue("parent")
            val z = p["z"]?.jsonPrimitive?.int ?: 0
            val art = p.getValue("art").jsonPrimitive.content
            RigPart(
                id = p.getValue("id").jsonPrimitive.content,
                parent = if (parent is JsonNull) "" else parent.jsonPrimitive.content,
                offsetX = p.getValue("offset").jsonArray[0].f(),
                offsetY = p.getValue("offset").jsonArray[1].f(),
                z = z,
                art = art,
                artBack = p["art_back"]?.jsonPrimitive?.content ?: art,
                zBack = p["z_back"]?.jsonPrimitive?.int ?: z,
                artSide = p["art_side"]?.jsonPrimitive?.content ?: art,
                zSide = p["z_side"]?.jsonPrimitive?.int ?: z,
                offsetSideX = p["offset_side"]?.jsonArray?.get(0)?.f() ?: p.getValue("offset").jsonArray[0].f(),
                offsetSideY = p["offset_side"]?.jsonArray?.get(1)?.f() ?: p.getValue("offset").jsonArray[1].f(),
            )
        }
        Rig((j["id"] as? JsonPrimitive)?.contentOrNull ?: "", parts)
    }

fun parseClip(jsonText: String): Result<Clip> =
    runCatching {
        val j = Json.parseToJsonElement(jsonText).jsonObject
        val tracks = j.getValue("tracks").jsonObject.mapValues { (_, value) ->
            val t = value.jsonObject
            Track(
                rot = t["rot"]?.jsonArray?.map { RotKey(it.jsonArray[0].f(), it.jsonArray[1].f()) } ?: emptyList(),
                pos = t["pos"]?.jsonArray?.map { PosKey(it.jsonArray[0].f(), it.jsonArray[1].f(), it.jsonArray[2].f()) }
                    ?: emptyList(),
            )
        }
        Clip(
            id = (j["id"] as? JsonPrimitive)?.contentOrNull ?: "",
            rig = (j["rig"] as? JsonPrimitive)?.contentOrNull ?: "",
            loop = j["loop"]?.jsonPrimitive?.boolean ?: false,
            lengthTicks = j.getValue("length_ticks").jsonPrimitive.int,
            tracks = tracks,
        )
    }

/** Linear interpolation of keyframes; clamps outside the key range. [keys] are (tick, values...). */
private fun interpolate(ticks: FloatArray, values: Array<FloatArray>, t: Float, width: Int): FloatArray {
    val out = FloatArray(width)
    if (ticks.isEmpty()) return out
    if (t <= ticks.first()) return values.first().copyOf(width)
    if (t >= ticks.last()) return values.last().copyOf(width)
    for (k in 0 until ticks.size - 1) {
        if (ticks[k] <= t && t <= ticks[k + 1]) {
            val span = ticks[k + 1] - ticks[k]
            val u = if (span == 0f) 0f else (t - ticks[k]) / span
            for (i in 0 until width) out[i] = values[k][i] + (values[k + 1][i] - values[k][i]) * u
            return out
        }
    }
    return out
}

/** World placement of every part at [tick]; [mirror] negates x and rotation (facing left). */
fun evaluatePose(rig: Rig, clip: Clip, tick: Float, mirror: Boolean, side: Boolean = false): List<PosedPart> {
    val length = clip.lengthTicks.toFloat()
    var t = tick
    if (clip.loop) {
        t = tick % length
        if (t < 0f) t += length
    } else if (t > length) {
        t = length
    }

    val worldX = FloatArray(rig.parts.size)
    val worldY = FloatArray(rig.parts.size)
    val worldRot = FloatArray(rig.parts.size)
    val index = HashMap<String, Int>()
    val out = ArrayList<PosedPart>(rig.parts.size)

    for ((i, part) in rig.parts.withIndex()) {
        index[part.id] = i
        var rot = 0f
        var px = 0f
        var py = 0f
        clip.tracks[part.id]?.let { track ->
            if (track.rot.isNotEmpty()) {
                rot = interpolate(FloatArray(track.rot.size) { track.rot[it].tick },
                    Array(track.rot.size) { floatArrayOf(track.rot[it].degrees) }, t, 1)[0]
            }
            if (track.pos.isNotEmpty()) {
                val v = interpolate(FloatArray(track.pos.size) { track.pos[it].tick },
                    Array(track.pos.size) { floatArrayOf(track.pos[it].x, track.pos[it].y) }, t, 2)
                px = v[0]
                py = v[1]
            }
        }
        val lx = (if (side) part.offsetSideX else part.offsetX) + px
        val ly = (if (side) part.offsetSideY else part.offsetY) + py
        val parent = if (part.parent.isEmpty()) null else index[part.parent]
        if (parent == null) {
            worldX[i] = lx
            worldY[i] = ly
            worldRot[i] = rot
        } else {
            val r = worldRot[parent].toDouble() * PI / 180.0
            val c = cos(r).toFloat()
            val s = sin(r).toFloat()
            worldX[i] = worldX[parent] + c * lx - s * ly
            worldY[i] = worldY[parent] + s * lx + c * ly
            worldRot[i] = worldRot[parent] + rot
        }
        out.add(
            PosedPart(
                partIndex = i,
                x = if (mirror) -worldX[i] else worldX[i],
                y = worldY[i],
                rotationDeg = if (mirror) -worldRot[i] else worldRot[i],
                z = part.z,
            ),
        )
    }
    return out
}
