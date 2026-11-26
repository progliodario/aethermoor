"""A small toolkit to build art recipes (schemas/art_recipe.schema.json) from code: layers, color math and seeded details.

`tools/make_art.py` uses it to write the recipes of data/base/art/. The recipes are plain JSON in the end: the game never runs this code.
Style rules (docs/design/art-style.md): light from the top left, soft shades and lights, the matter of things as noise, no cartoon
outline, soft shadow ellipses under things that stand on the ground; `finish()` gives any recipe the realistic finish (ADR 0015).
"""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "data" / "base" / "art"


# ------------------------------------------------------------------------------------------------ colors
def _rgb(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def _hex(r: float, g: float, b: float) -> str:
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(v))) for v in (r, g, b))


def mix(a: str, b: str, t: float) -> str:
    """A color between a (t = 0) and b (t = 1)."""
    (r1, g1, b1), (r2, g2, b2) = _rgb(a), _rgb(b)
    return _hex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)


def lighten(c: str, t: float = 0.25) -> str:
    return mix(c, "#FFFFFF", t)


def darken(c: str, t: float = 0.25) -> str:
    return mix(c, "#000000", t)


def warm(c: str, t: float = 0.15) -> str:
    return mix(c, "#FFB050", t)


def cool(c: str, t: float = 0.15) -> str:
    return mix(c, "#5070C0", t)


# ------------------------------------------------------------------------------------------------ recipes
class Recipe:
    def __init__(self, recipe_id: str, w: float, h: float, origin: tuple[float, float] = (0, 0), palette: dict | None = None, seed: str | int = 0):
        self.id = recipe_id
        self.w, self.h, self.origin = w, h, list(origin)
        self.palette = dict(palette or {})
        self.layers: list[dict] = []
        self.variants: dict[str, dict] = {}
        self.faces: str | None = None  # "left": the clients mirror the picture to face the player
        self.sway: float = 0.0  # how far the top moves in the wind, in art units (spec 13, "Sway")
        self.rng = random.Random(f"{recipe_id}/{seed}")
        # the realistic finish applied when the recipe is written (see `finish()`): None for none, or its settings
        self.finish: dict | None = None

    # --- layers
    def add(self, shape: dict, fill=None, stroke=None, width: float = 1.0, alpha: float | None = None, only=None,
            blur: float | None = None, clip: bool = False, blend: str | None = None, skip=None) -> "Recipe":
        """A layer. `blur` softens its edge (art units), `clip` keeps it inside what is already painted, `blend` is
        "multiply" (a shade) or "add" (a light); `only` and `skip` (the `except` of the format) are variant names."""
        layer: dict = {"shape": shape}
        if fill is not None:
            layer["fill"] = fill if isinstance(fill, dict) else {"color": fill}
        if stroke is not None:
            layer["stroke"] = {"color": stroke, "width": _n(width)}
        if alpha is not None and alpha < 1:
            layer["alpha"] = round(alpha, 3)
        if blur:
            layer["blur"] = _n(blur)
        if clip:
            layer["clip"] = True
        if blend:
            layer["blend"] = blend
        if only:
            layer["only"] = list(only)
        if skip:
            layer["except"] = list(skip)
        self.layers.append(layer)
        return self

    # --- shading: a tone, a shade, a light (docs/design/art-style.md); the finish softens the hard ones
    def shade(self, d: str, alpha: float = 0.42, color: str = "#5A4E9A", blur: float | None = None, **kw):
        """A shade over what is painted: a cool violet multiplied on the colors, so that every palette keeps its hue."""
        return self.add({"path": d}, color, alpha=alpha, blend="multiply", blur=blur, **kw)

    def lit(self, d: str, alpha: float = 0.35, color: str = "#FFF4D8", blur: float | None = None, **kw):
        """A light inside what is painted (a rim, a gloss)."""
        return self.add({"path": d}, color, alpha=alpha, blend="add", clip=True, blur=blur, **kw)

    def glow(self, cx, cy, r, color: str, alpha: float = 0.5):
        """A soft light around a point, also outside what is painted (a flame, a rune)."""
        return self.add({"ellipse": [_n(cx), _n(cy), _n(r * 0.6), _n(r * 0.6)]}, color, alpha=alpha, blend="add", blur=r * 0.4)

    def rect(self, x, y, w, h, fill=None, **kw):
        return self.add({"rect": [_n(x), _n(y), _n(w), _n(h)]}, fill, **kw)

    def ellipse(self, cx, cy, rx, ry, fill=None, **kw):
        return self.add({"ellipse": [_n(cx), _n(cy), _n(rx), _n(ry)]}, fill, **kw)

    def poly(self, points, fill=None, **kw):
        return self.add({"polygon": [[_n(x), _n(y)] for x, y in points]}, fill, **kw)

    def path(self, d: str, fill=None, **kw):
        return self.add({"path": d}, fill, **kw)

    def line(self, x0, y0, x1, y1, color, width=1.0, alpha=None):
        return self.add({"path": f"M {_n(x0)} {_n(y0)} L {_n(x1)} {_n(y1)}"}, None, stroke=color, width=width, alpha=alpha)

    def shadow(self, cx, cy, rx, ry, alpha=0.3):
        """The soft shadow of something standing on the ground: a wide faint one and a darker core."""
        self.ellipse(cx, cy, rx, ry, "#141030", alpha=alpha, blur=min(rx, ry) * 0.35)
        self.ellipse(cx, cy, rx * 0.6, ry * 0.55, "#141030", alpha=alpha * 0.8, blur=min(rx, ry) * 0.25)
        return self

    # --- seeded details
    def scatter(self, n: int, margin: float = 2.0):
        """n points in the canvas (away from the edges by margin)."""
        return [(self.rng.uniform(margin, self.w - margin), self.rng.uniform(margin, self.h - margin)) for _ in range(n)]

    def blades(self, n: int, color: str, hmin=2.5, hmax=5.5, width=1.4, margin=3.0, light: str | None = None):
        """Little tufts of three grass blades; `light` adds a lighter blade to each tuft."""
        for x, y in self.scatter(n, margin):
            h = self.rng.uniform(hmin, hmax)
            lean = self.rng.uniform(-1.2, 1.2)
            self.poly([(x - width, y), (x + lean, y - h), (x, y)], color)
            self.poly([(x, y), (x + lean * 0.6 + 0.8, y - h * 0.8), (x + width, y)], color)
            if light:
                self.poly([(x + width * 0.4, y), (x - lean * 0.5 - 0.4, y - h * 0.7), (x - width * 0.2, y)], light)
        return self

    def speckles(self, n: int, color: str, rmin=0.4, rmax=0.9, alpha=None, margin=1.0):
        for x, y in self.scatter(n, margin):
            r = self.rng.uniform(rmin, rmax)
            self.ellipse(x, y, r, r * 0.85, color, alpha=alpha)
        return self

    def blotches(self, n: int, color: str, rmin=3.0, rmax=7.0, alpha=0.22, margin=0.0):
        """Large soft patches of another tone (mottling)."""
        for x, y in self.scatter(n, margin):
            r = self.rng.uniform(rmin, rmax)
            self.ellipse(x, y, r * 1.15, r * 0.8, color, alpha=alpha)
        return self

    def pebbles(self, n: int, base: str, margin=3.0, rmin=0.9, rmax=2.0):
        for x, y in self.scatter(n, margin):
            r = self.rng.uniform(rmin, rmax)
            self.ellipse(x + 0.3, y + 0.5, r, r * 0.7, "#000000", alpha=0.22)
            self.ellipse(x, y, r, r * 0.75, mix(base, "#000000", self.rng.uniform(0.0, 0.18)))
            self.ellipse(x - r * 0.3, y - r * 0.25, r * 0.4, r * 0.28, lighten(base, 0.5), alpha=0.7)
        return self

    def flowers(self, n: int, colors: list[str], center="#FFE88A", margin=4.0, r=1.0):
        for x, y in self.scatter(n, margin):
            c = self.rng.choice(colors)
            for dx, dy in ((0, -r), (r, 0), (0, r), (-r, 0)):
                self.ellipse(x + dx, y + dy, r * 0.85, r * 0.85, c)
            self.ellipse(x, y, r * 0.7, r * 0.7, center)
        return self

    # --- output
    def to_json(self) -> dict:
        layers, palette, variants = self.layers, self.palette, self.variants
        if self.finish is not None:  # the realistic finish (docs/design/art-style.md, "The finish")
            layers, palette, variants = finish(self, **self.finish)
        data = {
            "$schema": "../../../../schemas/art_recipe.schema.json",
            "id": self.id,
            "canvas": {"w": _n(self.w), "h": _n(self.h), "origin": [_n(self.origin[0]), _n(self.origin[1])]},
            "layers": layers,
            "palette": palette,
        }
        if variants:
            data["variants"] = variants
        if self.faces:
            data["faces"] = self.faces
        if self.sway:
            data["sway"] = _n(self.sway)
        return data

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.to_json()
        # the schema reference is relative to the folder of the file
        depth = len(path.relative_to(ROOT).parts) - 1
        data["$schema"] = "../" * depth + "schemas/art_recipe.schema.json"
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def _n(v):
    """A short number: integers without a dot, others with at most two decimals."""
    v = round(float(v), 2)
    return int(v) if v == int(v) else v


def linear(x0, y0, x1, y1, *stops):
    """A linear gradient fill: stops are (t, color) pairs."""
    return {"linear": {"x0": _n(x0), "y0": _n(y0), "x1": _n(x1), "y1": _n(y1), "stops": [[t, c] for t, c in stops]}}


def radial(cx, cy, r, *stops):
    return {"radial": {"cx": _n(cx), "cy": _n(cy), "r": _n(r), "stops": [[t, c] for t, c in stops]}}


def noise(scale, seed, *stops, octaves: int = 4, period: int = 0, scale_y=None, period_y: int | None = None, ridged: bool = False):
    """A noise fill (spec 13): soft clouds of the stop colors, `scale` art units wide; `period` (in cells of `scale`)
    makes it repeat, so that a tile joins itself. `scale_y` stretches the clouds along y (grain, blades, ripples, strands of
    hair), `period_y` is its period (in cells of `scale_y`), `ridged` folds them into thin creases (veins, cracks, caustics)."""
    data = {"scale": _n(scale), "seed": int(seed), "octaves": octaves, "stops": [[t, c] for t, c in stops]}
    if period:
        data["period"] = int(period)
    if scale_y is not None and _n(scale_y) != _n(scale):
        data["scale_y"] = _n(scale_y)
    if period_y is not None and period_y != period:
        data["period_y"] = int(period_y)
    if ridged:
        data["ridged"] = True
    return {"noise": data}


# ------------------------------------------------------------------------------------------------ moving layers
def _map_path(d: str, s: float, dx: float, dy: float) -> str:
    """Scales and moves the points of a path made of the absolute commands M L Q C Z."""
    out: list[str] = []
    nums: list[float] = []

    def flush() -> None:
        for i in range(0, len(nums) - 1, 2):
            out.append(f"{_n(nums[i] * s + dx)} {_n(nums[i + 1] * s + dy)}")
        nums.clear()

    for tok in d.replace(",", " ").split():
        if tok.isalpha():
            flush()
            out.append(tok)
        else:
            nums.append(float(tok))
    flush()
    return " ".join(out)


def _map_paint(fill: dict, s: float, dx: float, dy: float) -> dict:
    if "linear" in fill:
        g = dict(fill["linear"])
        g.update(x0=_n(g["x0"] * s + dx), y0=_n(g["y0"] * s + dy), x1=_n(g["x1"] * s + dx), y1=_n(g["y1"] * s + dy))
        return {"linear": g}
    if "radial" in fill:
        g = dict(fill["radial"])
        g.update(cx=_n(g["cx"] * s + dx), cy=_n(g["cy"] * s + dy), r=_n(g["r"] * s))
        return {"radial": g}
    if "noise" in fill:
        g = dict(fill["noise"], scale=_n(fill["noise"]["scale"] * s))
        if "scale_y" in g:
            g["scale_y"] = _n(g["scale_y"] * s)
        return {"noise": g}
    return fill


def transform_layers(layers: list[dict], s: float = 1.0, dx: float = 0.0, dy: float = 0.0) -> list[dict]:
    """Copies the layers scaled by s (the same on both axes) and moved by (dx, dy)."""
    out = []
    for layer in layers:
        new = dict(layer)
        shape = layer["shape"]
        if "rect" in shape:
            x, y, w, h = shape["rect"]
            new["shape"] = {"rect": [_n(x * s + dx), _n(y * s + dy), _n(w * s), _n(h * s)]}
        elif "ellipse" in shape:
            x, y, rx, ry = shape["ellipse"]
            new["shape"] = {"ellipse": [_n(x * s + dx), _n(y * s + dy), _n(rx * s), _n(ry * s)]}
        elif "polygon" in shape:
            new["shape"] = {"polygon": [[_n(x * s + dx), _n(y * s + dy)] for x, y in shape["polygon"]]}
        else:
            new["shape"] = {"path": _map_path(shape["path"], s, dx, dy)}
        if "fill" in layer:
            new["fill"] = _map_paint(layer["fill"], s, dx, dy)
        if "stroke" in layer:
            new["stroke"] = dict(layer["stroke"], width=_n(layer["stroke"]["width"] * s))
        if "blur" in layer:
            new["blur"] = _n(layer["blur"] * s)
        out.append(new)
    return out


# ------------------------------------------------------------------------------------------------ the realistic finish
# The art was first drawn as an anime: flat tones, a hard shade, a dark outline. The finish turns any recipe into a painted,
# realistic picture without drawing it again (docs/design/art-style.md, "The finish"):
#
# - the outline of a filled shape becomes a faint edge in its own place (`outline`: what is left of its opacity), so that the
#   silhouette is read by its light and shade and not by a line;
# - every hard shade (a multiplied layer with no blur) and every hard light (an added, clipped layer) gets a soft edge;
# - the colours lose a part of their saturation (`desat`), as real things under real light;
# - a soft light from the top left and its shade on the far side give the whole picture a volume (`form`);
# - a fine grain of the matter covers it (`grain`), and a faint light of the sky falls on its upper edges;
# - fine scratches, pits and cracks of wear cover it (`wear`, for the props and the creatures).
SHADOW_INK = "#141030"


def _luma(c: str) -> float:
    r, g, b = _rgb(c)
    return 0.299 * r + 0.587 * g + 0.114 * b


def desaturate(c: str, t: float) -> str:
    """A colour (#RRGGBB or #RRGGBBAA) with a share t of its saturation taken away; other text is returned as it is."""
    if not (isinstance(c, str) and c.startswith("#") and len(c) in (7, 9)) or t <= 0:
        return c
    y = _luma(c)
    r, g, b = _rgb(c)
    out = _hex(r + (y - r) * t, g + (y - g) * t, b + (y - b) * t)
    return out + c[7:9] if len(c) == 9 else out


def _recolor(value, t: float):
    if isinstance(value, str):
        return desaturate(value, t)
    if isinstance(value, list):
        return [_recolor(v, t) for v in value]
    if isinstance(value, dict):
        return {k: _recolor(v, t) for k, v in value.items()}
    return value


def _numbers(d: str) -> list[float]:
    out = []
    for tok in d.replace(",", " ").split():
        try:
            out.append(float(tok))
        except ValueError:
            pass
    return out


def shape_box(shape: dict) -> tuple[float, float, float, float] | None:
    """A box (x0, y0, x1, y1) around a shape (for a path, around its points and control points)."""
    if "rect" in shape:
        x, y, w, h = shape["rect"]
        return x, y, x + w, y + h
    if "ellipse" in shape:
        x, y, rx, ry = shape["ellipse"]
        return x - rx, y - ry, x + rx, y + ry
    pts = shape["polygon"] if "polygon" in shape else None
    if pts is None:
        nums = _numbers(shape.get("path", ""))
        pts = list(zip(nums[0::2], nums[1::2]))
    if not pts:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _body_box(layers: list[dict], w: float, h: float) -> tuple[float, float, float, float]:
    """The box of what a recipe paints, without its shadow on the ground and its glows."""
    box = None
    for layer in layers:
        fill = layer.get("fill", {})
        if layer.get("blend") or layer.get("clip") or layer.get("alpha", 1) < 0.3 or "fill" not in layer:
            continue
        if fill.get("color") == SHADOW_INK or layer.get("blur", 0) > 1.5:
            continue
        b = shape_box(layer["shape"])
        if b is None:
            continue
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    if box is None:
        return 0.0, 0.0, w, h
    x0, y0, x1, y1 = max(0.0, box[0]), max(0.0, box[1]), min(w, box[2]), min(h, box[3])
    if x1 - x0 < 1 or y1 - y0 < 1:
        return 0.0, 0.0, w, h
    return x0, y0, x1, y1


def finish(r: "Recipe", outline: float = 0.4, desat: float = 0.15, form: float = 0.32, grain: float = 0.16, sky: float = 0.1,
           soften: float = 0.45, palette: bool = True, wear: float = 0.0) -> tuple[list[dict], dict, dict]:
    """The layers, palette and variants of `r` with the realistic finish (see above). The recipe itself is not changed."""
    layers: list[dict] = []
    for layer in r.layers:
        layer = _recolor(layer, desat)
        if "stroke" in layer and "fill" in layer and not layer.get("blend"):
            body = {k: v for k, v in layer.items() if k != "stroke"}
            edge = {k: v for k, v in layer.items() if k != "fill"}
            edge["stroke"] = dict(layer["stroke"], width=_n(max(0.15, layer["stroke"]["width"] * 0.8)))
            a = round(layer.get("alpha", 1.0) * outline, 3)
            if a <= 0.02:
                layers.append(body)
                continue
            edge["alpha"] = a
            layers += [body, edge]
            continue
        if not layer.get("blur") and layer.get("blend") == "multiply" and "fill" in layer and "color" in layer["fill"]:
            layer = dict(layer, blur=_n(soften))  # a soft shade
        elif not layer.get("blur") and layer.get("blend") == "add" and layer.get("clip") and "fill" in layer:
            layer = dict(layer, blur=_n(soften * 0.7))  # a soft light
        layers.append(layer)
    x0, y0, x1, y1 = _body_box(r.layers, r.w, r.h)
    bw, bh = x1 - x0, y1 - y0
    seed = sum(ord(ch) for ch in r.id) % 9973
    # the layers of the finish cover the whole canvas (a glow outside the body would show the edge of a smaller box)
    whole = {"rect": [0, 0, _n(r.w), _n(r.h)]}
    if sky > 0:  # the light of the sky on the upper edges
        layers.append({"shape": whole,
                       "fill": linear(x0, y0, x0 + bw * 0.25, y0 + bh * 0.55, (0, "#FFF6E0"), (1, "#FFF6E000")),
                       "blend": "add", "clip": True, "alpha": _n(sky)})
    if form > 0:  # the volume: shade on the side away from the light, which comes from the top left
        cx, cy = x0 + bw * 0.3, y0 + bh * 0.22
        rad = max(bw, bh) * 1.05
        layers.append({"shape": whole,
                       "fill": radial(cx, cy, rad, (0, "#FFFFFF"), (0.38, "#FFFFFF"), (1, "#4A4068")),
                       "blend": "multiply", "alpha": _n(form)})
    if grain > 0:  # the grain of the matter
        layers.append({"shape": whole,
                       "fill": noise(0.7, seed, (0.28, "#9C94A4"), (0.6, "#FFFFFF"), octaves=3),
                       "blend": "multiply", "alpha": _n(grain)})
    if wear > 0:  # the wear of things: scratches, pits and fine cracks
        layers.append({"shape": whole,
                       "fill": noise(1.2, seed + 1, (0.72, "#FFFFFF"), (0.94, "#3A3040"), octaves=3, ridged=True),
                       "blend": "multiply", "alpha": _n(wear)})
    if not palette:  # the palette is read back from the file it is written to (the creatures): it is left as it is
        return layers, dict(r.palette), dict(r.variants)
    palette = {k: desaturate(v, desat) for k, v in r.palette.items()}
    variants = {name: {k: desaturate(v, desat) for k, v in colors.items()} for name, colors in r.variants.items()}
    return layers, palette, variants
