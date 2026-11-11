"""The recipes of the props (trees, rocks, bushes, camps, signs...), built with tools/artkit.py. Canvas sizes and origins (the feet) are the same as
before, so that the collision radii in the world data still fit."""
from __future__ import annotations

import math

from artkit import Recipe, darken, lighten, linear, mix, radial  # noqa: E402

OUTLINE = "#1E1B28"


def prop(name: str, w, h, origin, palette: dict) -> Recipe:
    return Recipe(f"base:art/prop/{name}", w, h, origin, palette, seed="v2")


def lobe(r: Recipe, cx, cy, rx, ry, base: str, outline: str, width=1.3, light=0.35, dark=0.3):
    """A rounded mass with a radial light from the top left and an outline."""
    r.ellipse(cx, cy, rx, ry, radial(cx - rx * 0.35, cy - ry * 0.4, max(rx, ry) * 1.35, (0, lighten(base, light)), (0.55, base), (1, darken(base, dark))), stroke=outline, width=width)


def tree_oak() -> Recipe:
    r = prop("tree_oak", 64, 96, (32, 88), {"trunk": "#8B5E3C", "trunk_dark": "#5E3F27", "leaf": "#3E8E45", "leaf_light": "#6CBF63", "leaf_dark": "#2B6A34"})
    r.shadow(33, 88, 20, 5.5, 0.30)
    # roots and trunk
    r.poly([(24, 89), (28, 82), (36, 82), (41, 89), (36, 86.5), (28, 86.5)], "$p.trunk_dark")
    r.path("M 27 86 Q 29 62 28 52 L 38 52 Q 37 62 38 86 Z", linear(26, 0, 40, 0, (0, "$p.trunk"), (0.6, "$p.trunk"), (1, "$p.trunk_dark")), stroke="#2E1E12", width=1.3)
    for y in (58, 66, 74, 81):  # bark
        r.path(f"M 30 {y} Q 32.5 {y + 2} 35 {y - 1}", None, stroke="$p.trunk_dark", width=0.9, alpha=0.8)
    r.ellipse(32.5, 70, 1.5, 2.2, "#3E2A18", alpha=0.8)  # a knot
    r.path("M 29 52 Q 22 48 17 44", None, stroke="$p.trunk_dark", width=3.2)  # branches into the crown
    r.path("M 37 52 Q 44 48 49 43", None, stroke="$p.trunk_dark", width=3.2)
    outline = darken("#2B6A34", 0.5)
    # the crown: dark lobes at the back, the base color in the middle, light lobes in front
    for cx, cy, rx, ry in ((18, 40, 13, 11), (47, 38, 14, 11), (32, 24, 18, 14), (14, 28, 11, 9), (50, 26, 11, 9)):
        lobe(r, cx, cy, rx, ry, "$p.leaf_dark" if False else "#2B6A34", outline, 1.3, 0.25, 0.35)
    for cx, cy, rx, ry in ((24, 36, 14, 10), (42, 36, 14, 10), (32, 30, 17, 12), (20, 22, 11, 8), (44, 21, 11, 8), (32, 14, 12, 9)):
        lobe(r, cx, cy, rx, ry, "#3E8E45", outline, 1.2, 0.35, 0.3)
    for cx, cy, rx, ry in ((24, 24, 8, 6), (38, 18, 7, 5), (45, 30, 6, 4.5), (17, 33, 6, 4.5)):
        r.ellipse(cx, cy, rx, ry, "$p.leaf_light", alpha=0.9)
        r.ellipse(cx - rx * 0.3, cy - ry * 0.35, rx * 0.5, ry * 0.4, lighten("#6CBF63", 0.45), alpha=0.7)
    for x, y in r.scatter(26, 6):  # leaf clumps: small dark and light dabs inside the crown
        if ((x - 32) / 21) ** 2 + ((y - 28) / 17) ** 2 < 1:
            c = r.rng.choice(["#2B6A34", "#2B6A34", "#6CBF63", "#4FA654"])
            r.ellipse(x, y, r.rng.uniform(1.0, 2.0), r.rng.uniform(0.8, 1.4), c, alpha=0.8)
    r.variants = {"autumn": {"leaf": "#D2813A", "leaf_light": "#EDB05B", "leaf_dark": "#9C5524"}}
    return r


def pine() -> Recipe:
    r = prop("pine", 64, 96, (32, 88), {"trunk": "#6B4A32", "dark": "#2F6B4C", "mid": "#3A8059", "light": "#4A9A6A", "outline": "#1D4533", "snow": "#F2F6FA"})
    r.shadow(33, 88, 17, 5, 0.30)
    r.rect(29, 74, 6, 15, linear(29, 0, 35, 0, (0, "#8A6444"), (1, "$p.trunk")), stroke="#2E1E12", width=1.1)
    r.line(31, 76, 31, 87, "#4A3220", 0.8, 0.8)
    tiers = [(80, 23, 24), (62, 19, 20), (46, 15, 17), (32, 11, 14), (20, 7.5, 10)]  # (bottom y, half width, height)
    for by, hw, h in tiers:
        top = by - h
        r.poly([(32 - hw, by), (32, top), (32 + hw, by), (32 + hw * 0.55, by - 2.4), (32 + hw * 0.2, by), (32, by - 2), (32 - hw * 0.25, by), (32 - hw * 0.6, by - 2.4)], "$p.dark", stroke="$p.outline", width=1.3)
        r.poly([(32 - hw, by), (32, top), (32 + 0.5, by - 1)], "$p.mid")
        r.poly([(32 - hw * 0.62, by - 3), (32 - 1, top + 3.5), (32 - hw * 0.15, by - 4)], "$p.light", alpha=0.8)
        for k in range(3):  # needle lines
            x0 = 32 - hw * (0.7 - k * 0.3)
            r.line(x0, by - 1.2, x0 + hw * 0.18, by - h * 0.32, darken("#2F6B4C", 0.3), 0.8, 0.8)
        r.poly([(32 - hw * 0.34, top + h * 0.42), (32, top - 0.2), (32 + hw * 0.34, top + h * 0.42), (32 + hw * 0.18, top + h * 0.34), (32, top + h * 0.5), (32 - hw * 0.2, top + h * 0.34)], "$p.snow", alpha=0.95)
    return r


def dead_tree() -> Recipe:
    r = prop("dead_tree", 64, 96, (32, 88), {"trunk": "#5A4A44", "dark": "#2E2420", "light": "#7A6A62"})
    r.shadow(33, 88, 18, 5, 0.30)
    r.poly([(22, 90), (27, 80), (37, 80), (43, 90), (36, 86), (28, 86)], "$p.dark")
    r.path("M 26 86 Q 29 64 30 40 L 35 40 Q 36 64 38 86 Z", linear(26, 0, 40, 0, (0, "$p.light"), (0.4, "$p.trunk"), (1, "$p.dark")), stroke="#1A1412", width=1.3)
    for y in (48, 58, 68, 78):
        r.path(f"M 30 {y} Q 32 {y + 2.5} 35 {y - 0.5}", None, stroke="$p.dark", width=0.9, alpha=0.9)
    r.ellipse(32.6, 64, 1.5, 2.4, "#14100E")
    branches = [("M 31 46 Q 24 40 17 28 Q 14 22 12 18", 3.0), ("M 34 42 Q 42 36 49 26 Q 52 21 53 15", 3.0), ("M 32 38 Q 31 28 28 18", 2.4),
                ("M 24 38 Q 18 36 12 38", 1.8), ("M 40 36 Q 46 34 52 36", 1.8), ("M 17 28 Q 20 22 22 20", 1.6), ("M 49 26 Q 46 20 44 17", 1.6)]
    for d, w in branches:
        r.path(d, None, stroke="#1A1412", width=w + 1.6)
        r.path(d, None, stroke="$p.trunk", width=w)
        r.path(d, None, stroke="$p.light", width=max(0.6, w * 0.3), alpha=0.7)
    r.ellipse(29, 18, 1.3, 1.3, "#14100E")
    return r


def bush() -> Recipe:
    r = prop("bush", 32, 24, (16, 20), {"leaf": "#4E9A44", "light": "#8AD068", "dark": "#2E6228", "outline": "#143312", "berry": "#D8402A"})
    r.shadow(17, 21, 13, 3.4, 0.30)
    for cx, cy, rx, ry in ((9, 14, 8, 6.5), (23, 14, 8, 6.5), (16, 10, 10, 8)):
        lobe(r, cx, cy, rx, ry, "#4E9A44", "$p.outline", 1.2, 0.3, 0.38)
    for cx, cy, rx, ry in ((11, 9, 4.2, 3), (19, 7.5, 3.6, 2.6)):
        r.ellipse(cx, cy, rx, ry, "$p.light", alpha=0.8)
    for x, y in ((8, 14), (14, 15), (20, 11), (24, 15), (16, 8), (11, 11)):
        r.ellipse(x + 0.4, y + 0.6, 1.6, 1.4, "#000000", alpha=0.25)
        r.ellipse(x, y, 1.6, 1.6, "$p.berry", stroke="#7A1E10", width=0.5)
        r.ellipse(x - 0.5, y - 0.5, 0.5, 0.5, "#FFFFFF", alpha=0.9)
    return r


def rock() -> Recipe:
    r = prop("rock", 32, 28, (16, 24), {"base": "#8D949F", "light": "#BCC2CB", "dark": "#5A606A"})
    r.shadow(17, 25, 13.5, 3.2, 0.30)
    r.path("M 3 22 Q 2 12 9 8 Q 15 4 22 7 Q 29 11 29 20 Q 28 25 16 25 Q 5 25 3 22 Z", linear(6, 6, 26, 26, (0, "$p.light"), (0.5, "$p.base"), (1, "$p.dark")), stroke="#3E434C", width=1.4)
    r.poly([(9, 8), (16, 5.5), (15, 14), (8, 17)], "$p.light", alpha=0.6)  # facets
    r.poly([(16, 5.5), (22, 7), (23, 15), (15, 14)], "$p.base", alpha=0.5)
    r.poly([(15, 14), (23, 15), (28, 20), (24, 24), (14, 24)], "$p.dark", alpha=0.45)
    r.path("M 9 19 L 13 16 L 15 20", None, stroke="#3E434C", width=0.8, alpha=0.8)
    r.path("M 19 18 L 22 15", None, stroke="#3E434C", width=0.7, alpha=0.7)
    r.ellipse(10, 11, 2.6, 1.3, "#FFFFFF", alpha=0.45)
    r.ellipse(24, 22, 3.5, 1.2, "#5A8A4A", alpha=0.8)  # moss at the foot
    return r


def cactus() -> Recipe:
    r = prop("cactus", 32, 48, (16, 44), {"body": "#5FA865", "rib": "#3F8A4A", "outline": "#26502E"})
    r.shadow(17, 45, 11, 3, 0.30)

    def arm(d: str, w: float):
        r.path(d, None, stroke="$p.outline", width=w + 2)
        r.path(d, None, stroke="$p.body", width=w)
        r.path(d, None, stroke=lighten("#5FA865", 0.3), width=w * 0.25, alpha=0.8)

    arm("M 12 34 L 7 34 Q 5 34 5 31 L 5 21", 5.0)
    arm("M 20 28 L 25 28 Q 27 28 27 25 L 27 15", 5.0)
    r.path("M 11 44 Q 9 44 9 40 L 9 10 Q 9 3 16 3 Q 23 3 23 10 L 23 40 Q 23 44 21 44 Z", linear(9, 0, 23, 0, (0, lighten("#5FA865", 0.28)), (0.45, "$p.body"), (1, "$p.rib")), stroke="$p.outline", width=1.5)
    for x in (13, 16, 19):
        r.path(f"M {x} 6 Q {x + 0.4} 24 {x} 43", None, stroke="$p.rib", width=0.8, alpha=0.7)
    for x, y in ((12, 12), (20, 17), (12, 26), (20, 33), (12, 38), (6, 24), (26, 18)):  # spines
        r.line(x - 1, y, x + 1, y, "#F2EBC8", 0.6)
        r.line(x, y - 1, x, y + 1, "#F2EBC8", 0.6)
    r.ellipse(16, 3.5, 2.2, 1.5, "#E8628A")  # a flower
    r.ellipse(16, 3.5, 0.9, 0.7, "#FFE07A")
    return r


def campfire() -> Recipe:
    r = prop("campfire", 28, 26, (14, 22), {"log": "#7A5232", "dark": "#3E2814", "flame": "#F2862A", "core": "#FFE066", "outline": "#2A1608", "ash": "#5A5550"})
    r.shadow(14, 23, 11, 2.4, 0.28)
    r.ellipse(14, 20, 10, 3.2, "$p.ash", alpha=0.85)
    r.ellipse(14, 19.6, 6.5, 1.8, "#2A2622", alpha=0.9)
    for x, y in ((6, 19), (9.5, 22), (19, 22), (22, 19), (14, 23)):  # ring of stones
        r.ellipse(x, y, 2.2, 1.6, "#8D8D95", stroke="#3A3A42", width=0.6)
        r.ellipse(x - 0.5, y - 0.4, 0.9, 0.5, "#BCBCC4")
    for (x0, y0, x1, y1) in ((6, 21, 20, 15.5), (22, 21, 8, 15.5)):
        r.line(x0, y0, x1, y1, "$p.outline", 4.6)
        r.line(x0, y0, x1, y1, "$p.log", 3.2)
        r.line(x0, y0 - 0.8, x1, y1 - 0.8, "#9A6E44", 0.9, 0.8)
        r.ellipse(x1, y1, 1.4, 1.4, "$p.dark")
    r.path("M 14 2 Q 23 10 21 16 Q 19 21 14 21 Q 9 21 7 16 Q 5 10 14 2 Z", radial(14, 18, 13, (0, "$p.core"), (0.5, "$p.flame"), (1, "#D8441E")), stroke="$p.outline", width=0.8)
    r.path("M 14 8 Q 19 13 18 17 Q 16.5 20 14 20 Q 11.5 20 10 17 Q 9 13 14 8 Z", "$p.core", alpha=0.95)
    r.path("M 14 13 Q 16.5 16 15.5 18.5 Q 14 19.5 12.5 18.5 Q 11.5 16 14 13 Z", "#FFFBE0")
    r.path("M 6 8 Q 9 10 8 14 Q 6 12 6 8 Z", "$p.flame", alpha=0.85)
    r.path("M 22 7 Q 20 10 21 13 Q 23 10 22 7 Z", "$p.flame", alpha=0.85)
    for x, y in ((10, 5), (18, 3.5), (22, 9), (7, 11)):  # sparks
        r.ellipse(x, y, 0.55, 0.55, "#FFD070")
    return r


def crate() -> Recipe:
    r = prop("crate", 28, 26, (14, 23), {"wood": "#B07C44", "light": "#D8A468", "dark": "#6E4824", "outline": "#2E1C0A"})
    r.shadow(15, 24, 12, 2.6, 0.28)
    r.rect(3, 6, 22, 17, linear(0, 6, 0, 23, (0, "$p.light"), (0.4, "$p.wood"), (1, "$p.dark")), stroke="$p.outline", width=1.4)
    r.rect(3, 6, 22, 3, "$p.light", alpha=0.7)
    for x in (9, 14, 19):
        r.line(x, 9, x, 23, "$p.dark", 0.7, 0.8)
    for y in (12.5, 18):
        r.line(3.5, y, 24.5, y, darken("#B07C44", 0.35), 0.6, 0.7)
    r.rect(3, 6, 22, 2.4, "$p.dark", alpha=0.5)
    r.rect(3, 20.6, 22, 2.4, "$p.dark", alpha=0.4)
    for (x0, y0, x1, y1) in ((4, 8, 24, 22), (24, 8, 4, 22)):  # braces
        r.line(x0, y0, x1, y1, "$p.outline", 3.4)
        r.line(x0, y0, x1, y1, "$p.wood", 2.2)
        r.line(x0, y0 - 0.5, x1, y1 - 0.5, "$p.light", 0.7, 0.8)
    for x, y in ((5, 8), (23, 8), (5, 21.5), (23, 21.5)):
        r.ellipse(x, y, 0.8, 0.8, "#2E2E36")
        r.ellipse(x - 0.2, y - 0.2, 0.3, 0.3, "#C0C0C8")
    return r


def barrel() -> Recipe:
    r = prop("barrel", 24, 28, (12, 24), {"wood": "#9A6A38", "top": "#B88650", "band": "#4A4A52"})
    r.shadow(13, 25, 10, 2.4, 0.28)
    r.path("M 4 8 Q 2 16 4 23 Q 12 26 20 23 Q 22 16 20 8 Z", linear(2, 0, 22, 0, (0, lighten("#9A6A38", 0.2)), (0.45, "$p.wood"), (1, darken("#9A6A38", 0.35))), stroke="#2E1C0A", width=1.4)
    for x in (7.5, 10.5, 13.5, 16.5):
        r.path(f"M {x} 8.5 Q {x - 0.6} 16 {x} 23.4", None, stroke=darken("#9A6A38", 0.4), width=0.6, alpha=0.7)
    for y in (11, 20):
        r.path(f"M 3.2 {y} Q 12 {y + 2} 20.8 {y}", None, stroke="#1E1E24", width=3.0)
        r.path(f"M 3.2 {y} Q 12 {y + 2} 20.8 {y}", None, stroke="$p.band", width=2.0)
        r.path(f"M 3.6 {y - 0.6} Q 12 {y + 1.4} 20.4 {y - 0.6}", None, stroke="#8A8A94", width=0.6, alpha=0.8)
    r.ellipse(12, 8, 8.2, 3.4, "$p.top", stroke="#2E1C0A", width=1.3)
    r.ellipse(12, 8, 6.2, 2.4, darken("#B88650", 0.12))
    r.path("M 7 8 Q 12 6 17 8", None, stroke=lighten("#B88650", 0.3), width=0.7, alpha=0.8)
    return r


def bones() -> Recipe:
    r = prop("bones", 32, 20, (16, 16), {"bone": "#EAE2CC", "dark": "#A89E84", "outline": "#3A3426", "socket": "#1E1B28"})
    r.shadow(16, 17, 13, 2.6, 0.26)
    for (x0, y0, x1, y1) in ((4, 15, 27, 10), (6, 10, 28, 16)):  # crossed bones
        r.line(x0, y0, x1, y1, "$p.outline", 4.2)
        r.line(x0, y0, x1, y1, "$p.bone", 2.8)
        r.line(x0, y0 - 0.7, x1, y1 - 0.7, "#FFFDF0", 0.8, 0.9)
        for (ex, ey) in ((x0, y0), (x1, y1)):
            r.ellipse(ex - 0.8, ey - 1.2, 2.0, 1.8, "$p.outline")
            r.ellipse(ex - 0.8, ey + 1.2, 2.0, 1.8, "$p.outline")
            r.ellipse(ex - 0.8, ey - 1.2, 1.4, 1.2, "$p.bone")
            r.ellipse(ex - 0.8, ey + 1.2, 1.4, 1.2, "$p.bone")
    r.ellipse(16, 9.5, 6.4, 5.2, "$p.bone", stroke="$p.outline", width=1.2)
    r.rect(12.5, 12.5, 7, 3.4, "$p.bone", stroke="$p.outline", width=1.0)
    for x in (14, 16, 18):
        r.line(x, 12.8, x, 15.6, "$p.dark", 0.6)
    r.ellipse(13.6, 9.2, 1.7, 2.0, "$p.socket")
    r.ellipse(18.4, 9.2, 1.7, 2.0, "$p.socket")
    r.poly([(15.2, 11.6), (16.8, 11.6), (16, 13)], "$p.dark")
    r.ellipse(13.7, 6.8, 2.2, 1.0, "#FFFFFF", alpha=0.5)
    return r


def lamp() -> Recipe:
    r = prop("lamp", 16, 40, (8, 36), {"pole": "#3A3A44", "glow": "#FFD878", "core": "#FFF4C4"})
    r.ellipse(8, 7, 8, 8, "$p.glow", alpha=0.18)
    r.ellipse(8, 7, 6, 6.5, "$p.glow", alpha=0.25)
    r.shadow(9, 35.5, 5.5, 2.0, 0.28)
    r.rect(5, 33, 6, 3, "$p.pole", stroke=OUTLINE, width=0.9)
    r.rect(7, 12, 2, 22, linear(7, 0, 9, 0, (0, "#5A5A66"), (1, "#26262E")), stroke=OUTLINE, width=0.7)
    r.rect(5.8, 10, 4.4, 2.4, "$p.pole", stroke=OUTLINE, width=0.8)
    r.path("M 4 8 L 4.8 2.6 L 11.2 2.6 L 12 8 Q 8 10 4 8 Z", "$p.glow", stroke=OUTLINE, width=0.9)
    r.ellipse(8, 6, 2.4, 2.9, "$p.core")
    r.rect(3.6, 1.6, 8.8, 1.8, "$p.pole", stroke=OUTLINE, width=0.8)
    r.line(8, 4.5, 8, 7.5, "#FFFFFF", 0.7, 0.9)
    return r


def signpost() -> Recipe:
    r = prop("signpost", 24, 32, (12, 30), {"wood": "#9A6C3E", "light": "#C9955E", "dark": "#5E3E1E", "outline": "#2A1808", "ink": "#2A1808"})
    r.shadow(13, 30.5, 8, 2, 0.28)
    r.rect(10.4, 8, 3.4, 22, linear(10, 0, 14, 0, (0, "$p.light"), (1, "$p.dark")), stroke="$p.outline", width=1.1)
    for (x, y, w, h, flip) in ((3, 6, 17, 6.4, 0), (6, 14, 16, 6.4, 1)):
        if not flip:
            r.poly([(x, y), (x + w - 3, y), (x + w, y + h / 2), (x + w - 3, y + h), (x, y + h)], linear(0, y, 0, y + h, (0, "$p.light"), (1, "$p.wood")), stroke="$p.outline", width=1.1)
        else:
            r.poly([(x + 3, y), (x + w, y), (x + w, y + h), (x + 3, y + h), (x, y + h / 2)], linear(0, y, 0, y + h, (0, "$p.light"), (1, "$p.wood")), stroke="$p.outline", width=1.1)
        r.line(x + 3, y + 2.2, x + w - 6, y + 2.2, "$p.ink", 0.9, 0.9)
        r.line(x + 3, y + 4, x + w - 8, y + 4, "$p.ink", 0.7, 0.8)
        r.ellipse(x + (3 if not flip else w - 2.2), y + h / 2, 0.5, 0.5, "#2E2E36")
    return r


def statue() -> Recipe:
    r = prop("statue", 28, 42, (14, 38), {"stone": "#A8ADB4", "light": "#D8DCE2", "dark": "#6A6F76", "outline": "#26292E", "moss": "#6E9A55"})
    r.shadow(15, 39.5, 11, 2.4, 0.28)
    r.rect(4, 31, 20, 7, linear(4, 0, 24, 0, (0, "$p.stone"), (1, "$p.dark")), stroke="$p.outline", width=1.4)
    r.rect(6, 28, 16, 4, linear(6, 0, 22, 0, (0, "$p.light"), (1, "$p.stone")), stroke="$p.outline", width=1.2)
    r.line(5, 34.5, 23, 34.5, "$p.dark", 0.6, 0.8)
    r.path("M 9 28 Q 8 18 11 13 L 17 13 Q 20 18 19 28 Z", linear(8, 0, 20, 0, (0, "$p.light"), (0.5, "$p.stone"), (1, "$p.dark")), stroke="$p.outline", width=1.3)  # robe
    r.path("M 9 27 Q 14 24 19 27", None, stroke="$p.dark", width=0.8)
    r.path("M 11 22 Q 13 24 12 28", None, stroke="$p.dark", width=0.7, alpha=0.8)
    r.path("M 9.5 15 Q 5 20 6 24", None, stroke="$p.outline", width=3.4)
    r.path("M 9.5 15 Q 5 20 6 24", None, stroke="$p.stone", width=2.0)
    r.path("M 18.5 15 Q 23 17 23 12", None, stroke="$p.outline", width=3.4)
    r.path("M 18.5 15 Q 23 17 23 12", None, stroke="$p.stone", width=2.0)
    r.ellipse(14, 9.5, 4.4, 4.8, radial(12.5, 8, 7, (0, "$p.light"), (1, "$p.stone")), stroke="$p.outline", width=1.3)
    r.line(12.4, 9.8, 13.6, 9.8, "$p.dark", 0.6)
    r.line(14.8, 9.8, 16, 9.8, "$p.dark", 0.6)
    r.ellipse(8, 33, 3.6, 1.5, "$p.moss", alpha=0.85)
    r.ellipse(19, 30, 2.4, 1.0, "$p.moss", alpha=0.8)
    r.path("M 6 36 Q 5 33 7 31", None, stroke="$p.moss", width=1.2, alpha=0.9)
    return r


def tent() -> Recipe:
    r = prop("tent", 40, 32, (20, 28), {"cloth": "#C9A66B", "light": "#E8D2A0", "dark": "#8A6A3A", "stripe": "#B8483A", "outline": "#3A2810", "pole": "#6A4A2A"})
    r.shadow(21, 29, 17, 3.4, 0.28)
    r.poly([(3, 28), (20, 5), (37, 28)], "$p.dark", stroke="$p.outline", width=1.5)
    r.poly([(3, 28), (20, 5), (21.5, 28)], linear(3, 0, 21, 0, (0, "$p.light"), (1, "$p.cloth")))
    r.poly([(21.5, 28), (20, 5), (37, 28)], linear(20, 0, 37, 0, (0, "$p.cloth"), (1, "$p.dark")))
    r.poly([(20, 5), (24, 5.2), (37, 28), (31, 28)], "$p.stripe", alpha=0.9)
    r.poly([(20, 5), (16, 5.2), (3, 28), (9, 28)], "$p.stripe", alpha=0.9)
    r.poly([(14, 28), (20, 12), (26, 28)], "#2A1A10", stroke="$p.outline", width=1.0)
    r.poly([(20, 12), (26, 28), (23, 28), (20, 17)], "#3C2818")
    r.line(20, 5, 20, 1.2, "$p.pole", 1.4)
    r.poly([(20, 1.2), (27, 2.6), (20, 4.2)], "$p.stripe", stroke="$p.outline", width=0.8)
    for (x0, y0, x1, y1) in ((3, 28, 0, 30), (37, 28, 40, 30)):
        r.line(x0, y0, x1, y1, "$p.pole", 0.9)
        r.ellipse(x1, y1, 0.7, 0.7, "#2E2E36")
    return r


def banner() -> Recipe:
    r = prop("banner", 24, 40, (12, 36), {"cloth": "#B8483A", "light": "#E27A68", "dark": "#7A261C", "emblem": "#F2C94C", "outline": "#2E0E08", "pole": "#6A4A2A"})
    r.shadow(13, 37, 6, 1.8, 0.28)
    r.rect(11, 4, 2.4, 33, linear(11, 0, 13.4, 0, (0, "#8A6444"), (1, "$p.pole")), stroke="$p.outline", width=0.9)
    r.ellipse(12.2, 3.2, 2.6, 2.6, radial(11.4, 2.4, 3.6, (0, "#FFF0A0"), (1, "#D8A82C")), stroke="$p.outline", width=0.8)
    r.path("M 13 7 L 22.5 7 L 22.5 26 L 17.8 22.6 L 13 26 Z", linear(13, 0, 23, 0, (0, "$p.light"), (0.5, "$p.cloth"), (1, "$p.dark")), stroke="$p.outline", width=1.2)
    r.line(13.6, 9, 22, 9, "$p.dark", 0.8, 0.8)
    r.poly([(17.8, 11), (20.4, 15), (17.8, 19.4), (15.2, 15)], "$p.emblem", stroke="$p.outline", width=0.7)
    r.poly([(17.8, 12.4), (19.2, 15), (17.8, 17.6), (16.4, 15)], lighten("#F2C94C", 0.5), alpha=0.8)
    for y in (12, 17, 22):
        r.line(14, y, 14.8, y + 1, "$p.dark", 0.6, 0.7)
    return r


def well() -> Recipe:
    r = prop("well", 32, 36, (16, 32), {"stone": "#8F8F98", "water": "#3C78B4", "wood": "#7A5230", "roof": "#B04A3A"})
    r.shadow(17, 31, 14, 3.6, 0.28)
    r.ellipse(16, 23, 13, 8.4, "#5A5A62", stroke="#2A2A30", width=1.3)
    r.ellipse(16, 22, 12, 7.4, linear(4, 14, 28, 30, (0, lighten("#8F8F98", 0.3)), (1, "#6A6A72")))
    for k in range(9):  # the stones of the rim
        a = k / 9 * 6.28
        x, y = 16 + 11.3 * math.cos(a), 22 + 6.7 * math.sin(a)
        r.ellipse(x, y, 2.2, 1.6, mix("#8F8F98", "#BCBCC4", (k % 3) / 3), stroke="#3A3A42", width=0.5)
    r.ellipse(16, 20.5, 8.6, 5.2, "#1E3A5A")
    r.ellipse(16, 20.9, 8.0, 4.7, radial(14, 19.5, 9, (0, "#6CB0E8"), (1, "$p.water")))
    r.path("M 11 21 Q 14 19.4 17 21", None, stroke="#C8E4FA", width=0.7, alpha=0.9)
    for x in (7, 24):
        r.rect(x, 7, 2.6, 15, linear(x, 0, x + 2.6, 0, (0, "#9A6A44"), (1, "$p.wood")), stroke="#2E1C0A", width=1.0)
    r.rect(7, 12, 18.6, 1.8, "$p.wood", stroke="#2E1C0A", width=0.8)
    r.line(16, 12, 16, 17.5, "#D8C8A0", 0.7)
    r.rect(14.4, 17, 3.2, 2.4, "#6A4A2A", stroke="#2E1C0A", width=0.6)
    r.poly([(3, 9), (16, 1.4), (29, 9)], "$p.roof", stroke="#4A1E14", width=1.3)
    r.poly([(3, 9), (16, 1.4), (17, 9)], lighten("#B04A3A", 0.25), alpha=0.85)
    r.poly([(16, 1.4), (29, 9), (22, 9)], darken("#B04A3A", 0.25), alpha=0.7)
    for x in (8, 12.5, 17.5, 22):
        r.line(x, 3.4 + abs(x - 16) * 0.28, x + 0.6, 8.8, "#4A1E14", 0.6, 0.7)
    return r


def threshold_stone() -> Recipe:
    r = prop("threshold_stone", 32, 44, (16, 40), {"light": "#A9B3C4", "body": "#6C7585", "dark": "#3F4756", "outline": "#232A36", "rune": "#6FE3FF"})
    r.ellipse(16, 22, 15, 20, "$p.rune", alpha=0.10)
    r.ellipse(16, 24, 11, 15, "$p.rune", alpha=0.12)
    r.shadow(17, 40.5, 12.5, 3.4, 0.30)
    r.poly([(6, 41), (26, 41), (23, 35), (9, 35)], "$p.body", stroke="$p.outline", width=1.4)
    r.poly([(9, 35), (23, 35), (24, 33), (8, 33)], "$p.light", alpha=0.8)
    r.path("M 9 35 Q 7 22 11 12 Q 16 3 21 12 Q 25 22 23 35 Z", linear(8, 0, 24, 0, (0, "$p.light"), (0.45, "$p.body"), (1, "$p.dark")), stroke="$p.outline", width=1.5)
    r.path("M 11 33 Q 10 22 13 14", None, stroke=lighten("#A9B3C4", 0.4), width=1.0, alpha=0.6)
    r.path("M 16 11 L 16 15 M 14 13 L 18 13", None, stroke="$p.rune", width=0.9)
    r.poly([(16, 17), (19.4, 22), (16, 28), (12.6, 22)], "$p.rune", alpha=0.35, stroke="$p.rune", width=1.2)
    r.poly([(16, 19), (17.8, 22), (16, 25.4), (14.2, 22)], "#E4FBFF")
    for (x, y) in ((11.5, 30), (20.5, 29), (13, 15.5), (19.6, 16.5)):
        r.line(x - 1, y, x + 1, y, "$p.rune", 0.8, 0.9)
        r.line(x, y - 1, x, y + 1, "$p.rune", 0.8, 0.9)
    for x, y in ((6, 28), (26, 24), (9, 12), (24, 10)):  # motes of light
        r.ellipse(x, y, 0.7, 0.7, "$p.rune", alpha=0.8)
    return r


def stall() -> Recipe:
    r = prop("stall", 40, 34, (20, 30), {"wood": "#9A6A38", "cloth": "#C9302C", "cloth2": "#F4EFE0", "outline": "#2E1C0A"})
    r.shadow(21, 31, 17, 3, 0.28)
    r.rect(4, 17, 32, 11, linear(0, 17, 0, 28, (0, "#B88650"), (1, "#7A4F2A")), stroke="$p.outline", width=1.3)
    r.rect(4, 17, 32, 2.4, "#D8A468", alpha=0.7)
    for fx, color in ((9, "#E85A3A"), (14, "#F2C94C"), (19, "#7AC24A"), (25, "#E85A3A"), (30, "#B8553A")):
        r.ellipse(fx, 20, 2.3, 1.7, color, stroke="#3A2010", width=0.5)
    for px in (5, 34):
        r.rect(px, 6, 2, 22, "$p.wood", stroke="$p.outline", width=1.0)
    r.path("M 2 4 L 38 4 L 40 14 L 0 14 Z", "$p.cloth", stroke="$p.outline", width=1.3)
    for k in range(5):
        x0 = 2 + k * 7.2
        r.poly([(x0, 4), (x0 + 3.6, 4), (x0 + 3.2 + 0.4 * k * 0, 14), (x0 - 0.4, 14)], "$p.cloth2", alpha=0.95)
    r.path("M 0 14 Q 3.3 17.5 6.6 14 Q 10 17.5 13.4 14 Q 16.8 17.5 20 14 Q 23.2 17.5 26.6 14 Q 30 17.5 33.4 14 Q 36.8 17.5 40 14", None, stroke="$p.outline", width=1.0)
    r.rect(2, 4, 36, 1.8, "#FFFFFF", alpha=0.25)
    return r


def haybale() -> Recipe:
    r = prop("haybale", 30, 24, (15, 21), {"hay": "#E0C060", "dark": "#A8862A", "light": "#F4DC8A", "outline": "#4A3410"})
    r.shadow(16, 22, 13, 2.6, 0.28)
    r.rect(3, 6, 24, 15, linear(0, 6, 0, 21, (0, "$p.light"), (0.45, "$p.hay"), (1, "$p.dark")), stroke="$p.outline", width=1.3)
    for y in (10, 14, 18):
        r.path(f"M 4 {y} Q 15 {y + 1.2} 26 {y}", None, stroke="$p.dark", width=0.6, alpha=0.7)
    for x in (9.5, 20.5):
        r.rect(x, 6, 1.6, 15, "#7A5A2A", alpha=0.85)
    for x, y, a in ((6, 8, 0.8), (13, 12, -0.6), (22, 9, 0.6), (17, 17, -0.8), (8, 18, 0.5)):
        r.line(x, y, x + 3 * a, y - 1.2, "$p.light", width=0.6, alpha=0.9)
    r.path("M 3 6 Q 15 2 27 6", None, stroke="$p.light", width=1.0, alpha=0.6)
    return r


def anvil() -> Recipe:
    """An anvil on a stump, with a hammer: where fine gear is made (spec 06, "Stations")."""
    r = prop("anvil", 32, 28, (16, 25), {"iron": "#5C6470", "light": "#A9B2BE", "dark": "#2E333A", "wood": "#8A5A2E", "outline": "#1A1C20"})
    r.shadow(16, 25, 12, 2.6, 0.3)
    r.rect(9, 15, 14, 10, linear(0, 15, 0, 25, (0, "#A06A38"), (1, "#5E3A1A")), stroke="$p.outline", width=1.2)
    r.path("M 9 17 Q 16 15.5 23 17", None, stroke="#C08A50", width=0.7, alpha=0.8)
    r.path("M 11 15 L 21 15 L 22 12 L 26 11 L 28 8 L 4 8 L 6 11 L 10 12 Z", linear(0, 8, 0, 15, (0, "$p.light"), (0.5, "$p.iron"), (1, "$p.dark")), stroke="$p.outline", width=1.2)
    r.rect(4, 7, 24, 1.6, "#FFFFFF", alpha=0.3)
    r.rect(20, 3, 2, 6, "$p.wood", stroke="$p.outline", width=0.8)
    r.rect(17, 2, 8, 2.6, "$p.iron", stroke="$p.outline", width=0.8)
    r.ellipse(8, 21, 1.4, 1.0, "#F2A03A", alpha=0.85)
    return r


def reeds() -> Recipe:
    """Reeds on the shore, with a ripple and a fish under the water: where one fishes (spec 06, "Gathering")."""
    r = prop("reeds", 32, 28, (16, 24), {"reed": "#7FA44A", "light": "#B8D478", "dark": "#4A6A28", "water": "#4A8AC8", "outline": "#22341A"})
    r.ellipse(16, 24, 13, 3.6, "#2E6AA8", alpha=0.45)  # the water at the foot
    r.ellipse(16, 24, 9, 2.4, "#FFFFFF", stroke="#FFFFFF", width=0.6, alpha=0.25)  # a ripple
    r.ellipse(24, 23.5, 2.6, 1.0, "#E8B040", alpha=0.7)  # a fish, just under the surface
    for x0, top, lean in ((8, 7, -2.0), (11, 4, -0.8), (14, 6, 0.5), (17, 3, 1.2), (20, 8, 2.0), (23, 10, 2.6)):
        r.path(f"M {x0} 24 Q {x0 + lean * 0.4} {(24 + top) / 2} {x0 + lean} {top}", None, stroke="$p.reed", width=1.4)
        r.path(f"M {x0} 24 Q {x0 + lean * 0.4} {(24 + top) / 2} {x0 + lean} {top}", None, stroke="$p.light", width=0.5, alpha=0.7)
    for x, y in ((11 - 0.8, 4), (17 + 1.2, 3)):  # two cattail heads
        r.ellipse(x, y + 2.5, 1.3, 2.6, "#7A4A22", stroke="$p.outline", width=0.5)
    return r


def build_props() -> list[Recipe]:
    return [tree_oak(), pine(), dead_tree(), bush(), rock(), cactus(), campfire(), crate(), barrel(), bones(), lamp(), signpost(), statue(), tent(), banner(), well(), threshold_stone(), stall(), haybale(), anvil(), reeds()]
