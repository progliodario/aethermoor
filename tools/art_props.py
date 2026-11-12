"""The props of data/base/art/props/: trees, rocks, camp and town things, painted in the anime way (docs/design/art-style.md).

Every prop has its origin at its foot (the draw order and the collision of the world data use it), a soft shadow on the
ground, a thin dark line in its own hue, flat tones broken by a noise fill, a hard violet shade on the side away from the
light (top left) and a warm rim where the light lands. Used by `make_art.py`.
"""
from __future__ import annotations

import math

from artkit import ART, Recipe, darken, lighten, linear, mix, noise, radial  # noqa: F401

INK = "#1E1830"


def prop(name: str, w, h, origin, palette: dict) -> Recipe:
    return Recipe(f"base:art/prop/{name}", w, h, origin, palette, seed="v3")


def wobble(r: Recipe, cx: float, cy: float, rx: float, ry: float, n: int = 9, jitter: float = 0.18) -> str:
    """A closed organic outline around an ellipse: n bumps of slightly different sizes."""
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n + r.rng.uniform(-0.15, 0.15)
        m = 1 + r.rng.uniform(-jitter, jitter)
        pts.append((cx + math.cos(a) * rx * m, cy + math.sin(a) * ry * m))
    mids = [((pts[i][0] + pts[(i + 1) % n][0]) / 2, (pts[i][1] + pts[(i + 1) % n][1]) / 2) for i in range(n)]
    d = f"M {mids[-1][0]:.2f} {mids[-1][1]:.2f}"
    for i in range(n):
        # push the control point outward so that every bump is round
        px, py = pts[i]
        ox, oy = px + (px - cx) * 0.22, py + (py - cy) * 0.22
        d += f" Q {ox:.2f} {oy:.2f} {mids[i][0]:.2f} {mids[i][1]:.2f}"
    return d + " Z"


def ell(cx: float, cy: float, rx: float, ry: float) -> str:
    """An ellipse as a path (for shade() and lit(), which take paths)."""
    k = 0.5523
    return (f"M {cx - rx:.2f} {cy:.2f} C {cx - rx:.2f} {cy - ry * k:.2f} {cx - rx * k:.2f} {cy - ry:.2f} {cx:.2f} {cy - ry:.2f} "
            f"C {cx + rx * k:.2f} {cy - ry:.2f} {cx + rx:.2f} {cy - ry * k:.2f} {cx + rx:.2f} {cy:.2f} "
            f"C {cx + rx:.2f} {cy + ry * k:.2f} {cx + rx * k:.2f} {cy + ry:.2f} {cx:.2f} {cy + ry:.2f} "
            f"C {cx - rx * k:.2f} {cy + ry:.2f} {cx - rx:.2f} {cy + ry * k:.2f} {cx - rx:.2f} {cy:.2f} Z")


def box(x: float, y: float, w: float, h: float) -> str:
    return f"M {x:.2f} {y:.2f} L {x + w:.2f} {y:.2f} L {x + w:.2f} {y + h:.2f} L {x:.2f} {y + h:.2f} Z"


def wood(seed: int, tone: str, scale: float = 5.0):
    return noise(scale, seed, (0.3, darken(tone, 0.16)), (0.5, tone), (0.72, lighten(tone, 0.14)), octaves=3)


def stone(seed: int, tone: str, scale: float = 5.0):
    return noise(scale, seed, (0.28, darken(tone, 0.2)), (0.5, tone), (0.74, lighten(tone, 0.18)), octaves=3)


# ------------------------------------------------------------------------------------------------ trees and plants
def crown(r: Recipe, clumps: list[tuple[float, float, float, float]], dark: str, mid: str, light: str, seed: int, ink: str,
          tip: str | None = None) -> None:
    """The foliage of a tree: clumps drawn back to front, each one dark below, lit from the top left, with leaf strokes."""
    for i, (cx, cy, rx, ry) in enumerate(clumps):
        outline = wobble(r, cx, cy, rx, ry, 10, 0.14)
        r.path(outline, noise(rx * 0.7, seed + i, (0.25, dark), (0.5, mid), (0.85, light), octaves=3), stroke=ink, width=0.45)
        # the lower right of the clump is in shade, the upper left catches the light
        r.shade(ell(cx + rx * 0.3, cy + ry * 0.5, rx * 1.05, ry * 0.8), 0.5, blur=rx * 0.22, clip=True)
        r.lit(wobble(r, cx - rx * 0.28, cy - ry * 0.36, rx * 0.62, ry * 0.5, 8, 0.2), 0.5, light, blur=rx * 0.1)
        for _ in range(int(rx * 1.6)):  # leaves picked out by the light
            a, m = r.rng.uniform(0, 2 * math.pi), r.rng.uniform(0, 0.8)
            lx, ly = cx - rx * 0.2 + math.cos(a) * rx * m * 0.8, cy - ry * 0.25 + math.sin(a) * ry * m * 0.7
            s = r.rng.uniform(0.7, 1.4)
            r.path(f"M {lx - s:.2f} {ly + s * 0.3:.2f} Q {lx:.2f} {ly - s * 0.9:.2f} {lx + s:.2f} {ly - s * 0.2:.2f} Q {lx:.2f} {ly + s * 0.2:.2f} {lx - s:.2f} {ly + s * 0.3:.2f} Z",
                   tip or light, alpha=r.rng.uniform(0.45, 0.9), clip=True)
        for _ in range(int(rx * 0.8)):  # dark gaps between the leaves
            a, m = r.rng.uniform(0, 2 * math.pi), r.rng.uniform(0.2, 0.85)
            lx, ly = cx + rx * 0.15 + math.cos(a) * rx * m * 0.8, cy + ry * 0.2 + math.sin(a) * ry * m * 0.7
            s = r.rng.uniform(0.6, 1.2)
            r.ellipse(lx, ly, s, s * 0.6, "#0A2418", alpha=0.4, clip=True)


def trunk(r: Recipe, x: float, foot: float, top: float, w: float, tone: str, seed: int, roots: bool = True) -> None:
    d = (f"M {x - w * 0.5:.2f} {top:.2f} L {x + w * 0.5:.2f} {top:.2f} Q {x + w * 0.42:.2f} {(top + foot) / 2:.2f} {x + w * 0.62:.2f} {foot - 2:.2f} "
         + (f"L {x + w * 1.1:.2f} {foot:.2f} L {x + w * 0.2:.2f} {foot - 0.6:.2f} L {x:.2f} {foot + 0.8:.2f} L {x - w * 0.3:.2f} {foot - 0.6:.2f} L {x - w * 1.15:.2f} {foot:.2f} "
            if roots else f"L {x + w * 0.62:.2f} {foot:.2f} L {x - w * 0.62:.2f} {foot:.2f} ")
         + f"L {x - w * 0.62:.2f} {foot - 2:.2f} Q {x - w * 0.42:.2f} {(top + foot) / 2:.2f} {x - w * 0.5:.2f} {top:.2f} Z")
    r.path(d, wood(seed, tone, 3.5), stroke=INK, width=0.45)
    r.shade(box(x + w * 0.05, top, w * 1.2, foot - top + 1), 0.55, blur=0.6, clip=True)
    r.lit(box(x - w * 0.7, top, w * 0.3, foot - top), 0.3, "#FFE8B8", blur=0.4)
    for k in range(4):  # the bark
        bx = x - w * 0.3 + k * w * 0.2
        r.path(f"M {bx:.2f} {top + 2 + k:.2f} Q {bx + 0.6:.2f} {(top + foot) / 2:.2f} {bx - 0.3:.2f} {foot - 3 - k:.2f}", None, stroke=darken(tone, 0.55), width=0.3, alpha=0.6, clip=True)


def tree_oak() -> Recipe:
    r = prop("tree_oak", 96, 128, (48, 120), {"trunk": "#7A5236", "leaf": "#3E8E45", "leaf_light": "#9AD86A", "leaf_dark": "#1F5A3A"})
    r.shadow(50, 120, 30, 7, 0.4)
    trunk(r, 48, 120, 62, 9, "#7A5236", 201)
    r.path("M 44 86 Q 34 80 30 70", None, stroke=INK, width=3.4)
    r.path("M 44 86 Q 34 80 30 70", None, stroke="#6A4630", width=2.6)
    r.path("M 52 82 Q 62 76 66 66", None, stroke=INK, width=3.0)
    r.path("M 52 82 Q 62 76 66 66", None, stroke="#553824", width=2.2)
    clumps = [(48, 62, 34, 22), (24, 56, 17, 15), (72, 56, 17, 15), (36, 36, 21, 17), (62, 36, 20, 17), (48, 20, 20, 15), (30, 68, 14, 10), (64, 70, 14, 9), (48, 50, 18, 14)]
    crown(r, clumps, "$p.leaf_dark", "$p.leaf", "$p.leaf_light", 211, "#143A2A")
    r.variants = {"autumn": {"leaf": "#D2813A", "leaf_light": "#F8C860", "leaf_dark": "#8A3E22"}}
    return r


def pine() -> Recipe:
    r = prop("pine", 80, 128, (40, 120), {"trunk": "#6B4A32", "dark": "#1E5A44", "mid": "#2F7A58", "light": "#6FBE84", "snow": "#F4F8FF"})
    r.shadow(42, 120, 22, 6, 0.4)
    trunk(r, 40, 120, 92, 6.5, "#6B4A32", 221)
    tiers = [(96, 30, 22), (78, 26, 22), (60, 21, 21), (43, 16, 19), (27, 11, 17)]
    for i, (base_y, half, height) in enumerate(tiers):
        top = base_y - height
        pts = [(40, top)]
        teeth = 5
        for k in range(teeth + 1):  # the ragged lower edge, right to left
            x = 40 + half - k * (2 * half / teeth)
            pts.append((x, base_y - (2.5 if k in (0, teeth) else 0) + r.rng.uniform(-1, 1)))
            if k < teeth:
                pts.append((x - half / teeth, base_y - 5 + r.rng.uniform(-1, 1)))
        d = "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z"
        r.ellipse(40, base_y - 1, half * 0.8, 3, "#0A2A20", alpha=0.5, blur=1.2, clip=True)  # the shade under a tier, on the one below
        r.path(d, noise(6, 231 + i, (0.25, "$p.dark"), (0.5, "$p.mid"), (0.78, "$p.light"), octaves=3), stroke="#0E3226", width=0.45)
        r.shade(f"M 40 {top} L {40 + half} {base_y} L {40 + half * 0.1:.1f} {base_y} L {40 + half * 0.25:.1f} {top + height * 0.5:.1f} Z", 0.5, blur=1.0, clip=True)
        for _ in range(int(half * 0.9)):  # needles
            nx = 40 + r.rng.uniform(-half * 0.7, half * 0.5)
            ny = r.rng.uniform(top + height * 0.35, base_y - 3)
            if abs(nx - 40) > half * (ny - top) / height:
                continue
            r.path(f"M {nx:.2f} {ny:.2f} L {nx - 1.6:.2f} {ny + 2.6:.2f} L {nx + 0.6:.2f} {ny + 1.8:.2f} Z", "$p.light", alpha=r.rng.uniform(0.3, 0.7), clip=True)
        # snow on the upper left of the tier
        r.path(f"M 40 {top} L {40 - half * 0.42:.1f} {top + height * 0.5:.1f} Q {40 - half * 0.25:.1f} {top + height * 0.42:.1f} {40 - half * 0.1:.1f} {top + height * 0.56:.1f} "
               f"Q {40 + half * 0.05:.1f} {top + height * 0.4:.1f} {40 + half * 0.2:.1f} {top + height * 0.46:.1f} Z",
               linear(40 - half, top, 40 + half, top + height, (0, "$p.snow"), (1, "#B4C8F0")), stroke="#7A90C0", width=0.25)
    return r


def dead_tree() -> Recipe:
    r = prop("dead_tree", 80, 112, (40, 104), {"trunk": "#5A4A48", "dark": "#2A2028", "light": "#9A8A84"})
    r.shadow(42, 104, 18, 5, 0.38)
    limbs = [("M 40 60 Q 30 46 16 40 Q 12 34 10 24", 3.2), ("M 40 54 Q 50 40 62 36 Q 68 28 70 18", 3.0), ("M 40 44 Q 36 30 38 12", 3.4),
             ("M 22 42 Q 20 34 24 26", 1.8), ("M 58 37 Q 56 28 50 22", 1.8), ("M 38 28 Q 44 22 48 12", 1.6), ("M 14 34 Q 8 34 4 30", 1.3), ("M 66 28 Q 72 28 76 24", 1.3)]
    trunk(r, 40, 104, 44, 10, "#5A4A48", 241)
    for d, w in limbs:
        r.path(d, None, stroke=INK, width=w + 0.9)
    for d, w in limbs:
        r.path(d, None, stroke="$p.trunk", width=w)
    for d, w in limbs:  # the light along the upper left of the limbs
        r.path(d, None, stroke="$p.light", width=w * 0.3, alpha=0.6, clip=True)
    r.path("M 37 70 Q 34 76 37 83 Q 41 86 43 80 Q 44 73 37 70 Z", "#140E18", stroke=INK, width=0.3)  # a hollow
    r.path("M 38 72 Q 36 76 38 81", None, stroke="#7A6A64", width=0.4, alpha=0.7)
    return r


def bush() -> Recipe:
    r = prop("bush", 40, 30, (20, 26), {"leaf": "#3E8E45", "light": "#9AD86A", "dark": "#1F5A3A", "berry": "#E0402E"})
    r.shadow(21, 26, 16, 4, 0.36)
    crown(r, [(20, 17, 15, 8.5), (10, 15, 8, 7), (30, 15, 8, 7), (20, 10, 10, 7)], "$p.dark", "$p.leaf", "$p.light", 251, "#143A2A")
    for x, y in ((9, 15), (15, 9), (24, 12), (30, 17), (19, 19), (27, 21), (12, 20)):
        r.ellipse(x + 0.2, y + 0.3, 1.3, 1.3, "#5A0E18")
        r.ellipse(x, y, 1.2, 1.2, radial(x - 0.4, y - 0.4, 1.6, (0, "#FF9A7A"), (0.5, "$p.berry"), (1, "#8A1420")))
        r.ellipse(x - 0.4, y - 0.4, 0.3, 0.3, "#FFFFFF", alpha=0.9)
    return r


def rock() -> Recipe:
    r = prop("rock", 36, 30, (18, 26), {"base": "#8D949F", "light": "#D0D6E0", "dark": "#4A4E60"})
    r.shadow(19.5, 26, 15, 4, 0.4)
    body = "M 3 25 L 4 15 L 10 7 L 19 4 L 28 8 L 33 17 L 32 25 Q 18 28 3 25 Z"
    r.path(body, stone(261, "#8D949F", 6), stroke=INK, width=0.5)
    r.shade("M 19 4 L 28 8 L 33 17 L 32 25 L 16 27 L 20 15 Z", 0.55, clip=True)
    r.shade("M 3 25 L 4 21 Q 18 25 32 21 L 32 25 Q 18 28 3 25 Z", 0.4, blur=0.8, clip=True)
    r.lit("M 4 15 L 10 7 L 19 4 L 20 15 L 11 13 Z", 0.4, "#FFF0D0")
    r.path("M 10 7 L 11 13 L 4 15 M 11 13 L 20 15 L 19 4 M 20 15 L 16 27", None, stroke=INK, width=0.3, alpha=0.6)
    r.path("M 23 12 L 25 16 L 24 19", None, stroke=INK, width=0.3, alpha=0.7)
    r.ellipse(8, 24, 5, 1.8, "#5E9A50", alpha=0.75, blur=0.5, clip=True)  # moss
    r.ellipse(27, 24.5, 3.5, 1.4, "#5E9A50", alpha=0.6, blur=0.5, clip=True)
    return r


def cactus() -> Recipe:
    r = prop("cactus", 36, 52, (18, 48), {"body": "#4FA060", "rib": "#2F7A4A", "light": "#A8E090"})
    r.shadow(19, 48, 11, 3.2, 0.38)

    def limb(d: str, cx: float, top: float, bottom: float, w: float) -> None:
        r.path(d, noise(4, 271, (0.3, "#3A8A52"), (0.6, "$p.body"), (0.8, "#6FBE74"), octaves=2), stroke="#12382A", width=0.5)
        r.shade(box(cx + w * 0.1, top, w, bottom - top), 0.5, blur=0.5, clip=True)
        r.lit(box(cx - w * 0.5, top, w * 0.22, bottom - top), 0.4, "#E8FFC0", blur=0.3)
        for k in (-0.25, 0.05, 0.3):  # ribs with their thorns
            r.line(cx + w * k, top + 2, cx + w * k, bottom - 1, "$p.rib", 0.35, alpha=0.8)
        for k in range(int((bottom - top) / 3.5)):
            y = top + 3 + k * 3.5
            for sx in (-0.5, 0.5):
                r.line(cx + sx * w, y, cx + sx * (w + 1.6), y - 0.8, "#F4F0D8", 0.25)

    limb("M 6 30 Q 6 22 9.5 22 Q 13 22 13 30 L 13 34 L 6 34 Z", 9.5, 22, 34, 7)
    r.rect(8, 31, 6, 5, "$p.body", stroke="#12382A", width=0.4)
    limb("M 23 26 Q 23 17 26.5 17 Q 30 17 30 26 L 30 30 L 23 30 Z", 26.5, 17, 30, 7)
    r.rect(22, 26.5, 6, 5, "$p.body", stroke="#12382A", width=0.4)
    limb("M 12 47 L 12 12 Q 12 4 18 4 Q 24 4 24 12 L 24 47 Z", 18, 4, 47, 12)
    r.ellipse(18, 4.5, 2.2, 1.8, radial(17.4, 4, 2.6, (0, "#FFD0E0"), (1, "#E0508A")), stroke="#7A1E48", width=0.3)  # a flower
    r.ellipse(18, 4.5, 0.7, 0.6, "#FFE070")
    return r


def reeds() -> Recipe:
    r = prop("reeds", 36, 34, (18, 30), {"reed": "#7FA44A", "light": "#C8E088", "dark": "#3E6230", "water": "#4A8AC8"})
    r.ellipse(18, 29.5, 15, 3.6, "#2F6FC8", alpha=0.45, blur=1.0)
    r.ellipse(15, 29, 8, 1.4, "#CFE8FF", alpha=0.5, blur=0.5)
    for i in range(13):
        x = 5 + i * 2.1 + r.rng.uniform(-0.6, 0.6)
        top = r.rng.uniform(5, 14)
        lean = r.rng.uniform(-2.5, 2.5)
        c = mix("#3E6230", "#C8E088", r.rng.random())
        r.path(f"M {x - 0.5:.2f} 29.5 Q {x + lean * 0.3:.2f} {(top + 29.5) / 2:.2f} {x + lean:.2f} {top:.2f} Q {x + lean * 0.4 + 0.4:.2f} {(top + 29.5) / 2:.2f} {x + 0.5:.2f} 29.5 Z", c, stroke="#22341A", width=0.2)
        if i % 3 == 0:  # a cattail
            hx, hy = x + lean * 0.75, top + 4
            r.path(f"M {hx - 0.9:.2f} {hy - 2.6:.2f} Q {hx:.2f} {hy - 3.4:.2f} {hx + 0.9:.2f} {hy - 2.6:.2f} L {hx + 0.9:.2f} {hy + 2.2:.2f} Q {hx:.2f} {hy + 3:.2f} {hx - 0.9:.2f} {hy + 2.2:.2f} Z",
                   linear(hx - 1, hy, hx + 1, hy, (0, "#9A6A40"), (1, "#4A2C18")), stroke="#24140A", width=0.25)
    return r


def mushrooms() -> Recipe:
    r = prop("mushrooms", 32, 26, (16, 22), {"cap": "#C8483A", "light": "#FF9A7A", "stem": "#F6ECD6", "moss": "#4E8A3E"})
    r.shadow(16.5, 22, 13, 3.4, 0.36)
    r.ellipse(16, 21.5, 12, 2.6, "$p.moss", alpha=0.8, blur=0.8)
    for (x, y, s) in ((21, 12, 0.8), (9, 13.5, 0.7), (15, 9, 1.15)):
        r.path(f"M {x - 1.6 * s:.2f} {y:.2f} Q {x - 2 * s:.2f} {y + 5 * s:.2f} {x - 2.4 * s:.2f} {y + 9 * s:.2f} L {x + 2.4 * s:.2f} {y + 9 * s:.2f} Q {x + 2 * s:.2f} {y + 5 * s:.2f} {x + 1.6 * s:.2f} {y:.2f} Z",
               linear(x - 2 * s, y, x + 2 * s, y, (0, "#FFFFFF"), (0.4, "$p.stem"), (1, "#B8A88A")), stroke=INK, width=0.35)
        r.shade(box(x - 2.5 * s, y, 5 * s, 2.4 * s), 0.5, blur=0.5, clip=True)
        cap = (f"M {x - 7 * s:.2f} {y + 1 * s:.2f} Q {x - 6 * s:.2f} {y - 6 * s:.2f} {x:.2f} {y - 6.4 * s:.2f} Q {x + 6 * s:.2f} {y - 6 * s:.2f} {x + 7 * s:.2f} {y + 1 * s:.2f} "
               f"Q {x:.2f} {y + 2.6 * s:.2f} {x - 7 * s:.2f} {y + 1 * s:.2f} Z")
        r.path(cap, radial(x - 2.5 * s, y - 4 * s, 9 * s, (0, "$p.light"), (0.5, "$p.cap"), (1, "#7A1E2A")), stroke=INK, width=0.4)
        r.shade(f"M {x + 1 * s:.2f} {y - 6.4 * s:.2f} Q {x + 6 * s:.2f} {y - 6 * s:.2f} {x + 7 * s:.2f} {y + 1 * s:.2f} Q {x + 3 * s:.2f} {y + 2.2 * s:.2f} {x + 2 * s:.2f} {y + 2.2 * s:.2f} Q {x + 4 * s:.2f} {y - 2 * s:.2f} {x + 1 * s:.2f} {y - 6.4 * s:.2f} Z", 0.4, clip=True)
        for dx, dy, q in ((-3, -3, 0.9), (1.5, -4.2, 0.7), (3.6, -1.2, 0.6), (-1, -1, 0.6), (-4.8, -0.4, 0.5)):
            r.ellipse(x + dx * s, y + dy * s, q * s, q * s * 0.75, "#FFF8EC", clip=True)
    return r


# ------------------------------------------------------------------------------------------------ camp and road
def campfire() -> Recipe:
    r = prop("campfire", 36, 40, (18, 34), {"log": "#7A5232", "flame": "#FF7A1E", "core": "#FFE880", "ash": "#5A5550"})
    r.shadow(18, 34, 15, 4, 0.36)
    r.glow(18, 28, 20, "#FF8A30", 0.4)
    for k in range(9):  # a ring of stones
        a = 2 * math.pi * k / 9
        x, y = 18 + math.cos(a) * 12, 33 + math.sin(a) * 3.6
        r.ellipse(x, y, 2.6, 1.9, stone(281 + k, "#8A8C98", 2), stroke=INK, width=0.3)
        r.ellipse(x - 0.5, y - 0.6, 1.2, 0.6, "#FFD0A0", alpha=0.5)
    r.ellipse(18, 32.5, 9, 2.6, "#2A2028")
    for d in ("M 8 33 L 26 28", "M 28 33 L 10 28"):
        r.path(d, None, stroke=INK, width=4.0)
        r.path(d, None, stroke="$p.log", width=3.2)
        r.path(d, None, stroke="#C89060", width=0.8, alpha=0.6)
    r.ellipse(18, 31, 5, 1.6, "#FF5A1E", alpha=0.9, blur=0.8)
    flame = "M 18 4 Q 23 12 26 19 Q 28.5 26 24 30.5 Q 18 33.5 12 30.5 Q 7.5 26 10.5 19 Q 12.5 15 13 11 Q 15.5 13 15.5 16 Q 17 10 18 4 Z"
    r.path(flame, linear(18, 4, 18, 32, (0, "#FF4A1E"), (0.5, "$p.flame"), (1, "#FFC040")), blur=0.4)
    r.path("M 18 12 Q 21.5 18 23 23 Q 24 28 20.5 30 Q 18 31 15.5 30 Q 12 28 13.5 23 Q 14.5 20 16 18 Q 17 16 18 12 Z", linear(18, 12, 18, 31, (0, "#FFB030"), (1, "$p.core")), blur=0.3)
    r.path("M 18 20 Q 20 24 20 27 Q 20 30 18 30 Q 16 30 16 27 Q 16 24 18 20 Z", "#FFFBE8", blur=0.3)
    for x, y in ((11, 9), (25, 7), (21, 2), (14, 3)):  # sparks
        r.ellipse(x, y, 0.5, 0.5, "#FFE080")
        r.glow(x, y, 2, "#FF9A30", 0.5)
    return r


def crate() -> Recipe:
    r = prop("crate", 30, 30, (15, 26), {"wood": "#B07C44", "light": "#E8B878", "dark": "#5E3C1E"})
    r.shadow(16.5, 26, 14, 3.4, 0.4)
    r.path("M 3 9 L 9 4 L 27 4 L 27 21 L 21 26 L 3 26 Z", "$p.dark", stroke=INK, width=0.5)
    r.path("M 3 9 L 9 4 L 27 4 L 21 9 Z", wood(291, "#D0A064", 4), stroke=INK, width=0.4)  # the top
    r.path("M 21 9 L 27 4 L 27 21 L 21 26 Z", wood(292, "#7A5028", 4), stroke=INK, width=0.4)  # the side in shade
    r.rect(3, 9, 18, 17, wood(293, "#B07C44", 4), stroke=INK, width=0.4)
    for y in (13.2, 17.4, 21.6):
        r.line(3.4, y, 20.6, y, "#3E2410", 0.35, alpha=0.7)
    r.path("M 3 9 L 6 9 L 21 23 L 21 26 L 18 26 L 3 12 Z", wood(294, "#9A6836", 4), stroke=INK, width=0.35)  # the brace
    for x in (3, 18):
        r.rect(x, 9, 3, 17, wood(295, "#C08A50", 4), stroke=INK, width=0.35)
    r.rect(3, 9, 18, 1.0, "#FFF0D0", alpha=0.4)
    for x, y in ((4.5, 10.8), (19.5, 10.8), (4.5, 24.4), (19.5, 24.4)):
        r.ellipse(x, y, 0.5, 0.5, "#2A1608")
    return r


def barrel() -> Recipe:
    r = prop("barrel", 26, 32, (13, 28), {"wood": "#9A6A38", "top": "#C89A60", "band": "#5A5E6A"})
    r.shadow(14, 28, 12, 3.2, 0.4)
    body = "M 4 7 Q 1.5 17 4 27 Q 13 30.5 22 27 Q 24.5 17 22 7 Z"
    r.path(body, wood(301, "#9A6A38", 4), stroke=INK, width=0.5)
    for x in (7.5, 10.5, 13.5, 16.5, 19):  # staves
        r.path(f"M {x} 8 Q {x + (x - 13) * 0.12:.2f} 17 {x} 28", None, stroke="#3E2410", width=0.3, alpha=0.7, clip=True)
    r.shade("M 15 6 L 23 6 Q 25 17 22.5 28 L 14 30 Q 18 17 15 6 Z", 0.5, blur=0.8, clip=True)
    r.lit("M 4.5 8 Q 2.5 17 4.5 26 L 7 26.5 Q 5 17 7 8 Z", 0.4, "#FFE8B8", blur=0.4)
    for y in (10.5, 23.5):  # iron bands
        r.path(f"M 2.9 {y} Q 13 {y + 2.6} 23.1 {y} L 23.2 {y + 2.2} Q 13 {y + 4.8} 2.8 {y + 2.2} Z",
               linear(3, 0, 23, 0, (0, "#B8BCC8"), (0.4, "$p.band"), (1, "#2A2C38")), stroke=INK, width=0.3)
    r.ellipse(13, 7, 9, 2.8, wood(302, "#C89A60", 3), stroke=INK, width=0.45)
    r.ellipse(13, 7, 7.2, 2.0, "#2A1608", alpha=0.25)
    r.ellipse(11, 6.4, 3.5, 0.8, "#FFF0D0", alpha=0.4, blur=0.3)
    return r


def bones() -> Recipe:
    r = prop("bones", 34, 22, (17, 18), {"bone": "#EFE7D2", "dark": "#A89E84", "socket": "#1E1B28"})
    r.shadow(17.5, 18, 14, 3, 0.32)
    fill = linear(0, 4, 0, 20, (0, "#FFFBEE"), (0.6, "$p.bone"), (1, "$p.dark"))
    for d in ("M 4 15 L 30 9", "M 5 9 L 29 16"):  # crossed bones with knobbed ends
        r.path(d, None, stroke=INK, width=3.4)
        r.path(d, None, stroke="$p.bone", width=2.5)
    for x, y in ((4, 15), (30, 9), (5, 9), (29, 16)):
        for dx, dy in ((-0.9, -0.9), (0.9, 0.9)):
            r.ellipse(x + dx, y + dy, 1.9, 1.7, fill, stroke=INK, width=0.4)
    skull = "M 10.5 9 Q 10.5 2 17 2 Q 23.5 2 23.5 9 Q 23.5 12 21.5 13 L 21.5 16 L 12.5 16 L 12.5 13 Q 10.5 12 10.5 9 Z"
    r.path(skull, fill, stroke=INK, width=0.5)
    r.shade("M 18 2 Q 23.5 2 23.5 9 Q 23.5 12 21.5 13 L 21.5 16 L 17 16 Q 20 9 18 2 Z", 0.35, clip=True)
    for x in (14.2, 19.8):
        r.ellipse(x, 8.6, 1.9, 2.1, "$p.socket")
        r.ellipse(x + 0.5, 9.2, 0.6, 0.7, "#3A3050")
    r.poly([(17, 10.6), (17.9, 12.6), (16.1, 12.6)], "$p.socket")
    for x in (14, 15.5, 17, 18.5, 20):
        r.line(x, 13.6, x, 16, INK, 0.3)
    r.path("M 13 4.5 Q 15 3 17.5 3", None, stroke="#FFFFFF", width=0.6, alpha=0.8)
    return r


def lamp() -> Recipe:
    r = prop("lamp", 24, 48, (12, 44), {"pole": "#3A3A48", "glow": "#FFD878", "core": "#FFF6CC"})
    r.shadow(12.5, 44, 7, 2.2, 0.38)
    r.glow(12, 11, 16, "#FFC860", 0.45)
    r.path("M 8.5 44 L 9.5 40.5 L 14.5 40.5 L 15.5 44 Z", linear(8, 0, 16, 0, (0, "#7A7A8C"), (1, "#1E1E2A")), stroke=INK, width=0.4)
    r.rect(10.9, 17, 2.2, 24, linear(10.9, 0, 13.1, 0, (0, "#8A8A9C"), (0.4, "$p.pole"), (1, "#16161E")), stroke=INK, width=0.35)
    r.rect(10.2, 26, 3.6, 1.4, "$p.pole", stroke=INK, width=0.3)
    r.path("M 7 17 L 17 17 L 15.5 19 L 8.5 19 Z", "$p.pole", stroke=INK, width=0.35)
    r.path("M 8 17 L 7 7.5 L 17 7.5 L 16 17 Z", linear(12, 7, 12, 17, (0, "$p.core"), (1, "$p.glow")), stroke=INK, width=0.4)  # the glass
    r.ellipse(12, 12.5, 2.2, 3.2, "#FFFFFF", alpha=0.9, blur=0.8)
    r.line(12, 7.5, 12, 17, INK, 0.3, alpha=0.6)
    r.path("M 5.5 7.8 L 12 2.5 L 18.5 7.8 Z", linear(5, 0, 19, 0, (0, "#6A6A7C"), (1, "#1E1E2A")), stroke=INK, width=0.4)  # the cap
    r.ellipse(12, 2.4, 1.0, 1.0, "$p.pole", stroke=INK, width=0.3)
    return r


def signpost() -> Recipe:
    r = prop("signpost", 28, 36, (14, 33), {"wood": "#9A6C3E", "light": "#D8A870", "dark": "#5E3E1E", "ink": "#2A1808"})
    r.shadow(14.5, 33, 8, 2.2, 0.38)
    r.rect(12.6, 6, 2.8, 27, wood(311, "#7A5230", 3), stroke=INK, width=0.4)
    r.shade(box(14, 6, 1.6, 27), 0.5, clip=True)
    for y, d in ((8, "M 3 8 L 21 8 L 25.5 11.5 L 21 15 L 3 15 Z"), (18, "M 25 18 L 8 18 L 3.5 21.5 L 8 25 L 25 25 Z")):
        r.path(d, wood(312 + y, "#B88450", 4), stroke=INK, width=0.45)
        r.rect(3, y, 22.5, 1.0, "#FFF0D0", alpha=0.35, clip=True)
        r.rect(3, y + 5.6, 22.5, 1.4, "#2A1E4A", alpha=0.35, clip=True)
        for k in range(3):
            r.line(7 + k * 4, y + 2.6, 9.6 + k * 4, y + 2.6, "$p.ink", 0.5, alpha=0.8)
            r.line(7 + k * 4.4, y + 4.4, 9 + k * 4.4, y + 4.4, "$p.ink", 0.4, alpha=0.6)
        r.ellipse(14, y + 3.5, 0.6, 0.6, "#2A1608")
    r.ellipse(11, 32.5, 3, 1.2, "#5E9A50", alpha=0.8, blur=0.4)
    return r


def tent() -> Recipe:
    r = prop("tent", 52, 42, (26, 37), {"cloth": "#C9A66B", "light": "#F4E0B0", "dark": "#7A5A34", "stripe": "#B8483A", "pole": "#6A4A2A"})
    r.shadow(27, 37, 25, 5, 0.4)
    r.path("M 26 5 L 48 36 L 4 36 Z", noise(6, 321, (0.3, "#B8945A"), (0.5, "$p.cloth"), (0.75, "$p.light"), octaves=3), stroke=INK, width=0.5)
    r.shade("M 26 5 L 48 36 L 30 36 Z", 0.5, clip=True)
    r.lit("M 26 5 L 4 36 L 9 36 L 26 11 Z", 0.35, "#FFF4D0")
    r.path("M 26 12 L 34 36 L 18 36 Z", linear(26, 12, 26, 36, (0, "#1A1024"), (1, "#3A2A30")), stroke=INK, width=0.4)  # the opening
    r.path("M 26 12 L 18 36 L 13 36 L 24.5 12 Z", "$p.light", stroke=INK, width=0.35)  # a flap tied back
    r.path("M 14.5 30 L 43.5 30 L 45.5 33 L 12.5 33 Z", "$p.stripe", alpha=0.85, clip=True)
    r.path("M 26 12 L 34 36 L 18 36 Z", "#1A1024", alpha=0.9)
    r.path("M 26 12 L 18 36 L 13 36 L 24.5 12 Z", "$p.light", stroke=INK, width=0.35)
    r.line(26, 1.5, 26, 6, "$p.pole", 1.0)
    r.path("M 26 1.5 L 32 3 L 26 4.8 Z", "$p.stripe", stroke=INK, width=0.3)
    for x0, x1 in ((4, 0.8), (48, 51.2)):
        r.line(x0, 36, x1, 39.5, "#E8DCC0", 0.35)
        r.line(x1, 38, x1, 40.5, "$p.pole", 0.8)
    return r


def banner() -> Recipe:
    r = prop("banner", 28, 48, (14, 44), {"cloth": "#B8483A", "light": "#F08A70", "dark": "#6A1E1C", "emblem": "#F2C94C", "pole": "#6A4A2A"})
    r.shadow(14.5, 44, 7, 2, 0.38)
    r.rect(12.8, 3, 2.4, 41, wood(331, "#6A4A2A", 3), stroke=INK, width=0.4)
    r.shade(box(14.2, 3, 1.2, 41), 0.5, clip=True)
    r.ellipse(14, 2.6, 2, 2, radial(13.3, 2, 2.6, (0, "#FFF4B0"), (1, "#B8862A")), stroke=INK, width=0.35)
    cloth = "M 15.2 6 Q 20 7.5 26 6 L 26 28 L 20.6 24 L 15.2 28 Z"
    r.path(cloth, linear(15, 6, 26, 28, (0, "$p.light"), (0.4, "$p.cloth"), (1, "$p.dark")), stroke=INK, width=0.45)
    r.shade("M 19 6.8 Q 20.5 16 19.5 25 L 22 25 Q 23 16 22 7 Z", 0.35, blur=0.6, clip=True)  # a fold
    r.poly([(20.6, 11), (23.4, 15), (20.6, 19.5), (17.8, 15)], "$p.emblem", stroke="#6A4A0E", width=0.3)
    r.poly([(20.6, 12.8), (22, 15), (20.6, 17.4), (19.2, 15)], "#FFF4B0")
    r.rect(15.2, 6, 10.8, 1.4, "$p.emblem", alpha=0.9, clip=True)
    return r


def statue() -> Recipe:
    r = prop("statue", 32, 50, (16, 46), {"stone": "#A8ADB8", "light": "#E4E8F0", "dark": "#5A5E70", "moss": "#6E9A55"})
    r.shadow(17, 46, 13, 3.4, 0.4)
    fill = stone(341, "#A8ADB8", 5)
    r.path("M 5 46 L 6.5 39 L 25.5 39 L 27 46 Z", fill, stroke=INK, width=0.45)  # the plinth
    r.rect(8, 35, 16, 4.2, fill, stroke=INK, width=0.45)
    # a robed figure holding a sword point down
    r.path("M 10 35 Q 9 24 11.5 17 Q 16 14.5 20.5 17 Q 23 24 22 35 Z", fill, stroke=INK, width=0.45)
    r.path("M 11.5 17 Q 7 19 7.5 26 L 10.5 27 Q 10 21 12.5 19 Z", fill, stroke=INK, width=0.4)
    r.path("M 20.5 17 Q 25 19 24.5 26 L 21.5 27 Q 22 21 19.5 19 Z", fill, stroke=INK, width=0.4)
    r.ellipse(16, 11, 4.2, 4.8, fill, stroke=INK, width=0.45)
    r.path("M 11.6 10.5 Q 11 4.5 16 4.5 Q 21 4.5 20.4 10.5 Q 18.5 7.5 16 7.8 Q 13.5 7.5 11.6 10.5 Z", fill, stroke=INK, width=0.4)  # a hood
    r.rect(15.2, 19, 1.6, 17, linear(15, 0, 17, 0, (0, "#F0F4FA"), (1, "#7A8090")), stroke=INK, width=0.3)  # the blade
    r.rect(12.6, 18.4, 6.8, 1.6, fill, stroke=INK, width=0.3)
    r.shade("M 16.5 4 L 28 4 L 28 47 L 15.5 47 Q 19 28 16.5 4 Z", 0.45, blur=0.5, clip=True)
    r.lit("M 4 46 L 6.5 39 L 9 39 L 8 35 L 10 35 Q 8.5 24 11 17 Q 7 19 7.5 26 L 9 26.5 Q 9 20 12 17.5 L 11.6 10.5 Q 11 4.5 16 4.5 L 16 5.5 Q 12.5 6 12.8 10.5 L 13 17 Q 10.5 24 11.5 35 L 9.5 39 L 7 46 Z", 0.5, "#FFF6E0")
    r.path("M 13 31 Q 14 26 13.2 21 M 19 32 Q 18.4 27 19.4 22", None, stroke=INK, width=0.3, alpha=0.5)
    r.ellipse(8.5, 45, 4, 1.6, "$p.moss", alpha=0.85, blur=0.5, clip=True)
    r.ellipse(22, 39.5, 3, 1, "$p.moss", alpha=0.7, blur=0.4, clip=True)
    return r


def well() -> Recipe:
    r = prop("well", 40, 46, (20, 40), {"stone": "#8F8F9C", "water": "#3C78B4", "wood": "#7A5230", "roof": "#B04A3A"})
    r.shadow(21, 40, 18, 4.5, 0.4)
    for x in (8, 32):  # posts
        r.rect(x - 1.3, 10, 2.6, 22, wood(351, "#7A5230", 3), stroke=INK, width=0.4)
    r.rect(8, 15, 24, 1.8, wood(352, "#6A4426", 3), stroke=INK, width=0.35)  # the windlass
    r.line(20, 16.8, 20, 27, "#D8C8A0", 0.5)
    r.path("M 17.5 27 L 22.5 27 L 22 31 L 18 31 Z", wood(353, "#9A6A38", 2), stroke=INK, width=0.35)  # the bucket
    r.ellipse(20, 30, 13.4, 5, stone(354, "#7A7A88", 4), stroke=INK, width=0.5)  # the rim
    r.ellipse(20, 30, 10, 3.5, linear(10, 27, 30, 33, (0, "#12284E"), (1, "$p.water")), stroke=INK, width=0.4)
    r.path("M 14 30 Q 18 28.6 23 29.6", None, stroke="#BFE0FF", width=0.5, alpha=0.8)
    r.path("M 6.6 30 Q 6.6 39 20 40.5 Q 33.4 39 33.4 30 Q 33.4 35 20 35 Q 6.6 35 6.6 30 Z", stone(355, "#8F8F9C", 4), stroke=INK, width=0.5)  # the wall
    for k in range(7):
        x = 8.5 + k * 3.9
        r.line(x, 34 + (0.6 if k in (0, 6) else 1.0), x + (0.3 if k % 2 else -0.3), 39.4 - abs(k - 3) * 0.35, INK, 0.3, alpha=0.6)
    r.path("M 7 36.4 Q 20 38.6 33 36.4", None, stroke=INK, width=0.3, alpha=0.6)
    r.shade("M 21 33 L 34 30 L 34 41 L 20 41 Z", 0.5, blur=0.8, clip=True)
    r.path("M 2 12 L 20 1.5 L 38 12 L 36 13.5 L 20 5 L 4 13.5 Z", "#5A1E20", stroke=INK, width=0.4)
    r.path("M 3 12 L 20 2 L 37 12 Z", noise(4, 356, (0.3, "#8A3028"), (0.5, "$p.roof"), (0.75, "#D8705A"), octaves=2), stroke=INK, width=0.5)  # the roof
    for k in range(1, 5):  # rows of tiles
        y = 2 + k * 2
        half = (y - 2) * 1.7
        r.path(f"M {20 - half:.1f} {y} L {20 + half:.1f} {y}", None, stroke="#5A1E20", width=0.3, alpha=0.6)
    r.shade("M 20 2 L 37 12 L 20 12 Z", 0.4, clip=True)
    return r


def stall() -> Recipe:
    r = prop("stall", 48, 44, (24, 39), {"wood": "#9A6A38", "cloth": "#C9302C", "cloth2": "#F8F2E4"})
    r.shadow(25, 39, 23, 5, 0.4)
    for x in (5, 43):
        r.rect(x - 1.3, 12, 2.6, 27, wood(361, "#7A5230", 3), stroke=INK, width=0.4)
    r.rect(4, 24, 40, 14.5, wood(362, "#9A6A38", 5), stroke=INK, width=0.5)  # the counter
    for x in (14, 24, 34):
        r.line(x, 27.5, x, 38, "#3E2410", 0.35, alpha=0.7)
    r.rect(3, 22, 42, 3.4, wood(363, "#C89A60", 4), stroke=INK, width=0.45)
    r.shade(box(4, 25.4, 40, 3), 0.45, blur=0.6, clip=True)
    goods = [(9, "#E04A3A"), (13.5, "#F0A030"), (18, "#E04A3A"), (26, "#7AB848"), (30.5, "#F0D048"), (35, "#7AB848"), (39.5, "#B060D0")]
    for x, c in goods:  # fruit and jars on the counter
        r.ellipse(x, 20.6, 2.1, 1.9, radial(x - 0.7, 19.9, 2.8, (0, lighten(c, 0.5)), (0.5, c), (1, darken(c, 0.45))), stroke=INK, width=0.3)
        r.ellipse(x - 0.7, 19.9, 0.5, 0.4, "#FFFFFF", alpha=0.8)
    awning = "M 1 13 L 6 3 L 42 3 L 47 13 Z"
    r.path(awning, "$p.cloth2", stroke=INK, width=0.5)
    for k in range(4):  # stripes
        x0, x1 = 6 + k * 9, 6 + k * 9 + 4.5
        b0, b1 = 1 + k * 11.5, 1 + k * 11.5 + 5.75
        r.path(f"M {x0} 3 L {x1} 3 L {b1} 13 L {b0} 13 Z", "$p.cloth", clip=True)
    for k in range(8):  # the scalloped edge
        x = 1 + k * 5.75
        c = "$p.cloth" if k % 2 == 0 else "$p.cloth2"
        r.path(f"M {x} 13 L {x + 5.75} 13 Q {x + 5.75} 16.4 {x + 2.87} 16.4 Q {x} 16.4 {x} 13 Z", c, stroke=INK, width=0.35)
    r.shade("M 24 3 L 42 3 L 47 13 L 47 17 L 24 17 Z", 0.3, clip=True)
    r.lit("M 1 13 L 6 3 L 16 3 L 11 13 Z", 0.25, "#FFF4D0")
    r.rect(5, 16.4, 38, 3, "#2A1E4A", alpha=0.35, blur=0.8)
    return r


def haybale() -> Recipe:
    r = prop("haybale", 34, 28, (17, 24), {"hay": "#E0C060", "dark": "#9A7A2A", "light": "#FFF0A8"})
    r.shadow(18, 24, 16, 3.6, 0.4)
    body = "M 3 9 Q 3 5 7 5 L 27 5 Q 31 5 31 9 L 31 21 Q 31 25 27 25 L 7 25 Q 3 25 3 21 Z"
    r.path(body, noise(3, 371, (0.3, "$p.dark"), (0.5, "$p.hay"), (0.75, "$p.light"), octaves=3), stroke="#3E2C0E", width=0.5)
    for _ in range(46):  # straws
        x, y = r.rng.uniform(4, 30), r.rng.uniform(6, 24)
        length = r.rng.uniform(2, 5)
        r.line(x, y, x + length, y + r.rng.uniform(-0.5, 0.5), r.rng.choice(["#FFF4B8", "#A8862A", "#F0D878"]), 0.3, alpha=0.8)
    r.shade("M 19 5 L 31 5 L 31 25 L 17 25 Z", 0.4, blur=1.0, clip=True)
    r.shade(box(3, 20, 28, 5), 0.3, blur=0.8, clip=True)
    for x in (11, 23):  # the twine
        r.rect(x - 0.6, 5, 1.2, 20, "#7A5A2A", stroke="#3E2C0E", width=0.25)
    r.lit(box(3, 5, 28, 1.6), 0.4, "#FFFBE0")
    return r


def anvil() -> Recipe:
    r = prop("anvil", 36, 32, (18, 28), {"iron": "#5C6470", "light": "#C8D0DC", "dark": "#22262E", "wood": "#8A5A2E"})
    r.shadow(19, 28, 15, 3.6, 0.4)
    r.glow(18, 12, 12, "#FF9A40", 0.22)
    r.path("M 8 28 L 9 19 L 27 19 L 28 28 Z", wood(381, "#8A5A2E", 3), stroke=INK, width=0.45)  # the block
    r.ellipse(18, 19, 9, 2.2, wood(382, "#B88450", 2), stroke=INK, width=0.4)
    for rr in (6, 3.5):
        r.ellipse(18, 19, rr, rr * 0.24, None, stroke="#5A3A1A", width=0.25, alpha=0.7)
    r.shade("M 19 19 L 28 19 L 29 29 L 18 29 Z", 0.45, blur=0.6, clip=True)
    iron = linear(0, 6, 0, 19, (0, "$p.light"), (0.25, "$p.iron"), (1, "$p.dark"))
    r.path("M 2 8 Q 8 8 11 7 L 31 7 L 31 11 L 25 11 Q 22 13 22 16 L 25 18.5 L 11 18.5 L 14 16 Q 14 13 11 11.5 Q 6 11.5 2 8 Z", iron, stroke=INK, width=0.5)
    r.rect(11, 7, 20, 1.0, "#FFFFFF", alpha=0.6, clip=True)
    r.path("M 3 8.2 Q 8 8.6 11 8", None, stroke="#FFFFFF", width=0.4, alpha=0.6)
    r.ellipse(27.5, 8.2, 1.0, 0.5, "$p.dark")
    r.rect(14, 5.6, 7, 1.5, linear(14, 0, 21, 0, (0, "#FFE080"), (0.6, "#FF7A20"), (1, "#B03010")), stroke=INK, width=0.25)  # a glowing bar
    return r


def threshold_stone() -> Recipe:
    r = prop("threshold_stone", 40, 56, (20, 50), {"light": "#B8C2D4", "body": "#6C7585", "dark": "#343C4E", "rune": "#6FE3FF"})
    r.shadow(21, 50, 15, 4, 0.4)
    r.glow(20, 26, 26, "#5FD8FF", 0.3)
    for x, s in ((7, 1.0), (33, 0.8)):  # small stones at its sides
        r.path(f"M {x - 3 * s:.1f} 50 L {x - 2.4 * s:.1f} {50 - 5 * s:.1f} L {x:.1f} {50 - 7 * s:.1f} L {x + 2.6 * s:.1f} {50 - 4.6 * s:.1f} L {x + 3 * s:.1f} 50 Z", stone(391, "#6C7585", 3), stroke=INK, width=0.4)
        r.shade(f"M {x:.1f} {50 - 7 * s:.1f} L {x + 2.6 * s:.1f} {50 - 4.6 * s:.1f} L {x + 3 * s:.1f} 50 L {x:.1f} 50 Z", 0.45, clip=True)
    body = "M 10 50 L 11 20 Q 12 6 20 3 Q 28 6 29 20 L 30 50 Z"
    r.path(body, stone(392, "#6C7585", 6), stroke=INK, width=0.55)
    r.shade("M 20 3 Q 28 6 29 20 L 30 50 L 21 50 Q 24 26 20 3 Z", 0.5, clip=True)
    r.lit("M 10 50 L 11 20 Q 12 6 20 3 L 20 5.5 Q 14 8 13.4 20 L 12.6 50 Z", 0.5, "#E8F8FF")
    rune = "M 20 12 L 25 20 L 20 28 L 15 20 Z M 20 28 L 20 40 M 16 34 L 24 34 M 17 42.5 L 20 40 L 23 42.5"
    r.path(rune, None, stroke="$p.rune", width=2.6, alpha=0.5, blend="add", blur=1.2)
    r.path(rune, None, stroke="#0E3A50", width=1.3)
    r.path(rune, None, stroke="$p.rune", width=0.8)
    r.path(rune, None, stroke="#FFFFFF", width=0.3, alpha=0.9)
    r.ellipse(20, 20, 1.3, 1.3, "#FFFFFF")
    r.glow(20, 20, 5, "#9FF0FF", 0.7)
    r.path("M 13 44 L 16 46 L 15 49 M 26 9 L 27.5 13", None, stroke=INK, width=0.3, alpha=0.6)
    for x, y in ((6, 12), (34, 18), (31, 6), (8, 30)):  # motes of light
        r.ellipse(x, y, 0.5, 0.5, "#E0FCFF")
        r.glow(x, y, 2.2, "#6FE3FF", 0.6)
    r.ellipse(14, 49.5, 4, 1.4, "#5E9A50", alpha=0.8, blur=0.5, clip=True)
    return r


# ------------------------------------------------------------------------------------------------ scenery of the wild
def stump() -> Recipe:
    r = prop("stump", 30, 24, (15, 20), {"wood": "#7A5236", "top": "#D8B080"})
    r.shadow(16, 20, 13, 3.2, 0.36)
    r.path("M 5 9 Q 4.4 16 2.6 20 L 8 19 L 11 21 L 15 19.4 L 20 21 L 23 19 L 27.6 20 Q 25.6 16 25 9 Z", wood(401, "#7A5236", 3), stroke=INK, width=0.45)
    r.shade("M 16 9 L 25 9 Q 25.6 16 27.6 20 L 23 19 L 20 21 L 15.6 19.6 Z", 0.5, blur=0.6, clip=True)
    for x in (8, 11.6, 19, 22):
        r.line(x, 11, x + (0.4 if x > 15 else -0.4), 18.6, "#3E2410", 0.3, alpha=0.6)
    r.ellipse(15, 8.6, 10, 3.6, noise(3, 402, (0.3, "#B88C5A"), (0.7, "$p.top"), octaves=2), stroke=INK, width=0.45)
    for k in (7.4, 5, 2.6):
        r.ellipse(15, 8.6, k, k * 0.36, None, stroke="#8A5A30", width=0.25, alpha=0.7)
    r.path("M 15 8.6 L 22 6.6 M 15 8.6 L 9 10.6", None, stroke="#6A4020", width=0.25, alpha=0.7)
    r.ellipse(7, 19.6, 4, 1.4, "#5E9A50", alpha=0.85, blur=0.5)
    r.ellipse(20.6, 6.4, 1.6, 1.0, "#C8483A", stroke=INK, width=0.25)  # a small mushroom on the rim
    r.ellipse(20.2, 6.1, 0.4, 0.3, "#FFFFFF")
    return r


def flowers() -> Recipe:
    r = prop("flowers", 30, 22, (15, 19), {"petal": "#F06A9A", "petal2": "#FFD860", "petal3": "#8A7AF0", "leaf": "#3E8E45"})
    r.shadow(15.5, 19, 12, 2.4, 0.26)
    for _ in range(16):  # leaves and stems
        x, top = r.rng.uniform(4, 26), r.rng.uniform(6, 13)
        lean = r.rng.uniform(-2, 2)
        r.path(f"M {x - 0.6:.2f} 19 Q {x + lean * 0.3:.2f} {(top + 19) / 2:.2f} {x + lean:.2f} {top:.2f} Q {x + lean * 0.5 + 0.5:.2f} {(top + 19) / 2:.2f} {x + 0.6:.2f} 19 Z",
               mix("#2E7A40", "#8CD06A", r.rng.random()), stroke="#143A2A", width=0.2)
    for i, (x, y) in enumerate(((6, 9), (11, 5.6), (16, 8.6), (21, 4.8), (25, 9.6), (13.6, 12), (19.6, 12.6), (8.6, 13.6))):
        color = ("$p.petal", "$p.petal2", "$p.petal3")[i % 3]
        size = r.rng.uniform(1.5, 2.1)
        for k in range(5):
            a = k * 2 * math.pi / 5 - 0.6
            r.ellipse(x + math.cos(a) * size * 0.75, y + math.sin(a) * size * 0.7, size * 0.6, size * 0.5, color, stroke=INK, width=0.2)
        r.ellipse(x - size * 0.2, y - size * 0.3, size * 0.7, size * 0.5, "#FFFFFF", alpha=0.3)
        r.ellipse(x, y, size * 0.4, size * 0.36, "#FFF2A8", stroke="#A8741E", width=0.2)
    return r


def fern() -> Recipe:
    r = prop("fern", 34, 26, (17, 22), {"leaf": "#3E8E45", "light": "#9AD86A", "dark": "#1F5A3A"})
    r.shadow(17.5, 22, 13, 3, 0.3)
    for a in (-1.25, -0.85, -0.45, -0.1, 0.25, 0.6, 0.95, 1.3):  # fronds, like a fan
        length = r.rng.uniform(13, 17)
        ex, ey = 17 + math.sin(a) * length, 21 - math.cos(a) * length * 0.95
        mx, my = 17 + math.sin(a) * length * 0.55 + math.cos(a) * 1.4, 21 - math.cos(a) * length * 0.6
        color = mix("#1F5A3A", "#6FBE64", r.rng.random())
        nx, ny = math.cos(a) * 2.2, math.sin(a) * 2.2
        r.path(f"M 17 21 Q {mx - nx:.2f} {my - ny:.2f} {ex:.2f} {ey:.2f} Q {mx + nx:.2f} {my + ny:.2f} 17 21 Z", color, stroke="#143A2A", width=0.3)
        r.path(f"M 17 21 Q {mx:.2f} {my:.2f} {ex:.2f} {ey:.2f}", None, stroke="$p.light", width=0.3, alpha=0.7)
        for t in (0.35, 0.55, 0.75):  # the notches of the leaflets
            px, py = 17 + (mx - 17) * t * 1.4, 21 + (my - 21) * t * 1.4
            r.line(px - nx * 0.7, py - ny * 0.7, px + nx * 0.7, py + ny * 0.7, "#143A2A", 0.2, alpha=0.6)
    return r


def log() -> Recipe:
    r = prop("log", 46, 22, (23, 18), {"wood": "#6A4630", "top": "#D0A878", "moss": "#5E9A50"})
    r.shadow(24, 18, 21, 3.4, 0.36)
    r.path("M 6 8 L 38 6 Q 42 6 42 11 Q 42 16.6 38 17 L 6 18 Z", wood(411, "#6A4630", 4), stroke=INK, width=0.45)
    for y in (9.6, 12, 14.6):
        r.path(f"M 8 {y} Q 22 {y - 1.2} 38 {y - 1}", None, stroke="#2E1A0E", width=0.3, alpha=0.6)
    r.shade("M 6 13 L 42 11.6 Q 42 16.6 38 17 L 6 18 Z", 0.5, blur=0.8, clip=True)
    r.lit("M 6 8 L 38 6 Q 41 6 41.6 8 L 6 9.6 Z", 0.3, "#FFE8B8", blur=0.3)
    r.ellipse(6, 13, 3.4, 5, noise(2, 412, (0.3, "#B88C5A"), (0.7, "$p.top"), octaves=2), stroke=INK, width=0.45)  # the cut end
    for k in (3.4, 1.8):
        r.ellipse(6, 13, k * 0.62, k, None, stroke="#8A5A30", width=0.25, alpha=0.7)
    r.path("M 26 6.8 L 28 2.6 L 30 6.6", None, stroke=INK, width=1.9)  # the stub of a branch
    r.path("M 26 6.8 L 28 2.6 L 30 6.6", None, stroke="#6A4630", width=1.1)
    for x, w in ((14, 6), (33, 5), (22, 3.4)):
        r.ellipse(x, 7.6, w, 1.7, "$p.moss", alpha=0.9, blur=0.5, clip=True)
        r.ellipse(x - 1, 7.1, w * 0.5, 0.8, "#9AD86A", alpha=0.6, clip=True)
    return r


def driftwood() -> Recipe:
    r = prop("driftwood", 40, 20, (20, 16), {"wood": "#B8A890", "dark": "#6A5E50"})
    r.shadow(21, 16, 18, 2.8, 0.3)
    for d, w in (("M 4 14 Q 14 8 26 10 Q 32 11 37 7", 3.4), ("M 20 10 Q 23 5 28 3", 2.0), ("M 12 11.6 Q 10 7 6 6", 1.6)):
        r.path(d, None, stroke=INK, width=w + 0.9)
        r.path(d, None, stroke="$p.wood", width=w)
        r.path(d, None, stroke="#F2E8D6", width=w * 0.3, alpha=0.7)
    r.path("M 8 13.6 Q 16 10.6 25 11.6", None, stroke="$p.dark", width=0.3, alpha=0.7)
    r.ellipse(30, 15.4, 1.6, 1.1, radial(29.6, 15, 2, (0, "#FFFFFF"), (1, "#E8C8B8")), stroke="#A88070", width=0.2)  # a shell
    r.ellipse(11, 15.6, 3, 0.8, "#3E7A6A", alpha=0.6, blur=0.4)  # seaweed
    return r


def ice_shard() -> Recipe:
    r = prop("ice_shard", 30, 42, (15, 38), {"ice": "#BFE8FF", "deep": "#5A9ADC", "glow": "#A0E0FF"})
    r.shadow(16, 38, 12, 3, 0.34)
    r.glow(15, 22, 16, "$p.glow", 0.3)
    for x, base, h, w, lean in ((8, 37, 16, 3.2, -2.4), (22, 37.4, 20, 3.6, 2.6), (15, 38, 33, 5, 0.6), (11.6, 38, 11, 2.4, -1), (19, 38, 9, 2.2, 1.2)):
        tip = (x + lean, base - h)
        r.poly([(x - w, base), tip, (x + w, base)], linear(x - w, base - h, x + w, base, (0, "#FFFFFF"), (0.45, "$p.ice"), (1, "$p.deep")), stroke="#2A5A9A", width=0.4)
        r.poly([(x - w, base), tip, (x - w * 0.15, base)], "#FFFFFF", alpha=0.5)
        r.line(x + w * 0.2, base - 1, tip[0], tip[1] + 2, "#2A5A9A", 0.25, alpha=0.5)
    for x, y in ((6, 14), (24, 9), (20, 26)):
        r.poly([(x, y - 1.6), (x + 0.4, y - 0.4), (x + 1.6, y), (x + 0.4, y + 0.4), (x, y + 1.6), (x - 0.4, y + 0.4), (x - 1.6, y), (x - 0.4, y - 0.4)], "#FFFFFF", alpha=0.9)
    r.ellipse(15, 37.6, 11, 1.8, "#FFFFFF", alpha=0.8, blur=0.6)  # snow at its foot
    return r


def dry_shrub() -> Recipe:
    r = prop("dry_shrub", 32, 26, (16, 22), {"twig": "#8A6A3E", "light": "#D8C088", "dark": "#4A3418"})
    r.shadow(16.5, 22, 12, 2.6, 0.3)
    for _ in range(22):  # a tangle of dry twigs
        a = r.rng.uniform(-1.35, 1.35)
        length = r.rng.uniform(8, 16)
        ex, ey = 16 + math.sin(a) * length, 21.6 - math.cos(a) * length * 0.9
        bend = r.rng.uniform(-3, 3)
        d = f"M 16 21.6 Q {(16 + ex) / 2 + bend:.2f} {(21.6 + ey) / 2:.2f} {ex:.2f} {ey:.2f}"
        r.path(d, None, stroke="$p.dark", width=0.9)
        r.path(d, None, stroke=mix("#8A6A3E", "#D8C088", r.rng.random()), width=0.5)
        if r.rng.random() < 0.5:
            r.line(ex, ey, ex + r.rng.uniform(-2, 2), ey - r.rng.uniform(1, 3), "$p.twig", 0.4)
    for x, y in ((9, 12), (22, 10), (16, 7), (12.6, 17)):
        r.ellipse(x, y, 1.0, 0.7, "#B8C870", alpha=0.8)  # the last leaves
    return r


def build_props() -> list[Recipe]:
    props = [tree_oak(), pine(), dead_tree(), bush(), rock(), cactus(), campfire(), crate(), barrel(), bones(), lamp(), signpost(),
             statue(), tent(), banner(), well(), threshold_stone(), stall(), haybale(), anvil(), reeds(), mushrooms(),
             stump(), flowers(), fern(), log(), driftwood(), ice_shard(), dry_shrub()]
    sway = {"tree_oak": 1.8, "pine": 1.1, "dead_tree": 0.5, "bush": 0.7, "reeds": 1.4, "banner": 0.5, "campfire": 0.6, "flowers": 0.9, "fern": 0.8, "dry_shrub": 0.6}  # what the wind moves
    for r in props:
        r.sway = sway.get(r.id.rsplit("/", 1)[1], 0.0)
    return props
