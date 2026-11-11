#!/usr/bin/env python3
"""Builds the settlement stamps of the base pack (data/base/stamps/*.json) from small building templates.

A stamp is a picture of a hamlet, village or town made of characters; see docs/spec/09-worldgen.md ("Settlements").
Run it after changing a template, then run tools/gen_conformance.py (the vectors depend on the stamps).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "base" / "stamps"

LEGEND = {
    "#": {"tile": 5},  # stone wall (solid)
    ":": {"tile": 35},  # timber-framed wall of a house (solid)
    ";": {"tile": 37},  # a door: a doorway with a stone threshold
    "'": {"tile": 36},  # a house wall with a window (solid)
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
    "D": {"tile": 14, "spawner": "base:enemy/wolf_dire"},
    "M": {"tile": 14, "spawner": "base:enemy/slime_magma"},
    "Z": {"tile": 14, "spawner": "base:enemy/slime_coral"},
    "P": {"tile": 14, "spawner": "base:enemy/slime_amber"},
    "H": {"tile": 14, "spawner": "base:enemy/slime_ice"},
    "O": {"tile": 14, "spawner": "base:enemy/wolf_storm"},
    "U": {"tile": 14, "spawner": "base:enemy/dire_alpha"},
    "X": {"tile": 14, "spawner": "base:enemy/magma_heart"},
    "C": {"tile": 14, "spawner": "base:enemy/coral_matron"},
    "L": {"tile": 14, "spawner": "base:enemy/amber_queen"},
    "j": {"tile": 14, "spawner": "base:enemy/ice_warden"},
    "k": {"tile": 14, "spawner": "base:enemy/storm_sovereign"},
    "q": {"tile": 14, "spawner": "base:enemy/forge_tyrant"},
    "r": {"tile": 14, "spawner": "base:enemy/drowned_captain"},
    "z": {"tile": 14, "spawner": "base:enemy/frost_sovereign"},
    "y": {"tile": 14, "spawner": "base:enemy/vault_warden"},
    "3": {"tile": 14, "spawner": "base:enemy/slime_mint"},
    "4": {"tile": 14, "spawner": "base:enemy/wolf_tawny"},
    "5": {"tile": 14, "spawner": "base:enemy/slime_moss"},
    "6": {"tile": 14, "spawner": "base:enemy/slime_rust"},
    "7": {"tile": 14, "spawner": "base:enemy/wolf_dune"},
    "8": {"tile": 14, "spawner": "base:enemy/wolf_polar"},
    "9": {"tile": 14, "spawner": "base:enemy/slime_pearl"},
    "%": {"tile": 14, "spawner": "base:enemy/slime_nebula"},
    "&": {"tile": 14, "spawner": "base:enemy/slime_char"},
    "n": {"tile": 14, "spawner": "base:enemy/mint_matron"},
    "p": {"tile": 14, "spawner": "base:enemy/moss_elder"},
    "h": {"tile": 14, "spawner": "base:enemy/rust_baron"},
    "u": {"tile": 14, "spawner": "base:enemy/dune_mother"},
    "v": {"tile": 14, "spawner": "base:enemy/polar_king"},
    "0": {"tile": 14, "spawner": "base:enemy/pearl_empress"},
    "1": {"tile": 14, "spawner": "base:enemy/nebula_heart"},
    "2": {"tile": 14, "spawner": "base:enemy/char_tyrant"},
    "T": {"tile": 14, "prop": "base:art/prop/threshold_stone", "radius_x100": 35},  # Threshold Stone (fast travel)
    "*": {"prop": "base:art/prop/tent", "radius_x100": 60},
    "+": {"prop": "base:art/prop/signpost", "radius_x100": 15},
    "~": {"prop": "base:art/prop/crate", "radius_x100": 30},
    ")": {"tile": 14, "prop": "base:art/prop/stall", "radius_x100": 45},
    "(": {"prop": "base:art/prop/haybale", "radius_x100": 30},
    "^": {"prop": "base:art/prop/statue", "radius_x100": 35},
    "@": {"prop": "base:art/prop/banner", "radius_x100": 15},
    "!": {"prop": "base:art/prop/bush", "radius_x100": 30},
    "$": {"prop": "base:art/prop/bones", "radius_x100": 10},
    "?": {"prop": "base:art/prop/campfire", "radius_x100": 30},
    "/": {"tile": 14, "prop": "base:art/prop/anvil", "radius_x100": 35},  # where fine gear is made
    "V": {"tile": 13, "npc": "villager"},
    "G": {"tile": 13, "npc": "guild_clerk"},
    "S": {"tile": 13, "npc": "shopkeeper"},
    "I": {"tile": 13, "npc": "innkeeper"},
    "E": {"tile": 14, "npc": "elder"},
}
# the Echoes, the personal bosses of the protagonists (tools/make_echoes.py): one legend character each
for _who, _entry in __import__("make_echoes").ECHOES.items():
    LEGEND[_entry[0]] = {"tile": 14, "spawner": f"base:enemy/echo_{_who}"}


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
        self.rect(x, y, w, h, ":")
        self.rect(x + 1, y + 1, w - 2, h - 2, "_")
        door_x = x + (w // 2 if door is None else door)
        self.put(door_x, y + h - 1, ";")
        for wx in range(x + 1, x + w - 1, 2):  # a window in the top wall, every other tile
            self.put(wx, y, "'")
        if w >= 5:
            self.put(x, y + h // 2, "'")  # and one in the side
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


def stamp(stamp_id: str, canvas: Canvas, anchor: tuple[int, int], spots: list[tuple[int, int]], open_air: bool = False) -> dict:
    """The stamp document. In an `open_air` stamp (a glade, a ring of trees) the creatures, lamps and props keep the ground of the terrain instead of a cobblestone."""
    if not stamp_id.startswith(("base:stamp/hamlet", "base:stamp/village", "base:stamp/town", "base:stamp/outpost")):
        # the houses of a settlement are timber and plaster; elsewhere the same rooms are built of stone
        canvas.cells = [["#" if ch in ":'" else "_" if ch == ";" else ch for ch in row] for row in canvas.cells]
    used = {ch for row in canvas.rows() for ch in row if ch != "."}
    legend = {ch: LEGEND[ch] for ch in sorted(used)}
    if open_air:
        for ch, entry in legend.items():
            if ch != "T" and "tile" in entry and ("spawner" in entry or "prop" in entry):
                legend[ch] = {key: value for key, value in entry.items() if key != "tile"}
    return {
        "$schema": "../../../schemas/stamp.schema.json",
        "id": stamp_id,
        "w": canvas.w,
        "h": canvas.h,
        "anchor": list(anchor),
        "rows": canvas.rows(),
        "legend": legend,
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
    c.put(17, 8, "?")  # a campfire to cook at (spec 06, "Stations")
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
    c.put(21, 14, "?")  # a campfire to cook at (spec 06, "Stations")
    c.put(9, 14, "/")  # an anvil to make fine gear at
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


def hamlet_b() -> dict:
    """Two small houses on either side of a well."""
    c = Canvas(15, 9)
    c.house(1, 1, 5, 4, {(1, 1): "b", (2, 1): "V"})
    c.house(9, 1, 5, 4, {(1, 1): "b", (3, 1): "V"})
    c.vline(3, 5, 8, "=")
    c.vline(11, 5, 8, "=")
    c.hline(5, 9, 6, "c")
    c.put(7, 6, "w")
    c.put(9, 6, "T")
    for x, y in ((7, 1), (0, 7), (14, 7), (7, 8)):
        c.put(x, y, "t")
    return stamp("base:stamp/hamlet_b", c, (7, 6), [(6, 6), (8, 6)])


def hamlet_c() -> dict:
    """A long barn with a yard and a well."""
    c = Canvas(11, 11)
    c.house(2, 1, 7, 4, {(1, 1): "b", (2, 1): "b", (5, 2): "V"}, door=3)
    c.vline(5, 5, 10, "=")
    c.hline(3, 7, 7, "c")
    c.put(5, 7, "w")
    c.put(7, 7, "T")
    c.put(1, 7, "(")
    c.put(9, 8, "(")
    for x, y in ((1, 9), (9, 9), (1, 6), (9, 5)):
        c.put(x, y, "t")
    return stamp("base:stamp/hamlet_c", c, (5, 7), [(4, 7), (6, 7)])


def village_b() -> dict:
    """Four houses around a square with the well in the middle and the elder beside it."""
    c = Canvas(23, 17)
    c.hline(0, 22, 8, "=")
    c.vline(11, 0, 16, "=")
    c.plaza(11, 8, 2)
    for x, y in ((9, 6), (13, 6), (9, 10), (13, 10)):
        c.put(x, y, "l")
    c.put(11, 9, "E")
    c.put(13, 9, "T")
    c.house(1, 1, 7, 5, {(1, 1): "b", (4, 2): "V"}, door=3)
    c.house(15, 1, 7, 5, {(1, 1): "b", (2, 1): "b", (4, 2): "S"}, door=3)
    c.house(1, 11, 7, 5, {(1, 1): "b", (4, 2): "V"}, door=3)
    c.house(15, 11, 7, 5, {(4, 2): "V"}, door=3)
    for x, y in ((9, 2), (13, 14), (9, 14), (13, 2)):
        c.put(x, y, "t")
    return stamp("base:stamp/village_b", c, (11, 8), [(10, 7), (12, 7), (10, 9), (12, 9)])


def village_c() -> dict:
    """A main street with houses on both sides and a small square."""
    c = Canvas(25, 13)
    c.hline(0, 24, 6, "=")
    c.rect(11, 5, 3, 3, "c")
    c.put(12, 6, "w")
    c.put(12, 7, "E")
    c.put(13, 5, "T")
    c.house(1, 1, 6, 4, {(1, 1): "b", (3, 1): "V"})
    c.house(15, 1, 8, 4, {(1, 1): "b", (2, 1): "b", (5, 2): "S"}, door=4)
    c.house(2, 8, 7, 4, {(2, 1): "V"}, door=3)
    c.house(16, 8, 7, 4, {(3, 2): "V"}, door=3)
    for x, y in ((0, 12), (24, 0), (10, 10), (14, 10)):
        c.put(x, y, "t")
    return stamp("base:stamp/village_c", c, (12, 6), [(11, 6), (13, 6), (11, 7), (13, 7)])


def town_b() -> dict:
    """An open town around a big plaza: no walls, a guild hall, a shop and an inn."""
    c = Canvas(35, 27)
    c.vline(17, 0, 26, "=")
    c.hline(0, 34, 13, "=")
    c.plaza(17, 13, 4)
    for x, y in ((13, 9), (21, 9), (13, 17), (21, 17)):
        c.put(x, y, "l")
    c.put(17, 14, "E")
    c.put(20, 10, "T")
    for x, y in ((14, 12), (20, 12), (14, 16), (20, 16)):
        c.put(x, y, ")")
    c.house(3, 3, 10, 6, {(1, 1): "b", (2, 1): "b", (7, 3): "G"}, door=5)
    c.house(22, 3, 9, 6, {(1, 1): "b", (2, 1): "b", (6, 3): "S"}, door=4)
    c.house(3, 18, 10, 6, {(1, 1): "b", (7, 3): "I"}, door=5)
    c.house(23, 18, 8, 5, {(3, 2): "V"}, door=3)
    c.house(2, 10, 6, 3, {(2, 1): "V"}, door=2)
    c.house(27, 10, 6, 3, {(2, 1): "V"}, door=2)
    for x, y in ((0, 0), (34, 0), (0, 26), (34, 26), (15, 1), (19, 25)):
        c.put(x, y, "t")
    return stamp("base:stamp/town_b", c, (17, 13), [(15, 11), (16, 11), (18, 11), (15, 15), (19, 15), (17, 15)])


def hamlet_d() -> dict:
    """A crossroads with a well at the crossing and a single house."""
    c = Canvas(13, 11)
    c.hline(0, 12, 5, "=")
    c.vline(6, 0, 10, "=")
    c.rect(5, 4, 3, 3, "c")
    c.put(6, 5, "w")
    c.put(7, 4, "T")
    c.house(1, 1, 5, 4, {(1, 1): "b", (2, 1): "V"}, door=2)
    for x, y in ((10, 1), (11, 9), (1, 8), (9, 8)):
        c.put(x, y, "t")
    return stamp("base:stamp/hamlet_d", c, (6, 5), [(5, 5), (7, 6)])


def village_d() -> dict:
    """A long street running north to south with houses on both sides and a square in the middle."""
    c = Canvas(21, 19)
    c.vline(10, 0, 18, "=")
    c.rect(8, 8, 5, 3, "c")
    c.put(10, 9, "w")
    c.put(11, 10, "E")
    c.put(12, 8, "T")
    c.house(1, 1, 7, 5, {(1, 1): "b", (3, 2): "V"}, door=3)
    c.house(1, 12, 7, 5, {(1, 1): "b", (3, 2): "V"}, door=3)
    c.house(13, 1, 7, 5, {(1, 1): "b", (4, 2): "S"}, door=3)
    c.house(13, 12, 7, 5, {(3, 2): "V"}, door=3)
    for x, y in ((9, 1), (11, 17), (0, 8), (20, 9)):
        c.put(x, y, "t")
    return stamp("base:stamp/village_d", c, (10, 9), [(9, 9), (11, 9), (9, 10), (12, 10)])


def town_c() -> dict:
    """A town with its guild hall on the square, the shop and the inn on either side."""
    c = Canvas(37, 25)
    c.vline(18, 0, 24, "=")
    c.hline(0, 36, 16, "=")
    c.plaza(18, 16, 3)
    for x, y in ((15, 13), (21, 13), (15, 19), (21, 19)):
        c.put(x, y, "l")
    c.put(18, 17, "E")
    c.put(20, 14, "T")
    c.house(11, 2, 15, 6, {(2, 1): "b", (3, 1): "b", (11, 3): "G"}, door=7)
    c.house(2, 9, 9, 6, {(1, 1): "b", (2, 1): "b", (6, 3): "S"}, door=4)
    c.house(26, 9, 9, 6, {(1, 1): "b", (6, 3): "I"}, door=4)
    c.house(3, 19, 7, 4, {(3, 1): "V"}, door=3)
    c.house(27, 19, 7, 4, {(3, 1): "V"}, door=3)
    for x, y in ((16, 16), (20, 16)):
        c.put(x, y, ")")
    for x, y in ((0, 0), (36, 0), (0, 24), (36, 24), (13, 11), (23, 11)):
        c.put(x, y, "t")
    return stamp("base:stamp/town_c", c, (18, 16), [(16, 14), (17, 14), (19, 14), (16, 18), (20, 18), (18, 18)])


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
    c.put(15, 27, "^")
    c.put(17, 27, "^")
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
    c.put(16, 29, "@")
    c.put(18, 29, "@")
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
    return stamp("base:stamp/hollow", c, (17, 30), [], open_air=True)


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
    c.put(18, 39, "@")
    c.put(22, 39, "@")
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
    c.put(21, 37, "@")
    c.put(25, 37, "@")
    c.put(18, 36, "o")
    c.put(28, 36, "o")
    return stamp("base:stamp/citadel", c, (23, 39), [])


def lair(stamp_id: str, wall: str, thickness: int, floor: str, gaps: str, mob: str, other: str, elite: str, extras: list[tuple[str, int, int]]) -> dict:
    """A lair: a ring of `wall` around an open floor full of one kind of creature, with a few of another and an elite in the middle (spec 09, "Landmarks")."""
    c = Canvas(25, 21)
    c.rect(1, 1, 23, 19, wall)
    c.rect(1 + thickness, 1 + thickness, 23 - 2 * thickness, 19 - 2 * thickness, floor)
    anchor = (12, 10)
    for side in gaps:  # the ways in: a road three tiles wide through the ring
        for lane in (11, 12, 13) if side in "ns" else (9, 10, 11):
            for depth in range(thickness + 1):
                x, y = {"n": (lane, depth), "s": (lane, 20 - depth), "w": (depth, lane), "e": (24 - depth, lane)}[side]
                c.put(x, y, "=")
        if anchor == (12, 10):
            anchor = {"n": (12, 0), "s": (12, 20), "w": (0, 10), "e": (24, 10)}[side]
    points = [(x, y) for y in (5, 9, 13) for x in ((6, 10, 14, 18) if y != 9 else (8, 12, 16))]
    for i, (x, y) in enumerate(points):
        c.put(x, y, elite if i == 5 else other if i in (3, 8) else mob)
    for ch, x, y in extras:
        c.put(x, y, ch)
    if floor == ".":
        for x, y in ((4, 16), (20, 4)):
            c.put(x, y, "$")
    return stamp(stamp_id, c, anchor, [], open_air=(floor == "."))


def sanctum(who: str) -> dict:
    """A sanctum of the ring around the start: a round of stone open on four sides, lamps, a statue of Lyra, and one Echo in the middle (spec 18, "Personal bosses")."""
    from make_echoes import ECHOES
    c = Canvas(17, 17)
    c.rect(1, 1, 15, 15, "#")
    c.rect(2, 2, 13, 13, "c")
    for lane in (7, 8, 9):  # the four ways in
        for depth in (0, 1):
            c.put(lane, depth, "=")
            c.put(lane, 16 - depth, "=")
            c.put(depth, lane, "=")
            c.put(16 - depth, lane, "=")
    for x, y in ((3, 3), (13, 3), (3, 13), (13, 13)):
        c.put(x, y, "l")
    c.put(8, 4, "^")
    c.put(8, 8, ECHOES[who][0])
    return stamp(f"base:stamp/sanctum_{who}", c, (8, 8), [])


def den() -> dict:
    """Ironspine: a den of dire wolves inside a ring of trees."""
    return lair("base:stamp/den", "t", 2, ".", "e", "D", "W", "U", [("o", 6, 7), ("o", 18, 11), ("o", 10, 15)])


def vent() -> dict:
    """The Ashen Wastes: a ring of stone around a vent of magma slimes."""
    return lair("base:stamp/vent", "#", 1, "c", "w", "M", "e", "X", [("l", 3, 3), ("l", 21, 3), ("l", 3, 17), ("l", 21, 17)])


def grotto() -> dict:
    """Tidehaven: a coral grotto open to the north and the south."""
    return lair("base:stamp/grotto", "#", 1, "c", "ns", "Z", "i", "C", [("#", 8, 7), ("#", 16, 7), ("#", 8, 11), ("#", 16, 11)])


def amber() -> dict:
    """Sunscar: a hollow of rocks full of amber slimes."""
    return lair("base:stamp/amber", "o", 2, ".", "n", "P", "a", "L", [("t", 5, 7), ("t", 19, 7), ("t", 12, 15)])


def icepit() -> dict:
    """Frostveil: a pit of ice slimes with a way in on each side."""
    return lair("base:stamp/icepit", "#", 1, "c", "ew", "H", "f", "j", [("#", 11, 7), ("#", 13, 11), ("l", 3, 3), ("l", 21, 17)])


def roost() -> dict:
    """Lumeria: a roost of storm wolves inside a ring of trees."""
    return lair("base:stamp/roost", "t", 2, ".", "s", "O", "d", "k", [("o", 6, 7), ("o", 18, 7), ("o", 12, 11)])


def outpost(stamp_id: str, layout: str, deco: str) -> dict:
    """A far camp with a shop, an inn, a well and a Threshold Stone (spec 09, "Landmarks")."""
    if layout == "a":
        c = Canvas(23, 13)
        c.house(1, 1, 8, 5, {(1, 1): "b", (5, 2): "S"}, door=3)
        c.house(14, 1, 8, 5, {(1, 1): "b", (5, 2): "I"}, door=4)
        c.rect(9, 6, 5, 3, "c")
        c.put(11, 7, "w")
        c.put(12, 7, "T")
        c.put(10, 8, "V")
        c.vline(11, 9, 12, "=")
        for x, y in ((0, 12), (22, 12), (5, 9), (17, 9)):
            c.put(x, y, deco)
        for ch, x, y in (("+", 13, 10), ("?", 8, 10), ("*", 19, 10), ("~", 6, 7), ("~", 16, 7)):
            c.put(x, y, ch)
        return stamp(stamp_id, c, (11, 7), [(10, 7), (12, 8)])
    if layout == "b":
        c = Canvas(19, 13)
        c.house(2, 1, 15, 5, {(2, 2): "S", (12, 2): "I", (6, 1): "b", (8, 1): "b"}, door=7)
        c.rect(7, 7, 5, 3, "c")
        c.put(9, 8, "w")
        c.put(11, 8, "T")
        c.put(7, 8, "V")
        c.vline(9, 10, 12, "=")
        for x, y in ((0, 12), (18, 12), (3, 8), (15, 8)):
            c.put(x, y, deco)
        for ch, x, y in (("+", 10, 11), ("?", 6, 11), ("*", 13, 10), ("~", 4, 7), ("~", 14, 7)):
            c.put(x, y, ch)
        return stamp(stamp_id, c, (9, 8), [(8, 8), (10, 9)])
    c = Canvas(21, 13)
    c.house(1, 1, 7, 4, {(1, 1): "b", (3, 1): "S"}, door=3)
    c.house(13, 1, 7, 4, {(1, 1): "b", (3, 1): "I"}, door=3)
    c.rect(8, 6, 5, 3, "c")
    c.put(10, 7, "w")
    c.put(12, 7, "T")
    c.put(9, 8, "V")
    c.put(8, 6, "l")
    c.put(12, 8, "l")
    c.vline(10, 9, 12, "=")
    for x, y in ((0, 12), (20, 12), (4, 8), (16, 8)):
        c.put(x, y, deco)
    for ch, x, y in (("+", 11, 10), ("?", 7, 10), ("*", 15, 10), ("~", 4, 6), ("~", 16, 6)):
        c.put(x, y, ch)
    return stamp(stamp_id, c, (10, 7), [(9, 7), (11, 8)])


def outpost_ironspine() -> dict:
    return outpost("base:stamp/outpost_ironspine", "a", "o")


def outpost_tidehaven() -> dict:
    return outpost("base:stamp/outpost_tidehaven", "b", "o")


def outpost_frostveil() -> dict:
    return outpost("base:stamp/outpost_frostveil", "c", "t")


def outpost_whisperwood() -> dict:
    return outpost("base:stamp/outpost_whisperwood", "a", "t")


def outpost_sunscar() -> dict:
    return outpost("base:stamp/outpost_sunscar", "b", "o")


def outpost_lumeria() -> dict:
    return outpost("base:stamp/outpost_lumeria", "c", "t")


def outpost_ashen() -> dict:
    return outpost("base:stamp/outpost_ashen", "a", "o")


def outpost_verdalis() -> dict:
    return outpost("base:stamp/outpost_verdalis", "c", "t")


def forge() -> dict:
    """The Deep Forge of Ironspine: a serpentine of furnace halls from the south door to the Forge Tyrant in the north hall."""
    c = Canvas(41, 37)
    c.rect(1, 1, 39, 34, "#")
    c.rect(2, 2, 37, 32, "c")
    for y, gap in ((12, 36), (20, 4), (28, 36)):  # the walls between the halls, each with its gap on alternate sides
        c.hline(2, 38, y, "#")
        for x in (gap - 1, gap, gap + 1):
            c.put(x, y, "c")
    for x, y in ((9, 15), (20, 15), (31, 15), (9, 24), (20, 24), (31, 24), (9, 31), (31, 31)):  # anvils
        c.rect(x, y, 2, 2, "#")
    for y in (34, 35, 36):  # the entrance and the path to it
        for x in (19, 20, 21):
            c.put(x, y, "c")
    for x, y in ((3, 3), (37, 3), (3, 10), (37, 10), (3, 18), (37, 18), (3, 26), (37, 26), (17, 33), (23, 33)):
        c.put(x, y, "l")
    c.put(20, 5, "q")
    for x, y in ((14, 6), (26, 6)):
        c.put(x, y, "F")
    for x, y in ((6, 4), (34, 4), (6, 9), (34, 9), (20, 9)):
        c.put(x, y, "D")
    for x, y in ((6, 16), (14, 18), (26, 18), (34, 16), (14, 14), (26, 14)):
        c.put(x, y, "m")
    for x, y in ((6, 22), (34, 22), (14, 25), (26, 25)):
        c.put(x, y, "W")
    for x, y in ((6, 31), (14, 30), (26, 30), (34, 31)):
        c.put(x, y, "m")
    c.put(15, 36, "T")
    c.put(18, 35, "@")
    c.put(22, 35, "@")
    c.put(14, 35, "~")
    c.put(26, 35, "~")
    return stamp("base:stamp/forge", c, (20, 36), [])


def galleon() -> dict:
    """The Sunken Galleon of Tidehaven: a ship's hull with three holds, the Drowned Captain at the bow."""
    c = Canvas(47, 19)
    c.rect(1, 2, 45, 15, "#")
    c.rect(2, 3, 43, 13, "c")
    for j in range(5):  # the bow narrows
        for x in range(39 + j, 45):
            c.put(x, 3 + j, "#")
            c.put(x, 15 - j, "#")
    for x in (14, 28):  # the bulkheads, each with a door amidships
        c.vline(x, 3, 15, "#")
        for y in (8, 9, 10):
            c.put(x, y, "c")
    for y in (8, 9, 10):  # the way in at the stern
        for x in (0, 1):
            c.put(x, y, "c")
    for x, y in ((9, 5), (9, 13), (21, 5), (21, 13), (35, 5), (35, 13)):  # masts and barrels
        c.rect(x, y, 2, 1, "#")
    for x, y in ((3, 4), (3, 14), (12, 4), (12, 14), (16, 4), (26, 4), (30, 4), (30, 14)):
        c.put(x, y, "l")
    c.put(41, 9, "r")
    c.put(34, 9, "Q")
    for x, y in ((4, 6), (4, 12), (8, 9), (11, 6), (11, 12)):
        c.put(x, y, "i")
    for x, y in ((17, 6), (17, 12), (21, 9), (25, 6), (25, 12)):
        c.put(x, y, "Z")
    for x, y in ((31, 6), (31, 12), (37, 6), (37, 12)):
        c.put(x, y, "i")
    c.put(0, 13, "T")
    return stamp("base:stamp/galleon", c, (0, 9), [])


def keep() -> dict:
    """The Glacier Keep of Frostveil: a curtain wall, four towers and a central keep for the Frost Sovereign."""
    c = Canvas(41, 41)
    c.rect(1, 1, 39, 39, "#")
    c.rect(2, 2, 37, 37, "c")
    for x, y, dx, dy in ((2, 2, 6, 10), (30, 2, 34, 10), (2, 30, 6, 30), (30, 30, 34, 30)):  # the towers
        c.rect(x, y, 9, 9, "#")
        c.rect(x + 1, y + 1, 7, 7, "c")
        c.put(dx, dy, "c")
    c.rect(13, 13, 15, 15, "#")  # the keep
    c.rect(14, 14, 13, 13, "c")
    c.put(20, 27, "c")
    for y in (39, 40):  # the gate
        for x in (19, 20, 21):
            c.put(x, y, "c")
    for x, y in ((20, 31), (12, 20), (28, 20), (16, 35), (24, 35)):
        c.put(x, y, "l")
    c.put(20, 17, "z")
    for x, y in ((16, 16), (24, 16)):
        c.put(x, y, "R")
    for x, y in ((16, 24), (24, 24), (20, 21)):
        c.put(x, y, "H")
    for x, y in ((6, 6), (34, 6), (6, 34), (34, 34)):
        c.put(x, y, "H")
    for x, y in ((8, 20), (32, 20), (20, 8), (11, 11), (29, 11), (11, 29), (29, 29), (20, 33)):
        c.put(x, y, "f")
    c.put(15, 40, "T")
    c.put(18, 40, "^")
    c.put(22, 40, "^")
    return stamp("base:stamp/keep", c, (20, 40), [])


def vault() -> dict:
    """The Obsidian Vault of the Ashen Wastes: a cross of four arms around a central chamber, the Vault Warden at the end of the north arm."""
    c = Canvas(45, 33)
    c.rect(1, 1, 43, 31, "#")
    c.rect(15, 10, 15, 13, "c")  # the central chamber
    c.rect(17, 2, 11, 6, "c")  # the chamber of the Warden
    c.rect(20, 8, 5, 2, "c")  # the north arm
    c.rect(20, 23, 5, 8, "c")  # the south arm
    c.rect(2, 14, 13, 5, "c")  # the west arm
    c.rect(30, 14, 13, 5, "c")  # the east arm
    c.rect(2, 11, 5, 11, "c")  # the west end
    c.rect(38, 11, 5, 11, "c")  # the east end
    for y in (31, 32):
        for x in (21, 22, 23):
            c.put(x, y, "c")
    for x, y in ((18, 3), (26, 3), (16, 11), (28, 11), (16, 21), (28, 21), (21, 29), (23, 29), (3, 12), (41, 12)):
        c.put(x, y, "l")
    c.put(22, 4, "y")
    for x, y in ((19, 6), (25, 6)):
        c.put(x, y, "X")
    c.put(22, 16, "N")
    for x, y in ((18, 13), (26, 13), (18, 19), (26, 19)):
        c.put(x, y, "M")
    for x, y in ((22, 12), (22, 20)):
        c.put(x, y, "e")
    for x, y in ((6, 16), (10, 16), (36, 16), (40, 16), (4, 13), (4, 20), (40, 13), (40, 20)):
        c.put(x, y, "e")
    for x, y in ((22, 26), (22, 29), (8, 16)):
        c.put(x, y, "D")
    c.put(18, 32, "T")
    c.put(20, 32, "^")
    c.put(24, 32, "^")
    return stamp("base:stamp/vault", c, (22, 32), [])


def nest_mint() -> dict:
    """Mint Hollow: a nest of slime mints guarded by an elite."""
    return lair("base:stamp/mint", "o", 2, ".", "s", "3", "4", "n", [("o", 6, 7), ("o", 18, 11), ("o", 10, 15)])


def nest_moss() -> dict:
    """Mossy Den: a nest of slime mosss guarded by an elite."""
    return lair("base:stamp/moss", "t", 2, ".", "n", "5", "d", "p", [("o", 6, 7), ("o", 18, 11), ("o", 10, 15)])


def nest_rust() -> dict:
    """Rust Pit: a nest of slime rusts guarded by an elite."""
    return lair("base:stamp/rust", "#", 1, "c", "ns", "6", "m", "h", [("l", 3, 3), ("l", 21, 3), ("l", 3, 17), ("l", 21, 17)])


def nest_dune() -> dict:
    """Dune Den: a nest of wolf dunes guarded by an elite."""
    return lair("base:stamp/dune", "o", 2, ".", "e", "7", "a", "u", [("o", 6, 7), ("o", 18, 11), ("o", 10, 15)])


def nest_rookery() -> dict:
    """Polar Rookery: a nest of wolf polars guarded by an elite."""
    return lair("base:stamp/rookery", "#", 1, "c", "w", "8", "f", "v", [("l", 3, 3), ("l", 21, 3), ("l", 3, 17), ("l", 21, 17)])


def nest_shoal() -> dict:
    """Pearl Shoal: a nest of slime pearls guarded by an elite."""
    return lair("base:stamp/shoal", "#", 1, "c", "ns", "9", "i", "0", [("l", 3, 3), ("l", 21, 3), ("l", 3, 17), ("l", 21, 17)])


def nest_pool() -> dict:
    """Nebula Pool: a nest of slime nebulas guarded by an elite."""
    return lair("base:stamp/pool", "o", 2, ".", "s", "%", "g", "1", [("o", 6, 7), ("o", 18, 11), ("o", 10, 15)])


def nest_charpit() -> dict:
    """Char Pit: a nest of slime chars guarded by an elite."""
    return lair("base:stamp/charpit", "#", 1, "c", "e", "&", "e", "2", [("l", 3, 3), ("l", 21, 3), ("l", 3, 17), ("l", 21, 17)])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for build in (hamlet, village, town, barrow, cellar, mine, cavern, temple, hollow, ziggurat, observatory, citadel, den, vent, grotto, amber, icepit, roost, hamlet_b, hamlet_c, village_b, village_c, town_b,
                  outpost_ironspine, outpost_tidehaven, outpost_frostveil, outpost_whisperwood, outpost_sunscar, outpost_lumeria,
                  outpost_ashen, outpost_verdalis, forge, galleon, keep, vault, hamlet_d, village_d, town_c,
                  nest_mint, nest_moss, nest_rust, nest_dune, nest_rookery, nest_shoal, nest_pool, nest_charpit,
                  *[(lambda who=who: sanctum(who)) for who in ("ren", "sakura", "daichi", "haruka", "marco", "yuki", "lena", "gideon")]):
        data = build()
        name = data["id"].split("/")[-1]
        path = OUT / f"{name}.json"
        text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        current = path.read_bytes().decode("utf-8") if path.exists() else ""
        if current != text:  # LF line endings, and a file that did not change is not touched
            path.write_bytes(text.encode("utf-8"))
        print(f"{'wrote' if current != text else 'same '} {name}: {data['w']}x{data['h']}")
        if "--show" in sys.argv:
            for row in data["rows"]:
                print("  " + row)


if __name__ == "__main__":
    main()
