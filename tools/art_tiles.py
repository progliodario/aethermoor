"""The terrain tiles of data/base/art/tiles/, painted in the way of an anime background (docs/design/art-style.md).

The ground tiles are **macro tiles**: a recipe of 128 x 128 art units covers 4 x 4 tiles (spec 13, "Macro tiles"), so the
painted ground does not repeat at every tile. Its base is a noise fill that repeats every 128 units and is the same for
every variant of a ground (grass_a to grass_f share one), so that any variant joins any other; the small things (tufts,
flowers, pebbles) stay inside their own tile. Walls, floors and the bridge are plain 32 x 32 tiles.
Used by `make_art.py`.
"""
from __future__ import annotations

import math

from artkit import Recipe, darken, lighten, linear, mix, noise, radial

TILE = 32
SPAN = 4
MACRO = TILE * SPAN


def macro(name: str, base: str, extra: dict | None = None) -> Recipe:
    return Recipe(f"base:art/tile/{name}", MACRO, MACRO, (0, 0), {"base": base, **(extra or {})}, seed="v3")


def small(name: str, palette: dict) -> Recipe:
    return Recipe(f"base:art/tile/{name}", TILE, TILE, (0, 0), palette, seed="v3")


def cells(r: Recipe, n: int, margin: float = 3.0):
    """n points in every tile of a macro tile, away from the edges of the tile by margin."""
    span = int(r.w // TILE)
    for cy in range(span):
        for cx in range(span):
            for _ in range(n):
                yield (cx * TILE + r.rng.uniform(margin, TILE - margin), cy * TILE + r.rng.uniform(margin, TILE - margin))


def paint(r: Recipe, seed: int, dark: str, mid: str, light: str, grain: str | None = None, grain_alpha: float = 0.2,
          spread: float = 1.0) -> None:
    """The painted base of a ground: large soft clouds of three tones, a finer cloud over them, and a grain."""
    lo, hi = 0.5 - 0.22 * spread, 0.5 + 0.22 * spread
    r.rect(0, 0, r.w, r.h, noise(TILE, seed, (lo, dark), (0.5, mid), (hi, light), octaves=4, period=int(r.w // TILE)))
    r.rect(0, 0, r.w, r.h, noise(8, seed + 7, (0.3, darken(dark, 0.25)), (0.5, mid + "00"), (0.72, lighten(light, 0.2)),
                                 octaves=2, period=int(r.w // 8)), alpha=0.45)
    if grain:
        r.rect(0, 0, r.w, r.h, noise(4, seed + 13, (0.3, grain), (0.52, grain + "00"), octaves=3, period=int(r.w // 4)), alpha=grain_alpha)


# ------------------------------------------------------------------------------------------------ small things
def tuft(r: Recipe, x: float, y: float, dark: str, light: str, h: float = 5.0, n: int = 5) -> None:
    """A tuft of grass: thin curved blades, dark at the foot and light at the tip."""
    r.ellipse(x, y + 0.3, 2.6, 1.0, "#10301E", alpha=0.25, blur=0.6)
    for i in range(n):
        lean = (i - (n - 1) / 2) * 1.1 + r.rng.uniform(-0.5, 0.5)
        bh = h * r.rng.uniform(0.6, 1.0)
        bx = x + (i - (n - 1) / 2) * 0.75
        color = mix(dark, light, r.rng.uniform(0.0, 1.0))
        r.path(f"M {bx - 0.45:.2f} {y:.2f} Q {bx + lean * 0.3:.2f} {y - bh * 0.6:.2f} {bx + lean:.2f} {y - bh:.2f} "
               f"Q {bx + lean * 0.5 + 0.3:.2f} {y - bh * 0.5:.2f} {bx + 0.45:.2f} {y:.2f} Z", color)
    r.path(f"M {x:.2f} {y:.2f} Q {x + 0.2:.2f} {y - h * 0.5:.2f} {x + 0.9:.2f} {y - h * 0.85:.2f}", None, stroke=lighten(light, 0.25), width=0.3, alpha=0.8)


def flower(r: Recipe, x: float, y: float, color: str, size: float = 1.0) -> None:
    r.line(x, y, x + 0.3, y + 2.2 * size, "#2F7A3A", 0.4)
    for k in range(5):
        a = k * 2 * math.pi / 5 - 0.5
        r.ellipse(x + math.cos(a) * 0.9 * size, y + math.sin(a) * 0.8 * size, 0.75 * size, 0.6 * size, color)
    r.ellipse(x - 0.2 * size, y - 0.3 * size, 0.8 * size, 0.6 * size, "#FFFFFF", alpha=0.35)
    r.ellipse(x, y, 0.45 * size, 0.4 * size, "#FFD860")


def pebble(r: Recipe, x: float, y: float, size: float, color: str) -> None:
    r.ellipse(x + size * 0.3, y + size * 0.45, size * 1.1, size * 0.6, "#141030", alpha=0.3, blur=size * 0.3)
    d = (f"M {x - size:.2f} {y + size * 0.2:.2f} Q {x - size * 0.9:.2f} {y - size * 0.7:.2f} {x - size * 0.1:.2f} {y - size * 0.75:.2f} "
         f"Q {x + size * 0.9:.2f} {y - size * 0.7:.2f} {x + size:.2f} {y + size * 0.15:.2f} Q {x + size * 0.6:.2f} {y + size * 0.7:.2f} {x - size * 0.2:.2f} {y + size * 0.65:.2f} "
         f"Q {x - size * 0.9:.2f} {y + size * 0.6:.2f} {x - size:.2f} {y + size * 0.2:.2f} Z")
    r.path(d, linear(x - size, y - size, x + size, y + size, (0, lighten(color, 0.35)), (0.5, color), (1, darken(color, 0.35))),
           stroke=darken(color, 0.5), width=0.25)
    r.path(f"M {x - size * 0.6:.2f} {y - size * 0.3:.2f} Q {x - size * 0.2:.2f} {y - size * 0.6:.2f} {x + size * 0.3:.2f} {y - size * 0.45:.2f}",
           None, stroke="#FFFFFF", width=0.3, alpha=0.6)


def leaf(r: Recipe, x: float, y: float, color: str, size: float = 1.6) -> None:
    a = r.rng.uniform(0, math.pi)
    dx, dy = math.cos(a) * size, math.sin(a) * size
    nx, ny = -dy * 0.45, dx * 0.45
    r.path(f"M {x - dx:.2f} {y - dy:.2f} Q {x + nx:.2f} {y + ny:.2f} {x + dx:.2f} {y + dy:.2f} Q {x - nx:.2f} {y - ny:.2f} {x - dx:.2f} {y - dy:.2f} Z", color)
    r.line(x - dx, y - dy, x + dx, y + dy, darken(color, 0.35), 0.25)


def sparkle(r: Recipe, x: float, y: float, s: float, alpha: float = 0.9, color: str = "#FFFFFF") -> None:
    r.poly([(x, y - s * 1.7), (x + s * 0.35, y - s * 0.35), (x + s * 1.7, y), (x + s * 0.35, y + s * 0.35),
            (x, y + s * 1.7), (x - s * 0.35, y + s * 0.35), (x - s * 1.7, y), (x - s * 0.35, y - s * 0.35)], color, alpha=alpha)


def sunspots(r: Recipe, n: int, color: str = "#FFF2B0", alpha: float = 0.16) -> None:
    """Soft patches of warm light, as through leaves or clouds."""
    for x, y in cells(r, n, 8):
        rad = r.rng.uniform(3.5, 7)
        r.ellipse(x, y, rad * 1.3, rad * 0.8, color, alpha=alpha, blend="add", blur=rad * 0.5)


# ------------------------------------------------------------------------------------------------ grounds
GRASS = ("#2F7F4A", "#4FA352", "#8CC860")


def grass(name: str, tones=GRASS, seed: int = 11, flowers=None, clover=False, mushrooms=False, dry=False, pebbles: int = 0,
          tufts: int = 5, tuft_tones=("#2A7040", "#9AD468")) -> Recipe:
    r = macro(name, tones[1])
    paint(r, seed, *tones, grain="#1E5A36")
    sunspots(r, 1)
    if dry:
        for x, y in cells(r, 2, 7):
            r.ellipse(x, y, r.rng.uniform(4, 7), r.rng.uniform(2.5, 4), "#D8C46A", alpha=0.3, blur=2.0)
    if clover:
        for x, y in cells(r, 2, 6):
            for k in range(3):
                a = k * 2.1 + r.rng.uniform(0, 1)
                cx, cy = x + math.cos(a) * 1.5, y + math.sin(a) * 1.3
                r.ellipse(cx, cy, 1.5, 1.2, "#2E7A40")
                r.ellipse(cx - 0.3, cy - 0.3, 0.8, 0.6, "#6FBE64", alpha=0.8)
    for x, y in cells(r, tufts, 4):
        tuft(r, x, y, *tuft_tones, h=r.rng.uniform(3.5, 6))
    for x, y in cells(r, pebbles, 4):
        pebble(r, x, y, r.rng.uniform(0.9, 1.7), "#9A9AA6")
    if flowers:
        for x, y in cells(r, 3, 4):
            flower(r, x, y, r.rng.choice(flowers), r.rng.uniform(0.8, 1.1))
    if mushrooms:
        for x, y in cells(r, 1, 8):
            if r.rng.random() > 0.3:  # a few rings of mushrooms in a meadow, not one in every tile
                continue
            for (dx, dy, s) in ((0, 0, 1.0), (4.5, 2.5, 0.75), (-3.5, 3, 0.6)):
                mx, my = x + dx, y + dy
                r.ellipse(mx + 0.5, my + 3 * s, 3 * s, 1 * s, "#141030", alpha=0.3, blur=0.6)
                r.rect(mx - 0.8 * s, my, 1.6 * s, 3 * s, linear(mx - s, my, mx + s, my, (0, "#FFF6E4"), (1, "#C9B79A")))
                r.path(f"M {mx - 3.2 * s:.2f} {my + 0.6 * s:.2f} Q {mx - 2.6 * s:.2f} {my - 2.6 * s:.2f} {mx:.2f} {my - 2.6 * s:.2f} Q {mx + 2.6 * s:.2f} {my - 2.6 * s:.2f} {mx + 3.2 * s:.2f} {my + 0.6 * s:.2f} Q {mx:.2f} {my + 1.5 * s:.2f} {mx - 3.2 * s:.2f} {my + 0.6 * s:.2f} Z",
                       radial(mx - s, my - 1.6 * s, 4.5 * s, (0, "#F0705A"), (0.6, "#C83C34"), (1, "#8A2030")), stroke="#5A1420", width=0.25)
                r.ellipse(mx - 1.1 * s, my - 1.2 * s, 0.6 * s, 0.45 * s, "#FFFFFF", alpha=0.9)
                r.ellipse(mx + 1.0 * s, my - 0.5 * s, 0.45 * s, 0.35 * s, "#FFFFFF", alpha=0.9)
    return r


def forest_floor() -> Recipe:
    r = macro("forest_floor", "#356F3E")
    paint(r, 23, "#1F4E34", "#356F3E", "#5C9A4C", grain="#143A26", grain_alpha=0.3)
    sunspots(r, 3, "#FFF0A0", 0.2)  # dappled light through the leaves
    for x, y in cells(r, 6, 3):
        leaf(r, x, y, r.rng.choice(["#A86B32", "#C98A3C", "#8A5A2A", "#B8742E", "#D8A040"]), r.rng.uniform(1.2, 2.0))
    for x, y in cells(r, 3, 4):
        tuft(r, x, y, "#1F5A30", "#6FB85A", h=r.rng.uniform(3, 5))
    for x, y in cells(r, 1, 5):
        pebble(r, x, y, r.rng.uniform(0.8, 1.4), "#7E8A84")
    return r


def moss(name: str, seed: int, mushrooms: bool) -> Recipe:
    r = macro(name, "#2F6B3F")
    paint(r, seed, "#16402C", "#2A6240", "#4E9050", grain="#0E2E20", grain_alpha=0.35)
    for x, y in cells(r, 4, 4):  # cushions of moss
        rad = r.rng.uniform(1.8, 3.4)
        c = mix("#3E8A4A", "#7CC060", r.rng.random())
        r.ellipse(x + 0.4, y + 0.6, rad * 1.2, rad * 0.8, "#0A2418", alpha=0.35, blur=0.7)
        r.ellipse(x, y, rad * 1.15, rad * 0.75, radial(x - rad * 0.4, y - rad * 0.4, rad * 1.6, (0, lighten(c, 0.3)), (0.6, c), (1, darken(c, 0.35))))
    sunspots(r, 1, "#D8F0A0", 0.12)
    for x, y in cells(r, 3, 4):
        tuft(r, x, y, "#184A2A", "#5FA85A", h=r.rng.uniform(3, 4.5))
    if mushrooms:
        for x, y in cells(r, 1, 6):
            r.rect(x - 0.6, y, 1.2, 2.6, "#E8DFEA")
            r.ellipse(x, y, 2.6, 1.8, radial(x - 0.8, y - 0.8, 3.4, (0, "#D8B0F8"), (1, "#7A4AB8")), stroke="#3A1E6A", width=0.2)
            r.ellipse(x - 0.8, y - 0.6, 0.6, 0.4, "#FFFFFF", alpha=0.9)
            r.glow(x, y, 4, "#B080FF", 0.25)
    else:
        for x, y in cells(r, 1, 8):  # a fallen twig
            r.line(x - 4, y + 1.5, x + 4, y - 1.5, "#3A2A1A", 0.9)
            r.line(x - 4, y + 1.2, x + 4, y - 1.8, "#7A5A38", 0.3, alpha=0.8)
            r.line(x, y, x + 2, y + 2, "#3A2A1A", 0.6)
    return r


def dirt(name: str, tones, seed: int, ruts: bool = False, pebbles: int = 2) -> Recipe:
    r = macro(name, tones[1])
    paint(r, seed, *tones, grain=darken(tones[0], 0.4), grain_alpha=0.3)
    if ruts:  # the tracks of the carts: two soft grooves along every tile
        for cy in range(SPAN):
            for off in (9, 22):
                y = cy * TILE + off
                r.rect(0, y - 1.6, MACRO, 3.2, darken(tones[0], 0.45), alpha=0.35, blur=0.9)
                r.rect(0, y + 1.4, MACRO, 0.6, lighten(tones[2], 0.3), alpha=0.3, blur=0.3)
    for x, y in cells(r, 5, 2):
        rad = r.rng.uniform(0.3, 0.7)
        r.ellipse(x, y, rad, rad * 0.8, darken(tones[0], 0.35), alpha=0.6)
    for x, y in cells(r, pebbles, 4):
        pebble(r, x, y, r.rng.uniform(0.8, 1.6), mix(tones[1], "#8A8A90", 0.6))
    for x, y in cells(r, 1, 5):
        tuft(r, x, y, "#4A7A3A", "#9AC060", h=3, n=3)
    return r


def sand(name: str = "sand") -> Recipe:
    r = macro(name, "#EBD59B")
    paint(r, 41, "#D2B578", "#EBD59B", "#FFF1C4", grain="#A88A50", grain_alpha=0.25)
    for cy in range(SPAN * 4):  # ripples left by the wind
        y = cy * 8 + 4
        d = f"M -2 {y}"
        for cx in range(SPAN * 2 + 1):
            x = cx * 16
            d += f" Q {x + 4} {y - 2.2 + (cy % 3) * 0.6:.1f} {x + 8} {y} Q {x + 12} {y + 2.2 - (cy % 2) * 0.8:.1f} {x + 16} {y}"
        r.path(d, None, stroke="#B8985A", width=0.7, alpha=0.3, blur=0.5)
        r.path(d.replace(f"M -2 {y}", f"M -2 {y + 1.2}"), None, stroke="#FFFBE0", width=0.5, alpha=0.3, blur=0.3)
    for x, y in cells(r, 1, 5):
        pebble(r, x, y, r.rng.uniform(0.6, 1.1), "#CDBB8E")
    for x, y in cells(r, 2, 3):
        sparkle(r, x, y, 0.35, 0.7)
    return r


def coast(name: str, seed: int) -> Recipe:
    r = macro(name, "#7FB068")
    paint(r, 11, "#4E9858", "#7FB068", "#B0D47A", grain="#2E6A40")
    for x, y in cells(r, 2, 7):  # sand showing through the grass
        rx, ry = r.rng.uniform(4, 6.5), r.rng.uniform(2.6, 4)
        r.ellipse(x, y, rx, ry, noise(5, seed, (0.3, "#D8C080"), (0.7, "#F6E8B4"), octaves=2), blur=1.2)
        r.ellipse(x - 1, y - 0.8, rx * 0.5, ry * 0.4, "#FFF6D0", alpha=0.5, blur=0.8)
    for x, y in cells(r, 3, 4):
        tuft(r, x, y, "#4A8A4E", "#B4D880", h=r.rng.uniform(3, 5))
    for x, y in cells(r, 1, 5):
        if r.rng.random() < 0.5:
            flower(r, x, y, "#FFFFFF", 0.8)
        else:  # a shell
            r.ellipse(x, y, 1.3, 0.9, radial(x - 0.4, y - 0.3, 1.6, (0, "#FFFFFF"), (1, "#E8C8B8")), stroke="#A88070", width=0.2)
    return r


def rocky(name: str, seed: int, boulders: int) -> Recipe:
    r = macro(name, "#79946B")
    paint(r, 53, "#56745A", "#79946B", "#A4B884", grain="#3A5444", grain_alpha=0.3)
    for x, y in cells(r, boulders, 8):
        s = r.rng.uniform(3.2, 5.2)
        r.ellipse(x + s * 0.3, y + s * 0.5, s * 1.25, s * 0.55, "#141030", alpha=0.35, blur=1.0)
        d = (f"M {x - s:.2f} {y + s * 0.35:.2f} L {x - s * 0.8:.2f} {y - s * 0.4:.2f} L {x - s * 0.15:.2f} {y - s * 0.8:.2f} L {x + s * 0.7:.2f} {y - s * 0.5:.2f} "
             f"L {x + s:.2f} {y + s * 0.3:.2f} L {x + s * 0.4:.2f} {y + s * 0.7:.2f} L {x - s * 0.5:.2f} {y + s * 0.7:.2f} Z")
        r.path(d, noise(3, seed, (0.3, "#7C8088"), (0.7, "#A8ACB4"), octaves=2), stroke="#3A3C48", width=0.3)
        r.shade(f"M {x - s * 0.15:.2f} {y - s * 0.8:.2f} L {x + s * 0.7:.2f} {y - s * 0.5:.2f} L {x + s:.2f} {y + s * 0.3:.2f} L {x + s * 0.4:.2f} {y + s * 0.7:.2f} L {x - s * 0.5:.2f} {y + s * 0.7:.2f} L {x + s * 0.1:.2f} {y:.2f} Z", 0.45)
        r.path(f"M {x - s * 0.8:.2f} {y - s * 0.4:.2f} L {x - s * 0.15:.2f} {y - s * 0.8:.2f} L {x + s * 0.1:.2f} {y:.2f} Z", "#FFFFFF", alpha=0.22)
        r.ellipse(x - s * 0.5, y + s * 0.55, s * 0.5, s * 0.25, "#6FA85A", alpha=0.7, blur=0.4)  # moss at the foot
    for x, y in cells(r, 2, 4):
        pebble(r, x, y, r.rng.uniform(0.8, 1.5), "#9A9EA6")
    for x, y in cells(r, 3, 4):
        tuft(r, x, y, "#4A7048", "#A8C880", h=r.rng.uniform(3, 4.5), n=4)
    return r


def savanna(name: str, seed: int, crack: bool) -> Recipe:
    r = macro(name, "#C4B058")
    paint(r, 61, "#A08A3E", "#C8B25C", "#EAD88A", grain="#7A6628", grain_alpha=0.28)
    for x, y in cells(r, 5, 4):
        tuft(r, x, y, "#9A8438", "#F0E09A", h=r.rng.uniform(4, 6.5))
    for x, y in cells(r, 2, 4):
        tuft(r, x, y, "#6F8A3C", "#B8C870", h=r.rng.uniform(3, 4.5), n=4)
    for x, y in cells(r, 1, 5):
        pebble(r, x, y, r.rng.uniform(0.8, 1.4), "#B0A07A")
    if crack:
        for x, y in cells(r, 1, 9):
            d = f"M {x - 6:.1f} {y + 2:.1f} L {x - 2:.1f} {y - 1:.1f} L {x + 1:.1f} {y + 1:.1f} L {x + 6:.1f} {y - 3:.1f}"
            r.path(d, None, stroke="#5A4A1E", width=0.7, alpha=0.7)
            r.path(d, None, stroke="#F4E6A8", width=0.25, alpha=0.5)
    return r


def snowfield(name: str, tones, seed: int, crystals: bool = False, tufts: bool = False) -> Recipe:
    r = macro(name, tones[1])
    paint(r, seed, *tones, grain=None)
    for x, y in cells(r, 2, 6):  # drifts: a bluish shade under a bright crest
        rx, ry = r.rng.uniform(5, 8), r.rng.uniform(2, 3.2)
        r.ellipse(x + 1, y + 1.6, rx, ry, darken(tones[0], 0.12), alpha=0.5, blur=1.4)
        r.ellipse(x - 0.5, y - 0.6, rx * 0.9, ry * 0.8, "#FFFFFF", alpha=0.85, blur=1.0)
    for x, y in cells(r, 3, 3):
        sparkle(r, x, y, r.rng.uniform(0.3, 0.5), 0.9)
    if crystals:
        for x, y in cells(r, 2, 5):
            s = r.rng.uniform(1.6, 2.8)
            r.ellipse(x + 0.4, y + s, s * 0.8, s * 0.3, "#203060", alpha=0.3, blur=0.5)
            r.poly([(x, y - s), (x + s * 0.55, y), (x, y + s), (x - s * 0.55, y)], linear(x - s, y - s, x + s, y + s, (0, "#FFFFFF"), (0.5, "#BFE4FF"), (1, "#6FA8E0")), stroke="#4A7AB8", width=0.2)
            r.poly([(x, y - s), (x + s * 0.55, y), (x, y)], "#FFFFFF", alpha=0.6)
            r.glow(x, y, s * 1.6, "#A0E0FF", 0.25)
    if tufts:
        for x, y in cells(r, 2, 4):
            tuft(r, x, y, "#7A988A", "#C4D8CC", h=r.rng.uniform(2.5, 4), n=4)
    return r


def ash(name: str, tones, seed: int, embers: int, cracks: int) -> Recipe:
    r = macro(name, tones[1])
    paint(r, 71, *tones, grain="#0E0C12", grain_alpha=0.35)
    for x, y in cells(r, 2, 6):  # drifts of pale ash
        r.ellipse(x, y, r.rng.uniform(4, 7), r.rng.uniform(1.6, 2.8), lighten(tones[2], 0.25), alpha=0.4, blur=1.2)
    for x, y in cells(r, cracks, 7):
        pts = [(x - 5, y)]
        for _ in range(4):
            px, py = pts[-1]
            pts.append((px + r.rng.uniform(1.5, 3.2), min(max(py + r.rng.uniform(-2.5, 2.5), y - 5), y + 5)))
        d = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in pts)
        r.path(d, None, stroke="#FF5A1E", width=2.2, alpha=0.3, blend="add", blur=1.0)
        r.path(d, None, stroke="#120C0A", width=1.1, alpha=0.9)
        r.path(d, None, stroke="#FF8A3A", width=0.4, alpha=0.9)
    for x, y in cells(r, embers, 4):
        r.glow(x, y, 3.2, "#FF6A20", 0.45)
        r.ellipse(x, y, 0.7, 0.7, "#FFD080")
    for x, y in cells(r, 1, 5):
        pebble(r, x, y, r.rng.uniform(0.8, 1.5), "#5A5A62")
    return r


# ------------------------------------------------------------------------------------------------ water
def water() -> Recipe:
    r = macro("water", "#2F6FC8", {"deep": "#1E4E9E", "wave": "#BFE0FF"})
    r.rect(0, 0, MACRO, MACRO, noise(TILE, 81, (0.28, "#1B4690"), (0.5, "#2F6FC8"), (0.72, "#58A0E8"), octaves=3, period=SPAN))
    r.rect(0, 0, MACRO, MACRO, noise(16, 83, (0.3, "#12306E"), (0.5, "#2F6FC800"), (0.75, "#8CC8FF"), octaves=2, period=MACRO // 16), alpha=0.5)
    for x, y in cells(r, 3, 5):  # glints of the waves: a light crest and its shade
        length = r.rng.uniform(5, 9)
        r.path(f"M {x - length / 2:.1f} {y + 1.1:.1f} Q {x:.1f} {y - 1.4:.1f} {x + length / 2:.1f} {y + 1.1:.1f}", None, stroke="#143A80", width=0.7, alpha=0.5, blur=0.3)
        r.path(f"M {x - length / 2:.1f} {y:.1f} Q {x:.1f} {y - 2.4:.1f} {x + length / 2:.1f} {y:.1f}", None, stroke="$p.wave", width=0.6, alpha=0.8)
    for x, y in cells(r, 1, 5):
        sparkle(r, x, y, r.rng.uniform(0.5, 0.9), 0.9)
        r.glow(x, y, 2.5, "#CFE8FF", 0.3)
    return r


def shallows() -> Recipe:
    r = macro("shallows", "#6CC0E4", {"sand": "#E8D9A6"})
    r.rect(0, 0, MACRO, MACRO, noise(TILE, 91, (0.28, "#4A9CD0"), (0.5, "#6CC0E4"), (0.72, "#9FE0F0"), octaves=3, period=SPAN))
    r.rect(0, 0, MACRO, MACRO, noise(16, 93, (0.45, "#F2E4B000"), (0.7, "#F6EBC4"), octaves=2, period=MACRO // 16), alpha=0.6)  # the sand under the water
    for x, y in cells(r, 3, 5):  # the net of light on the bottom
        length = r.rng.uniform(5, 9)
        r.path(f"M {x - length / 2:.1f} {y:.1f} Q {x - length / 4:.1f} {y - 2:.1f} {x:.1f} {y:.1f} Q {x + length / 4:.1f} {y + 2:.1f} {x + length / 2:.1f} {y:.1f}",
               None, stroke="#F4FFFF", width=0.5, alpha=0.7)
    for x, y in cells(r, 1, 5):
        sparkle(r, x, y, r.rng.uniform(0.4, 0.7), 0.9)
    return r


# ------------------------------------------------------------------------------------------------ rock and buildings
def mountain() -> Recipe:
    r = Recipe("base:art/tile/mountain", 64, 64, (0, 0), {"rock": "#77738A", "snow": "#F6FAFF"}, seed="v3")
    r.rect(0, 0, 64, 64, noise(16, 101, (0.3, "#4A465C"), (0.5, "#6C6880"), (0.7, "#8E8AA0"), octaves=3, period=4))
    peaks = [(14, 30, 4, 12), (46, 28, 3, 13), (30, 46, 14, 14), (10, 62, 36, 9), (52, 60, 34, 10), (32, 20, 2, 8)]
    for cx, base_y, top_y, half in sorted(peaks, key=lambda p: p[1]):
        r.ellipse(cx + 3, base_y, half * 1.1, 2.6, "#141030", alpha=0.4, blur=1.2)
        body = f"M {cx - half} {base_y} L {cx - half * 0.45:.1f} {(base_y + top_y) / 2 + 1:.1f} L {cx} {top_y} L {cx + half * 0.5:.1f} {(base_y + top_y) / 2:.1f} L {cx + half} {base_y} Z"
        r.path(body, noise(5, 103 + cx, (0.3, "#6A6680"), (0.7, "#A8A4BC"), octaves=3), stroke="#2E2A40", width=0.4)
        r.shade(f"M {cx} {top_y} L {cx + half * 0.5:.1f} {(base_y + top_y) / 2:.1f} L {cx + half} {base_y} L {cx + half * 0.15:.1f} {base_y} L {cx + half * 0.2:.1f} {(base_y + top_y) / 2 + 2:.1f} Z", 0.6)
        r.path(f"M {cx} {top_y} L {cx - half * 0.45:.1f} {(base_y + top_y) / 2 + 1:.1f} L {cx - half * 0.2:.1f} {(base_y + top_y) / 2 + 1:.1f} Z", "#FFFFFF", alpha=0.2)
        h = (base_y - top_y) * 0.38
        r.path(f"M {cx} {top_y} L {cx + half * 0.32:.1f} {top_y + h:.1f} L {cx + half * 0.12:.1f} {top_y + h * 0.8:.1f} L {cx} {top_y + h * 1.25:.1f} "
               f"L {cx - half * 0.14:.1f} {top_y + h * 0.8:.1f} L {cx - half * 0.3:.1f} {top_y + h:.1f} Z", linear(cx - half, 0, cx + half, 0, (0, "#FFFFFF"), (1, "#B8CCEE")))
        r.line(cx - half * 0.2, base_y - 3, cx - half * 0.05, (base_y + top_y) / 2 + 3, "#2E2A40", 0.3, alpha=0.5)
    for x, y in ((6, 8), (24, 34), (58, 44), (40, 62), (22, 60)):
        pebble(r, x, y, 1.3, "#8E8AA0")
    return r


def cobble() -> Recipe:
    r = small("cobble", {"base": "#5E5E6A"})
    r.rect(0, 0, TILE, TILE, noise(8, 111, (0.3, "#44444E"), (0.7, "#6A6A76"), octaves=2, period=4))
    stones = [(7, 7, 6.2, 5.0), (22, 6, 6.6, 4.6), (8, 21, 6.4, 5.4), (23, 22, 6.2, 5.2), (15, 14.5, 5.0, 4.0), (31, 14, 3.4, 4.0), (-1, 14, 3.4, 4.0)]
    for i, (x, y, rx, ry) in enumerate(stones):
        c = ["#9C9CA8", "#8C8C9A", "#A8A6B2"][i % 3]
        r.ellipse(x + 0.6, y + 0.9, rx, ry, "#141030", alpha=0.45, blur=0.5)
        d = (f"M {x - rx:.1f} {y:.1f} Q {x - rx:.1f} {y - ry:.1f} {x:.1f} {y - ry:.1f} Q {x + rx:.1f} {y - ry:.1f} {x + rx:.1f} {y:.1f} "
             f"Q {x + rx:.1f} {y + ry:.1f} {x:.1f} {y + ry:.1f} Q {x - rx:.1f} {y + ry:.1f} {x - rx:.1f} {y:.1f} Z")
        r.path(d, noise(3, 113 + i, (0.3, darken(c, 0.12)), (0.7, lighten(c, 0.12)), octaves=2), stroke="#33333E", width=0.3)
        r.ellipse(x - rx * 0.25, y - ry * 0.3, rx * 0.6, ry * 0.45, "#FFFFFF", alpha=0.22, blur=0.8)
        r.path(f"M {x - rx * 0.75:.1f} {y + ry * 0.5:.1f} Q {x:.1f} {y + ry * 1.0:.1f} {x + rx * 0.8:.1f} {y + ry * 0.4:.1f}", None, stroke="#2A2A40", width=0.7, alpha=0.35, blur=0.3)
    for x, y in ((15, 3), (2, 28), (29, 29)):
        r.ellipse(x, y, 1.2, 0.8, "#5A8A50", alpha=0.7, blur=0.3)  # a bit of moss in the gaps
    return r


def planks(r: Recipe, y0: float, rows: int, row_h: float, seed: int) -> None:
    """Rows of boards with grain, a lit upper edge, a dark lower one and nails."""
    for i in range(rows):
        y = y0 + i * row_h
        tone = ["#B07A44", "#A46C3C", "#BA8650", "#AA7442"][i % 4]
        r.rect(0, y, TILE, row_h, noise(6, seed + i, (0.3, darken(tone, 0.14)), (0.7, lighten(tone, 0.12)), octaves=2, period=0))
        for k in range(3):  # the grain
            gy = y + row_h * (0.25 + 0.25 * k)
            r.path(f"M 0 {gy:.1f} Q 8 {gy - 0.7:.1f} 16 {gy + 0.3:.1f} Q 24 {gy + 0.9:.1f} 32 {gy:.1f}", None, stroke=darken(tone, 0.35), width=0.3, alpha=0.5)
        r.rect(0, y, TILE, 0.9, lighten(tone, 0.4), alpha=0.5)
        r.rect(0, y + row_h - 1.0, TILE, 1.0, "#2A1608", alpha=0.55)
        joint = 8 + (i * 13) % 18
        r.rect(joint, y, 0.7, row_h, "#2A1608", alpha=0.7)
        for nx in (joint - 1.6, joint + 2.2):
            r.ellipse(nx, y + row_h / 2, 0.45, 0.45, "#2A1608")
            r.ellipse(nx - 0.12, y + row_h / 2 - 0.12, 0.18, 0.18, "#E8C8A0", alpha=0.7)


def plank_floor() -> Recipe:
    r = small("plank_floor", {"wood": "#B07A44"})
    planks(r, 0, 4, 8, 121)
    r.rect(0, 0, TILE, TILE, linear(0, 0, TILE, TILE, (0, "#FFF0D0"), (1, "#3A2A5A")), alpha=0.1)
    return r


def bridge() -> Recipe:
    r = small("bridge", {"wood": "#A8703A", "water": "#2F6FC8"})
    r.rect(0, 0, TILE, TILE, noise(8, 81, (0.3, "#1B4690"), (0.7, "#58A0E8"), octaves=2, period=4))
    r.rect(0, 1, TILE, 30, "#141030", alpha=0.5, blur=1.0)
    planks(r, 2, 4, 7, 131)
    for y in (0.6, 28.6):  # the rails
        r.rect(0, y, TILE, 2.8, linear(0, y, 0, y + 2.8, (0, "#D8A870"), (0.5, "#8A5A30"), (1, "#4A2C14")), stroke="#2A1608", width=0.3)
        for x in (4, 16, 28):
            r.rect(x - 1.3, y - 0.4, 2.6, 3.6, linear(x - 1.3, 0, x + 1.3, 0, (0, "#C89A60"), (1, "#6A4222")), stroke="#2A1608", width=0.3)
    return r


def wall_stone() -> Recipe:
    r = small("wall_stone", {"base": "#7E8794", "mortar": "#3E4450"})
    r.rect(0, 0, TILE, TILE, "$p.mortar")
    rows = [(0, 8, 0), (8, 8, 7), (16, 8, 0), (24, 8, 7)]
    k = 0
    for ry, rh, off in rows:
        x = -off
        while x < TILE:
            bw = r.rng.choice([13, 15, 17])
            tone = mix("#7A8290", "#A0A8B6", r.rng.random())
            x0, x1 = max(x, 0) + 0.5, min(x + bw, TILE) - 0.5
            if x1 - x0 > 2:
                k += 1
                r.rect(x0, ry + 0.5, x1 - x0, rh - 1.0, noise(4, 141 + k, (0.3, darken(tone, 0.14)), (0.7, lighten(tone, 0.1)), octaves=3))
                r.rect(x0, ry + 0.5, x1 - x0, 1.2, "#FFFFFF", alpha=0.28)
                r.rect(x0, ry + rh - 2.0, x1 - x0, 1.5, "#1E1A3A", alpha=0.35)
                r.rect(x1 - 1.0, ry + 0.5, 1.0, rh - 1.0, "#1E1A3A", alpha=0.25)
            x += bw
    r.rect(0, 0, TILE, 5, linear(0, 0, 0, 5, (0, "#DDE4F0"), (1, "#DDE4F000")), alpha=0.7)  # the lit top of the wall
    r.rect(0, 24, TILE, 8, linear(0, 24, 0, 32, (0, "#1E1A3A00"), (1, "#1E1A3A")), alpha=0.45)  # the shade at the foot
    r.path("M 6 18 L 9 21.5 L 8 26", None, stroke="#2A2E3A", width=0.5, alpha=0.8)
    r.ellipse(26, 29, 4, 1.6, "#5A8A50", alpha=0.6, blur=0.6)
    return r


def _timber_frame(r: Recipe) -> None:
    """The timber frame shared by the house walls: posts at the edges, a beam on the top, a sill at the bottom."""
    def beam(x, y, w, h, across: bool):
        fill = linear(x, y, x if across else x + w, y + h if across else y, (0, "#9A6C40"), (0.35, "#6A4426"), (1, "#3E2412"))
        r.rect(x, y, w, h, fill, stroke="#24140A", width=0.3)
        for k in range(2):
            if across:
                gy = y + h * (0.35 + 0.3 * k)
                r.line(x + 1, gy, x + w - 1, gy + 0.2, "#24140A", 0.25, alpha=0.45)
            else:
                gx = x + w * (0.35 + 0.3 * k)
                r.line(gx, y + 1, gx + 0.2, y + h - 1, "#24140A", 0.25, alpha=0.45)

    r.rect(0, 4.5, TILE, 3.5, linear(0, 4.5, 0, 8, (0, "#2A1E4A"), (1, "#2A1E4A00")), alpha=0.4)  # the shadow of the eaves
    beam(0, 0, TILE, 4.5, True)
    beam(0, 27.5, TILE, 4.5, True)
    for px in (0, 29):
        beam(px, 0, 3, TILE, False)


def _plaster(r: Recipe, seed: int) -> None:
    r.rect(0, 0, TILE, TILE, noise(10, seed, (0.3, "#D9C9A2"), (0.5, "#EADDBC"), (0.72, "#F8EED4"), octaves=3))
    r.rect(0, 0, TILE, TILE, linear(0, 0, 0, TILE, (0, "#FFF6DC00"), (1, "#8A6E9A")), alpha=0.22)
    r.path("M 20 22 L 22 25 L 21 27", None, stroke="#A8946A", width=0.3, alpha=0.7)


def wall_timber() -> Recipe:
    r = small("wall_timber", {"plaster": "#E6D9B8", "beam": "#6A4426"})
    _plaster(r, 151)
    r.path("M 3 27.5 L 29 6", None, stroke="#24140A", width=2.6)
    r.path("M 3 27.5 L 29 6", None, stroke="#6A4426", width=2.0)
    r.path("M 3 27 L 29 5.5", None, stroke="#A87A4A", width=0.5, alpha=0.8)
    _timber_frame(r)
    return r


def wall_window() -> Recipe:
    r = small("wall_window", {"plaster": "#E6D9B8", "beam": "#6A4426"})
    _plaster(r, 153)
    r.rect(7.5, 8.5, 17, 16, "#3A2412", stroke="#24140A", width=0.3)
    r.rect(9, 10, 14, 13, linear(9, 10, 23, 23, (0, "#D8F0FF"), (0.5, "#7FB4E0"), (1, "#3E6EA8")))
    r.path("M 10 22 L 16 10.5 L 19 10.5 L 13 22 Z", "#FFFFFF", alpha=0.35)
    r.path("M 18.5 22.5 L 21.5 15 L 22.6 15 L 20 22.5 Z", "#FFFFFF", alpha=0.25)
    r.rect(15.4, 10, 1.2, 13, "#3A2412")
    r.rect(9, 15.9, 14, 1.2, "#3A2412")
    r.rect(9, 10, 14, 1.4, "#141030", alpha=0.4)  # the shade of the frame on the glass
    r.rect(6.5, 23.6, 19, 2.4, linear(0, 23.6, 0, 26, (0, "#C89A60"), (1, "#6A4222")), stroke="#24140A", width=0.3)  # the sill
    r.rect(6.5, 26, 19, 1.6, "#2A1E4A", alpha=0.3, blur=0.5)
    for fx, c in ((11, "#F06A8A"), (14.5, "#FFD860"), (18, "#F06A8A"), (21, "#FFFFFF")):  # a box of flowers
        r.ellipse(fx, 22.6, 1.9, 1.3, "#3E8A46")
        r.ellipse(fx - 0.4, 22.2, 1.0, 0.7, "#7CC060", alpha=0.8)
        r.ellipse(fx, 21.4, 1.0, 0.9, c)
        r.ellipse(fx - 0.3, 21.1, 0.4, 0.35, "#FFFFFF", alpha=0.6)
    _timber_frame(r)
    return r


def door() -> Recipe:
    r = small("door", {"wood": "#B07A44", "frame": "#6A4426"})
    r.rect(0, 0, TILE, TILE, "#2A1A10")
    for i in range(4):  # upright boards
        x = 3 + i * 6.5
        tone = ["#A8703C", "#B47E48", "#A06A38", "#AE7844"][i]
        r.rect(x, 5, 6.3, 18, noise(5, 161 + i, (0.3, darken(tone, 0.15)), (0.7, lighten(tone, 0.12)), octaves=2), stroke="#24140A", width=0.25)
        r.rect(x, 5, 1.0, 18, "#FFFFFF", alpha=0.14)
    for y in (8.5, 18.5):  # iron bands
        r.rect(3, y, 26, 2.2, linear(0, y, 0, y + 2.2, (0, "#8A8E9A"), (1, "#3A3E4A")), stroke="#1A1C24", width=0.25)
        for x in (5, 12, 20, 27):
            r.ellipse(x, y + 1.1, 0.5, 0.5, "#D8DCE8")
    r.ellipse(24.5, 14.5, 1.4, 1.4, radial(24, 14, 2, (0, "#FFE8A0"), (1, "#9A6A1E")), stroke="#3A2408", width=0.25)  # the handle
    r.rect(0, 5, TILE, 3.5, linear(0, 5, 0, 8.5, (0, "#141030"), (1, "#14103000")), alpha=0.55)
    r.rect(0, 23, TILE, 9, noise(6, 165, (0.3, "#A8A294"), (0.7, "#D4CEC0"), octaves=2))  # the stone threshold
    r.rect(0, 23, TILE, 1.2, "#141030", alpha=0.45)
    r.rect(2, 25, 28, 5.4, "#FFFFFF", alpha=0.18)
    r.path("M 6 28 L 26 28", None, stroke="#7A7468", width=0.4)
    for px in (0, 29):
        r.rect(px, 0, 3, 23.5, linear(px, 0, px + 3, 0, (0, "#9A6C40"), (0.4, "#6A4426"), (1, "#3E2412")), stroke="#24140A", width=0.3)
    r.rect(0, 0, TILE, 5, linear(0, 0, 0, 5, (0, "#9A6C40"), (0.4, "#6A4426"), (1, "#3E2412")), stroke="#24140A", width=0.3)
    return r


# ------------------------------------------------------------------------------------------------ the tiles
def build_tiles() -> list[Recipe]:
    violet = ["#B07AE0", "#8A5CD0", "#D8B8F8"]
    return [
        grass("grass_a", tufts=6),
        grass("grass_b", tufts=4, pebbles=1),
        grass("grass_c", flowers=["#FFFFFF", "#FFF3A0", "#FFD0E0"], tufts=4),
        grass("grass_d", clover=True, tufts=3, pebbles=1),
        grass("grass_e", dry=True, tufts=6, tuft_tones=("#5A8A3A", "#D8D070")),
        grass("grass_f", mushrooms=True, tufts=3),
        grass("violet_a", flowers=violet, tufts=4),
        grass("violet_b", flowers=["#7A9AE8", "#B8C8FF", "#B07AE0"], tufts=4),
        forest_floor(),
        moss("moss_a", 31, True),
        moss("moss_b", 31, False),
        dirt("path_dirt", ("#A87A44", "#C99A5A", "#E4BC7C"), 33, pebbles=2),
        dirt("road", ("#96703E", "#B88A52", "#D4AA70"), 33, ruts=True, pebbles=1),
        sand(),
        coast("coast_a", 43),
        coast("coast_b", 45),
        rocky("rocky_a", 55, 2),
        rocky("rocky_b", 57, 1),
        savanna("savanna_a", 63, False),
        savanna("savanna_b", 65, True),
        snowfield("snow", ("#C4D6F0", "#EAF2FC", "#FFFFFF"), 67),
        snowfield("frost_a", ("#9CBCC8", "#C8E0E2", "#EAF6F6"), 69, crystals=True, tufts=True),
        snowfield("frost_b", ("#9CBCC8", "#C8E0E2", "#EAF6F6"), 69, crystals=True),
        ash("ash_a", ("#26242E", "#3C3A46", "#56525E"), 71, embers=1, cracks=1),
        ash("ash_b", ("#26242E", "#3C3A46", "#56525E"), 73, embers=1, cracks=1),
        ash("ash_c", ("#26242E", "#3C3A46", "#56525E"), 75, embers=2, cracks=0),
        ash("ash_sand", ("#443F38", "#5E584C", "#7C7462"), 77, embers=1, cracks=1),
        water(),
        shallows(),
        mountain(),
        cobble(),
        plank_floor(),
        wall_stone(),
        bridge(),
        wall_timber(),
        wall_window(),
        door(),
    ]
