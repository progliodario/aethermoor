"""The people of the game: the parts of the humanoid rig (data/base/art/characters/ren/), the rig and its clips.

    python tools/art_chars.py

A person is about 56 art units tall (1.75 tiles) with the proportions of a real body (five and a half heads: see PROPORTIONS) and
the face of a real face (almond eyes, a nose, lips).
The rig has a soft shadow, two legs, two arms, a torso, a head and a `cape` part behind the body (capes, long hair); the
torso, the head and the cape have a second recipe for the view from behind (`art_back`, spec 13). Every part is drawn
around its joint (the origin of its canvas) with its tones and a violet shade away from the light (top left); `textures()`
adds the strands of the hair and the weave of the cloth, and the finish of `artkit.finish` softens the shades, fades the
outlines and gives every part a volume (ADR 0015). The palette variants are the protagonists and the kinds of people; what each one wears is in `art_looks.py`
(`only` and `except` layers). The shading is multiplied or added, so it works with every palette.
"""
from __future__ import annotations

import json

from art_looks import LOOKS, PEOPLE, PROTAGONISTS
from art_looks_side import SIDE
from artkit import ART, ROOT, Recipe, linear, noise, radial, shape_box, transform_layers

OUT = "$p.outline"
CHAR = ART / "characters" / "ren"

BASE = {"skin": "#F4CFAE", "hair": "#2E2A3A", "eye": "#4A6FA8", "shirt": "#3F6FD1", "shirt_dark": "#2E54A5", "pants": "#4A4F62",
        "boots": "#3A2E2A", "outline": "#1E1B28"}
VARIANTS = {
    "red": {"shirt": "#D14B3F", "shirt_dark": "#A5362E", "eye": "#6A4A2A"},
    "green": {"shirt": "#4FA464", "shirt_dark": "#38804A", "hair": "#5A3A24", "eye": "#3E7A48", "pants": "#5A4A38"},
    "ochre": {"shirt": "#D4A040", "shirt_dark": "#A67C2A", "skin": "#D9A77A", "hair": "#1E1B28", "eye": "#5A3A1E", "pants": "#6B4A32"},
    "purple": {"shirt": "#8A5CC0", "shirt_dark": "#6B439A", "hair": "#C9C1B0", "eye": "#8A5CC0", "pants": "#3E2E76"},
    "teal": {"shirt": "#3FA8A8", "shirt_dark": "#2E8080", "skin": "#8D5A3C", "hair": "#1A1620", "eye": "#2E2018", "pants": "#245E70"},
    "cream": {"shirt": "#E8E4DC", "shirt_dark": "#BDB8AC", "pants": "#6B5A48", "hair": "#A0522D", "eye": "#6A8A3A"},
    "brown": {"shirt": "#8C6A48", "shirt_dark": "#6A4E32", "skin": "#C98E66", "hair": "#2A1E16", "eye": "#3A2A1A", "pants": "#4A3424"},
    "sakura": {"skin": "#F8D8C0", "hair": "#E07AB8", "eye": "#A050D0", "shirt": "#8A5FD0", "shirt_dark": "#6A45A8", "pants": "#3C3A5C", "boots": "#2A2230"},
    "daichi": {"skin": "#D9A878", "hair": "#1E1A18", "eye": "#5A3A1E", "shirt": "#D6532B", "shirt_dark": "#A33E1E", "pants": "#2E3238", "boots": "#1E1E1E"},
    "haruka": {"skin": "#F2CCAE", "hair": "#7A5232", "eye": "#3E9A5A", "shirt": "#4FA87A", "shirt_dark": "#3A8260", "pants": "#6A5A44", "boots": "#4A3A2A"},
    "marco": {"skin": "#E6BE9A", "hair": "#1E1814", "eye": "#4A3220", "shirt": "#ECECEC", "shirt_dark": "#BDBDC8", "pants": "#3A4A5A", "boots": "#2A2A30"},
    "yuki": {"skin": "#F4D8C2", "hair": "#DCDCF0", "eye": "#C03A50", "shirt": "#3A3A58", "shirt_dark": "#2A2A42", "pants": "#26263A", "boots": "#14141E"},
    "lena": {"skin": "#EFD4C4", "hair": "#3A2A2A", "eye": "#5A7A9A", "shirt": "#D8DCE6", "shirt_dark": "#AEB4C4", "pants": "#4A4F66", "boots": "#262630"},
    "gideon": {"skin": "#CFA58A", "hair": "#8A2A2A", "eye": "#E02838", "shirt": "#3A2E48", "shirt_dark": "#261E32", "pants": "#1E1A28", "boots": "#120E18"},
}

# canvas (w, h) and joint of every part: what is drawn below is in units around the joint
CANVAS = {"head": (44, 50, 22, 38), "torso": (40, 56, 20, 25), "arm": (14, 30, 7, 3), "leg": (14, 34, 7, 2), "cape": (48, 56, 24, 6)}


def part(name: str) -> Recipe:
    w, h, _, _ = CANVAS[name.replace("_back", "").replace("_side", "")]
    r = Recipe(f"base:art/char/ren/{name}", w, h, (0, 0), seed="v3")
    r.finish = {"outline": 0.45, "desat": 0.12, "form": 0.26, "grain": 0.07, "sky": 0.08}  # the realistic finish (artkit.finish)
    return r


# ------------------------------------------------------------------------------------------------ head
FACE = "M -5.4 -9 Q -5.6 -4.6 -3.7 -2.3 Q -1.7 -0.4 0 -0.3 Q 1.7 -0.4 3.7 -2.3 Q 5.6 -4.6 5.4 -9 Q 5.2 -13.7 0 -13.9 Q -5.2 -13.7 -5.4 -9 Z"
HAIR_BACK = "M -6.2 -7.4 Q -6.9 -15.8 0 -16 Q 6.9 -15.8 6.2 -7.4 Q 6.1 -5.4 5.4 -4.6 L 4.8 -7 L -4.8 -7 L -5.4 -4.6 Q -6.1 -5.4 -6.2 -7.4 Z"
FRINGE = ("M -6 -7.4 Q -6.8 -15.5 0 -15.7 Q 6.8 -15.5 6 -7.4 Q 5.5 -9.6 4.6 -10.3 L 4 -7.9 Q 3.2 -10.1 2.1 -10.7 L 1.5 -8.3 "
          "Q 0.5 -10.5 -0.8 -10.9 L -1.2 -8.5 Q -2.2 -10.3 -3.3 -10.5 L -3.9 -8.1 Q -4.7 -9.9 -5.3 -10 Z")
SKULL_BACK = "M -6.3 -7 Q -7 -15.8 0 -16 Q 7 -15.8 6.3 -7 Q 6.2 -2.2 3.4 -1.2 Q 0 -0.4 -3.4 -1.2 Q -6.2 -2.2 -6.3 -7 Z"


def eye(r: Recipe, x: float, only=None, skip=None) -> None:
    """An eye in the proportions of a real face: an almond white, a round iris half under the upper lid, a pupil, one
    catchlight, the shade of the lid, a fine line of lashes and the crease above."""
    kw = {"only": only, "skip": skip}
    s = -1 if x < 0 else 1  # the outer corner is a little higher
    almond = (f"M {x - 1.3 * s:.2f} -5.85 Q {x - 0.45 * s:.2f} -7.0 {x + 0.35 * s:.2f} -6.9 Q {x + 1.05 * s:.2f} -6.75 {x + 1.35 * s:.2f} -6.05 "
              f"Q {x + 0.55 * s:.2f} -5.25 {x - 0.2 * s:.2f} -5.3 Q {x - 0.95 * s:.2f} -5.35 {x - 1.3 * s:.2f} -5.85 Z")
    r.path(almond, linear(x, -6.9, x, -5.3, (0, "#C8BCC0"), (0.45, "#F0EAE6"), (1, "#E4DCDA")), **kw)
    r.ellipse(x + 0.05, -6.08, 0.64, 0.66, radial(x - 0.05, -6.25, 0.7, (0, "$p.eye"), (0.7, "$p.eye"), (1, "#1E1626")), **kw)
    r.ellipse(x + 0.05, -6.08, 0.64, 0.66, linear(x, -6.8, x, -5.5, (0, "#1E1626"), (0.5, "#1E162600")), alpha=0.7, **kw)  # the lid's shade on it
    r.ellipse(x + 0.05, -6.08, 0.27, 0.28, "#0E0A12", **kw)
    r.ellipse(x - 0.2, -6.3, 0.15, 0.15, "#FFFFFF", alpha=0.9, **kw)
    r.path(f"M {x - 1.4 * s:.2f} -5.8 Q {x - 0.45 * s:.2f} -7.1 {x + 0.35 * s:.2f} -7.0 Q {x + 1.1 * s:.2f} -6.85 {x + 1.45 * s:.2f} -6.05",
           None, stroke=OUT, width=0.34, **kw)  # the upper lid and its lashes
    r.path(f"M {x - 1.1 * s:.2f} -5.5 Q {x - 0.1 * s:.2f} -5.15 {x + 1.1 * s:.2f} -5.75", None, stroke="#6A4A50", width=0.16, alpha=0.5, **kw)
    r.path(f"M {x - 1.1 * s:.2f} -7.2 Q {x:.2f} -7.75 {x + 1.2 * s:.2f} -7.15", None, stroke="#8A5A5A", width=0.16, alpha=0.35, **kw)  # the crease


def head() -> Recipe:
    r = part("head")
    r.path(HAIR_BACK, "$p.hair", stroke=OUT, width=0.45)
    for sx in (-1, 1):  # ears
        r.ellipse(sx * 5.5, -6.2, 0.95, 1.5, "$p.skin", stroke=OUT, width=0.35)
        r.ellipse(sx * 5.5, -6.1, 0.45, 0.8, "#C8607A", alpha=0.3)
    r.path(FACE, "$p.skin", stroke=OUT, width=0.45)
    r.shade("M -5.6 -11 L 5.6 -11 L 5.5 -8.3 Q 0 -9.6 -5.5 -8.3 Z", 0.3, "#B06A80")  # the shade of the fringe
    r.shade("M 2.6 -11 Q 6.4 -6 3.7 -2.3 Q 1.7 -0.4 0 -0.3 Q 2.8 -2 3.4 -5 Q 3.6 -8 2.6 -11 Z", 0.22, "#B06A80")
    for sx in (-1, 1):  # the warmth of the cheeks
        r.ellipse(sx * 3.4, -4.0, 1.6, 0.9, "#D8706A", alpha=0.12, blur=0.8)
    r.ellipse(-1.5, -9.6, 2.6, 1.2, "#FFF4E8", alpha=0.16, blend="add", clip=True, blur=0.8)  # the light on the forehead
    r.path("M 0.35 -6.4 Q 0.9 -4.6 0.95 -3.6 L 0.2 -3.3 Q 0.5 -4.8 0.35 -6.4 Z", "#9A5A60", alpha=0.3, blend="multiply", blur=0.25)  # the side of the nose
    r.ellipse(-0.15, -3.75, 0.35, 0.22, "#FFF4E8", alpha=0.3, blend="add", clip=True, blur=0.15)  # the tip of the nose
    for sx in (-1, 1):
        r.ellipse(sx * 0.42, -3.35, 0.2, 0.12, "#5A3038", alpha=0.6)  # the nostrils
    eye(r, -2.55)
    eye(r, 2.55)
    for sx in (-1, 1):
        r.path(f"M {sx * 1.0} -8.35 Q {sx * 2.3} -8.95 {sx * 3.9} -8.2", None, stroke=OUT, width=0.36, alpha=0.75)  # eyebrows
        r.path(f"M {sx * 1.3} -8.45 Q {sx * 2.3} -8.85 {sx * 3.4} -8.4", None, stroke="$p.hair", width=0.22, alpha=0.6)
    r.path("M -1.0 -2.2 Q -0.4 -2.45 0 -2.3 Q 0.4 -2.45 1.0 -2.2 Q 0.5 -2.0 0 -2.05 Q -0.5 -2.0 -1.0 -2.2 Z", "#A8606A", alpha=0.75)  # the upper lip
    r.path("M -0.8 -2.1 Q 0 -1.45 0.8 -2.1 Q 0 -1.8 -0.8 -2.1 Z", "#C07878", alpha=0.6)  # the lower lip
    r.path("M -1.0 -2.15 Q 0 -1.95 1.0 -2.15", None, stroke="#6A3A40", width=0.16, alpha=0.8)
    r.ellipse(0, -1.25, 0.6, 0.2, "#9A5A60", alpha=0.25, blend="multiply", blur=0.2)  # the shade under the lip
    r.path(FRINGE, "$p.hair", stroke=OUT, width=0.45)
    r.shade("M 0.5 -15.7 Q 6.8 -15.5 6 -7.4 Q 5.5 -9.6 4.6 -10.3 L 4 -7.9 Q 3.2 -10.1 2.1 -10.7 Q 3.6 -13 0.5 -15.7 Z", 0.4)
    r.path("M -4.6 -12.2 Q -1 -14.2 3.2 -13", None, stroke="#FFFFFF", width=0.9, alpha=0.3, blend="add", clip=True)  # the ring of light
    r.path("M -2 -11 L -1.6 -12.8 M 1 -11.2 L 1.6 -13 M -4.2 -10.6 L -4.4 -12.6", None, stroke=OUT, width=0.2, alpha=0.5)
    return r


def head_back() -> Recipe:
    r = part("head_back")
    for sx in (-1, 1):
        r.ellipse(sx * 5.6, -6.2, 0.9, 1.4, "$p.skin", stroke=OUT, width=0.35)
    r.rect(-1.6, -2.2, 3.2, 3, "$p.skin")
    r.path(SKULL_BACK, "$p.hair", stroke=OUT, width=0.45)
    r.shade("M 1 -16 Q 7 -15.8 6.3 -7 Q 6.2 -2.2 3.4 -1.2 Q 0 -0.4 -3.4 -1.2 Q 3 -3 3.2 -8 Q 3.4 -12 1 -16 Z", 0.4)
    r.path("M -4.8 -12 Q -1.5 -14.4 2.6 -13.2", None, stroke="#FFFFFF", width=0.9, alpha=0.3, blend="add", clip=True)
    r.path("M -3 -3 Q -3.6 -8 -2.6 -13 M 0 -1.6 Q -0.4 -8 0.2 -14.6 M 3 -2.6 Q 3.8 -8 2.8 -13", None, stroke=OUT, width=0.22, alpha=0.5)
    return r


# ------------------------------------------------------------------------------------------------ the side view
# the figure looks to the right; the clients mirror it to look left (spec 13)
PROFILE = ("M 0 -13.7 Q 4.6 -13.7 5.3 -9.6 L 5.5 -7.2 L 6.7 -5.2 L 5.6 -4.6 L 5.7 -3.3 L 5.1 -2.7 Q 5.3 -1 3.7 -0.5 L 0.8 -0.9 "
           "Q -1.6 -1.6 -2.2 -4 L -2.6 -9 Q -2.2 -13.7 0 -13.7 Z")
HAIR_SIDE = ("M -6.4 -7 Q -7.1 -16 0.4 -16 Q 5.9 -15.8 6.2 -10.8 Q 5 -11.8 3.9 -11.6 L 3.5 -8.6 Q 2.6 -10.6 1.6 -10.8 L 1.6 -7.4 "
             "Q 0.6 -8.8 -0.6 -8.4 L -1 -3.4 Q -3.2 -2.2 -5.6 -3 Q -6.4 -4.6 -6.4 -7 Z")
BODY_SIDE = "M -3.6 -16.2 Q 0 -17 3 -16 Q 4.9 -12 4.4 -7 Q 3.8 -3 4.2 0 L 4.6 4.2 Q 0 5.4 -4.4 4.2 L -4 0 Q -3.6 -3 -4.2 -7 Q -4.9 -12 -3.6 -16.2 Z"


def head_side() -> Recipe:
    r = part("head_side")
    r.rect(-1.6, -2.4, 3.2, 3.2, "$p.skin")  # the neck under the jaw
    r.path(PROFILE, "$p.skin", stroke=OUT, width=0.45)
    r.shade("M 0 -13.7 Q -2.2 -13.7 -2.6 -9 L -2.2 -4 Q -1.6 -1.6 0.8 -0.9 L 3.7 -0.5 Q 1 -2 0.4 -5 Q 0 -9 0 -13.7 Z", 0.2, "#B06A80")
    r.ellipse(-0.6, -6.1, 1.1, 1.6, "$p.skin", stroke=OUT, width=0.35)  # the ear
    r.ellipse(-0.5, -6.0, 0.5, 0.8, "#C8607A", alpha=0.3)
    r.ellipse(2.4, -4.0, 1.2, 0.6, "#F06A7A", alpha=0.3, blur=0.35)
    # the eye, narrower from the side
    r.path("M 2.9 -6.1 Q 3.6 -6.95 4.6 -6.6 Q 4.5 -5.6 4.2 -5.4 Q 3.4 -5.4 2.9 -6.1 Z", "#ECE4E2")
    r.ellipse(4.05, -6.1, 0.42, 0.62, radial(4.0, -6.25, 0.6, (0, "$p.eye"), (0.7, "$p.eye"), (1, "#1E1626")))
    r.ellipse(4.15, -6.1, 0.18, 0.28, "#0E0A12")
    r.ellipse(3.92, -6.32, 0.12, 0.12, "#FFFFFF", alpha=0.9)
    r.path("M 2.8 -6.05 Q 3.6 -7.05 4.7 -6.65", None, stroke=OUT, width=0.32)
    r.path("M 2.2 -8.4 Q 3.5 -9.0 4.9 -8.5", None, stroke=OUT, width=0.34, alpha=0.75)
    r.path("M 4.5 -2.5 Q 5 -2.3 5.4 -2.6", None, stroke="#A84A5A", width=0.35)
    r.path(HAIR_SIDE, "$p.hair", stroke=OUT, width=0.45)
    r.shade("M -6.4 -7 Q -7.1 -16 -1 -16 Q -4.4 -12 -3.6 -7 Q -3.2 -3.6 -5.6 -3 Q -6.4 -4.6 -6.4 -7 Z", 0.4)
    r.path("M -3.4 -12.6 Q 0.4 -14.6 4.2 -13.2", None, stroke="#FFFFFF", width=0.9, alpha=0.3, blend="add", clip=True)
    r.path("M -2 -9 L -1.6 -12 M 0.6 -9.4 L 1 -12.6 M -4.4 -5 L -4.6 -9", None, stroke=OUT, width=0.2, alpha=0.5)
    return r


def torso_side() -> Recipe:
    r = part("torso_side")
    r.rect(-1.3, -19.4, 3.0, 4, "$p.skin", stroke=OUT, width=0.35)  # the neck
    r.path(BODY_SIDE, linear(0, -16, 0, 5, (0, "$p.shirt"), (1, "$p.shirt_dark")), stroke=OUT, width=0.45)
    r.shade("M -3.6 -16.2 Q -4.9 -12 -4.2 -7 Q -3.6 -3 -4 0 L -4.4 4.2 L -1.6 5 Q -0.6 -6 -1.4 -16.8 Z", 0.32)
    r.path("M 1 -16.6 L 3.4 -13.4 L 3.2 -16 Z", "$p.shirt", stroke=OUT, width=0.3)  # the collar
    r.path("M 3.6 -12.6 Q 4.2 -6 4 -0.2", None, stroke=OUT, width=0.25, alpha=0.5)
    r.path("M -2.6 -9 Q -1.8 -6 -2.6 -2.6", None, stroke=OUT, width=0.22, alpha=0.4)
    r.path("M -4.1 -0.3 Q 0 0.7 4.3 -0.3 L 4.4 1.6 Q 0 2.6 -4.3 1.6 Z", "#4A3426", stroke=OUT, width=0.35)  # the belt
    r.rect(2.6, 0.1, 1.6, 1.9, "#E0BE60", stroke=OUT, width=0.3)
    r.path("M -4.4 2 Q 0 3 4.5 2 L 4.6 4.2 Q 0 5.4 -4.4 4.2 Z", "$p.pants", stroke=OUT, width=0.4)
    return r


# ------------------------------------------------------------------------------------------------ torso
BODY = ("M -7.7 -14.5 Q -8.3 -15.4 -6 -15.9 L -2.2 -16.6 L 2.2 -16.6 L 6 -15.9 Q 8.3 -15.4 7.7 -14.5 L 6.3 -7 Q 5.7 -3 6.1 0 "
        "L 6.6 4.2 Q 0 5.6 -6.6 4.2 L -6.1 0 Q -5.7 -3 -6.3 -7 Z")


def torso(back: bool = False) -> Recipe:
    r = part("torso_back" if back else "torso")
    r.rect(-1.7, -19.4, 3.4, 4, "$p.skin", stroke=OUT, width=0.35)  # the neck
    r.shade("M -1.7 -19.4 L 1.7 -19.4 L 1.7 -16.6 Q 0 -17.6 -1.7 -16.6 Z", 0.4, "#B06A80")
    r.path(BODY, linear(0, -16, 0, 5, (0, "$p.shirt"), (1, "$p.shirt_dark")), stroke=OUT, width=0.45)
    r.shade("M 2.4 -16.6 L 6 -15.9 Q 8.3 -15.4 7.7 -14.5 L 6.3 -7 Q 5.7 -3 6.1 0 L 6.6 4.2 L 2.6 5.2 Q 4.4 -4 2.4 -16.6 Z", 0.35)
    r.lit("M -7.7 -14.5 Q -8.3 -15.4 -6 -15.9 L -3 -16.4 L -5.6 -14.6 L -6.6 -8 Z", 0.14, blur=0.4)
    if back:
        r.path("M 0 -15.6 Q 0.3 -6 0 4", None, stroke=OUT, width=0.25, alpha=0.4)  # the seam of the back
        r.path("M -2.2 -16.6 Q 0 -15.2 2.2 -16.6", None, stroke=OUT, width=0.35)
    else:
        r.path("M -2.2 -16.6 L 0 -13.4 L 2.2 -16.6 Q 0 -15.4 -2.2 -16.6 Z", "$p.skin", stroke=OUT, width=0.3)  # the open collar
        r.path("M -2.6 -16.7 L -0.3 -12.6 L -3.4 -14.4 Z", "$p.shirt", stroke=OUT, width=0.3)
        r.path("M 2.6 -16.7 L 0.3 -12.6 L 3.4 -14.4 Z", "$p.shirt", stroke=OUT, width=0.3)
        r.path("M 0 -12.6 L 0 -0.2", None, stroke=OUT, width=0.25, alpha=0.5)  # the row of buttons
        for y in (-10.4, -7.6, -4.8, -2):
            r.ellipse(0, y, 0.3, 0.3, "#FFFFFF", alpha=0.8)
    r.path("M -5.2 -9 Q -4.2 -6 -5 -2.6 M 5.2 -9 Q 4.4 -6 5.2 -3", None, stroke=OUT, width=0.22, alpha=0.4)  # folds
    r.path("M -6.2 -0.3 Q 0 0.9 6.2 -0.3 L 6.4 1.6 Q 0 2.8 -6.4 1.6 Z", "#4A3426", stroke=OUT, width=0.35)  # the belt
    r.path("M -6.2 -0.3 Q 0 0.9 6.2 -0.3", None, stroke="#FFFFFF", width=0.25, alpha=0.3)
    if not back:
        r.rect(-1.1, 0.1, 2.2, 2.1, "#E0BE60", stroke=OUT, width=0.3)
        r.rect(-0.45, 0.7, 0.9, 0.9, "#7A5A1E")
    r.path("M -6.5 2 Q 0 3.2 6.5 2 L 6.6 4.2 Q 0 5.6 -6.6 4.2 Z", "$p.pants")  # the hips, in the color of the legs
    r.path("M -6.5 2 Q 0 3.2 6.5 2 L 6.6 4.2 Q 0 5.6 -6.6 4.2 Z", None, stroke=OUT, width=0.4)
    return r


# ------------------------------------------------------------------------------------------------ limbs
SLEEVE = "M -2.1 -0.8 Q 0 -1.8 2.1 -0.8 Q 2.4 6 1.8 13.6 L -1.8 13.6 Q -2.4 6 -2.1 -0.8 Z"
HAND = "M -1.5 13.4 L 1.5 13.4 Q 2 15.4 1.6 17.2 Q 1 18.8 0 18.8 Q -1 18.8 -1.6 17.2 Q -2 15.4 -1.5 13.4 Z"


def arm() -> Recipe:
    r = part("arm")
    r.path(HAND, "$p.skin", stroke=OUT, width=0.35)
    r.path("M 0.2 16.4 L 0.2 18.2 M -0.7 16.6 L -0.7 18", None, stroke=OUT, width=0.2, alpha=0.5)
    r.shade("M 0.4 13.4 L 1.5 13.4 Q 2 15.4 1.6 17.2 Q 1 18.8 0.2 18.8 Z", 0.3, "#B06A80")
    r.path(SLEEVE, linear(0, -1, 0, 14, (0, "$p.shirt"), (1, "$p.shirt_dark")), stroke=OUT, width=0.45)
    r.shade("M 0.5 -1.6 Q 2.1 -1.2 2.1 -0.8 Q 2.4 6 1.8 13.6 L 0.3 13.6 Q 1 6 0.5 -1.6 Z", 0.38)
    r.lit("M -2.1 -0.8 Q -1.2 -1.5 -0.4 -1.6 Q -1.3 3 -1.6 8 Q -2.3 4 -2.1 -0.8 Z", 0.14, blur=0.3)
    r.path("M -1.6 6.6 Q 0 7.4 1.7 6.4", None, stroke=OUT, width=0.22, alpha=0.4)  # the elbow
    r.path("M -1.9 11.8 L 1.9 11.8 L 1.8 13.6 L -1.8 13.6 Z", "$p.shirt_dark", stroke=OUT, width=0.35)  # the cuff
    return r


LEG = "M -2.7 -0.5 L 2.7 -0.5 Q 2.6 7 2.2 12.5 L 2 19.5 L -2 19.5 L -2.2 12.5 Q -2.6 7 -2.7 -0.5 Z"
BOOT = "M -2.3 17.2 L 2.3 17.2 L 2.5 24.6 Q 2.9 27.2 0.7 27.2 L -1.7 27.2 Q -3 27.2 -2.6 24.6 Z"


def leg() -> Recipe:
    r = part("leg")
    r.path(LEG, "$p.pants", stroke=OUT, width=0.45)
    r.shade("M 0.6 -0.5 L 2.7 -0.5 Q 2.6 7 2.2 12.5 L 2 19.5 L 0.4 19.5 Q 1.2 9 0.6 -0.5 Z", 0.38)
    r.lit("M -2.7 -0.5 L -1.6 -0.5 Q -1.6 7 -1.4 13 L -2.2 12.5 Q -2.6 7 -2.7 -0.5 Z", 0.1, blur=0.3)
    r.path("M -2 11.6 Q 0 12.6 2.1 11.4", None, stroke=OUT, width=0.22, alpha=0.4)  # the knee
    r.path(BOOT, "$p.boots", stroke=OUT, width=0.45)
    r.shade("M 0.6 17.2 L 2.3 17.2 L 2.5 24.6 Q 2.9 27.2 0.7 27.2 Z", 0.4)
    r.path("M -2.3 17.2 L 2.3 17.2 L 2.35 18.8 L -2.35 18.8 Z", "#FFFFFF", alpha=0.18)  # the top of the boot
    r.path("M -2.2 24.8 Q -0.6 23.4 1.2 24.2", None, stroke="#FFFFFF", width=0.4, alpha=0.3)  # the toe
    r.path("M -2.7 26.2 Q 0 27.6 2.7 26.2", None, stroke=OUT, width=0.5, alpha=0.7)  # the sole
    return r


def shadow() -> Recipe:
    r = Recipe("base:art/char/ren/shadow", 28, 12, (14, 6), seed="v3")
    r.ellipse(14, 6, 10, 3.2, "#141030", alpha=0.34, blur=1.2)
    r.ellipse(14, 6, 6, 1.8, "#141030", alpha=0.3, blur=0.8)
    return r


# ------------------------------------------------------------------------------------------------ rig and clips
RIG = [  # the joints of a body of real proportions (see PROPORTIONS)
    ("shadow", None, (0, 0), 0, None, "shadow", None),
    ("cape", "torso", (0, -15.2), 1, 6, "cape", "cape_back"),
    ("leg_l", "shadow", (-2.8, -29), 2, None, "leg", None),
    ("leg_r", "shadow", (2.8, -29), 2, None, "leg", None),
    ("arm_l", "torso", (-6.8, -12.55), 3, None, "arm", None),
    ("torso", "shadow", (0, -29), 4, None, "torso", "torso_back"),
    ("arm_r", "torso", (6.8, -12.55), 5, None, "arm", None),
    ("head", "torso", (0, -16.3), 7, None, "head", "head_back"),
]
# seen from the side (spec 13): the parts that have a picture of their own, and where the limbs hang (the far arm and leg
# are a little behind the near ones)
SIDE_ART = {"head": "head_side", "torso": "torso_side", "cape": "cape_side"}
SIDE_OFFSET = {"leg_l": (-0.8, -29), "leg_r": (0.65, -29), "arm_l": (-0.8, -13.75), "arm_r": (0.55, -13.75), "head": (0.35, -16.3)}


def write_rig() -> None:
    order = ["shadow", "torso", "cape", "leg_l", "leg_r", "arm_l", "arm_r", "head"]  # parents first
    by_id = {p[0]: p for p in RIG}
    parts = []
    for pid in order:
        _, parent, offset, z, z_back, art, art_back = by_id[pid]
        item = {"id": pid, "parent": parent, "offset": list(offset), "z": z, "art": f"base:art/char/ren/{art}"}
        if art_back:
            item["art_back"] = f"base:art/char/ren/{art_back}"
        if z_back is not None:
            item["z_back"] = z_back
        if pid in SIDE_ART:
            item["art_side"] = f"base:art/char/ren/{SIDE_ART[pid]}"
        if pid in SIDE_OFFSET:
            item["offset_side"] = list(SIDE_OFFSET[pid])
        parts.append(item)
    rig = {"$schema": "../../../../schemas/rig.schema.json", "id": "base:art/rig/humanoid", "parts": parts}
    (ART / "rigs" / "humanoid.json").write_text(json.dumps(rig, indent=2) + "\n", encoding="utf-8", newline="\n")
    idle = {
        "$schema": "../../../../schemas/clip.schema.json", "id": "base:art/clip/humanoid_idle", "rig": "base:art/rig/humanoid", "loop": True, "length_ticks": 90,
        "tracks": {
            "torso": {"pos": [[0, 0, 0], [45, 0, -0.5], [90, 0, 0]]},
            "head": {"rot": [[0, 0], [45, 1.2], [90, 0]], "pos": [[0, 0, 0], [45, 0, -0.2], [90, 0, 0]]},
            "arm_l": {"rot": [[0, 3], [45, 5], [90, 3]]},
            "arm_r": {"rot": [[0, -3], [45, -5], [90, -3]]},
            "cape": {"rot": [[0, 0], [45, 1.5], [90, 0]]},
        },
    }
    walk = {
        "$schema": "../../../../schemas/clip.schema.json", "id": "base:art/clip/humanoid_walk", "rig": "base:art/rig/humanoid", "loop": True, "length_ticks": 28,
        "tracks": {
            "torso": {"pos": [[0, 0, 0], [7, 0, -1.0], [14, 0, 0], [21, 0, -1.0], [28, 0, 0]], "rot": [[0, 2], [14, -2], [28, 2]]},
            "head": {"rot": [[0, -1.5], [14, 1.5], [28, -1.5]]},
            "leg_l": {"rot": [[0, 20], [14, -20], [28, 20]], "pos": [[0, 0, 0], [7, 0, -1.2], [14, 0, 0], [28, 0, 0]]},
            "leg_r": {"rot": [[0, -20], [14, 20], [28, -20]], "pos": [[0, 0, 0], [14, 0, 0], [21, 0, -1.2], [28, 0, 0]]},
            "arm_l": {"rot": [[0, -22], [14, 22], [28, -22]]},
            "arm_r": {"rot": [[0, 22], [14, -22], [28, 22]]},
            "cape": {"rot": [[0, 4], [14, -4], [28, 4]]},
        },
        "events": [{"tick": 7, "event": "footstep"}, {"tick": 21, "event": "footstep"}],
    }
    # a blow (spec 13, "The blow"): the arm goes back in the first 5 ticks, comes down in the next 4, then returns
    attack = {
        "$schema": "../../../../schemas/clip.schema.json", "id": "base:art/clip/humanoid_attack", "rig": "base:art/rig/humanoid", "loop": False, "length_ticks": 30,
        "tracks": {
            "torso": {"rot": [[0, 0], [5, -6], [9, 8], [16, 3], [30, 0]], "pos": [[0, 0, 0], [5, -0.6, 0], [9, 1.2, 0.4], [30, 0, 0]]},
            "head": {"rot": [[0, 0], [5, -3], [9, 4], [30, 0]]},
            "arm_r": {"rot": [[0, -4], [5, -150], [9, 42], [15, 26], [30, -4]]},
            "arm_l": {"rot": [[0, 4], [5, 14], [9, -22], [30, 4]]},
            "leg_l": {"rot": [[0, 0], [9, 8], [30, 0]]},
            "leg_r": {"rot": [[0, 0], [9, -10], [30, 0]]},
            "cape": {"rot": [[0, 0], [9, -8], [30, 0]]},
        },
    }
    for name, clip in (("humanoid_idle", idle), ("humanoid_walk", walk), ("humanoid_attack", attack)):
        (ART / "clips" / f"{name}.json").write_text(json.dumps(clip, indent=2) + "\n", encoding="utf-8", newline="\n")


# ------------------------------------------------------------------------------------------------ the proportions of a real body
# Every part (and every look of it) is drawn in the units of its joint, then **warped** to the proportions of a real body, a little
# short, with a generous head and a short neck so that people stay pleasant to look at: five and a half heads, 56 units from the
# soles to the crown. The head is made smaller (0.66) while what hangs below the chin (long hair)
# keeps more of its length and width; a short neck shows between the chin and the shoulders; the torso is a little narrower; the arms
# reach the middle of the thigh (the sleeve grows, the hand less); the waist narrows; the legs are half of the height. The joints
# of the rig follow (RIG, SIDE_OFFSET). Landmarks from the soles (y up is negative): crown -56, chin -45.5, shoulders -44.2, elbow
# and belt -34 to -32, crotch -27, fingertips -21.6, knee -16.
def _piecewise(knots: list[tuple[float, float]]):
    """A piecewise linear map through the knots (sorted by their first value), straight on beyond the ends."""
    def f(v: float) -> float:
        for (a0, b0), (a1, b1) in zip(knots, knots[1:]):
            if v <= a1 or (a1, b1) == knots[-1]:
                return b0 + (v - a0) * (b1 - b0) / (a1 - a0)
        return v
    return f


def _shoulder_drop(x: float, y: float) -> float:
    """Shoulders slope down from the neck, as on a real body: the top of the torso sinks towards its sides."""
    across = min(max((abs(x) - 2.0) / 5.0, 0.0), 1.0)
    along = min(max((-10.0 - y) / 5.0, 0.0), 1.0)
    return 1.3 * across * along


def _head_point(x: float, y: float) -> tuple[float, float]:
    kx = 0.66 if y <= -1 else (0.82 if y >= 4 else 0.66 + (y + 1) / 5 * 0.16)  # hair below the jaw keeps more of its width
    return x * kx, y * 0.66 if y <= 0 else y * 0.9


_TORSO_Y = _piecewise([(-30.0, -27.8), (-19.4, -17.2), (-16.6, -15.2), (0.0, -3.0), (4.2, 2.0), (40.0, 41.4)])
_TORSO_X = _piecewise([(-30.0, 0.92), (-16.6, 0.92), (-12.0, 0.9), (-5.0, 0.8), (0.0, 0.84), (4.2, 0.9), (40.0, 0.9)])  # a waist
_ARM_Y = _piecewise([(-5.0, -5.0), (0.0, 0.0), (13.6, 15.2), (18.8, 20.2), (30.0, 31.0)])
_LEG_Y = _piecewise([(-5.0, -5.0), (-0.5, -0.5), (17.2, 19.0), (27.2, 29.0), (40.0, 41.8)])
PROPORTIONS = {
    "head": _head_point,
    "torso": lambda x, y: (x * _TORSO_X(y), _TORSO_Y(y) + _shoulder_drop(x, y)),
    "arm": lambda x, y: (x * 0.85, _ARM_Y(y)),
    "leg": lambda x, y: (x * 0.9, _LEG_Y(y)),
    "cape": lambda x, y: (x * 0.92, y * 0.97),
}


def _scales(pt, x: float, y: float) -> tuple[float, float]:
    e = 0.05
    sx = (pt(x + e, y)[0] - pt(x - e, y)[0]) / (2 * e)
    sy = (pt(x, y + e)[1] - pt(x, y - e)[1]) / (2 * e)
    return sx, sy


def _r(v: float) -> float:
    v = round(v, 2)
    return int(v) if v == int(v) else v


def _warp_path(d: str, pt) -> str:
    out: list[str] = []
    cmd = ""
    nums: list[float] = []
    last = [0.0, 0.0]

    def flush() -> None:
        if cmd in ("H", "V"):
            for v in nums:
                if cmd == "H":
                    last[0] = v
                else:
                    last[1] = v
                nx, ny = pt(last[0], last[1])
                out.append(f"{_r(nx)} {_r(ny)}")
        else:
            for i in range(0, len(nums) - 1, 2):
                last[0], last[1] = nums[i], nums[i + 1]
                nx, ny = pt(last[0], last[1])
                out.append(f"{_r(nx)} {_r(ny)}")
        nums.clear()

    for tok in d.replace(",", " ").split():
        if tok.isalpha():
            flush()
            cmd = tok
            out.append("L" if tok in ("H", "V") else tok)  # a warped horizontal or vertical line may slant
        else:
            nums.append(float(tok))
    flush()
    return " ".join(out)


def warp(layers: list[dict], pt) -> list[dict]:
    """The layers with every point moved by pt(x, y); radii, widths and blurs follow the local scale."""
    out = []
    for layer in layers:
        new = dict(layer)
        shape = layer["shape"]
        box = shape_box(shape) or (0, 0, 0, 0)
        sx, sy = _scales(pt, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
        mean = (sx + sy) / 2
        if "rect" in shape:  # a warped rect may lean: it becomes its four corners
            x, y, w, h = shape["rect"]
            new["shape"] = {"polygon": [[_r(a) for a in pt(px, py)] for px, py in ((x, y), (x + w, y), (x + w, y + h), (x, y + h))]}
        elif "ellipse" in shape:
            cx, cy, rx, ry = shape["ellipse"]
            nx, ny = pt(cx, cy)
            ex, ey = _scales(pt, cx, cy)
            new["shape"] = {"ellipse": [_r(nx), _r(ny), _r(rx * ex), _r(ry * ey)]}
        elif "polygon" in shape:
            new["shape"] = {"polygon": [[_r(a) for a in pt(x, y)] for x, y in shape["polygon"]]}
        else:
            new["shape"] = {"path": _warp_path(shape["path"], pt)}
        fill = layer.get("fill")
        if fill and "linear" in fill:
            g = dict(fill["linear"])
            (g["x0"], g["y0"]), (g["x1"], g["y1"]) = [tuple(_r(a) for a in pt(g["x0"], g["y0"])), tuple(_r(a) for a in pt(g["x1"], g["y1"]))]
            new["fill"] = {"linear": g}
        elif fill and "radial" in fill:
            g = dict(fill["radial"])
            g["cx"], g["cy"] = (_r(a) for a in pt(g["cx"], g["cy"]))
            g["r"] = _r(g["r"] * mean)
            new["fill"] = {"radial": g}
        if "stroke" in layer:
            new["stroke"] = dict(layer["stroke"], width=_r(max(0.12, layer["stroke"]["width"] * mean)))
        if layer.get("blur"):
            new["blur"] = _r(layer["blur"] * mean)
        out.append(new)
    return out


CLOTH_PARTS = ("torso", "arm", "leg", "cape")


def textures(layers: list[dict], base: str, seed: int) -> list[dict]:
    """After every shape of hair, its strands (a noise stretched along the fall of the hair, multiplied) and their sheen;
    after every large shape of cloth of the torso, the arms, the legs and the cape, the weave of the cloth."""
    out = []
    for i, layer in enumerate(layers):
        out.append(layer)
        if layer.get("blend") or layer.get("clip") or "fill" not in layer or layer.get("alpha", 1) < 0.6:
            continue
        box = shape_box(layer["shape"])
        if box is None or (box[2] - box[0]) * (box[3] - box[1]) < 4:
            continue
        keep = {k: layer[k] for k in ("only", "except") if k in layer}
        paint = json.dumps(layer["fill"])
        if "$p.hair" in paint:
            out.append({"shape": layer["shape"], "fill": noise(0.26, seed + i, (0.3, "#3E3450"), (0.62, "#FFFFFF"), octaves=3, scale_y=3.2),
                        "blend": "multiply", "alpha": 0.6, **keep})
            out.append({"shape": layer["shape"], "fill": noise(0.12, seed + i + 250, (0.3, "#2E2640"), (0.6, "#FFFFFF"), octaves=2, scale_y=1.6),
                        "blend": "multiply", "alpha": 0.4, **keep})  # single hairs
            out.append({"shape": layer["shape"], "fill": noise(0.26, seed + i + 500, (0.6, "#000000"), (0.86, "#FFF2DC"), octaves=2, scale_y=3.2),
                        "blend": "add", "clip": True, "alpha": 0.32, **keep})
        elif base in CLOTH_PARTS and "$p.skin" not in paint:
            out.append({"shape": layer["shape"], "fill": noise(0.45, seed + i, (0.32, "#8A8498"), (0.6, "#FFFFFF"), octaves=3),
                        "blend": "multiply", "alpha": 0.18, **keep})
            out.append({"shape": layer["shape"], "fill": noise(0.14, seed + i + 250, (0.3, "#7A7488"), (0.62, "#FFFFFF"), octaves=1, scale_y=0.14),
                        "blend": "multiply", "alpha": 0.14, **keep})  # the threads of the weave
            out.append({"shape": layer["shape"], "fill": noise(0.9, seed + i + 500, (0.66, "#FFFFFF"), (0.9, "#3A3050"), octaves=3, scale_y=4.5, ridged=True),
                        "blend": "multiply", "alpha": 0.32, **keep})  # folds of the cloth along the fall
            out.append({"shape": layer["shape"], "fill": noise(0.9, seed + i + 750, (0.6, "#000000"), (0.85, "#FFF6E8"), octaves=2, scale_y=4.5),
                        "blend": "add", "clip": True, "alpha": 0.14, **keep})  # their lit ridges
        elif "$p.skin" in paint:
            out.append({"shape": layer["shape"], "fill": noise(0.6, seed + i, (0.36, "#C08080"), (0.6, "#FFFFFF"), octaves=3),
                        "blend": "multiply", "alpha": 0.12, **keep})  # the warmth and unevenness of skin
    return out


def finish(recipe: Recipe, name: str) -> None:
    """Applies the looks, moves the drawing from joint units to the canvas and writes the file."""
    base = name.replace("_back", "").replace("_side", "")
    back = name.endswith("_back")
    from_side = name.endswith("_side")
    for person in [*PROTAGONISTS, *PEOPLE, "ren"]:
        for behind, build in (SIDE if from_side else LOOKS).get((person, base), []):
            x = Recipe("x", recipe.w, recipe.h, seed=person + name)
            if from_side:
                build(x)
            else:
                build(x, back)
            for layer in x.layers:
                if person == "ren":
                    layer["except"] = [*PROTAGONISTS, *PEOPLE]
                else:
                    layer["only"] = [person]
            recipe.layers = x.layers + recipe.layers if behind else recipe.layers + x.layers
    recipe.layers = warp(recipe.layers, PROPORTIONS[base])  # the proportions of a real body
    recipe.layers = textures(recipe.layers, base, sum(ord(ch) for ch in name))
    w, h, ox, oy = CANVAS[base]
    recipe.layers = transform_layers(recipe.layers, 1.0, ox, oy)
    recipe.origin = [ox, oy]
    recipe.palette = dict(BASE)
    recipe.variants = {k: dict(v) for k, v in VARIANTS.items()}
    if not recipe.layers:  # a part that only some people have (the cape): one invisible layer keeps the recipe valid
        recipe.rect(0, 0, 1, 1, "#00000000")
    recipe.write(CHAR / f"{name}.json")
    print("wrote", name, len(recipe.layers), "layers")


def main() -> None:
    finish(head(), "head")
    finish(head_back(), "head_back")
    finish(torso(), "torso")
    finish(torso(back=True), "torso_back")
    finish(arm(), "arm")
    finish(leg(), "leg")
    finish(part("cape"), "cape")
    finish(part("cape_back"), "cape_back")
    finish(head_side(), "head_side")
    finish(torso_side(), "torso_side")
    finish(part("cape_side"), "cape_side")
    shadow().write(CHAR / "shadow.json")
    write_rig()
    print("rig and clips written under", (ART / "rigs").relative_to(ROOT))


if __name__ == "__main__":
    main()
