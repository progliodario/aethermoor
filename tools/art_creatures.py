"""Adds detail layers (shading, highlights, bubbles, fur, armor plates, eye glints) over the recipes of data/base/art/creatures/.

The palettes and the variants of every file stay as they are: only layers are appended on top. The script keeps the first layers of each recipe
(the original body, by family) and rebuilds everything above them, so it can be run again and again. Run from tools/: `python art_creatures.py`.
"""
from __future__ import annotations

import json
import random

from art_creature_looks import KNIGHTS, NECKLACE, SLIMES, WOLVES, necklace
from artkit import ART, Recipe, transform_layers

DIR = ART / "creatures"
# the number of layers of the original recipes, by family
ORIGINAL = {"wolf": 15, "knight": 11, "giant": 7}
SINGLES = {"cave_bat": 11, "cave_spider": 18, "dune_scorpion": 17, "shore_crab": 15, "night_owl": 15, "myconid": 9, "stone_golem": 13, "wisp": 6}


def _add(layers: list, r: Recipe) -> list:
    return layers + r.layers


def slime_overlay(x0, x1, ytop, ybot, eyes, er, name: str) -> list[dict]:
    """Jelly details for a dome-shaped body: wet rim, bubbles, a second highlight, mouth, eye glints."""
    r = Recipe("x", 1, 1, seed=name)
    w, h = x1 - x0, ybot - ytop
    cx = (x0 + x1) / 2
    # the thick bottom edge: a darker band that follows the base
    r.path(f"M {x0 + w * 0.06} {ybot - h * 0.1} Q {cx} {ybot + h * 0.12} {x1 - w * 0.06} {ybot - h * 0.1} Q {cx} {ybot - h * 0.22} {x0 + w * 0.06} {ybot - h * 0.1} Z", "#000000", alpha=0.16)
    r.path(f"M {x0 + w * 0.12} {ybot - h * 0.02} Q {cx} {ybot + h * 0.1} {x1 - w * 0.12} {ybot - h * 0.02}", None, stroke="$p.light", width=max(0.7, h * 0.04), alpha=0.4)
    # bubbles and the glints inside the jelly
    for fx, fy, fr in ((0.74, 0.62, 0.075), (0.28, 0.72, 0.055), (0.8, 0.38, 0.045), (0.62, 0.8, 0.04)):
        bx, by, br = x0 + w * fx, ytop + h * fy, w * fr
        r.ellipse(bx, by, br, br, "#FFFFFF", alpha=0.16)
        r.ellipse(bx - br * 0.3, by - br * 0.3, br * 0.4, br * 0.4, "#FFFFFF", alpha=0.7)
    r.ellipse(x0 + w * 0.56, ytop + h * 0.2, w * 0.05, h * 0.03, "#FFFFFF", alpha=0.55)
    r.path(f"M {x0 + w * 0.2} {ytop + h * 0.26} Q {x0 + w * 0.26} {ytop + h * 0.12} {x0 + w * 0.42} {ytop + h * 0.09}", None, stroke="#FFFFFF", width=max(0.8, h * 0.05), alpha=0.35)
    # a small mouth between the eyes
    (ex0, ey), (ex1, _) = eyes[0], eyes[-1]
    mx = (ex0 + ex1) / 2
    r.path(f"M {mx - er * 1.5} {ey + er * 1.9} Q {mx} {ey + er * 3.2} {mx + er * 1.5} {ey + er * 1.9}", None, stroke="$p.outline", width=max(0.6, er * 0.45), alpha=0.75)
    for ex, ey in eyes:
        r.ellipse(ex - er * 0.35, ey - er * 0.6, er * 0.38, er * 0.42, "#FFFFFF", alpha=0.9)
        r.ellipse(ex + er * 0.25, ey + er * 0.55, er * 0.22, er * 0.2, "#FFFFFF", alpha=0.45)
    return r.layers


def wolf_overlay(name: str) -> list[dict]:
    r = Recipe("x", 40, 40, seed=name)
    # fur strokes on the body, following its shape
    for x, y, lean in ((11, 27, -1.5), (14, 31, -1), (18, 33, -0.5), (23, 33, 0.5), (27, 31, 1), (30, 27, 1.5), (16, 28, -0.6), (25, 29, 0.6), (20, 29.5, 0)):
        r.path(f"M {x} {y} Q {x + lean * 0.6} {y + 2} {x + lean} {y + 4}", None, stroke="$p.dark", width=0.9, alpha=0.5)
    for x, y in ((12, 24), (28, 24), (20, 26)):
        r.path(f"M {x} {y} Q {x + 0.6} {y - 1.5} {x + 1.8} {y - 2.4}", None, stroke="$p.light", width=0.8, alpha=0.5)
    # a ruff around the face: jagged tufts at the sides of the head
    r.poly([(8.2, 14.5), (5.2, 17.5), (8.6, 17.2), (6.2, 21), (10, 20.2), (9.5, 14)], "$p.fur", stroke="$p.outline", width=1.0)
    r.poly([(31.8, 14.5), (34.8, 17.5), (31.4, 17.2), (33.8, 21), (30, 20.2), (30.5, 14)], "$p.fur", stroke="$p.outline", width=1.0)
    r.poly([(9.5, 16), (7.6, 18.2), (9.8, 18.4)], "$p.light", alpha=0.6)
    r.poly([(30.5, 16), (32.4, 18.2), (30.2, 18.4)], "$p.light", alpha=0.6)
    # a darker mask over the muzzle bridge, a brow over each eye, a glint in each eye
    r.path("M 20 9.5 Q 18.4 14 19 19 L 21 19 Q 21.6 14 20 9.5 Z", "$p.dark", alpha=0.55)
    r.path("M 11.5 12.8 Q 14.5 12 17 13.6", None, stroke="$p.outline", width=1.1)
    r.path("M 28.5 12.8 Q 25.5 12 23 13.6", None, stroke="$p.outline", width=1.1)
    for ex in (14.5, 25.5):
        r.ellipse(ex - 0.7, 14.4, 0.55, 0.45, "#FFFFFF", alpha=0.95)
    # whiskers, the nose shine, the line of the mouth
    for dy, sy in ((0, -1), (1.6, 0.4)):
        r.line(15.8, 21.4 + dy, 10.4, 20.6 + dy + sy, "$p.light", width=0.5, alpha=0.7)
        r.line(24.2, 21.4 + dy, 29.6, 20.6 + dy + sy, "$p.light", width=0.5, alpha=0.7)
    r.ellipse(19.5, 20.2, 0.6, 0.35, "#FFFFFF", alpha=0.7)
    r.path("M 17.5 23.4 Q 20 25 22.5 23.4", None, stroke="$p.outline", width=0.7)
    # a rim light on the top of the head and the ears
    r.path("M 12 8.5 Q 20 5.8 28 8.5", None, stroke="#FFFFFF", width=0.8, alpha=0.3)
    r.path("M 9.4 4.6 L 11.6 8.4", None, stroke="$p.light", width=0.8, alpha=0.7)
    r.path("M 30.6 4.6 L 28.4 8.4", None, stroke="$p.light", width=0.8, alpha=0.7)
    return r.layers


def knight_overlay(name: str) -> list[dict]:
    r = Recipe("x", 56, 64, seed=name)
    # plates of the body with rivets and cracks that glow
    r.path("M 14 56 Q 12 38 28 33 Q 44 38 42 56", None, stroke="$p.dark", width=1.0, alpha=0.7)
    r.path("M 15 46 Q 28 50 41 46", None, stroke="$p.dark", width=1.2, alpha=0.6)
    r.path("M 14 40 Q 28 44 42 40", None, stroke="$p.light", width=0.8, alpha=0.4)
    for x, y in ((17, 42), (39, 42), (19, 53), (37, 53), (28, 56)):
        r.ellipse(x, y, 1.1, 1.1, "$p.light", stroke="$p.outline", width=0.5)
    r.path("M 28 52 L 26 57 L 28.4 55.6 L 27 60", None, stroke="$p.glow", width=0.9, alpha=0.8)
    r.path("M 20 36 L 22 40 L 21 43", None, stroke="$p.glow", width=0.7, alpha=0.6)
    # the shoulders (round pauldrons) with a rim
    for x in (12, 44):
        r.ellipse(x, 35.5, 6.6, 5.4, None, stroke="$p.light", width=0.8, alpha=0.5)
        r.ellipse(x - 1.6, 34, 2.4, 1.5, "#FFFFFF", alpha=0.3)
        r.path(f"M {x - 5} 38.5 Q {x} 41.5 {x + 5} 38.5", None, stroke="#000000", width=0.9, alpha=0.3)
    # the helmet: a crest line, a rim light, the visor glow
    r.path("M 28 8.4 L 28 18", None, stroke="$p.dark", width=1.0, alpha=0.7)
    r.path("M 20 12 Q 22 9.5 26 9", None, stroke="#FFFFFF", width=1.0, alpha=0.4)
    r.rect(20, 18.5, 16, 1.2, "#000000", alpha=0.35)
    r.ellipse(24.5, 20.5, 3.2, 2.2, "$p.glow", alpha=0.25)
    r.ellipse(31.5, 20.5, 3.2, 2.2, "$p.glow", alpha=0.25)
    # shine on the horns and a nick
    r.path("M 13 5.5 L 19 12.5", None, stroke="#FFFFFF", width=0.6, alpha=0.55)
    r.path("M 43 5.5 L 37 12.5", None, stroke="#FFFFFF", width=0.6, alpha=0.55)
    r.ellipse(28, 30, 9, 1.6, "#000000", alpha=0.25)  # the shadow of the helmet on the chest
    return r.layers


def gloss(layers: list[dict], palette: dict, name: str) -> list[dict]:
    """Generic detail for the single creatures: a highlight and a shade on the biggest shape, a glint in every eye."""
    r = Recipe("x", 1, 1, seed=name)
    best, best_area = None, 0.0
    for layer in layers:
        shape = layer["shape"]
        fill = layer.get("fill", {})
        if "ellipse" in shape and fill.get("color", "") != "#000000" and "linear" not in fill:
            cx, cy, rx, ry = shape["ellipse"]
            if rx * ry > best_area and "radial" in fill:
                best, best_area = (cx, cy, rx, ry), rx * ry
    if best:
        cx, cy, rx, ry = best
        r.ellipse(cx - rx * 0.28, cy - ry * 0.45, rx * 0.34, ry * 0.2, "#FFFFFF", alpha=0.3)
        r.ellipse(cx + rx * 0.2, cy + ry * 0.55, rx * 0.7, ry * 0.28, "#000000", alpha=0.12)
        rng = random.Random(name)
        for _ in range(4):
            a = rng.uniform(0, 6.28)
            px, py = cx + rx * 0.5 * rng.uniform(-1, 1), cy + ry * 0.5 * rng.uniform(-1, 1)
            r.line(px, py, px + 1.6 * (1 if a < 3.14 else -1), py + 1.2, "$p.dark", width=0.6, alpha=0.4)
    for layer in layers:
        if layer.get("fill", {}).get("color") == "$p.eye" and "ellipse" in layer["shape"]:
            ex, ey, erx, ery = layer["shape"]["ellipse"]
            r.ellipse(ex - erx * 0.3, ey - ery * 0.35, erx * 0.3, ery * 0.3, "#FFFFFF", alpha=0.85)
    return r.layers


def _crowned(layers: list[dict]) -> bool:
    return len(layers) > 5 and layers[5].get("fill", {}).get("color") == "#F2C94C"


def _features(fn, necklace_too: bool = False) -> list[dict]:
    r = Recipe("x", 1, 1)
    fn(r)
    if necklace_too:
        necklace(r)
    return r.layers


def main() -> None:
    changed = 0
    for path in sorted(DIR.glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        name = path.stem
        pal = set(d["palette"])
        w = d["canvas"]["w"]
        layers = d["layers"]
        extra: list[dict] | None = None
        if w == 36 and d["canvas"]["h"] == 30 and "gold" not in pal:
            layers = layers[: 7 if _crowned(layers) else 5]
            extra = slime_overlay(3, 33, 6, 27, [(13, 18), (23, 18)], 1.8, name)
            if name in SLIMES:
                extra += _features(SLIMES[name], name in NECKLACE)
        elif w == 61:
            layers = layers[: ORIGINAL["giant"]]
            extra = slime_overlay(5.1, 56.1, 22.2, 58, [(22.1, 42.6), (39.1, 42.6)], 3.1, name)
            extra += transform_layers(_features(SLIMES[name]), 1.7, 0, 12)
        elif w == 40 and "fur" in pal:
            layers = layers[: ORIGINAL["wolf"]]
            extra = wolf_overlay(name) + _features(WOLVES[name])
        elif w == 56 and "slit" in pal:
            layers = layers[: ORIGINAL["knight"]]
            extra = knight_overlay(name) + _features(KNIGHTS[name])
        elif name in SINGLES:
            layers = layers[: SINGLES[name]]
            extra = gloss(layers, d["palette"], name)
        if extra is None:
            continue
        d["layers"] = layers + extra
        path.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        changed += 1
    print("rebuilt", changed, "recipes")


if __name__ == "__main__":
    main()
