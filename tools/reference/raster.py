"""The reference rasterizer of the art recipes (docs/spec/13-vector-art.md), in plain Python.

Both clients implement the same algorithm (desktop/src/vector/raster.cpp, android .../core/vector/Raster.kt). This one
is used to build the conformance probes of the newer features (blur, clip, blend, noise) and to draw the previews of
`tools/art_preview.py`. It computes in double precision; the clients use 32-bit floats and are compared with a tolerance.
"""
from __future__ import annotations

import math

SUB = 4  # sub-scanlines per pixel row
M32 = 0xFFFFFFFF


# ------------------------------------------------------------------------------------------------ geometry
def _circle_segments(radius_px: float) -> int:
    return 16 + 4 * int(math.floor(math.sqrt(max(radius_px, 0.0))))


def _ellipse(cx: float, cy: float, rx: float, ry: float, n: int) -> list[tuple[float, float]]:
    return [(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n)]


def _parse_path(d: str, s: float) -> list[tuple[list[tuple[float, float]], bool]]:
    out: list[tuple[list[tuple[float, float]], bool]] = []
    tokens: list[str] = []
    for raw in d.replace(",", " ").split():
        # a letter may be glued to a number ("M10"): split them
        cur = ""
        for ch in raw:
            if ch.isalpha() and ch not in "eE":
                if cur:
                    tokens.append(cur)
                    cur = ""
                tokens.append(ch)
            else:
                cur += ch
        if cur:
            tokens.append(cur)
    pts: list[tuple[float, float]] = []
    have = False
    cx = cy = sx = sy = 0.0
    cmd = ""
    i = 0

    def take(n: int) -> list[float] | None:
        nonlocal i
        if i + n > len(tokens):
            return None
        try:
            values = [float(t) for t in tokens[i:i + n]]
        except ValueError:
            return None
        i += n
        return values

    def start() -> None:
        nonlocal pts, have
        if not have:
            pts = [(cx * s, cy * s)]
            have = True

    while i < len(tokens):
        tok = tokens[i]
        if tok.isalpha():
            cmd = tok
            i += 1
            if cmd == "Z":
                if have:
                    out.append((pts, True))
                    pts, have = [], False
                cx, cy = sx, sy
            continue
        if cmd == "M":
            v = take(2)
            if v is None:
                return out
            if have:
                out.append((pts, False))
            pts, have = [(v[0] * s, v[1] * s)], True
            cx, cy = sx, sy = v
            cmd = "L"
        elif cmd == "L":
            v = take(2)
            if v is None:
                return out
            start()
            cx, cy = v
            pts.append((cx * s, cy * s))
        elif cmd == "H":
            v = take(1)
            if v is None:
                return out
            start()
            cx = v[0]
            pts.append((cx * s, cy * s))
        elif cmd == "V":
            v = take(1)
            if v is None:
                return out
            start()
            cy = v[0]
            pts.append((cx * s, cy * s))
        elif cmd == "Q":
            v = take(4)
            if v is None:
                return out
            start()
            x0, y0 = cx, cy
            for k in range(1, 13):
                t = k / 12
                u = 1 - t
                cx = u * u * x0 + 2 * u * t * v[0] + t * t * v[2]
                cy = u * u * y0 + 2 * u * t * v[1] + t * t * v[3]
                pts.append((cx * s, cy * s))
        elif cmd == "C":
            v = take(6)
            if v is None:
                return out
            start()
            x0, y0 = cx, cy
            for k in range(1, 17):
                t = k / 16
                u = 1 - t
                cx = u * u * u * x0 + 3 * u * u * t * v[0] + 3 * u * t * t * v[2] + t * t * t * v[4]
                cy = u * u * u * y0 + 3 * u * u * t * v[1] + 3 * u * t * t * v[3] + t * t * t * v[5]
                pts.append((cx * s, cy * s))
        else:
            return out
    if have:
        out.append((pts, False))
    return out


def _subpaths(shape: dict, s: float) -> list[tuple[list[tuple[float, float]], bool]]:
    if "rect" in shape:
        x, y, w, h = (v * s for v in shape["rect"])
        return [([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], True)]
    if "ellipse" in shape:
        cx, cy, rx, ry = (v * s for v in shape["ellipse"])
        return [(_ellipse(cx, cy, rx, ry, _circle_segments(max(rx, ry))), True)]
    if "polygon" in shape:
        return [([(x * s, y * s) for x, y in shape["polygon"]], True)]
    return _parse_path(shape["path"], s)


def _area(poly: list[tuple[float, float]]) -> float:
    total = 0.0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        total += x0 * y1 - x1 * y0
    return total / 2


def _stroke_polys(subpaths, half: float) -> list[list[tuple[float, float]]]:
    out = []

    def push(poly):
        a = _area(poly)
        if a == 0:
            return
        out.append(poly if a > 0 else poly[::-1])

    seg = _circle_segments(half)
    for pts, closed in subpaths:
        n = len(pts)
        if n == 0:
            continue
        for i in range(n if closed else n - 1):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
            dx, dy = x1 - x0, y1 - y0
            length = math.hypot(dx, dy)
            if length <= 0:
                continue
            nx, ny = -dy / length * half, dx / length * half
            push([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)])
        for x, y in pts:
            push(_ellipse(x, y, half, half, seg))
    return out


# ------------------------------------------------------------------------------------------------ coverage
class Mask:
    """The coverage of a layer: a flat list and the box of the pixels that may be covered."""

    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.cov = [0.0] * (w * h)
        self.x0, self.y0, self.x1, self.y1 = w, h, 0, 0  # empty box (x1, y1 exclusive)

    def empty(self) -> bool:
        return self.x1 <= self.x0 or self.y1 <= self.y0


def _coverage(polys, w: int, h: int) -> Mask:
    mask = Mask(w, h)
    edges = []
    min_y, max_y, min_x, max_x = math.inf, -math.inf, math.inf, -math.inf
    for poly in polys:
        n = len(poly)
        for i in range(n):
            (px, py), (qx, qy) = poly[i], poly[(i + 1) % n]
            min_y, max_y = min(min_y, py, qy), max(max_y, py, qy)
            min_x, max_x = min(min_x, px, qx), max(max_x, px, qx)
            if py == qy:
                continue
            edges.append((px, py, qx, qy, 1 if qy > py else -1, min(py, qy), max(py, qy)))
    if not edges:
        return mask
    r0 = max(0, int(math.floor(min_y)))
    r1 = min(h - 1, int(math.floor(max_y)))
    cov = mask.cov
    for r in range(r0, r1 + 1):
        base = r * w
        row_edges = [e for e in edges if e[5] < r + 1 and e[6] > r]
        for k in range(SUB):
            ys = r + (k + 0.5) / SUB
            cross = []
            for (x0, y0, x1, y1, d, ymin, ymax) in row_edges:
                if ymin <= ys < ymax:
                    cross.append((x0 + (ys - y0) * (x1 - x0) / (y1 - y0), d))
            cross.sort()
            wind = 0
            for i, (x, d) in enumerate(cross):
                if i > 0 and wind != 0:
                    xa, xb = max(cross[i - 1][0], 0.0), min(x, float(w))
                    if xb > xa:
                        first = int(math.floor(xa))
                        last = min(int(math.floor(xb)), w - 1)
                        for p in range(first, last + 1):
                            left, right = max(xa, p), min(xb, p + 1)
                            if right > left:
                                cov[base + p] += (right - left) / SUB
                wind += d
    mask.x0 = max(0, int(math.floor(min_x)))
    mask.x1 = min(w, int(math.floor(max_x)) + 1)
    mask.y0, mask.y1 = r0, r1 + 1
    for y in range(mask.y0, mask.y1):
        base = y * w
        for x in range(mask.x0, mask.x1):
            if cov[base + x] > 1.0:
                cov[base + x] = 1.0
    return mask


def _box_pass(line: list[float], rad: int) -> list[float]:
    """One box blur pass of a line: the mean of the 2*rad+1 values around each one (0 outside the line)."""
    n = len(line)
    out = [0.0] * n
    width = 2 * rad + 1
    total = 0.0
    for i in range(min(rad, n - 1) + 1):
        total += line[i]
    for i in range(n):
        out[i] = total / width
        add = i + rad + 1
        if add < n:
            total += line[add]
        drop = i - rad
        if drop >= 0:
            total -= line[drop]
    return out


def _blur(mask: Mask, rad: int) -> None:
    if rad < 1 or mask.empty():
        return
    w, h, cov = mask.w, mask.h, mask.cov
    grow = 3 * rad
    x0, x1 = max(0, mask.x0 - grow), min(w, mask.x1 + grow)
    y0, y1 = max(0, mask.y0 - grow), min(h, mask.y1 + grow)
    for y in range(mask.y0, mask.y1):  # rows first (only the rows that hold something)
        line = cov[y * w:(y + 1) * w]
        for _ in range(3):
            line = _box_pass(line, rad)
        cov[y * w:(y + 1) * w] = line
    for x in range(x0, x1):
        line = cov[x::w]
        for _ in range(3):
            line = _box_pass(line, rad)
        cov[x::w] = line
    mask.x0, mask.x1, mask.y0, mask.y1 = x0, x1, y0, y1


# ------------------------------------------------------------------------------------------------ paint
def parse_color(text: str) -> tuple[float, float, float, float]:
    if not text.startswith("#") or len(text) not in (7, 9):
        return (0.0, 0.0, 0.0, 0.0)
    try:
        ch = [int(text[i:i + 2], 16) / 255 for i in range(1, len(text), 2)]
    except ValueError:
        return (0.0, 0.0, 0.0, 0.0)
    return (ch[0], ch[1], ch[2], ch[3] if len(ch) == 4 else 1.0)


def _resolve(text: str, palette: dict) -> tuple[float, float, float, float]:
    if text.startswith("$p."):
        value = palette.get(text[3:])
        return parse_color(value) if value else (0.0, 0.0, 0.0, 0.0)
    return parse_color(text)


def _from_stops(stops, t: float):
    if t <= stops[0][0]:
        return stops[0][1]
    if t >= stops[-1][0]:
        return stops[-1][1]
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            span = t1 - t0
            u = 0.0 if span <= 0 else (t - t0) / span
            return tuple(c0[i] + (c1[i] - c0[i]) * u for i in range(4))
    return stops[-1][1]


def noise_hash(ix: int, iy: int, seed: int) -> float:
    """The lattice value of the noise fill: a 32-bit mix of the cell and the seed, as a number in 0..1."""
    h = (ix * 0x9E3779B1 + iy * 0x85EBCA77 + seed * 0xC2B2AE3D) & M32
    h ^= h >> 15
    h = (h * 0x2C1B3C6D) & M32
    h ^= h >> 12
    h = (h * 0x297A2D39) & M32
    h ^= h >> 15
    return (h >> 8) / 16777215.0


def noise_value(px: float, py: float, scale: float, seed: int, octaves: int, period: int) -> float:
    total, norm, amp = 0.0, 0.0, 1.0
    for o in range(octaves):
        f = (1 << o) / scale
        u, v = px * f, py * f
        ix, iy = int(math.floor(u)), int(math.floor(v))
        fu, fv = u - ix, v - iy
        su, sv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
        ix1, iy1 = ix + 1, iy + 1
        if period > 0:
            per = period << o
            ix, iy, ix1, iy1 = ix % per, iy % per, ix1 % per, iy1 % per
        s = seed + o
        a, b = noise_hash(ix, iy, s), noise_hash(ix1, iy, s)
        c, d = noise_hash(ix, iy1, s), noise_hash(ix1, iy1, s)
        top, bottom = a + (b - a) * su, c + (d - c) * su
        total += (top + (bottom - top) * sv) * amp
        norm += amp
        amp *= 0.5
    return total / norm


def _paint_fn(fill: dict, palette: dict):
    if "color" in fill:
        color = _resolve(fill["color"], palette)
        return lambda px, py: color
    if "linear" in fill:
        g = fill["linear"]
        stops = [(t, _resolve(c, palette)) for t, c in g["stops"]]
        x0, y0, dx, dy = g["x0"], g["y0"], g["x1"] - g["x0"], g["y1"] - g["y0"]
        den = dx * dx + dy * dy
        return lambda px, py: _from_stops(stops, 0.0 if den <= 0 else min(1.0, max(0.0, ((px - x0) * dx + (py - y0) * dy) / den)))
    if "radial" in fill:
        g = fill["radial"]
        stops = [(t, _resolve(c, palette)) for t, c in g["stops"]]
        cx, cy, r = g["cx"], g["cy"], g["r"]
        return lambda px, py: _from_stops(stops, 1.0 if r <= 0 else min(1.0, math.hypot(px - cx, py - cy) / r))
    g = fill["noise"]
    stops = [(t, _resolve(c, palette)) for t, c in g["stops"]]
    scale, seed, octaves, period = g["scale"], g.get("seed", 0), g.get("octaves", 3), g.get("period", 0)
    return lambda px, py: _from_stops(stops, noise_value(px, py, scale, seed, octaves, period))


def _composite(acc: list[float], mask: Mask, paint, alpha: float, s: float, clip: bool, blend: str) -> None:
    w, cov = mask.w, mask.cov
    for y in range(mask.y0, mask.y1):
        base = y * w
        py = (y + 0.5) / s
        for x in range(mask.x0, mask.x1):
            c = cov[base + x]
            if c <= 0:
                continue
            r, g, b, ca = paint((x + 0.5) / s, py)
            a = c * alpha * ca
            i = (base + x) * 4
            da = acc[i + 3]
            if blend == "multiply":  # darkens what is there, never adds coverage
                acc[i] *= 1 - a + a * r
                acc[i + 1] *= 1 - a + a * g
                acc[i + 2] *= 1 - a + a * b
                continue
            if clip:
                a *= da
            if blend == "add":
                acc[i] += r * a
                acc[i + 1] += g * a
                acc[i + 2] += b * a
            else:
                inv = 1 - a
                acc[i] = r * a + acc[i] * inv
                acc[i + 1] = g * a + acc[i + 1] * inv
                acc[i + 2] = b * a + acc[i + 2] * inv
            if not clip:
                acc[i + 3] = a + da * (1 - a)


def _byte(v: float) -> int:
    return int(max(0.0, min(255.0, math.floor(v * 255 + 0.5))))


def rasterize(recipe: dict, scale: float, variant: str | None = None) -> tuple[int, int, bytearray]:
    """Draws a recipe: (width, height, RGBA8 bytes with straight alpha)."""
    palette = dict(recipe.get("palette", {}))
    palette.update(recipe.get("variants", {}).get(variant or "", {}))
    w = max(1, int(math.ceil(recipe["canvas"]["w"] * scale)))
    h = max(1, int(math.ceil(recipe["canvas"]["h"] * scale)))
    acc = [0.0] * (w * h * 4)
    for layer in recipe["layers"]:
        if (layer.get("only") and variant not in layer["only"]) or variant in layer.get("except", []):
            continue
        subpaths = _subpaths(layer["shape"], scale)
        alpha = layer.get("alpha", 1.0)
        clip = bool(layer.get("clip", False))
        blend = layer.get("blend", "normal")
        rad = int(math.floor(layer.get("blur", 0.0) * scale + 0.5))
        if "fill" in layer:
            mask = _coverage([pts for pts, _ in subpaths if len(pts) >= 3], w, h)
            _blur(mask, rad)
            if not mask.empty():
                _composite(acc, mask, _paint_fn(layer["fill"], palette), alpha, scale, clip, blend)
        if "stroke" in layer:
            mask = _coverage(_stroke_polys(subpaths, layer["stroke"]["width"] * scale / 2), w, h)
            _blur(mask, rad)
            if not mask.empty():
                color = _resolve(layer["stroke"]["color"], palette)
                _composite(acc, mask, lambda px, py, color=color: color, alpha, scale, clip, blend)
    out = bytearray(w * h * 4)
    for p in range(w * h):
        a = acc[p * 4 + 3]
        a8 = _byte(a)
        if a8 == 0:
            continue
        out[p * 4] = _byte(acc[p * 4] / a)
        out[p * 4 + 1] = _byte(acc[p * 4 + 1] / a)
        out[p * 4 + 2] = _byte(acc[p * 4 + 2] / a)
        out[p * 4 + 3] = a8
    return w, h, out


def pixel(image: tuple[int, int, bytearray], x: int, y: int) -> list[int]:
    w, _, data = image
    i = (y * w + x) * 4
    return list(data[i:i + 4])
