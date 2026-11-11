package io.github.progliodario.aethermoor.core.vector

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.double
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

// Vector art recipes. Spec: docs/spec/13-vector-art.md. Schema: schemas/art_recipe.schema.json.

data class Color(val r: Float = 0f, val g: Float = 0f, val b: Float = 0f, val a: Float = 0f)

private fun hexDigit(c: Char): Int =
    when (c) {
        in '0'..'9' -> c - '0'
        in 'a'..'f' -> c - 'a' + 10
        in 'A'..'F' -> c - 'A' + 10
        else -> -1
    }

/** "#RRGGBB" or "#RRGGBBAA"; null for anything else. */
fun parseHexColor(text: String): Color? {
    if ((text.length != 7 && text.length != 9) || text[0] != '#') return null
    val channel = intArrayOf(0, 0, 0, 255)
    val count = (text.length - 1) / 2
    for (i in 0 until count) {
        val hi = hexDigit(text[1 + 2 * i])
        val lo = hexDigit(text[2 + 2 * i])
        if (hi < 0 || lo < 0) return null
        channel[i] = hi * 16 + lo
    }
    return Color(channel[0] / 255f, channel[1] / 255f, channel[2] / 255f, channel[3] / 255f)
}

data class GradientStop(val t: Float, val color: String)

sealed interface Paint {
    data object None : Paint

    data class Solid(val color: String) : Paint

    data class Linear(val x0: Float, val y0: Float, val x1: Float, val y1: Float, val stops: List<GradientStop>) : Paint

    data class Radial(val cx: Float, val cy: Float, val r: Float, val stops: List<GradientStop>) : Paint

    /** A cloudy texture (spec 13, "Noise"): [scale] is the size of the largest clouds, [period] makes it repeat. */
    data class Noise(val scale: Float, val seed: Int, val octaves: Int, val period: Int, val stops: List<GradientStop>) : Paint
}

enum class Blend { NORMAL, MULTIPLY, ADD }

sealed interface Shape {
    data class Rect(val x: Float, val y: Float, val w: Float, val h: Float) : Shape

    data class Ellipse(val cx: Float, val cy: Float, val rx: Float, val ry: Float) : Shape

    data class Polygon(val points: List<Pair<Float, Float>>) : Shape

    data class Path(val d: String) : Shape
}

data class StrokeStyle(val color: String, val width: Float)

data class Layer(
    val shape: Shape,
    val fill: Paint,
    val stroke: StrokeStyle?,
    val alpha: Float,
    /** Drawn only with one of these variants (empty: always). */
    val only: List<String> = emptyList(),
    /** Not drawn with one of these variants. */
    val except: List<String> = emptyList(),
    /** Softens the edge: the radius of the blur of the coverage, in art units. */
    val blur: Float = 0f,
    /** Painted only where something is already painted. */
    val clip: Boolean = false,
    val blend: Blend = Blend.NORMAL,
)

typealias Palette = Map<String, String>

data class Recipe(
    val id: String,
    val width: Float,
    val height: Float,
    val originX: Float,
    val originY: Float,
    val palette: Palette,
    val variants: Map<String, Palette>,
    val layers: List<Layer>,
    /** The picture looks to the left: mirrored to face the player (spec 13, "Facing"). */
    val facesLeft: Boolean = false,
)

// Numbers are read through Double and then narrowed, exactly like the C++ client does.
internal fun JsonElement.f(): Float = jsonPrimitive.double.toFloat()

private fun JsonObject.str(key: String): String = getValue(key).jsonPrimitive.content

private fun parsePalette(element: JsonElement): Palette =
    element.jsonObject.mapValues { it.value.jsonPrimitive.content }

private fun parseStops(array: JsonArray): List<GradientStop> =
    array.map { GradientStop(it.jsonArray[0].f(), it.jsonArray[1].jsonPrimitive.content) }

private fun parsePaint(fill: JsonObject): Paint {
    fill["color"]?.let { return Paint.Solid(it.jsonPrimitive.content) }
    fill["linear"]?.let {
        val g = it.jsonObject
        return Paint.Linear(g.getValue("x0").f(), g.getValue("y0").f(), g.getValue("x1").f(), g.getValue("y1").f(),
            parseStops(g.getValue("stops").jsonArray))
    }
    fill["noise"]?.let {
        val n = it.jsonObject
        return Paint.Noise(
            n.getValue("scale").f(), n["seed"]?.asInt() ?: 0, n["octaves"]?.asInt() ?: 3, n["period"]?.asInt() ?: 0,
            parseStops(n.getValue("stops").jsonArray),
        )
    }
    val g = fill.getValue("radial").jsonObject
    return Paint.Radial(g.getValue("cx").f(), g.getValue("cy").f(), g.getValue("r").f(),
        parseStops(g.getValue("stops").jsonArray))
}

private fun parseShape(shape: JsonObject): Shape {
    shape["rect"]?.let { val a = it.jsonArray; return Shape.Rect(a[0].f(), a[1].f(), a[2].f(), a[3].f()) }
    shape["ellipse"]?.let { val a = it.jsonArray; return Shape.Ellipse(a[0].f(), a[1].f(), a[2].f(), a[3].f()) }
    shape["polygon"]?.let { poly ->
        return Shape.Polygon(poly.jsonArray.map { Pair(it.jsonArray[0].f(), it.jsonArray[1].f()) })
    }
    return Shape.Path(shape.str("path"))
}

/** Parses a recipe from JSON text; the failure carries the reason. */
fun parseRecipe(jsonText: String): Result<Recipe> =
    runCatching {
        val j = Json.parseToJsonElement(jsonText).jsonObject
        val canvas = j.getValue("canvas").jsonObject
        val origin = canvas.getValue("origin").jsonArray
        val layers = j.getValue("layers").jsonArray.map { element ->
            val l = element.jsonObject
            val stroke = l["stroke"]?.jsonObject?.let { StrokeStyle(it.str("color"), it.getValue("width").f()) }
            Layer(
                shape = parseShape(l.getValue("shape").jsonObject),
                fill = l["fill"]?.let { parsePaint(it.jsonObject) } ?: Paint.None,
                stroke = stroke,
                alpha = l["alpha"]?.f() ?: 1f,
                only = l["only"]?.jsonArray?.map { it.jsonPrimitive.content } ?: emptyList(),
                except = l["except"]?.jsonArray?.map { it.jsonPrimitive.content } ?: emptyList(),
                blur = l["blur"]?.f() ?: 0f,
                clip = l["clip"]?.asBoolean() ?: false,
                blend = when ((l["blend"] as? JsonPrimitive)?.contentOrNull) {
                    "multiply" -> Blend.MULTIPLY
                    "add" -> Blend.ADD
                    else -> Blend.NORMAL
                },
            )
        }
        Recipe(
            id = (j["id"] as? JsonPrimitive)?.contentOrNull ?: "",
            width = canvas.getValue("w").f(),
            height = canvas.getValue("h").f(),
            originX = origin[0].f(),
            originY = origin[1].f(),
            palette = j["palette"]?.let { parsePalette(it) } ?: emptyMap(),
            variants = j["variants"]?.jsonObject?.mapValues { parsePalette(it.value) } ?: emptyMap(),
            layers = layers,
            facesLeft = (j["faces"] as? JsonPrimitive)?.contentOrNull == "left",
        )
    }

// Kept for symmetry with the other parsers (booleans and ints are read by the rig and map parsers).
internal fun JsonElement.asBoolean(): Boolean = jsonPrimitive.boolean

internal fun JsonElement.asInt(): Int = jsonPrimitive.int
