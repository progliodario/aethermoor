# ADR 0013: Painted anime art, still as vector recipes

- Status: accepted (extends ADR 0004 and ADR 0012)
- Date: 2026-11-11

## Context

The art of the game was a cartoon of mascots: people two and a half heads tall, thick outlines, flat terrain tiles that
repeated at every tile. The owner wants the look of an anime: believable proportions, cel shading, painted backgrounds, light.
The recipes of spec 13 (flat and gradient fills, strokes, alpha) cannot draw that: there is no soft edge, no shade that stays
inside a silhouette, no texture.

Two ways were open:

1. **Painted bitmaps** (PNG) made outside the game. Any look is possible, but the desktop client needs an image decoder (a
   new dependency that CI alone can check), the pack grows by tens of megabytes, a bitmap has one size, and the palette
   variants (fifteen people from one figure, seventy creatures from four bodies) become as many pictures.
2. **Richer recipes**: add to the in-house rasterizer the few things a painter needs, and redraw everything with them.

## Decision

The art stays vector recipes, and the rasterizer of both clients gains (spec 13, v2):

- `blur` on a layer (a box blur of its coverage, three passes): soft shadows, glows, airbrushed shades;
- `clip` (paint only where something is painted) and `blend` (`multiply` for shades that keep the hue of what is under them,
  `add` for light);
- a `noise` fill (value noise from an integer hash, optionally periodic): the matter of ground, bark, stone and cloth;
- **macro tiles**: a terrain recipe of `n * 32` units covers `n x n` tiles, so the painted ground does not repeat at every
  tile, and a `blend` rank in the tileset makes one ground fade over the next;
- a **view from behind** for the rig (`art_back`, `z_back`) and `faces` for beasts drawn from the side.

A reference rasterizer in Python (`tools/reference/raster.py`) is the third implementation: it builds the conformance probes
of the new features and draws the previews, so the art can be judged without a compiler.

Everything is drawn again by generators (`tools/art_tiles.py`, `art_props.py`, `art_chars.py`, `art_looks.py`,
`art_creatures.py`): people are 59 units tall and 4.6 heads, with a second view from behind.

## Consequences

- No new dependency, the pack stays small (about 7 MB of recipes), art scales with the screen, and a new protagonist or
  creature is still a palette and a few layers.
- Baking costs more: a recipe has hundreds of layers, some blurred. The rasterizers now work on the box of each layer
  instead of the whole canvas; the textures are still baked on first use, on the thread that draws.
- The noise is specified to the bit (an integer hash) and the rest is float: the clients are compared with the reference
  with a tolerance of 3 or 4 levels per channel.
- The base size of a tile on screen goes from 48 to 64 pixels: one sees a little less of the world and much more of it.
- Presentation effects that are not recipes (the light of the hour, long shadows, wind, weather, a real font) are the next
  step and do not need the data to change.
