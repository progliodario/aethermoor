#!/usr/bin/env python3
"""Draws art recipes (data/base/art/**) as an HTML sheet of SVG pictures, to look at creatures and props without the game.

    python tools/art_preview.py [--out sheet.html] [--scale 4] [pattern ...]

The patterns match the ID of the recipe (`creatures/wolf` shows every recipe whose path contains it); no pattern shows all of them.
It follows the format of `schemas/art_recipe.schema.json` (layers of rect, ellipse, polygon and path with flat, linear or radial fills,
strokes, alpha and `$p.` palette colors); the game draws the same recipes with its own rasterizer (docs/spec/13-vector-art.md).
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "data" / "base" / "art"


def color(value: str, palette: dict) -> str:
    return palette[value[3:]] if value.startswith("$p.") else value


def svg_of(recipe: dict, uid: str) -> str:
    canvas, palette = recipe["canvas"], recipe["palette"]
    defs, body = [], []
    for i, layer in enumerate(recipe["layers"]):
        shape = layer["shape"]
        (kind, data), = shape.items()
        if kind == "rect":
            x, y, w, h = data
            element = f'<rect x="{x}" y="{y}" width="{w}" height="{h}"'
        elif kind == "ellipse":
            cx, cy, rx, ry = data
            element = f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}"'
        elif kind == "polygon":
            element = '<polygon points="' + " ".join(f"{x},{y}" for x, y in data) + '"'
        else:
            element = f'<path d="{data}"'
        fill = layer.get("fill")
        if fill is None:
            paint = "none"
        else:
            (fkind, f), = fill.items()
            if fkind == "color":
                paint = color(f, palette)
            else:
                gid = f"{uid}g{i}"
                stops = "".join(f'<stop offset="{o}" stop-color="{color(c, palette)}"/>' for o, c in f["stops"])
                if fkind == "linear":
                    defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{f["x0"]}" y1="{f["y0"]}" x2="{f["x1"]}" y2="{f["y1"]}">{stops}</linearGradient>')
                else:
                    defs.append(f'<radialGradient id="{gid}" gradientUnits="userSpaceOnUse" cx="{f["cx"]}" cy="{f["cy"]}" r="{f["r"]}">{stops}</radialGradient>')
                paint = f"url(#{gid})"
        stroke = layer.get("stroke")
        attrs = f' fill="{paint}"'
        if stroke:
            attrs += f' stroke="{color(stroke["color"], palette)}" stroke-width="{stroke["width"]}" stroke-linejoin="round"'
        if "alpha" in layer:
            attrs += f' opacity="{layer["alpha"]}"'
        body.append(element + attrs + "/>")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas["w"]}" height="{canvas["h"]}" viewBox="0 0 {canvas["w"]} {canvas["h"]}">'
            f'<defs>{"".join(defs)}</defs>{"".join(body)}</svg>')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("patterns", nargs="*")
    parser.add_argument("--out", default="art_sheet.html")
    parser.add_argument("--scale", type=float, default=4.0)
    args = parser.parse_args()
    cards = []
    for path in sorted(ART.rglob("*.json")):
        rel = path.relative_to(ART).as_posix()
        if args.patterns and not any(p in rel for p in args.patterns):
            continue
        recipe = json.loads(path.read_text(encoding="utf-8"))
        if "layers" not in recipe:
            continue
        uid = "a" + str(len(cards))
        size = f'width:{recipe["canvas"]["w"] * args.scale}px;height:{recipe["canvas"]["h"] * args.scale}px'
        cards.append(f'<figure><div style="{size}">{svg_of(recipe, uid).replace("<svg ", f"<svg style=\'{size}\' ", 1)}</div><figcaption>{html.escape(rel)}</figcaption></figure>')
    page = ('<!doctype html><meta charset="utf-8"><title>Art sheet</title>'
            '<style>body{background:#2b3a2b;color:#eee;font:12px sans-serif;display:flex;flex-wrap:wrap;gap:16px;padding:16px}'
            'figure{margin:0;text-align:center}figcaption{margin-top:4px}</style>' + "".join(cards))
    Path(args.out).write_text(page, encoding="utf-8")
    print(f"{len(cards)} pictures in {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
