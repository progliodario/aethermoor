#!/usr/bin/env python3
"""Builds the settlement stamps of the base pack (data/base/stamps/*.json) from small building templates.

A stamp is a picture of a hamlet, village or town made of characters; see docs/spec/09-worldgen.md ("Settlements").
Run it after changing a template, then run tools/gen_conformance.py (the vectors depend on the stamps).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "base" / "stamps"

LEGEND = {
    "#": {"tile": 5},  # stone wall (solid)
    "_": {"tile": 13},  # plank floor
    "=": {"tile": 11},  # dirt road
    "c": {"tile": 14},  # cobblestones
    "w": {"tile": 14, "prop": "base:art/prop/well", "radius_x100": 40},
    "l": {"tile": 14, "prop": "base:art/prop/lamp", "radius_x100": 15},
    "b": {"tile": 13, "prop": "base:art/prop/barrel", "radius_x100": 25},
    "t": {"prop": "base:art/prop/tree_oak", "radius_x100": 30},
    "x": {"tile": 14, "spawner": "base:enemy/slime_blue"},  # dungeon spawners
    "W": {"tile": 14, "spawner": "base:enemy/wolf_grey"},
    "B": {"tile": 14, "spawner": "base:enemy/barrow_warden"},
    "s": {"tile": 14, "spawner": "base:enemy/slime_green"},
    "K": {"tile": 14, "spawner": "base:enemy/gel_king"},
    "m": {"tile": 14, "spawner": "base:enemy/slime_slate"},
    "d": {"tile": 14, "spawner": "base:enemy/wolf_shade"},
    "F": {"tile": 14, "spawner": "base:enemy/iron_foreman"},
    "f": {"tile": 14, "spawner": "base:enemy/wolf_frost"},
    "i": {"tile": 14, "spawner": "base:enemy/slime_tide"},
    "R": {"tile": 14, "spawner": "base:enemy/rime_revenant"},
    "Q": {"tile": 14, "spawner": "base:enemy/tide_regent"},
    "g": {"tile": 14, "spawner": "base:enemy/slime_glow"},
    "a": {"tile": 14, "spawner": "base:enemy/slime_sand"},
    "e": {"tile": 14, "spawner": "base:enemy/slime_ember"},
    "A": {"tile": 14, "spawner": "base:enemy/moonshade_alpha"},
    "Y": {"tile": 14, "spawner": "base:enemy/sand_sentinel"},
    "J": {"tile": 14, "spawner": "base:enemy/astral_curator"},
    "N": {"tile": 14, "spawner": "base:enemy/cinder_colossus"},
    "o": {"prop": "base:art/prop/rock", "radius_x100": 30},
    "T": {"tile": 14, "prop": "base:art/prop/threshold_stone", "radius_x100": 35},  # Threshold Stone (fast travel)
    "V": {"tile": 13, "npc": "villager"},
    "G": {"tile": 13, "npc": "guild_clerk"},
    "S": {"tile": 13, "npc": "shopkeeper"},
    "I": {"tile": 13, "npc": "innkeeper"},
    "E": {"tile": 14, "npc": "elder"},
}


class Canvas:
    def __init__(self, w: int, h: int) -> None:
        self.w, self.h = w, h
        self.cells = [["."] * w for _ in range(h)]

    def put(self, x: int, y: int, ch: str) -> None:
        assert 0 <= x < self.w and 0 <= y < self.h, (x, y, ch)
        self.cells[y][x] = ch

    def rect(self, x: int, y: int, w: int, h: int, ch: str) -> None:
        for j in range(y, y + h):
            for i in range(x, x + w):
                self.put(i, j, ch)

    def house(self, x: int, y: int, w: int, h: int, inside: dict[tuple[int, int], str], door: int | None = None) -> None:
        """A walled room with plank floor; the door is a floor tile in the bottom wall (column `door`, default the middle)."""
        self.rect(x, y, w, h, "#")
        self.rect(x + 1, y + 1, w - 2, h - 2, "_")
        self.put(x + (w // 2 if door is None else door), y + h - 1, "_")
        for (dx, dy), ch in inside.items():
            self.put(x + dx, y + dy, ch)

    def hline(self, x0: int, x1: int, y: int, ch: str) -> None:
        for i in range(x0, x1 + 1):
            self.put(i, y, ch)

    def vline(self, x: int, y0: int, y1: int, ch: str) -> None:
        for j in range(y0, y1 + 1):
            self.put(x, j, ch)

    def plaza(self, cx: int, cy: int, radius: int) -> None:
        for j in range(cy - radius, cy + radius + 1):
            for i in range(cx - radius, cx + radius + 1):
                self.put(i, j, "c")
        self.put(cx, cy, "w")

    def rows(self) -> list[str]:
        return ["".join(row) for row in self.cells]


def stamp(stamp_id: str, canvas: Canvas, anchor: tuple[int, int], spots: list[tuple[int, int]]) -> dict:
    used = {ch for row in canvas.rows() for ch in row if ch != "."}
    return {
        "$schema": "../../../schemas/stamp.schema.json",
        "id": stamp_id,
        "w": canvas.w,
        "h": canvas.h,
        "anchor": list(anchor),
        "rows": canvas.rows(),
        "legend": {ch: LEGEND[ch] for ch in sorted(used)},
        "spots": [list(spot) for spot in spots],  # where the people gather in the evening (plaza tiles)
    }


def hamlet() -> dict:
    c = Canvas(11, 9)
    c.house(3, 1, 5, 4, {(1, 1): "b", (2, 1): "V"})
    c.vline(5, 5, 8, "=")
    c.hline(3, 7, 6, "c")
    c.put(5, 6, "w")
    c.put(7, 6, "T")
    for x, y in ((1, 1), (9, 2), (1, 7), (9, 7)):
        c.put(x, y, "t")
    return stamp("base:stamp/hamlet", c, (5, 4), [(4, 6), (6, 6)])


def village() -> dict:
    c = Canvas(21, 15)
    c.plaza(10, 7, 2)
    c.put(8, 5, "l")
    c.put(12, 5, "l")
    c.put(8, 9, "l")
    c.put(12, 9, "l")
    c.put(10, 8, "E")
    c.hline(0, 20, 7, "=")
    c.vline(10, 0, 14, "=")
    for x, y in ((8, 7), (9, 7), (11, 7), (12, 7)):
        c.put(x, y, "c")
    for y in (5, 6, 8, 9):
        c.put(10, y, "c")
    c.put(10, 7, "w")
    c.put(10, 8, "E")
    c.put(12, 6, "T")
    c.house(1, 1, 6, 4, {(1, 1): "b", (3, 1): "V"})
    c.house(13, 1, 7, 5, {(1, 1): "b", (2, 1): "b", (5, 2): "S"}, door=3)
    c.house(1, 9, 6, 4, {(2, 1): "V"})
    c.house(14, 10, 6, 4, {(1, 1): "b", (3, 2): "V"})
    for x, y in ((8, 1), (0, 13), (9, 13), (20, 8)):
        c.put(x, y, "t")
    return stamp("base:stamp/village", c, (10, 7), [(9, 6), (11, 6), (9, 8), (11, 8)])


def town() -> dict:
    c = Canvas(31, 25)
    # Walls with four gates, crossing roads and a plaza in the middle.
    c.rect(2, 2, 27, 21, "#")
    c.rect(3, 3, 25, 19, ".")
    for gate in ((15, 2), (15, 22), (2, 12), (28, 12)):
        c.put(gate[0], gate[1], "=")
    c.vline(15, 0, 24, "=")
    c.hline(0, 30, 12, "=")
    c.plaza(15, 12, 3)
    for x, y in ((12, 9), (18, 9), (12, 15), (18, 15)):
        c.put(x, y, "l")
    c.put(15, 13, "E")
    c.put(18, 10, "T")
    # Guild hall (north-west), shop (north-east), inn (south-west) and houses.
    c.house(4, 4, 9, 5, {(1, 1): "b", (2, 1): "b", (6, 2): "G", (7, 1): "b"}, door=4)
    c.house(18, 4, 8, 5, {(1, 1): "b", (2, 1): "b", (5, 2): "S"}, door=4)
    c.house(4, 16, 9, 5, {(1, 1): "b", (6, 2): "I"}, door=4)
    c.house(19, 16, 6, 4, {(2, 1): "V"}, door=3)
    c.house(4, 10, 5, 4, {(2, 1): "V"}, door=2)
    c.house(22, 10, 5, 4, {(2, 1): "V"}, door=2)
    for x, y in ((0, 0), (30, 0), (0, 24), (30, 24), (6, 0), (24, 24)):
        c.put(x, y, "t")
    return stamp("base:stamp/town", c, (15, 12), [(13, 10), (14, 10), (16, 10), (13, 14), (17, 14), (15, 14)])


def barrow() -> dict:
    """The dungeon of Verdalis: a walled barrow with a corridor, two side rooms, a north hall and a boss (spec 09, "Landmarks")."""
    c = Canvas(33, 26)
    c.rect(1, 1, 31, 23, "#")
    c.rect(2, 2, 29, 21, "c")
    c.hline(2, 30, 11, "#")
    c.vline(14, 12, 22, "#")
    c.vline(18, 12, 22, "#")
    c.put(16, 11, "c")  # the door of the north hall
    c.put(14, 17, "c")  # the doors of the side rooms
    c.put(18, 17, "c")
    c.put(16, 23, "c")  # the entrance
    c.put(16, 24, "c")
    c.put(16, 25, "c")
    for x, y in ((15, 22), (17, 22), (3, 3), (29, 3), (3, 12), (29, 12)):
        c.put(x, y, "l")
    for x, y in ((5, 14), (10, 14), (7, 20)):
        c.put(x, y, "x")
    for x, y in ((11, 20), (3, 16)):
        c.put(x, y, "W")
    for x, y in ((22, 14), (27, 14), (24, 20)):
        c.put(x, y, "W")
    c.put(28, 20, "x")
    for x, y in ((6, 5), (26, 5)):
        c.put(x, y, "W")
    for x, y in ((10, 8), (22, 8)):
        c.put(x, y, "x")
    c.put(16, 4, "B")
    c.put(13, 24, "T")
    return stamp("base:stamp/barrow", c, (16, 24), [])


def cellar() -> dict:
    """The second dungeon of Verdalis: a flooded cellar of slimes with the Gel King in its north room (spec 09, "Landmarks")."""
    c = Canvas(29, 24)
    c.rect(1, 1, 27, 21, "#")
    c.rect(2, 2, 25, 19, "c")
    c.hline(2, 26, 9, "#")
    c.put(14, 9, "c")  # the door of the north room
    for y in (21, 22, 23):  # the entrance and the path to it
        c.put(14, y, "c")
    for x, y in ((13, 20), (15, 20), (3, 3), (25, 3), (3, 10), (25, 10)):
        c.put(x, y, "l")
    for x, y in ((6, 5), (22, 5)):
        c.put(x, y, "x")
    c.put(14, 4, "K")
    for x, y in ((5, 13), (9, 17), (19, 13), (23, 17)):
        c.put(x, y, "s")
    for x, y in ((7, 15), (21, 15), (14, 12)):
        c.put(x, y, "x")
    c.put(11, 22, "T")
    return stamp("base:stamp/cellar", c, (14, 22), [])


def mine() -> dict:
    """The first dungeon of Ironspine: a sealed mine of three galleries and the Ironbound Foreman in its north hall (spec 09, "Landmarks")."""
    c = Canvas(37, 30)
    c.rect(1, 1, 35, 27, "#")
    c.rect(2, 2, 33, 25, "c")
    c.hline(2, 34, 9, "#")
    c.put(18, 9, "c")  # the door of the north hall
    for x in (12, 24):  # the pillars that divide the galleries, with a passage in the middle
        c.vline(x, 10, 14, "#")
        c.vline(x, 17, 25, "#")
    for y in (26, 27, 28, 29):  # the entrance and the path to it
        c.put(18, y, "c")
    for x, y in ((3, 3), (33, 3), (3, 11), (33, 11), (17, 25), (19, 25)):
        c.put(x, y, "l")
    c.put(18, 4, "F")
    for x, y in ((8, 5), (28, 5)):
        c.put(x, y, "d")
    for x, y in ((7, 12), (7, 22), (18, 12), (18, 23), (29, 12), (29, 22)):
        c.put(x, y, "m")
    for x, y in ((4, 17), (32, 17)):
        c.put(x, y, "d")
    for x, y in ((18, 17), (8, 17), (28, 17)):
        c.put(x, y, "W")
    c.put(15, 28, "T")
    return stamp("base:stamp/mine", c, (18, 28), [])


def cavern() -> dict:
    """The dungeon of Frostveil: a frozen cavern of pillars and wolves, the Rime Revenant in its north hall (spec 09, "Landmarks")."""
    c = Canvas(33, 28)
    c.rect(1, 1, 31, 26, "#")
    c.rect(2, 2, 29, 24, "c")
    c.hline(2, 30, 7, "#")
    c.put(16, 7, "c")  # the door of the north hall
    for x, y in ((6, 10), (6, 17), (25, 10), (25, 17), (15, 13), (15, 19)):  # ice pillars
        c.rect(x, y, 2, 2, "#")
    for y in (26, 27):  # the entrance and the path to it
        c.put(16, y, "c")
    for x, y in ((3, 3), (29, 3), (3, 9), (29, 9), (15, 25), (17, 25)):
        c.put(x, y, "l")
    c.put(16, 3, "R")
    for x, y in ((8, 4), (24, 4)):
        c.put(x, y, "f")
    for x, y in ((4, 12), (28, 12), (10, 21), (22, 21), (16, 16), (11, 12), (21, 12)):
        c.put(x, y, "f")
    for x, y in ((4, 20), (28, 20), (16, 23)):
        c.put(x, y, "x")
    c.put(13, 27, "T")
    return stamp("base:stamp/cavern", c, (16, 27), [])


def temple() -> dict:
    """The dungeon of Tidehaven: a drowned temple with a nave, four side chambers and the Tide Regent in its apse (spec 09, "Landmarks")."""
    c = Canvas(35, 31)
    c.rect(1, 1, 33, 28, "#")
    c.rect(2, 2, 31, 26, "c")
    c.hline(13, 21, 8, "#")
    c.put(17, 8, "c")  # the door of the apse
    for x in (12, 22):  # the walls between the nave and the chambers, with a door for each chamber
        c.vline(x, 2, 27, "#")
        for y in (12, 20):
            c.put(x, y, "c")
    c.hline(2, 11, 16, "#")
    c.hline(23, 32, 16, "#")
    for y in (28, 29, 30):  # the entrance and the path to it
        c.put(17, y, "c")
    for x, y in ((3, 3), (31, 3), (14, 9), (20, 9), (3, 17), (31, 17), (16, 27), (18, 27)):
        c.put(x, y, "l")
    c.put(17, 4, "Q")
    for x, y in ((14, 4), (20, 4)):
        c.put(x, y, "i")
    for x, y in ((6, 12), (6, 22), (28, 12), (28, 22), (8, 4), (26, 4)):
        c.put(x, y, "i")
    for x, y in ((17, 14), (17, 20), (15, 24), (19, 24)):
        c.put(x, y, "x")
    c.put(14, 29, "T")
    return stamp("base:stamp/temple", c, (17, 29), [])


def hollow() -> dict:
    """The dungeon of Whisperwood: a glade inside a ring of trees, shade wolves and the Moonshade Alpha in its north clearing (spec 09, "Landmarks")."""
    c = Canvas(35, 31)
    c.rect(1, 1, 33, 29, "t")  # the ring of trees, two deep
    c.rect(3, 3, 29, 25, ".")
    c.hline(8, 26, 9, "t")  # the grove of the Alpha, with a gap for the path
    c.put(17, 9, "=")
    c.vline(17, 3, 27, "=")
    for y in (28, 29, 30):  # the way in
        for x in (16, 17, 18):
            c.put(x, y, "=")
    for x, y in ((9, 14), (10, 14), (24, 14), (25, 14), (12, 19), (22, 19), (8, 23), (26, 23)):
        c.put(x, y, "t")
    for x, y in ((14, 12), (20, 12), (14, 22), (20, 22), (5, 18), (29, 18)):
        c.put(x, y, "o")
    c.put(17, 5, "A")
    for x, y in ((12, 5), (22, 5)):
        c.put(x, y, "d")
    for x, y in ((6, 12), (28, 12), (10, 16), (24, 16), (6, 20), (28, 20), (13, 24), (21, 24)):
        c.put(x, y, "d")
    for x, y in ((12, 11), (22, 11), (8, 26), (26, 26)):
        c.put(x, y, "W")
    for x, y in ((17, 16), (17, 22)):
        c.put(x, y, "s")
    for x, y in ((16, 30), (18, 30)):
        c.put(x, y, "l")
    c.put(14, 30, "T")
    return stamp("base:stamp/hollow", c, (17, 30), [])


def ziggurat() -> dict:
    """The dungeon of Sunscar: three rings of walls, each with its gate on the opposite side, and the Sand Sentinel at the center (spec 09, "Landmarks")."""
    c = Canvas(41, 41)
    c.rect(1, 1, 39, 38, "#")
    c.rect(2, 2, 37, 36, "c")
    c.rect(8, 8, 25, 24, "#")
    c.rect(9, 9, 23, 22, "c")
    c.put(20, 8, "c")  # the gate of the second ring, opposite the entrance
    c.rect(14, 14, 13, 12, "#")
    c.rect(15, 15, 11, 10, "c")
    c.put(20, 25, "c")  # the gate of the inner sanctum
    for y in (38, 39, 40):  # the entrance and the path to it
        for x in (19, 20, 21):
            c.put(x, y, "c")
    for x, y in ((3, 3), (37, 3), (3, 36), (37, 36), (10, 10), (30, 10), (10, 29), (30, 29)):
        c.put(x, y, "l")
    c.put(20, 19, "Y")
    for x, y in ((17, 17), (23, 17), (17, 22), (23, 22)):
        c.put(x, y, "a")
    for x, y in ((5, 5), (35, 5), (5, 35), (35, 35), (5, 20), (35, 20), (12, 5), (28, 5), (12, 35), (28, 35)):
        c.put(x, y, "a")
    for x, y in ((11, 20), (29, 20), (20, 11), (20, 28), (12, 12), (28, 28)):
        c.put(x, y, "W")
    for x, y in ((11, 12), (29, 12)):
        c.put(x, y, "s")
    c.put(16, 40, "T")
    return stamp("base:stamp/ziggurat", c, (20, 40), [])


def observatory() -> dict:
    """The dungeon of Lumeria: a domed hall with a library on each side and the Astral Curator in its north chamber (spec 09, "Landmarks")."""
    c = Canvas(39, 39)
    c.rect(1, 1, 37, 36, "#")
    c.rect(10, 10, 19, 19, "c")  # the domed hall
    for i in range(4):  # chamfered corners
        for j in range(4 - i):
            for dx, dy in ((i, j), (18 - i, j), (i, 18 - j), (18 - i, 18 - j)):
                c.put(10 + dx, 10 + dy, "#")
    c.rect(12, 2, 15, 7, "c")  # the chamber of the Curator
    c.rect(18, 9, 3, 1, "c")
    c.rect(2, 14, 7, 11, "c")  # the west library
    c.put(9, 19, "c")
    c.rect(30, 14, 7, 11, "c")  # the east library
    c.put(29, 19, "c")
    c.rect(18, 29, 3, 9, "c")  # the south arm and the way in
    for y in (37, 38):
        for x in (18, 19, 20):
            c.put(x, y, "c")
    for x, y in ((13, 13), (25, 13), (13, 25), (25, 25), (13, 3), (25, 3), (3, 15), (35, 15), (3, 23), (35, 23)):
        c.put(x, y, "l")
    c.put(19, 4, "J")
    for x, y in ((14, 6), (24, 6)):
        c.put(x, y, "g")
    for x, y in ((14, 19), (24, 19), (19, 14), (19, 24)):
        c.put(x, y, "g")
    for x, y in ((4, 17), (6, 22), (34, 17), (32, 22)):
        c.put(x, y, "g")
    for x, y in ((5, 19), (33, 19)):
        c.put(x, y, "x")
    for x, y in ((15, 15), (23, 15), (15, 23), (23, 23)):
        c.put(x, y, "W")
    c.put(16, 38, "T")
    return stamp("base:stamp/observatory", c, (19, 38), [])


def citadel() -> dict:
    """The dungeon of the Ashen Wastes: a burned citadel with four bastions, a courtyard and the Cinder Colossus in the keep (spec 09, "Landmarks")."""
    c = Canvas(47, 40)
    c.rect(1, 1, 45, 34, "#")
    c.rect(2, 2, 43, 32, "c")
    for x, y, dx in ((2, 2, 6), (36, 2, 40), (2, 24, 6), (36, 24, 40)):  # the four bastions, each with a door to the courtyard
        c.rect(x, y, 9, 9, "#")
        c.rect(x + 1, y + 1, 7, 7, "c")
        c.put(dx, y + (8 if y == 2 else 0), "c")
    c.rect(14, 2, 19, 12, "#")  # the keep
    c.rect(15, 3, 17, 10, "c")
    c.put(23, 13, "c")
    for x, y in ((14, 18), (30, 18), (14, 26), (30, 26)):  # broken columns
        c.rect(x, y, 2, 2, "#")
    for y in (34, 35, 36, 37, 38, 39):  # the gate and the road to it
        for x in (22, 23, 24):
            c.put(x, y, "c")
    for x, y in ((12, 14), (34, 14), (21, 32), (25, 32), (16, 4), (30, 4)):
        c.put(x, y, "l")
    c.put(23, 6, "N")
    for x, y in ((19, 5), (27, 5), (19, 10), (27, 10)):
        c.put(x, y, "e")
    for x, y in ((6, 6), (40, 6), (6, 28), (40, 28)):
        c.put(x, y, "e")
    for x, y in ((13, 16), (33, 16), (23, 20), (13, 22), (33, 22), (18, 29), (28, 29), (23, 15)):
        c.put(x, y, "e")
    for x, y in ((20, 17), (26, 17), (18, 23), (28, 23)):
        c.put(x, y, "W")
    c.put(19, 38, "T")
    return stamp("base:stamp/citadel", c, (23, 39), [])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for build in (hamlet, village, town, barrow, cellar, mine, cavern, temple, hollow, ziggurat, observatory, citadel):
        data = build()
        name = data["id"].split("/")[-1]
        (OUT / f"{name}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {name}: {data['w']}x{data['h']}")
        for row in data["rows"]:
            print("  " + row)


if __name__ == "__main__":
    main()
