#!/usr/bin/env python3
"""Writes the font of the interface, `data/base/fonts/aether.json` (schemas/font.schema.json; spec 13, "Font").

    python tools/make_font.py [--show out.png "a text"]

The font is drawn here, stroke by stroke: every glyph is a path of single lines and curves that the clients draw with a
round pen of the `stroke` width, using the rasterizer of the art recipes, at the size they need. A glyph lives in a cell of
8 x 11 units: the caps go from y 2.5 to 8.5 (the baseline), the lower case is 4 units tall, accents and descenders have the
room above and below. `w` is the width a glyph takes in a text that is not monospaced; its strokes are centred in the cell.
`--show` draws a text with the reference rasterizer, to look at the font.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "base" / "fonts" / "aether.json"
CELL_W, CELL_H, TOP = 8, 11, 1.5
STROKE = 0.95


def ring(cx: float, cy: float, rx: float, ry: float) -> str:
    k = 0.5523
    return (f"M {cx - rx} {cy} C {cx - rx} {cy - ry * k} {cx - rx * k} {cy - ry} {cx} {cy - ry} C {cx + rx * k} {cy - ry} {cx + rx} {cy - ry * k} {cx + rx} {cy} "
            f"C {cx + rx} {cy + ry * k} {cx + rx * k} {cy + ry} {cx} {cy + ry} C {cx - rx * k} {cy + ry} {cx - rx} {cy + ry * k} {cx - rx} {cy} Z")


def dot(x: float, y: float) -> str:
    return f"M {x} {y - 0.1} L {x} {y + 0.1}"


BOWL = ring(2.85, 5, 1.85, 2)  # the round of a, d, g, o, q
BOWL_B = ring(2.85, 5, 1.85, 2)  # the round of b and p (the stem is on the left)
O_CAP = ring(3.3, 4, 2.4, 3)
P_CAP = "M 1 7 L 1 1 L 3.2 1 Q 5 1 5 2.7 Q 5 4.4 3.2 4.4 L 1 4.4"

# glyph: (width, strokes); y 1 is the top of the caps, 3 the top of the lower case, 7 the baseline, 9 the descenders
GLYPHS: dict[str, tuple[float, str]] = {
    " ": (3.2, ""),
    "a": (5.8, BOWL + " M 4.7 3 L 4.7 7"),
    "b": (5.8, "M 1 0.8 L 1 7 " + BOWL_B),
    "c": (5.2, "M 4.5 3.9 Q 3.7 3 2.8 3 Q 0.95 3 0.95 5 Q 0.95 7 2.8 7 Q 3.7 7 4.5 6.1"),
    "d": (5.8, BOWL + " M 4.7 0.8 L 4.7 7"),
    "e": (5.6, "M 0.95 5 L 4.65 5 Q 4.65 3 2.8 3 Q 0.95 3 0.95 5 Q 0.95 7 2.8 7 Q 3.8 7 4.45 6.3"),
    "f": (4.2, "M 3.9 1.1 Q 3.4 0.8 2.9 0.8 Q 1.9 0.8 1.9 2 L 1.9 7 M 0.8 3.2 L 3.4 3.2"),
    "g": (5.8, BOWL + " M 4.7 3 L 4.7 7.6 Q 4.7 9 3 9 Q 1.9 9 1.3 8.5"),
    "h": (5.6, "M 1 0.8 L 1 7 M 1 4.4 Q 1.6 3 2.9 3 Q 4.6 3 4.6 4.6 L 4.6 7"),
    "i": (2.4, "M 1.2 3 L 1.2 7 " + dot(1.2, 1.4)),
    "j": (2.8, "M 1.7 3 L 1.7 7.8 Q 1.7 9 0.6 9 " + dot(1.7, 1.4)),
    "k": (5.2, "M 1 0.8 L 1 7 M 4.2 3 L 1 5.4 M 2.2 4.6 L 4.4 7"),
    "l": (2.4, "M 1.2 0.8 L 1.2 7"),
    "m": (7.2, "M 1 3 L 1 7 M 1 4.2 Q 1.4 3 2.4 3 Q 3.6 3 3.6 4.4 L 3.6 7 M 3.6 4.2 Q 4 3 5 3 Q 6.2 3 6.2 4.4 L 6.2 7"),
    "n": (5.6, "M 1 3 L 1 7 M 1 4.4 Q 1.6 3 2.9 3 Q 4.6 3 4.6 4.6 L 4.6 7"),
    "o": (5.7, BOWL),
    "p": (5.8, "M 1 3 L 1 9 " + BOWL_B),
    "q": (5.8, BOWL + " M 4.7 3 L 4.7 9"),
    "r": (4.0, "M 1 3 L 1 7 M 1 4.6 Q 1.5 3 3.4 3.1"),
    "s": (5.0, "M 4 3.6 Q 3.4 3 2.5 3 Q 1 3 1 4 Q 1 4.9 2.5 5 Q 4.1 5.1 4.1 6 Q 4.1 7 2.5 7 Q 1.5 7 0.9 6.4"),
    "t": (4.4, "M 1.9 1.4 L 1.9 6 Q 1.9 7 3 7 Q 3.4 7 3.8 6.8 M 0.7 3.1 L 3.5 3.1"),
    "u": (5.6, "M 1 3 L 1 5.4 Q 1 7 2.6 7 Q 3.9 7 4.6 5.6 M 4.6 3 L 4.6 7"),
    "v": (5.2, "M 0.8 3 L 2.6 7 L 4.4 3"),
    "w": (7.0, "M 0.8 3 L 2.1 7 L 3.5 3.8 L 4.9 7 L 6.2 3"),
    "x": (5.2, "M 0.9 3 L 4.3 7 M 4.3 3 L 0.9 7"),
    "y": (5.2, "M 0.8 3 L 2.6 7 M 4.4 3 L 2.2 8 Q 1.8 9 0.8 9"),
    "z": (5.2, "M 1 3 L 4.2 3 L 1 7 L 4.2 7"),
    "A": (6.4, "M 0.8 7 L 3.2 1 L 5.6 7 M 1.7 5 L 4.7 5"),
    "B": (6.2, "M 1 1 L 1 7 M 1 1 L 3.2 1 Q 4.8 1 4.8 2.5 Q 4.8 4 3.2 4 L 1 4 M 3.2 4 Q 5.2 4 5.2 5.5 Q 5.2 7 3.4 7 L 1 7"),
    "C": (6.2, "M 5.3 2.2 Q 4.6 1 3.3 1 Q 0.9 1 0.9 4 Q 0.9 7 3.3 7 Q 4.6 7 5.3 5.8"),
    "D": (6.4, "M 1 1 L 1 7 L 2.8 7 Q 5.4 7 5.4 4 Q 5.4 1 2.8 1 L 1 1"),
    "E": (5.8, "M 4.8 1 L 1 1 L 1 7 L 4.8 7 M 1 4 L 4.2 4"),
    "F": (5.6, "M 4.8 1 L 1 1 L 1 7 M 1 4 L 4.2 4"),
    "G": (6.4, "M 5.3 2.2 Q 4.6 1 3.3 1 Q 0.9 1 0.9 4 Q 0.9 7 3.3 7 Q 5.3 7 5.3 4.6 L 3.4 4.6"),
    "H": (6.2, "M 1 1 L 1 7 M 5.2 1 L 5.2 7 M 1 4 L 5.2 4"),
    "I": (2.4, "M 1.2 1 L 1.2 7"),
    "J": (4.6, "M 3.6 1 L 3.6 5.4 Q 3.6 7 2.2 7 Q 1.2 7 0.8 6.2"),
    "K": (6.0, "M 1 1 L 1 7 M 5 1 L 1 4.6 M 2.4 3.6 L 5.2 7"),
    "L": (5.2, "M 1 1 L 1 7 L 4.6 7"),
    "M": (7.2, "M 1 7 L 1 1 L 3.6 5.2 L 6.2 1 L 6.2 7"),
    "N": (6.2, "M 1 7 L 1 1 L 5.2 7 L 5.2 1"),
    "O": (6.6, O_CAP),
    "P": (5.8, P_CAP),
    "Q": (6.6, O_CAP + " M 3.8 5.4 L 5.6 7.4"),
    "R": (6.0, P_CAP + " M 3 4.4 L 5.2 7"),
    "S": (6.0, "M 4.9 2 Q 4.2 1 3 1 Q 1.1 1 1.1 2.5 Q 1.1 3.8 3 4 Q 5.1 4.2 5.1 5.5 Q 5.1 7 3 7 Q 1.6 7 0.9 6"),
    "T": (5.8, "M 0.7 1 L 5.1 1 M 2.9 1 L 2.9 7"),
    "U": (6.2, "M 1 1 L 1 4.8 Q 1 7 3.1 7 Q 5.2 7 5.2 4.8 L 5.2 1"),
    "V": (6.2, "M 0.8 1 L 3.1 7 L 5.4 1"),
    "W": (7.8, "M 0.7 1 L 2.2 7 L 3.9 2.4 L 5.6 7 L 7.1 1"),
    "X": (6.0, "M 0.9 1 L 5.1 7 M 5.1 1 L 0.9 7"),
    "Y": (5.8, "M 0.7 1 L 2.9 4.2 L 5.1 1 M 2.9 4.2 L 2.9 7"),
    "Z": (5.9, "M 0.9 1 L 5 1 L 0.9 7 L 5 7"),
    "0": (5.7, ring(2.85, 4, 1.85, 3) + " M 2.2 5.2 L 3.5 2.8"),
    "1": (4.4, "M 1.1 2.5 L 2.8 1 L 2.8 7"),
    "2": (5.6, "M 1 2.4 Q 1.2 1 2.8 1 Q 4.6 1 4.6 2.6 Q 4.6 3.8 1 7 L 4.7 7"),
    "3": (5.6, "M 1 1.9 Q 1.6 1 2.8 1 Q 4.5 1 4.5 2.5 Q 4.5 3.9 2.6 3.9 Q 4.7 3.9 4.7 5.5 Q 4.7 7 2.8 7 Q 1.4 7 0.9 6"),
    "4": (5.6, "M 3.7 7 L 3.7 1 L 0.8 5.2 L 4.9 5.2"),
    "5": (5.6, "M 4.4 1 L 1.4 1 L 1.1 3.9 Q 1.8 3.4 2.8 3.4 Q 4.7 3.4 4.7 5.2 Q 4.7 7 2.8 7 Q 1.5 7 0.9 6.1"),
    "6": (5.6, "M 4.3 1.6 Q 3.7 1 2.9 1 Q 1 1 1 4.4 Q 1 7 2.8 7 Q 4.6 7 4.6 5.2 Q 4.6 3.6 2.8 3.6 Q 1.4 3.6 1 4.8"),
    "7": (5.4, "M 0.9 1 L 4.7 1 L 2.2 7"),
    "8": (5.6, ring(2.8, 2.5, 1.5, 1.5) + " " + ring(2.8, 5.5, 1.85, 1.5)),
    "9": (5.6, "M 1.3 6.4 Q 1.9 7 2.7 7 Q 4.6 7 4.6 3.6 Q 4.6 1 2.8 1 Q 1 1 1 2.8 Q 1 4.4 2.8 4.4 Q 4.2 4.4 4.6 3.2"),
    ".": (2.4, dot(1.2, 6.9)),
    ",": (2.4, "M 1.3 6.8 L 1.3 7.2 L 0.8 8.2"),
    ":": (2.4, dot(1.2, 3.6) + " " + dot(1.2, 6.9)),
    ";": (2.4, dot(1.3, 3.6) + " M 1.3 6.8 L 1.3 7.2 L 0.8 8.2"),
    "!": (2.4, "M 1.2 1 L 1.2 5 " + dot(1.2, 6.9)),
    "?": (5.0, "M 1 2.3 Q 1.2 1 2.6 1 Q 4.2 1 4.2 2.4 Q 4.2 3.4 2.6 4.2 L 2.6 5 " + dot(2.6, 6.9)),
    "'": (2.0, "M 1 1 L 1 2.6"),
    '"': (3.6, "M 1 1 L 1 2.6 M 2.6 1 L 2.6 2.6"),
    "`": (2.8, "M 0.9 0.9 L 1.9 2.1"),
    "(": (3.2, "M 2.4 0.6 Q 0.9 4 2.4 8"),
    ")": (3.2, "M 0.8 0.6 Q 2.3 4 0.8 8"),
    "[": (3.2, "M 2.4 0.8 L 1 0.8 L 1 7.8 L 2.4 7.8"),
    "]": (3.2, "M 0.8 0.8 L 2.2 0.8 L 2.2 7.8 L 0.8 7.8"),
    "{": (3.6, "M 2.8 0.8 Q 1.8 0.8 1.8 2 L 1.8 3.4 Q 1.8 4.3 0.8 4.3 Q 1.8 4.3 1.8 5.2 L 1.8 6.6 Q 1.8 7.8 2.8 7.8"),
    "}": (3.6, "M 0.8 0.8 Q 1.8 0.8 1.8 2 L 1.8 3.4 Q 1.8 4.3 2.8 4.3 Q 1.8 4.3 1.8 5.2 L 1.8 6.6 Q 1.8 7.8 0.8 7.8"),
    "+": (5.4, "M 0.9 4.4 L 4.5 4.4 M 2.7 2.6 L 2.7 6.2"),
    "-": (4.2, "M 0.9 4.4 L 3.3 4.4"),
    "=": (5.4, "M 0.9 3.5 L 4.5 3.5 M 0.9 5.3 L 4.5 5.3"),
    "*": (4.6, "M 2.3 1.6 L 2.3 4.6 M 1 2.4 L 3.6 3.8 M 3.6 2.4 L 1 3.8"),
    "/": (4.4, "M 3.6 0.8 L 0.8 7.6"),
    "\\": (4.4, "M 0.8 0.8 L 3.6 7.6"),
    "|": (2.4, "M 1.2 0.6 L 1.2 8"),
    "_": (5.4, "M 0.6 7.9 L 4.8 7.9"),
    "<": (5.0, "M 4 2.2 L 1 4.4 L 4 6.6"),
    ">": (5.0, "M 1 2.2 L 4 4.4 L 1 6.6"),
    "^": (5.0, "M 1 3.2 L 2.5 1 L 4 3.2"),
    "~": (5.6, "M 0.9 4.8 Q 1.8 3.4 2.8 4.4 Q 3.8 5.4 4.7 4"),
    "#": (6.4, "M 2.4 1.4 L 1.8 7 M 4.6 1.4 L 4 7 M 0.8 3.2 L 5.6 3.2 M 0.6 5.2 L 5.4 5.2"),
    "%": (6.8, ring(1.8, 2.2, 1.0, 1.2) + " " + ring(5, 5.8, 1.0, 1.2) + " M 5.4 1 L 1.4 7"),
    "&": (6.6, "M 5.6 7 L 2 2.8 Q 1.4 1 2.8 1 Q 4.2 1 3.8 2.6 Q 3.4 3.6 1.8 4.6 Q 0.6 5.6 1.4 6.6 Q 2.6 7.6 4.2 6.2 Q 5 5.4 5.4 4.2"),
    "@": (7.6, "M 5 5.6 Q 3.2 6 3.2 4.4 Q 3.2 2.8 4.6 2.8 Q 5.4 2.8 5.2 4.4 Q 5 5.6 6 5.4 Q 6.9 5 6.9 3.8 Q 6.9 1 4 1 Q 0.8 1 0.8 4.2 Q 0.8 7.4 4 7.4 Q 5.2 7.4 6 6.9"),
    "$": (5.6, "M 4.5 2.4 Q 3.9 1.6 2.8 1.6 Q 1.2 1.6 1.2 2.9 Q 1.2 4 2.8 4.2 Q 4.6 4.4 4.6 5.6 Q 4.6 6.8 2.8 6.8 Q 1.6 6.8 0.9 6 M 2.8 0.6 L 2.8 7.8"),
    "°": (3.6, ring(1.8, 1.9, 1.0, 1.0)),
    "«": (5.6, "M 2.6 3 L 1 5 L 2.6 7 M 4.6 3 L 3 5 L 4.6 7"),
    "»": (5.6, "M 1 3 L 2.6 5 L 1 7 M 3 3 L 4.6 5 L 3 7"),
    "‘": (2.2, "M 1.3 0.9 L 0.9 1.9 L 0.9 2.4"),
    "’": (2.2, "M 1.1 0.9 L 1.1 1.4 L 0.7 2.4"),
    "“": (3.8, "M 1.3 0.9 L 0.9 1.9 L 0.9 2.4 M 2.9 0.9 L 2.5 1.9 L 2.5 2.4"),
    "”": (3.8, "M 1.1 0.9 L 1.1 1.4 L 0.7 2.4 M 2.7 0.9 L 2.7 1.4 L 2.3 2.4"),
    "–": (5.4, "M 0.8 4.4 L 4.6 4.4"),
    "—": (7.6, "M 0.6 4.4 L 7 4.4"),
    "…": (7.0, dot(1.3, 6.9) + " " + dot(3.5, 6.9) + " " + dot(5.7, 6.9)),
    "→": (7.0, "M 0.8 4.4 L 6 4.4 M 4.2 2.8 L 6 4.4 L 4.2 6"),
    "←": (7.0, "M 6.2 4.4 L 1 4.4 M 2.8 2.8 L 1 4.4 L 2.8 6"),
    "↑": (5.4, "M 2.7 7 L 2.7 1.4 M 1 3.2 L 2.7 1.4 L 4.4 3.2"),
    "↓": (5.4, "M 2.7 1.4 L 2.7 7 M 1 5.2 L 2.7 7 L 4.4 5.2"),
    "★": (7.0, "M 3.5 1 L 4.3 3.3 L 6.7 3.4 L 4.8 4.9 L 5.5 7.2 L 3.5 5.8 L 1.5 7.2 L 2.2 4.9 L 0.3 3.4 L 2.7 3.3 Z"),
    "•": (3.6, "M 1.8 4.3 L 1.8 4.5"),
}

# accented letters: the letter (without its dot) and the mark above it
DOTLESS = {"i": "M 1.2 3 L 1.2 7", "j": "M 1.7 3 L 1.7 7.8 Q 1.7 9 0.6 9"}
MARKS = {"grave": "M {a} {t} L {b} {u}", "acute": "M {b} {t} L {a} {u}", "circumflex": "M {a} {u} L {c} {t} L {b} {u}", "umlaut": None}
ACCENTED = {"à": ("a", "grave"), "è": ("e", "grave"), "é": ("e", "acute"), "ì": ("i", "grave"), "í": ("i", "acute"), "ò": ("o", "grave"),
            "ó": ("o", "acute"), "ù": ("u", "grave"), "ú": ("u", "acute"), "á": ("a", "acute"), "ê": ("e", "circumflex"),
            "À": ("A", "grave"), "È": ("E", "grave"), "É": ("E", "acute"), "Ì": ("I", "grave"), "Ò": ("O", "grave"), "Ù": ("U", "grave"),
            "ä": ("a", "umlaut"), "ö": ("o", "umlaut"), "ü": ("u", "umlaut")}


def accented(letter: str, mark: str) -> tuple[float, str]:
    w, d = GLYPHS[letter]
    d = DOTLESS.get(letter, d)
    upper = letter.isupper()
    centre = {"i": 1.2, "I": 1.2}.get(letter, w / 2 - 0.2)
    top, low = (-0.9, 0.2) if upper else (0.9, 2.1)
    if mark == "umlaut":
        extra = dot(centre - 0.9, low - 0.4) + " " + dot(centre + 0.9, low - 0.4)
    else:
        extra = MARKS[mark].format(a=round(centre - 0.7, 2), b=round(centre + 0.7, 2), c=round(centre, 2), t=top, u=low)
    return max(w, 2.8), d + " " + extra


def shift(d: str, dx: float, dy: float) -> str:
    """Moves a path made of the absolute commands M L Q C Z."""
    out, nums = [], []

    def flush() -> None:
        for i in range(0, len(nums) - 1, 2):
            out.append(f"{round(nums[i] + dx, 2):g} {round(nums[i + 1] + dy, 2):g}")
        nums.clear()

    for tok in d.split():
        if tok.isalpha():
            flush()
            out.append(tok)
        else:
            nums.append(float(tok))
    flush()
    return " ".join(out)


def build() -> dict:
    glyphs = dict(GLYPHS)
    for ch, (letter, mark) in ACCENTED.items():
        glyphs[ch] = accented(letter, mark)
    data = {}
    for ch in sorted(glyphs):
        w, d = glyphs[ch]
        entry: dict = {"w": w}
        if d:
            entry["d"] = shift(d, (CELL_W - w) / 2, TOP)
        data[ch] = entry
    return {"$schema": "../../../schemas/font.schema.json", "id": "base:font/aether",
            "cell": {"w": CELL_W, "h": CELL_H, "top": TOP, "cap_top": TOP + 1, "cap_height": 6, "x_height": 4, "line": 9.8},
            "stroke": STROKE, "glyphs": data}


def show(font: dict, text: str, target: Path, scales=(1, 1.5, 2, 3)) -> None:
    """Draws the text once for each scale, monospaced as the desktop does and then with the widths of the glyphs."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from art_preview import Image
    from reference import raster

    rows = []
    for scale in scales:
        for mono in (True, False):
            image = Image(int((len(text) * CELL_W + 4) * scale), int(CELL_H * scale + 2), (0.07, 0.13, 0.25, 1.0))
            pen = 2.0
            for ch in text:
                glyph = font["glyphs"].get(ch, font["glyphs"]["?"])
                if "d" in glyph:
                    recipe = {"canvas": {"w": CELL_W, "h": CELL_H}, "layers": [{"shape": {"path": glyph["d"]}, "stroke": {"color": "#FFFFFF", "width": font["stroke"]}}]}
                    left = 0 if mono else (CELL_W - glyph["w"]) / 2
                    image.blit(raster.rasterize(recipe, scale), round((pen - left) * scale), 1)
                pen += CELL_W if mono else glyph["w"]
            rows.append(image)
    sheet = Image(max(r.w for r in rows), sum(r.h + 4 for r in rows), (0.07, 0.13, 0.25, 1.0))
    y = 0
    for row in rows:
        for py in range(row.h):
            sheet.px[((y + py) * sheet.w) * 4:((y + py) * sheet.w + row.w) * 4] = row.px[py * row.w * 4:(py + 1) * row.w * 4]
        y += row.h + 4
    sheet.save(target)


def main() -> int:
    font = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(font, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(font['glyphs'])} glyphs to {OUT.relative_to(ROOT)}")
    if "--show" in sys.argv:
        at = sys.argv.index("--show")
        show(font, sys.argv[at + 2], Path(sys.argv[at + 1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
