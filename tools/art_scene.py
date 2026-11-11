"""A piece of world drawn with the art of the pack, to judge how tiles, props, people and creatures look together.

Used by `python tools/art_preview.py --scene`. It is a picture for the eyes of who draws, not a map of the game: the tiles
are laid by hand below, with the macro tiles cut as the clients cut them (spec 13, "Macro tiles").
"""
from __future__ import annotations

from art_preview import Image, baked, draw_figure

ROWS = [
    "ggggGGggggffffff",
    "ggGggggggfffffff",
    "gg######ggggffff",
    "gg#w##w#gggggggg",
    "gg###d##ggggGggs",
    "ggpppppppppggsss",
    "gGgggggppggssswW",
    "ggggggggpgsswwWW",
    "gggGggggpgsswWWW",
]
TILES = {"g": "grass_a", "G": "grass_c", "f": "forest_floor", "#": "wall_timber", "w": "wall_window", "d": "door", "p": "path_dirt",
         "s": "sand", "W": "water"}
TILES["w"] = "wall_window"


def draw(scale: float) -> Image:
    tile = int(32 * scale)
    image = Image(len(ROWS[0]) * tile, len(ROWS) * tile, (0, 0, 0, 1))
    for ty, row in enumerate(ROWS):
        for tx, ch in enumerate(row):
            name = TILES[ch]
            if ch == "w" and ty > 5:
                name = "shallows"
            recipe, sprite = baked(f"base:art/tile/{name}", scale)
            span = max(1, round(recipe["canvas"]["w"] / 32))
            sw, sh, data = sprite
            cx, cy = (tx % span) * tile, (ty % span) * tile
            cell = bytearray()
            for y in range(tile):
                start = ((cy + y) * sw + cx) * 4
                cell += data[start:start + tile * 4]
            image.blit((tile, tile, cell), tx * tile, ty * tile)
    things = [("prop/tree_oak", 12.5, 2.4), ("prop/pine", 14.6, 1.9), ("prop/tree_oak", 10.4, 1.6), ("prop/bush", 9.5, 3.6), ("prop/rock", 1.2, 7.4),
              ("prop/campfire", 4.5, 7.6), ("prop/barrel", 8.6, 4.9), ("prop/crate", 1.4, 5.0), ("prop/lamp", 9.4, 5.2), ("prop/signpost", 10.6, 6.2),
              ("prop/threshold_stone", 6.4, 8.6), ("prop/well", 12.2, 4.8), ("creature/slime_green", 2.6, 8.4), ("creature/wolf_grey", 11.6, 8.3),
              ("creature/barrow_warden", 14.4, 5.2), ("prop/reeds", 12.6, 7.6)]
    people = [("ren", 5.6, 6.4, False, False), ("sakura", 7.0, 6.8, True, False), ("gideon", 3.4, 6.6, False, True), ("green", 8.4, 8.4, False, False)]
    items = [(y, "thing", (art, x, y)) for art, x, y in things] + [(y, "person", (who, x, y, mirror, back)) for who, x, y, mirror, back in people]
    for _, kind, data in sorted(items, key=lambda i: i[0]):
        if kind == "thing":
            art, x, y = data
            recipe, sprite = baked(f"base:art/{art}", scale)
            ox, oy = recipe["canvas"]["origin"]
            image.blit(sprite, round(x * tile - ox * scale), round(y * tile - oy * scale))
        else:
            who, x, y, mirror, back = data
            draw_figure(image, (x * tile, y * tile), scale, None if who == "ren" else who, mirror=mirror, back=back)
    return image
