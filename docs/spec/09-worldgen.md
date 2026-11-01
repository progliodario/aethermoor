# 09. World generation

Status: **v1.1 (M5a, M5b-1: chunks)**. Reference: `tools/reference/worldgen.py`. Conformance suite: `worldgen`.
Parameters: `data/base/worlds/overworld.json` (`schemas/world.schema.json`). All math is integer, see `01-numerics.md`.

The world is a **pure function** of `(seed, parameters)`: the content of a tile depends only on its own coordinates, never on the
order in which tiles are generated. The same seed therefore gives the same world on every platform, and a save only needs the seed.

## Noise fields

For a field spec `{salt, scale, octaves}` and tile `(x, y)` (non-negative):

```
field(seed, spec, x, y) = fbm2(hash64(seed, spec.salt), (x << 16) / scale, (y << 16) / scale, spec.octaves)     # 0..65535
```

`scale` is the period of the first octave in tiles. Three fields are used: `elevation`, `moisture`, `temperature`.

## Biomes

In this order (first match wins), with `w`, `h`, `border`, `spawn_clear_radius = r`, `(cx, cy) = (w / 2, h / 2)` and the `thresholds`:

1. `x < border`, `y < border`, `x >= w - border` or `y >= h - border`: **water** (a solid sea around the world).
2. `(x-cx)^2 + (y-cy)^2 < r^2`: **plains** (the spawn clearing).
3. `e = elevation`: `e < water`: **water**; `e < beach`: **beach**; `e >= mountain`: **mountain**.
4. `t = temperature < snow`: **snow**.
5. `t >= desert_heat` and `moisture < desert_dry`: **desert**.
6. `moisture >= forest_wet`: **forest**.
7. otherwise **plains**.

Fields are only evaluated when needed (the result does not depend on that).

## Tiles

Each biome maps to a tile gid (`tiles` in the parameters); `plains` has several gids and picks
`plains[(hash64(seed, x, y, 5) >> 40) % count]`. `beach` and `desert` may share a gid. Water and mountain are solid
(`data/base/tilesets/overworld.json`).

## Props

For each tile outside the spawn clearing, with the biome's list of options `{art, radius_x100, per_mille}` in order:
`h = hash64(seed, x, y, 7)`, `roll = (h >> 20) % 1000`; the first option whose cumulative `per_mille` exceeds `roll` is placed
(none when the biome has no list or the roll is above the total). The feet position, in 1/256 tile units, is
`x256 = x*256 + 48 + ((h >> 8) & 0x7F)`, `y256 = y*256 + 128 + ((h >> 16) & 0x7F)`. Props are solid circles of the given radius.

## Enemy spawners

A tile outside the clearing is a spawner when its biome is in `spawners.biomes`, its distance from the center is at least
`spawners.min_distance` (`(x-cx)^2 + (y-cy)^2 >= d^2`) and `(hash64(seed, x, y, 11) >> 20) % 10000 < per_10000`.
It spawns one `spawners.enemy`, at the center of the tile (`x + 0.5`, `y + 0.5`).

## Spawn and NPCs

The player starts at the center of tile `(cx, cy)`. Each `npcs[i]` stands at the center of tile `(cx + dx, cy + dy)`.

## Order and digests

Tiles are row-major. Props and spawners are listed in scan order (rows from the top, columns left to right).
The conformance vectors compare: 120 probes (`x, y, gid`), a row digest every 8 rows (`fold hash64(h, gid)`), the number of tiles, props and
spawners, a props digest (`fold hash64(h, x256, y256, radius_x100 * 2^32 + (fnv1a64(art) >> 32))`), a spawners digest (`fold hash64(h, x, y)`),
the spawn, the NPC positions and the histogram of gids.

## Chunks

The world is also generated in **chunks** of `CHUNK_SIZE = 32` x 32 tiles, so that a world far larger than memory can be played:
chunk `(cx, cy)` is the window of tiles `[cx * 32, (cx + 1) * 32)` x `[cy * 32, (cy + 1) * 32)`. Any integers are valid chunk coordinates;
tiles outside the world are water (the border rule), with no props and no spawners.

`generate_chunk(seed, params, cx, cy)` returns the 1024 gids (row-major), the props and the spawners of the window (scan order inside the
chunk, spawners with absolute tile coordinates). It is **exactly the restriction** of the whole-world generation to the window (same tiles,
same props, same spawners, only ordered by chunk); a chunk never needs its neighbours. Parameters may describe worlds up to 65536 x 65536 tiles.

Conformance suite `worldgen_chunks`: chunks of a 16384 x 16384 world (far from the origin, over the spawn clearing and beyond the edge),
compared by probes, a tile digest (`fold hash64(h, gid)` over the 1024 gids), the prop and spawner digests and the gid histogram.
Both clients also test that the union of chunks equals the whole-world generation.

## Scale and what comes next

M5a generates the whole world at load time (512 x 512 tiles by default; about 0.1 s in C++). The shipped world must be far larger, so
the next step (M5b-2) streams chunks around the player in the simulation and the renderer; after it come per-chunk deltas in saves,
rivers, roads, hand-made stamps, regions, day/night and weather are the next steps of the world milestone.
