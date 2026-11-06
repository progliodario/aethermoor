#!/usr/bin/env python3
"""Writes the art recipes of data/base/art/ that are made by code: the terrain tiles and the props (more kinds come with the next steps).

    python tools/make_art.py [tiles] [props] [--show]

The recipes are plain JSON (`schemas/art_recipe.schema.json`); this script only builds them with `tools/artkit.py` so that the
details (hundreds of blades, pebbles, planks) do not have to be written by hand. The style rules are in `docs/design/art-style.md`.
Run `python tools/art_preview.py <pattern>` to look at the result, `python tools/validate_data.py` to check it.
"""
from __future__ import annotations

import sys

from art_props import build_props  # noqa: E402
from artkit import ART, Recipe, darken, lighten, linear, mix  # noqa: E402

TILE = 32


def tile(name: str, base: str, extra: dict | None = None) -> Recipe:
    return Recipe(f"base:art/tile/{name}", TILE, TILE, (0, 0), {"base": base, **(extra or {})}, seed="v2")


def mottle(r: Recipe, base: str, light=0.10, dark=0.10, n=7) -> None:
    """A flat base with soft patches of lighter and darker tones, so that a tile is never one flat color."""
    r.rect(0, 0, TILE, TILE, "$p.base")
    r.blotches(n, lighten(base, light * 2), 4, 8, alpha=0.14)
    r.blotches(n, darken(base, dark * 2), 4, 8, alpha=0.12)


# ------------------------------------------------------------------------------------------------ grass and ground families
def grass(name: str, base="#5DA95A", flower=None, clover=False, mushrooms=False, dry=0.0, pebbles=0, tufts=12) -> Recipe:
    r = tile(name, base)
    mottle(r, base)
    dark, light = mix(darken(base, 0.12), "#2F7A3A", 0.45), mix(lighten(base, 0.08), "#B4E27A", 0.55)
    if dry:
        dry_color = mix(base, "#C8B45A", dry)
        r.blotches(4, dry_color, 3, 6, alpha=0.2)
    if clover:
        for x, y in r.scatter(5, 5):
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 1.8)):
                r.ellipse(x + dx * 0.9, y + dy * 0.9, 2.3, 1.8, darken(base, 0.28))
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 1.8)):
                r.ellipse(x + dx * 0.9 - 0.5, y + dy * 0.9 - 0.5, 1.2, 0.9, lighten(base, 0.14), alpha=0.8)
    r.blades(max(3, tufts * 6 // 10), dark, light=light)
    r.speckles(3, light, 0.35, 0.6, alpha=0.7)
    if pebbles:
        r.pebbles(pebbles, "#9A9AA4")
    if flower:
        r.flowers(3, flower, r=0.9)
    if mushrooms:
        r.ellipse(16, 17, 10, 6.5, darken(base, 0.20), alpha=0.45)  # a darker ring where they grow
        for (x, y, s) in ((13, 15, 1.0), (19.5, 18.5, 0.75), (10, 19.5, 0.6)):
            r.ellipse(x, y + 2.5 * s, 3 * s, 1 * s, "#000000", alpha=0.22)
            r.rect(x - 0.9 * s, y, 1.8 * s, 3 * s, "#F2E8D2")
            r.ellipse(x, y, 3.3 * s, 2.5 * s, "#D14B3F")
            r.ellipse(x - 1.1 * s, y - 0.8 * s, 0.6 * s, 0.5 * s, "#FFFFFF")
            r.ellipse(x + 1.0 * s, y - 0.2 * s, 0.5 * s, 0.4 * s, "#FFFFFF")
    return r


def dirt(name: str, base: str, ruts=False, pebbles=5, speck="#000000") -> Recipe:
    r = tile(name, base)
    mottle(r, base, 0.12, 0.12, 8)
    if ruts:
        for y in (9, 22):
            r.rect(0, y - 2, TILE, 4, darken(base, 0.22), alpha=0.45)
            r.rect(0, y - 2, TILE, 1.2, darken(base, 0.4), alpha=0.35)
            r.rect(0, y + 1.2, TILE, 0.9, lighten(base, 0.3), alpha=0.35)
    r.speckles(24, darken(base, 0.35), 0.4, 0.9, alpha=0.55)
    r.speckles(14, lighten(base, 0.35), 0.3, 0.7, alpha=0.7)
    r.pebbles(pebbles, mix(base, "#8A8A90", 0.55), 4)
    return r


def sand(name: str, base="#EBD59B", dunes=True) -> Recipe:
    r = tile(name, base)
    mottle(r, base, 0.10, 0.10, 6)
    if dunes:
        for i in range(4):
            y = 5 + i * 7.5 + r.rng.uniform(-1, 1)
            r.path(f"M 1 {y:.1f} Q 9 {y - 2.4:.1f} 16 {y:.1f} Q 23 {y + 2.4:.1f} 31 {y:.1f}", None, stroke=darken(base, 0.13), width=1.1, alpha=0.7)
            r.path(f"M 1 {y + 1.3:.1f} Q 9 {y - 1.1:.1f} 16 {y + 1.3:.1f} Q 23 {y + 3.7:.1f} 31 {y + 1.3:.1f}", None, stroke=lighten(base, 0.4), width=0.8, alpha=0.8)
    r.speckles(26, darken(base, 0.3), 0.3, 0.7, alpha=0.5)
    r.pebbles(2, "#C9B98A", 4, 0.7, 1.3)
    return r


def snowfield(name: str, base="#F4F8FC", shadow="#B9CCE6", crystals=False, grass_tufts=False) -> Recipe:
    r = tile(name, base)
    r.rect(0, 0, TILE, TILE, "$p.base")
    for x, y in r.scatter(5, 4):  # drifts: a soft bluish shadow under a bright top
        r.ellipse(x + 1, y + 1.6, 7, 3.2, shadow, alpha=0.55)
        r.ellipse(x - 0.5, y - 0.4, 6.5, 2.8, "#FFFFFF", alpha=0.9)
    r.speckles(22, "#FFFFFF", 0.4, 0.8)
    r.speckles(10, shadow, 0.3, 0.6, alpha=0.6)
    if crystals:
        for x, y in r.scatter(4, 4):
            s = r.rng.uniform(1.5, 2.6)
            r.poly([(x, y - s), (x + s * 0.55, y), (x, y + s), (x - s * 0.55, y)], "#CFE9FF")
            r.poly([(x, y - s), (x + s * 0.55, y), (x, y)], "#FFFFFF", alpha=0.85)
    if grass_tufts:
        r.blades(5, "#8FA89A", 2, 4, light="#B7CBBE")
    return r


def ash(name: str, base: str, embers=0, cracks=0, drifts=3) -> Recipe:
    r = tile(name, base)
    mottle(r, base, 0.08, 0.10, 7)
    for x, y in r.scatter(drifts, 4):
        r.ellipse(x, y, 6.5, 2.6, lighten(base, 0.22), alpha=0.55)
    r.speckles(22, lighten(base, 0.3), 0.3, 0.7, alpha=0.6)
    r.speckles(16, darken(base, 0.45), 0.35, 0.8, alpha=0.7)
    r.pebbles(3, "#6A6A70", 4)
    for _ in range(cracks):
        x, y = r.rng.uniform(4, 24), r.rng.uniform(4, 26)
        pts = [(x, y)]
        for _ in range(4):
            x += r.rng.uniform(1.5, 4.5)
            y += r.rng.uniform(-3, 3)
            pts.append((min(x, 30), min(max(y, 2), 30)))
        d = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in pts)
        r.path(d, None, stroke="#14100E", width=1.3, alpha=0.85)
        r.path(d, None, stroke="#E8672A", width=0.5, alpha=0.8)
    for x, y in r.scatter(embers, 3):
        r.ellipse(x, y, 1.9, 1.9, "#FF7A2A", alpha=0.28)
        r.ellipse(x, y, 0.9, 0.9, "#FFC070")
    return r


# ------------------------------------------------------------------------------------------------ the tiles
def build_tiles() -> list[Recipe]:
    out: list[Recipe] = []
    out.append(grass("grass_a", "#5DA95A", tufts=14))
    out.append(grass("grass_b", "#68B364", tufts=8, pebbles=1))
    out.append(grass("grass_c", "#5DA95A", flower=["#FFFFFF", "#FFF3A0", "#FFD0E0"], tufts=9))
    out.append(grass("grass_d", "#5AA357", clover=True, tufts=7, pebbles=2))
    out.append(grass("grass_e", "#6BAE57", dry=0.5, tufts=14))
    out.append(grass("grass_f", "#5DA95A", mushrooms=True, tufts=6))
    out.append(grass("violet_a", "#5DA95A", flower=["#B07AE0", "#8A5CD0", "#D8B8F8"], tufts=9))
    out.append(grass("violet_b", "#5FAC5E", flower=["#7A9AE8", "#B8C8FF", "#B07AE0"], tufts=9))

    forest = tile("forest_floor", "#3F8A47")
    mottle(forest, "#3F8A47", 0.10, 0.14, 8)
    forest.blotches(4, "#E8D890", 3, 5, alpha=0.18)  # dappled light through the leaves
    for x, y in forest.scatter(10, 3):  # fallen leaves
        c = forest.rng.choice(["#A86B32", "#C98A3C", "#8A5A2A", "#B8742E"])
        forest.poly([(x, y), (x + 1.7, y - 0.9), (x + 3.2, y + 0.2), (x + 1.5, y + 1.0)], c)
        forest.line(x, y, x + 3.0, y + 0.1, darken(c, 0.35), 0.4)
    forest.blades(9, "#2E6F3A", light="#5AAE5A")
    forest.pebbles(2, "#8A8A8A", 4, 0.8, 1.4)
    out.append(forest)

    for name, light in (("moss_a", False), ("moss_b", True)):
        r = tile(name, "#2F6B3F" if not light else "#2A5E3A")
        mottle(r, "#2F6B3F", 0.10, 0.18, 8)
        for x, y in r.scatter(11, 3):  # moss clumps
            for _ in range(4):
                rr = r.rng.uniform(1.2, 2.4)
                r.ellipse(x + r.rng.uniform(-2, 2), y + r.rng.uniform(-1.2, 1.2), rr, rr * 0.75, mix("#3E8A4A", "#6FB85A", r.rng.random()))
        r.blades(8, "#1F4E2C", light="#5FA85A")
        if name == "moss_a":
            for x, y in r.scatter(2, 6):
                r.rect(x - 0.7, y, 1.4, 2.6, "#E8DFEA")
                r.ellipse(x, y, 2.6, 1.9, "#B07AE0")
                r.ellipse(x - 0.8, y - 0.6, 0.6, 0.4, "#FFFFFF")
        else:
            r.line(4, 25, 13, 21, "#4B3A26", 1.1)
            r.line(9, 23, 12, 26, "#4B3A26", 0.8)
            r.pebbles(2, "#7A8A7A", 4)
        out.append(r)

    out.append(dirt("path_dirt", "#C99A5A", pebbles=4))
    out.append(dirt("road", "#B88A52", ruts=True, pebbles=3))
    out.append(sand("sand", "#EBD59B"))

    for name, c in (("coast_a", "#7FB068"), ("coast_b", "#86B56C")):
        r = tile(name, c)
        mottle(r, c, 0.10, 0.10, 6)
        for x, y in r.scatter(3 if name == "coast_a" else 2, 6):  # sandy patches
            r.ellipse(x, y, 6.2, 3.8, "#E3D199", alpha=0.95)
            r.ellipse(x - 1.2, y - 1.0, 4.4, 2.3, "#F0E0AE", alpha=0.9)
            r.speckles(5, "#B8A874", 0.3, 0.6)
        r.blades(9, "#5E9A58", light="#9ACB7C")
        r.flowers(2, ["#FFFFFF"], r=0.8)
        r.ellipse(24, 8, 1.2, 0.8, "#F5E6D8")  # a shell
        out.append(r)

    out.append(grass("rocky_a", "#79946B", pebbles=5, tufts=6))
    out.append(grass("rocky_b", "#7A9570", pebbles=3, tufts=7))
    for name in ("rocky_a", "rocky_b"):
        r = [t for t in out if t.id.endswith("/" + name)][0]
        for x, y in r.scatter(1 if name == "rocky_b" else 2, 7):  # a boulder
            r.ellipse(x + 1, y + 2.2, 5.6, 1.8, "#000000", alpha=0.25)
            r.ellipse(x, y, 5.2, 3.8, "#8E9298")
            r.ellipse(x - 1.0, y - 1.0, 3.4, 2.3, "#B2B6BC")
            r.path(f"M {x - 3:.1f} {y + 1:.1f} Q {x:.1f} {y + 2.6:.1f} {x + 4:.1f} {y + 0.5:.1f}", None, stroke="#6C7076", width=0.9)

    for name, base, light_dry in (("savanna_a", "#C4B058", "#E0D082"), ("savanna_b", "#C8B060", "#E6D68C")):
        r = tile(name, base)
        mottle(r, base, 0.10, 0.12, 7)
        r.blades(11, darken(base, 0.28), 3, 6, light=light_dry)
        r.blades(5, "#8FA04C", 2.5, 4.5, light="#B8C870")
        r.speckles(14, darken(base, 0.3), 0.3, 0.7, alpha=0.6)
        r.pebbles(1 if name == "savanna_a" else 2, "#B0A07A", 4)
        for _ in range(1 if name == "savanna_b" else 0):  # a crack in the dry ground
            r.path("M 4 24 L 9 21 L 12 23 L 18 19", None, stroke=darken(base, 0.45), width=0.9, alpha=0.8)
        out.append(r)

    out.append(snowfield("snow", "#F2F7FC"))
    out.append(snowfield("frost_a", "#CFE4E2", "#9FB9BE", crystals=True, grass_tufts=True))
    out.append(snowfield("frost_b", "#C4DCDE", "#92B0B6", crystals=True))

    out.append(ash("ash_a", "#3C3A42", embers=3, cracks=1))
    out.append(ash("ash_b", "#43404A", embers=2, cracks=2))
    out.append(ash("ash_c", "#37353D", embers=4, cracks=0, drifts=4))
    out.append(ash("ash_sand", "#5A564C", embers=1, cracks=1, drifts=5))

    # water and the shallows
    w = Recipe("base:art/tile/water", TILE, TILE, (0, 0), {"top": "#4C8DE0", "bottom": "#3470C4", "wave": "#B0D4FA"}, seed="v2")
    w.rect(0, 0, TILE, TILE, linear(0, 0, 0, TILE, (0, "$p.top"), (1, "$p.bottom")))
    w.blotches(6, "#2A5CAA", 4, 8, alpha=0.30)
    w.blotches(5, "#78B0F0", 3, 6, alpha=0.22)
    for i in range(5):
        x, y = w.rng.uniform(2, 20), 3 + i * 6 + w.rng.uniform(-1, 1)
        L = w.rng.uniform(7, 11)
        w.path(f"M {x:.1f} {y:.1f} Q {x + L / 2:.1f} {y - 2.8:.1f} {x + L:.1f} {y:.1f}", None, stroke="$p.wave", width=1.2, alpha=0.85)
        w.path(f"M {x + 1:.1f} {y + 1.3:.1f} Q {x + L / 2 + 1:.1f} {y - 1.2:.1f} {x + L - 1:.1f} {y + 1.3:.1f}", None, stroke="#2C62B0", width=0.8, alpha=0.5)
    for x, y in w.scatter(5, 3):  # sparkles
        s = w.rng.uniform(0.8, 1.5)
        w.poly([(x, y - s * 1.6), (x + s * 0.5, y), (x, y + s * 1.6), (x - s * 0.5, y)], "#FFFFFF", alpha=0.85)
        w.poly([(x - s * 1.6, y), (x, y + s * 0.5), (x + s * 1.6, y), (x, y - s * 0.5)], "#FFFFFF", alpha=0.6)
    out.append(w)

    sh = Recipe("base:art/tile/shallows", TILE, TILE, (0, 0), {"top": "#7CC6E8", "bottom": "#5AAAD8", "sand": "#E8D9A6"}, seed="v2")
    sh.rect(0, 0, TILE, TILE, linear(0, 0, 0, TILE, (0, "$p.top"), (1, "$p.bottom")))
    for x, y in sh.scatter(5, 4):
        sh.ellipse(x, y, 6.5, 3.0, "$p.sand", alpha=0.78)
        sh.ellipse(x - 1.2, y - 0.8, 4.2, 1.7, "#F6EBC4", alpha=0.7)
    for i in range(4):
        x, y = sh.rng.uniform(1, 18), 4 + i * 7 + sh.rng.uniform(-1, 1)
        sh.path(f"M {x:.1f} {y:.1f} Q {x + 5:.1f} {y - 2:.1f} {x + 10:.1f} {y:.1f}", None, stroke="#EAF8FF", width=1.0, alpha=0.8)
    for x, y in sh.scatter(4, 3):
        sh.ellipse(x, y, 0.9, 0.9, "#FFFFFF", alpha=0.9)
    out.append(sh)

    # mountain: the faces of the peaks, snow and scree
    m = Recipe("base:art/tile/mountain", TILE, TILE, (0, 0), {"ground": "#706C78", "light": "#A8A2B0", "dark": "#4C4856", "snow": "#F6FAFF"}, seed="v2")
    m.rect(0, 0, TILE, TILE, linear(0, 0, 0, TILE, (0, "#8A8694"), (1, "#5E5A68")))
    for cx, base_y, top_y, half in ((9, 29, 7, 9.5), (23, 30, 11, 8.5), (16, 22, 3, 8)):
        m.ellipse(cx + 1.5, base_y, half, 2.2, "#000000", alpha=0.22)
        m.poly([(cx - half, base_y), (cx, top_y), (cx + half, base_y)], "$p.dark")
        m.poly([(cx - half, base_y), (cx, top_y), (cx + 1.2, base_y - 1)], "$p.light")
        m.poly([(cx - half * 0.55, base_y - 4), (cx - 0.5, top_y + 3), (cx - 3.5, base_y - 1)], lighten("#A8A2B0", 0.18), alpha=0.7)
        m.poly([(cx, top_y), (cx + 3.3, top_y + 4.6), (cx + 1.5, top_y + 3.9), (cx + 0.2, top_y + 5.4), (cx - 1.4, top_y + 3.8), (cx - 3.3, top_y + 4.6)], "$p.snow")
        m.poly([(cx, top_y), (cx + 3.3, top_y + 4.6), (cx + 1.5, top_y + 3.9), (cx + 0.2, top_y + 5.4)], "#C8D8EE", alpha=0.7)
    m.pebbles(5, "#9A96A2", 2, 0.7, 1.3)
    out.append(m)

    cobble = Recipe("base:art/tile/cobble", TILE, TILE, (0, 0), {"base": "#6A6A72", "stone": "#9C9CA6", "stone2": "#8E8E98"}, seed="v2")
    cobble.rect(0, 0, TILE, TILE, "$p.base")
    stones = [(7, 7, 6.2, 5.0), (22, 6, 6.6, 4.6), (8, 21, 6.4, 5.4), (23, 22, 6.2, 5.2), (15, 14.5, 5.0, 4.0), (30, 14, 3.4, 4.0), (1, 14, 3.2, 4.0)]
    for i, (x, y, rx, ry) in enumerate(stones):
        c = ["#9C9CA6", "#8E8E98", "#A6A6B0"][i % 3]
        cobble.ellipse(x + 0.7, y + 1.0, rx, ry, "#000000", alpha=0.3)
        cobble.ellipse(x, y, rx, ry, c)
        cobble.ellipse(x - rx * 0.25, y - ry * 0.3, rx * 0.65, ry * 0.5, lighten(c, 0.35), alpha=0.75)
        cobble.path(f"M {x - rx * 0.7:.1f} {y + ry * 0.55:.1f} Q {x:.1f} {y + ry * 1.0:.1f} {x + rx * 0.7:.1f} {y + ry * 0.55:.1f}", None, stroke=darken(c, 0.3), width=0.8, alpha=0.8)
    cobble.speckles(10, "#4A4A52", 0.3, 0.6, alpha=0.7)
    cobble.speckles(3, "#5A8A50", 0.6, 1.0, alpha=0.8)  # a bit of moss in the gaps
    out.append(cobble)

    plank = Recipe("base:art/tile/plank_floor", TILE, TILE, (0, 0), {"wood": "#B07A44", "dark": "#7A4F2A", "light": "#D09A62"}, seed="v2")
    plank.rect(0, 0, TILE, TILE, "$p.dark")
    for i in range(4):
        y = i * 8
        shift = (i % 2) * 6
        tone = ["#B07A44", "#A87040", "#B88450", "#AC7644"][i]
        plank.rect(0, y + 0.5, TILE, 7, tone)
        plank.rect(0, y + 0.5, TILE, 1.5, lighten(tone, 0.28), alpha=0.7)
        plank.rect(0, y + 6.0, TILE, 1.5, darken(tone, 0.25), alpha=0.6)
        for gx in (4 + shift, 19 + shift):  # grain
            plank.path(f"M {gx} {y + 3} Q {gx + 6} {y + 2} {gx + 12} {y + 4}", None, stroke=darken(tone, 0.28), width=0.7, alpha=0.7)
        plank.line(8 + shift * 2 % 20, y + 0.5, 8 + shift * 2 % 20, y + 7.5, "$p.dark", 1.0)
        plank.ellipse(2.0 + shift, y + 4, 0.55, 0.55, "#4A2E18")
        plank.ellipse(29.5 - shift / 2, y + 4, 0.55, 0.55, "#4A2E18")
    out.append(plank)

    wall = Recipe("base:art/tile/wall_stone", TILE, TILE, (0, 0), {"base": "#7E8794", "top": "#B2BAC6", "mortar": "#4E5662"}, seed="v2")
    wall.rect(0, 0, TILE, TILE, "$p.mortar")
    rows = [(0, 8, 0), (8, 8, 7), (16, 8, 0), (24, 8, 7)]
    for ry, rh, off in rows:
        x = -off
        while x < TILE:
            bw = wall.rng.choice([13, 15, 17])
            tone = mix("#7E8794", "#9AA3B0", wall.rng.random())
            x0, x1 = max(x, 0) + 0.7, min(x + bw, TILE) - 0.7
            if x1 - x0 > 2:
                wall.rect(x0, ry + 0.7, x1 - x0, rh - 1.4, tone)
                wall.rect(x0, ry + 0.7, x1 - x0, 1.8, lighten(tone, 0.28), alpha=0.8)
                wall.rect(x0, ry + rh - 2.4, x1 - x0, 1.7, darken(tone, 0.25), alpha=0.7)
                wall.speckles(2, darken(tone, 0.35), 0.4, 0.8, alpha=0.6)
            x += bw
    wall.rect(0, 0, TILE, 4, linear(0, 0, 0, 4, (0, "$p.top"), (1, "#7E8794")), alpha=0.85)
    wall.path("M 6 19 L 9 22 L 8 26", None, stroke="#3A404A", width=0.7, alpha=0.8)
    out.append(wall)

    bridge = Recipe("base:art/tile/bridge", TILE, TILE, (0, 0), {"wood": "#A8703A", "dark": "#6A4222", "water": "#4C8DE0"}, seed="v2")
    bridge.rect(0, 0, TILE, TILE, "$p.water")
    bridge.rect(0, 2, TILE, 28, "$p.dark")
    for i in range(4):
        y = 2 + i * 7
        tone = ["#B07A44", "#A8703A", "#B88450", "#AC7640"][i]
        bridge.rect(0, y + 0.4, TILE, 6.2, tone)
        bridge.rect(0, y + 0.4, TILE, 1.4, lighten(tone, 0.3), alpha=0.8)
        bridge.rect(0, y + 5.1, TILE, 1.4, darken(tone, 0.28), alpha=0.7)
        bridge.path(f"M 3 {y + 3.2} Q 11 {y + 2.4} 20 {y + 3.6}", None, stroke=darken(tone, 0.3), width=0.7, alpha=0.7)
        bridge.ellipse(2.4, y + 3.3, 0.55, 0.55, "#3A2412")
        bridge.ellipse(29.6, y + 3.3, 0.55, 0.55, "#3A2412")
    bridge.rect(0, 0, TILE, 2, "#2C62B0", alpha=0.7)
    bridge.rect(0, 30, TILE, 2, "#2C62B0", alpha=0.7)
    out.append(bridge)
    return out


def main() -> int:
    what = [a for a in sys.argv[1:] if not a.startswith("--")] or ["tiles"]
    count = 0
    if "tiles" in what:
        for r in build_tiles():
            r.write(ART / "tiles" / (r.id.rsplit("/", 1)[1] + ".json"))
            count += 1
    if "props" in what:
        for r in build_props():
            r.write(ART / "props" / (r.id.rsplit("/", 1)[1] + ".json"))
            count += 1
    print(f"wrote {count} recipes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
