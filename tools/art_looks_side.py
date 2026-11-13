"""The looks of the people **seen from the side** (the figure looks to the right; the clients mirror it to look left).

Same idea as `art_looks.py`: `SIDE[(person, part)]` is a list of `(behind, function)`, a function draws on a part in the
units of that part, around its joint. Only the head, the torso and the cape have a side picture of their own: arms and
legs are the ones of the front view (and take their looks from `art_looks.py`).

Units, from the side: head, the neck joint is (0, 0), the face looks right: the forehead is at x 5.3, the tip of the nose at
x 6.7 and y -5.2, the chin at x 4 and y -0.6, the eye at (3.4, -6.3), the ear at (-0.6, -6), the back of the head at x -6.4;
torso, the waist is (0, 0), the chest is at x 4.4 and the back at x -4.4, the shoulders at y -16.
"""
from __future__ import annotations

from art_looks import GOLD, OUT, STEEL, cloth
from artkit import Recipe, linear

SIDE: dict = {}

DOME = "M -6.7 -9.4 Q -7.5 -17.3 0.4 -17.5 Q 6.6 -17.3 6.7 -10.8 Q 0 -12.8 -6.7 -9.4 Z"  # what a cap covers, from the side
DOME_SHADE = "M -6.7 -9.4 Q -7.5 -17.3 -2 -17.4 Q -4 -13 -2.6 -11.2 Q -5 -10.4 -6.7 -9.4 Z"
BODY = "M -3.6 -16.2 Q 0 -17 3 -16 Q 4.9 -12 4.4 -7 Q 3.8 -3 4.2 0 L 4.6 4.2 Q 0 5.4 -4.4 4.2 L -4 0 Q -3.6 -3 -4.2 -7 Q -4.9 -12 -3.6 -16.2 Z"


def side(person: str, part: str, behind: bool = False):
    def register(fn):
        SIDE.setdefault((person, part), []).append((behind, fn))
        return fn
    return register


def lens(x: Recipe, color: str) -> None:
    x.ellipse(3.5, -6.2, 1.7, 1.85, "#CFEFFF", alpha=0.16, stroke=color, width=0.35)
    x.line(1.8, -6.5, -0.6, -6.9, color, 0.3)
    x.path("M 2.6 -7.1 L 3.3 -7.6", None, stroke="#FFFFFF", width=0.3, alpha=0.8)


def tail(x: Recipe, d: str, light: str) -> None:
    x.path(d, "$p.hair", stroke=OUT, width=0.45)
    x.path(light, None, stroke="#FFFFFF", width=0.7, alpha=0.3, blend="add", clip=True)


def coat(color: str, lapel: str):
    def build(x: Recipe) -> None:
        cloth(x, "M -3.8 -16.2 Q 0 -17.2 3.2 -16.2 Q 5.2 -12 4.8 -6 L 5.6 12.8 Q 0 14.4 -5.6 12.8 L -4.6 -6 Q -5.2 -12 -3.8 -16.2 Z", color)
        x.shade("M -3.8 -16.2 Q -5.2 -12 -4.6 -6 L -5.6 12.8 L -2 13.8 Q -1 0 -1.6 -16.6 Z", 0.28)
        x.path("M 3.2 -16.2 L 2.2 -9 L 4.6 -11.6 Z", lapel, stroke=OUT, width=0.3)
        x.path("M 3.4 -8 L 4.2 13", None, stroke=OUT, width=0.25, alpha=0.5)
    return build


def apron(color: str, top: float, stripes: str | None = None):
    def build(x: Recipe) -> None:
        cloth(x, f"M 1.6 {top} L 4.5 {top} Q 4 -3 4.4 0 L 5.8 12.4 Q 3 13.4 0.6 12.6 L 1.2 0 Z", color, tone=0.12)
        if stripes:
            for sx in (2.2, 3.8):
                x.path(f"M {sx - 0.4} {top + 0.4} L {sx + 0.4} {top + 0.4} L {sx * 1.2 + 0.5} 12.6 L {sx * 1.2 - 0.5} 12.6 Z", stripes, alpha=0.75)
        x.path(f"M 1.8 {top} L -1 -16.4", None, stroke=color, width=0.9)
        x.path("M 1.2 -0.6 L -4.2 -0.2", None, stroke=color, width=1.0)
    return build


# ------------------------------------------------------------------------------------------------ the protagonists
@side("ren", "head")
def _ren_head(x: Recipe) -> None:
    lens(x, "#2A2A36")


@side("ren", "torso")
def _ren_torso(x: Recipe) -> None:
    x.path("M 3.2 -13.4 L 4.4 -13 L 4.5 -3 L 3.7 -1.6 Z", linear(0, -13, 0, -2, (0, "#D04450"), (1, "#8A1E2A")), stroke=OUT, width=0.3)


@side("sakura", "head", behind=True)
def _sakura_tail(x: Recipe) -> None:
    tail(x, "M -3 -13.4 Q -10.6 -14.6 -10.4 -3 Q -10.4 5 -7.6 10 Q -8.4 3 -6.6 -1 Q -5.4 -6 -3.6 -9.6 Z", "M -7.4 -12 Q -9.2 -6 -8.8 0")


@side("sakura", "head")
def _sakura_head(x: Recipe) -> None:
    x.path("M -6.3 -11.6 Q 0 -14.8 6.1 -12.6 L 5.9 -11 Q 0 -13.2 -6.2 -10 Z", "#3A3A48", stroke=OUT, width=0.35)
    x.ellipse(3.9, -12.3, 1.9, 1.4, linear(2, -14, 6, -11, (0, "#D8F8FF"), (1, "#3A9AD8")), stroke=OUT, width=0.35)
    x.ellipse(3.3, -12.7, 0.55, 0.32, "#FFFFFF", alpha=0.9)
    x.path("M -3.2 -12.8 L -6.6 -15 L -6.2 -11.8 Z", "#FF6FA8", stroke=OUT, width=0.3)
    x.path("M -3.2 -12.8 L -5.4 -10 L -3.6 -10.4 Z", "#E0508A", stroke=OUT, width=0.3)
    x.ellipse(-3.2, -12.7, 0.9, 0.9, "#FFD1E3", stroke=OUT, width=0.3)
    x.path("M 1.6 -9.6 Q 2.4 -5 1.6 -1.6 Q 0.8 -0.8 0.4 -2.6 Q 1 -5 0.6 -9.4 Z", "$p.hair", stroke=OUT, width=0.4)  # a lock by the cheek


side("sakura", "torso")(coat("#F4F6FA", "#FFFFFF"))


@side("daichi", "head")
def _daichi_head(x: Recipe) -> None:
    x.path(DOME, linear(0, -17.4, 0, -10, (0, "#FFB44A"), (1, "#C45A1C")), stroke=OUT, width=0.45)
    x.shade(DOME_SHADE, 0.35)
    x.path("M 2 -12.4 Q 6 -12.4 9 -9.6 L 8.6 -8.6 Q 5.6 -10.6 1.6 -10.8 Z", "#B04A16", stroke=OUT, width=0.4)  # the peak
    x.path("M -6.8 -9.8 Q -3 -11.8 0 -12 L -1 -5.6 Q -5 -4.6 -8 -5.4 Z", "#B04A16", stroke=OUT, width=0.4)  # the neck flap
    x.path("M -7.2 -7.4 Q -4 -6.4 -0.8 -7.6", None, stroke="#F0E24A", width=0.8)
    x.path("M -1 -16.6 Q 2 -17 4.4 -15.4", None, stroke="#FFFFFF", width=0.6, alpha=0.5)
    x.ellipse(2.4, -2.6, 1.1, 0.6, "#2A2028", alpha=0.3, blur=0.3)


@side("daichi", "torso")
def _daichi_torso(x: Recipe) -> None:
    for y in (-9.2, -3.6):
        x.path(f"M -4.4 {y} Q 0 {y + 0.8} 4.5 {y} L 4.4 {y + 1.8} Q 0 {y + 2.6} -4.3 {y + 1.8} Z", "#F0E24A", stroke=OUT, width=0.25, clip=True)
        x.path(f"M -4.3 {y + 0.6} Q 0 {y + 1.4} 4.4 {y + 0.6}", None, stroke="#F4F4F8", width=0.45, clip=True)


@side("haruka", "head", behind=True)
def _haruka_tail(x: Recipe) -> None:
    tail(x, "M -3.6 -14.6 Q -11.6 -17 -11 -6 Q -10.6 0 -8 3 Q -8.8 -3 -6.8 -8 Q -5.6 -11 -3.4 -12 Z", "M -8.4 -13.6 Q -10 -9 -9.6 -4")


@side("haruka", "head")
def _haruka_head(x: Recipe) -> None:
    x.path("M -2.6 -15.8 Q -4.6 -17.4 -6.2 -15 Q -5.2 -13.2 -3 -13.6 Z", "#4FB06A", stroke=OUT, width=0.35)
    x.path("M 1.6 -9.6 Q 2.4 -5.6 1.6 -2.6 Q 0.8 -1.8 0.4 -3.6 Q 1 -5.6 0.6 -9.4 Z", "$p.hair", stroke=OUT, width=0.4)
    for fx, fy in ((2.6, -3.8), (3.3, -3.3), (3.9, -3.9)):
        x.ellipse(fx, fy, 0.22, 0.22, "#B8754A", alpha=0.7)


side("haruka", "torso")(apron("#F4F0E6", -11))


@side("marco", "head")
def _marco_head(x: Recipe) -> None:
    x.path(DOME, linear(0, -17.4, 0, -10, (0, "#E8504A"), (1, "#A82428")), stroke=OUT, width=0.45)
    for bx, by in ((-4.4, -12.6), (-1.6, -15.2), (1.8, -14.8), (4.6, -13), (-2.6, -11.8), (1, -12.8)):
        x.ellipse(bx, by, 0.4, 0.4, "#FFFFFF", alpha=0.9)
    x.shade(DOME_SHADE, 0.35)
    x.path("M -6.4 -10 L -10 -11.6 L -9 -8.4 L -10.4 -5.6 L -7 -8 Z", "#C9302C", stroke=OUT, width=0.35)
    x.ellipse(-6.5, -9.7, 0.9, 0.9, "#A82428", stroke=OUT, width=0.3)
    x.path("M 3 -3.3 Q 4.6 -4.2 6 -3 Q 4.6 -2.4 3 -3.3 Z", "#2A1E18", stroke=OUT, width=0.25)
    for sx, sy in ((2.2, -1.6), (3.2, -1), (4.2, -1.2), (1.4, -2.4)):
        x.ellipse(sx, sy, 0.17, 0.17, "#2A1E18", alpha=0.65)


side("marco", "torso")(apron("#FFFFFF", -8.4, stripes="#D03A34"))


@side("yuki", "head", behind=True)
def _yuki_hair(x: Recipe) -> None:
    x.path("M -6.8 -8 Q -7.8 -2 -6.2 1.4 Q -2 2.4 0.6 1 L 0.4 -8 Z", "$p.hair", stroke=OUT, width=0.45)
    x.shade("M -6.8 -8 Q -7.8 -2 -6.2 1.4 Q -4.6 1.8 -3.4 1.8 Q -4.4 -3 -3.6 -8 Z", 0.3)


@side("yuki", "head")
def _yuki_head(x: Recipe) -> None:
    x.path("M 0.6 -8.4 Q 3.4 -9 5.4 -7.6 L 5.5 -6.6 Q 5 -4.6 3.6 -4.2 Q 1.6 -4.4 0.6 -5.6 Z", "#1C1C24", stroke=OUT, width=0.3)  # the mask
    x.ellipse(3.5, -6.3, 0.95, 1.3, "#FFFFFF")
    x.ellipse(3.7, -6.2, 0.7, 1.15, "$p.eye")
    x.ellipse(3.8, -6.2, 0.3, 0.6, OUT)
    x.ellipse(3.4, -6.7, 0.28, 0.28, "#FFFFFF")
    x.path("M -7.4 -10.4 Q -8.6 -18.4 0.4 -18.2 Q 8 -17.8 7 -12.2 Q 0 -14.4 -7.4 -10.4 Z", linear(0, -18, 0, -11, (0, "#3A3A4A"), (1, "#16161E")), stroke=OUT, width=0.45)
    x.path("M -3 -16.6 Q 0 -17.6 3.4 -16.6", None, stroke="#FFFFFF", width=0.6, alpha=0.25)
    x.ellipse(-0.6, -18.5, 0.7, 0.6, "#26262E", stroke=OUT, width=0.3)
    x.path("M 1.6 -9.6 Q 2.4 -5 1.6 -0.8 Q 0.8 0 0.4 -1.8 Q 1 -5 0.6 -9.4 Z", "$p.hair", stroke=OUT, width=0.4)


@side("yuki", "torso")
def _yuki_torso(x: Recipe) -> None:
    x.path("M -4.2 -0.3 Q 0 0.7 4.3 -0.3 L 4.4 1.6 Q 0 2.6 -4.3 1.6 Z", "#1C1C24", stroke=OUT, width=0.3)
    x.path("M -3 -18 Q 0 -16.4 3.2 -18 L 4 -14.6 Q 0 -12.4 -3.8 -14.6 Z", linear(0, -18, 0, -12, (0, "#E04A5A"), (1, "#9A2434")), stroke=OUT, width=0.4)
    x.path("M -3 -15.6 L -8.6 -13 L -9.4 -3 L -6.4 -5.6 L -4.4 -12.4 Z", linear(0, -15, 0, -3, (0, "#D03A4A"), (1, "#8A1E2E")), stroke=OUT, width=0.4)  # the tail, behind
    x.path("M -6.6 -9 L -8.8 -7.4", None, stroke="#7A1828", width=0.4)


@side("lena", "head", behind=True)
def _lena_bun(x: Recipe) -> None:
    x.ellipse(-5.2, -13.4, 3.2, 2.7, "$p.hair", stroke=OUT, width=0.45)
    x.path("M -7 -14.8 Q -5.2 -15.8 -3.4 -14.8", None, stroke="#FFFFFF", width=0.5, alpha=0.3)


@side("lena", "head")
def _lena_head(x: Recipe) -> None:
    lens(x, "#B8C4D4")
    x.path("M 4.6 -10.6 Q 3.6 -14 0.6 -15", None, stroke="#F2F2F8", width=1.0)
    x.line(-7.4, -15, -3, -11.6, "#C8D4E4", 0.5)


side("lena", "torso")(coat("#2A2A36", "#E8ECF4"))


@side("gideon", "head", behind=True)
def _gideon_horn(x: Recipe) -> None:
    x.path("M -1.6 -13.6 Q -7.6 -15.6 -9.6 -22 Q -4.6 -20 -2.4 -17 Q 0.4 -15 1.6 -13.4 Z", linear(0, -22, 0, -12, (0, "#6A4A6A"), (1, "#2B1B30")), stroke=OUT, width=0.45)
    x.path("M -2.6 -15 Q -6 -17 -8.4 -20.4", None, stroke="#C7586A", width=0.4, alpha=0.8)


@side("gideon", "head")
def _gideon_head(x: Recipe) -> None:
    x.path("M -0.4 -7.6 L -5.4 -9.8 L -1.4 -4.4 Z", "$p.skin", stroke=OUT, width=0.4)  # a pointed ear
    x.path("M -6.3 -10 Q 0 -13.8 6 -11.6 L 5.9 -10.4 Q 0 -12.6 -6.2 -8.8 Z", GOLD, stroke=OUT, width=0.3)
    x.poly([(4.6, -13), (5.5, -11.8), (4.6, -10.5), (3.7, -11.8)], "#D8283A", stroke=OUT, width=0.25)
    x.ellipse(3.8, -6.2, 0.2, 1.1, "#1A0A10")
    x.poly([(4.5, -2.5), (5.1, -2.5), (4.8, -1.5)], "#FFFFFF", stroke=OUT, width=0.15)


@side("gideon", "cape", behind=True)
def _gideon_cape(x: Recipe) -> None:
    x.path("M -2.6 0.4 Q -10.6 16 -9.6 42 Q -4 44.4 0.6 42.6 Q -3 20 1.6 0.6 Q 0 -0.6 -2.6 0.4 Z", linear(0, 0, 0, 44, (0, "#B02A40"), (1, "#4A0E1E")), stroke=OUT, width=0.45)
    x.shade("M -2.6 0.4 Q -10.6 16 -9.6 42 L -6 43.4 Q -6.6 18 -0.6 0 Z", 0.3)
    x.path("M -5 10 Q -7.6 26 -6.6 42", None, stroke=OUT, width=0.3, alpha=0.5)
    x.path("M -2.8 0.2 Q 0 -0.9 2 0.4 L 1.6 2.4 Q 0 1.2 -3 2.4 Z", GOLD, stroke=OUT, width=0.3)


@side("gideon", "torso")
def _gideon_torso(x: Recipe) -> None:
    x.ellipse(2.2, -14.6, 1.5, 1.5, GOLD, stroke=OUT, width=0.3)
    x.ellipse(2.2, -14.6, 0.55, 0.55, "#C92A3A")
    x.poly([(3.6, -9), (4.6, -6.6), (3.6, -4), (2.8, -6.6)], None, stroke="#C92A3A", width=0.4)


# ------------------------------------------------------------------------------------------------ the people
@side("red", "head")
def _guard_head(x: Recipe) -> None:
    x.path(DOME, STEEL, stroke=OUT, width=0.45)
    x.path("M -8.2 -9 Q 0 -13 8.4 -10.4 L 8.2 -9 Q 0 -11.4 -8 -7.6 Z", STEEL, stroke=OUT, width=0.4)
    x.path("M -1 -16.6 Q 2 -17 4 -15.6", None, stroke="#FFFFFF", width=0.6, alpha=0.6)


@side("red", "torso")
def _guard_torso(x: Recipe) -> None:
    x.path("M -3.4 -15.8 Q 0 -16.8 3 -15.8 Q 5.2 -11 4.6 -4 Q 0 -2 -4.2 -4 Q -5 -11 -3.4 -15.8 Z", STEEL, stroke=OUT, width=0.45)
    x.path("M 2.4 -14 Q 3.6 -9 3 -5", None, stroke="#FFFFFF", width=0.5, alpha=0.5)
    x.path("M -3.6 -13.4 Q -2 -17.6 2.6 -16.8 Q 3.6 -14 2.4 -12.6 Q -1 -12 -3.6 -13.4 Z", STEEL, stroke=OUT, width=0.4)  # the pauldron


@side("green", "head", behind=True)
def _ranger_hood_back(x: Recipe) -> None:
    x.path("M -7.6 -6 Q -8.8 -18.4 0 -18.6 Q 7 -18.4 6.8 -11 L 2 -11.4 L 0.6 0.8 L -4.6 0.8 Q -6.8 -0.6 -7.6 -6 Z", "#2E5E3A", stroke=OUT, width=0.45)


@side("green", "head")
def _ranger_hood(x: Recipe) -> None:
    x.path("M -7.6 -6 Q -8.8 -18.4 0 -18.6 Q 7 -18.4 6.8 -11 Q 4 -12.4 2 -11.2 Q 0 -9 -0.2 -3 Q -1 0.6 -4.4 0.8 Q -6.8 -0.6 -7.6 -6 Z",
           linear(0, -18, 0, 0, (0, "#5A9A64"), (1, "#356A42")), stroke=OUT, width=0.45)
    x.path("M -5 -14.4 Q -2 -17.4 1.6 -17.6", None, stroke="#FFFFFF", width=0.6, alpha=0.3)
    x.shade("M -7.6 -6 Q -8.8 -18.4 -3 -18.4 Q -5.6 -10 -4 0.8 Q -6.8 -0.6 -7.6 -6 Z", 0.3)


@side("green", "torso")
def _ranger_torso(x: Recipe) -> None:
    x.path("M -5 -14 Q -5 -16.6 -2 -16.8 L 2.6 -16.6 Q 5.2 -15.6 5 -13.6 L 4.4 -9.6 Q 0 -7.6 -4.6 -9.6 Z", linear(0, -16, 0, -8, (0, "#4E8A58"), (1, "#2A5234")), stroke=OUT, width=0.45)
    x.path("M -3.4 -16 L -7.6 -17.6 L -8.4 -5 L -4.6 -4 Z", "#6A4426", stroke=OUT, width=0.4)  # the quiver on the back
    for dx in (0, 1.1, 2.2):
        x.line(-7 + dx, -17.4 + dx * 0.4, -7.6 + dx, -20.4 + dx * 0.4, "#E8E0C8", 0.35)


@side("ochre", "head")
def _farmer_hat(x: Recipe) -> None:
    x.ellipse(0, -11.4, 10.4, 2.4, linear(-10, 0, 10, 0, (0, "#B8963E"), (1, "#F8E4A0")), stroke=OUT, width=0.45)
    x.path("M -5.6 -11.6 Q -5.6 -18.4 0 -18.4 Q 5.6 -18.4 5.6 -11.6 Q 0 -10 -5.6 -11.6 Z", linear(-5, -18, 5, -11, (0, "#C8A650"), (1, "#FFF0B8")), stroke=OUT, width=0.45)
    x.path("M -5.6 -12.8 Q 0 -11.2 5.6 -12.8 L 5.6 -11.6 Q 0 -10 -5.6 -11.6 Z", "#A8503A", stroke=OUT, width=0.25)


@side("ochre", "torso")
def _farmer_torso(x: Recipe) -> None:
    x.path("M 1.6 -16.2 L 2.6 -0.2", None, stroke="#6A4426", width=1.0)
    x.ellipse(2.7, -1, 0.45, 0.45, GOLD)


@side("purple", "head")
def _mage_hat(x: Recipe) -> None:
    x.path("M -5.8 -11.8 Q -3.6 -14 -3 -20 Q -2.6 -26.4 -6.4 -27.4 Q 2 -24 5.8 -11.8 Q 0 -10.2 -5.8 -11.8 Z", linear(-5, -27, 5, -11, (0, "#8A6CD8"), (1, "#3E2E76")), stroke=OUT, width=0.45)
    x.ellipse(0, -11.4, 9.6, 2.2, linear(-9, 0, 9, 0, (0, "#32245E"), (1, "#7A5CC0")), stroke=OUT, width=0.45)
    x.path("M -5.6 -13 Q 0 -11.4 5.6 -13 L 5.8 -11.8 Q 0 -10.2 -5.8 -11.8 Z", GOLD, stroke=OUT, width=0.25)


@side("purple", "torso")
def _mage_robe(x: Recipe) -> None:
    x.path("M -3.8 -16.2 Q 0 -17.2 3.2 -16.2 Q 5.2 -12 4.8 -6 L 6.4 24 Q 0 26.2 -6.4 24 L -4.6 -6 Q -5.2 -12 -3.8 -16.2 Z",
           linear(0, -16, 0, 26, (0, "#6A4CB0"), (1, "#2E2060")), stroke=OUT, width=0.45)
    x.shade("M -3.8 -16.2 Q -5.2 -12 -4.6 -6 L -6.4 24 L -2.4 25.4 Q -1 4 -1.6 -16.6 Z", 0.3)
    x.path("M -4.3 -0.6 Q 0 0.6 4.4 -0.6 L 4.5 1 Q 0 2.2 -4.4 1 Z", GOLD, stroke=OUT, width=0.3)
    x.path("M -6.2 22 Q 0 24.2 6.2 22", None, stroke=GOLD, width=0.6)


@side("teal", "head", behind=True)
def _traveler_bun(x: Recipe) -> None:
    x.ellipse(-3.6, -15.6, 3.2, 2.6, "$p.hair", stroke=OUT, width=0.45)


@side("teal", "head")
def _traveler_band(x: Recipe) -> None:
    x.path("M -6.3 -10.6 Q 0 -14.4 6.1 -12.4 L 5.9 -10.8 Q 0 -12.8 -6.2 -9 Z", "#2E9AB8", stroke=OUT, width=0.35)
    x.path("M -6 -10 L -9.6 -8 L -7.4 -7.4 L -10 -4 L -6.2 -7.8 Z", "#2E9AB8", stroke=OUT, width=0.3)


@side("teal", "torso")
def _traveler_sash(x: Recipe) -> None:
    x.path("M -3.6 -15.8 L -1.4 -16.4 L 4.3 -1.4 L 4.3 1 L 2.4 1.2 Z", linear(0, -16, 0, 1, (0, "#F0C860"), (1, "#B8862A")), stroke=OUT, width=0.4)


@side("cream", "head")
def _baker_hat(x: Recipe) -> None:
    for cx, cy, rx, ry in ((-3.6, -19.4, 3.6, 3.0), (3.6, -19.4, 3.6, 3.0), (0, -21.4, 4.2, 3.4)):
        x.ellipse(cx, cy, rx, ry, linear(cx - rx, cy - ry, cx + rx, cy + ry, (0, "#C8CCE0"), (1, "#FFFFFF")), stroke=OUT, width=0.4)
    x.path("M -5.8 -17.8 L 5.8 -17.8 L 6.1 -11.8 Q 0 -13.4 -6.1 -10.6 Z", linear(-6, 0, 6, 0, (0, "#C8CCE0"), (1, "#FFFFFF")), stroke=OUT, width=0.4)


side("cream", "torso")(apron("#FFFFFF", -9))


@side("brown", "head")
def _laborer_head(x: Recipe) -> None:
    x.path(DOME, linear(0, -17.4, 0, -10, (0, "#8A6444"), (1, "#4E3422")), stroke=OUT, width=0.45)
    x.path("M 1 -12.6 Q 6.6 -13 10 -9.6 Q 6 -10.4 1.6 -10.6 Z", "#4A3020", stroke=OUT, width=0.4)  # the visor
    x.path("M 0.6 -4.6 Q 0 1.6 3.6 2.4 Q 6.2 1.6 5.6 -2.6 Q 4.2 -1.4 3 -2 Q 1.6 -2.4 0.6 -4.6 Z", "$p.hair", stroke=OUT, width=0.4)  # the beard


@side("brown", "torso")
def _laborer_torso(x: Recipe) -> None:
    x.path("M 1.6 -16.2 L 2.6 -0.2", None, stroke="#3E2A1A", width=1.1)
    x.rect(0.6, 1.2, 2.8, 3, "#6A4426", stroke=OUT, width=0.3)
