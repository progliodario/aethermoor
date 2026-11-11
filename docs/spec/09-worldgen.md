# 09. World generation

Status: **v1.10 (M5a, M5b: chunks and streaming, M5d: rivers and roads, M5e: the world map, M5f: regions and settlements, then landmarks, fauna, stones, clearings, regions that look like their names, and the map view)**. Reference: `tools/reference/worldgen.py`. Conformance suite: `worldgen`.
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

`home` (`{radius, stamp, dx, dy}` and an optional `name`) guarantees a village next to the start. Tiles within `radius` of the center of the world that would otherwise be land are
**plains** (the home meadow, after the spawn clearing and before the elevation: it is only a change of biome, trees, rocks and enemies grow there as on any plains). The site
cell that contains the tile `(width / 2 + dx, height / 2 + dy)` has a settlement at exactly that site point with the stamp `home.stamp` and the kind of the first
entry of `settlements.kinds` that lists that stamp, without the random roll and the biome conditions (the footprint must lie inside its site cell); its name is `home.name` when the data gives one (Fenwick in the base pack), otherwise it is made like the others.
A world with no `home` has neither the meadow nor the village.

## Regions look like their names

Found by looking at frames of the game: Sunscar was snow with pines and the Ashen Wastes a green meadow, because the biomes come from noise fields that did not know about the regions. Now each region may have:

- `bias {elevation, temperature, moisture}`: added to the three fields near its center. The bias of a tile is a weighted mean of the biases of all the regions (`weight = region_blend^2 - squared distance to the center`, zero beyond; regions
  without a bias count with 0, so Verdalis cools its neighbors); the biases are shifted by 32768 to be positive before the integer division, which rounds the same on every platform. `region_blend` (world data, 4500 tiles) is the reach.
  The spawn clearing and the home meadow stay plains. In the base pack: Sunscar hot and dry (desert), Frostveil cold (snow), Ashen Wastes hot and dry (desert, with ash for ground), Whisperwood wet (forest), Ironspine higher and cooler (mountains and snow),
  Tidehaven lower and a little wetter (coast), Lumeria a little wetter.
- `ground {biome: [gids]}`: the ground tiles of the region instead of `tiles` (picked by the same hash). Sixteen new tiles: ash and ash sand, savanna, frosted grass, moss, coast grass, violet meadow, rocky meadow.
- `props {biome: [options]}`: the random props of the region instead of `props` (dead trees in the Ashen Wastes, cacti in Sunscar, pines in Frostveil...).

In a stamp marked as open air (the glade and the lairs and nests of grass), creatures, lamps and props keep the ground of the terrain instead of a cobblestone.

## Landmarks and dungeons

**Clearings.** The world data may have `landmark_clearing` (tiles, base pack: 24). Around the footprint of every landmark, grown by that many tiles on every side, a tile whose biome is water or mountain becomes plains (the border of the world
stays water). The test is made per site cell: a tile can be inside the clearing of the landmark of its own site cell only. Without it, a third of the random seeds would bury a dungeon in a lake or a range of mountains (measured on 12 seeds: on
average 27 percent of the tiles around a landmark were solid, with a clearing none, and from every landmark land could be followed for at least 110 tiles in every seed tested).

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

The plains pick one of six ground tiles (`tiles.plains` of the world data: two grasses, daisies, clover, dry grass and a mushroom patch).

The random props of the biomes include the new ones: bushes in the plains (20 per mille) and the forest (40), rocks and bones in the desert (10 and 4) and in the snow (10 and 3).

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
chunks is updated, the cell of the player `(floor(x) / 128, floor(y) / 128)` and the cells within two of it in each direction (5 x 5 cells, 640 tiles across) that lie inside the world become **explored**; explored
cells are never forgotten and are stored in the save (spec 12, `explored`).

The map shows each explored cell with the biome of the tile at the center of the cell (`cell * 128 + 64`): code 0 water, 1 beach, 2 mountain, 3 snow, 4 desert,
5 forest, 6 plains. Rivers and roads are shown from the middle zoom: when the map draws a cell as `n x n` samples with `n >= 4`, each sample is `map_code_at(x, y, widen)` with `widen = 128 / n / 2`: on land outside the spawn clearing, code 7 (a river) when `|river - 32768| < river.half_width * widen`, else code 8 (a road) when `|road - 32768| < road.half_width * widen`, else the biome; the small map samples every 16 tiles with `widen` 8. Conformance: `map_codes` of the suite `worldmap`. A settlement is shown on the map cell that contains its site point as a marker, with its name, once the cell is explored. Unexplored cells are drawn dark. Clients open the map with the `M` key (and a button on touch screens);
the game is paused while it is open. The player is drawn as a dot at its position.

### The map view

The view is presentation, not rules (no vectors): both clients draw the same thing from the same constants, and nothing of it is saved.

- The map is shown in a square **view** onto the grid of cells. A **zoom level** `0..4` sets the size of a cell: level 0 fits the whole world in the view
  (`cell_px = side / max(columns, rows)`), every level doubles it (`cell_px * 2^level`, so 16 times at level 4). The view has a **center**, a cell position
  (fractional) kept inside `[0, columns] x [0, rows]`.
- Opening the map **frames what was explored**: the center is the middle of the bounding box of the explored cells, and the level is the biggest at which the box plus a margin
  of one cell on each side fits in the view. A new game, which has explored 5 x 5 cells, opens at level 3 or 4; a game that has crossed the world opens at level 0 or 1.
- The player moves the view (a step is a sixth of the view), changes the level, goes back to the player (the view is centered on the player's position, same level) or frames the
  explored cells again. Keys, drag, wheel, pinch and buttons are in spec 16.
- **Detail.** What is explored stays whole cells of 128 x 128 tiles, but a cell is drawn as a grid of `n x n` squares, `n = 1` at level 0 and `n = 2^level` from level 1 (2, 4, 8, 16), so that a square stays about 4 or 5 pixels at every zoom. The square `(i, j)` (column, row, from the top left) has the
  biome code of the tile at `(cell_x * 128 + (2i + 1) * 128 / (2n), cell_y * 128 + (2j + 1) * 128 / (2n))` (`biome_code_at`, integer division): at `n = 1` the center of the cell, as before; at `n = 16` one square is 8 x 8 tiles. Coasts, mountain ranges, deserts and snow are visible as shapes when zoomed in. Cells and markers outside the view are not drawn.
- Markers: settlements (hamlets, villages, towns) in yellow, the other sites (dungeons, lairs, nests) in violet; their size grows with the level.
  A name is drawn at the first free side of its marker (right, left, below, above) where it is entirely inside the view and over no marker and no name already drawn, in this order of priority:
  towns, villages, other sites, then hamlets (hamlets only from level 3). The names of the regions follow (below their center, above it, or on it, the same way) when their center is explored. Text on the map has a dark edge.
- The player is a red square with a white edge that pulses; when it is outside the view, it stays on the edge of the view, in orange, so the way back is always shown.
- **The goal.** The player can mark a place of the world as the goal (not saved, one at a time, cleared when returning to the title screen): `P` marks the center of the view,
  a right click marks the pointer's position, `X` removes it (on touch screens a button marks the center of the view and, pressed again, removes it). The map shows it as a green square joined to the player by a green line, both kept inside
  the view when they are outside it. The goal is kept with the game (a file `goal.txt`, `x y` in tiles, in the folder of the slot; removed with the goal), not in the save document. On the HUD, in a streamed world, the player always sees `Position x, y` (in tiles) and, with a goal, `Goal: <direction>, <distance> tiles` where
  the direction is one of eight points of the compass (`atan2(dy, dx)` rounded to the nearest eighth of a turn, y pointing down) and the distance is the rounded Euclidean distance; under 6 tiles it says the player is there.
- The Threshold Stones that were woken are shown as small pale squares.
- **The small map.** In a streamed world a small square map of the land around the player stays in the top left corner (hidden while a dialogue or the world map is open; `N` shows or hides it;
  a tap on it opens the world map on touch screens): 40 x 40 samples 16 tiles apart (640 tiles across) with the biome code of the tile at the middle of each sample (`biome_code_at`), drawn only where the cell
  (128 x 128 tiles) is explored, sampled again whenever the player has walked into another 16-tile square. On it: the player in red, the woken stones in pale green, and the goal in green (kept on its edge when far).
- **Jumping between places.** `Tab` (a button on touch screens) moves the view to the next place found (every settlement, dungeon, lair or nest of an explored cell), nearest to the player
  first (ties by name), at the exact point of the site, and says its name; opening the map starts the cycle again. With `P` the place becomes the goal.
- **In the world.** With a goal more than 12 tiles away, a green arrow with a dark edge circles the player (about 2 tiles from them) and points toward it. Entering another region shows
  its name in a short notice (`You enter Whisperwood`). The HUD texts (clock, region, gold, position, goal, the quests) have a dark edge so that they read over the world.
- Under the view: the keys, the position in tiles and the zoom (`You are at x, y   zoom 4x`) and a legend of the three colors.

Conformance suite `worldmap`: scripted positions through a 16384 x 16384 world (also at the corners and edges): the number of explored cells and their digest
(`fold hash64(h, x, y)` ordered by row, then column), the biome codes of 40 cells (`biome_code`) and of 60 tiles (`biome_code_at`).

## Scale and what comes next

The shipped overworld is 16384 x 16384 tiles and is streamed (M5b); `generate_world` of the whole world remains for small worlds and tests. World time,
weather, seasons and respawn are in spec 08.
