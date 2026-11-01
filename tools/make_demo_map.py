#!/usr/bin/env python3
"""Generate data/base/maps/demo.tmj, the M2 test map (Tiled TMJ format, docs/spec/02).

Deterministic: variation comes from the reference coordinate hash, never from random().
Usage: python tools/make_demo_map.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reference.numerics import hash64  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "base" / "maps" / "demo.tmj"

WIDTH, HEIGHT, TILE = 40, 30, 32
GRASS_A, GRASS_B, PATH, WATER, WALL = 1, 2, 3, 4, 5
SEED = 0xA37E5
SPAWN = (5.5, 15.5)


def build_ground() -> list[list[int]]:
    grid = [[GRASS_A] * WIDTH for _ in range(HEIGHT)]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if (hash64(SEED, x, y) >> 40) & 3 == 0:
                grid[y][x] = GRASS_B
    for x in range(3, 37):                      # main road, two tiles wide
        grid[15][x] = PATH
        grid[16][x] = PATH
    for y in range(3, 15):                      # branch to the north
        grid[y][20] = PATH
    for y in range(6, 13):                      # pond with cut corners
        for x in range(26, 34):
            corner = (x in (26, 33)) and (y in (6, 12))
            if not corner:
                grid[y][x] = WATER
    for x in range(WIDTH):                      # border wall
        grid[0][x] = WALL
        grid[HEIGHT - 1][x] = WALL
    for y in range(HEIGHT):
        grid[y][0] = WALL
        grid[y][WIDTH - 1] = WALL
    for x in range(12, 18):                     # a small ruin with a gap in the south wall
        grid[20][x] = WALL
        if x != 14:
            grid[23][x] = WALL
    for y in range(20, 24):
        grid[y][12] = WALL
        grid[y][17] = WALL
    return grid


def near_walkway_or_water(grid: list[list[int]], x: int, y: int) -> bool:
    for yy in range(max(0, y - 1), min(HEIGHT, y + 2)):
        for xx in range(max(0, x - 1), min(WIDTH, x + 2)):
            if grid[yy][xx] in (PATH, WATER, WALL):
                return True
    return False


def build_objects(grid: list[list[int]]) -> list[dict]:
    objects: list[dict] = []
    next_id = 1

    def add(obj: dict) -> None:
        nonlocal next_id
        objects.append({"id": next_id, "name": "", "width": 0, "height": 0, **obj})
        next_id += 1

    add({"name": "player_spawn", "type": "spawn_player", "point": True,
         "x": SPAWN[0] * TILE, "y": SPAWN[1] * TILE})
    for y in range(2, HEIGHT - 2):
        for x in range(2, WIDTH - 2):
            if near_walkway_or_water(grid, x, y) or abs(x + 0.5 - SPAWN[0]) + abs(y + 0.5 - SPAWN[1]) < 4:
                continue
            if abs(y - 15.5) < 3:
                continue
            roll = (hash64(SEED + 1, x, y) >> 32) % 1000
            if roll < 70:
                kind, radius = "base:art/prop/tree_oak", 0.3
            elif roll < 95:
                kind, radius = "base:art/prop/rock", 0.35
            else:
                continue
            add({"type": "prop", "point": True, "x": (x + 0.5) * TILE, "y": (y + 0.9) * TILE,
                 "properties": [{"name": "art", "type": "string", "value": kind},
                                {"name": "radius", "type": "float", "value": radius}]})
    return objects


def build_map() -> dict:
    grid = build_ground()
    objects = build_objects(grid)
    return {
        "type": "map", "version": "1.10", "tiledversion": "1.10.2", "orientation": "orthogonal",
        "renderorder": "right-down", "infinite": False, "width": WIDTH, "height": HEIGHT,
        "tilewidth": TILE, "tileheight": TILE, "nextlayerid": 3, "nextobjectid": len(objects) + 1,
        "properties": [{"name": "tileset", "type": "string", "value": "base:tileset/overworld"}],
        "layers": [
            {"id": 1, "name": "ground", "type": "tilelayer", "x": 0, "y": 0, "width": WIDTH, "height": HEIGHT,
             "data": [gid for row in grid for gid in row]},
            {"id": 2, "name": "objects", "type": "objectgroup", "x": 0, "y": 0, "objects": objects},
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = json.dumps(build_map(), indent=1) + "\n"
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print(f"OUT OF DATE: {OUT.relative_to(ROOT)} (run python tools/make_demo_map.py)")
            return 1
        print("OK: demo map is up to date")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
