# 09. World generation

Status: **v1.3 (M5a, M5b: chunks and streaming, M5d: rivers and roads, M5e: exploration and the world map)**. Reference: `tools/reference/worldgen.py`. Conformance suite: `worldgen`.
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

## Rivers and roads

On top of the biome, a **land** tile (plains, forest, desert, snow or beach) outside the spawn clearing may carry an overlay. Rivers and roads are
the places where a noise field is close to its middle value, which gives long winding lines whose width follows the field:

```
is_river = |field(seed, river, x, y) - 32768| < river.half_width
is_road  = |field(seed, road,  x, y) - 32768| < road.half_width
```

`river` and `road` are noise specs like `elevation` (`salt`, `scale`, `octaves`) with a `half_width`; `river` also has `ford_salt`, `ford_scale`
and `ford_min`. The overlay is (first match wins):

1. river and road: **bridge**;
2. river with `noise2(hash64(seed, ford_salt), (x << 16) / ford_scale, (y << 16) / ford_scale) >= ford_min`: **ford** (shallows, walkable), so a
   river can be crossed every few tens of tiles;
3. river: **river** (deep water, solid);
4. road: **road**;
5. otherwise none.

The overlay replaces the tile gid (`tiles.river`, `tiles.ford`, `tiles.road`, `tiles.bridge`). A tile with an overlay has **no prop and no
spawner**. Water, mountains and the border are never overlaid.

## Tiles

Each biome maps to a tile gid (`tiles` in the parameters; the overlay gids are in the previous section); `plains` has several gids and picks
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

## Streaming

A streamed world is played through a **window** of `5 x 5` active chunks (`ACTIVE_RADIUS = 2`, Chebyshev distance) centered on the chunk of the
player, `(floor(x / 32), floor(y / 32))` with `(x, y)` in tiles. The window is re-evaluated at the start of every tick, after the player moved.

- **Terrain and props.** Only chunks that are loaded exist for collision and drawing. A client loads the active chunks and may keep others
  cached (it should keep those within distance 3 to avoid regenerating at a border; this is not observable). Tiles of a chunk that is not
  loaded are solid, so an unloaded area can never be entered. Props are solid circles; only the props of the chunk of the entity and its
  eight neighbours matter for collision (a prop lies inside its own tile and its radius is below one tile).
- **Enemies.** An enemy exists iff its spawner lies in an active chunk and the spawner is not *cleared*. It starts at the center of the spawner
  tile with full hit points, and its home is that point. Chunks that **enter** the window add their enemies at the end of the enemy list
  (chunks in row-major order, spawners in scan order); chunks that **leave** remove theirs; the order of the other enemies never changes.
  A killed enemy stays in the list (dead, not drawn) until its chunk leaves, and its spawner becomes cleared. A cleared spawner stays cleared
  until its enemy has been dead for `respawn_ticks` of world time and its chunk enters the window again (spec 08, "Respawn").
- **NPCs** are placed from the world parameters (see above) and always exist.
- **Saves** keep the seed, the cleared spawners and the enemies of the window with their state (spec 12); on load the window is rebuilt around the
  saved player position and the saved enemy list defines the order.

Conformance suite `chunk_window`: scripted walks (`move` to a chunk, `kill` an enemy by index, `wait` some world ticks) through a 16384 x 16384 world; after each step the
number of enemies and their digest (`fold hash64(h, x, y, dead)` over the spawner tiles) are compared.

## Exploration and the world map

The world map divides the world in **cells** of `MAP_CELL = 128` x 128 tiles (`columns = ceil(width / 128)`, same for rows). At every tick, after the window of
chunks is updated, the cell of the player `(floor(x) / 128, floor(y) / 128)` and its eight neighbours that lie inside the world become **explored**; explored
cells are never forgotten and are stored in the save (spec 12, `explored`).

The map shows each explored cell with the biome of the tile at the center of the cell (`cell * 128 + 64`): code 0 water, 1 beach, 2 mountain, 3 snow, 4 desert,
5 forest, 6 plains. Rivers and roads are not shown. Unexplored cells are drawn dark. Clients open the map with the `M` key (and a button on touch screens);
the game is paused while it is open. The player is drawn as a dot at its position.

Conformance suite `worldmap`: scripted positions through a 16384 x 16384 world (also at the corners and edges): the number of explored cells and their digest
(`fold hash64(h, x, y)` ordered by row, then column), and the biome codes of 40 cells.

## Scale and what comes next

The shipped overworld is 16384 x 16384 tiles and is streamed (M5b); `generate_world` of the whole world remains for small worlds and tests. World time,
weather and respawn are in spec 08 (M5c). Next come changes of the world kept in saves, rivers, roads, hand-made stamps and regions.
