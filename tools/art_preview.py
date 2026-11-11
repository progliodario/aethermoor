#!/usr/bin/env python3
"""Draws art recipes (data/base/art/**) to PNG pictures and an HTML sheet, to look at them without the game.

    python tools/art_preview.py [--out sheet.html] [--scale 3] [pattern ...]
    python tools/art_preview.py --figures            every person assembled (front and back)
    python tools/art_preview.py --scene              a piece of world: terrain, props, people, creatures

The patterns match the path of the recipe (`creatures/wolf` shows every recipe whose path contains it); no pattern shows
all of them. The pictures are drawn by the reference rasterizer (`tools/reference/raster.py`), the same algorithm of the
game (docs/spec/13-vector-art.md), so what is here is what the clients draw. `--scale` is in pixels per art unit (the game
uses 2 to 4). The PNG files go to a folder next to the sheet.
"""
from __future__ import annotations

import argparse
import html
import json
import struct
import sys
import zlib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "data" / "base" / "art"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from reference import pose, raster  # noqa: E402


def write_png(path: Path, w: int, h: int, rgba: bytes) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    rows = b"".join(b"\x00" + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b""))


class Image:
    """A premultiplied RGBA picture to compose scenes on."""

    def __init__(self, w: int, h: int, color=(0.0, 0.0, 0.0, 0.0)):
        self.w, self.h = w, h
        r, g, b, a = color
        self.px = [r * a, g * a, b * a, a] * (w * h)

    def blit(self, sprite: tuple[int, int, bytearray], x: int, y: int, mirror: bool = False) -> None:
        sw, sh, data = sprite
        for sy in range(sh):
            dy = y + sy
            if dy < 0 or dy >= self.h:
                continue
            for sx in range(sw):
                dx = x + (sw - 1 - sx if mirror else sx)
                if dx < 0 or dx >= self.w:
                    continue
                i = (sy * sw + sx) * 4
                a = data[i + 3] / 255
                if a <= 0:
                    continue
                o = (dy * self.w + dx) * 4
                inv = 1 - a
                self.px[o] = data[i] / 255 * a + self.px[o] * inv
                self.px[o + 1] = data[i + 1] / 255 * a + self.px[o + 1] * inv
                self.px[o + 2] = data[i + 2] / 255 * a + self.px[o + 2] * inv
                self.px[o + 3] = a + self.px[o + 3] * inv

    def blit_rotated(self, sprite: tuple[int, int, bytearray], pivot: tuple[float, float], at: tuple[float, float], deg: float, mirror: bool) -> None:
        """Draws a sprite with its pivot at `at`, turned by deg (nearest sample: a preview, not the game's filter)."""
        import math
        sw, sh, data = sprite
        if abs(deg) < 0.01:
            px = (sw - pivot[0]) if mirror else pivot[0]
            self.blit(sprite, round(at[0] - px), round(at[1] - pivot[1]), mirror)
            return
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        reach = int(math.hypot(sw, sh)) + 2
        for dy in range(int(at[1]) - reach, int(at[1]) + reach):
            if dy < 0 or dy >= self.h:
                continue
            for dx in range(int(at[0]) - reach, int(at[0]) + reach):
                if dx < 0 or dx >= self.w:
                    continue
                rx, ry = dx + 0.5 - at[0], dy + 0.5 - at[1]
                lx, ly = rx * c + ry * s, -rx * s + ry * c
                if mirror:
                    lx = -lx
                sx, sy = int(math.floor(lx + pivot[0])), int(math.floor(ly + pivot[1]))
                if sx < 0 or sy < 0 or sx >= sw or sy >= sh:
                    continue
                i = (sy * sw + sx) * 4
                a = data[i + 3] / 255
                if a <= 0:
                    continue
                o = (dy * self.w + dx) * 4
                inv = 1 - a
                self.px[o] = data[i] / 255 * a + self.px[o] * inv
                self.px[o + 1] = data[i + 1] / 255 * a + self.px[o + 1] * inv
                self.px[o + 2] = data[i + 2] / 255 * a + self.px[o + 2] * inv
                self.px[o + 3] = a + self.px[o + 3] * inv

    def save(self, path: Path) -> None:
        out = bytearray(self.w * self.h * 4)
        for p in range(self.w * self.h):
            a = self.px[p * 4 + 3]
            if a <= 0:
                continue
            for c in range(3):
                out[p * 4 + c] = max(0, min(255, round(self.px[p * 4 + c] / a * 255)))
            out[p * 4 + 3] = max(0, min(255, round(a * 255)))
        write_png(path, self.w, self.h, out)


def load(recipe_id: str) -> dict:
    """The recipe of an ID such as base:art/prop/rock (the folders are plural, the IDs singular)."""
    _, rest = recipe_id.split(":", 1)
    parts = rest.split("/")[1:]
    folder = {"tile": "tiles", "prop": "props", "creature": "creatures", "char": "characters"}[parts[0]]
    return json.loads((ART / folder / "/".join(parts[1:])).with_suffix(".json").read_text(encoding="utf-8"))


_cache: dict = {}


def baked(recipe_id: str, scale: float, variant: str | None = None):
    key = (recipe_id, scale, variant)
    if key not in _cache:
        recipe = load(recipe_id)
        _cache[key] = (recipe, raster.rasterize(recipe, scale, variant))
    return _cache[key]


def draw_figure(image: Image, feet: tuple[float, float], scale: float, variant: str | None, tick: float = 0.0,
                clip_name: str = "humanoid_idle", mirror: bool = False, back: bool = False) -> None:
    rig = json.loads((ART / "rigs" / "humanoid.json").read_text(encoding="utf-8"))
    clip = json.loads((ART / "clips" / f"{clip_name}.json").read_text(encoding="utf-8"))
    posed = pose.evaluate_pose(rig, clip, tick, mirror)
    parts = {p["id"]: p for p in rig["parts"]}
    order = sorted(posed, key=lambda q: parts[q["part"]].get("z_back" if back else "z", parts[q["part"]]["z"]))
    for item in order:
        part = parts[item["part"]]
        art = part.get("art_back", part["art"]) if back else part["art"]
        recipe, sprite = baked(art, scale, variant)
        ox, oy = recipe["canvas"]["origin"]
        image.blit_rotated(sprite, (ox * scale, oy * scale), (feet[0] + item["x"] * scale, feet[1] + item["y"] * scale), item["rot"], mirror)


def _render_one(job: tuple[str, float, str]) -> tuple[int, int, bytes]:
    path, scale, out = job
    recipe = json.loads(Path(path).read_text(encoding="utf-8"))
    w, h, data = raster.rasterize(recipe, scale)
    write_png(Path(out), w, h, data)
    return w, h, bytes(data)


def pack(sprites: list[tuple[int, int, bytes]], width: int, gap: int = 12) -> Image:
    """One picture with all the sprites in rows, on the green of a meadow."""
    x = y = gap
    row_h = 0
    places = []
    for w, h, _ in sprites:
        if x + w + gap > width and x > gap:
            x, y, row_h = gap, y + row_h + gap, 0
        places.append((x, y))
        x += w + gap
        row_h = max(row_h, h)
    image = Image(width, y + row_h + gap, (0.36, 0.56, 0.34, 1.0))
    for (w, h, data), (px, py) in zip(sprites, places):
        image.blit((w, h, bytearray(data)), px, py)
    return image


def _figure_one(job: tuple[str | None, float, str]) -> str:
    variant, scale, out = job
    image = Image(int(150 * scale), int(84 * scale), (0.32, 0.45, 0.30, 1.0))
    draw_figure(image, (28 * scale, 76 * scale), scale, variant)
    draw_figure(image, (75 * scale, 76 * scale), scale, variant, tick=6, clip_name="humanoid_walk", mirror=True)
    draw_figure(image, (120 * scale, 76 * scale), scale, variant, back=True)
    image.save(Path(out))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("patterns", nargs="*")
    parser.add_argument("--out", default="art_sheet.html")
    parser.add_argument("--scale", type=float, default=3.0)
    parser.add_argument("--width", type=int, default=1100, help="the width of the one picture with everything (sheet.png)")
    parser.add_argument("--figures", action="store_true", help="draw every person assembled")
    parser.add_argument("--scene", action="store_true", help="draw a piece of world (tools/art_scene.py)")
    args = parser.parse_args()
    out = Path(args.out)
    files = out.with_name(out.stem + "_files")
    files.mkdir(parents=True, exist_ok=True)
    cards = []
    if args.scene:
        import art_scene
        target = files / "scene.png"
        art_scene.draw(args.scale).save(target)
        cards.append(f'<figure><img src="{files.name}/scene.png"><figcaption>scene</figcaption></figure>')
    elif args.figures:
        head = json.loads((ART / "characters" / "ren" / "head.json").read_text(encoding="utf-8"))
        names = [None, *head.get("variants", {})]
        if args.patterns:
            names = [n for n in names if (n or "ren") in args.patterns]
        jobs = [(n, args.scale, str(files / f"figure_{n or 'ren'}.png")) for n in names]
        with ProcessPoolExecutor() as pool:
            for (n, _, _), _ in zip(jobs, pool.map(_figure_one, jobs)):
                cards.append(f'<figure><img src="{files.name}/figure_{n or "ren"}.png"><figcaption>{n or "ren (base)"}</figcaption></figure>')
    else:
        jobs = []
        for path in sorted(ART.rglob("*.json")):
            rel = path.relative_to(ART).as_posix()
            if args.patterns and not any(p in rel for p in args.patterns):
                continue
            if "layers" not in json.loads(path.read_text(encoding="utf-8")):
                continue
            jobs.append((str(path), args.scale, str(files / (rel.replace("/", "_")[:-5] + ".png"))))
        sprites = []
        with ProcessPoolExecutor() as pool:
            for (path, _, target), sprite in zip(jobs, pool.map(_render_one, jobs)):
                sprites.append(sprite)
                rel = Path(path).relative_to(ART).as_posix()
                cards.append(f'<figure><img src="{files.name}/{Path(target).name}"><figcaption>{html.escape(rel)}</figcaption></figure>')
        if sprites:
            pack(sprites, args.width).save(out.with_suffix(".png"))
    page = ('<!doctype html><meta charset="utf-8"><title>Art sheet</title>'
            '<style>body{background:#3d5a3a;color:#eee;font:12px sans-serif;display:flex;flex-wrap:wrap;gap:16px;padding:16px}'
            'figure{margin:0;text-align:center}figcaption{margin-top:4px}</style>' + "".join(cards))
    out.write_text(page, encoding="utf-8")
    print(f"{len(cards)} pictures in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
