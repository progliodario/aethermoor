# 09. World generation

Status: **v1.4 (M5a, M5b: chunks and streaming, M5d: rivers and roads, M5e: the world map, M5f: regions and settlements)**. Reference: `tools/reference/worldgen.py`. Conformance suite: `worldgen`.
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

## Regions

`regions` lists the named regions of a world: `{id, name (an $i18n: key), x_pm, y_pm, danger}`. The center of a region is `(x_pm * width / 1000, y_pm * height / 1000)`
(integer division). The region of a tile is the one with the nearest center (squared distance); on a tie the lower index wins. Regions are hand-placed key
points (the same in every seed); they do not change the terrain yet. `danger` is the base danger level of the region for the enemies and quests that use it later.

## Settlements

Villages and towns are drawn by **stamps** (documents `base:stamp/...`, `schemas/stamp.schema.json`) at **sites** placed from the seed. The world is divided in
**site cells** of 256 x 256 tiles; each cell has at most one settlement.

For the site cell `(sx, sy)` (tile `(x, y)` belongs to cell `(x / 256, y / 256)`):

1. `h = hash64(seed, sx, sy, 41)`. There is a settlement only if `(h >> 40) % 1000 < settlements.per_mille`.
2. The site point is `px = sx * 256 + 40 + (h >> 8) % 176`, `py = sy * 256 + 40 + (h >> 24) % 176` (at least 40 tiles from the border of the cell, so a stamp
   never leaves its cell; stamps are at most 48 tiles wide).
3. `k = hash64(seed, sx, sy, 42)`. The kind is picked from `settlements.kinds` (`id`, `weight`, `stamps`) with `roll = (k >> 20) % total_weight` over the cumulative
   weights in list order; the stamp is `stamps[(k >> 40) % count]`.
4. The stamp is placed so that its `anchor` is on the site point: its top-left tile is `(px - anchor_x, py - anchor_y)` and it covers `w x h` tiles (the **footprint**).
5. The settlement exists only if the site point and the four corners of the footprint are on plains or forest, and the site point is at least
   `spawn_clear_radius + 48` tiles from the center of the world.
6. The name is made of three syllables of `settlements.names`: `n = hash64(seed, sx, sy, 43)`, `start[n % count] + mid[(n >> 16) % count] + end[(n >> 32) % count]`.
   Names are proper nouns from data tables and are not translated.

**Stamp tiles.** A stamp has `rows` of `w` characters (`h` rows) and a `legend` that maps characters to `{tile, prop, radius_x100, npc}`. A tile of the footprint takes the gid of its
character's `tile` (a character with no `tile`, or one that is not in the legend, such as `.`, keeps the terrain's gid without river or road). A `prop` stands at the
center of the tile, `x256 = x * 256 + 128`, `y256 = y * 256 + 192`. No random prop, enemy spawner, river, road or ford appears inside a footprint. `npc` marks a slot for a settlement NPC
with that role (spec below). A stamp may also list `spots`, tiles `[x, y]` relative to it where its people gather in the evening (spec 08, Routines).

**Order.** Props of stamps join the others in scan order (rows from the top, columns left to right), like all props.

Conformance suite `settlements`: the settlements (top-left tile, site point, kind, stamp, name, region) of blocks of site cells, regions of 40 random tiles and the
names for the world map markers; the chunks that contain settlements are also in the `worldgen_chunks` suite.

## The home village

`home` (`{radius, stamp, dx, dy}`) guarantees a village next to the start. Tiles within `radius` of the center of the world that would otherwise be land are
**plains** (the home meadow, after the spawn clearing and before the elevation: it is only a change of biome, trees, rocks and enemies grow there as on any plains). The site
cell that contains the tile `(width / 2 + dx, height / 2 + dy)` has a settlement at exactly that site point with the stamp `home.stamp` and the kind of the first
entry of `settlements.kinds` that lists that stamp, without the random roll and the biome conditions (the footprint must lie inside its site cell); its name is made like the others.
A world with no `home` has neither the meadow nor the village.

## Landmarks and dungeons

`landmarks` (world data, `{id, name, stamp, kind, dx, dy}`) places hand-made sites such as dungeons. The site cell that contains the tile `(width / 2 + dx, height / 2 + dy)` has a settlement of that `kind`
at exactly that site point, with the stamp, the proper-noun `name` of the landmark and no random roll or biome condition (like the home village); each landmark lies in a site cell of its own. A footprint
replaces everything under it, so a landmark is a **fully specified** picture (walls, floors, doors): its characters decide every tile.

A legend entry may name a `spawner` (an enemy ID): the tile is an **enemy spawner** of that enemy, listed with the other spawners in scan order (spec 09, "Enemy spawners"; the random spawner test does not
apply inside footprints). The enemy of any spawner is therefore the `spawner` of its stamp tile when it has one, else a pick of the fauna of its region. Spawners of a dungeon respawn like any other (spec 08).
Verdalis has two dungeons: Grunmoor Barrow (`base:stamp/barrow`), north-west of the start, with the Barrow Warden in its north hall, and Mossveil Cellar (`base:stamp/cellar`), north-east, a cellar of slimes with the Gel King in its north room. Each has a Threshold Stone at its entrance.
Ironspine has Ironspine Mine (`base:stamp/mine`), far to the north-east (about 6300 tiles from the start): three galleries of slate slimes, grey wolves and shade wolves and the Ironbound Foreman in the north hall, with a Threshold Stone at the door. Tidehaven has the Drowned Temple (`base:stamp/temple`), far to the south-west: a nave, four side chambers of tide slimes and the Tide Regent in the apse. Frostveil has the Frostveil Cavern (`base:stamp/cavern`), far to the north: a cavern of ice pillars and frost wolves and the Rime Revenant in its north hall. Each has a Threshold Stone at its entrance. The last four regions have one too: the Whisperwood Hollow (`base:stamp/hollow`), a glade inside a ring of trees with shade wolves and the Moonshade Alpha; the Sunken Ziggurat (`base:stamp/ziggurat`) in Sunscar, three rings of walls whose gates are on opposite sides, sand slimes and the Sand Sentinel at the center; the Starfall Observatory (`base:stamp/observatory`) in Lumeria, a domed hall with a library on each side, glow slimes and the Astral Curator in the north chamber; and the Cinder Citadel (`base:stamp/citadel`) in the Ashen Wastes, a fortress of four bastions and a courtyard of ember slimes with the Cinder Colossus in the keep. Six lairs of the creatures added later are landmarks too (`kind` `dungeon`, no boss and no Threshold Stone): the Dire Den (`base:stamp/den`, Ironspine, a ring of trees full of dire wolves), the Magma Vent (`vent`, Ashen Wastes), the Coral Grotto (`grotto`, Tidehaven, open to the north and south), the Amber Hollow (`amber`, Sunscar), the Ice Pit (`icepit`, Frostveil, open to the east and west) and the Storm Roost (`roost`, Lumeria); each is a ring of walls, rocks or trees around eight spawners of its creature and three of a second one. The middle spawner of each lair is an **elite** (a stronger version of its creature, levels 10 to 13, with a sure drop of a unique weapon or armor): the Dire Alpha, the Magma Heart, the Coral Matron, the Amber Queen, the Ice Warden and the Storm Sovereign. Conformance suite `fauna` includes every spawner of the dungeons.

Eight **outposts** (landmarks of `kind` `hamlet`) stand near the dungeons of each region and in Verdalis, so the long trips have a rest on the way: each is a small camp with a shopkeeper, an innkeeper, a villager, a well and a Threshold Stone
(Ironspine Waystation, Brinewatch Post, Rimewatch Hut, Hollow's Edge Camp, Dune Caravanserai, Lantern Rest, Ember Watch, Crossroads Camp; stamps `outpost_<region>` with three layouts). Four **deep dungeons** are the last of Mira's letters
(spec 07): the Deep Forge (`forge`, Ironspine: a serpentine of four furnace halls and the Forge Tyrant), the Sunken Galleon (`galleon`, Tidehaven: three holds of a ship's hull and the Drowned Captain at the bow), the Glacier Keep (`keep`, Frostveil:
a curtain wall, four towers and the Frost Sovereign in the keep) and the Obsidian Vault (`vault`, the Ashen Wastes: a cross of four arms and the Vault Warden at the end of the north arm). Each has a Threshold Stone at its entrance.
Nine more creatures live in the fauna of the regions (levels 2 to 12: mint slimes, tawny wolves, moss slimes, rust slimes, dune wolves, polar wolves, pearl slimes, nebula slimes and char slimes), each with a material for the guild's commissions.

Eight **nests** complete the map: small lairs of the creatures that came with the commissions, one in each region, in the free site cell nearest to its center: the Mint Hollow (`mint`, Verdalis, only about 180 tiles from the start),
the Mossy Den (`moss`), the Rust Pit (`rust`), the Dune Den (`dune`), the Polar Rookery (`rookery`), the Pearl Shoal (`shoal`), the Nebula Pool (`pool`) and the Char Pit (`charpit`). They are built like the lairs (ring, eight spawners of the creature and three of
a second one) with an elite in the middle that stays near its post (behavior `guardian`) and drops a unique rare or epic piece: from the Minty charm vest (defense 3) of the Mint Matron, level 5, to the Char tyrant's blade (attack 30), level 16.

Eight creatures with silhouettes of their own join the fauna (cave bats and cave spiders in Ironspine, Whisperwood and Lumeria, myconids from Verdalis to Lumeria, stone golems in Ironspine, Sunscar and the Ashen Wastes, will-o'-the-wisps,
shore crabs on the coast of Tidehaven, dune scorpions in Sunscar and night owls), each with its material for the guild's gather jobs. The slime elites wear a crown to tell them from their kind. Stamps can use eight more props (`tent`,
`signpost`, `crate`, `statue`, `banner`, `bush`, `bones`, `campfire`): the outposts have a signpost, a campfire, a tent and crates, the lairs have bones and the entrances of the dungeons have banners, statues or crates. A prop has no tile of its
own, so a stamp puts it on terrain that is not a wall.

Settlements have more than one look: `settlements.kinds[].stamps` lists the stamps of a kind and the site picks one of them (step 3 above). Hamlets have four (`hamlet`, `hamlet_b` with two houses, `hamlet_c` with a barn and `hamlet_d` a crossroads), villages four (`village`, `village_b` four houses around a square, `village_c` a main street and `village_d` a long street) and towns three (`town` walled, `town_b` open around a big plaza and `town_c` with the guild hall on the square). All of a kind keep the same roles.

## Settlement people

The stamp characters whose legend entry has an `npc` role are **NPC slots**. Slots are numbered `0, 1, ...` in scan order of the stamp (rows from the top, columns left to right).
The NPC of slot `i` of the settlement of site cell `(sx, sy)`, standing on tile `(x, y)`:

| Field | Value |
|---|---|
| `key` | `settle:<sx>:<sy>:<i>` |
| `role` | the `npc` role of the slot (`elder`, `shopkeeper`, `innkeeper`, `guild_clerk`, `villager`, ...) |
| position | `x256 = x * 256 + 128`, `y256 = y * 256 + 160` (feet, in 1/256 tile) |
| `h` | `hash64(seed, sx, sy, 100 + i)` |
| `name` | `people.start[h % n] + people.end[(h >> 16) % m]` with `settlements.people` |
| `variant` | `settlements.variants[(h >> 32) % count]` (a palette of the character art, `""` is the default one) |
| `tone` | the `tone` of the region of the settlement (`regions[].tone`) |
| `dialogue` | `settlements.dialogue` with `{role}` and `{tone}` replaced |
| `place` | the name of the settlement |
| `region` | the `name` text key of the region of the settlement |
| `plaza` | `x256`, `y256` of its gathering spot (spec 08, Routines), or -1 when the stamp has no spots |
| `quirk` | `settlements.quirks[hash64(seed, sx, sy, 44) % count]`, a text key: what the place is known for, the same for the whole settlement |

The region gives the **tone** of the voice of its people (warm, mystic, gruff, flowery, stoic, salty, grim, scholarly); the quirk and the name make each place different.
The dialogue texts use `{npc}`, `{place}`, `{region}` and `{quirk}` (spec 07, "Dialogue arguments").

An NPC exists while the chunk of its tile is in the active window and its routine (spec 08) does not keep it away; the dynamic NPCs are listed in the order of chunks (row-major), then slots (scan order).
`generate_chunk` also returns the people of the chunk, in scan order of their tiles; the conformance vectors of `worldgen_chunks` list them.

## Threshold Stones

A **Threshold Stone** is a prop in the plaza of a hamlet, village or town (legend character `T` of the stamps, art `stones.art`, radius 0.35). The world data has `stones {art, range_x100}`.
A stone is **near** when the distance from the player's feet to the foot of the prop is at most `range_x100 / 100` tiles (1.6).

*Using* a stone (the interact action when no NPC is in range) **wakes** it: its tile `(floor(x), floor(y))` of the prop is added, if new, to the player's list of stones (order of waking, saved as `stones`, spec 12),
the player's health is restored to the maximum, and the list of stones is offered. *Traveling* to another stone of the list (never the one in use) puts the player at `(x + 0.5, y + 1.75)` of the tile,
one tile in front of the stone, and loads the chunks around. The list shows the name of the settlement of each stone (the settlement of the site cell that contains it) and its region.
Traveling costs nothing and takes no time. The stones are placed by the stamps, so they follow the placement of settlements (the conformance vectors of `worldgen_chunks` and `settlements` include their props).

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
It spawns one enemy, at the center of the tile (`x + 0.5`, `y + 0.5`), chosen by the **fauna** of the region of the tile.

**Fauna.** Every region lists `fauna`: entries `{enemy, drop, weight}` (`drop` is the item the enemy leaves, used by the guild for collect jobs). The enemy of a spawner is the entry
that `r = (hash64(seed, x, y, 12) >> 20) mod W` falls on, where `W` is the sum of the weights and the entries share the slots `0..W-1` in order (an entry of weight `w` takes the next `w` slots).
The choice depends only on the seed, the tile and its region, so a spawner always makes the same enemy and a saved enemy is rebuilt from its spawner tile.
Conformance suite `fauna`: the region and the enemy of spawners near the center of every region.

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
5 forest, 6 plains. Rivers and roads are not shown. A settlement is shown on the map cell that contains its site point as a marker, with its name, once the cell is explored. Unexplored cells are drawn dark. Clients open the map with the `M` key (and a button on touch screens);
the game is paused while it is open. The player is drawn as a dot at its position.

Conformance suite `worldmap`: scripted positions through a 16384 x 16384 world (also at the corners and edges): the number of explored cells and their digest
(`fold hash64(h, x, y)` ordered by row, then column), and the biome codes of 40 cells.

## Scale and what comes next

The shipped overworld is 16384 x 16384 tiles and is streamed (M5b); `generate_world` of the whole world remains for small worlds and tests. World time,
weather and respawn are in spec 08 (M5c). Next come changes of the world kept in saves, rivers, roads, hand-made stamps and regions.
