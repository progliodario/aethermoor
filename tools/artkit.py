"""A small toolkit to build art recipes (schemas/art_recipe.schema.json) from code: layers, color math and seeded details.

`tools/make_art.py` uses it to write the recipes of data/base/art/. The recipes are plain JSON in the end: the game never runs this code.
Style rules (docs/design/art-style.md): light from the top left, three tones (shade, base, light), a dark outline on objects and none on tiles,
soft shadow ellipses under things that stand on the ground.
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
        self.rng = random.Random(f"{recipe_id}/{seed}")

    # --- layers
    def add(self, shape: dict, fill=None, stroke=None, width: float = 1.0, alpha: float | None = None, only=None) -> "Recipe":
        layer: dict = {"shape": shape}
        if fill is not None:
            layer["fill"] = fill if isinstance(fill, dict) else {"color": fill}
        if stroke is not None:
            layer["stroke"] = {"color": stroke, "width": width}
        if alpha is not None and alpha < 1:
            layer["alpha"] = round(alpha, 3)
        if only:
            layer["only"] = list(only)
        self.layers.append(layer)
        return self

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

    def shadow(self, cx, cy, rx, ry, alpha=0.28):
        """The soft shadow of something standing on the ground."""
        self.ellipse(cx, cy, rx, ry, "#000000", alpha=alpha)
        self.ellipse(cx, cy, rx * 0.72, ry * 0.7, "#000000", alpha=alpha * 0.6)
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
        data = {
            "$schema": "../../../../schemas/art_recipe.schema.json",
            "id": self.id,
            "canvas": {"w": _n(self.w), "h": _n(self.h), "origin": [_n(self.origin[0]), _n(self.origin[1])]},
            "layers": self.layers,
            "palette": self.palette,
        }
        if self.variants:
            data["variants"] = self.variants
        return data

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.to_json()
        # the schema reference is relative to the folder of the file
        depth = len(path.relative_to(ROOT).parts) - 1
        data["$schema"] = "../" * depth + "schemas/art_recipe.schema.json"
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _n(v):
    """A short number: integers without a dot, others with at most two decimals."""
    v = round(float(v), 2)
    return int(v) if v == int(v) else v


def linear(x0, y0, x1, y1, *stops):
    """A linear gradient fill: stops are (t, color) pairs."""
    return {"linear": {"x0": _n(x0), "y0": _n(y0), "x1": _n(x1), "y1": _n(y1), "stops": [[t, c] for t, c in stops]}}


def radial(cx, cy, r, *stops):
    return {"radial": {"cx": _n(cx), "cy": _n(cy), "r": _n(r), "stops": [[t, c] for t, c in stops]}}


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
        out.append(new)
    return out
