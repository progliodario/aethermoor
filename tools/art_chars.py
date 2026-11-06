"""Richer parts for the humanoid rig (data/base/art/characters/ren/): head, torso, arm, leg.

Keeps the canvas, the origin, the palette and the variants of each file (the palettes of the protagonists and of the
people), and rebuilds the layers with shading, highlights and small details. Shading is black or white with an alpha, so it
works with every palette. Run from tools/: `python art_chars.py`.
"""
from __future__ import annotations

import json

from art_looks import arm_looks, head_looks, leg_looks, torso_looks
from artkit import ART, Recipe, linear, radial, transform_layers

OUT = "$p.outline"
CHAR = ART / "characters" / "ren"


def head() -> Recipe:
    r = Recipe("base:art/char/ren/head", 22, 22, (11, 19))
    # hair behind the head (a little volume at the back and the sides)
    r.path("M 1.5 11 Q 0.5 1 11 0.5 Q 21.5 1 20.5 11 Q 20 14 18.5 14 L 3.5 14 Q 2 14 1.5 11 Z", "$p.hair", stroke=OUT, width=1.4)
    # ears
    for x in (2.6, 19.4):
        r.ellipse(x, 12.5, 1.7, 2.2, radial(x, 12, 3, (0, "#FFE0BD"), (1, "$p.skin")), stroke=OUT, width=1.0)
    # face
    r.ellipse(11, 12, 7.8, 8.2, radial(8, 8, 15, (0, "#FFEBD0"), (0.55, "$p.skin"), (1, "$p.skin")), stroke=OUT, width=1.4)
    r.ellipse(11, 17.4, 5.8, 2.6, "#000000", alpha=0.07)  # the shade of the chin
    # cheeks
    r.ellipse(6.4, 14.6, 1.8, 1.1, "#E8707A", alpha=0.32)
    r.ellipse(15.6, 14.6, 1.8, 1.1, "#E8707A", alpha=0.32)
    # eyes: white, iris, pupil, a spark of light
    for x in (8.0, 14.0):
        r.ellipse(x, 12.6, 1.9, 2.3, "#FFFFFF", stroke=OUT, width=0.7)
        r.ellipse(x, 12.9, 1.3, 1.8, "#3E2E26")
        r.ellipse(x, 13.1, 0.75, 1.1, OUT)
        r.ellipse(x - 0.45, 12.2, 0.5, 0.55, "#FFFFFF")
        r.line(x - 2.1, 10.3, x + 1.9, 10.0, OUT, width=0.9)  # the eyebrow
    r.path("M 9.8 17.2 Q 11 18.1 12.2 17.2", None, stroke="#B5546A", width=0.8)  # the mouth
    r.ellipse(11, 15.2, 0.5, 0.35, "#000000", alpha=0.18)  # the nose
    # the fringe with strands, and a highlight
    r.path("M 2.2 10.5 Q 2.4 1.5 11 1.2 Q 19.6 1.5 19.8 10.5 Q 18 6.5 15.5 7.3 Q 13.5 5.2 11 6.8 Q 8.5 5 6.5 7.3 Q 4 6.5 2.2 10.5 Z", "$p.hair", stroke=OUT, width=1.2)
    r.path("M 4 8.5 Q 4.5 3.5 10 2.6", None, stroke="#FFFFFF", width=1.4, alpha=0.28)
    r.path("M 9 6.8 Q 10 4.5 11.5 4.2", None, stroke="#000000", width=0.7, alpha=0.3)
    r.path("M 15 7.2 Q 16.5 4.5 18 5", None, stroke="#000000", width=0.7, alpha=0.25)
    return r


def torso() -> Recipe:
    r = Recipe("base:art/char/ren/torso", 22, 26, (11, 13))
    body = "M 3 3 Q 11 0 19 3 L 20 24 Q 11 26 2 24 Z"
    r.path(body, linear(0, 0, 0, 26, (0, "$p.shirt"), (1, "$p.shirt_dark")), stroke=OUT, width=1.4)
    r.path("M 3 3 Q 11 0 19 3 L 18.6 6 Q 11 3.6 3.4 6 Z", "#FFFFFF", alpha=0.18)  # the light on the shoulders
    r.path("M 15 6 L 19 5 L 20 24 L 16 24.5 Z", "#000000", alpha=0.14)  # the side in shade
    # collar
    r.path("M 7.5 2.2 Q 11 6.5 14.5 2.2 L 13.5 1.4 Q 11 4.2 8.5 1.4 Z", "$p.skin", stroke=OUT, width=0.9)
    r.path("M 6.5 2.4 L 11 8.5 L 15.5 2.4", None, stroke="$p.shirt_dark", width=1.3)
    # fold lines and the stitched seam
    r.path("M 11 8.5 L 11 21", None, stroke="#000000", width=0.7, alpha=0.18)
    r.path("M 6 11 Q 7 15 5.5 19", None, stroke="#000000", width=0.6, alpha=0.16)
    r.path("M 16 11 Q 15 15 16.5 19", None, stroke="#000000", width=0.6, alpha=0.16)
    # belt with a buckle, and the pants showing below
    r.rect(2.2, 19.5, 17.6, 3.6, "#4A3426", stroke=OUT, width=0.9)
    r.rect(2.6, 19.9, 16.8, 1.0, "#FFFFFF", alpha=0.14)
    r.rect(9.6, 19.3, 2.8, 4.0, "#D8B65A", stroke=OUT, width=0.7)
    r.rect(10.4, 20.4, 1.2, 1.8, "#7A5A1E")
    return r


def arm() -> Recipe:
    r = Recipe("base:art/char/ren/arm", 8, 16, (4, 2))
    r.path("M 1 1 Q 4 0 7 1 L 7 11 Q 4 13 1 11 Z", linear(0, 0, 8, 0, (0, "$p.shirt"), (1, "$p.shirt_dark")), stroke=OUT, width=1.4)
    r.path("M 1.6 1.4 Q 4 0.6 6.4 1.4 L 6.4 3.4 Q 4 2.6 1.6 3.4 Z", "#FFFFFF", alpha=0.2)  # the shoulder
    r.rect(1, 9, 6, 2.4, "$p.shirt_dark", stroke=OUT, width=0.8)  # the cuff
    r.rect(1.4, 9.3, 5.2, 0.7, "#FFFFFF", alpha=0.18)
    r.ellipse(4, 13.3, 3, 2.9, radial(3, 12, 5, (0, "#FFE0BD"), (1, "$p.skin")), stroke=OUT, width=1.2)  # the hand
    r.path("M 3 14.5 L 3 15.5 M 5 14.5 L 5 15.5", None, stroke=OUT, width=0.5, alpha=0.6)  # fingers
    return r


def leg() -> Recipe:
    r = Recipe("base:art/char/ren/leg", 9, 16, (4.5, 1))
    r.rect(1.5, 0, 6, 10, "$p.pants", stroke=OUT, width=1.4)
    r.rect(5.2, 0.4, 2, 9.6, "#000000", alpha=0.18)  # the side in shade
    r.rect(1.9, 0.6, 1.2, 8.6, "#FFFFFF", alpha=0.1)
    r.path("M 2 5 L 7 5.4", None, stroke="#000000", width=0.6, alpha=0.2)  # a crease at the knee
    # the boot: shaft with a cuff, toe cap, sole
    r.path("M 0.5 9.4 L 8.5 9.4 Q 9 15 6 15 L 1 15 Q 0 13 0.5 9.4 Z", "$p.boots", stroke=OUT, width=1.4)
    r.rect(0.6, 9.4, 7.8, 1.6, "#FFFFFF", alpha=0.16)
    r.path("M 0.3 14.4 L 7.6 14.4 Q 8.4 15.6 6 15.6 L 1 15.6 Z", "#000000", alpha=0.35)  # the sole
    r.ellipse(3.2, 12.8, 1.8, 1.2, "#FFFFFF", alpha=0.16)  # the toe cap
    return r


# the new canvas of every part: (width, height, shift x, shift y), so that the looks can reach outside the old one
GROW = {"head": (30, 32, 4, 10), "torso": (30, 30, 4, 0), "arm": (10, 20, 1, 0), "leg": (9, 16, 0, 0)}


def main() -> None:
    looks = {"head": head_looks, "torso": torso_looks, "arm": arm_looks, "leg": leg_looks}
    for recipe in (head(), torso(), arm(), leg()):
        name = recipe.id.rsplit("/", 1)[1]
        path = CHAR / f"{name}.json"
        old = json.loads(path.read_text(encoding="utf-8"))
        looks[name](recipe)
        w, h, dx, dy = GROW[name]
        if (dx, dy) != (0, 0):
            recipe.layers = transform_layers(recipe.layers, 1.0, dx, dy)
            recipe.origin = [recipe.origin[0] + dx, recipe.origin[1] + dy]
        recipe.w, recipe.h = w, h
        recipe.palette = old["palette"]
        recipe.variants = old.get("variants", {})
        recipe.write(path)
        print("wrote", path.name, len(recipe.layers), "layers")


if __name__ == "__main__":
    main()
