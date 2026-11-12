"""The people of the game: the parts of the humanoid rig (data/base/art/characters/ren/), the rig and its clips.

    python tools/art_chars.py

A person is about 59 art units tall (1.8 tiles) and 4.6 heads: the proportions of an anime character, not of a mascot.
The rig has a soft shadow, two legs, two arms, a torso, a head and a `cape` part behind the body (capes, long hair); the
torso, the head and the cape have a second recipe for the view from behind (`art_back`, spec 13). Every part is drawn
around its joint (the origin of its canvas) with flat tones, a hard violet shade away from the light (top left) and a thin
dark line. The palette variants are the protagonists and the kinds of people; what each one wears is in `art_looks.py`
(`only` and `except` layers). The shading is multiplied or added, so it works with every palette.
"""
from __future__ import annotations

import json

from art_looks import LOOKS, PEOPLE, PROTAGONISTS
from artkit import ART, ROOT, Recipe, linear, transform_layers

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
CANVAS = {"head": (44, 50, 22, 38), "torso": (40, 52, 20, 22), "arm": (14, 26, 7, 3), "leg": (14, 32, 7, 2), "cape": (48, 54, 24, 6)}


def part(name: str) -> Recipe:
    w, h, _, _ = CANVAS[name.replace("_back", "")]
    return Recipe(f"base:art/char/ren/{name}", w, h, (0, 0), seed="v3")


# ------------------------------------------------------------------------------------------------ head
FACE = "M -5.4 -9 Q -5.6 -4.6 -3.7 -2.3 Q -1.7 -0.4 0 -0.3 Q 1.7 -0.4 3.7 -2.3 Q 5.6 -4.6 5.4 -9 Q 5.2 -13.7 0 -13.9 Q -5.2 -13.7 -5.4 -9 Z"
HAIR_BACK = "M -6.2 -7.4 Q -6.9 -15.8 0 -16 Q 6.9 -15.8 6.2 -7.4 Q 6.1 -5.4 5.4 -4.6 L 4.8 -7 L -4.8 -7 L -5.4 -4.6 Q -6.1 -5.4 -6.2 -7.4 Z"
FRINGE = ("M -6 -7.4 Q -6.8 -15.5 0 -15.7 Q 6.8 -15.5 6 -7.4 Q 5.5 -9.6 4.6 -10.3 L 4 -7.9 Q 3.2 -10.1 2.1 -10.7 L 1.5 -8.3 "
          "Q 0.5 -10.5 -0.8 -10.9 L -1.2 -8.5 Q -2.2 -10.3 -3.3 -10.5 L -3.9 -8.1 Q -4.7 -9.9 -5.3 -10 Z")
SKULL_BACK = "M -6.3 -7 Q -7 -15.8 0 -16 Q 7 -15.8 6.3 -7 Q 6.2 -2.2 3.4 -1.2 Q 0 -0.4 -3.4 -1.2 Q -6.2 -2.2 -6.3 -7 Z"


def eye(r: Recipe, x: float, only=None, skip=None) -> None:
    """An anime eye: a white, a tall iris that is darker at the top, a pupil, two sparks, a heavy upper lash."""
    kw = {"only": only, "skip": skip}
    r.ellipse(x, -6.0, 1.5, 1.6, "#FFFFFF", **kw)
    r.ellipse(x, -5.9, 1.1, 1.45, linear(x, -7.4, x, -4.4, (0, OUT), (0.35, "$p.eye"), (1, "#FFFFFF")), **kw)
    r.ellipse(x, -5.9, 1.1, 1.45, "$p.eye", alpha=0.45, **kw)
    r.ellipse(x, -6.0, 0.48, 0.75, OUT, **kw)
    r.rect(x - 1.5, -7.6, 3, 0.9, "#201838", alpha=0.35, **kw)  # the shade of the lid
    r.ellipse(x - 0.45, -6.6, 0.4, 0.4, "#FFFFFF", **kw)
    r.ellipse(x + 0.42, -5.2, 0.22, 0.22, "#FFFFFF", alpha=0.9, **kw)
    r.path(f"M {x - 1.75} -6.4 Q {x - 1.2} -7.9 {x} -7.95 Q {x + 1.3} -7.9 {x + 1.8} -6.5", None, stroke=OUT, width=0.55, **kw)
    r.path(f"M {x - 1.2} -4.45 Q {x} -4.2 {x + 1.2} -4.5", None, stroke=OUT, width=0.2, alpha=0.6, **kw)


def head() -> Recipe:
    r = part("head")
    r.path(HAIR_BACK, "$p.hair", stroke=OUT, width=0.45)
    for sx in (-1, 1):  # ears
        r.ellipse(sx * 5.5, -6.2, 0.95, 1.5, "$p.skin", stroke=OUT, width=0.35)
        r.ellipse(sx * 5.5, -6.1, 0.45, 0.8, "#C8607A", alpha=0.3)
    r.path(FACE, "$p.skin", stroke=OUT, width=0.45)
    r.shade("M -5.6 -11 L 5.6 -11 L 5.5 -8.3 Q 0 -9.6 -5.5 -8.3 Z", 0.3, "#B06A80")  # the shade of the fringe
    r.shade("M 2.6 -11 Q 6.4 -6 3.7 -2.3 Q 1.7 -0.4 0 -0.3 Q 2.8 -2 3.4 -5 Q 3.6 -8 2.6 -11 Z", 0.22, "#B06A80")
    for sx in (-1, 1):  # a blush
        r.ellipse(sx * 3.5, -4.0, 1.25, 0.6, "#F06A7A", alpha=0.3, blur=0.35)
    eye(r, -2.55)
    eye(r, 2.55)
    for sx in (-1, 1):
        r.path(f"M {sx * 1.1} -9.0 Q {sx * 2.4} -9.5 {sx * 4.0} -8.9", None, stroke=OUT, width=0.32, alpha=0.85)  # eyebrows
    r.path("M 0.15 -4.0 L -0.1 -3.4", None, stroke="#A8607A", width=0.3, alpha=0.7)  # the nose
    r.path("M -0.9 -2.25 Q 0 -1.85 0.9 -2.25", None, stroke="#A84A5A", width=0.35)  # the mouth
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
RIG = [
    ("shadow", None, (0, 0), 0, None, "shadow", None),
    ("cape", "torso", (0, -16.6), 1, 6, "cape", "cape_back"),
    ("leg_l", "shadow", (-3.1, -27), 2, None, "leg", None),
    ("leg_r", "shadow", (3.1, -27), 2, None, "leg", None),
    ("arm_l", "torso", (-7.4, -14.6), 3, None, "arm", None),
    ("torso", "shadow", (0, -29), 4, None, "torso", "torso_back"),
    ("arm_r", "torso", (7.4, -14.6), 5, None, "arm", None),
    ("head", "torso", (0, -16.6), 7, None, "head", "head_back"),
]


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
        parts.append(item)
    rig = {"$schema": "../../../../schemas/rig.schema.json", "id": "base:art/rig/humanoid", "parts": parts}
    (ART / "rigs" / "humanoid.json").write_text(json.dumps(rig, indent=2) + "\n", encoding="utf-8")
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
        (ART / "clips" / f"{name}.json").write_text(json.dumps(clip, indent=2) + "\n", encoding="utf-8")


def finish(recipe: Recipe, name: str) -> None:
    """Applies the looks, moves the drawing from joint units to the canvas and writes the file."""
    base = name.replace("_back", "")
    back = name.endswith("_back")
    for person in [*PROTAGONISTS, *PEOPLE, "ren"]:
        for behind, build in LOOKS.get((person, base), []):
            x = Recipe("x", recipe.w, recipe.h, seed=person + name)
            build(x, back)
            for layer in x.layers:
                if person == "ren":
                    layer["except"] = [*PROTAGONISTS, *PEOPLE]
                else:
                    layer["only"] = [person]
            recipe.layers = x.layers + recipe.layers if behind else recipe.layers + x.layers
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
    shadow().write(CHAR / "shadow.json")
    write_rig()
    print("rig and clips written under", (ART / "rigs").relative_to(ROOT))


if __name__ == "__main__":
    main()
