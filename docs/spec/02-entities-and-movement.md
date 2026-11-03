# 02. Entities, maps and movement

Status: **v1**. Reference: `tools/reference/movement.py`. Conformance suites: `movement` (this file), `combat` and `chunk_window` (the world around the player).
There is no component model: the player, the enemies, the people and the props are plain structures in the simulation (`WorldSim` in C++ and Kotlin), and
the rules about them are in the specs named below.

## Maps

Hand-made maps are **Tiled TMJ** files (`data/<pack>/maps/*.tmj`, JSON, no compression, orthogonal, 32 px tiles).

- Map property `tileset` (string): the ID of a tileset (`schemas/tileset.schema.json`), which maps each `gid` to an art
  recipe and a `solid` flag.
- Tile layer `ground`: `data` holds `width * height` gids, row-major, `0` = empty (treated as not solid, not drawn).
- Object layer `objects`; positions are in pixels (divide by `tilewidth` for tiles):
  - `type: "spawn_player"`: point object, the player's starting position.
  - `type: "enemy_spawner"`: point object at the enemy's feet with property `enemy` (enemy ID); see `05-combat-v1.md`.
  - `type: "prop"`: point object at the **feet** of the prop; properties `art` (recipe ID) and `radius` (float, tiles).
    A prop is a solid circle.
- Cells outside the map are solid.

A **streamed world** (spec 09) has no map file: the tiles, the props and the people come from the chunks around the player (the same rules apply: a solid tile or a
prop circle pushes the player out). The tile gids come from `ChunkStore`, which answers for any tile of the world; a chunk that is not loaded is solid and empty (gid 0, not drawn), which the player never reaches because the window follows the player.
People (spec 07, 09) are solid circles of radius 0.3 at their current position, added to the props while they are in the loaded window and moved when a routine
changes it (spec 08). Enemies are pushed out of solid tiles and props with the same `resolve` and their own radius (spec 05), but they do not push the player or each other: they hurt the player through their attack, not by contact.

## Player and input

- `normalize_input(x, y)`: `len = sqrt(x*x + y*y)`; if `len < 0.15` the result is `(0, 0)`; if `len > 1` it is
  `(x/len, y/len)`; otherwise unchanged. Keyboards produce `(+-1, 0|+-1)` and are normalized (diagonals are not faster).
- Speed in tiles per second: `move_speed_x100 / 100` from the derived stats (`docs/spec/04`).
- The player collider is a circle of radius **0.3 tiles**.

## Movement step (one tick, `dt = 1/60`)

```
x += vx * speed * dt ; resolve ; y += vy * speed * dt ; resolve
```

`resolve(x, y)` repeats up to 4 times, stopping early when nothing moved:

1. For every tile `(tx, ty)` in the range `floor(x-r)..floor(x+r)` by `floor(y-r)..floor(y+r)` (rows from top, then
   columns) that is solid: let `(cx, cy)` be the point of the tile square closest to `(x, y)`, `d = (x-cx, y-cy)`.
   If `|d|^2 < r^2`: when `|d|^2 > 0` push the center along `d` by `r - |d|`; otherwise (center inside the tile)
   push out through the nearest tile face to a distance `r`. Mark moved.
2. For every prop circle `(ex, ey, er)` in map order: if the centers are closer than `r + er`, push the player
   out along the line between the centers (`+x` when the centers coincide). Mark moved.

Movement is floating point (float32 in the clients); the conformance suite compares positions with a tolerance.

## Camera

The camera centers on the player and is clamped so the view stays inside the map; if the map is smaller than the view
in one axis it is centered on that axis. The view size in tiles is `screen_px / tile_px`.

## Draw order

1. Ground tiles, row by row.
2. Entities and props sorted by their feet `y` (smaller first); ties keep map order, the player after props.
3. Debug overlay.
