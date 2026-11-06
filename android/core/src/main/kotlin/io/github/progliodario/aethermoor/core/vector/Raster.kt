package io.github.progliodario.aethermoor.core.vector

import kotlin.math.PI
import kotlin.math.ceil
import kotlin.math.cos
import kotlin.math.floor
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

// Software rasterizer for vector art recipes. Spec: docs/spec/13-vector-art.md (normative algorithm).
// Keep this file in step with desktop/src/vector/raster.cpp: same operations, same order, 32-bit floats.

/** RGBA8 image with straight (non-premultiplied) alpha: [rgba] holds width * height * 4 bytes. */
class Bitmap(val width: Int, val height: Int, val rgba: ByteArray) {
    fun channel(x: Int, y: Int, channel: Int): Int = rgba[(y * width + x) * 4 + channel].toInt() and 0xFF
}

private const val SUB_SCANLINES = 4

private class Pt(val x: Float, val y: Float)

private class Subpath(val pts: MutableList<Pt> = ArrayList(), var closed: Boolean = false)

private class Edge(val x0: Float, val y0: Float, val x1: Float, val y1: Float, val dir: Int) {
    val ymin = min(y0, y1)
    val ymax = max(y0, y1)
}

private class Crossing(val x: Float, val dir: Int)

// ----------------------------------------------------------------------------------- geometry

private fun circleSegments(radiusPx: Float): Int = 16 + 4 * floor(sqrt(radiusPx)).toInt()

private fun appendEllipse(out: MutableList<Pt>, cx: Float, cy: Float, rx: Float, ry: Float, segments: Int) {
    for (k in 0 until segments) {
        val angle = 2.0 * PI * k.toDouble() / segments.toDouble()
        out.add(Pt((cx + rx * cos(angle)).toFloat(), (cy + ry * sin(angle)).toFloat()))
    }
}

private fun isSpaceOrComma(c: Char) = c == ' ' || c == ',' || c == '\t' || c == '\n' || c == '\r'

private fun isLetter(c: Char) = c in 'A'..'Z' || c in 'a'..'z'

private fun parsePath(d: String, scale: Float): List<Subpath> {
    val out = ArrayList<Subpath>()
    var current = Subpath()
    var have = false
    var curX = 0f
    var curY = 0f
    var startX = 0f
    var startY = 0f
    var cmd = ' '
    var i = 0
    val n = d.length

    fun skip() {
        while (i < n && isSpaceOrComma(d[i])) i++
    }

    /** Reads a float following the usual grammar: sign, digits, fraction, exponent. */
    fun number(): Float? {
        skip()
        if (i >= n) return null
        var j = i
        if (d[j] == '+' || d[j] == '-') j++
        var digits = 0
        while (j < n && d[j].isAsciiDigit()) {
            j++
            digits++
        }
        if (j < n && d[j] == '.') {
            j++
            while (j < n && d[j].isAsciiDigit()) {
                j++
                digits++
            }
        }
        if (digits == 0) return null
        if (j < n && (d[j] == 'e' || d[j] == 'E')) {
            var k = j + 1
            if (k < n && (d[k] == '+' || d[k] == '-')) k++
            var expDigits = 0
            while (k < n && d[k].isAsciiDigit()) {
                k++
                expDigits++
            }
            if (expDigits > 0) j = k
        }
        val value = d.substring(i, j).toDoubleOrNull() ?: return null
        i = j
        return value.toFloat()
    }

    fun ensureStarted() {
        if (!have) {
            current = Subpath()
            current.pts.add(Pt(curX * scale, curY * scale))
            have = true
        }
    }

    fun addPoint(x: Float, y: Float) {
        current.pts.add(Pt(x * scale, y * scale))
        curX = x
        curY = y
    }

    while (true) {
        skip()
        if (i >= n) break
        if (isLetter(d[i])) {
            cmd = d[i]
            i++
            if (cmd == 'Z') {
                if (have) {
                    current.closed = true
                    out.add(current)
                    current = Subpath()
                    have = false
                }
                curX = startX
                curY = startY
            }
            continue
        }
        when (cmd) {
            'M' -> {
                val a = number() ?: return out
                val b = number() ?: return out
                if (have) out.add(current)
                current = Subpath()
                current.pts.add(Pt(a * scale, b * scale))
                have = true
                curX = a
                startX = a
                curY = b
                startY = b
                cmd = 'L'
            }
            'L' -> {
                val a = number() ?: return out
                val b = number() ?: return out
                ensureStarted()
                addPoint(a, b)
            }
            'H' -> {
                val a = number() ?: return out
                ensureStarted()
                addPoint(a, curY)
            }
            'V' -> {
                val a = number() ?: return out
                ensureStarted()
                addPoint(curX, a)
            }
            'Q' -> {
                val a = number() ?: return out
                val b = number() ?: return out
                val c = number() ?: return out
                val dd = number() ?: return out
                ensureStarted()
                val x0 = curX
                val y0 = curY
                for (s in 1..12) {
                    val t = s.toFloat() / 12f
                    val u = 1f - t
                    addPoint(u * u * x0 + 2f * u * t * a + t * t * c, u * u * y0 + 2f * u * t * b + t * t * dd)
                }
            }
            'C' -> {
                val a = number() ?: return out
                val b = number() ?: return out
                val c = number() ?: return out
                val dd = number() ?: return out
                val e = number() ?: return out
                val f = number() ?: return out
                ensureStarted()
                val x0 = curX
                val y0 = curY
                for (s in 1..16) {
                    val t = s.toFloat() / 16f
                    val u = 1f - t
                    addPoint(
                        u * u * u * x0 + 3f * u * u * t * a + 3f * u * t * t * c + t * t * t * e,
                        u * u * u * y0 + 3f * u * u * t * b + 3f * u * t * t * dd + t * t * t * f,
                    )
                }
            }
            else -> return out
        }
    }
    if (have) out.add(current)
    return out
}

private fun Char.isAsciiDigit() = this in '0'..'9'

private fun shapeSubpaths(shape: Shape, scale: Float): List<Subpath> =
    when (shape) {
        is Shape.Rect -> {
            val x = shape.x * scale
            val y = shape.y * scale
            val w = shape.w * scale
            val h = shape.h * scale
            listOf(Subpath(arrayListOf(Pt(x, y), Pt(x + w, y), Pt(x + w, y + h), Pt(x, y + h)), true))
        }
        is Shape.Ellipse -> {
            val rx = shape.rx * scale
            val ry = shape.ry * scale
            val pts = ArrayList<Pt>()
            appendEllipse(pts, shape.cx * scale, shape.cy * scale, rx, ry, circleSegments(max(rx, ry)))
            listOf(Subpath(pts, true))
        }
        is Shape.Polygon ->
            listOf(Subpath(shape.points.mapTo(ArrayList()) { Pt(it.first * scale, it.second * scale) }, true))
        is Shape.Path -> parsePath(shape.d, scale)
    }

private fun signedArea(poly: List<Pt>): Float {
    var total = 0f
    for (i in poly.indices) {
        val p = poly[i]
        val q = poly[(i + 1) % poly.size]
        total += p.x * q.y - q.x * p.y
    }
    return total * 0.5f
}

/** Round-join, round-cap stroke as a union of positively oriented pieces (spec 13, step 3). */
private fun strokePolygons(subpaths: List<Subpath>, halfWidth: Float): List<List<Pt>> {
    val out = ArrayList<List<Pt>>()
    fun pushOriented(poly: List<Pt>) {
        val area = signedArea(poly)
        if (area == 0f) return
        out.add(if (area < 0f) poly.reversed() else poly)
    }
    val segments = circleSegments(halfWidth)
    for (sp in subpaths) {
        val n = sp.pts.size
        if (n == 0) continue
        val edges = if (sp.closed) n else n - 1
        for (i in 0 until edges) {
            val p0 = sp.pts[i]
            val p1 = sp.pts[(i + 1) % n]
            val dx = p1.x - p0.x
            val dy = p1.y - p0.y
            val length = sqrt(dx * dx + dy * dy)
            if (length <= 0f) continue
            val nx = -dy / length * halfWidth
            val ny = dx / length * halfWidth
            pushOriented(listOf(Pt(p0.x + nx, p0.y + ny), Pt(p1.x + nx, p1.y + ny), Pt(p1.x - nx, p1.y - ny), Pt(p0.x - nx, p0.y - ny)))
        }
        for (p in sp.pts) {
            val circle = ArrayList<Pt>()
            appendEllipse(circle, p.x, p.y, halfWidth, halfWidth, segments)
            pushOriented(circle)
        }
    }
    return out
}

// ---------------------------------------------------------------------------------- coverage

private fun addSpan(cov: FloatArray, rowOffset: Int, width: Int, xaIn: Float, xbIn: Float) {
    val xa = max(xaIn, 0f)
    val xb = min(xbIn, width.toFloat())
    if (xb <= xa) return
    val first = floor(xa).toInt()
    val last = min(floor(xb).toInt(), width - 1)
    for (p in first..last) {
        val left = max(xa, p.toFloat())
        val right = min(xb, (p + 1).toFloat())
        if (right > left) cov[rowOffset + p] += (right - left) * 0.25f
    }
}

private fun coverage(polys: List<List<Pt>>, width: Int, height: Int): FloatArray {
    val edges = ArrayList<Edge>()
    var minY = 0f
    var maxY = 0f
    var any = false
    for (poly in polys) {
        for (i in poly.indices) {
            val p = poly[i]
            val q = poly[(i + 1) % poly.size]
            if (!any) {
                minY = p.y
                maxY = p.y
                any = true
            }
            minY = min(minY, min(p.y, q.y))
            maxY = max(maxY, max(p.y, q.y))
            if (p.y == q.y) continue
            edges.add(Edge(p.x, p.y, q.x, q.y, if (q.y > p.y) 1 else -1))
        }
    }
    val cov = FloatArray(width * height)
    if (edges.isEmpty()) return cov
    val rowBegin = max(0, floor(minY).toInt())
    val rowEnd = min(height - 1, floor(maxY).toInt())
    val crossings = ArrayList<Crossing>()
    val order = Comparator<Crossing> { a, b -> if (a.x != b.x) a.x.compareTo(b.x) else a.dir.compareTo(b.dir) }
    for (r in rowBegin..rowEnd) {
        for (k in 0 until SUB_SCANLINES) {
            val ys = r.toFloat() + (k.toFloat() + 0.5f) / 4f
            crossings.clear()
            for (e in edges) {
                if (ys >= e.ymin && ys < e.ymax) {
                    val x = e.x0 + (ys - e.y0) * (e.x1 - e.x0) / (e.y1 - e.y0)
                    crossings.add(Crossing(x, e.dir))
                }
            }
            crossings.sortWith(order)
            var winding = 0
            for (i in crossings.indices) {
                if (i > 0 && winding != 0) addSpan(cov, r * width, width, crossings[i - 1].x, crossings[i].x)
                winding += crossings[i].dir
            }
        }
    }
    for (i in cov.indices) cov[i] = min(cov[i], 1f)
    return cov
}

// ------------------------------------------------------------------------------------- paint

private fun resolveColor(text: String, palette: Palette): Color {
    if (text.startsWith("\$p.")) {
        val hex = palette[text.substring(3)] ?: return Color()
        return parseHexColor(hex) ?: Color()
    }
    return parseHexColor(text) ?: Color()
}

private class ResolvedStop(val t: Float, val color: Color)

private sealed interface ResolvedPaint {
    class Solid(val color: Color) : ResolvedPaint

    class Linear(val x0: Float, val y0: Float, val x1: Float, val y1: Float, val stops: List<ResolvedStop>) : ResolvedPaint

    class Radial(val cx: Float, val cy: Float, val r: Float, val stops: List<ResolvedStop>) : ResolvedPaint
}

private fun resolveStops(stops: List<GradientStop>, palette: Palette) =
    stops.map { ResolvedStop(it.t, resolveColor(it.color, palette)) }

private fun resolvePaint(paint: Paint, palette: Palette): ResolvedPaint? =
    when (paint) {
        Paint.None -> null
        is Paint.Solid -> ResolvedPaint.Solid(resolveColor(paint.color, palette))
        is Paint.Linear -> ResolvedPaint.Linear(paint.x0, paint.y0, paint.x1, paint.y1, resolveStops(paint.stops, palette))
        is Paint.Radial -> ResolvedPaint.Radial(paint.cx, paint.cy, paint.r, resolveStops(paint.stops, palette))
    }

private fun clamp01(v: Float) = if (v < 0f) 0f else if (v > 1f) 1f else v

private fun colorFromStops(stops: List<ResolvedStop>, t: Float): Color {
    if (stops.isEmpty()) return Color()
    if (t <= stops.first().t) return stops.first().color
    if (t >= stops.last().t) return stops.last().color
    for (i in 0 until stops.size - 1) {
        val s0 = stops[i]
        val s1 = stops[i + 1]
        if (t <= s1.t) {
            val span = s1.t - s0.t
            val u = if (span <= 0f) 0f else (t - s0.t) / span
            return Color(
                s0.color.r + (s1.color.r - s0.color.r) * u,
                s0.color.g + (s1.color.g - s0.color.g) * u,
                s0.color.b + (s1.color.b - s0.color.b) * u,
                s0.color.a + (s1.color.a - s0.color.a) * u,
            )
        }
    }
    return stops.last().color
}

private fun paintAt(paint: ResolvedPaint, px: Float, py: Float): Color =
    when (paint) {
        is ResolvedPaint.Solid -> paint.color
        is ResolvedPaint.Linear -> {
            val dx = paint.x1 - paint.x0
            val dy = paint.y1 - paint.y0
            val denom = dx * dx + dy * dy
            val t = if (denom <= 0f) 0f else clamp01(((px - paint.x0) * dx + (py - paint.y0) * dy) / denom)
            colorFromStops(paint.stops, t)
        }
        is ResolvedPaint.Radial -> {
            val ex = px - paint.cx
            val ey = py - paint.cy
            val t = if (paint.r <= 0f) 1f else clamp01(sqrt(ex * ex + ey * ey) / paint.r)
            colorFromStops(paint.stops, t)
        }
    }

private fun composite(acc: FloatArray, cov: FloatArray, paint: ResolvedPaint, layerAlpha: Float, width: Int, height: Int, scale: Float) {
    for (y in 0 until height) {
        for (x in 0 until width) {
            val index = y * width + x
            val c = cov[index]
            if (c <= 0f) continue
            val color = paintAt(paint, (x.toFloat() + 0.5f) / scale, (y.toFloat() + 0.5f) / scale)
            val a = (c * layerAlpha) * color.a
            val inv = 1f - a
            val o = index * 4
            acc[o] = color.r * a + acc[o] * inv
            acc[o + 1] = color.g * a + acc[o + 1] * inv
            acc[o + 2] = color.b * a + acc[o + 2] * inv
            acc[o + 3] = a + acc[o + 3] * inv
        }
    }
}

private fun toByte(v: Float): Int = max(0f, min(255f, floor(v * 255f + 0.5f))).toInt()

/** Renders [recipe] at [scale] pixels per art unit, using the palette of [variant] when it exists. */
fun rasterize(recipe: Recipe, scale: Float, variant: String? = null): Bitmap {
    val palette = HashMap(recipe.palette)
    variant?.let { recipe.variants[it] }?.let { palette.putAll(it) }

    val width = max(1, ceil(recipe.width * scale).toInt())
    val height = max(1, ceil(recipe.height * scale).toInt())
    val pixels = width * height
    val acc = FloatArray(pixels * 4)

    for (layer in recipe.layers) {
        if ((layer.only.isNotEmpty() && variant !in layer.only) || (variant != null && variant in layer.except)) continue
        val subpaths = shapeSubpaths(layer.shape, scale)
        resolvePaint(layer.fill, palette)?.let { paint ->
            val polys = subpaths.filter { it.pts.size >= 3 }.map { it.pts as List<Pt> }
            composite(acc, coverage(polys, width, height), paint, layer.alpha, width, height, scale)
        }
        layer.stroke?.let { stroke ->
            val polys = strokePolygons(subpaths, stroke.width * scale / 2f)
            val paint = ResolvedPaint.Solid(resolveColor(stroke.color, palette))
            composite(acc, coverage(polys, width, height), paint, layer.alpha, width, height, scale)
        }
    }

    val rgba = ByteArray(pixels * 4)
    for (i in 0 until pixels) {
        val a = acc[i * 4 + 3]
        val alpha = toByte(a)
        if (alpha == 0) continue
        rgba[i * 4] = toByte(acc[i * 4] / a).toByte()
        rgba[i * 4 + 1] = toByte(acc[i * 4 + 1] / a).toByte()
        rgba[i * 4 + 2] = toByte(acc[i * 4 + 2] / a).toByte()
        rgba[i * 4 + 3] = alpha.toByte()
    }
    return Bitmap(width, height, rgba)
}
