"""The looks of the people: what makes each protagonist and each kind of villager different from the base figure.

A look is a function that draws on a part of the humanoid rig (head, torso, arm, leg, cape) in the units of that part (around
its joint, see `art_chars.py`); `art_chars.py` gives its layers to the palette variant of that person (`only`), or to the
base figure alone (`except`, Ren). A look is in front of the part or behind it (a ponytail, a cape) and is told whether the
part is seen from behind (`back`). `LOOKS[(person, part)]` is a list of `(behind, function)`. Spec 13 has `only`/`except`.

Units of the parts: head, the neck joint is (0, 0), the face goes from y -13.9 to -0.3 and x -5.4 to 5.4, the eyes are at
y -6; torso, the waist is (0, 0), the shoulders are at y -16 and x +/-7.7, the hem at y 4; arm, the shoulder is (0, 0) and
the hand ends at y 18.8; leg, the hip is (0, 0), the boot goes from y 17 to 27; cape, the neck is (0, 0), the feet at y 45.
"""
from __future__ import annotations

from artkit import Recipe, darken, lighten, linear

OUT = "$p.outline"
GOLD = "#E0BE60"
PROTAGONISTS = ["sakura", "daichi", "haruka", "marco", "yuki", "lena", "gideon"]
PEOPLE = ["red", "green", "ochre", "purple", "teal", "cream", "brown"]
LOOKS: dict = {}

SLEEVE = "M -2.1 -0.8 Q 0 -1.8 2.1 -0.8 Q 2.4 6 1.8 13.6 L -1.8 13.6 Q -2.4 6 -2.1 -0.8 Z"
HAND = "M -1.5 13.4 L 1.5 13.4 Q 2 15.4 1.6 17.2 Q 1 18.8 0 18.8 Q -1 18.8 -1.6 17.2 Q -2 15.4 -1.5 13.4 Z"
LEG = "M -2.7 -0.5 L 2.7 -0.5 Q 2.6 7 2.2 12.5 L 2 19.5 L -2 19.5 L -2.2 12.5 Q -2.6 7 -2.7 -0.5 Z"
BOOT = "M -2.3 17.2 L 2.3 17.2 L 2.5 24.6 Q 2.9 27.2 0.7 27.2 L -1.7 27.2 Q -3 27.2 -2.6 24.6 Z"
DOME = "M -6.6 -10.2 Q -7.4 -17.2 0 -17.4 Q 7.4 -17.2 6.6 -10.2 Q 0 -12.4 -6.6 -10.2 Z"  # what a cap covers of the head
DOME_SHADE = "M 1.6 -17.3 Q 7.4 -17.2 6.6 -10.2 Q 4 -11.2 2.6 -11.4 Q 3.6 -14 1.6 -17.3 Z"
STEEL = linear(-6, 0, 6, 0, (0, "#E4E8F0"), (0.5, "#8A90A0"), (1, "#4A4E5C"))


def look(person: str, part: str, behind: bool = False):
    def register(fn):
        LOOKS.setdefault((person, part), []).append((behind, fn))
        return fn
    return register


def cloth(x: Recipe, d: str, color: str, width: float = 0.4, tone: float = 0.2) -> None:
    """A piece of clothing: its color fading to a darker one at the bottom, with the thin line."""
    if color.startswith("$"):
        x.path(d, color, stroke=OUT, width=width)
    else:
        x.path(d, linear(0, -16, 0, 12, (0, lighten(color, 0.08)), (1, darken(color, tone))), stroke=OUT, width=width)


def glasses(x: Recipe, color: str) -> None:
    for cx in (-2.55, 2.55):
        x.ellipse(cx, -6.0, 2.05, 1.95, "#CFEFFF", alpha=0.16, stroke=color, width=0.35)
        x.path(f"M {cx - 1.3} -6.9 L {cx - 0.5} -7.5", None, stroke="#FFFFFF", width=0.3, alpha=0.8)
    x.line(-0.55, -6.3, 0.55, -6.3, color, 0.35)
    for sx in (-1, 1):
        x.line(sx * 4.55, -6.4, sx * 5.6, -6.8, color, 0.3)


def long_coat(color: str, lapel: str, lining: str):
    """A coat open at the front, down to the knees; from behind, its back with a seam."""
    def build(x: Recipe, back: bool) -> None:
        if back:
            cloth(x, "M -7.9 -14.6 Q -8.4 -15.6 -6 -16 L 6 -16 Q 8.4 -15.6 7.9 -14.6 L 6.6 -6 L 8.2 12.6 Q 0 14.6 -8.2 12.6 L -6.6 -6 Z", color)
            x.shade("M 2 -16 L 6 -16 Q 8.4 -15.6 7.9 -14.6 L 6.6 -6 L 8.2 12.6 L 3 13.8 Q 4.6 0 2 -16 Z", 0.3)
            x.path("M 0 -15.8 L 0 13.8", None, stroke=OUT, width=0.25, alpha=0.5)
            x.path("M -6.4 -1.4 L 6.4 -1.4 L 6.5 0.2 L -6.5 0.2 Z", lapel, stroke=OUT, width=0.3)
            x.path("M -2.4 -16.2 Q 0 -14.6 2.4 -16.2 L 2.8 -17.2 Q 0 -15.8 -2.8 -17.2 Z", lapel, stroke=OUT, width=0.3)
            return
        for sx in (-1, 1):
            d = (f"M {sx * 7.9} -14.6 Q {sx * 8.4} -15.6 {sx * 6} -16 L {sx * 2.6} -16.6 L {sx * 1.6} -6 L {sx * 2.6} 13.4 "
                 f"Q {sx * 5.6} 13.6 {sx * 8.2} 12.6 L {sx * 6.6} -6 Z")
            cloth(x, d, color)
            x.path(f"M {sx * 2.6} -16.6 L {sx * 0.9} -8.6 L {sx * 4.2} -11.4 Z", lapel, stroke=OUT, width=0.3)
            x.path(f"M {sx * 2.2} -3 L {sx * 2.6} 13.2", None, stroke=lining, width=0.5, alpha=0.8)
        x.shade("M 2.6 -16.6 L 6 -16 Q 8.4 -15.6 7.9 -14.6 L 6.6 -6 L 8.2 12.6 L 4.6 13.4 Q 5.6 0 2.6 -16.6 Z", 0.3)
        x.rect(3.4, 1.6, 2.8, 3.2, color, stroke=OUT, width=0.3)  # a pocket
    return build


def apron(color: str, top: float, stripes: str | None = None, emblem=None):
    def build(x: Recipe, back: bool) -> None:
        if back:  # the straps and their bow
            x.path("M -5.6 -15.6 L 0.6 -0.6 M 5.6 -15.6 L -0.6 -0.6", None, stroke=color, width=1.1)
            x.path("M -6.2 -0.8 Q 0 0.4 6.2 -0.8", None, stroke=color, width=1.2)
            for sx in (-1, 1):
                x.path(f"M 0 0 Q {sx * 3} -2.6 {sx * 3.4} 0.4 Q {sx * 2.6} 2 0 0 Z", color, stroke=OUT, width=0.3)
                x.path(f"M 0 0 L {sx * 1.6} 5.4", None, stroke=color, width=0.9)
            return
        cloth(x, f"M -4.4 {top} L 4.4 {top} L 5.6 -1 L 7 12.4 Q 0 14 -7 12.4 L -5.6 -1 Z", color, tone=0.12)
        if stripes:
            for sx in (-4.4, -1.5, 1.5, 4.4):
                x.path(f"M {sx - 0.6} {top + 0.4} L {sx + 0.6} {top + 0.4} L {sx * 1.3 + 0.7} 12.8 L {sx * 1.3 - 0.7} 12.8 Z", stripes, alpha=0.75)
        x.shade(f"M 1.6 {top} L 4.4 {top} L 5.6 -1 L 7 12.4 L 3 13.4 Q 4 2 1.6 {top} Z", 0.25)
        x.path(f"M -4.4 {top} L -5.4 -15.8 M 4.4 {top} L 5.4 -15.8", None, stroke=color, width=1.0)
        x.path("M -5.7 -0.6 Q 0 0.6 5.7 -0.6", None, stroke=OUT, width=0.25, alpha=0.5)
        if emblem:
            emblem(x)
    return build


def bare_forearm(band: str | None = None):
    def build(x: Recipe, back: bool) -> None:
        x.path("M -1.95 6 L 1.95 6 L 1.8 13.6 L -1.8 13.6 Z", "$p.skin", stroke=OUT, width=0.4)
        x.shade("M 0.4 6 L 1.95 6 L 1.8 13.6 L 0.3 13.6 Z", 0.3, "#B06A80")
        x.path("M -2.2 5.2 L 2.2 5.2 L 2.1 6.8 L -2.1 6.8 Z", "$p.shirt_dark", stroke=OUT, width=0.35)  # the rolled sleeve
        if band:
            x.path("M -1.9 11.4 L 1.9 11.4 L 1.8 13.2 L -1.8 13.2 Z", band, stroke=OUT, width=0.3)
    return build


def sleeve(color: str, cuff: str | None = None, glove: str | None = None):
    def build(x: Recipe, back: bool) -> None:
        if glove:
            x.path(HAND, glove, stroke=OUT, width=0.35)
        cloth(x, SLEEVE, color)
        x.shade("M 0.5 -1.6 Q 2.1 -1.2 2.1 -0.8 Q 2.4 6 1.8 13.6 L 0.3 13.6 Q 1 6 0.5 -1.6 Z", 0.32)
        if cuff:
            x.path("M -1.95 11.6 L 1.95 11.6 L 1.8 13.6 L -1.8 13.6 Z", cuff, stroke=OUT, width=0.35)
    return build


def trousers(color: str, boot: str | None = None, band: str | None = None):
    def build(x: Recipe, back: bool) -> None:
        cloth(x, LEG, color)
        x.shade("M 0.6 -0.5 L 2.7 -0.5 Q 2.6 7 2.2 12.5 L 2 19.5 L 0.4 19.5 Q 1.2 9 0.6 -0.5 Z", 0.35)
        if boot:
            cloth(x, BOOT, boot)
            x.shade("M 0.6 17.2 L 2.3 17.2 L 2.5 24.6 Q 2.9 27.2 0.7 27.2 Z", 0.35)
        if band:
            x.path("M -2.35 17.2 L 2.35 17.2 L 2.4 19 L -2.4 19 Z", band, stroke=OUT, width=0.3)
    return build


def plate(d: str):
    return lambda x, back: x.path(d, STEEL, stroke=OUT, width=0.35)


def hair_tail(x: Recipe, d: str, light: str) -> None:
    x.path(d, "$p.hair", stroke=OUT, width=0.45)
    x.path(light, None, stroke="#FFFFFF", width=0.7, alpha=0.3, blend="add", clip=True)


def sidelocks(x: Recipe, length: float = -1.0) -> None:
    """Locks of hair framing the face, down to `length`."""
    for sx in (-1, 1):
        x.path(f"M {sx * 6.1} -9.6 Q {sx * 6.9} -5 {sx * 6.1} {length} Q {sx * 5.2} {length + 0.9} {sx * 4.7} {length - 1} Q {sx * 5.3} -5 {sx * 4.9} -9.4 Z",
               "$p.hair", stroke=OUT, width=0.4)


# ------------------------------------------------------------------------------------------------ Ren (the base figure)
@look("ren", "head")
def _ren_head(x: Recipe, back: bool) -> None:  # the glasses of a tired office worker
    if not back:
        glasses(x, "#2A2A36")


@look("ren", "torso")
def _ren_torso(x: Recipe, back: bool) -> None:  # a tie, loosened
    if back:
        return
    x.path("M -1.1 -14 L 1.1 -14 L 0.8 -12.2 L -0.8 -12.2 Z", "#B8323A", stroke=OUT, width=0.3)
    x.path("M -0.8 -12.2 L 0.8 -12.2 L 1.5 -2.6 L 0 -0.8 L -1.5 -2.6 Z", linear(0, -12, 0, -1, (0, "#D04450"), (1, "#8A1E2A")), stroke=OUT, width=0.3)
    x.path("M -0.9 -9 L 1 -8 M -1.1 -6 L 1.2 -5", None, stroke="#FFFFFF", width=0.25, alpha=0.35)


@look("ren", "arm")
def _ren_arm(x: Recipe, back: bool) -> None:  # a wristwatch
    x.rect(-1.7, 12.9, 3.4, 0.9, "#3A3A44", stroke=OUT, width=0.2)
    x.rect(-0.7, 12.75, 1.4, 1.2, "#DDE8F0", stroke=OUT, width=0.2)


# ------------------------------------------------------------------------------------------------ Sakura
@look("sakura", "head", behind=True)
def _sakura_tails(x: Recipe, back: bool) -> None:  # two long tails
    for sx in (-1, 1):
        hair_tail(x, f"M {sx * 5.6} -12.6 Q {sx * 12.4} -13.6 {sx * 12} -2 Q {sx * 11.8} 5 {sx * 9.4} 9.6 Q {sx * 9.8} 3 {sx * 8.2} -1 Q {sx * 7.4} -6 {sx * 5.8} -9 Z",
                  f"M {sx * 9} -11 Q {sx * 10.8} -6 {sx * 10.6} 0")


@look("sakura", "head")
def _sakura_head(x: Recipe, back: bool) -> None:  # ribbons, goggles pushed up on the forehead
    if not back:
        sidelocks(x, -1.6)
        x.path("M -5.9 -13 Q 0 -14.6 5.9 -13 L 5.8 -11.4 Q 0 -13 -5.8 -11.4 Z", "#3A3A48", stroke=OUT, width=0.35)
        for cx in (-2.7, 2.7):
            x.ellipse(cx, -12.5, 2.0, 1.45, linear(cx - 2, -14, cx + 2, -11, (0, "#D8F8FF"), (1, "#3A9AD8")), stroke=OUT, width=0.35)
            x.ellipse(cx - 0.6, -12.9, 0.6, 0.35, "#FFFFFF", alpha=0.9)
    for sx in (-1, 1):
        bx = sx * 6.4
        x.path(f"M {bx} -12.4 L {bx + sx * 3.4} -14.6 L {bx + sx * 3} -11.6 Z", "#FF6FA8", stroke=OUT, width=0.3)
        x.path(f"M {bx} -12.4 L {bx + sx * 2.4} -9.6 L {bx + sx * 0.4} -10 Z", "#E0508A", stroke=OUT, width=0.3)
        x.ellipse(bx, -12.3, 0.9, 0.9, "#FFD1E3", stroke=OUT, width=0.3)


look("sakura", "torso")(long_coat("#F4F6FA", "#FFFFFF", "#C8D0E0"))


@look("sakura", "torso")
def _sakura_pens(x: Recipe, back: bool) -> None:
    if not back:
        x.rect(3.9, 0.2, 0.6, 2.4, "#E04A4A")
        x.rect(4.8, 0.5, 0.6, 2.1, "#4A7AE0")
        x.ellipse(-4.6, -11.4, 0.9, 0.9, "#FFD860", stroke=OUT, width=0.25)  # a badge


look("sakura", "arm")(sleeve("#F4F6FA", "#DDE3EE"))


@look("sakura", "leg")
def _sakura_leg(x: Recipe, back: bool) -> None:  # long socks, white boots with a pink band
    x.path("M -2.25 9 L 2.25 9 L 2 19.5 L -2 19.5 Z", "#F6F6FC", stroke=OUT, width=0.35)
    x.path("M -2.25 9 L 2.25 9 L 2.2 10.2 L -2.2 10.2 Z", "#E04A6A")
    cloth(x, BOOT, "#F2F2F8", tone=0.1)
    x.path("M -2.35 17.2 L 2.35 17.2 L 2.4 19 L -2.4 19 Z", "#FF6FA8", stroke=OUT, width=0.3)
    x.shade("M 0.6 9 L 2.25 9 L 2.5 24.6 Q 2.9 27.2 0.7 27.2 Z", 0.25)


# ------------------------------------------------------------------------------------------------ Daichi
@look("daichi", "head")
def _daichi_head(x: Recipe, back: bool) -> None:  # a firefighter's helmet with a badge, and a soot smudge
    x.path(DOME, linear(0, -17.4, 0, -10, (0, "#FFB44A"), (1, "#C45A1C")), stroke=OUT, width=0.45)
    x.path("M -1.1 -17.3 Q 0 -18.4 1.1 -17.3 L 1 -11.4 L -1 -11.4 Z", "#FFD08A", alpha=0.55)
    x.shade(DOME_SHADE, 0.35)
    if back:
        x.path("M -6.8 -10.6 Q 0 -12.6 6.8 -10.6 L 8 -5.4 Q 0 -3.4 -8 -5.4 Z", "#B04A16", stroke=OUT, width=0.4)  # the neck flap
        x.path("M -7.2 -8 Q 0 -6 7.2 -8", None, stroke="#F0E24A", width=0.9)
        return
    x.path("M -7.6 -10.4 Q 0 -12.8 7.6 -10.4 L 7.4 -9.2 Q 0 -11.4 -7.4 -9.2 Z", "#B04A16", stroke=OUT, width=0.4)
    x.path("M -1.9 -15.6 L 1.9 -15.6 L 1.9 -13.2 L 0 -11.9 L -1.9 -13.2 Z", "#F6E7B8", stroke=OUT, width=0.3)
    x.line(0, -15, 0, -12.8, "#C45A1C", 0.4)
    x.path("M -5 -15 Q -3 -16.8 -0.6 -17", None, stroke="#FFFFFF", width=0.6, alpha=0.5)
    x.ellipse(3.2, -2.9, 1.3, 0.7, "#2A2028", alpha=0.3, blur=0.3)


@look("daichi", "torso")
def _daichi_torso(x: Recipe, back: bool) -> None:  # the bands of the turnout coat
    for y in (-9.2, -3.6):
        x.path(f"M -6.4 {y} Q 0 {y + 1} 6.4 {y} L 6.3 {y + 1.8} Q 0 {y + 2.8} -6.3 {y + 1.8} Z", "#F0E24A", stroke=OUT, width=0.25, clip=True)
        x.path(f"M -6.3 {y + 0.6} Q 0 {y + 1.6} 6.3 {y + 0.6}", None, stroke="#F4F4F8", width=0.45, clip=True)
    if not back:
        x.path("M -0.9 -13 L 0.9 -13 L 0.9 -0.4 L -0.9 -0.4 Z", "$p.shirt_dark", stroke=OUT, width=0.3)
        for y in (-11.4, -7, -2.2):
            x.rect(-0.55, y, 1.1, 0.7, "#C8CCD4")
    else:
        x.path("M -4 -13.6 L 4 -13.6 L 4 -10.6 L -4 -10.6 Z", "#F0E24A", stroke=OUT, width=0.25)


@look("daichi", "arm")
def _daichi_arm(x: Recipe, back: bool) -> None:
    x.path(HAND, "#2A2A36", stroke=OUT, width=0.35)
    x.path("M -2.25 8 L 2.25 8 L 2.2 9.8 L -2.2 9.8 Z", "#F0E24A", stroke=OUT, width=0.25)
    x.path("M -2.2 8.6 L 2.2 8.6", None, stroke="#F4F4F8", width=0.4)
    x.path("M -2 11.6 L 2 11.6 L 1.9 13.8 L -1.9 13.8 Z", "#2A2A36", stroke=OUT, width=0.3)


@look("daichi", "leg")
def _daichi_leg(x: Recipe, back: bool) -> None:
    x.path("M -2.5 12.6 L 2.5 12.6 L 2.5 14.4 L -2.5 14.4 Z", "#F0E24A", stroke=OUT, width=0.25)
    x.path("M -2.5 13.2 L 2.5 13.2", None, stroke="#F4F4F8", width=0.4)
    x.path("M -2.5 17.2 L 2.5 17.2 L 2.7 24.6 Q 3.1 27.4 0.7 27.4 L -1.9 27.4 Q -3.2 27.4 -2.8 24.6 Z", "#1E1E22", stroke=OUT, width=0.45)
    x.path("M -2.5 17.2 L 2.5 17.2 L 2.55 18.6 L -2.55 18.6 Z", "#3A3A44")
    x.path("M -2.4 24.8 Q -0.6 23.2 1.4 24.2", None, stroke="#FFFFFF", width=0.4, alpha=0.3)


# ------------------------------------------------------------------------------------------------ Haruka
@look("haruka", "head", behind=True)
def _haruka_tail(x: Recipe, back: bool) -> None:  # a high ponytail
    if not back:
        hair_tail(x, "M 2.6 -15.4 Q 11.6 -19 11.4 -7 Q 11.2 -1 8.8 2.4 Q 9.4 -4 7.2 -8.6 Q 6.2 -11.6 3.4 -12.6 Z", "M 8.6 -14.6 Q 10.6 -10 10 -4")


@look("haruka", "head")
def _haruka_head(x: Recipe, back: bool) -> None:  # a green ribbon, a paw clip, freckles
    if back:
        hair_tail(x, "M -2.4 -15 Q -3.6 -6 -2.6 3 Q 0 6 2.6 3 Q 3.6 -6 2.4 -15 Q 0 -16.4 -2.4 -15 Z", "M -1.2 -12 Q -1.8 -5 -1 1")
        x.shade("M 0.6 -15.6 Q 3.6 -6 2.6 3 Q 1.4 4.6 0.4 4.8 Q 1.6 -6 0.6 -15.6 Z", 0.35)
        x.path("M -3 -15 Q 0 -17 3 -15 L 2.8 -13 Q 0 -14.6 -2.8 -13 Z", "#4FB06A", stroke=OUT, width=0.35)
        return
    sidelocks(x, -2.6)
    x.path("M 2.4 -16 Q 4.4 -17.6 6.2 -15.4 Q 5.2 -13.4 3 -13.6 Z", "#4FB06A", stroke=OUT, width=0.35)
    x.ellipse(-4.3, -12.1, 0.95, 0.8, "#F6F6F6", stroke=OUT, width=0.25)
    for dx in (-0.7, 0, 0.7):
        x.ellipse(-4.3 + dx, -13.1, 0.3, 0.32, "#F6F6F6", stroke=OUT, width=0.2)
    for fx, fy in ((-3.9, -3.6), (-3.1, -3.1), (-2.5, -3.7), (2.5, -3.7), (3.1, -3.1), (3.9, -3.6)):
        x.ellipse(fx, fy, 0.22, 0.22, "#B8754A", alpha=0.7)


def _paw(x: Recipe) -> None:
    x.ellipse(0, -3.6, 1.5, 1.2, "#4FB06A")
    for dx in (-1.6, -0.55, 0.55, 1.6):
        x.ellipse(dx, -5.5 + abs(dx) * 0.25, 0.5, 0.65, "#4FB06A")


look("haruka", "torso")(apron("#F4F0E6", -11, emblem=_paw))
look("haruka", "arm")(bare_forearm("#4FB06A"))
look("haruka", "leg")(trousers("#6A5A44", "#3E8A5A", "#F4F0E6"))


# ------------------------------------------------------------------------------------------------ Marco
@look("marco", "head")
def _marco_head(x: Recipe, back: bool) -> None:  # a red bandana, a thick mustache and stubble
    x.path(DOME, linear(0, -17.4, 0, -10, (0, "#E8504A"), (1, "#A82428")), stroke=OUT, width=0.45)
    for bx, by in ((-4.4, -13.6), (-1.6, -15.4), (1.8, -14.8), (4.4, -12.8), (-3, -11.6), (0.4, -12.6), (3.2, -15.8)):
        x.ellipse(bx, by, 0.4, 0.4, "#FFFFFF", alpha=0.9)
    x.shade(DOME_SHADE, 0.35)
    knot = 0 if back else 6.2
    x.path(f"M {knot} -11 L {knot + 3.6} -12.6 L {knot + 2.6} -9.4 L {knot + 4} -6.6 L {knot + 0.6} -9 Z", "#C9302C", stroke=OUT, width=0.35)
    x.ellipse(knot + 0.2, -10.6, 0.9, 0.9, "#A82428", stroke=OUT, width=0.3)
    if back:
        return
    x.path("M -2.9 -2.9 Q -1.4 -4.1 0 -3.3 Q 1.4 -4.1 2.9 -2.9 Q 1.4 -2.2 0 -2.7 Q -1.4 -2.2 -2.9 -2.9 Z", "#2A1E18", stroke=OUT, width=0.25)
    for sx, sy in ((-3.4, -1.9), (-2.4, -1.1), (-1.2, -0.7), (0, -0.6), (1.2, -0.7), (2.4, -1.1), (3.4, -1.9), (-1.8, -1.5), (1.8, -1.5)):
        x.ellipse(sx, sy, 0.17, 0.17, "#2A1E18", alpha=0.65)


def _spanner(x: Recipe) -> None:
    x.rect(3, 4.6, 3, 2.4, "#C9302C", stroke=OUT, width=0.25)
    x.ellipse(-3.6, 6.4, 1.5, 1.5, "#8A929C", stroke=OUT, width=0.3)
    x.ellipse(-3.6, 6.4, 0.55, 0.55, "#3A4048")


look("marco", "torso")(apron("#FFFFFF", -8.4, stripes="#D03A34", emblem=_spanner))
look("marco", "arm")(bare_forearm("#8A5A32"))


@look("marco", "leg")
def _marco_leg(x: Recipe, back: bool) -> None:  # a cargo pocket
    x.rect(-2.1, 6, 3.4, 3.6, "$p.pants", stroke=OUT, width=0.3)
    x.line(-2.1, 7.2, 1.3, 7.2, OUT, 0.25, alpha=0.6)


# ------------------------------------------------------------------------------------------------ Yuki
@look("yuki", "head", behind=True)
def _yuki_hair(x: Recipe, back: bool) -> None:  # a bob down to the jaw
    x.path("M -6.6 -8 Q -7.6 -2 -6.2 1.4 Q 0 2.6 6.2 1.4 Q 7.6 -2 6.6 -8 Z", "$p.hair", stroke=OUT, width=0.45)
    x.shade("M 1 -8 L 6.6 -8 Q 7.6 -2 6.2 1.4 Q 3 2.2 1 2.2 Z", 0.35)


@look("yuki", "head")
def _yuki_head(x: Recipe, back: bool) -> None:  # a black beret and a domino mask
    if back:
        x.path("M -6.2 -7 Q -6.8 -1 -5.4 1.2 Q 0 2.4 5.4 1.2 Q 6.8 -1 6.2 -7 Z", "$p.hair", stroke=OUT, width=0.45)
        x.shade("M 1 -7 L 6.2 -7 Q 6.8 -1 5.4 1.2 Q 3 2 1 2 Z", 0.35)
    else:
        sidelocks(x, -0.6)
        mask = "M -5.2 -7.8 Q 0 -9 5.2 -7.8 Q 5.6 -5.4 4.6 -4.2 Q 2.6 -4.6 1 -3.9 L -1 -3.9 Q -2.6 -4.6 -4.6 -4.2 Q -5.6 -5.4 -5.2 -7.8 Z"
        x.path(mask, "#1C1C24", stroke=OUT, width=0.3)
        for cx in (-2.55, 2.55):
            x.ellipse(cx, -6.0, 1.45, 1.4, "#FFFFFF")
            x.ellipse(cx, -5.9, 1.05, 1.3, "$p.eye")
            x.ellipse(cx, -6.0, 0.45, 0.7, OUT)
            x.ellipse(cx - 0.45, -6.5, 0.36, 0.36, "#FFFFFF")
    x.path("M -7 -11.4 Q -8.4 -18.6 0.6 -18.2 Q 8.6 -17.8 7 -12.4 Q 0 -14.2 -7 -11.4 Z", linear(0, -18, 0, -11, (0, "#3A3A4A"), (1, "#16161E")), stroke=OUT, width=0.45)
    x.path("M -5.4 -15 Q -2 -17.6 2.4 -17.4", None, stroke="#FFFFFF", width=0.6, alpha=0.25)
    x.ellipse(1.4, -18.5, 0.7, 0.6, "#26262E", stroke=OUT, width=0.3)


@look("yuki", "torso")
def _yuki_torso(x: Recipe, back: bool) -> None:  # a long red scarf and a dark belt
    x.path("M -6.3 -0.3 Q 0 0.9 6.3 -0.3 L 6.4 1.6 Q 0 2.8 -6.4 1.6 Z", "#1C1C24", stroke=OUT, width=0.3)
    x.path("M -4.4 -18.2 Q 0 -16 4.4 -18.2 L 5.2 -14.6 Q 0 -11.6 -5.2 -14.6 Z", linear(0, -18, 0, -12, (0, "#E04A5A"), (1, "#9A2434")), stroke=OUT, width=0.4)
    x.path("M -4.6 -16.4 Q 0 -13.8 4.6 -16.4", None, stroke="#7A1828", width=0.35)
    if back:
        for sx, end in ((-1, 9), (1, 6)):
            x.path(f"M {sx * 0.4} -14 L {sx * 3.6} -14.4 L {sx * 4.4} {end} L {sx * 1.2} {end - 1.2} Z", linear(0, -14, 0, 9, (0, "#D03A4A"), (1, "#8A1E2E")), stroke=OUT, width=0.4)
            x.path(f"M {sx * 1.4} {end - 5} L {sx * 4.1} {end - 4.4}", None, stroke="#7A1828", width=0.4)
    else:
        x.path("M 1.6 -13.6 L 5 -14.4 L 5.4 3.6 L 2.4 2.6 Z", linear(0, -14, 0, 4, (0, "#D03A4A"), (1, "#8A1E2E")), stroke=OUT, width=0.4)
        x.path("M 2.2 -3 L 5.2 -2.4 M 2.3 0.4 L 5.3 1", None, stroke="#7A1828", width=0.4)


look("yuki", "arm")(sleeve("$p.shirt", "#1C1C24", "#1C1C24"))
look("yuki", "leg")(trousers("#1C1C24", "#26262E", "#C23A4A"))


# ------------------------------------------------------------------------------------------------ Lena
@look("lena", "head", behind=True)
def _lena_bun(x: Recipe, back: bool) -> None:  # a tight bun
    if not back:
        x.ellipse(0, -17, 3.4, 2.7, "$p.hair", stroke=OUT, width=0.45)
        x.path("M -2 -18.4 Q 0 -19.4 2 -18.2", None, stroke="#FFFFFF", width=0.5, alpha=0.3)


@look("lena", "head")
def _lena_head(x: Recipe, back: bool) -> None:  # thin silver glasses and a white streak
    if back:
        x.ellipse(0, -11, 3.6, 3.2, "$p.hair", stroke=OUT, width=0.45)
        x.shade("M 0.6 -14.2 Q 3.8 -13 3.5 -10 Q 3 -8 0.4 -7.8 Q 2 -11 0.6 -14.2 Z", 0.35)
        x.line(-3.6, -13.2, 3.4, -9, "#C8D4E4", 0.5)
        x.ellipse(-3.6, -13.2, 0.6, 0.6, "#E0508A", stroke=OUT, width=0.2)
        return
    glasses(x, "#B8C4D4")
    x.path("M -4.9 -9.9 Q -5.6 -13.4 -3.2 -15", None, stroke="#F2F2F8", width=1.0)


look("lena", "torso")(long_coat("#2A2A36", "#E8ECF4", "#5A5A6C"))


@look("lena", "torso")
def _lena_chain(x: Recipe, back: bool) -> None:
    if not back:
        x.path("M -1.6 -12.6 Q -3.6 -7 -3.2 -3.4", None, stroke="#C8D4E4", width=0.35)
        x.ellipse(-3.2, -2.8, 0.9, 0.9, "#E8ECF4", stroke=OUT, width=0.25)


look("lena", "arm")(sleeve("#2A2A36", "#E8ECF4", "#E4EAF4"))
look("lena", "leg")(trousers("#2E2E3C", "#3A3A48"))


# ------------------------------------------------------------------------------------------------ Gideon
@look("gideon", "head", behind=True)
def _gideon_horns(x: Recipe, back: bool) -> None:  # swept horns and pointed ears
    for sx in (-1, 1):
        horn = f"M {sx * 3.2} -13.4 Q {sx * 8.4} -15.6 {sx * 9.6} -22 Q {sx * 5.6} -19.4 {sx * 6.2} -12 Z"
        x.path(horn, linear(0, -22, 0, -12, (0, "#6A4A6A"), (1, "#2B1B30")), stroke=OUT, width=0.45)
        x.path(f"M {sx * 5} -13.6 Q {sx * 7.8} -16 {sx * 8.8} -20", None, stroke="#C7586A", width=0.4, alpha=0.8)
        x.path(f"M {sx * 5.6} -8 L {sx * 10} -9.8 L {sx * 6.2} -4.6 Z", "$p.skin", stroke=OUT, width=0.4)


@look("gideon", "head")
def _gideon_head(x: Recipe, back: bool) -> None:  # slit pupils, fangs, a golden circlet
    x.path("M -6.3 -11.6 Q 0 -13.6 6.3 -11.6 L 6.2 -10.4 Q 0 -12.4 -6.2 -10.4 Z", GOLD, stroke=OUT, width=0.3)
    if back:
        return
    for cx in (-2.55, 2.55):
        x.ellipse(cx, -5.9, 0.22, 1.2, "#1A0A10")
    x.poly([(0, -13.7), (0.9, -12.4), (0, -11.1), (-0.9, -12.4)], "#D8283A", stroke=OUT, width=0.25)
    for fx in (-0.75, 0.75):
        x.poly([(fx - 0.3, -2.2), (fx + 0.3, -2.2), (fx, -1.2)], "#FFFFFF", stroke=OUT, width=0.15)


@look("gideon", "cape")
def _gideon_cape(x: Recipe, back: bool) -> None:
    shape = "M -8.6 0.6 Q -13.8 20 -13 42 Q -6 44.6 0 43 Q 6 44.6 13 42 Q 13.8 20 8.6 0.6 Q 0 -1.4 -8.6 0.6 Z"
    if back:
        x.path(shape, linear(0, 0, 0, 44, (0, "#3A2444"), (1, "#18101E")), stroke=OUT, width=0.45)
        x.shade("M 2 -0.6 L 8.6 0.6 Q 13.8 20 13 42 Q 8 44 4 43.6 Q 6 20 2 -0.6 Z", 0.3)
        x.path("M -6 6 Q -8.6 24 -7.6 42 M 0 3 Q 0.6 24 0 43 M 6 6 Q 8.6 24 7.6 42", None, stroke=OUT, width=0.3, alpha=0.5)
        x.poly([(0, 12), (3.4, 17), (0, 22.4), (-3.4, 17)], None, stroke="#C92A3A", width=0.5)
        x.ellipse(0, 17, 1.1, 1.1, "#C92A3A")
        x.path("M -8.6 0.6 Q 0 -1.4 8.6 0.6 L 8 2.8 Q 0 0.8 -8 2.8 Z", GOLD, stroke=OUT, width=0.3)
    else:
        x.path(shape, linear(0, 0, 0, 44, (0, "#B02A40"), (1, "#4A0E1E")), stroke=OUT, width=0.45)
        x.path("M -11 12 Q -12.6 28 -11.6 41 M 11 12 Q 12.6 28 11.6 41", None, stroke=OUT, width=0.3, alpha=0.5)
        x.shade("M 6.5 0.4 L 8.6 0.6 Q 13.8 20 13 42 L 8 43.6 Q 9.6 20 6.5 0.4 Z", 0.35)


@look("gideon", "torso")
def _gideon_torso(x: Recipe, back: bool) -> None:  # golden clasps and a sigil
    if back:
        return
    for sx in (-1, 1):
        x.ellipse(sx * 5.6, -14.6, 1.5, 1.5, GOLD, stroke=OUT, width=0.3)
        x.ellipse(sx * 5.6, -14.6, 0.55, 0.55, "#C92A3A")
    x.path("M -4.4 -14.2 Q 0 -11.4 4.4 -14.2", None, stroke=GOLD, width=0.6)
    x.poly([(0, -9.4), (1.9, -6.6), (0, -3.6), (-1.9, -6.6)], None, stroke="#C92A3A", width=0.45)
    x.ellipse(0, -6.6, 0.7, 0.7, "#C92A3A")


@look("gideon", "arm")
def _gideon_arm(x: Recipe, back: bool) -> None:  # golden bracers with spikes
    x.path("M -2.3 8.4 L 2.3 8.4 L 2 13.6 L -2 13.6 Z", linear(-2, 0, 2, 0, (0, "#FFE898"), (1, "#A8862A")), stroke=OUT, width=0.35)
    for sx in (-1.3, 0.3):
        x.poly([(sx, 8.4), (sx + 1, 8.4), (sx + 0.5, 6.6)], GOLD, stroke=OUT, width=0.25)
    x.path(HAND, "#2B1B30", stroke=OUT, width=0.35)


@look("gideon", "leg")
def _gideon_leg(x: Recipe, back: bool) -> None:  # tall boots with golden tips
    x.path("M -2.5 12.4 L 2.5 12.4 L 2.7 24.6 Q 3.1 27.4 0.7 27.4 L -1.9 27.4 Q -3.2 27.4 -2.8 24.6 Z", linear(0, 12, 0, 27, (0, "#3A2444"), (1, "#18101E")), stroke=OUT, width=0.45)
    x.path("M -2.5 12.4 L 2.5 12.4 L 2.55 13.8 L -2.55 13.8 Z", GOLD, stroke=OUT, width=0.25)
    x.poly([(-0.6, 13.8), (0.6, 13.8), (0, 15.8)], GOLD, stroke=OUT, width=0.2)
    x.path("M -2.6 25 Q -0.4 23.6 1.6 24.6 L 1.4 27.2 L -2 27.2 Z", GOLD, stroke=OUT, width=0.25)


# ------------------------------------------------------------------------------------------------ the people
@look("red", "head")
def _guard_head(x: Recipe, back: bool) -> None:  # a guard: a kettle helmet
    x.path(DOME, STEEL, stroke=OUT, width=0.45)
    x.path("M -8.2 -10 Q 0 -12.8 8.2 -10 L 8 -8.6 Q 0 -11.2 -8 -8.6 Z", STEEL, stroke=OUT, width=0.4)
    x.path("M 0 -17.4 L 0 -11.6", None, stroke="#4C505C", width=0.5)
    x.path("M -4.8 -14.6 Q -3 -16.6 -1 -16.9", None, stroke="#FFFFFF", width=0.6, alpha=0.6)


@look("red", "torso")
def _guard_torso(x: Recipe, back: bool) -> None:  # a breastplate over the tunic
    x.path("M -6 -15.4 L -2.4 -16.2 Q 0 -14.8 2.4 -16.2 L 6 -15.4 L 5.6 -4 Q 0 -1.4 -5.6 -4 Z", STEEL, stroke=OUT, width=0.45)
    x.path("M 0 -14.6 L 0 -2.6", None, stroke="#4C505C", width=0.4)
    x.path("M -4.6 -13.6 Q -3.6 -9 -4.4 -5", None, stroke="#FFFFFF", width=0.5, alpha=0.5)
    for sx in (-1, 1):
        x.path(f"M {sx * 8.4} -14.2 Q {sx * 8} -17.4 {sx * 4.6} -16.6 L {sx * 5.4} -13 Z", STEEL, stroke=OUT, width=0.4)


look("red", "arm")(plate("M -2.2 7.6 L 2.2 7.6 L 1.9 13.6 L -1.9 13.6 Z"))
look("red", "leg")(plate("M -2.5 11 L 2.5 11 L 2.4 18.4 L -2.4 18.4 Z"))


@look("green", "head", behind=True)
def _ranger_hood_back(x: Recipe, back: bool) -> None:
    x.path("M -7.4 -6 Q -8.6 -18.4 0 -18.6 Q 8.6 -18.4 7.4 -6 Q 6.6 -0.6 4.4 0.8 L -4.4 0.8 Q -6.6 -0.6 -7.4 -6 Z", "#2E5E3A", stroke=OUT, width=0.45)


@look("green", "head")
def _ranger_hood(x: Recipe, back: bool) -> None:  # a ranger: a green hood
    if back:
        x.path("M -7.4 -6 Q -8.6 -18.4 0 -18.6 Q 8.6 -18.4 7.4 -6 Q 6.6 0 0 1.6 Q -6.6 0 -7.4 -6 Z", linear(0, -18, 0, 2, (0, "#4E8A58"), (1, "#2A5234")), stroke=OUT, width=0.45)
        x.shade("M 1 -18.6 Q 8.6 -18.4 7.4 -6 Q 6.6 0 0.6 1.6 Q 4 -8 1 -18.6 Z", 0.3)
        x.path("M 0 -18.4 Q 0.6 -8 0 1.4", None, stroke=OUT, width=0.25, alpha=0.5)
        return
    x.path("M -7.4 -6 Q -8.6 -18.4 0 -18.6 Q 8.6 -18.4 7.4 -6 Q 6.4 -10.4 4.6 -11.6 Q 0 -13.6 -4.6 -11.6 Q -6.4 -10.4 -7.4 -6 Z",
           linear(0, -18, 0, -6, (0, "#5A9A64"), (1, "#356A42")), stroke=OUT, width=0.45)
    x.path("M -5.6 -14.4 Q -3 -17.4 0 -17.6", None, stroke="#FFFFFF", width=0.6, alpha=0.3)


@look("green", "torso")
def _ranger_torso(x: Recipe, back: bool) -> None:  # a short mantle and the strap of the quiver
    x.path("M -8.4 -14.4 Q -8.6 -16.4 -5 -16.6 L 5 -16.6 Q 8.6 -16.4 8.4 -14.4 L 7 -9.6 Q 0 -6.6 -7 -9.6 Z", linear(0, -16, 0, -8, (0, "#4E8A58"), (1, "#2A5234")), stroke=OUT, width=0.45)
    x.path("M 5 -8.6 L -5.6 0.8" if back else "M -5 -8.6 L 5.6 0.8", None, stroke="#5A3A1E", width=0.7)
    if back:
        x.path("M 2.4 -15.6 L 6.4 -17.6 L 8.4 -5.6 L 4.4 -4 Z", "#6A4426", stroke=OUT, width=0.4)  # the quiver
        for dx in (0, 1.1, 2.2):
            x.line(3.6 + dx, -16.6 - dx * 0.4, 3.2 + dx, -19.6 - dx * 0.4, "#E8E0C8", 0.35)


look("green", "arm")(lambda x, back: x.path("M -2 9.6 L 2 9.6 L 1.85 13.6 L -1.85 13.6 Z", "#6A4426", stroke=OUT, width=0.35))


@look("ochre", "head")
def _farmer_hat(x: Recipe, back: bool) -> None:  # a farmer: a straw hat
    x.ellipse(0, -11.4, 10.4, 2.6, linear(-10, 0, 10, 0, (0, "#F8E4A0"), (1, "#B8963E")), stroke=OUT, width=0.45)
    x.path("M -5.4 -11.6 Q -5.4 -18.4 0 -18.4 Q 5.4 -18.4 5.4 -11.6 Q 0 -10 -5.4 -11.6 Z", linear(-5, -18, 5, -11, (0, "#FFF0B8"), (1, "#C8A650")), stroke=OUT, width=0.45)
    x.path("M -5.4 -12.8 Q 0 -11.2 5.4 -12.8 L 5.4 -11.6 Q 0 -10 -5.4 -11.6 Z", "#A8503A", stroke=OUT, width=0.25)
    for k in range(5):
        x.line(-8 + k * 4, -11.6 + (k % 2) * 0.6, -6.4 + k * 4, -10.2 + (k % 2) * 0.4, "#A8862A", 0.25, alpha=0.7)


@look("ochre", "torso")
def _farmer_torso(x: Recipe, back: bool) -> None:  # suspenders
    for sx in (-1, 1):
        x.path(f"M {sx * 4.4} -16 L {sx * -1} -0.2" if back else f"M {sx * 4.4} -16 L {sx * 3.4} -0.2", None, stroke="#6A4426", width=1.0)
    if not back:
        for sx in (-1, 1):
            x.ellipse(sx * 3.5, -1, 0.45, 0.45, GOLD)


look("ochre", "arm")(bare_forearm())


@look("purple", "head")
def _mage_hat(x: Recipe, back: bool) -> None:  # a mage: a tall pointed hat
    x.path("M -5.6 -11.8 Q -3 -14 -1.4 -20 Q 0.6 -26.4 4.4 -27 Q 2.4 -20.4 5.6 -11.8 Q 0 -10.2 -5.6 -11.8 Z", linear(-5, -27, 5, -11, (0, "#8A6CD8"), (1, "#3E2E76")), stroke=OUT, width=0.45)
    x.ellipse(0, -11.4, 9.6, 2.3, linear(-9, 0, 9, 0, (0, "#7A5CC0"), (1, "#32245E")), stroke=OUT, width=0.45)
    x.path("M -5.4 -13 Q 0 -11.4 5.4 -13 L 5.6 -11.8 Q 0 -10.2 -5.6 -11.8 Z", GOLD, stroke=OUT, width=0.25)
    if not back:
        x.poly([(0, -14.6), (0.5, -13.5), (1.6, -13.4), (0.8, -12.6), (1, -11.5), (0, -12.1), (-1, -11.5), (-0.8, -12.6), (-1.6, -13.4), (-0.5, -13.5)], "#FFF3B0")
    x.path("M -2.4 -15 Q -0.8 -20 1.2 -23.6", None, stroke="#FFFFFF", width=0.5, alpha=0.3)


@look("purple", "torso")
def _mage_robe(x: Recipe, back: bool) -> None:  # a robe down to the ankles
    robe = "M -7.9 -14.6 Q -8.4 -15.6 -6 -16 L -2.4 -16.6 L 0 -14 L 2.4 -16.6 L 6 -16 Q 8.4 -15.6 7.9 -14.6 L 6.6 -6 L 8.6 24 Q 0 26.4 -8.6 24 L -6.6 -6 Z"
    x.path(robe, linear(0, -16, 0, 26, (0, "#6A4CB0"), (1, "#2E2060")), stroke=OUT, width=0.45)
    x.shade("M 2.4 -16.6 L 6 -16 Q 8.4 -15.6 7.9 -14.6 L 6.6 -6 L 8.6 24 L 3.4 25.6 Q 5 4 2.4 -16.6 Z", 0.3)
    x.path("M -6.3 -0.6 Q 0 0.8 6.3 -0.6 L 6.4 1 Q 0 2.4 -6.4 1 Z", GOLD, stroke=OUT, width=0.3)
    x.path("M -8.4 22 Q 0 24.4 8.4 22", None, stroke=GOLD, width=0.6)
    x.path("M -3 3 Q -4 14 -3.4 24 M 3 3 Q 4 14 3.4 24", None, stroke=OUT, width=0.25, alpha=0.45)
    if not back:
        x.ellipse(0, -9, 1.1, 1.1, "#FFF3B0", stroke=OUT, width=0.25)
        x.glow(0, -9, 3, "#FFE880", 0.4)


look("purple", "arm")(lambda x, back: x.path("M -2.3 -0.8 Q 0 -1.8 2.3 -0.8 L 3.4 13.4 Q 0 15 -3.4 13.4 Z", linear(0, -1, 0, 14, (0, "#6A4CB0"), (1, "#3E2E76")), stroke=OUT, width=0.45))


@look("teal", "head", behind=True)
def _traveler_bun(x: Recipe, back: bool) -> None:
    x.ellipse(0, -16.8, 3.2, 2.6, "$p.hair", stroke=OUT, width=0.45)


@look("teal", "head")
def _traveler_band(x: Recipe, back: bool) -> None:  # a traveler: a headband
    x.path("M -6.3 -12.4 Q 0 -14.4 6.3 -12.4 L 6.2 -10.6 Q 0 -12.6 -6.2 -10.6 Z", "#2E9AB8", stroke=OUT, width=0.35)
    x.path("M 6 -11.6 L 9.6 -9.6 L 7.4 -9 L 10 -5.6 L 6.2 -9.4 Z", "#2E9AB8", stroke=OUT, width=0.3)


@look("teal", "torso")
def _traveler_sash(x: Recipe, back: bool) -> None:  # a sash across the chest
    d = "M 7 -15.6 L 4.4 -16.2 L -6.2 -1.4 L -6.1 1 L -4 1.2 Z" if back else "M -7 -15.6 L -4.4 -16.2 L 6.2 -1.4 L 6.1 1 L 4 1.2 Z"
    x.path(d, linear(0, -16, 0, 1, (0, "#F0C860"), (1, "#B8862A")), stroke=OUT, width=0.4)


look("teal", "arm")(bare_forearm("#5A3A1E"))


@look("cream", "head")
def _baker_hat(x: Recipe, back: bool) -> None:  # a baker: a tall white hat
    for cx, cy, rx, ry in ((-3.6, -19.4, 3.6, 3.0), (3.6, -19.4, 3.6, 3.0), (0, -21.4, 4.2, 3.4)):
        x.ellipse(cx, cy, rx, ry, linear(cx - rx, cy - ry, cx + rx, cy + ry, (0, "#FFFFFF"), (1, "#C8CCE0")), stroke=OUT, width=0.4)
    x.path("M -5.6 -17.8 L 5.6 -17.8 L 5.9 -11.8 Q 0 -13.4 -5.9 -11.8 Z", linear(-6, 0, 6, 0, (0, "#FFFFFF"), (1, "#C8CCE0")), stroke=OUT, width=0.4)
    for k in (-3, 0, 3):
        x.line(k, -17, k * 1.05, -12.8, "#A8ACC4", 0.25)


look("cream", "torso")(apron("#FFFFFF", -9))
look("cream", "arm")(bare_forearm())


@look("brown", "head")
def _laborer_head(x: Recipe, back: bool) -> None:  # a laborer: a flat cap and a bushy beard
    x.path(DOME, linear(0, -17.4, 0, -10, (0, "#8A6444"), (1, "#4E3422")), stroke=OUT, width=0.45)
    x.path("M -2 -13.4 L 2 -16 M -5 -12 L -2 -15 M 2.6 -12.6 L 5 -14.4", None, stroke=OUT, width=0.2, alpha=0.4)
    if back:
        return
    x.path("M -6.4 -10.6 Q 0 -13.4 6.6 -11 Q 9.4 -10.4 9 -8.6 Q 2 -10.6 -6.2 -9.4 Z", "#4A3020", stroke=OUT, width=0.4)
    x.path("M -4.9 -4.4 Q -5.6 2 0 2.6 Q 5.6 2 4.9 -4.4 Q 3 -1.6 1 -1.9 Q 0 -1.1 -1 -1.9 Q -3 -1.6 -4.9 -4.4 Z", "$p.hair", stroke=OUT, width=0.4)
    x.path("M -2 0.4 L -1.6 1.8 M 0 0.8 L 0 2.2 M 2 0.4 L 1.6 1.8", None, stroke="#FFFFFF", width=0.2, alpha=0.3)


@look("brown", "torso")
def _laborer_torso(x: Recipe, back: bool) -> None:  # suspenders and a tool belt
    for sx in (-1, 1):
        x.path(f"M {sx * 4.6} -16 L {sx * 3.6} -0.2", None, stroke="#3E2A1A", width=1.1)
    if not back:
        x.rect(2.6, 1.2, 2.8, 3, "#6A4426", stroke=OUT, width=0.3)
        x.line(4, 0, 4, 1.4, "#8A929C", 0.6)


look("brown", "arm")(sleeve("$p.shirt", None, "#5A3E28"))
