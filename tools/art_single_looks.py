"""Detail layers for the single creatures (bat, spider, scorpion, crab, owl, myconid, golem, wisp), drawn over their recipes.

Used by `art_creatures.py`. Each function adds layers to a scratch recipe in the coordinates of the creature's own canvas.
"""
from __future__ import annotations

from artkit import Recipe


def cave_bat(x: Recipe) -> None:  # veins in the wings, a tuft on the chest, pink ears, glints in the eyes
    for sx in (-1, 1):
        for tx, ty in ((3, 10), (5, 17), (10, 21)):
            x.line(22 + sx * 3, 16, 22 + sx * (22 - tx), ty, "#120C1A", width=0.8, alpha=0.55)
        x.path(f"M {22 + sx * 7} 14 Q {22 + sx * 12} 9 {22 + sx * 17} 11", None, stroke="#FFFFFF", width=0.7, alpha=0.25)
    for ex in (19.4, 24.6):
        x.poly([(ex - 1, 7), (ex + (-0.4 if ex < 22 else 0.4), 4), (ex + 1, 7.4)], "#E58AA8", alpha=0.8)
    for tx in (19.4, 22, 24.6):
        x.poly([(tx - 1.1, 21), (tx, 25), (tx + 1.1, 21)], "$p.light", alpha=0.7)
    for ex in (20, 24):
        x.ellipse(ex - 0.4, 11.6, 0.4, 0.4, "#FFFFFF", alpha=0.95)
    x.path("M 18 8.6 Q 22 6.4 26 8.6", None, stroke="#FFFFFF", width=0.7, alpha=0.3)


def cave_spider(x: Recipe) -> None:  # bristles on the legs, spots on the abdomen, a silk thread, glints
    for sx in (-1, 1):
        for ax, ay in ((10, 14), (7, 20), (8, 27), (14, 29)):
            lx = 22 + sx * (22 - ax)
            x.line(lx, ay, lx + sx * 1.6, ay - 1.4, "#000000", width=0.6, alpha=0.7)
    for px, py, r in ((19, 25.5, 1.1), (25, 26, 1.0), (22, 27.6, 0.9), (17.4, 22, 0.7), (26.6, 22, 0.7)):
        x.ellipse(px, py, r, r, "$p.light", alpha=0.7)
    x.line(22, 2, 22, 9.6, "#FFFFFF", width=0.5, alpha=0.45)
    for ex in (19.5, 24.5):
        x.ellipse(ex - 0.3, 12.6, 0.4, 0.4, "#FFFFFF", alpha=0.95)
    x.path("M 17 19 Q 22 16.4 27 19", None, stroke="#FFFFFF", width=0.7, alpha=0.3)


def dune_scorpion(x: Recipe) -> None:  # the rings of the tail, plates on the back, shine on the claws
    for tx, ty in ((41.8, 22.4), (42.2, 18.4), (41.2, 13.6), (38.6, 9.4)):
        x.line(tx - 1.8, ty, tx + 1.8, ty - 0.6, "#000000", width=0.8, alpha=0.5)
    for py in (20.5, 23, 25.5):
        x.path(f"M 17 {py} Q 24 {py + 1.6} 31 {py}", None, stroke="#000000", width=0.8, alpha=0.4)
    x.path("M 18 18 Q 24 15.4 30 18", None, stroke="#FFFFFF", width=0.8, alpha=0.3)
    for cx, sx in ((8, -1), (40, 1)):
        x.path(f"M {cx - sx * 0.5} 9 Q {cx + sx * 2} 8 {cx + sx * 3.4} 11", None, stroke="#FFFFFF", width=0.8, alpha=0.4)
        x.path(f"M {cx} 10 L {cx - sx * 1.6} 14", None, stroke="#000000", width=0.8, alpha=0.5)
    x.ellipse(36.2, 6.4, 0.6, 0.6, "#FFFFFF", alpha=0.8)


def shore_crab(x: Recipe) -> None:  # ridges on the shell, teeth in the claws, bubbles
    for rx, ry in ((10, 4), (14.5, 2.4), (22, 1.6)):
        x.path(f"M {22 - rx} {21 - ry} Q 22 {21 - ry - 4} {22 + rx} {21 - ry}", None, stroke="#000000", width=0.8, alpha=0.3)
    x.path("M 12 18 Q 22 14.6 32 18", None, stroke="#FFFFFF", width=0.8, alpha=0.3)
    for cx, sx in ((7, 1), (37, -1)):
        for k in range(3):
            tx = cx + sx * (k * 1.6 - 1)
            x.poly([(tx - 0.8, 7.4 + k * 0.6), (tx, 9.6 + k * 0.6), (tx + 0.8, 7.4 + k * 0.6)], "#FFFFFF", stroke="#3A2010", width=0.4)
    for bx, by, r in ((36, 22, 1.2), (38.4, 19.4, 0.8), (6, 14, 1.0)):
        x.ellipse(bx, by, r, r, "#BFE6FF", alpha=0.5, stroke="#FFFFFF", width=0.3)
    for ex in (17.5, 26.5):
        x.ellipse(ex - 0.5, 12, 0.5, 0.5, "#FFFFFF", alpha=0.95)
    x.path("M 18 24 Q 22 26.4 26 24", None, stroke="#000000", width=0.7, alpha=0.5)


def night_owl(x: Recipe) -> None:  # feather chevrons on the belly, a brow, the rings of the wings, glints
    for cy, hw in ((22, 3.4), (25.4, 3.8), (28.8, 3.4), (32, 2.6)):
        x.path(f"M {18 - hw} {cy} Q 18 {cy + 2.2} {18 + hw} {cy}", None, stroke="#000000", width=0.7, alpha=0.3)
    for sx in (-1, 1):
        for k in range(3):
            x.path(f"M {18 + sx * (9.6 - k * 0.6)} {23 + k * 3} Q {18 + sx * (12.2 - k * 0.6)} {24.4 + k * 3} {18 + sx * (10.6 - k * 0.6)} {26.6 + k * 3}", None, stroke="#000000", width=0.7, alpha=0.4)
        x.path(f"M {18 + sx * 5.6} 8.4 L {18 + sx * 7.6} 3.4", None, stroke="#E8D8B8", width=0.9, alpha=0.7)
    x.path("M 10 9 Q 14 7 17.4 9.4 M 26 9 Q 22 7 18.6 9.4", None, stroke="#000000", width=1.0, alpha=0.5)
    for ex in (14, 22):
        x.ellipse(ex - 0.9, 10.8, 0.9, 0.9, "#FFFFFF", alpha=0.95)
    x.path("M 12 18 Q 18 20.4 24 18", None, stroke="#FFFFFF", width=0.8, alpha=0.2)


def myconid(x: Recipe) -> None:  # gills under the cap, more spots, a blush, little roots
    for gx in (5, 8.5, 12, 15.5, 18, 20.5, 24, 27.5, 31):
        x.line(gx, 19.6 + abs(gx - 18) * 0.04, gx + (18 - gx) * 0.12, 21.6 - abs(gx - 18) * 0.05, "#7A3A30", width=0.6, alpha=0.6)
    for sx, sy, r in ((6, 14, 1.4), (30, 11, 1.2), (17, 15.4, 1.0), (13.5, 5.4, 1.1)):
        x.ellipse(sx, sy, r * 1.2, r, "$p.spot", alpha=0.9)
    x.path("M 6 8 Q 12 3.6 20 3.6", None, stroke="#FFFFFF", width=1.2, alpha=0.35)
    for bx in (13, 23):
        x.ellipse(bx, 28, 1.4, 0.8, "#E8707A", alpha=0.5)
    x.rect(12.4, 20.4, 11.2, 1.6, "#000000", alpha=0.2)  # the shade under the cap
    for rx in (13.4, 22.6):
        x.path(f"M {rx} 34 Q {rx + (rx - 18) * 0.2} 36 {rx + (rx - 18) * 0.5} 36.4", None, stroke="#7A5A3A", width=0.9, alpha=0.8)


def stone_golem(x: Recipe) -> None:  # glowing runes, cracks, plates and rubble
    for rx, ry in ((18.4, 21), (22, 24), (25.6, 21)):
        x.rect(rx - 0.5, ry, 1.0, 4.4, "$p.glow", alpha=0.9)
        x.ellipse(rx, ry + 2.2, 2.2, 3.4, "$p.glow", alpha=0.18)
    x.path("M 16 28 L 28 28 M 22 25 L 22 31", None, stroke="$p.glow", width=0.8, alpha=0.8)
    x.path("M 12 22 L 15 26 L 13 30", None, stroke="#1E2126", width=0.9, alpha=0.8)
    x.path("M 31 24 L 29 28 L 31 32", None, stroke="#1E2126", width=0.9, alpha=0.8)
    for px, py in ((6, 22), (38, 22), (15, 38), (29, 38)):
        x.path(f"M {px - 2} {py} L {px} {py - 2.4} L {px + 2} {py} Z", "#FFFFFF", alpha=0.18)
    for ex in (18.5, 25.5):
        x.ellipse(ex, 9, 4, 3, "$p.glow", alpha=0.25)
    for rx, ry, r in ((8, 44, 1.6), (36, 44.4, 1.4), (4, 42, 1.0)):
        x.ellipse(rx, ry, r * 1.3, r, "#8A8F96", stroke="#1E2126", width=0.5)
    x.path("M 15 5 L 29 5", None, stroke="#FFFFFF", width=0.8, alpha=0.3)


def wisp(x: Recipe) -> None:  # a flame within a flame, sparks, a trail of embers
    x.path("M 16 9 Q 22 16 21.6 24 Q 20.6 30 16 30 Q 11.4 30 10.4 24 Q 10 16 16 9 Z", "$p.light", alpha=0.5)
    for sx, sy, r in ((6, 14, 0.9), (26.6, 11, 0.8), (4.6, 24, 0.7), (28, 22, 0.9), (9, 6, 0.6), (23.4, 5, 0.7)):
        x.ellipse(sx, sy, r, r, "$p.light", alpha=0.9)
        x.ellipse(sx, sy, r * 2.2, r * 2.2, "$p.halo", alpha=0.25)
    for ex, ey in ((13, 36.4), (19, 37), (16, 38.4)):
        x.ellipse(ex, ey, 0.7, 0.5, "$p.halo", alpha=0.7)
    x.path("M 13 15 Q 14 12 16 10.6", None, stroke="#FFFFFF", width=1.0, alpha=0.6)
    x.path("M 12.4 27 Q 16 29.6 19.6 27", None, stroke="$p.eye", width=0.8, alpha=0.7)


SINGLE_LOOKS = {
    "cave_bat": cave_bat, "cave_spider": cave_spider, "dune_scorpion": dune_scorpion, "shore_crab": shore_crab,
    "night_owl": night_owl, "myconid": myconid, "stone_golem": stone_golem, "wisp": wisp,
}
