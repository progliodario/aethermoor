#!/usr/bin/env python3
"""The creatures of data/base/art/creatures/, drawn by family in the anime way (docs/design/art-style.md).

    python tools/art_creatures.py

Every creature keeps the palette of its file (so a new creature is a copy of a file with its own colours, added to the tables
below) and gets the body of its family and its own feature: slimes are jelly with a light inside; wolves, the game of the hunt
and the alphas are seen from the side and look to the left (the clients turn them to face the player); the guardians in armor
stand in front of you; the others are drawn one by one. The Echoes are not here: `make_echoes.py` recolours a guardian.
"""
from __future__ import annotations

import json
import math

from art_props import box
from artkit import ART, Recipe, linear, radial, transform_layers

CREATURES = ART / "creatures"
GOLD = "#F2C94C"
OUT = "$p.outline"


def palette_of(name: str) -> dict:
    return json.loads((CREATURES / f"{name}.json").read_text(encoding="utf-8"))["palette"]


def new(name: str, w: float, h: float, origin: tuple[float, float]) -> Recipe:
    return Recipe(f"base:art/creature/{name}", w, h, origin, palette_of(name), seed="v3")


def star(r: Recipe, x: float, y: float, s: float, color: str = "#FFFFFF", alpha: float = 0.95) -> None:
    r.poly([(x, y - s), (x + s * 0.25, y - s * 0.25), (x + s, y), (x + s * 0.25, y + s * 0.25), (x, y + s), (x - s * 0.25, y + s * 0.25), (x - s, y), (x - s * 0.25, y - s * 0.25)], color, alpha=alpha)


def flame(r: Recipe, x: float, base: float, h: float, w: float = 2.4) -> None:
    r.glow(x, base - h * 0.4, h * 0.9, "#FF7A20", 0.4)
    r.path(f"M {x} {base - h} Q {x + w} {base - h * 0.4} {x + w * 0.7} {base} L {x - w * 0.7} {base} Q {x - w} {base - h * 0.45} {x - w * 0.2} {base - h * 0.6} Q {x} {base - h * 0.8} {x} {base - h} Z",
           linear(x, base - h, x, base, (0, "#FF5A1E"), (0.6, "#FFA030"), (1, "#FFE070")))
    r.path(f"M {x} {base - h * 0.55} Q {x + w * 0.5} {base - h * 0.2} {x + w * 0.3} {base} L {x - w * 0.3} {base} Q {x - w * 0.5} {base - h * 0.25} {x} {base - h * 0.55} Z", "#FFF4C0")


def crystal(r: Recipe, x: float, base: float, h: float, w: float, lean: float = 0.0) -> None:
    tip = (x + lean, base - h)
    r.poly([(x - w, base), tip, (x + w, base)], linear(x - w, base - h, x + w, base, (0, "#FFFFFF"), (0.5, "#BFE8FF"), (1, "#5A9ADC")), stroke="#2A5A9A", width=0.3)
    r.poly([(x - w, base), tip, (x - w * 0.1, base)], "#FFFFFF", alpha=0.55)


def crown(r: Recipe, x: float, base: float, w: float, h: float, gem: str = "#E0302A") -> None:
    pts = [(x - w, base), (x - w * 1.05, base - h * 0.75), (x - w * 0.5, base - h * 0.4), (x, base - h), (x + w * 0.5, base - h * 0.4), (x + w * 1.05, base - h * 0.75), (x + w, base)]
    r.poly(pts, linear(x - w, base - h, x + w, base, (0, "#FFF4B0"), (0.5, GOLD), (1, "#A8741E")), stroke="#5A3A08", width=0.4)
    r.rect(x - w, base - h * 0.22, 2 * w, h * 0.22, "#A8741E", alpha=0.6)
    for px, py in ((x - w * 1.05, base - h * 0.75), (x, base - h), (x + w * 1.05, base - h * 0.75)):
        r.ellipse(px, py, w * 0.13, w * 0.13, "#FFF8D0", stroke="#5A3A08", width=0.25)
    r.ellipse(x, base - h * 0.38, w * 0.2, w * 0.24, gem, stroke="#5A3A08", width=0.25)
    r.ellipse(x - w * 0.06, base - h * 0.45, w * 0.07, w * 0.08, "#FFFFFF", alpha=0.9)


# ------------------------------------------------------------------------------------------------ slimes
SLIME = "M 4 22 Q 3 8 18 6 Q 33 8 32 22 Q 32 26.5 18 26.5 Q 4 26.5 4 22 Z"


def _sprout(r):
    r.path("M 18 6.5 Q 17.6 3.6 18.4 1.4", None, stroke="#2E7A3A", width=0.7)
    for sx in (-1, 1):
        r.path(f"M 18.3 2 Q {18.3 + sx * 3} {-1.2} {18.3 + sx * 5.6} 1.2 Q {18.3 + sx * 3} 3.4 18.3 2 Z", linear(12, 0, 24, 3, (0, "#B4F08A"), (1, "#3E9A46")), stroke="#1E5A2A", width=0.3)


def _drop(r):
    r.path("M 18 0.4 Q 21 4 20.4 5.8 Q 18 7.6 15.6 5.8 Q 15 4 18 0.4 Z", linear(15, 0, 21, 7, (0, "#FFFFFF"), (1, "#5AA8F0")), stroke="#1E4A8A", width=0.3)
    for ry in (20, 23):
        r.path(f"M 7 {ry} Q 18 {ry + 2.4} 29 {ry}", None, stroke="#FFFFFF", width=0.4, alpha=0.4, clip=True)


def _flames(r):
    for x, h in ((12, 6), (18, 8.5), (24, 6)):
        flame(r, x, 8.4 + abs(x - 18) * 0.25, h)
    for x, y in ((8, 3), (28, 2), (21, -1)):
        r.ellipse(x, y, 0.45, 0.45, "#FFE080")


def _ice(r):
    for x, h, w, lean in ((11, 7, 2, -1.5), (17, 10, 2.6, 0), (24, 7.5, 2.2, 1.6)):
        crystal(r, x, 8.6 + abs(x - 17.5) * 0.3, h, w, lean)
    for x, y in ((9, 20), (26, 16), (20, 23)):
        star(r, x, y, 1.1, "#FFFFFF", 0.8)


def _cracks(r, color="#FFB030"):
    for d in ("M 9 12 L 12 16 L 10.5 20 L 13 23", "M 22 8.4 L 21 12.6 L 24.6 15 L 23.6 19", "M 27 14 L 29 18 L 27.6 22"):
        r.path(d, None, stroke=color, width=1.8, alpha=0.5, blend="add", blur=0.7, clip=True)
        r.path(d, None, stroke="#FFF0B0", width=0.5, clip=True)


def _char(r):
    _cracks(r, "#FF6A20")
    r.path("M 19 5 Q 16 2 19 -0.6 Q 22 -3 19.6 -5", None, stroke="#8A8088", width=1.2, alpha=0.45, blur=0.6)


def _lure(r):
    r.path("M 18 6.4 Q 17 1 21.6 -0.6", None, stroke=OUT, width=0.6)
    r.glow(22.4, -0.8, 6, "#FFF0A0", 0.7)
    r.ellipse(22.4, -0.8, 1.5, 1.5, "#FFFBE0", stroke="#A8821A", width=0.3)
    for x, y in ((9, 18), (27, 17), (14, 22.6), (23, 22)):
        r.glow(x, y, 2.4, "#FFF6B0", 0.5)


def _moss(r):
    for x, y, rx in ((10, 10.6, 4.6), (24, 9.4, 4), (28.4, 17, 2.6)):
        r.ellipse(x, y, rx, rx * 0.5, "#3E8A3A", alpha=0.9, blur=0.5, clip=True)
        r.ellipse(x - 0.6, y - 0.5, rx * 0.5, rx * 0.22, "#8AD06A", alpha=0.8, clip=True)
    r.rect(17.2, 2.6, 1.6, 4, "#F6ECD6", stroke=OUT, width=0.25)
    r.path("M 14 3.4 Q 14.4 -0.6 18 -0.6 Q 21.6 -0.6 22 3.4 Q 18 4.6 14 3.4 Z", radial(16.6, 0.6, 5, (0, "#FF9A7A"), (1, "#B02A2A")), stroke="#4A0E14", width=0.3)
    r.ellipse(16.4, 1.4, 0.6, 0.45, "#FFFFFF")
    r.ellipse(19.6, 2.2, 0.45, 0.35, "#FFFFFF")


def _mint(r):
    for sx, a in ((-1, -0.5), (1, 0.4)):
        x = 18 + sx * 2.6
        r.path(f"M 18 6.6 Q {x + sx * 2} {1 + a} {x + sx * 5} 2 Q {x + sx * 3} 6 18 6.6 Z", linear(12, 0, 24, 7, (0, "#D8FFE8"), (1, "#3EA878")), stroke="#1B5040", width=0.3)
    r.path("M 9 19 Q 14 15 19 19 Q 24 23 28.6 18.6", None, stroke="#FFFFFF", width=0.9, alpha=0.5, clip=True)


def _coral(r):
    for x, s in ((11, 0.8), (18, 1.1), (25, 0.85)):
        b = 8.6 + abs(x - 18) * 0.25
        for d in (f"M {x} {b} L {x} {b - 6 * s}", f"M {x} {b - 2.4 * s} L {x - 2.4 * s} {b - 5 * s}", f"M {x} {b - 3.4 * s} L {x + 2.4 * s} {b - 6.4 * s}"):
            r.path(d, None, stroke="#7A1E3A", width=1.6 * s)
            r.path(d, None, stroke="#FF8AA8", width=1.0 * s)


def _pearl(r):
    r.ellipse(18, 3.6, 3.4, 3.4, radial(16.8, 2.4, 4.6, (0, "#FFFFFF"), (0.6, "#F0E4FF"), (1, "#A890D0")), stroke="#5A4880", width=0.35)
    r.ellipse(16.8, 2.4, 0.9, 0.7, "#FFFFFF")
    for k in range(4):
        r.path(f"M {7 + k * 2} 23.4 Q 18 {14 + k * 1.6} {29 - k * 2} 23.4", None, stroke="#FFFFFF", width=0.35, alpha=0.4, clip=True)


def _nebula(r):
    r.path("M 9 20 Q 13 12 20 14 Q 26 16 23 21 Q 20 24 17 21", None, stroke="#FFB0F0", width=1.4, alpha=0.45, blur=0.6, clip=True)
    for x, y, s in ((10, 13, 1.3), (25, 11, 1.0), (27, 20, 1.5), (15, 23, 0.9), (20, 9.6, 0.8)):
        star(r, x, y, s)
    star(r, 18, 2.6, 2.4, "#FFE9A3")
    r.glow(18, 2.6, 4, "#C8B0FF", 0.5)


def _rust(r):
    for x, y, rx in ((9.6, 12, 3.4), (25, 19, 4), (20, 9, 2.6)):
        r.ellipse(x, y, rx, rx * 0.6, "#4A1E08", alpha=0.6, blur=0.5, clip=True)
    for x, y in ((8, 20), (13, 9.6), (28.4, 13.6), (23.6, 23.6)):
        r.ellipse(x, y, 0.8, 0.8, "#D8DCE4", stroke="#3A2A20", width=0.25)
    pts = []
    for k in range(16):
        a, rad = k * math.pi / 8, (3.4 if k % 2 == 0 else 2.5)
        pts.append((18 + math.cos(a) * rad, 3.4 + math.sin(a) * rad))
    r.poly(pts, linear(15, 0, 21, 7, (0, "#E8C890"), (1, "#7A4A20")), stroke="#2A1006", width=0.3)
    r.ellipse(18, 3.4, 1.0, 1.0, "#2A1006")


def _sand(r):
    for y in (13, 17, 21):
        r.path(f"M 6 {y} Q 12 {y - 2} 18 {y} Q 24 {y + 2} 30 {y}", None, stroke="#8A5A1E", width=0.5, alpha=0.5, clip=True)
        r.path(f"M 6 {y + 0.9} Q 12 {y - 1.1} 18 {y + 0.9} Q 24 {y + 2.9} 30 {y + 0.9}", None, stroke="#FFF4C8", width=0.4, alpha=0.6, clip=True)


def _slate(r):
    for d in ("M 7 13 L 13 8 L 19 9.4 L 17 15 L 9 16.6 Z", "M 20.6 8.6 L 27 10.6 L 29.6 16 L 23 16.4 Z", "M 24 18 L 30 17.6 L 30 23 L 25 24 Z"):
        r.path(d, linear(7, 8, 30, 24, (0, "#D8E0EA"), (1, "#5A6472")), stroke="#1F252C", width=0.35, clip=True)
    r.path("M 11 10.6 L 13 13 L 12 15.4 M 25 11.6 L 26 14.6", None, stroke="#1F252C", width=0.3, alpha=0.7)


def _tide(r):
    r.path("M 15 7 Q 18 -1.6 23 2.4 Q 20 4 21.6 7 Z", linear(15, 0, 23, 7, (0, "#C8FFF4"), (1, "#18836B")), stroke="#0B2F2C", width=0.35)
    for sx in (-1, 1):
        r.path(f"M {18 + sx * 13.4} 17 L {18 + sx * 18} 13.6 L {18 + sx * 16.6} 20.6 Z", linear(0, 13, 0, 21, (0, "#C8FFF4"), (1, "#18836B")), stroke="#0B2F2C", width=0.35)
    r.path("M 7 21 Q 10 18.6 13 21 Q 16 23.4 19 21 Q 22 18.6 25 21 Q 27 22.6 29.6 21", None, stroke="#FFFFFF", width=0.6, alpha=0.6, clip=True)


def _amber(r):
    r.ellipse(22.6, 19.6, 1.9, 1.2, "#3A1E04", alpha=0.8)
    for sx in (-1, 0, 1):
        r.line(22.6 + sx * 1.1, 19.6, 22.6 + sx * 2.2, 21.6, "#3A1E04", 0.3, alpha=0.8)
        r.line(22.6 + sx * 1.1, 19.6, 22.6 + sx * 2.2, 17.8, "#3A1E04", 0.3, alpha=0.8)
    r.path("M 7.6 19 Q 8 11 14 8.6", None, stroke="#FFF4C0", width=1.6, alpha=0.5, blur=0.4, clip=True)


def _colossus(r):
    for sx in (-1, 1):
        r.path(f"M {18 + sx * 7} 8.6 Q {18 + sx * 12.6} 5 {18 + sx * 12} -1.6 Q {18 + sx * 8} 2.6 {18 + sx * 4} 7 Z", linear(0, -2, 0, 9, (0, "#C8B0A0"), (1, "#3A2A24")), stroke=OUT, width=0.4)
    _cracks(r, "#FF7A1A")
    r.path("M 18 5 Q 15 1.4 18.4 -1.6 Q 21 -4 19 -6.6", None, stroke="#8A8088", width=1.4, alpha=0.45, blur=0.7)


FEATURES = {"green": _sprout, "blue": _drop, "ember": _flames, "ice": _ice, "magma": _cracks, "char": _char, "glow": _lure, "moss": _moss, "mint": _mint,
            "coral": _coral, "pearl": _pearl, "nebula": _nebula, "rust": _rust, "sand": _sand, "slate": _slate, "tide": _tide, "amber": _amber, "colossus": _colossus}
ROYAL = {"amber_queen": "amber", "char_tyrant": "char", "coral_matron": "coral", "ice_warden": "ice", "magma_heart": "magma", "mint_matron": "mint",
         "moss_elder": "moss", "nebula_heart": "nebula", "pearl_empress": "pearl", "rust_baron": "rust", "cinder_colossus": "colossus"}
GIANT = {"gel_king": "blue", "astral_curator": "nebula", "frost_sovereign": "ice", "tide_regent": "tide"}


def slime_layers(r: Recipe, feature: str, royal: bool) -> None:
    r.shadow(18, 26, 15, 3.4, 0.36)
    r.path(SLIME, radial(13, 11, 23, (0, "$p.light"), (0.45, "$p.body"), (1, "$p.dark")), stroke=OUT, width=0.5)
    r.ellipse(18, 20, 10, 4.6, "$p.light", alpha=0.45, blend="add", blur=2.0, clip=True)  # the light that passes through the jelly
    r.shade("M 20 6.2 Q 33 8 32 22 Q 32 26.5 18 26.5 Q 10 26.5 6.6 25 Q 26 24 20 6.2 Z", 0.4, blur=1.6)
    for x, y, rad in ((24, 13, 1.1), (27, 19, 0.8), (21, 22.6, 0.6), (9, 21, 0.7)):  # bubbles
        r.ellipse(x, y, rad, rad, None, stroke="#FFFFFF", width=0.25, alpha=0.5)
        r.ellipse(x - rad * 0.3, y - rad * 0.3, rad * 0.3, rad * 0.3, "#FFFFFF", alpha=0.6)
    FEATURES[feature](r)
    r.path("M 6.6 15 Q 8.4 8.8 15.6 7.4", None, stroke="#FFFFFF", width=1.3, alpha=0.6, blur=0.35, clip=True)  # the rim of light
    r.ellipse(10.6, 11.8, 2.5, 1.5, "#FFFFFF", alpha=0.85)
    r.ellipse(14.6, 9.2, 0.8, 0.5, "#FFFFFF", alpha=0.85)
    for x in (13, 23):  # the eyes
        r.ellipse(x, 17.2, 1.7, 2.3, "$p.eye", stroke=OUT, width=0.25)
        r.ellipse(x - 0.5, 16.2, 0.6, 0.75, "#FFFFFF")
        r.ellipse(x + 0.5, 18.4, 0.3, 0.35, "#FFFFFF", alpha=0.8)
    r.path("M 16.6 20.4 Q 18 21.6 19.4 20.4", None, stroke=OUT, width=0.4)
    for x in (9.6, 26.4):
        r.ellipse(x, 19.8, 1.5, 0.7, "#FF6A8A", alpha=0.3, blur=0.4)
    if royal:
        for k in range(7):  # a necklace of beads
            t = k / 6
            x, y = 9.6 + t * 16.8, 22.6 + math.sin(t * math.pi) * 1.9
            r.ellipse(x, y, 0.9, 0.9, radial(x - 0.3, y - 0.3, 1.2, (0, "#FFF8D0"), (1, "#B8862A")), stroke="#5A3A08", width=0.2)
        crown(r, 18, 7.4, 5.2, 5.6)


def slime(name: str, feature: str, royal: bool = False) -> Recipe:
    r = new(name, 36, 34, (18, 30))
    slime_layers(r, feature, royal)
    r.layers = transform_layers(r.layers, 1.0, 0, 4)
    return r


def giant_slime(name: str, feature: str) -> Recipe:
    r = new(name, 76, 74, (38, 66))
    slime_layers(r, feature, False)
    crown(r, 18, 7.4, 6.4, 7.4, "#4A7AE0")
    r.layers = transform_layers(r.layers, 2.0, 2, 14)
    return r


# ------------------------------------------------------------------------------------------------ wolves and the game of the hunt
def beast(r: Recipe, tail: str = "bushy", ears: float = 1.0, snout: bool = False) -> None:
    """A four-legged beast from the side, looking to the left, on the ground at y 40 (canvas 56 x 44)."""
    fur = linear(0, 10, 0, 34, (0, "$p.light"), (0.4, "$p.fur"), (1, "$p.dark"))
    r.shadow(29, 40, 19, 3.6, 0.36)
    if tail == "bushy":
        r.path("M 42 20 Q 50 16 52.6 6 Q 53.6 14 51 20 Q 48 25 43 25 Z", fur, stroke=OUT, width=0.45)
        r.path("M 46 19 Q 50 15 51.6 10", None, stroke="$p.light", width=0.8, alpha=0.7, clip=True)
    elif tail == "curl":
        r.path("M 45 20 Q 49 18 48.6 15 Q 47.6 13.4 46.4 15", None, stroke=OUT, width=1.6)
        r.path("M 45 20 Q 49 18 48.6 15 Q 47.6 13.4 46.4 15", None, stroke="$p.fur", width=0.9)
    else:
        r.path("M 44.6 19 Q 47.6 18.4 48 21 Q 46.6 22.4 44.6 22 Z", fur, stroke=OUT, width=0.4)
    for d in ("M 24.6 27 L 29 27 L 28 35.4 L 29.4 39.6 L 24.6 39.6 L 25.2 35 Z", "M 33 27 L 37.6 27 L 36.6 34.6 L 38 39.6 L 33.2 39.6 L 33.8 34 Z"):  # the far legs
        r.path(d, "$p.dark", stroke=OUT, width=0.45)
    body = "M 15.6 19 Q 20 12 31 13.6 Q 42 12.4 45.4 18.6 Q 47.6 25.6 43.6 30 Q 34 33.4 24 31.4 Q 16.6 29.6 15.6 19 Z"
    r.path(body, fur, stroke=OUT, width=0.45)
    r.shade("M 16.6 26 Q 30 30 46 24 Q 46 29 43.6 30 Q 34 33.4 24 31.4 Q 18 30 16.6 26 Z", 0.45, blur=1.0)
    for d in ("M 18.6 26.6 L 24 26.6 L 23 35.4 L 24.6 39.6 L 19.2 39.6 L 19.8 35 Z", "M 37.4 24.6 Q 44 26 43.4 30.6 L 41.6 35 L 43.2 39.6 L 37.8 39.6 L 38.4 34 L 36.2 30 Z"):  # the near legs
        r.path(d, fur, stroke=OUT, width=0.45)
    for x in (21.8, 40.4):
        r.path(f"M {x - 2.6} 38.2 L {x + 2.6} 38.2 L {x + 2.8} 39.6 L {x - 2.8} 39.6 Z", "$p.dark", alpha=0.7)
    r.path("M 13 18 Q 16 10.6 22.6 13 L 24.6 24.6 Q 19 28 15 23.6 Z", fur, stroke=OUT, width=0.45)  # the neck and its ruff
    for k in range(4):
        y = 17 + k * 2.2
        r.path(f"M {15.6 + k * 0.6} {y} L {13.6 + k * 0.8} {y + 2.6} L {17.6 + k * 0.6} {y + 1.4} Z", "$p.light", alpha=0.8)
    e = ears
    r.path(f"M 16.4 10.4 L {19.4} {10 - 6 * e} L 20.8 11 Z", "$p.dark", stroke=OUT, width=0.4)  # the far ear
    head = "M 2.6 17.4 L 7.6 13.6 Q 9.8 9.4 15 9.4 Q 20.2 10 20.6 15 Q 20.6 20.2 15 21.2 L 8.6 21.2 Q 4 20.6 2.6 17.4 Z"
    r.path(head, fur, stroke=OUT, width=0.45)
    r.shade("M 4 19.4 Q 12 20.4 20.4 17 Q 20 20.4 15 21.2 L 8.6 21.2 Q 5.4 20.8 4 19.4 Z", 0.4, blur=0.5)
    r.path("M 2.8 17.6 Q 6 16.4 9.6 17.6 Q 8 20.4 5 20.2 Q 3.4 19.4 2.8 17.6 Z", "$p.light", alpha=0.7)  # the muzzle
    r.path(f"M 12.6 10.6 L {14.2} {10.2 - 6.6 * e} L 17.6 9.8 Z", fur, stroke=OUT, width=0.45)  # the near ear
    r.path(f"M 13.6 10.2 L {14.6} {10.4 - 4.4 * e} L 16.4 9.9 Z", "$p.inner")
    r.glow(11.9, 14.4, 2.6, "$p.eye", 0.35)
    r.path("M 10.2 14.6 Q 11.8 12.8 13.8 14 Q 12.4 15.6 10.2 14.6 Z", "$p.eye", stroke=OUT, width=0.35)  # the eye
    r.ellipse(11.9, 14.3, 0.45, 0.7, OUT)
    r.ellipse(11.5, 13.9, 0.25, 0.25, "#FFFFFF")
    r.path("M 9.6 12.8 L 14.4 12.6", None, stroke=OUT, width=0.45)  # the brow
    if snout:
        r.ellipse(3.2, 17.6, 1.9, 2.3, "$p.inner", stroke=OUT, width=0.4)
        for y in (16.8, 18.4):
            r.ellipse(3, y, 0.35, 0.45, OUT)
    else:
        r.ellipse(3.2, 17.2, 1.2, 0.95, "$p.nose")
        r.ellipse(2.9, 16.9, 0.35, 0.25, "#FFFFFF", alpha=0.6)
    r.path("M 4 19.6 Q 7.6 20.8 11 19.4", None, stroke=OUT, width=0.35)
    r.poly([(5.6, 19.8), (6.4, 19.9), (6, 21.2)], "#FFFFFF", stroke=OUT, width=0.15)


def _blaze(r):
    r.path("M 14.6 19 Q 16 24 19.6 26.4 Q 21 22 18.6 18 Z", "#FFFFFF", alpha=0.85)
    r.path("M 9.6 11.4 L 12 9.8 L 12.6 12.4 Z", "#FFFFFF", alpha=0.85)


def _scar(r):
    r.path("M 10 11.4 L 13.4 16.6", None, stroke="#C83A3A", width=0.6)
    r.path("M 14 21.6 Q 18 24.6 23.4 22.6 L 23.6 24.6 Q 18 26.8 13.8 23.6 Z", "#3A2A24", stroke=OUT, width=0.35)
    for x, y in ((15.6, 23.4), (18.6, 24.6), (21.6, 24)):
        r.poly([(x - 0.7, y), (x + 0.7, y), (x, y + 2.2)], "#D8DCE4", stroke=OUT, width=0.2)


def _scarf(r):
    r.path("M 13.6 19.6 Q 18 23.6 24 21 L 24.4 24 Q 18 27 13.4 22.6 Z", linear(13, 19, 24, 27, (0, "#F0C068"), (1, "#B8742A")), stroke=OUT, width=0.35)
    r.path("M 21 23 L 26 29.6 L 22.6 29 L 20 25 Z", "#D89A48", stroke=OUT, width=0.35)
    r.path("M 6.6 16 L 9 17 M 6.6 17.6 L 8.6 18.4", None, stroke="#6A3A10", width=0.4)


def _shards(r):
    for x, h, lean in ((24, 7, -1), (30, 9, 0.6), (36, 7, 1.4), (41, 5, 2)):
        crystal(r, x, 14.6, h, 1.7, lean)
    crystal(r, 15, 6, 3.4, 0.9, 0.3)


def _ruff(r):
    for k in range(7):
        a = k / 6
        x, y = 13.6 + a * 9, 17.6 + math.sin(a * math.pi) * 8.4
        r.path(f"M {x - 1.4} {y - 1.6} L {x - 2.8} {y + 2.6} L {x + 1.6} {y + 0.8} Z", "#FFFFFF", stroke="#9FB8D8", width=0.25)
    r.ellipse(5, 18.6, 3, 1.6, "#FFFFFF", alpha=0.7, blur=0.4)


def _wisps(r):
    for x, y in ((26, 11), (36, 10), (46, 14), (50, 5)):
        r.path(f"M {x} {y + 3} Q {x - 2.6} {y} {x + 0.6} {y - 2.6} Q {x + 2.6} {y - 5} {x + 1} {y - 7}", None, stroke="#6A4AA8", width=1.4, alpha=0.5, blur=0.6)
    r.glow(11.9, 14.4, 4.6, "$p.eye", 0.5)


def _bolts(r):
    for d in ("M 26 15 L 29 19.6 L 27 20.6 L 30.6 26", "M 36 15 L 38.6 19 L 36.8 20 L 40 25"):
        r.path(d, None, stroke="#FFF35A", width=1.8, alpha=0.5, blend="add", blur=0.6)
        r.path(d, None, stroke="#FFFBD0", width=0.6)


def _stripes(r):
    for x in (23, 27.6, 32.2, 36.8, 41):
        r.path(f"M {x} 13.6 Q {x + 1.6} 18.6 {x - 0.6} 24 Q {x + 2.8} 19 {x + 1.6} 13.6 Z", "#3A220C", alpha=0.75, clip=True)


def _tusks(r):
    for k in range(8):  # a bristly mane
        x = 16 + k * 3.2
        r.path(f"M {x} 14 L {x + 0.6} {9.6 - (k % 2)} L {x + 2.4} 13.6 Z", "$p.dark", stroke=OUT, width=0.25)
    r.path("M 6 19.6 Q 4.4 17.6 5.6 15 L 6.6 15.8 Q 6 17.6 7.2 19 Z", "#FFF8E8", stroke=OUT, width=0.3)


def _antlers(r):
    for dx, c in ((2.4, "$p.dark"), (0, "#E8D8B8")):
        for d in (f"M {15 + dx} 9.6 Q {13 + dx} 3 {17 + dx} -3.4", f"M {14.2 + dx} 4.6 L {10.4 + dx} 1", f"M {15.2 + dx} 1 L {12.4 + dx} -3.4", f"M {16 + dx} 4 L {20 + dx} 1.6"):
            r.path(d, None, stroke=OUT, width=1.7)
            r.path(d, None, stroke=c, width=1.0)
    r.path("M 13.6 19.6 Q 16 25 20 27 Q 21 22.6 18.6 18.6 Z", "#F4E4C8", alpha=0.85)


def _fox(r):
    r.path("M 49 13 Q 52 9 52.6 6 Q 53.6 12 51.6 17 Z", "#FFFFFF", stroke=OUT, width=0.3)
    r.path("M 2.8 17.6 Q 7 15.6 11 18.6 Q 9 21 5 20.4 Z", "#FFFFFF", alpha=0.9)
    r.path("M 13.6 19.6 Q 16 25 20 27 Q 21 22.6 18.6 18.6 Z", "#FFFFFF", alpha=0.85)


BEASTS = {"wolf_grey": (_blaze, {}), "wolf_dire": (_scar, {}), "wolf_dune": (_scarf, {}), "wolf_frost": (_shards, {}), "wolf_polar": (_ruff, {}),
          "wolf_shade": (_wisps, {}), "wolf_storm": (_bolts, {}), "wolf_tawny": (_stripes, {}),
          "wild_boar": (_tusks, {"tail": "curl", "ears": 0.55, "snout": True}), "ridge_elk": (_antlers, {"tail": "stub", "ears": 0.7}),
          "dune_fox": (_fox, {"ears": 1.45})}


def _bone_crest(r):
    _scar(r)
    for x in (25, 30, 35, 40):
        r.poly([(x - 1.2, 14.4), (x + 1.2, 14.4), (x + 0.4, 9)], "#F0E8D0", stroke=OUT, width=0.3)


def _headdress(r):
    _scarf(r)
    r.path("M 9 11.6 Q 13 8.4 18 10 L 17.6 11.8 Q 13 10.4 9.6 13 Z", GOLD, stroke="#5A3A08", width=0.3)
    r.ellipse(12.6, 10.4, 1.0, 1.0, "#E0302A", stroke="#5A3A08", width=0.25)


def _crescent(r):
    _wisps(r)
    r.path("M 11 6.4 Q 14 9.4 17.6 6.4 Q 14 11.4 11 6.4 Z", "#E8F4FF", stroke="#5A6A9A", width=0.3)
    r.glow(14.2, 7.6, 5, "#A8D8FF", 0.5)


def _ice_crown(r):
    _ruff(r)
    for x, h in ((10.6, 4.4), (13.6, 6.4), (16.6, 4.4)):
        crystal(r, x, 9.8, h, 1.2)


def _storm_crown(r):
    _bolts(r)
    r.path("M 9.6 9 L 12 3.4 L 13 7 L 15.6 2 L 16 7.4 L 19 4.4 L 18.6 10", None, stroke="#FFF35A", width=1.6, alpha=0.5, blend="add", blur=0.5)
    r.path("M 9.6 9 L 12 3.4 L 13 7 L 15.6 2 L 16 7.4 L 19 4.4 L 18.6 10", None, stroke="#FFFBD0", width=0.6)


ALPHAS = {"dire_alpha": _bone_crest, "dune_mother": _headdress, "moonshade_alpha": _crescent, "polar_king": _ice_crown, "storm_sovereign": _storm_crown}


def wolf(name: str, feature, alpha: bool = False, **kw) -> Recipe:
    r = new(name, 72, 58, (36, 51)) if alpha else new(name, 56, 50, (28, 46))
    beast(r, **kw)
    feature(r)
    r.faces = "left"
    r.layers = transform_layers(r.layers, 1.25, 0, 1) if alpha else transform_layers(r.layers, 1.0, 0, 6)
    return r


# ------------------------------------------------------------------------------------------------ the guardians in armor
def knight(r: Recipe) -> None:
    """A guardian in full armor, standing in front of you (canvas 56 x 64, the feet at y 60)."""
    steel = linear(14, 0, 42, 0, (0, "$p.light"), (0.4, "$p.body"), (1, "$p.dark"))
    r.shadow(28, 60, 19, 4, 0.4)
    r.path("M 13 22 Q 6 42 9 58 Q 28 61 47 58 Q 50 42 43 22 Z", linear(0, 22, 0, 60, (0, "$p.dark"), (1, "$p.outline")), stroke=OUT, width=0.5)  # the cape
    for x in (19.4, 29.6):  # the legs
        r.path(f"M {x} 43 L {x + 7} 43 L {x + 6.4} 55 L {x + 7.6} 59.6 L {x - 0.6} 59.6 L {x + 0.6} 55 Z", steel, stroke=OUT, width=0.5)
        r.path(f"M {x + 0.4} 49 Q {x + 3.5} 51.4 {x + 6.6} 49", None, stroke=OUT, width=0.4)
        r.ellipse(x + 3.5, 47, 2.6, 1.9, "$p.light", stroke=OUT, width=0.35)
    for sx in (-1, 1):  # the arms and the gauntlets
        x = 28 + sx * 16.6
        r.path(f"M {x - 3.4} 24 L {x + 3.4} 24 L {x + 3} 38 L {x - 3} 38 Z", steel, stroke=OUT, width=0.5)
        r.path(f"M {x - 3.8} 36.4 L {x + 3.8} 36.4 L {x + 3.4} 44.6 Q {x} 46.6 {x - 3.4} 44.6 Z", steel, stroke=OUT, width=0.5)
        r.path(f"M {x - 2.4} 41.6 L {x + 2.4} 41.6", None, stroke=OUT, width=0.3)
    r.path("M 16.6 38 Q 28 43.6 39.4 38 L 41 47 Q 28 52 15 47 Z", steel, stroke=OUT, width=0.5)  # the fauld
    r.path("M 22 41 L 21 49 M 28 42 L 28 50.6 M 34 41 L 35 49", None, stroke=OUT, width=0.35, alpha=0.7)
    r.path("M 15.6 22 Q 28 17 40.4 22 L 38.6 39 Q 28 44.6 17.4 39 Z", steel, stroke=OUT, width=0.5)  # the breastplate
    r.path("M 28 20.6 L 28 42", None, stroke=OUT, width=0.35, alpha=0.6)
    r.path("M 18.6 23.6 Q 19 32 20.6 38", None, stroke="#FFFFFF", width=0.9, alpha=0.4, blur=0.3)
    r.path("M 17 37 Q 28 42.4 39 37 L 39.2 39.4 Q 28 44.8 16.8 39.4 Z", "$p.dark", stroke=OUT, width=0.35)  # the belt
    for sx in (-1, 1):  # the pauldrons
        x = 28 + sx * 15
        r.path(f"M {x - sx * 6.4} 22 Q {x - sx * 4} 15 {x + sx * 3} 16.6 Q {x + sx * 8.6} 19 {x + sx * 7.6} 27 Q {x} 28.6 {x - sx * 6.4} 22 Z", steel, stroke=OUT, width=0.5)
        r.path(f"M {x - sx * 4} 24 Q {x + sx * 2} 26 {x + sx * 7} 23.6", None, stroke=OUT, width=0.35, alpha=0.7)
    r.shade("M 29 17 L 52 17 L 50 60 L 29 60 Z", 0.4, blur=1.4)
    for sx in (-1, 1):  # the horns of the helm
        r.path(f"M {28 + sx * 7.6} 9 Q {28 + sx * 14.6} 8 {28 + sx * 15.6} 0.6 Q {28 + sx * 10} 3.4 {28 + sx * 7} 5.4 Z", linear(0, 0, 0, 9, (0, "$p.bone"), (1, "$p.dark")), stroke=OUT, width=0.45)
    r.path("M 18.6 12 Q 18.6 2.6 28 2.6 Q 37.4 2.6 37.4 12 L 36.4 20.6 Q 28 24 19.6 20.6 Z", steel, stroke=OUT, width=0.5)  # the helm
    r.path("M 28 2.6 L 28 9.6", None, stroke=OUT, width=0.5)
    r.path("M 21.6 10.6 L 34.4 10.6 L 33.6 13.6 L 28 15 L 22.4 13.6 Z", "$p.slit", stroke=OUT, width=0.35)  # the visor
    for x in (24.6, 31.4):
        r.glow(x, 12, 4, "$p.glow", 0.7)
        r.path(f"M {x - 1.6} 11.4 L {x + 1.6} 11.4 L {x + 1.2} 12.8 L {x - 1.2} 12.8 Z", "$p.glow")
        r.ellipse(x, 12, 0.5, 0.4, "#FFFFFF", alpha=0.9)
    for x in (25, 27, 29, 31):
        r.line(x, 16.6, x, 19.6, "$p.slit", 0.5)
    r.path("M 20.6 9 Q 22 4.6 26 3.6", None, stroke="#FFFFFF", width=0.8, alpha=0.5, blur=0.25)


def _skull(r):
    r.path("M 24 26 Q 24 22 28 22 Q 32 22 32 26 Q 32 28.4 30.6 29 L 30.6 31 L 25.4 31 L 25.4 29 Q 24 28.4 24 26 Z", "$p.bone", stroke=OUT, width=0.4)
    for x in (26.4, 29.6):
        r.ellipse(x, 26.2, 1.0, 1.2, "$p.slit")
    for sx in (-1, 1):
        for k in range(3):
            x = 28 + sx * (11 + k * 3.2)
            r.poly([(x - 1.1, 18.6 + k), (x + 1.1, 18.6 + k), (x + sx * 0.8, 12 + k * 1.6)], "$p.bone", stroke=OUT, width=0.3)


def _tricorn(r):
    r.path("M 13 6.6 Q 28 -3.4 43 6.6 Q 36 9.6 28 6 Q 20 9.6 13 6.6 Z", linear(0, -3, 0, 9, (0, "#3A5A64"), (1, "#0E2428")), stroke=OUT, width=0.5)
    r.path("M 15 6.4 Q 28 -1.4 41 6.4", None, stroke=GOLD, width=0.6)
    r.path("M 28 24 L 28 35 M 24 27 L 32 27 M 23 32 Q 28 38 33 32", None, stroke="$p.bone", width=1.2)
    r.ellipse(28, 23.4, 1.3, 1.3, None, stroke="$p.bone", width=0.8)
    for x, y in ((19, 30), (37, 26), (21, 46), (36, 44), (44, 20)):
        r.ellipse(x, y, 1.1, 0.9, "#C8D8C0", stroke=OUT, width=0.25)


def _hammer(r):
    r.path("M 44 46 L 49 10", None, stroke=OUT, width=2.4)
    r.path("M 44 46 L 49 10", None, stroke="#6A4426", width=1.6)
    r.path("M 42.6 3 L 55 5 L 54 14.6 L 41.6 12.6 Z", linear(42, 3, 55, 15, (0, "#E8ECF4"), (0.5, "#7A808E"), (1, "#2A2E3A")), stroke=OUT, width=0.5)
    for x, y in ((10, 12), (48, 22), (6, 30), (38, 2)):
        r.glow(x, y, 2.6, "#FF8A30", 0.6)
        r.ellipse(x, y, 0.5, 0.5, "#FFE080")


def _hardhat(r):
    r.path("M 17.6 8.6 Q 18 0.6 28 0.6 Q 38 0.6 38.4 8.6 Q 28 6.6 17.6 8.6 Z", linear(0, 0, 0, 9, (0, "#FFE070"), (1, "#C8861E")), stroke=OUT, width=0.5)
    r.glow(28, 4.6, 9, "#FFF0A0", 0.6)
    r.ellipse(28, 4.6, 2.2, 2.2, "#FFFBE0", stroke=OUT, width=0.4)
    pts = []
    for k in range(16):
        a, rad = k * math.pi / 8, (5 if k % 2 == 0 else 3.8)
        pts.append((28 + math.cos(a) * rad, 30 + math.sin(a) * rad))
    r.poly(pts, linear(23, 25, 33, 35, (0, "#FFE0A0"), (1, "#8A5A20")), stroke=OUT, width=0.4)
    r.ellipse(28, 30, 1.6, 1.6, "$p.slit")


def _rime(r):
    for sx in (-1, 1):
        for k, h in enumerate((9, 12, 8)):
            crystal(r, 28 + sx * (10 + k * 3.6), 18.6 + k * 0.8, h, 1.7, sx * 1.2)
    for x, y in ((22, 30), (34, 27), (20, 48), (37, 52), (28, 36)):
        star(r, x, y, 1.6, "#FFFFFF", 0.85)
    r.rect(15, 20, 26, 22, "#DFF4FF", alpha=0.2, blur=1.2, clip=True)


def _turban(r):
    r.path("M 17.6 9.6 Q 17 0.6 28 0.6 Q 39 0.6 38.4 9.6 Q 28 6.6 17.6 9.6 Z", linear(0, 0, 0, 10, (0, "#FFF8E0"), (1, "#C8A870")), stroke=OUT, width=0.5)
    r.path("M 19 6.6 Q 28 2.6 37 6.6 M 20 3.6 Q 28 0.6 36 3.6", None, stroke="#8A6A3A", width=0.4)
    r.ellipse(28, 5.6, 1.5, 1.8, "#4FE0D0", stroke=OUT, width=0.35)
    r.path("M 47 60 L 49.6 6", None, stroke=OUT, width=1.9)
    r.path("M 47 60 L 49.6 6", None, stroke="#8A6A3A", width=1.2)
    r.path("M 49.8 -3 L 52.6 6 L 49.6 9 L 46.8 5.6 Z", linear(47, -3, 53, 9, (0, "#FFFFFF"), (1, "#8A8E9A")), stroke=OUT, width=0.4)


def _keys(r):
    r.rect(24, 26, 8, 7, linear(24, 26, 32, 33, (0, "#FFE898"), (1, "#8A6A1E")), stroke=OUT, width=0.4)
    r.path("M 25.4 26 Q 25.4 21.6 28 21.6 Q 30.6 21.6 30.6 26", None, stroke="#C8A040", width=1.1)
    r.ellipse(28, 28.6, 1.0, 1.0, "$p.slit")
    r.rect(27.6, 29, 0.8, 2.4, "$p.slit")
    r.ellipse(40.6, 42, 2.6, 2.6, None, stroke="#C8A040", width=0.7)
    for a in (0.3, 0.9, 1.5):
        x, y = 40.6 + math.cos(a) * 6, 44.6 + math.sin(a) * 6
        r.line(40.6 + math.cos(a) * 2.4, 42.6 + math.sin(a) * 2.4, x, y, "#E8C860", 0.7)
        r.ellipse(x, y, 1.1, 1.1, None, stroke="#E8C860", width=0.6)
    r.path("M 24 3 L 28 -2.4 L 32 3 Z", "$p.glow", stroke=OUT, width=0.4)


KNIGHTS = {"barrow_warden": _skull, "drowned_captain": _tricorn, "forge_tyrant": _hammer, "iron_foreman": _hardhat, "rime_revenant": _rime,
           "sand_sentinel": _turban, "vault_warden": _keys}


def guardian(name: str, feature) -> Recipe:
    r = new(name, 64, 74, (32, 68))
    knight(r)
    feature(r)
    r.layers = transform_layers(r.layers, 1.0, 4, 8)
    return r


# ------------------------------------------------------------------------------------------------ the others
def cave_bat() -> Recipe:
    r = new("cave_bat", 52, 40, (26, 36))
    r.shadow(26, 36, 10, 2.2, 0.25)
    for sx in (-1, 1):
        wing = (f"M {26 + sx * 4} 16 Q {26 + sx * 12} 4 {26 + sx * 24} 7 Q {26 + sx * 22} 12 {26 + sx * 23.6} 17 Q {26 + sx * 19} 15.6 {26 + sx * 17} 20 "
                f"Q {26 + sx * 13} 18 {26 + sx * 11} 22.6 Q {26 + sx * 8} 20.6 {26 + sx * 4.6} 22 Z")
        r.path(wing, linear(26, 4, 26, 23, (0, "$p.light"), (0.5, "$p.wing"), (1, "$p.dark")), stroke=OUT, width=0.45)
        for tx, ty in ((23.6, 17), (17, 20), (11, 22.6)):
            r.path(f"M {26 + sx * 6} 14 L {26 + sx * tx} {ty}", None, stroke=OUT, width=0.35, alpha=0.7)
        r.path(f"M {26 + sx * 3} 9 L {26 + sx * 6} 1.6 L {26 + sx * 7} 9.6 Z", "$p.body", stroke=OUT, width=0.45)  # an ear
        r.path(f"M {26 + sx * 4.2} 8.6 L {26 + sx * 5.8} 4 L {26 + sx * 6.2} 9 Z", "#E88AA0")
    r.path("M 20.6 16 Q 20 8 26 8 Q 32 8 31.4 16 Q 31.6 25 26 26.6 Q 20.4 25 20.6 16 Z", radial(23.6, 12, 14, (0, "$p.light"), (0.5, "$p.body"), (1, "$p.dark")), stroke=OUT, width=0.45)
    for k in range(5):
        x = 22.6 + k * 1.7
        r.path(f"M {x} 19.6 L {x + 0.8} 22.6 L {x + 1.7} 19.6", None, stroke="$p.light", width=0.35, alpha=0.8)
    for sx in (-1, 1):
        x = 26 + sx * 2.5
        r.glow(x, 13.4, 3, "$p.eye", 0.6)
        r.ellipse(x, 13.4, 1.3, 1.5, "$p.eye", stroke=OUT, width=0.3)
        r.ellipse(x - 0.3, 13, 0.4, 0.45, "#FFFFFF")
        r.poly([(x - 0.6, 17), (x + 0.6, 17), (x, 19.4)], "$p.fang", stroke=OUT, width=0.2)
    r.ellipse(26, 15.6, 0.9, 0.6, "$p.dark")
    return r


def cave_spider() -> Recipe:
    r = new("cave_spider", 52, 38, (26, 33))
    r.shadow(26, 33, 19, 3.4, 0.34)
    r.line(30, 0, 30, 9, "#E8E8F0", 0.3, alpha=0.7)
    for sx in (-1, 1):
        for k, (kx, ky, fx, fy) in enumerate(((9, 9, 17, 31), (13, 12, 22, 32), (12, 20, 19, 33), (9, 15, 23.6, 24))):
            d = f"M {26 + sx * 5} {19 + k} L {26 + sx * kx} {ky} L {26 + sx * fx} {fy}"
            r.path(d, None, stroke=OUT, width=2.0)
            r.path(d, None, stroke="$p.body", width=1.2)
            r.path(d, None, stroke="$p.light", width=0.3, alpha=0.7)
    r.ellipse(30, 17, 9.6, 8, radial(26.6, 13, 13, (0, "$p.light"), (0.5, "$p.body"), (1, "$p.dark")), stroke=OUT, width=0.5)  # the abdomen
    r.path("M 30 12.6 L 32.6 16 L 30 19.4 L 27.4 16 Z M 30 19.4 L 31.6 22 L 30 24 L 28.4 22 Z", "$p.mark", stroke=OUT, width=0.3)
    r.ellipse(20, 22, 6, 5, radial(18, 19.6, 8, (0, "$p.light"), (0.5, "$p.body"), (1, "$p.dark")), stroke=OUT, width=0.5)  # the head
    for x, y, rad in ((17, 20.6, 1.2), (20.6, 20, 1.2), (15.6, 22.8, 0.7), (22.6, 22.2, 0.7)):
        r.glow(x, y, rad * 2, "$p.eye", 0.6)
        r.ellipse(x, y, rad, rad, "$p.eye", stroke=OUT, width=0.25)
        r.ellipse(x - rad * 0.3, y - rad * 0.3, rad * 0.3, rad * 0.3, "#FFFFFF")
    for x in (17.4, 20.4):
        r.path(f"M {x - 0.7} 25.6 L {x + 0.7} 25.6 L {x} 28.6 Z", "$p.fang", stroke=OUT, width=0.25)
    return r


def dune_scorpion() -> Recipe:
    r = new("dune_scorpion", 56, 42, (28, 37))
    shell = linear(0, 8, 0, 36, (0, "$p.light"), (0.5, "$p.body"), (1, "$p.dark"))
    r.shadow(28, 37, 20, 3.4, 0.34)
    for sx in (-1, 1):
        for k in range(3):
            d = f"M {28 + sx * 7} {26 + k * 2.4} L {28 + sx * (14 + k)} {23.6 + k * 3} L {28 + sx * (17 + k)} {33 + k}"
            r.path(d, None, stroke=OUT, width=1.9)
            r.path(d, None, stroke="$p.body", width=1.1)
        r.path(f"M {28 + sx * 7} 24 Q {28 + sx * 15} 20 {28 + sx * 17} 13", None, stroke=OUT, width=3.2)
        r.path(f"M {28 + sx * 7} 24 Q {28 + sx * 15} 20 {28 + sx * 17} 13", None, stroke="$p.body", width=2.2)
        cx = 28 + sx * 19
        r.path(f"M {cx - sx * 4} 13.6 Q {cx - sx * 5} 6 {cx + sx * 1} 4 Q {cx + sx * 6} 5 {cx + sx * 5.6} 11 L {cx + sx * 2} 8.6 L {cx + sx * 2.6} 14 Q {cx - sx * 1} 16.6 {cx - sx * 4} 13.6 Z", shell, stroke=OUT, width=0.45)
    tail = "M 28 22 Q 30 12 36 9 Q 42 6 41 0.6"
    r.path(tail, None, stroke=OUT, width=4.6)
    r.path(tail, None, stroke="$p.body", width=3.6)
    for x, y in ((29.4, 16), (33, 11), (38, 7.6), (41, 4)):
        r.ellipse(x, y, 2.3, 2.1, shell, stroke=OUT, width=0.35)
    r.path("M 41 2 Q 46 0.6 44 -3.6 Q 43 -0.6 39.6 -0.4 Z", "$p.sting", stroke=OUT, width=0.4)
    r.glow(44, -3, 3, "$p.sting", 0.5)
    r.path("M 19 27 Q 19 19 28 19 Q 37 19 37 27 Q 37 34.6 28 35 Q 19 34.6 19 27 Z", shell, stroke=OUT, width=0.5)
    for y in (24, 27.6, 31):
        r.path(f"M 20.4 {y} Q 28 {y + 2} 35.6 {y}", None, stroke=OUT, width=0.35, alpha=0.7)
    r.shade("M 29 19 Q 37 19 37 27 Q 37 34.6 28 35 Q 33 28 29 19 Z", 0.35)
    for x in (25.6, 30.4):
        r.ellipse(x, 22, 0.8, 0.9, "$p.eye")
        r.ellipse(x - 0.25, 21.7, 0.25, 0.25, "#FFFFFF")
    return r


def shore_crab() -> Recipe:
    r = new("shore_crab", 52, 36, (26, 32))
    shell = radial(21, 14, 20, (0, "$p.light"), (0.5, "$p.body"), (1, "$p.dark"))
    r.shadow(26, 32, 19, 3.2, 0.34)
    for sx in (-1, 1):
        for k in range(3):
            d = f"M {26 + sx * 10} {22 + k * 2} L {26 + sx * (17 + k)} {21 + k * 3} L {26 + sx * (19 + k)} {29.6 + k}"
            r.path(d, None, stroke=OUT, width=2.0)
            r.path(d, None, stroke="$p.claw", width=1.2)
        r.path(f"M {26 + sx * 9} 18 Q {26 + sx * 15} 14 {26 + sx * 16} 10", None, stroke=OUT, width=3.0)
        r.path(f"M {26 + sx * 9} 18 Q {26 + sx * 15} 14 {26 + sx * 16} 10", None, stroke="$p.claw", width=2.0)
        cx = 26 + sx * 18
        r.path(f"M {cx - sx * 4.6} 10 Q {cx - sx * 5} 2.6 {cx + sx * 1.6} 1 Q {cx + sx * 6.6} 2.6 {cx + sx * 5.6} 8 L {cx + sx * 1.6} 5.6 L {cx + sx * 2.6} 11 Q {cx - sx * 1.6} 13.6 {cx - sx * 4.6} 10 Z",
               linear(0, 1, 0, 13, (0, "$p.light"), (1, "$p.claw")), stroke=OUT, width=0.45)
        r.line(26 + sx * 3.4, 13, 26 + sx * 4.6, 8, OUT, 0.8)
        r.ellipse(26 + sx * 4.8, 7.4, 1.6, 1.6, "#FFFFFF", stroke=OUT, width=0.35)
        r.ellipse(26 + sx * 4.8, 7.6, 0.8, 0.9, "$p.eye")
    r.path("M 12.6 21 Q 12.6 11.6 26 11.6 Q 39.4 11.6 39.4 21 Q 39.4 28.6 26 29 Q 12.6 28.6 12.6 21 Z", shell, stroke=OUT, width=0.5)
    r.shade("M 27 11.6 Q 39.4 11.6 39.4 21 Q 39.4 28.6 26 29 Q 34 22 27 11.6 Z", 0.35, blur=0.8)
    for x, y in ((20, 16), (26, 14.6), (32, 16), (23, 20.6), (29, 20.6)):
        r.ellipse(x, y, 1.3, 0.9, "$p.dark", alpha=0.5)
    r.path("M 16 15 Q 19 12.6 24 12.4", None, stroke="#FFFFFF", width=0.9, alpha=0.6, blur=0.3)
    r.path("M 22.6 24.6 Q 26 26.4 29.4 24.6", None, stroke=OUT, width=0.45)
    for x, y, rad in ((41, 6, 1.1), (44, 2.6, 0.7), (9, 4, 0.8)):
        r.ellipse(x, y, rad, rad, None, stroke="#E8F8FF", width=0.3, alpha=0.8)
    return r


def night_owl() -> Recipe:
    r = new("night_owl", 40, 46, (20, 42))
    feathers = linear(0, 6, 0, 42, (0, "$p.light"), (0.45, "$p.body"), (1, "$p.dark"))
    r.shadow(20, 42, 12, 2.8, 0.34)
    for sx in (-1, 1):
        r.path(f"M {20 + sx * 8} 16 Q {20 + sx * 16.6} 22 {20 + sx * 13} 37 Q {20 + sx * 9} 34 {20 + sx * 8} 28 Z", feathers, stroke=OUT, width=0.45)
        for y in (24, 28, 32):
            r.path(f"M {20 + sx * 9} {y} Q {20 + sx * 12} {y + 1.6} {20 + sx * 14} {y - 0.6}", None, stroke=OUT, width=0.3, alpha=0.6)
        r.path(f"M {20 + sx * 3} 39 L {20 + sx * 1.6} 42 M {20 + sx * 4} 39 L {20 + sx * 4.4} 42 M {20 + sx * 5} 39 L {20 + sx * 7} 41.6", None, stroke="$p.beak", width=0.8)
        r.path(f"M {20 + sx * 5} 8 L {20 + sx * 10} 1.6 L {20 + sx * 10.6} 10 Z", feathers, stroke=OUT, width=0.45)  # the ear tufts
    r.path("M 10 22 Q 9 5.6 20 5.6 Q 31 5.6 30 22 Q 30.6 38 20 40 Q 9.4 38 10 22 Z", feathers, stroke=OUT, width=0.5)
    r.path("M 13.6 22 Q 20 17.6 26.4 22 Q 27.6 35 20 37.6 Q 12.4 35 13.6 22 Z", "$p.belly", stroke=OUT, width=0.35)
    for row in range(4):
        for k in range(3 + row % 2):
            x, y = 16.6 + k * 2.6 - (row % 2) * 1.3, 24.6 + row * 3
            r.path(f"M {x} {y} L {x + 1} {y + 1.4} L {x + 2} {y}", None, stroke="$p.body", width=0.4, alpha=0.8)
    r.shade("M 21 5.6 Q 31 5.6 30 22 Q 30.6 38 20 40 Q 27 24 21 5.6 Z", 0.3, blur=0.8)
    for sx in (-1, 1):
        x = 20 + sx * 4.4
        r.ellipse(x, 14, 4.2, 4.4, "$p.light", stroke=OUT, width=0.35)
        r.glow(x, 14, 4.4, "$p.eye", 0.4)
        r.ellipse(x, 14, 2.9, 3.1, radial(x, 14, 3.1, (0, "#FFF4B0"), (1, "$p.eye")), stroke=OUT, width=0.35)
        r.ellipse(x, 14, 1.3, 1.5, "$p.pupil")
        r.ellipse(x - 0.6, 13.2, 0.5, 0.5, "#FFFFFF")
    r.path("M 13 9 L 18.6 11.6 M 27 9 L 21.4 11.6", None, stroke=OUT, width=0.7)
    r.path("M 18.6 16 L 21.4 16 L 20 20 Z", "$p.beak", stroke=OUT, width=0.35)
    return r


def myconid() -> Recipe:
    r = new("myconid", 40, 44, (20, 40))
    r.shadow(20, 40, 12, 2.8, 0.34)
    for sx in (-1, 1):
        r.path(f"M {20 + sx * 5} 28 Q {20 + sx * 10} 29 {20 + sx * 10.6} 34", None, stroke=OUT, width=2.6)
        r.path(f"M {20 + sx * 5} 28 Q {20 + sx * 10} 29 {20 + sx * 10.6} 34", None, stroke="$p.stem", width=1.7)
        r.path(f"M {20 + sx * 2} 36 L {20 + sx * 3.6} 40", None, stroke=OUT, width=3.0)
        r.path(f"M {20 + sx * 2} 36 L {20 + sx * 3.6} 40", None, stroke="$p.stem", width=2.1)
    r.path("M 13.6 20 Q 12 30 14.6 37 Q 20 39.6 25.4 37 Q 28 30 26.4 20 Z", linear(13, 0, 27, 0, (0, "#FFFFFF"), (0.4, "$p.stem"), (1, "#B8A88A")), stroke=OUT, width=0.5)
    r.shade(box(12, 19, 16, 4.6), 0.45, blur=0.8)
    for sx in (-1, 1):
        x = 20 + sx * 3
        r.ellipse(x, 27, 1.4, 1.8, "$p.eye")
        r.ellipse(x - 0.4, 26.3, 0.45, 0.5, "#FFFFFF")
        r.ellipse(20 + sx * 5, 30, 1.4, 0.7, "#F08090", alpha=0.4, blur=0.3)
    r.path("M 18.6 31 Q 20 32.4 21.4 31", None, stroke=OUT, width=0.45)
    cap = "M 2.6 20 Q 3.6 3 20 2.6 Q 36.4 3 37.4 20 Q 20 25 2.6 20 Z"
    r.path(cap, radial(13.6, 8, 24, (0, "$p.light"), (0.5, "$p.body"), (1, "$p.dark")), stroke=OUT, width=0.5)
    r.shade("M 22 2.6 Q 36.4 3 37.4 20 Q 30 22.6 24 23 Q 30 12 22 2.6 Z", 0.35, blur=0.8)
    for k in range(9):
        x = 5 + k * 3.8
        r.line(x, 20.6 + math.sin(k / 8 * math.pi) * 1.6, x + 0.3, 22.4 + math.sin(k / 8 * math.pi) * 1.4, OUT, 0.3, alpha=0.6)
    for x, y, rad in ((11, 10, 2.4), (20, 6, 1.8), (28, 10.6, 2.6), (16, 15.6, 1.5), (31, 16.6, 1.4), (7, 16, 1.3), (23.6, 14.6, 1.2)):
        r.ellipse(x, y, rad, rad * 0.75, "$p.spot", clip=True)
    r.path("M 6 14 Q 9 6 17 4", None, stroke="#FFFFFF", width=1.0, alpha=0.5, blur=0.3)
    return r


def stone_golem() -> Recipe:
    r = new("stone_golem", 56, 60, (28, 55))
    rock = linear(8, 0, 48, 0, (0, "$p.light"), (0.45, "$p.body"), (1, "$p.dark"))
    r.shadow(28, 55, 21, 4, 0.4)
    for x in (16.6, 30.4):  # the legs
        r.path(f"M {x} 40 L {x + 9} 40 L {x + 10} 54.6 L {x - 1} 54.6 Z", rock, stroke=OUT, width=0.5)
    for sx in (-1, 1):  # the arms
        x = 28 + sx * 19
        r.path(f"M {x - 5} 18 L {x + 5} 19 L {x + 6} 34 L {x - 4} 34 Z", rock, stroke=OUT, width=0.5)
        r.path(f"M {x - 5.6} 33 L {x + 6.6} 33 L {x + 7} 45 L {x} 47.6 L {x - 6} 45 Z", rock, stroke=OUT, width=0.5)
    r.path("M 11 16 L 20 10 L 36 10 L 45 16 L 42.6 41 L 28 44.6 L 13.4 41 Z", rock, stroke=OUT, width=0.5)  # the chest
    r.path("M 20 4 L 28 0.6 L 36 4 L 37 13 L 28 16 L 19 13 Z", rock, stroke=OUT, width=0.5)  # the head
    r.shade("M 29 0 L 54 12 L 54 56 L 29 56 Z", 0.4, blur=1.2)
    rune = "M 28 20 L 33 27 L 28 34 L 23 27 Z M 28 34 L 28 39"
    r.path(rune, None, stroke="$p.glow", width=2.6, alpha=0.5, blend="add", blur=1.0)
    r.path(rune, None, stroke="$p.glow", width=0.9)
    for x in (24.6, 31.4):
        r.glow(x, 8, 3.6, "$p.glow", 0.7)
        r.rect(x - 1.5, 7.2, 3, 1.6, "$p.glow")
    r.path("M 14 22 L 18 26 L 16.6 31 M 40 30 L 37.6 35 L 39.6 39 M 21 12 L 24 13.6", None, stroke=OUT, width=0.4, alpha=0.8)
    for x, y, rx in ((14.6, 16.6, 4.6), (40, 13.6, 3.6), (20, 53, 4), (10, 34, 3)):
        r.ellipse(x, y, rx, rx * 0.45, "$p.moss", alpha=0.85, blur=0.5, clip=True)
    r.path("M 12.6 17 L 20 11.6 L 27 11.4", None, stroke="#FFFFFF", width=0.9, alpha=0.45, blur=0.3)
    return r


def wisp() -> Recipe:
    r = new("wisp", 36, 46, (18, 42))
    r.ellipse(18, 42, 8, 2, "#141030", alpha=0.2, blur=0.8)
    r.glow(18, 21, 14, "$p.halo", 0.5)
    for x, y, rad in ((8, 34, 0.8), (27, 31, 0.6), (12, 40, 0.5), (24, 38, 0.7)):
        r.glow(x, y, rad * 4, "$p.halo", 0.6)
        r.ellipse(x, y, rad, rad, "$p.light")
    body = "M 18 2.6 Q 21 9 26 14 Q 31 20 28.6 27 Q 25 34 18 34 Q 11 34 7.4 27 Q 5 20 10 14 Q 12 12 13 8 Q 15.6 10 16 13 Q 17.6 8 18 2.6 Z"
    r.path(body, linear(18, 2, 18, 34, (0, "$p.dark"), (0.5, "$p.body"), (1, "$p.light")), blur=0.5)
    r.path("M 18 12 Q 21 17 23 21 Q 25 26 22 30 Q 18 32 14 30 Q 11 26 13.6 21 Q 15.6 17 18 12 Z", "$p.light", alpha=0.9, blur=0.6)
    r.ellipse(18, 25, 4.6, 5, "#FFFFFF", alpha=0.85, blur=1.2)
    for sx in (-1, 1):
        r.ellipse(18 + sx * 2.6, 23.6, 1.1, 1.7, "$p.eye")
        r.ellipse(18 + sx * 2.6 - 0.3, 23, 0.35, 0.4, "#FFFFFF")
    return r


def build_creatures() -> list[Recipe]:
    out = [slime(f"slime_{kind}", kind) for kind in FEATURES if kind != "colossus"]
    out += [slime(name, kind, royal=True) for name, kind in ROYAL.items()]
    out += [giant_slime(name, kind) for name, kind in GIANT.items()]
    out += [wolf(name, feature, **kw) for name, (feature, kw) in BEASTS.items()]
    out += [wolf(name, feature, alpha=True) for name, feature in ALPHAS.items()]
    out += [guardian(name, feature) for name, feature in KNIGHTS.items()]
    out += [cave_bat(), cave_spider(), dune_scorpion(), shore_crab(), night_owl(), myconid(), stone_golem(), wisp()]
    return out


def main() -> None:
    recipes = build_creatures()
    for r in recipes:
        r.write(CREATURES / (r.id.rsplit("/", 1)[1] + ".json"))
    print(f"wrote {len(recipes)} creatures (the Echoes come from make_echoes.py)")


if __name__ == "__main__":
    main()
