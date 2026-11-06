"""What makes each kind of creature look different from its siblings: a feature for every slime, wolf and knight variant.

The creature recipes of one family share a body (slime, wolf, knight); the palette changes the colors, and the features here
change the shape: a sprout, flames, crystals, a scar, a crown of lightning, a lantern... `art_creatures.py` appends them over
the shared body. Slime features are drawn in the coordinates of the 36 x 30 slime; the big ones (the kings of the slimes)
use the same functions scaled up. Wolf features use the 40 x 40 wolf, knight features the 56 x 64 knight.
"""
from __future__ import annotations

from artkit import Recipe, linear, radial

LEAF = "#4FB04A"
FIRE = "#FF8A2A"
FIRE2 = "#FFD84A"
CRYSTAL = "#BFEFFF"
GOLD = "#F2C94C"


def _flame(x: Recipe, cx: float, base: float, h: float, w: float = 2.4) -> None:
    x.path(f"M {cx - w} {base} Q {cx - w * 1.1} {base - h * 0.5} {cx} {base - h} Q {cx + w * 0.2} {base - h * 0.45} {cx + w * 1.1} {base - h * 0.4} Q {cx + w * 1.2} {base - h * 0.1} {cx + w} {base} Z", FIRE, stroke="#8A2A0A", width=0.7)
    x.path(f"M {cx - w * 0.5} {base} Q {cx - w * 0.4} {base - h * 0.4} {cx} {base - h * 0.7} Q {cx + w * 0.5} {base - h * 0.3} {cx + w * 0.5} {base} Z", FIRE2)


def _star(x: Recipe, cx: float, cy: float, r: float, color: str = "#FFFFFF", alpha: float = 0.95) -> None:
    x.poly([(cx, cy - r), (cx + r * 0.28, cy - r * 0.28), (cx + r, cy), (cx + r * 0.28, cy + r * 0.28), (cx, cy + r), (cx - r * 0.28, cy + r * 0.28), (cx - r, cy), (cx - r * 0.28, cy - r * 0.28)], color, alpha=alpha)


def _crystal(x: Recipe, cx: float, base: float, h: float, w: float, color: str = CRYSTAL) -> None:
    x.poly([(cx - w, base), (cx - w * 0.5, base - h * 0.75), (cx, base - h), (cx + w * 0.6, base - h * 0.7), (cx + w, base)], color, stroke="#4A7A9A", width=0.7)
    x.poly([(cx, base - h), (cx + w * 0.6, base - h * 0.7), (cx + w * 0.2, base)], "#FFFFFF", alpha=0.45)


# ---------------------------------------------------------------------------------------------------------- slimes
def slime_green(x: Recipe) -> None:  # a sprout with two leaves
    x.path("M 18 7 Q 17 3.6 19 1.4", None, stroke="#2F7A3A", width=1.5)
    x.path("M 19 1.6 Q 24 0 25 4.4 Q 20.6 5 19 1.6 Z", LEAF, stroke="#1E5A28", width=0.8)
    x.path("M 18 3.4 Q 13.4 1.6 12.6 5.6 Q 16.4 6.4 18 3.4 Z", LEAF, stroke="#1E5A28", width=0.8)
    x.line(19.4, 2, 23, 3.6, "#CFF2A0", width=0.5)


def slime_blue(x: Recipe) -> None:  # a water drop and ripples
    x.path("M 18 0.4 Q 21 4 21 5.6 Q 21 8 18 8 Q 15 8 15 5.6 Q 15 4 18 0.4 Z", "#7FD0FF", stroke="#1E5A9A", width=0.8)
    x.ellipse(17, 5.4, 0.8, 1.2, "#FFFFFF", alpha=0.8)
    for rx, ry, a in ((8, 3.2, 0.5), (11.5, 4.6, 0.3)):
        x.ellipse(18, 22.5, rx, ry, None, stroke="#FFFFFF", width=0.7, alpha=a)


def slime_ember(x: Recipe) -> None:  # three flames and floating sparks
    for cx, h in ((12.5, 5), (18, 7.4), (23.5, 4.6)):
        _flame(x, cx, 8.6 if cx == 18 else 10, h)
    for sx, sy in ((8, 7), (28, 5), (31, 12), (5, 13)):
        x.ellipse(sx, sy, 0.7, 0.7, FIRE2)


def slime_ice(x: Recipe) -> None:  # crystals on the back and frost
    _crystal(x, 11, 10.5, 8, 2.4)
    _crystal(x, 18, 8, 10, 2.8)
    _crystal(x, 25.5, 10.5, 7, 2.2)
    for fx, fy in ((9, 22), (27, 21), (21, 24)):
        _star(x, fx, fy, 1.1, "#FFFFFF", 0.8)


def slime_magma(x: Recipe) -> None:  # glowing cracks and a drip of lava
    x.path("M 8 11 L 11 15 L 9 19 L 12 23", None, stroke=FIRE2, width=1.1)
    x.path("M 26 10 L 24 14 L 27 18 L 25 22", None, stroke=FIRE2, width=1.1)
    x.path("M 15 8 L 17 11 L 15.6 14", None, stroke=FIRE, width=0.9)
    x.path("M 8 11 L 11 15 L 9 19 L 12 23 M 26 10 L 24 14 L 27 18 L 25 22", None, stroke=FIRE, width=2.2, alpha=0.25)
    x.ellipse(30.4, 26.4, 1.0, 1.5, FIRE, stroke="#8A2A0A", width=0.5)
    x.ellipse(7, 26.8, 0.8, 1.2, FIRE2)


def slime_char(x: Recipe) -> None:  # charred stripes, glowing embers, a wisp of smoke
    for sx in (9, 15, 21, 27):
        x.path(f"M {sx} 9 Q {sx + 1.4} 17 {sx - 0.4} 25", None, stroke="#000000", width=1.5, alpha=0.4)
    for ex, ey in ((12, 14), (24, 12), (20, 23), (8, 21)):
        x.ellipse(ex, ey, 0.8, 0.8, FIRE, alpha=0.9)
    x.path("M 17 5 Q 14 2 17 -0.5 Q 20 -3 17.4 -5", None, stroke="#9AA0A8", width=1.2, alpha=0.5)


def slime_glow(x: Recipe) -> None:  # a light on a stalk, glowing spots
    x.path("M 18 7 Q 16 3 19 0.6", None, stroke="$p.dark", width=1.2)
    x.ellipse(19, 0.8, 2.4, 2.4, radial(19, 0.8, 3.4, (0, "#FFFFFF"), (0.45, "#FFF3A0"), (1, "#FFD84A")), alpha=0.95)
    x.ellipse(19, 0.8, 4.6, 4.6, "#FFF3A0", alpha=0.2)
    for sx, sy, r in ((9, 12, 1.4), (26, 14, 1.8), (12, 22, 1.2), (23, 23, 1.3)):
        x.ellipse(sx, sy, r, r, "#FFF3A0", alpha=0.8)
        x.ellipse(sx, sy, r * 2, r * 2, "#FFF3A0", alpha=0.18)


def slime_moss(x: Recipe) -> None:  # patches of moss and a small red mushroom
    for mx, my, r in ((10, 11, 4), (21, 9, 3.4), (27, 15, 3)):
        x.ellipse(mx, my, r * 1.2, r * 0.8, "#4F8A3A", alpha=0.85)
        x.ellipse(mx - r * 0.3, my - r * 0.2, r * 0.6, r * 0.35, "#8FC24A", alpha=0.8)
    x.rect(14.6, 3, 1.6, 4, "#EFE6C8", stroke="#6A5A38", width=0.5)
    x.ellipse(15.4, 3, 3.2, 2.1, "#C9302C", stroke="#6A1A18", width=0.7)
    for dx in (-1.2, 0.6, 1.8):
        x.ellipse(15.4 + dx, 2.6, 0.45, 0.4, "#FFFFFF")


def slime_mint(x: Recipe) -> None:  # mint leaves and a swirl of cream
    for lx, ly, sx in ((13.4, 5, -1), (22.6, 5, 1)):
        x.path(f"M 18 7 Q {lx + sx * 1} {ly - 4} {lx + sx * 4.4} {ly - 0.6} Q {lx + sx * 1} {ly + 2.4} 18 7 Z", "#7EE0A8", stroke="#2E8060", width=0.8)
        x.line(18, 7, lx + sx * 3.4, ly - 0.2, "#2E8060", width=0.5)
    x.path("M 10 22 Q 18 26 26 22", None, stroke="#FFFFFF", width=1.6, alpha=0.7)
    x.path("M 12 19.6 Q 18 23 24 19.6", None, stroke="#FFFFFF", width=1.0, alpha=0.5)


def slime_coral(x: Recipe) -> None:  # branches of coral
    for bx, lean in ((11, -2.4), (18, 0), (25, 2.4)):
        x.path(f"M {bx} 8 Q {bx + lean} 4 {bx + lean * 1.4} 1", None, stroke="#F2708A", width=1.8)
        x.path(f"M {bx + lean * 0.6} 4.6 Q {bx + lean * 0.6 - 2.4} 3 {bx + lean * 0.6 - 3} 1.2", None, stroke="#F2708A", width=1.3)
        x.ellipse(bx + lean * 1.4, 1, 1.0, 1.0, "#FFB3C4")
    x.ellipse(24, 21, 2.2, 1.4, "#FFE0E6", stroke="#B04060", width=0.5)


def slime_pearl(x: Recipe) -> None:  # a big pearl and the ridges of a shell
    for r in (3, 5.4, 7.8):
        x.path(f"M {18 - r * 1.6} {9 + r * 0.7} Q 18 {9 - r * 0.9} {18 + r * 1.6} {9 + r * 0.7}", None, stroke="#FFFFFF", width=0.7, alpha=0.5)
    x.ellipse(23.5, 20.5, 3.4, 3.4, radial(22.4, 19.4, 5, (0, "#FFFFFF"), (0.6, "#F2E6F2"), (1, "#C8B8D8")), stroke="#9A88B0", width=0.6)
    x.ellipse(22.4, 19.4, 0.9, 0.7, "#FFFFFF")


def slime_nebula(x: Recipe) -> None:  # stars and a swirl
    x.ellipse(24, 14, 5.5, 3.2, "#C06AFF", alpha=0.3)
    x.ellipse(10, 21, 4.5, 2.6, "#5AD0FF", alpha=0.25)
    for sx, sy, r in ((9, 11, 1.8), (26, 11, 2.2), (21, 23, 1.6), (13, 7, 1.2), (30, 19, 1.2)):
        _star(x, sx, sy, r)
    x.path("M 9 22 Q 18 14 28 20", None, stroke="#FFFFFF", width=0.6, alpha=0.4)


def slime_rust(x: Recipe) -> None:  # patches of rust, rivets and a small cog
    for rx, ry, r in ((9, 14, 3.2), (26, 12, 2.8), (20, 22, 3.4)):
        x.ellipse(rx, ry, r * 1.2, r * 0.8, "#A8501E", alpha=0.7)
        x.ellipse(rx + 0.6, ry + 0.4, r * 0.6, r * 0.4, "#D8883A", alpha=0.6)
    for bx, by in ((6, 19), (29, 17), (14, 10)):
        x.ellipse(bx, by, 0.9, 0.9, "#7A7F88", stroke="#2A2D34", width=0.4)
    x.ellipse(27, 22, 2.4, 2.4, "#8A8F98", stroke="#2A2D34", width=0.6)
    x.ellipse(27, 22, 0.9, 0.9, "#2A2D34")
    for k in range(6):
        x.line(27, 22, 27 + 3.1 * (1 if k % 2 else -1) * (0.5 + 0.5 * (k % 3) / 2), 22 + 2.6 * (k - 2.5) / 2.5, "#8A8F98", width=1.0)


def slime_sand(x: Recipe) -> None:  # dune ripples and grains
    for i, ry in enumerate((13, 17, 21)):
        x.path(f"M {7 + i} {ry} Q 13 {ry - 2} 18 {ry} Q 24 {ry + 2} {29 - i} {ry}", None, stroke="#C8A25A", width=0.8, alpha=0.7)
    for sx, sy in ((9, 10), (23, 9), (27, 16), (12, 24), (22, 25)):
        x.ellipse(sx, sy, 0.5, 0.5, "#E8CC8A")
    x.poly([(15, 7.4), (18, 2), (21, 7.4)], "#D8B46A", stroke="#8A6A2A", width=0.7)


def slime_slate(x: Recipe) -> None:  # stone plates with cracks
    x.path("M 7 12 L 14 9 L 18 14 L 12 18 Z", "#5E6672", alpha=0.7, stroke="#2A2D34", width=0.6)
    x.path("M 20 9 L 28 12 L 25 19 L 19 15 Z", "#5E6672", alpha=0.7, stroke="#2A2D34", width=0.6)
    x.path("M 10 21 L 17 19 L 22 23 L 13 25 Z", "#5E6672", alpha=0.7, stroke="#2A2D34", width=0.6)
    x.path("M 14 9 L 16 4 L 20 8", "#8A929E", stroke="#2A2D34", width=0.6)
    x.path("M 8 14 L 11 16", None, stroke="#FFFFFF", width=0.5, alpha=0.4)


def slime_tide(x: Recipe) -> None:  # fins and waves
    x.path("M 3.6 18 Q -1 14 0.6 8 Q 4 10 6 14 Z", "#4FB0E0", stroke="#1E5A9A", width=0.8)
    x.path("M 32.4 18 Q 37 14 35.4 8 Q 32 10 30 14 Z", "#4FB0E0", stroke="#1E5A9A", width=0.8)
    x.path("M 15 7 Q 18 0 21 7 Q 18 5 15 7 Z", "#4FB0E0", stroke="#1E5A9A", width=0.8)
    for wy in (21, 24):
        x.path(f"M 7 {wy} Q 10 {wy - 2} 13 {wy} Q 16 {wy + 2} 19 {wy} Q 22 {wy - 2} 25 {wy} Q 28 {wy + 2} 30 {wy}", None, stroke="#FFFFFF", width=0.8, alpha=0.55)


def slime_amber(x: Recipe) -> None:  # a little insect trapped inside, resin shine
    x.ellipse(21, 19, 2.6, 1.7, "#4A2E10", alpha=0.85)
    x.ellipse(24.2, 18.6, 1.0, 0.9, "#4A2E10", alpha=0.85)
    for lx in (19.6, 21, 22.4):
        x.line(lx, 19, lx - 0.6, 21.6, "#4A2E10", width=0.5)
    x.path("M 20 18 Q 21.6 14 24 16", None, stroke="#FFFFFF", width=0.6, alpha=0.5)
    x.ellipse(9, 20, 2, 1.2, "#FFE8A0", alpha=0.55)


def cinder_colossus(x: Recipe) -> None:  # horns, cracks and smoke
    slime_char(x)
    for sx in (-1, 1):
        x.path(f"M {18 + sx * 6} 9 Q {18 + sx * 11} 5 {18 + sx * 10.4} -1.4 Q {18 + sx * 7.6} 3.4 {18 + sx * 3.6} 7.4 Z", "#2A1E1A", stroke="#0A0605", width=0.9)
        x.line(18 + sx * 8.4, 4, 18 + sx * 9.6, 0.4, "#FF7A1A", width=0.6, alpha=0.8)


SLIMES = {
    "slime_green": slime_green, "slime_blue": slime_blue, "slime_ember": slime_ember, "slime_ice": slime_ice, "slime_magma": slime_magma,
    "slime_char": slime_char, "slime_glow": slime_glow, "slime_moss": slime_moss, "slime_mint": slime_mint, "slime_coral": slime_coral,
    "slime_pearl": slime_pearl, "slime_nebula": slime_nebula, "slime_rust": slime_rust, "slime_sand": slime_sand, "slime_slate": slime_slate,
    "slime_tide": slime_tide, "slime_amber": slime_amber, "cinder_colossus": cinder_colossus,
    # the crowned ones share the element of their kind, and a necklace of beads sets them apart from it
    "amber_queen": slime_amber, "char_tyrant": slime_char, "coral_matron": slime_coral, "ice_warden": slime_ice, "magma_heart": slime_magma,
    "mint_matron": slime_mint, "moss_elder": slime_moss, "nebula_heart": slime_nebula, "pearl_empress": slime_pearl, "rust_baron": slime_rust,
    # the giants
    "gel_king": slime_blue, "astral_curator": slime_nebula, "frost_sovereign": slime_ice, "tide_regent": slime_tide,
}
NECKLACE = {"amber_queen", "char_tyrant", "coral_matron", "ice_warden", "magma_heart", "mint_matron", "moss_elder", "nebula_heart", "pearl_empress", "rust_baron"}


def necklace(x: Recipe) -> None:
    x.path("M 6 21 Q 18 29 30 21", None, stroke=GOLD, width=1.1, alpha=0.9)
    for bx, by in ((9, 23.4), (13, 25.5), (18, 26.4), (23, 25.5), (27, 23.4)):
        x.ellipse(bx, by, 1.1, 1.1, GOLD, stroke="#7A5A10", width=0.4)
    x.ellipse(18, 27.6, 1.5, 1.7, "#D8402A", stroke="#7A1A10", width=0.5)


# ---------------------------------------------------------------------------------------------------------- wolves
def wolf_grey(x: Recipe) -> None:  # a white blaze on the chest and the forehead
    x.path("M 20 9 Q 18.8 12 19.4 15 L 20.6 15 Q 21.2 12 20 9 Z", "#F2F2F6", alpha=0.85)
    x.path("M 14 28 Q 20 24 26 28 Q 24 33 20 34 Q 16 33 14 28 Z", "#F2F2F6", alpha=0.75)


def wolf_dire(x: Recipe) -> None:  # a scar over the eye and a spiked collar
    x.path("M 12 8.6 L 17.2 18", None, stroke="#C9302C", width=1.1)
    x.path("M 13.2 11 L 15 11.6 M 14.4 13.6 L 16.2 14.2", None, stroke="#F2F2F6", width=0.5, alpha=0.8)
    x.path("M 12 26 Q 20 31.4 28 26", None, stroke="#3A2A20", width=2.6)
    for sx in (13.6, 17, 20, 23, 26.4):
        x.poly([(sx - 1, 28.6), (sx, 25.4), (sx + 1, 28.6)], "#C8CCD4", stroke="#2A2D34", width=0.5)


def wolf_dune(x: Recipe) -> None:  # a sand scarf and stripes on the cheeks
    x.path("M 10 25.6 Q 20 31 30 25.6 L 30.4 29 Q 20 34.4 9.6 29 Z", "#E3C27A", stroke="#7A5A2A", width=0.9)
    x.path("M 28 29 L 31 36 L 27.4 34.6 Z", "#E3C27A", stroke="#7A5A2A", width=0.8)
    for dy in (0, 1.6):
        x.line(9.4, 19.4 + dy, 12.6, 20 + dy, "#7A5A2A", width=0.7)
        x.line(30.6, 19.4 + dy, 27.4, 20 + dy, "#7A5A2A", width=0.7)


def wolf_frost(x: Recipe) -> None:  # ice shards on the back and the ears
    for sx, h in ((14, 7), (20, 9), (26, 7)):
        x.poly([(sx - 1.8, 12), (sx, 12 - h), (sx + 1.8, 12)], CRYSTAL, stroke="#4A7A9A", width=0.6, alpha=0.9)
    for sx, sy in ((12, 30), (28, 31), (20, 35)):
        _star(x, sx, sy, 1.3, "#FFFFFF", 0.8)


def wolf_polar(x: Recipe) -> None:  # a thick white ruff and a frosted muzzle
    for sx in (-1, 1):
        for k in range(4):
            x.poly([(20 + sx * (6 + k * 2.4), 24 + k * 1.2), (20 + sx * (10 + k * 2.4), 28 + k * 1.6), (20 + sx * (5 + k * 2.4), 29 + k * 1.2)], "#F6FAFF", stroke="#8AA0B8", width=0.6)
    x.ellipse(20, 22.4, 4, 2, "#FFFFFF", alpha=0.5)


def wolf_shade(x: Recipe) -> None:  # wisps of shadow and glowing eyes
    for wx, wy, a in ((6, 30, 0.45), (34, 28, 0.4), (10, 36, 0.35), (30, 36, 0.35)):
        x.path(f"M {wx} {wy} Q {wx + 3} {wy - 5} {wx} {wy - 9} Q {wx - 1} {wy - 4} {wx - 3} {wy - 3} Z", "#2A1A40", alpha=a)
    for ex in (14.5, 25.5):
        x.ellipse(ex, 15, 3.4, 2.6, "#B47CFF", alpha=0.3)


def wolf_storm(x: Recipe) -> None:  # lightning marks
    x.path("M 10 24 L 13.4 27 L 11 29 L 14.6 33", None, stroke=FIRE2, width=1.2)
    x.path("M 30 24 L 26.6 27 L 29 29 L 25.4 33", None, stroke=FIRE2, width=1.2)
    x.path("M 20 8.6 L 18.4 12 L 20.6 13 L 19.2 16.6", None, stroke=FIRE2, width=1.0)


def wolf_tawny(x: Recipe) -> None:  # tiger stripes
    for sy in (26, 29.4, 32.6):
        x.path(f"M 8 {sy} Q 10 {sy + 1} 12.4 {sy - 1}", None, stroke="#3A2410", width=1.2, alpha=0.7)
        x.path(f"M 32 {sy} Q 30 {sy + 1} 27.6 {sy - 1}", None, stroke="#3A2410", width=1.2, alpha=0.7)
    for dx in (-3, 0, 3):
        x.line(20 + dx, 9.4, 20 + dx * 0.8, 12.6, "#3A2410", width=0.9, alpha=0.7)


def dire_alpha(x: Recipe) -> None:  # an alpha of the dire wolves: a bone crest and fierce scars
    wolf_dire(x)
    for sx, h in ((14, 5), (17, 6.4), (20, 7.4), (23, 6.4), (26, 5)):
        x.poly([(sx - 1.3, 7.6), (sx, 7.6 - h), (sx + 1.3, 7.6)], "#EFE6CC", stroke="#3A2A20", width=0.6)


def dune_mother(x: Recipe) -> None:  # an alpha of the dunes: a headdress of gold and a gem
    wolf_dune(x)
    x.path("M 11 9 Q 20 4.4 29 9 L 28 11 Q 20 7.4 12 11 Z", GOLD, stroke="#7A5A10", width=0.8)
    x.poly([(20, 4.4), (22, 8), (20, 10.4), (18, 8)], "#D8402A", stroke="#7A1A10", width=0.6)
    for sx in (13.4, 26.6):
        x.ellipse(sx, 10.6, 0.9, 0.9, "#4FC0A0")


def moonshade_alpha(x: Recipe) -> None:  # an alpha of the shades: a crescent moon on the brow
    wolf_shade(x)
    x.ellipse(20, 9.6, 2.9, 2.9, "#F4F0FF")
    x.ellipse(21.3, 9.1, 2.6, 2.6, "$p.fur")
    x.ellipse(20, 9.6, 4.6, 4.6, "#B47CFF", alpha=0.2)


def polar_king(x: Recipe) -> None:  # king of the polar wolves: a crown of ice
    wolf_polar(x)
    for sx, h in ((12.6, 5), (16.4, 8), (20, 10), (23.6, 8), (27.4, 5)):
        x.poly([(sx - 1.7, 8.2), (sx, 8.2 - h), (sx + 1.7, 8.2)], CRYSTAL, stroke="#4A7A9A", width=0.6)
    x.rect(11, 7.6, 18, 1.8, "#8FC8F0", stroke="#4A7A9A", width=0.6)


def storm_sovereign(x: Recipe) -> None:  # sovereign of the storm wolves: a crown of lightning
    wolf_storm(x)
    for sx, h in ((13, 4), (16.6, 7), (20, 9), (23.4, 7), (27, 4)):
        x.path(f"M {sx - 1.6} 8.4 L {sx - 0.4} {8.4 - h * 0.5} L {sx - 1.2} {8.4 - h * 0.5} L {sx + 0.8} {8.4 - h}", None, stroke=FIRE2, width=1.3)
    x.ellipse(20, 6, 9, 3.4, FIRE2, alpha=0.18)


WOLVES = {
    "wolf_grey": wolf_grey, "wolf_dire": wolf_dire, "wolf_dune": wolf_dune, "wolf_frost": wolf_frost, "wolf_polar": wolf_polar,
    "wolf_shade": wolf_shade, "wolf_storm": wolf_storm, "wolf_tawny": wolf_tawny, "dire_alpha": dire_alpha, "dune_mother": dune_mother,
    "moonshade_alpha": moonshade_alpha, "polar_king": polar_king, "storm_sovereign": storm_sovereign,
}


# ---------------------------------------------------------------------------------------------------------- knights
def barrow_warden(x: Recipe) -> None:  # a skull on the chest, bone spikes on the shoulders
    x.ellipse(28, 45, 6, 5.4, "#EFE6CC", stroke="#241209", width=1.0)
    x.rect(24.4, 48, 7.2, 3.4, "#EFE6CC", stroke="#241209", width=0.8)
    for ex in (25.8, 30.2):
        x.ellipse(ex, 45, 1.6, 1.9, "#14161C")
    x.poly([(27.2, 47.4), (28.8, 47.4), (28, 49)], "#14161C")
    for sx in (-1, 1):
        for k in range(3):
            x.poly([(28 + sx * (14 + k * 2.4), 31), (28 + sx * (17 + k * 2.6), 25 - k * 1.4), (28 + sx * (16 + k * 2.4), 33)], "#EFE6CC", stroke="#241209", width=0.7)


def drowned_captain(x: Recipe) -> None:  # a tricorn over the horns, an anchor and barnacles
    x.path("M 12 12 Q 28 -2 44 12 L 40 14 Q 28 6 16 14 Z", "#2A3A46", stroke="#0A1218", width=1.2)
    x.path("M 12 12 Q 6 12 6 16 L 18 14 Z", "#2A3A46", stroke="#0A1218", width=1.0)
    x.path("M 44 12 Q 50 12 50 16 L 38 14 Z", "#2A3A46", stroke="#0A1218", width=1.0)
    x.ellipse(28, 6.4, 2.2, 2.2, GOLD, stroke="#7A5A10", width=0.6)
    x.path("M 28 38 L 28 52 M 23 42 L 33 42 M 22 49 Q 28 56 34 49", None, stroke="#C8D0D8", width=1.6)
    for bx, by in ((16, 50), (40, 48), (18, 58), (38, 58)):
        x.ellipse(bx, by, 1.8, 1.4, "#D8D0B0", stroke="#3A3A2A", width=0.5)


def forge_tyrant(x: Recipe) -> None:  # a great hammer on the shoulder and embers
    x.rect(46, 18, 3.2, 26, "#6A4A2A", stroke="#241209", width=1.0)
    x.rect(41, 12, 13.6, 9, "#6C727E", stroke="#14161C", width=1.2)
    x.rect(42, 13, 11.6, 2, "#FFFFFF", alpha=0.25)
    for ex, ey in ((8, 40), (49, 54), (10, 52), (45, 30)):
        x.ellipse(ex, ey, 1.0, 1.0, FIRE2)
        x.ellipse(ex, ey, 2.2, 2.2, FIRE, alpha=0.3)


def iron_foreman(x: Recipe) -> None:  # a hard hat with a lamp, a gear on the chest
    x.path("M 17 12 Q 18 -1 28 -1 Q 38 -1 39 12 Z", "#F2C94C", stroke="#7A5A10", width=1.2)
    x.rect(15, 11, 26, 3, "#D8A92A", stroke="#7A5A10", width=0.9)
    x.ellipse(28, 4.4, 3, 2.6, "#FFF3B0", stroke="#7A5A10", width=0.7)
    x.ellipse(28, 4.4, 6.4, 5.4, "#FFF3B0", alpha=0.2)
    x.ellipse(28, 46, 4.6, 4.6, "#8A929C", stroke="#14161C", width=0.9)
    x.ellipse(28, 46, 1.6, 1.6, "#14161C")
    for k in range(8):
        x.rect(27 + 5.8 * (1 if k % 4 in (0, 1) else -1) * (0 if k in (2, 6) else 1) - 1, 46 - 1 + 5.6 * (1 if k in (2, 3) else -1) * (0 if k in (0, 4) else 1) - 1, 2, 2, "#8A929C")


def rime_revenant(x: Recipe) -> None:  # ice spikes and frost over the armor
    for sx, h in ((9, 12), (14, 16), (42, 16), (47, 12)):
        _crystal(x, sx, 38, h, 2.4)
    for sx, sy in ((20, 44), (36, 50), (24, 56), (32, 40)):
        _star(x, sx, sy, 2.0, "#FFFFFF", 0.7)
    x.path("M 18 56 Q 28 60 38 56", None, stroke="#FFFFFF", width=1.2, alpha=0.5)


def sand_sentinel(x: Recipe) -> None:  # a wrapped turban, a spear and sand
    x.path("M 15 14 Q 14 -2 28 -2 Q 42 -2 41 14 Q 28 8 15 14 Z", "#E3C27A", stroke="#7A5A2A", width=1.1)
    for k in range(3):
        x.path(f"M {16 + k * 2} {10 - k * 3.4} Q 28 {5 - k * 3.2} {40 - k * 2} {10 - k * 3.4}", None, stroke="#B8924A", width=0.8)
    x.rect(5, 6, 2.2, 52, "#6A4A2A", stroke="#241209", width=0.8)
    x.poly([(3.4, 8), (6.1, 0), (8.8, 8)], "#C8CCD4", stroke="#2A2D34", width=0.8)
    for sx, sy in ((14, 60), (42, 58), (22, 62), (36, 62)):
        x.ellipse(sx, sy, 1.4, 0.8, "#E3C27A", alpha=0.8)


def vault_warden(x: Recipe) -> None:  # a ring of keys, a lock on the chest and a locked crest
    x.ellipse(17, 54, 4.4, 4.4, None, stroke=GOLD, width=1.4)
    for k, dx in enumerate((-3, 0, 3)):
        x.path(f"M {17 + dx} 57 L {17 + dx} {64 if k != 1 else 62}", None, stroke=GOLD, width=1.2)
        x.rect(16 + dx, 62 - k, 2.4, 1.6, GOLD)
    x.rect(24, 42, 8, 7, GOLD, stroke="#7A5A10", width=0.9)
    x.path("M 25.6 42 Q 25.6 37.6 28 37.6 Q 30.4 37.6 30.4 42", None, stroke="#C8CCD4", width=1.6)
    x.ellipse(28, 45.2, 1.1, 1.1, "#14161C")
    x.rect(27.4, 45.6, 1.2, 2.2, "#14161C")


KNIGHTS = {
    "barrow_warden": barrow_warden, "drowned_captain": drowned_captain, "forge_tyrant": forge_tyrant, "iron_foreman": iron_foreman,
    "rime_revenant": rime_revenant, "sand_sentinel": sand_sentinel, "vault_warden": vault_warden,
}

__all__ = ["KNIGHTS", "NECKLACE", "SLIMES", "WOLVES", "linear", "necklace"]
