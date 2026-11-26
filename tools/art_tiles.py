"""The terrain tiles of data/base/art/tiles/, painted to look like real ground seen from above (docs/design/art-style.md).

The ground tiles are **macro tiles**: a recipe of 128 x 128 art units covers 4 x 4 tiles (spec 13, "Macro tiles"), so the
painted ground does not repeat at every tile. Its base is five noise fills that repeat every 128 units and are the same for
every variant of a ground (grass_a to grass_f share them), so that any variant joins any other:

1. the broad light and shade of the land, slow and soft;
2. patches of a darker and a lighter tone;
3. the matter itself, multiplied: the shade between blades, grains or fibres, stretched along y for grass (`scale_y`);
4. the lit tips of that matter, added;
5. a grain finer than a pixel of the smallest bucket.

Over the base go the small things (clumps of blades, pebbles, leaves, flowers), each inside its own tile and away from its
edges (`cells()`), drawn in **batches**: one layer holds every blade of one tone of a tile, so that a tile has hundreds of
blades in a few dozen layers. Every small thing has its contact shadow (a blurred dark layer under it, multiplied) and a
light from the top left. Walls, floors and the bridge are plain 32 x 32 tiles. Used by `make_art.py`.
"""
from __future__ import annotations

import math

from artkit import Recipe, darken, lighten, linear, mix, noise, radial

TILE = 32
SPAN = 4
MACRO = TILE * SPAN
LIGHT = "#FFF4DC"  # the warm light of the sun
AO = "#2A2018"  # the dark of a contact shadow (multiplied: it keeps the hue of the ground)


def macro(name: str, base: str, extra: dict | None = None) -> Recipe:
    return Recipe(f"base:art/tile/{name}", MACRO, MACRO, (0, 0), {"base": base, **(extra or {})}, seed="v4")


def small(name: str, palette: dict) -> Recipe:
    return Recipe(f"base:art/tile/{name}", TILE, TILE, (0, 0), palette, seed="v4")


def per(size: float, scale: float) -> int:
    """The period, in cells, that makes a noise of `scale` repeat every `size` art units."""
    n = size / scale
    assert abs(n - round(n)) < 1e-9, (size, scale)
    return int(round(n))


def nz(r: Recipe, scale: float, seed: int, *stops, octaves: int = 3, scale_y: float | None = None, ridged: bool = False) -> dict:
    """A noise fill that repeats with the canvas (a tile joins itself and the other variants of its ground)."""
    return noise(scale, seed, *stops, octaves=octaves, period=per(r.w, scale), scale_y=scale_y,
                 period_y=per(r.h, scale_y) if scale_y else None, ridged=ridged)


def cells(r: Recipe, n: int, margin: float = 3.0):
    """n points in every tile of a macro tile, away from the edges of the tile by margin."""
    span = int(r.w // TILE)
    for cy in range(span):
        for cx in range(span):
            for _ in range(n):
                yield (cx * TILE + r.rng.uniform(margin, TILE - margin), cy * TILE + r.rng.uniform(margin, TILE - margin))


def tiles_of(r: Recipe):
    """The top left corner of every tile of a canvas."""
    span = int(r.w // TILE)
    for cy in range(span):
        for cx in range(span):
            yield cx * TILE, cy * TILE


def inside(r: Recipe, x0: float, y0: float, n: int, margin: float = 3.0):
    """n points inside the tile at (x0, y0), away from its edges by margin."""
    return [(x0 + r.rng.uniform(margin, TILE - margin), y0 + r.rng.uniform(margin, TILE - margin)) for _ in range(n)]


def _f(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


# ------------------------------------------------------------------------------------------------ the base
def ground(r: Recipe, seed: int, dark: str, mid: str, light: str, *, streak: tuple[float, float] = (1.0, 1.0), texture: float = 0.55,
           tips: str = LIGHT, tips_alpha: float = 0.22, grain: float = 0.3, patches: float = 0.42) -> None:
    """The five layers of a ground (see the docstring of the module)."""
    w = r.w
    r.rect(0, 0, w, w, nz(r, 32, seed, (0.3, mix(mid, dark, 0.32)), (0.5, mid), (0.7, mix(mid, light, 0.3)), octaves=4))
    r.rect(0, 0, w, w, nz(r, 16, seed + 1, (0.34, dark), (0.46, dark + "00"), (0.56, light + "00"), (0.68, light), octaves=3), alpha=patches)
    sx, sy = streak
    r.rect(0, 0, w, w, nz(r, sx, seed + 2, (0.26, darken(dark, 0.45)), (0.6, "#FFFFFF"), octaves=3, scale_y=sy), blend="multiply", alpha=texture)
    r.rect(0, 0, w, w, nz(r, sx, seed + 3, (0.58, "#000000"), (0.84, tips), octaves=2, scale_y=sy), blend="add", alpha=tips_alpha)
    r.rect(0, 0, w, w, nz(r, 0.5, seed + 4, (0.22, "#8E8680"), (0.62, "#FFFFFF"), octaves=1), blend="multiply", alpha=grain)


def light_and_shade(r: Recipe, seed: int, alpha: float = 0.1) -> None:
    """Broad soft light and shadow over the ground, as of clouds and of the canopy (the same for every variant)."""
    r.rect(0, 0, r.w, r.h, nz(r, 64, seed, (0.36, "#3A3460"), (0.5, "#FFFFFF"), octaves=2), blend="multiply", alpha=alpha)
    r.rect(0, 0, r.w, r.h, nz(r, 64, seed + 1, (0.55, "#000000"), (0.72, "#FFE6A8"), octaves=2), blend="add", alpha=alpha * 0.8)


# ------------------------------------------------------------------------------------------------ batches of small things
def blade(x: float, y: float, h: float, lean: float, w: float = 0.42) -> str:
    """One blade of grass: a thin curved spike from its foot at (x, y)."""
    return (f"M {_f(x - w)} {_f(y)} Q {_f(x + lean * 0.35 - w * 0.3)} {_f(y - h * 0.55)} {_f(x + lean)} {_f(y - h)} "
            f"Q {_f(x + lean * 0.35 + w * 0.5)} {_f(y - h * 0.5)} {_f(x + w)} {_f(y)} Z")


def clumps(r: Recipe, x0: float, y0: float, n: int, tones: tuple[str, str, str], h: tuple[float, float] = (3.0, 6.0),
           blades: int = 8, margin: float = 4.0, ao: float = 0.5) -> None:
    """Clumps of grass inside one tile: a soft contact shadow, then blades in three tones (dark at the back, lit in
    front), each tone one layer."""
    spots = inside(r, x0, y0, n, margin)
    shade = " ".join(f"M {_f(x - 2.6)} {_f(y)} Q {_f(x)} {_f(y - 1.6)} {_f(x + 2.6)} {_f(y)} Q {_f(x)} {_f(y + 1.3)} {_f(x - 2.6)} {_f(y)} Z" for x, y in spots)
    if spots:
        r.path(shade, AO, alpha=ao, blend="multiply", blur=0.8)
    parts: list[list[str]] = [[], [], []]
    for x, y in spots:
        size = r.rng.uniform(*h)
        for i in range(blades):
            spread = (i - (blades - 1) / 2) / max(1, blades - 1)
            bx = x + spread * 4.2 + r.rng.uniform(-0.4, 0.4)
            by = y + r.rng.uniform(-0.6, 0.8)
            lean = spread * 2.6 + r.rng.uniform(-0.8, 0.8)
            tone = 0 if i % 3 == 0 else (1 if i % 3 == 1 else 2)
            parts[tone].append(blade(bx, by, size * r.rng.uniform(0.55, 1.0), lean, r.rng.uniform(0.3, 0.5)))
    top = y0 + margin - h[1]
    for tone, d in zip(tones, parts):
        if d:
            r.path(" ".join(d), linear(0, y0 + TILE, 0, top, (0, darken(tone, 0.35)), (0.6, tone), (1, lighten(tone, 0.3))))


def field_blades(r: Recipe, x0: float, y0: float, n: int, tones: tuple[str, ...], h: tuple[float, float] = (1.6, 3.4), margin: float = 1.5) -> None:
    """Many small loose blades over a tile, in a few tones (one layer each): the grass between the clumps."""
    groups: list[list[str]] = [[] for _ in tones]
    for x, y in inside(r, x0, y0, n, margin):
        groups[r.rng.randrange(len(tones))].append(blade(x, y, r.rng.uniform(*h), r.rng.uniform(-1.2, 1.2), r.rng.uniform(0.22, 0.34)))
    for tone, d in zip(tones, groups):
        if d:
            r.path(" ".join(d), tone, alpha=0.9)


def stone_path(x: float, y: float, s: float, rng, flat: float = 0.72) -> str:
    """An irregular rounded stone of size s around (x, y)."""
    n = 7
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.25, 0.25)
        rad = s * rng.uniform(0.78, 1.08)
        pts.append((x + math.cos(a) * rad, y + math.sin(a) * rad * flat))
    d = f"M {_f((pts[-1][0] + pts[0][0]) / 2)} {_f((pts[-1][1] + pts[0][1]) / 2)}"
    for i, (px, py) in enumerate(pts):
        nx, ny = pts[(i + 1) % n]
        d += f" Q {_f(px)} {_f(py)} {_f((px + nx) / 2)} {_f((py + ny) / 2)}"
    return d + " Z"


def stones(r: Recipe, spots: list[tuple[float, float, float]], base: str, seed: int, moss: str | None = None, flat: float = 0.72) -> None:
    """Stones in one batch: a contact shadow, the stone with the grain of rock, a light on top, a shade below, and moss."""
    if not spots:
        return
    shapes = [stone_path(x, y, s, r.rng, flat) for x, y, s in spots]
    r.path(" ".join(stone_path(x + s * 0.25, y + s * 0.45, s * 1.08, r.rng, flat) for x, y, s in spots), AO, alpha=0.6, blend="multiply", blur=0.6)
    r.path(" ".join(shapes), noise(1.4, seed, (0.3, darken(base, 0.22)), (0.5, base), (0.72, lighten(base, 0.18)), octaves=3))
    r.path(" ".join(shapes), noise(0.9, seed + 1, (0.7, "#FFFFFF"), (0.92, darken(base, 0.55)), octaves=2, ridged=True), blend="multiply", alpha=0.4)
    r.path(" ".join(f"M {_f(x - s * 0.9)} {_f(y + s * 0.1)} Q {_f(x - s * 0.6)} {_f(y - s * 0.75 * flat)} {_f(x + s * 0.3)} {_f(y - s * 0.7 * flat)} "
                    f"Q {_f(x - s * 0.2)} {_f(y - s * 0.2)} {_f(x - s * 0.9)} {_f(y + s * 0.1)} Z" for x, y, s in spots),
           LIGHT, alpha=0.45, blend="add", blur=0.35)
    r.path(" ".join(f"M {_f(x - s)} {_f(y + s * 0.15)} Q {_f(x)} {_f(y + s * 0.55)} {_f(x + s)} {_f(y - s * 0.1)} Q {_f(x + s * 0.9)} {_f(y + s * 0.8 * flat)} "
                    f"{_f(x)} {_f(y + s * 0.78 * flat)} Q {_f(x - s * 0.9)} {_f(y + s * 0.7 * flat)} {_f(x - s)} {_f(y + s * 0.15)} Z" for x, y, s in spots),
           "#3A3456", alpha=0.45, blend="multiply", blur=0.35)
    if moss:
        r.path(" ".join(f"M {_f(x - s * 0.9)} {_f(y + s * 0.45)} Q {_f(x - s * 0.3)} {_f(y + s * 0.2)} {_f(x + s * 0.2)} {_f(y + s * 0.6)} "
                        f"Q {_f(x - s * 0.4)} {_f(y + s * 0.85)} {_f(x - s * 0.9)} {_f(y + s * 0.45)} Z" for x, y, s in spots),
               noise(0.7, seed + 2, (0.35, darken(moss, 0.3)), (0.65, lighten(moss, 0.2)), octaves=2), alpha=0.85, blur=0.2)


def pebbles(r: Recipe, x0: float, y0: float, n: int, base: str, seed: int, size: tuple[float, float] = (0.5, 1.3), margin: float = 2.5) -> None:
    stones(r, [(x, y, r.rng.uniform(*size)) for x, y in inside(r, x0, y0, n, margin)], base, seed)


def gravel(r: Recipe, x0: float, y0: float, n: int, tones: tuple[str, str], margin: float = 1.0) -> None:
    """Tiny grains of grit: one dark and one light batch of dots."""
    for tone, k in ((tones[0], n), (tones[1], n // 2)):
        d = []
        for x, y in inside(r, x0, y0, k, margin):
            s = r.rng.uniform(0.18, 0.42)
            d.append(f"M {_f(x - s)} {_f(y)} Q {_f(x - s)} {_f(y - s * 0.8)} {_f(x)} {_f(y - s * 0.8)} Q {_f(x + s)} {_f(y - s * 0.8)} {_f(x + s)} {_f(y)} "
                     f"Q {_f(x + s)} {_f(y + s * 0.8)} {_f(x)} {_f(y + s * 0.8)} Q {_f(x - s)} {_f(y + s * 0.8)} {_f(x - s)} {_f(y)} Z")
        if d:
            r.path(" ".join(d), tone, alpha=0.75)


def flowers(r: Recipe, x0: float, y0: float, n: int, colors: list[str], size: tuple[float, float] = (0.6, 1.0), margin: float = 4.0) -> None:
    """Small wild flowers: stems, petals in batches by color, a warm heart, a soft shadow."""
    spots = [(x, y, r.rng.uniform(*size), r.rng.choice(colors)) for x, y in inside(r, x0, y0, n, margin)]
    if not spots:
        return
    r.path(" ".join(f"M {_f(x - 0.18)} {_f(y)} L {_f(x + 0.18)} {_f(y)} L {_f(x + 0.3)} {_f(y + 2.2 * s)} L {_f(x - 0.1)} {_f(y + 2.2 * s)} Z" for x, y, s, _ in spots), "#3A5A28")
    r.path(" ".join(f"M {_f(x - 1.4 * s)} {_f(y + 0.9)} Q {_f(x)} {_f(y + 0.2)} {_f(x + 1.6 * s)} {_f(y + 1.1)} Q {_f(x)} {_f(y + 1.9)} {_f(x - 1.4 * s)} {_f(y + 0.9)} Z"
                    for x, y, s, _ in spots), AO, alpha=0.45, blend="multiply", blur=0.5)
    by_color: dict[str, list[str]] = {}
    for x, y, s, c in spots:
        d = by_color.setdefault(c, [])
        for k in range(5):
            a = k * 2 * math.pi / 5 - 0.5
            px, py = x + math.cos(a) * 0.75 * s, y + math.sin(a) * 0.62 * s
            rx, ry = 0.62 * s, 0.48 * s
            d.append(f"M {_f(px - rx)} {_f(py)} Q {_f(px - rx)} {_f(py - ry)} {_f(px)} {_f(py - ry)} Q {_f(px + rx)} {_f(py - ry)} {_f(px + rx)} {_f(py)} "
                     f"Q {_f(px + rx)} {_f(py + ry)} {_f(px)} {_f(py + ry)} Q {_f(px - rx)} {_f(py + ry)} {_f(px - rx)} {_f(py)} Z")
    for c, d in by_color.items():
        r.path(" ".join(d), c)
    r.path(" ".join(f"M {_f(x - 0.4 * s)} {_f(y + 0.25 * s)} Q {_f(x)} {_f(y + 0.75 * s)} {_f(x + 0.55 * s)} {_f(y + 0.1 * s)} Q {_f(x + 0.6 * s)} {_f(y + 0.75 * s)} "
                    f"{_f(x)} {_f(y + 0.85 * s)} Q {_f(x - 0.6 * s)} {_f(y + 0.7 * s)} {_f(x - 0.4 * s)} {_f(y + 0.25 * s)} Z" for x, y, s, _ in spots),
           "#4A3060", alpha=0.35, blend="multiply", blur=0.15)
    r.path(" ".join(f"M {_f(x - 0.36 * s)} {_f(y)} Q {_f(x)} {_f(y - 0.4 * s)} {_f(x + 0.36 * s)} {_f(y)} Q {_f(x)} {_f(y + 0.4 * s)} {_f(x - 0.36 * s)} {_f(y)} Z"
                    for x, y, s, _ in spots), "#E8B83A")


def leaves(r: Recipe, x0: float, y0: float, n: int, colors: list[str], size: tuple[float, float] = (1.0, 2.0), margin: float = 2.5) -> None:
    """Fallen leaves in batches by color, each with a soft shadow and a midrib."""
    spots = []
    for x, y in inside(r, x0, y0, n, margin):
        a = r.rng.uniform(0, math.pi)
        s = r.rng.uniform(*size)
        spots.append((x, y, math.cos(a) * s, math.sin(a) * s, r.rng.choice(colors)))

    def shape(x, y, dx, dy, k=1.0, ox=0.0, oy=0.0):
        nx, ny = -dy * 0.5 * k, dx * 0.5 * k
        x, y = x + ox, y + oy
        return (f"M {_f(x - dx)} {_f(y - dy)} Q {_f(x + nx)} {_f(y + ny)} {_f(x + dx)} {_f(y + dy)} "
                f"Q {_f(x - nx)} {_f(y - ny)} {_f(x - dx)} {_f(y - dy)} Z")

    r.path(" ".join(shape(x, y, dx, dy, 1.1, 0.35, 0.45) for x, y, dx, dy, _ in spots), AO, alpha=0.5, blend="multiply", blur=0.45)
    by_color: dict[str, list[str]] = {}
    for x, y, dx, dy, c in spots:
        by_color.setdefault(c, []).append(shape(x, y, dx, dy))
    for c, d in by_color.items():
        r.path(" ".join(d), noise(0.8, 7, (0.35, darken(c, 0.18)), (0.65, lighten(c, 0.12)), octaves=2))
    r.path(" ".join(f"M {_f(x - dx)} {_f(y - dy)} L {_f(x + dx)} {_f(y + dy)}" for x, y, dx, dy, _ in spots), None, stroke="#2A1A0C", width=0.16, alpha=0.5)


def sparkles(r: Recipe, x0: float, y0: float, n: int, size: tuple[float, float] = (0.25, 0.45), alpha: float = 0.8, margin: float = 3.0) -> None:
    """Small glints of light (snow, sand, water): a soft halo and a bright point, added."""
    spots = [(x, y, r.rng.uniform(*size)) for x, y in inside(r, x0, y0, n, margin)]
    if not spots:
        return
    r.path(" ".join(f"M {_f(x - s * 3)} {_f(y)} Q {_f(x)} {_f(y - s * 2)} {_f(x + s * 3)} {_f(y)} Q {_f(x)} {_f(y + s * 2)} {_f(x - s * 3)} {_f(y)} Z" for x, y, s in spots),
           "#FFFFFF", alpha=alpha * 0.35, blend="add", blur=0.6)
    r.path(" ".join(f"M {_f(x)} {_f(y - s * 1.6)} L {_f(x + s * 0.3)} {_f(y - s * 0.3)} L {_f(x + s * 1.6)} {_f(y)} L {_f(x + s * 0.3)} {_f(y + s * 0.3)} "
                    f"L {_f(x)} {_f(y + s * 1.6)} L {_f(x - s * 0.3)} {_f(y + s * 0.3)} L {_f(x - s * 1.6)} {_f(y)} L {_f(x - s * 0.3)} {_f(y - s * 0.3)} Z" for x, y, s in spots),
           "#FFFFFF", alpha=alpha, blend="add")


# ------------------------------------------------------------------------------------------------ grounds
GRASS = ("#30562A", "#4F7C36", "#86AA54")
BLADES = ("#2E5626", "#5C8C3A", "#9ABE62")


def grass(name: str, tones=GRASS, seed: int = 11, flowers_of=None, clover=False, mushrooms=False, dry=False, pebbles_n: int = 0,
          clumps_n: int = 3, blades=BLADES) -> Recipe:
    r = macro(name, tones[1])
    ground(r, seed, *tones, streak=(1.0, 4.0), texture=0.6, tips="#E8F4B0", tips_alpha=0.2)
    light_and_shade(r, seed + 20)
    for x0, y0 in tiles_of(r):
        if dry:
            for x, y in inside(r, x0, y0, 2, 8):
                r.ellipse(x, y, r.rng.uniform(4, 7), r.rng.uniform(2.5, 4), nz(r, 2, seed + 30, (0.35, "#B8A858"), (0.65, "#D8C880"), scale_y=4.0), alpha=0.35, blur=2.2)
        field_blades(r, x0, y0, 34, (darken(blades[0], 0.1), blades[1], lighten(blades[1], 0.15)))
        if clover:
            d = []
            for x, y in inside(r, x0, y0, 2, 6):
                for k in range(3):
                    a = k * 2.1 + r.rng.uniform(0, 1)
                    cx, cy = x + math.cos(a) * 1.3, y + math.sin(a) * 1.1
                    d.append(f"M {_f(cx - 1.2)} {_f(cy)} Q {_f(cx - 1.2)} {_f(cy - 1)} {_f(cx)} {_f(cy - 1)} Q {_f(cx + 1.2)} {_f(cy - 1)} {_f(cx + 1.2)} {_f(cy)} "
                             f"Q {_f(cx + 1.2)} {_f(cy + 1)} {_f(cx)} {_f(cy + 1)} Q {_f(cx - 1.2)} {_f(cy + 1)} {_f(cx - 1.2)} {_f(cy)} Z")
            if d:
                r.path(" ".join(d), noise(0.8, seed + 5, (0.35, "#2E6030"), (0.65, "#5E9A48"), octaves=2))
        clumps(r, x0, y0, clumps_n, blades)
        if pebbles_n:
            pebbles(r, x0, y0, pebbles_n, "#8E8C88", seed + 40)
        if flowers_of:
            flowers(r, x0, y0, 3, flowers_of)
        if mushrooms and r.rng.random() < 0.3:  # a few rings of mushrooms in a meadow, not one in every tile
            x, y = inside(r, x0, y0, 1, 9)[0]
            for (dx, dy, s) in ((0, 0, 1.0), (4.5, 2.5, 0.75), (-3.5, 3, 0.6)):
                mx, my = x + dx, y + dy
                r.ellipse(mx + 0.6, my + 3 * s, 3 * s, 1.1 * s, AO, alpha=0.5, blend="multiply", blur=0.7)
                r.rect(mx - 0.8 * s, my, 1.6 * s, 3 * s, linear(mx - s, my, mx + s, my, (0, "#F4EAD8"), (1, "#B8A68A")))
                r.path(f"M {_f(mx - 3.2 * s)} {_f(my + 0.6 * s)} Q {_f(mx - 2.6 * s)} {_f(my - 2.6 * s)} {_f(mx)} {_f(my - 2.6 * s)} Q {_f(mx + 2.6 * s)} {_f(my - 2.6 * s)} "
                       f"{_f(mx + 3.2 * s)} {_f(my + 0.6 * s)} Q {_f(mx)} {_f(my + 1.5 * s)} {_f(mx - 3.2 * s)} {_f(my + 0.6 * s)} Z",
                       radial(mx - s, my - 1.6 * s, 4.5 * s, (0, "#D86A4E"), (0.6, "#A8382C"), (1, "#6A1C20")))
                r.ellipse(mx - 1.1 * s, my - 1.2 * s, 0.55 * s, 0.4 * s, "#F2EAE0", alpha=0.85)
                r.ellipse(mx + 1.0 * s, my - 0.5 * s, 0.42 * s, 0.32 * s, "#F2EAE0", alpha=0.85)
    return r


def forest_floor() -> Recipe:
    r = macro("forest_floor", "#3E4A26")
    ground(r, 23, "#2A2E1A", "#40482A", "#5E6436", streak=(1.0, 1.6), texture=0.6, tips="#E0D8A0", tips_alpha=0.14, patches=0.32)
    r.rect(0, 0, MACRO, MACRO, nz(r, 16, 25, (0.42, "#3A6A2E00"), (0.62, "#46702F")), alpha=0.4)  # green undergrowth in patches
    light_and_shade(r, 27, 0.18)  # dappled light through the leaves
    for x0, y0 in tiles_of(r):
        leaves(r, x0, y0, 16, ["#7A4A22", "#9A6430", "#6A4020", "#A8782E", "#5A3A1E"], (0.8, 1.6))
        field_blades(r, x0, y0, 10, ("#2E4A22", "#4E6E30"))
        clumps(r, x0, y0, 1, ("#2A4A22", "#44682E", "#76984C"), h=(2.5, 4.5), blades=6)
        if r.rng.random() < 0.5:
            pebbles(r, x0, y0, 1, "#6E6A60", 29, (0.7, 1.2))
        if r.rng.random() < 0.35:  # a fallen twig
            x, y = inside(r, x0, y0, 1, 8)[0]
            r.path(f"M {_f(x - 4)} {_f(y + 1.9)} L {_f(x + 4)} {_f(y - 1.1)}", None, stroke=AO, width=1.2, alpha=0.4, blend="multiply", blur=0.4)
            r.path(f"M {_f(x - 4)} {_f(y + 1.5)} L {_f(x + 4)} {_f(y - 1.5)} M {_f(x)} {_f(y)} L {_f(x + 2)} {_f(y + 2)}", None, stroke="#4A3420", width=0.7)
            r.path(f"M {_f(x - 4)} {_f(y + 1.25)} L {_f(x + 4)} {_f(y - 1.75)}", None, stroke="#8A6A48", width=0.22, alpha=0.8)
    return r


def moss(name: str, seed: int, mushrooms: bool) -> Recipe:
    r = macro(name, "#2F5A34")
    ground(r, seed, "#17321E", "#2C5432", "#4E7E44", streak=(0.8, 0.8), texture=0.65, tips="#C8F0A0", tips_alpha=0.22)
    light_and_shade(r, seed + 20, 0.22)
    for x0, y0 in tiles_of(r):
        spots = [(x, y, r.rng.uniform(1.8, 3.4)) for x, y in inside(r, x0, y0, 4, 4)]  # cushions of moss
        r.path(" ".join(f"M {_f(x - s * 1.25)} {_f(y + 0.6)} Q {_f(x)} {_f(y - s * 0.4)} {_f(x + s * 1.25)} {_f(y + 0.6)} Q {_f(x)} {_f(y + s)} {_f(x - s * 1.25)} {_f(y + 0.6)} Z"
                        for x, y, s in spots), AO, alpha=0.55, blend="multiply", blur=0.8)
        r.path(" ".join(f"M {_f(x - s * 1.15)} {_f(y)} Q {_f(x - s * 1.1)} {_f(y - s * 0.8)} {_f(x)} {_f(y - s * 0.78)} Q {_f(x + s * 1.1)} {_f(y - s * 0.8)} {_f(x + s * 1.15)} {_f(y)} "
                        f"Q {_f(x + s)} {_f(y + s * 0.7)} {_f(x)} {_f(y + s * 0.72)} Q {_f(x - s)} {_f(y + s * 0.7)} {_f(x - s * 1.15)} {_f(y)} Z" for x, y, s in spots),
               noise(0.6, seed + 3, (0.3, "#1E4426"), (0.5, "#33643A"), (0.72, "#5A8E48"), octaves=3), alpha=0.9)
        r.path(" ".join(f"M {_f(x - s * 0.8)} {_f(y - s * 0.2)} Q {_f(x - s * 0.4)} {_f(y - s * 0.75)} {_f(x + s * 0.4)} {_f(y - s * 0.6)} Q {_f(x)} {_f(y - s * 0.2)} {_f(x - s * 0.8)} {_f(y - s * 0.2)} Z"
                        for x, y, s in spots), "#D8F8A0", alpha=0.14, blend="add", blur=0.7)
        field_blades(r, x0, y0, 12, ("#1E4426", "#3E6E3A"), (1.4, 2.8))
        if mushrooms and r.rng.random() < 0.6:
            x, y = inside(r, x0, y0, 1, 7)[0]
            r.ellipse(x + 0.5, y + 2.6, 2.4, 0.9, AO, alpha=0.5, blend="multiply", blur=0.5)
            r.rect(x - 0.6, y, 1.2, 2.6, linear(x - 0.6, 0, x + 0.6, 0, (0, "#ECE4EE"), (1, "#A89AB0")))
            r.ellipse(x, y, 2.6, 1.8, radial(x - 0.8, y - 0.8, 3.4, (0, "#D0A8F0"), (0.6, "#8A5AC0"), (1, "#4A2A7A")))
            r.ellipse(x - 0.8, y - 0.6, 0.6, 0.4, "#FFFFFF", alpha=0.7)
            r.glow(x, y, 4, "#B080FF", 0.25)
    return r


def dirt(name: str, tones, seed: int, ruts: bool = False, pebbles_n: int = 2) -> Recipe:
    r = macro(name, tones[1])
    ground(r, seed, *tones, streak=(0.8, 0.8), texture=0.5, tips="#FFF0D0", tips_alpha=0.14, patches=0.5)
    r.rect(0, 0, MACRO, MACRO, nz(r, 8, seed + 9, (0.6, "#FFFFFF"), (0.8, darken(tones[0], 0.3)), octaves=2, ridged=True), blend="multiply", alpha=0.35)  # dry cracks
    light_and_shade(r, seed + 20, 0.12)
    if ruts:  # the tracks of the carts: two soft grooves along every tile, lit on their far edge
        for cy in range(SPAN):
            for off in (9, 22):
                y = cy * TILE + off
                r.rect(0, y - 1.6, MACRO, 2.8, darken(tones[0], 0.2), alpha=0.28, blend="multiply", blur=1.4)
                r.rect(0, y + 1.3, MACRO, 0.7, LIGHT, alpha=0.1, blend="add", blur=0.6)
    for x0, y0 in tiles_of(r):
        gravel(r, x0, y0, 26, (darken(tones[0], 0.3), lighten(tones[2], 0.2)))
        pebbles(r, x0, y0, pebbles_n + r.rng.randrange(2), mix(tones[1], "#8A8682", 0.6), seed + 40)
        if r.rng.random() < 0.4:
            clumps(r, x0, y0, 1, ("#3E5A2C", "#5E7E3A", "#8CA65A"), h=(2.0, 3.4), blades=5, margin=4)
    return r


def sand(name: str = "sand") -> Recipe:
    r = macro(name, "#D8C092")
    ground(r, 41, "#B89E70", "#D8C092", "#EEDCB0", streak=(0.8, 0.8), texture=0.4, tips="#FFFFFF", tips_alpha=0.2, grain=0.35)
    # ripples left by the wind: stretched creases, dark on their lee side and lit on their crest
    r.rect(0, 0, MACRO, MACRO, nz(r, 8, 43, (0.7, "#FFFFFF"), (0.95, "#A08660"), octaves=3, scale_y=2, ridged=True), blend="multiply", alpha=0.32)
    r.rect(0, 0, MACRO, MACRO, nz(r, 8, 44, (0.76, "#000000"), (0.97, "#FFF6E0"), octaves=3, scale_y=2, ridged=True), blend="add", alpha=0.14)
    light_and_shade(r, 47, 0.1)
    for x0, y0 in tiles_of(r):
        gravel(r, x0, y0, 14, ("#A08A64", "#F8ECCC"))
        if r.rng.random() < 0.45:
            pebbles(r, x0, y0, 1, "#C8B898", 49, (0.5, 1.0))
        sparkles(r, x0, y0, 2, (0.2, 0.32), 0.6)
    return r


def coast(name: str, seed: int) -> Recipe:
    r = macro(name, "#6A8E4C")
    ground(r, 11, "#3E6A34", "#668E46", "#9CB868", streak=(1.0, 4.0), texture=0.55, tips="#F0F4B8", tips_alpha=0.18)
    light_and_shade(r, 31)
    for x0, y0 in tiles_of(r):
        for x, y in inside(r, x0, y0, 2, 8):  # sand showing through the grass
            rx, ry = r.rng.uniform(4, 6.5), r.rng.uniform(2.6, 4)
            r.ellipse(x, y, rx, ry, nz(r, 1, seed, (0.3, "#C8B080"), (0.7, "#EADCB0"), octaves=2), blur=1.3)
            r.ellipse(x + 0.6, y + 0.8, rx * 0.9, ry * 0.7, AO, alpha=0.18, blend="multiply", blur=1.2)
        field_blades(r, x0, y0, 22, ("#3A6430", "#62903E", "#A4C070"))
        clumps(r, x0, y0, 2, ("#3A6630", "#6A9A44", "#B4D07C"), h=(3.0, 5.0))
        if r.rng.random() < 0.5:
            flowers(r, x0, y0, 1, ["#F4F2EA"], (0.6, 0.8))
        else:  # a shell
            x, y = inside(r, x0, y0, 1, 5)[0]
            r.ellipse(x + 0.3, y + 0.5, 1.4, 0.8, AO, alpha=0.5, blend="multiply", blur=0.35)
            r.ellipse(x, y, 1.3, 0.9, radial(x - 0.4, y - 0.3, 1.6, (0, "#FFF8F0"), (1, "#D8B8A4")))
            r.path(f"M {_f(x - 0.9)} {_f(y)} L {_f(x)} {_f(y - 0.8)} L {_f(x + 0.9)} {_f(y)} M {_f(x)} {_f(y - 0.8)} L {_f(x)} {_f(y + 0.8)}", None, stroke="#A88470", width=0.12, alpha=0.6)
    return r


def rocky(name: str, seed: int, boulders: int) -> Recipe:
    r = macro(name, "#6E8460")
    ground(r, 53, "#46603E", "#6A8258", "#9AAE7A", streak=(1.0, 3.2), texture=0.55, tips="#F0F0C0", tips_alpha=0.16)
    light_and_shade(r, 57)
    for x0, y0 in tiles_of(r):
        field_blades(r, x0, y0, 20, ("#3E5A34", "#64824A", "#98B070"))
        spots = [(x, y, r.rng.uniform(3.0, 4.8)) for x, y in inside(r, x0, y0, boulders, 8)]
        stones(r, spots, "#8E8E8A", seed, moss="#5E8A40", flat=0.68)
        pebbles(r, x0, y0, 2, "#94928E", seed + 2)
        clumps(r, x0, y0, 2, ("#405E36", "#6A8A4C", "#A4BC7A"), h=(2.6, 4.4), blades=6)
    return r


def savanna(name: str, seed: int, crack: bool) -> Recipe:
    r = macro(name, "#B8A45E")
    ground(r, 61, "#8A7638", "#B4A05A", "#D8C688", streak=(1.0, 4.0), texture=0.55, tips="#FFF6C8", tips_alpha=0.24)
    light_and_shade(r, 63, 0.12)
    for x0, y0 in tiles_of(r):
        field_blades(r, x0, y0, 30, ("#8A7432", "#B8A058", "#E2D294"), (2.0, 4.2))
        clumps(r, x0, y0, 4, ("#8A7430", "#C4AE62", "#EEE0A6"), h=(4.0, 7.0), blades=9)
        clumps(r, x0, y0, 1, ("#5E6E30", "#7E8E44", "#B0BC74"), h=(3.0, 4.5), blades=6)
        if r.rng.random() < 0.5:
            pebbles(r, x0, y0, 1, "#A89A7A", seed + 3)
        if crack and r.rng.random() < 0.4:
            x, y = inside(r, x0, y0, 1, 9)[0]
            d = f"M {_f(x - 6)} {_f(y + 2)} L {_f(x - 2)} {_f(y - 1)} L {_f(x + 1)} {_f(y + 1)} L {_f(x + 6)} {_f(y - 3)}"
            r.path(d, None, stroke="#3A2E14", width=0.8, alpha=0.55, blend="multiply", blur=0.2)
            r.path(d.replace(f"M {_f(x - 6)} {_f(y + 2)}", f"M {_f(x - 6)} {_f(y + 2.5)}"), None, stroke="#FFF0C0", width=0.25, alpha=0.3, blend="add")
    return r


def snowfield(name: str, tones, seed: int, crystals: bool = False, tufts: bool = False) -> Recipe:
    r = macro(name, tones[1])
    ground(r, seed, *tones, streak=(2.0, 1.0), texture=0.22, tips="#FFFFFF", tips_alpha=0.3, grain=0.12, patches=0.5)
    r.rect(0, 0, MACRO, MACRO, nz(r, 16, seed + 9, (0.35, "#6A84B8"), (0.55, "#FFFFFF"), octaves=3), blend="multiply", alpha=0.3)  # the blue of its shade
    for x0, y0 in tiles_of(r):
        for x, y in inside(r, x0, y0, 2, 7):  # drifts: a bluish shade under a bright crest
            rx, ry = r.rng.uniform(5, 8), r.rng.uniform(2, 3.2)
            r.ellipse(x + 1, y + 1.6, rx, ry, "#7088C0", alpha=0.35, blend="multiply", blur=1.5)
            r.ellipse(x - 0.5, y - 0.6, rx * 0.9, ry * 0.8, "#FFFFFF", alpha=0.7, blur=1.1)
        sparkles(r, x0, y0, 4, (0.25, 0.45), 0.85)
        if crystals and r.rng.random() < 0.7:
            x, y = inside(r, x0, y0, 1, 6)[0]
            s = r.rng.uniform(1.6, 2.8)
            r.ellipse(x + 0.5, y + s, s * 0.9, s * 0.3, "#203060", alpha=0.4, blend="multiply", blur=0.5)
            r.poly([(x, y - s), (x + s * 0.55, y), (x, y + s), (x - s * 0.55, y)], linear(x - s, y - s, x + s, y + s, (0, "#FFFFFF"), (0.5, "#BFE4FF"), (1, "#5A90C8")))
            r.poly([(x, y - s), (x + s * 0.55, y), (x, y)], "#FFFFFF", alpha=0.55)
            r.glow(x, y, s * 1.6, "#A0E0FF", 0.22)
        if tufts:
            clumps(r, x0, y0, 2, ("#5E7468", "#8EA49A", "#C8D8D0"), h=(2.4, 4.0), blades=5)
    return r


def ash(name: str, tones, seed: int, embers: int, cracks: int) -> Recipe:
    r = macro(name, tones[1])
    ground(r, 71, *tones, streak=(0.8, 0.8), texture=0.55, tips="#C8C0B8", tips_alpha=0.1, grain=0.4)
    r.rect(0, 0, MACRO, MACRO, nz(r, 16, seed + 9, (0.78, "#000000"), (0.95, "#FF5A18"), octaves=2, ridged=True), blend="add", alpha=0.22 * cracks)  # embers under the crust
    for x0, y0 in tiles_of(r):
        for x, y in inside(r, x0, y0, 2, 6):  # drifts of pale ash
            r.ellipse(x, y, r.rng.uniform(4, 7), r.rng.uniform(1.6, 2.8), lighten(tones[2], 0.2), alpha=0.35, blur=1.3)
        gravel(r, x0, y0, 18, ("#141216", "#7A7478"))
        if cracks and r.rng.random() < 0.5:
            x, y = inside(r, x0, y0, 1, 7)[0]
            pts = [(x - 5, y)]
            for _ in range(4):
                px, py = pts[-1]
                pts.append((px + r.rng.uniform(1.5, 3.2), min(max(py + r.rng.uniform(-2.5, 2.5), y - 5), y + 5)))
            d = "M " + " L ".join(f"{_f(px)} {_f(py)}" for px, py in pts)
            r.path(d, None, stroke="#FF5A1E", width=2.4, alpha=0.3, blend="add", blur=1.0)
            r.path(d, None, stroke="#100A08", width=1.0, alpha=0.9)
            r.path(d, None, stroke="#FFA050", width=0.35, alpha=0.9)
        for x, y in inside(r, x0, y0, embers if r.rng.random() < 0.6 else 0, 4):
            r.glow(x, y, 3.0, "#FF6A20", 0.4)
            r.ellipse(x, y, 0.55, 0.5, "#FFD080")
        pebbles(r, x0, y0, 1, "#4E4A4E", seed + 3, (0.6, 1.2))
    return r


# ------------------------------------------------------------------------------------------------ water
def water() -> Recipe:
    r = macro("water", "#245672", {"deep": "#163A52", "wave": "#CFE6F2"})
    r.rect(0, 0, MACRO, MACRO, nz(r, 32, 81, (0.3, "#14344C"), (0.5, "#235470"), (0.72, "#3A7896"), octaves=4))
    r.rect(0, 0, MACRO, MACRO, nz(r, 16, 82, (0.35, "#0E2840"), (0.5, "#23547000"), (0.66, "#4A8AA6")), alpha=0.45)
    # the ripples: long thin creases across the wind, shaded on one side and lit on the other
    r.rect(0, 0, MACRO, MACRO, nz(r, 4, 83, (0.62, "#FFFFFF"), (0.9, "#1A3E5A"), octaves=3, scale_y=1, ridged=True), blend="multiply", alpha=0.45)
    r.rect(0, 0, MACRO, MACRO, nz(r, 4, 84, (0.72, "#000000"), (0.95, "#BFE0F0"), octaves=3, scale_y=1, ridged=True), blend="add", alpha=0.32)
    r.rect(0, 0, MACRO, MACRO, nz(r, 4, 85, (0.8, "#000000"), (0.96, "#8CC8E0"), octaves=2, ridged=True), blend="add", alpha=0.25)  # light deep down
    light_and_shade(r, 86, 0.14)
    for x0, y0 in tiles_of(r):
        sparkles(r, x0, y0, 2, (0.3, 0.6), 0.85, 5)
    return r


def shallows() -> Recipe:
    r = macro("shallows", "#4E98AC", {"sand": "#E8D9A6"})
    r.rect(0, 0, MACRO, MACRO, nz(r, 32, 91, (0.3, "#35768A"), (0.5, "#4A90A0"), (0.7, "#6EAAB2"), octaves=4))
    r.rect(0, 0, MACRO, MACRO, nz(r, 16, 93, (0.45, "#D8C89A00"), (0.66, "#D8CCA0"), octaves=3), alpha=0.5)  # the sand under the water
    r.rect(0, 0, MACRO, MACRO, nz(r, 2, 94, (0.3, "#6A7A70"), (0.6, "#FFFFFF"), octaves=2), blend="multiply", alpha=0.25)  # grains on the bottom
    # the net of light on the bottom (caustics): ridged creases, added, at two sizes
    r.rect(0, 0, MACRO, MACRO, nz(r, 8, 95, (0.8, "#000000"), (0.97, "#E8FAF4"), octaves=2, ridged=True), blend="add", alpha=0.3)
    r.rect(0, 0, MACRO, MACRO, nz(r, 4, 96, (0.82, "#000000"), (0.97, "#E0F8F0"), octaves=2, ridged=True), blend="add", alpha=0.18)
    r.rect(0, 0, MACRO, MACRO, nz(r, 8, 97, (0.66, "#FFFFFF"), (0.9, "#2A6A84"), octaves=2, scale_y=1, ridged=True), blend="multiply", alpha=0.3)
    for x0, y0 in tiles_of(r):
        if r.rng.random() < 0.4:
            pebbles(r, x0, y0, 1, "#9A9C90", 98, (0.6, 1.0))
        sparkles(r, x0, y0, 2, (0.25, 0.5), 0.85, 5)
    return r


# ------------------------------------------------------------------------------------------------ rock and buildings
def mountain() -> Recipe:
    r = Recipe("base:art/tile/mountain", 64, 64, (0, 0), {"rock": "#6E6A6A", "snow": "#F6FAFF"}, seed="v4")
    r.rect(0, 0, 64, 64, nz(r, 16, 101, (0.3, "#3E3A3C"), (0.5, "#5E5A5A"), (0.7, "#86827E"), octaves=4))
    r.rect(0, 0, 64, 64, nz(r, 4, 102, (0.7, "#FFFFFF"), (0.92, "#2A2628"), octaves=3, ridged=True), blend="multiply", alpha=0.5)
    peaks = [(14, 30, 4, 12), (46, 28, 3, 13), (30, 46, 14, 14), (10, 62, 36, 9), (52, 60, 34, 10), (32, 20, 2, 8)]
    for cx, base_y, top_y, half in sorted(peaks, key=lambda p: p[1]):
        mid_y = (base_y + top_y) / 2
        r.ellipse(cx + 3, base_y, half * 1.15, 2.8, AO, alpha=0.6, blend="multiply", blur=1.4)
        body = f"M {cx - half} {base_y} L {_f(cx - half * 0.45)} {_f(mid_y + 1)} L {cx} {top_y} L {_f(cx + half * 0.5)} {_f(mid_y)} L {cx + half} {base_y} Z"
        r.path(body, noise(3, 103 + cx, (0.3, "#5A5654"), (0.5, "#7A7672"), (0.7, "#A09A94"), octaves=4))
        r.path(body, noise(2, 104 + cx, (0.66, "#FFFFFF"), (0.9, "#2E2A2C"), octaves=3, scale_y=4, ridged=True), blend="multiply", alpha=0.55)  # the cracks
        r.path(f"M {cx} {top_y} L {_f(cx + half * 0.5)} {_f(mid_y)} L {cx + half} {base_y} L {_f(cx + half * 0.15)} {base_y} L {_f(cx + half * 0.2)} {_f(mid_y + 2)} Z",
               "#3A3458", alpha=0.55, blend="multiply", blur=0.8)
        r.path(f"M {cx} {top_y} L {_f(cx - half * 0.45)} {_f(mid_y + 1)} L {_f(cx - half * 0.2)} {_f(mid_y + 1)} Z", LIGHT, alpha=0.3, blend="add", blur=0.6)
        h = (base_y - top_y) * 0.38
        snow = (f"M {cx} {top_y} L {_f(cx + half * 0.32)} {_f(top_y + h)} L {_f(cx + half * 0.12)} {_f(top_y + h * 0.8)} L {cx} {_f(top_y + h * 1.25)} "
                f"L {_f(cx - half * 0.14)} {_f(top_y + h * 0.8)} L {_f(cx - half * 0.3)} {_f(top_y + h)} Z")
        r.path(snow, linear(cx - half, 0, cx + half, 0, (0, "#FFFFFF"), (0.5, "#E4ECF6"), (1, "#9AAAC8")), blur=0.25)
        r.path(snow, noise(1, 105 + cx, (0.3, "#A8B4CC"), (0.6, "#FFFFFF"), octaves=2), blend="multiply", alpha=0.5)
    for x, y, s in ((6, 8, 1.3), (24, 34, 1.1), (58, 44, 1.4), (40, 62, 1.2), (22, 60, 1.0)):
        stones(r, [(x, y, s)], "#7E7A76", 106)
    return r


def cobble() -> Recipe:
    r = small("cobble", {"base": "#6A6A70"})
    r.rect(0, 0, TILE, TILE, nz(r, 8, 111, (0.3, "#2E2C30"), (0.7, "#4A4848"), octaves=2))  # the earth in the joints
    r.rect(0, 0, TILE, TILE, nz(r, 0.5, 112, (0.3, "#202020"), (0.7, "#5A5650"), octaves=1), alpha=0.5)
    cobbles = [(7, 7, 6.2, 5.0), (22, 6, 6.6, 4.6), (8, 21, 6.4, 5.4), (23, 22, 6.2, 5.2), (15, 14.5, 5.0, 4.0), (31, 14, 3.4, 4.0), (-1, 14, 3.4, 4.0),
               (15, 30, 3.0, 2.2), (15, -1, 3.0, 2.2)]
    for i, (x, y, rx, ry) in enumerate(cobbles):
        c = ["#8C8A90", "#7E7C84", "#9A9698", "#86847C"][i % 4]
        d = (f"M {_f(x - rx)} {_f(y)} Q {_f(x - rx)} {_f(y - ry)} {_f(x)} {_f(y - ry)} Q {_f(x + rx)} {_f(y - ry)} {_f(x + rx)} {_f(y)} "
             f"Q {_f(x + rx)} {_f(y + ry)} {_f(x)} {_f(y + ry)} Q {_f(x - rx)} {_f(y + ry)} {_f(x - rx)} {_f(y)} Z")
        r.ellipse(x + 0.5, y + 0.8, rx * 1.02, ry * 1.02, "#100C10", alpha=0.6, blur=0.7)  # the shade in the joint
        r.path(d, noise(1.5, 113 + i, (0.3, darken(c, 0.2)), (0.5, c), (0.7, lighten(c, 0.15)), octaves=3))
        r.path(d, radial(x - rx * 0.35, y - ry * 0.45, max(rx, ry) * 1.5, (0, "#FFFFFF"), (0.45, "#FFFFFF"), (1, "#40384E")), blend="multiply", alpha=0.7)  # rounded and worn
        r.path(d, noise(1, 117 + i, (0.7, "#FFFFFF"), (0.92, "#3A3434"), octaves=2, ridged=True), blend="multiply", alpha=0.35)
        r.ellipse(x - rx * 0.3, y - ry * 0.38, rx * 0.5, ry * 0.32, LIGHT, alpha=0.3, blend="add", blur=0.8)
    for x, y in ((15, 3.5), (2, 28), (29, 29), (30, 4)):
        r.ellipse(x, y, 1.3, 0.8, noise(0.5, 119, (0.3, "#3E6A30"), (0.7, "#6E9A48"), octaves=2), alpha=0.85, blur=0.3)  # a bit of moss in the joints
    return r


def planks(r: Recipe, y0: float, rows: int, row_h: float, seed: int, tones=("#9A6C40", "#8C6036", "#A47648", "#946A3E")) -> None:
    """Rows of boards: the grain of the wood (stretched noise), a lit upper edge, a dark gap below, the joints and the nails."""
    for i in range(rows):
        y = y0 + i * row_h
        tone = tones[i % len(tones)]
        r.rect(0, y, TILE, row_h, noise(16, seed + i, (0.3, darken(tone, 0.2)), (0.5, tone), (0.7, lighten(tone, 0.14)), octaves=4, period=2, scale_y=0.5, period_y=64))
        r.rect(0, y, TILE, row_h, noise(8, seed + 50 + i, (0.7, "#FFFFFF"), (0.92, darken(tone, 0.5)), octaves=3, period=4, scale_y=0.6, ridged=True), blend="multiply", alpha=0.45)
        r.rect(0, y, TILE, 0.8, LIGHT, alpha=0.22, blend="add", blur=0.2)
        r.rect(0, y + row_h - 0.9, TILE, 0.9, "#1A0E06", alpha=0.75)
        r.rect(0, y + row_h - 2.2, TILE, 1.4, "#3A2A40", alpha=0.25, blend="multiply", blur=0.5)
        joint = 8 + (i * 13) % 18
        r.rect(joint - 0.1, y, 0.65, row_h, "#1A0E06", alpha=0.8)
        r.rect(joint + 0.55, y, 0.5, row_h, LIGHT, alpha=0.12, blend="add")
        for nx in (joint - 1.6, joint + 2.2):
            r.ellipse(nx, y + row_h / 2, 0.42, 0.42, radial(nx - 0.15, y + row_h / 2 - 0.15, 0.5, (0, "#9A9AA4"), (1, "#2A2420")))


def plank_floor() -> Recipe:
    r = small("plank_floor", {"wood": "#9A6C40"})
    planks(r, 0, 4, 8, 121)
    r.rect(0, 0, TILE, TILE, nz(r, 0.5, 125, (0.3, "#8A8078"), (0.7, "#FFFFFF"), octaves=1), blend="multiply", alpha=0.25)
    return r


def bridge() -> Recipe:
    r = small("bridge", {"wood": "#8E6436", "water": "#245672"})
    r.rect(0, 0, TILE, TILE, nz(r, 8, 81, (0.3, "#14344C"), (0.7, "#3A7896"), octaves=2))
    r.rect(0, 1, TILE, 30, "#0A0A14", alpha=0.55, blur=1.0)
    planks(r, 2, 4, 7, 131, ("#8E6436", "#80582E", "#986C3C", "#865E34"))
    for y in (0.6, 28.6):  # the rails
        r.rect(0, y + 0.8, TILE, 2.8, AO, alpha=0.5, blend="multiply", blur=0.6)
        r.rect(0, y, TILE, 2.8, noise(16, 133, (0.3, "#5A3A1E"), (0.7, "#8A6038"), octaves=3, period=2, scale_y=0.4, period_y=80))
        r.rect(0, y, TILE, 2.8, linear(0, y, 0, y + 2.8, (0, "#FFFFFF"), (0.4, "#FFFFFF"), (1, "#40304A")), blend="multiply", alpha=0.6)
        r.rect(0, y, TILE, 0.6, LIGHT, alpha=0.25, blend="add", blur=0.2)
        for x in (4, 16, 28):
            r.rect(x - 1.3, y - 0.4, 2.6, 3.6, noise(1, 134 + x, (0.3, "#5A3A1E"), (0.7, "#8C643A"), octaves=2, scale_y=4))
            r.rect(x - 1.3, y - 0.4, 2.6, 3.6, linear(x - 1.3, 0, x + 1.3, 0, (0, "#FFFFFF"), (0.4, "#FFFFFF"), (1, "#3A2E44")), blend="multiply", alpha=0.6)
            r.ellipse(x, y + 1.2, 0.4, 0.4, "#2A2420")
    return r


def wall_stone() -> Recipe:
    r = small("wall_stone", {"base": "#7A7C80", "mortar": "#3C3A3A"})
    r.rect(0, 0, TILE, TILE, nz(r, 2, 140, (0.3, "#2A2828"), (0.7, "#4A4644"), octaves=2))
    rows = [(0, 8, 0), (8, 8, 7), (16, 8, 0), (24, 8, 7)]
    k = 0
    for ry, rh, off in rows:
        x = -off
        while x < TILE:
            bw = r.rng.choice([13, 15, 17])
            tone = mix("#6E7074", "#9A9894", r.rng.random())
            x0, x1 = max(x, 0) + 0.5, min(x + bw, TILE) - 0.5
            if x1 - x0 > 2:
                k += 1
                block = (f"M {_f(x0 + 0.5)} {_f(ry + 0.5)} L {_f(x1 - 0.4)} {_f(ry + 0.6)} L {_f(x1)} {_f(ry + 1.2)} L {_f(x1 - 0.2)} {_f(ry + rh - 1.0)} "
                         f"L {_f(x1 - 0.8)} {_f(ry + rh - 0.5)} L {_f(x0 + 0.4)} {_f(ry + rh - 0.6)} L {_f(x0)} {_f(ry + rh - 1.2)} L {_f(x0 + 0.1)} {_f(ry + 1.1)} Z")
                r.rect(x0 + 0.3, ry + 0.9, x1 - x0, rh - 0.6, "#0E0C0C", alpha=0.55, blur=0.5)
                r.path(block, noise(2, 141 + k, (0.3, darken(tone, 0.2)), (0.5, tone), (0.7, lighten(tone, 0.12)), octaves=4))
                r.path(block, noise(1.5, 151 + k, (0.68, "#FFFFFF"), (0.9, "#2E2A2A"), octaves=3, ridged=True), blend="multiply", alpha=0.45)
                r.path(block, linear(0, ry, 0, ry + rh, (0, "#FFFFFF"), (0.5, "#FFFFFF"), (1, "#3E3850")), blend="multiply", alpha=0.6)
                r.rect(x0 + 0.5, ry + 0.6, x1 - x0 - 1.2, 1.0, LIGHT, alpha=0.25, blend="add", blur=0.3)
            x += bw
    r.rect(0, 0, TILE, 5, linear(0, 0, 0, 5, (0, "#FFF6E4"), (1, "#FFF6E400")), alpha=0.3, blend="add")  # the lit top of the wall
    r.rect(0, 22, TILE, 10, linear(0, 22, 0, 32, (0, "#FFFFFF"), (1, "#2E2A44")), blend="multiply", alpha=0.6)  # the shade at the foot
    r.path("M 6 18 L 9 21.5 L 8 26", None, stroke="#1A1818", width=0.45, alpha=0.8)
    r.ellipse(26, 29.5, 4, 1.6, noise(0.6, 159, (0.3, "#3A5E2C"), (0.7, "#6A9044"), octaves=2), alpha=0.8, blur=0.5)
    return r


def _beam(r: Recipe, x, y, w, h, across: bool, seed: int) -> None:
    """A beam of old timber with its grain, rounded by the light from the top left."""
    if across:
        r.rect(x, y, w, h, noise(16, seed, (0.3, "#3A2414"), (0.5, "#5A3A22"), (0.7, "#7A5232"), octaves=4, period=2, scale_y=0.6, period_y=0))
        r.rect(x, y, w, h, noise(8, seed + 1, (0.7, "#FFFFFF"), (0.92, "#1A0E06"), octaves=3, scale_y=0.5, ridged=True), blend="multiply", alpha=0.5)
        r.rect(x, y, w, h, linear(x, y, x, y + h, (0, "#FFE8C8"), (0.3, "#FFFFFF"), (1, "#3A2E48")), blend="multiply", alpha=0.6)
        r.rect(x, y, w, 0.6, LIGHT, alpha=0.25, blend="add", blur=0.2)
    else:
        r.rect(x, y, w, h, noise(0.6, seed, (0.3, "#3A2414"), (0.5, "#5A3A22"), (0.7, "#7A5232"), octaves=4, scale_y=16))
        r.rect(x, y, w, h, noise(0.5, seed + 1, (0.7, "#FFFFFF"), (0.92, "#1A0E06"), octaves=3, scale_y=8, ridged=True), blend="multiply", alpha=0.5)
        r.rect(x, y, w, h, linear(x, y, x + w, y, (0, "#FFE8C8"), (0.3, "#FFFFFF"), (1, "#3A2E48")), blend="multiply", alpha=0.6)


def _timber_frame(r: Recipe) -> None:
    """The timber frame shared by the house walls: posts at the edges, a beam on the top, a sill at the bottom."""
    r.rect(0, 4.5, TILE, 4, linear(0, 4.5, 0, 8.5, (0, "#3A3050"), (1, "#FFFFFF")), blend="multiply", alpha=0.55)  # the shadow of the eaves
    _beam(r, 0, 0, TILE, 4.5, True, 171)
    _beam(r, 0, 27.5, TILE, 4.5, True, 173)
    for px in (0, 29):
        r.rect(px + (3 if px == 0 else -1.2), 0, 1.2, TILE, "#2A2238", alpha=0.35, blend="multiply", blur=0.5)
        _beam(r, px, 0, 3, TILE, False, 175 + px)


def _plaster(r: Recipe, seed: int) -> None:
    r.rect(0, 0, TILE, TILE, noise(8, seed, (0.3, "#C4B494"), (0.5, "#D8CAA8"), (0.72, "#EAE0C4"), octaves=4))
    r.rect(0, 0, TILE, TILE, noise(0.8, seed + 1, (0.3, "#A89A80"), (0.62, "#FFFFFF"), octaves=3), blend="multiply", alpha=0.45)  # the roughness of lime
    r.rect(0, 0, TILE, TILE, noise(4, seed + 2, (0.72, "#FFFFFF"), (0.9, "#7A6A50"), octaves=2, ridged=True), blend="multiply", alpha=0.25)  # hairline cracks
    r.rect(0, 0, TILE, TILE, linear(0, 0, 0, TILE, (0, "#FFFFFF"), (1, "#8A7A8A")), blend="multiply", alpha=0.35)
    r.rect(0, 22, TILE, 10, noise(3, seed + 3, (0.4, "#FFFFFF"), (0.7, "#8A7A60"), octaves=3), blend="multiply", alpha=0.35)  # the splashes of the rain at the foot
    r.path("M 20 22 L 22 25 L 21 27", None, stroke="#8A7A5A", width=0.25, alpha=0.7)


def wall_timber() -> Recipe:
    r = small("wall_timber", {"plaster": "#D8CAA8", "beam": "#5A3A22"})
    _plaster(r, 151)
    r.path("M 3 28.6 L 30 6.8", None, stroke="#2A2238", width=3.0, alpha=0.35, blend="multiply", blur=0.6)
    r.path("M 3 27.5 L 29 6", None, stroke="#4A3020", width=2.4)
    r.path("M 3 27.1 L 29 5.6", None, stroke="#8A6440", width=0.5, alpha=0.6)
    r.path("M 3.4 28 L 29.4 6.6", None, stroke="#1A0E06", width=0.4, alpha=0.6)
    _timber_frame(r)
    return r


def wall_window() -> Recipe:
    r = small("wall_window", {"plaster": "#D8CAA8", "beam": "#5A3A22"})
    _plaster(r, 153)
    r.rect(7.5, 9.5, 18, 16.5, "#2A2238", alpha=0.4, blend="multiply", blur=0.8)
    r.rect(7.5, 8.5, 17, 16, noise(0.6, 154, (0.3, "#2A1A0E"), (0.7, "#4A3220"), octaves=3, scale_y=8))
    r.rect(9, 10, 14, 13, linear(9, 10, 23, 23, (0, "#B8D0DC"), (0.45, "#5A7E96"), (1, "#22364A")))
    r.rect(9, 10, 14, 13, radial(19, 20, 6, (0, "#FFC870"), (1, "#FFC87000")), alpha=0.35, blend="add")  # a warm light inside
    r.path("M 10 22 L 16 10.5 L 19 10.5 L 13 22 Z", "#FFFFFF", alpha=0.22, blur=0.3)
    r.path("M 18.5 22.5 L 21.5 15 L 22.6 15 L 20 22.5 Z", "#FFFFFF", alpha=0.15, blur=0.2)
    r.rect(15.4, 10, 1.2, 13, "#3A2616")
    r.rect(9, 15.9, 14, 1.2, "#3A2616")
    r.rect(9, 10, 14, 1.6, "#0A0810", alpha=0.45, blur=0.4)  # the shade of the frame on the glass
    r.rect(6.5, 24.6, 19, 2.6, "#2A2238", alpha=0.45, blend="multiply", blur=0.6)
    r.rect(6.5, 23.6, 19, 2.4, noise(8, 155, (0.3, "#6A4422"), (0.7, "#9A6E44"), octaves=3, scale_y=0.5))  # the sill
    r.rect(6.5, 23.6, 19, 2.4, linear(0, 23.6, 0, 26, (0, "#FFFFFF"), (0.3, "#FFFFFF"), (1, "#3A2E48")), blend="multiply", alpha=0.6)
    for fx, c in ((11, "#D8506E"), (14.5, "#E8C048"), (18, "#D8506E"), (21, "#F0EEE8")):  # a box of flowers
        r.ellipse(fx + 0.3, 23.2, 2.0, 1.0, AO, alpha=0.5, blend="multiply", blur=0.4)
        r.ellipse(fx, 22.6, 1.9, 1.3, noise(0.5, 156, (0.3, "#2A5A2A"), (0.7, "#5A8A40"), octaves=2))
        r.ellipse(fx, 21.4, 1.0, 0.9, radial(fx - 0.3, 21.1, 1.1, (0, lighten(c, 0.3)), (1, darken(c, 0.25))))
    _timber_frame(r)
    return r


def door() -> Recipe:
    r = small("door", {"wood": "#8E6238", "frame": "#5A3A22"})
    r.rect(0, 0, TILE, TILE, "#1E140C")
    for i in range(4):  # upright boards
        x = 3 + i * 6.5
        tone = ["#7E5430", "#8A5E36", "#76502E", "#86603A"][i]
        r.rect(x, 5, 6.3, 18, noise(0.7, 161 + i, (0.3, darken(tone, 0.22)), (0.5, tone), (0.7, lighten(tone, 0.12)), octaves=4, scale_y=12))
        r.rect(x, 5, 6.3, 18, noise(0.6, 171 + i, (0.7, "#FFFFFF"), (0.92, "#1A0E06"), octaves=3, scale_y=6, ridged=True), blend="multiply", alpha=0.45)
        r.rect(x, 5, 0.8, 18, LIGHT, alpha=0.14, blend="add")
        r.rect(x + 5.8, 5, 0.5, 18, "#100804", alpha=0.7)
    for y in (8.5, 18.5):  # iron bands
        r.rect(3, y + 0.6, 26, 2.2, AO, alpha=0.5, blend="multiply", blur=0.4)
        r.rect(3, y, 26, 2.2, noise(1, 181, (0.3, "#3A3A40"), (0.7, "#5E5E66"), octaves=3))
        r.rect(3, y, 26, 2.2, linear(0, y, 0, y + 2.2, (0, "#E8E8F0"), (0.4, "#FFFFFF"), (1, "#404058")), blend="multiply", alpha=0.7)
        r.rect(3, y, 26, 2.2, nz(r, 2, 182, (0.4, "#FFFFFF"), (0.7, "#8A4A22")), blend="multiply", alpha=0.4)  # rust
        for x in (5, 12, 20, 27):
            r.ellipse(x, y + 1.1, 0.5, 0.5, radial(x - 0.15, y + 0.95, 0.6, (0, "#C8C8D0"), (1, "#2A2A30")))
    r.ellipse(24.5, 15.2, 1.6, 1.4, AO, alpha=0.5, blend="multiply", blur=0.4)
    r.ellipse(24.5, 14.5, 1.4, 1.4, radial(24, 14, 2, (0, "#F0D890"), (0.5, "#A87A30"), (1, "#4A3010")))  # the handle
    r.rect(0, 5, TILE, 3.5, linear(0, 5, 0, 8.5, (0, "#2A2238"), (1, "#FFFFFF")), blend="multiply", alpha=0.7)
    r.rect(0, 23, TILE, 9, nz(r, 2, 165, (0.3, "#8A8478"), (0.5, "#A8A294"), (0.7, "#C4BEB0"), octaves=4))  # the stone threshold
    r.rect(0, 23, TILE, 9, nz(r, 2, 166, (0.7, "#FFFFFF"), (0.92, "#4A4640"), octaves=3, ridged=True), blend="multiply", alpha=0.4)
    r.rect(0, 23, TILE, 1.4, "#0E0A10", alpha=0.6, blur=0.3)
    r.rect(2, 25, 28, 4.4, LIGHT, alpha=0.14, blend="add", blur=0.8)
    r.path("M 6 28 L 26 28", None, stroke="#5A5650", width=0.35, alpha=0.8)
    for px in (0, 29):
        _beam(r, px, 0, 3, 23.5, False, 191 + px)
    _beam(r, 0, 0, TILE, 5, True, 195)
    return r


# ------------------------------------------------------------------------------------------------ the tiles
def build_tiles() -> list[Recipe]:
    violet = ["#A878D0", "#8A5CC0", "#D0B4EC"]
    return [
        grass("grass_a", clumps_n=4),
        grass("grass_b", clumps_n=3, pebbles_n=1),
        grass("grass_c", flowers_of=["#F4F2EA", "#F2E28A", "#F0C4D0"], clumps_n=3),
        grass("grass_d", clover=True, clumps_n=2, pebbles_n=1),
        grass("grass_e", dry=True, clumps_n=4, blades=("#4E6E2E", "#8A9A48", "#C8C27A")),
        grass("grass_f", mushrooms=True, clumps_n=3),
        grass("violet_a", flowers_of=violet, clumps_n=3),
        grass("violet_b", flowers_of=["#7A90D8", "#B0BEF0", "#A878D0"], clumps_n=3),
        forest_floor(),
        moss("moss_a", 31, True),
        moss("moss_b", 31, False),
        dirt("path_dirt", ("#6A5034", "#8A6C48", "#AA8E66"), 33, pebbles_n=2),
        dirt("road", ("#64503A", "#82694C", "#A0886A"), 33, ruts=True, pebbles_n=1),
        sand(),
        coast("coast_a", 43),
        coast("coast_b", 45),
        rocky("rocky_a", 55, 2),
        rocky("rocky_b", 57, 1),
        savanna("savanna_a", 63, False),
        savanna("savanna_b", 65, True),
        snowfield("snow", ("#BCCCE0", "#E2EAF4", "#FAFCFF"), 67),
        snowfield("frost_a", ("#98AEB8", "#C2D4D8", "#E6F0F0"), 69, crystals=True, tufts=True),
        snowfield("frost_b", ("#98AEB8", "#C2D4D8", "#E6F0F0"), 69, crystals=True),
        ash("ash_a", ("#242226", "#38353A", "#524E54"), 71, embers=1, cracks=1),
        ash("ash_b", ("#242226", "#38353A", "#524E54"), 73, embers=1, cracks=1),
        ash("ash_c", ("#242226", "#38353A", "#524E54"), 75, embers=2, cracks=0),
        ash("ash_sand", ("#403A34", "#5A5448", "#78705E"), 77, embers=1, cracks=1),
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
