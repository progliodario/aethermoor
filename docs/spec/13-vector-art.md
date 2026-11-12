# 13. Vector art

Status: **v2** (blur, clip, blend, noise fills, macro tiles and the view from behind were added to v1). Schemas: `art_recipe`, `rig`, `clip`, `tileset`. Conformance suites: `raster`, `rig_pose`.
See ADR 0012 for why both clients use the same in-house software rasterizer.

## Recipes

A recipe describes one image in **art units** (32 art units = 1 tile). `canvas.origin` is the anchor of the
image (feet of a character, joint of a limb, base of a tree).

```json
{ "id": "base:art/prop/rock", "canvas": {"w": 32, "h": 28, "origin": [16, 24]},
  "palette": {"base": "#8D949F"}, "variants": {"dark": {"base": "#555C66"}},
  "layers": [ {"shape": {"ellipse": [16, 16, 12, 9]}, "fill": {"color": "$p.base"},
               "stroke": {"color": "#222222", "width": 1.5}, "alpha": 1.0} ] }
```

- **Shapes** (exactly one key): `rect [x, y, w, h]`, `ellipse [cx, cy, rx, ry]`, `polygon [[x, y], ...]`,
  `path "<d>"` with the **absolute, upper-case** commands `M L H V C Q Z`, numbers separated by spaces or commas.
- **Fill** (optional): `{"color": c}`, `{"linear": {x0, y0, x1, y1, stops}}`, `{"radial": {cx, cy, r, stops}}`.
  `stops` are `[[t, color], ...]` with `t` in 0..1, increasing. Outside the first/last stop the end color is kept.
  `{"noise": {scale, seed, octaves, period, stops}}` is a cloudy texture (see "Noise" below): `scale` is the size of the largest
  clouds in art units, `seed` (default 0) picks the pattern, `octaves` (1 to 6, default 3) adds finer clouds, `period` (default 0:
  none) makes the pattern repeat every `period * scale` art units, so that a tile joins itself.
- **Stroke** (optional): `{"color": c, "width": w}` in art units, round joins and round caps.
- **alpha** (optional, default 1): layer opacity.
- **blur** (optional, default 0, art units): softens the edge of the layer (a soft shadow, a glow, an airbrushed shade).
- **clip** (optional, default false): the layer is painted only where something is already painted, and adds no coverage
  (a shade or a light that stays inside the silhouette).
- **blend** (optional): `"normal"` (default), `"multiply"` (darkens what is under it and keeps its hue: the shades) or `"add"`
  (lightens: glows, rims of light).
- **only** / **except** (optional, lists of variant names): a layer with `only` is drawn just when the chosen variant is
  one of the names; a layer with `except` is skipped when it is. With no variant (the base look) a layer with `only`
  is skipped. This gives a variant its own shapes (a hairstyle, a horn, a scarf), not only its own colors.
- **Colors**: `#RRGGBB`, `#RRGGBBAA` or `$p.name`. `$p.name` is looked up in the recipe palette, overridden by the
  chosen variant. An unknown name renders transparent black.
- Layers are drawn in order; each layer paints its fill, then its stroke.

## Rasterization algorithm (normative)

Input: a recipe, a **scale** `s` (pixels per art unit) and an optional variant name.
Output: an RGBA8 bitmap of `ceil(w*s) x ceil(h*s)` pixels, straight (non-premultiplied) alpha.

All arithmetic is 32-bit float, except trigonometric tables for ellipses (double, then rounded to float).

1. **Polygons.** Convert every shape to closed polygons in pixel space (art coordinates times `s`):
   - `rect`: four points `(x,y) (x+w,y) (x+w,y+h) (x,y+h)`.
   - `ellipse`: `N = 16 + 4 * floor(sqrt(max(rx, ry) * s))` points at angle `2*pi*k/N`, `k = 0..N-1`.
   - `polygon`: the given points.
   - `path`: each `M` starts a subpath; `L H V` add lines; `Q` is flattened into 12 segments and `C` into 16
     segments at uniform `t`; `Z` closes. Every subpath is implicitly closed for filling.
2. **Coverage** (`nonzero` winding rule, 4 sub-scanlines per pixel row): for row `r` and `k = 0..3`, the sample
   height is `ys = r + (k + 0.5) / 4`. An edge `(x0,y0)-(x1,y1)` with `y0 != y1` crosses `ys` when
   `min(y0,y1) <= ys < max(y0,y1)`, at `x = x0 + (ys - y0) * (x1 - x0) / (y1 - y0)`, with direction `+1` when
   `y1 > y0`, else `-1`. Sort crossings by `x`, accumulate the winding number, and for every span with a non-zero
   winding add its **exact horizontal coverage** (clipped to `[0, W]`) divided by 4 to the pixels it touches.
   Coverage is clamped to 1.
3. **Stroke geometry.** For each subpath segment (including the closing segment of a closed shape) with length > 0,
   add a quad `p0 +/- n*h, p1 +/- n*h` (`h = width * s / 2`, `n` the unit normal), and for every vertex a circle polygon
   of radius `h` (same point-count rule as ellipses). Every piece is oriented so its signed area is positive
   (`sum(x_i*y_{i+1} - x_{i+1}*y_i) > 0`); the union is then filled with the nonzero rule.
   The stroke of a layer uses the `blur`, `clip` and `blend` of the layer, like its fill.
3b. **Blur.** `rad = floor(blur * s + 0.5)` pixels. When `rad >= 1` the coverage (of the fill, and of the stroke) is blurred
   before painting: every row is replaced three times by its box blur, then every column three times. One box blur pass
   of a line replaces each value by the sum of the `2*rad + 1` values centred on it, divided by `2*rad + 1`; values outside
   the bitmap count as 0 (so a blurred shape is cut at the edge of the canvas).
4. **Paint.** For every pixel with coverage `c > 0`, evaluate the paint at the pixel center `((x+0.5)/s, (y+0.5)/s)`
   in art units. `a = c * layer_alpha * paint.a`. The destination `dst` is premultiplied float RGBA.
   - `blend: multiply`: `dst.rgb = dst.rgb * (1 - a + a * src.rgb)` for each channel; `dst.a` does not change (`clip` has no
     effect: a multiplied layer never adds coverage).
   - Otherwise, with `clip`: `a = a * dst.a` first.
   - `blend: add`: `dst.rgb = dst.rgb + src.rgb * a`. `blend: normal`: `dst.rgb = src.rgb * a + dst.rgb * (1 - a)`
     (*source over*).
   - Without `clip`, `dst.a = a + dst.a * (1 - a)`; with `clip`, `dst.a` does not change.
   - Linear: `t = clamp(((px-x0)*dx + (py-y0)*dy) / (dx*dx + dy*dy), 0, 1)` with `dx = x1-x0`, `dy = y1-y0`.
   - Radial: `t = clamp(sqrt((px-cx)^2 + (py-cy)^2) / r, 0, 1)`.
   - Noise: `t` is the value of "Noise" below at the pixel center.
   - Stop colors are interpolated linearly in straight RGBA.
5. **Output.** `alpha8 = floor(a * 255 + 0.5)`. If `alpha8 == 0` the pixel is `(0,0,0,0)`. Otherwise each
   channel is `floor(premul / a * 255 + 0.5)`, clamped to 0..255.

### Noise

The value of a noise fill at the art point `(px, py)` is a sum of `octaves` layers of value noise. All integers are unsigned
32-bit and wrap; the rest is float.

```
total = 0; norm = 0; amp = 1
for o in 0 .. octaves-1:
    f = 2^o / scale;  u = px * f;  v = py * f
    ix = floor(u); iy = floor(v); fu = u - ix; fv = v - iy
    su = fu*fu*(3 - 2*fu);  sv = fv*fv*(3 - 2*fv)
    ix1 = ix + 1; iy1 = iy + 1
    if period > 0:  per = period * 2^o;  ix, iy, ix1, iy1 are taken modulo per
    a = H(ix, iy, seed+o);  b = H(ix1, iy, seed+o);  c = H(ix, iy1, seed+o);  d = H(ix1, iy1, seed+o)
    top = a + (b - a)*su;  bottom = c + (d - c)*su
    total += (top + (bottom - top)*sv) * amp;  norm += amp;  amp = amp / 2
t = total / norm

H(i, j, s):  h = i*0x9E3779B1 + j*0x85EBCA77 + s*0xC2B2AE3D
             h ^= h >> 15;  h *= 0x2C1B3C6D;  h ^= h >> 12;  h *= 0x297A2D39;  h ^= h >> 15
             return (h >> 8) / 16777215
```

`t` is in 0..1 and stays near 0.5, so the stops of a noise fill are usually between 0.25 and 0.75.

Tolerances in the conformance suite are +/-2 per channel for probes and a relative area tolerance for shapes.
The two clients must agree with the *geometry*, not bit by bit.

## Macro tiles

A terrain tile is 32 x 32 art units. A tile recipe whose canvas is `n * 32` units wide (`n = round(canvas.w / 32)`, at least
1) is a **macro tile**: it covers `n x n` tiles, and the tile at `(tx, ty)` of the map shows the cell `(tx mod n, ty mod n)` of
the picture (cell 0, 0 is the top left). The painted ground of the base pack uses `n = 4` with noise fills of period 128
units, so the ground does not repeat at every tile and joins itself everywhere. Recipes of the same ground share the base
noise, so that any of them joins any other.

## Ground blending

A tile of the tileset may have a `blend` rank (an integer above 0; walls and floors have none). The clients first draw every
tile, then, for every tile `T` with a rank and each of its four neighbours `N` with a **higher** rank, they draw the picture of
`N` again over the half of `T` next to `N`: fully opaque on the edge they share and fading in a straight line to nothing at
the middle of `T`. The picture of `N` is cut at the cell of `T` (`tx mod n, ty mod n` of `N`'s macro tile), so the ground of `N`
simply goes on. Grass (rank 80) thus fades over a path (40), a path over sand (30), sand over water (10). Tiles of the same
rank do not blend (they are the same ground). Presentation only.

**Corners.** A diagonal neighbour `N` of a higher rank, when neither of the two tiles between them (`(tx + dx, ty)` and
`(tx, ty + dy)`) has a rank higher than `T`, rounds the corner of `T`: the picture of `N` over the quarter of `T` next to it,
opaque at the corner and fading to nothing at the middle of the two edges and at the middle of the tile.

## Water

A macro tile whose tileset `surface` is `water` moves: after the tile, the clients draw the same picture twice more over
it, cut at the cells `(tx + 1, ty + 2)` and `(tx + 2, ty + 3)` (so each copy is the whole water shifted by whole tiles and
joins itself), with opacity `0.26 + 0.22 * sin(t / 1300)` and `0.20 + 0.18 * sin(t / 2100 + 2)` (`t` in milliseconds). The
glints of the picture come and go and the dark and light of the water drift. Presentation only.

## Sway

A recipe may have `"sway": a` (art units): the wind moves it. The clients draw it with its foot still and its top moved
sideways by `a * sin(t / 620 + x * 0.9 + y * 0.6)` art units, where `t` is the time in milliseconds and `(x, y)` the tile
of its foot (so neighbours do not move together); the picture is sheared, not turned. Presentation only: the collision does
not move. The trees, the bushes, the reeds, the banners and the flame of the campfire of the base pack sway.

## Font

`data/base/fonts/aether.json` (ID `base:font/aether`, schema `font`) is the font of the interface: for each character a width
`w` and its strokes `d`, a path in a cell of `cell.w x cell.h` font units, drawn with a round pen of the `stroke` width by the
rasterizer above (one layer with a stroke and no fill), white, at the size a screen needs, and tinted with the colour of the
text. A line of text is its glyphs one after the other, each taking its `w`; a glyph is placed with its cell centred on that
width. A character the font does not have is drawn as `?`. `tools/make_font.py` writes the file. Both clients draw
all their text with it. The desktop lays its screens out in columns of 8 units (`cell.top` is the room that accents take
above the line) and bakes a glyph when a size first needs it; Android bakes all the glyphs once into one texture, at the
size of its screen (capitals `11 * max(1, 0.9 * density)` pixels tall), and makes a libGDX font of them with the metrics of
`cell` (`cap_top`, `cap_height`, `x_height`, `line`): a text is drawn with the top of its capitals where it is asked.

## Facing

A recipe may say `"faces": "left"`: the picture looks to the left (the beasts, seen from the side), and the clients draw it
mirrored when the player is to the right of the creature, so that it faces the player. Without it a picture is never mirrored.

## Rigs and clips

A **rig** lists parts (parents first): `id`, `parent` (or null), `offset [x, y]` (joint position in the parent's
space, art units), `z` (draw order) and `art` (the recipe of the part; the recipe `canvas.origin` is the pivot).
**The blow.** `base:art/clip/humanoid_attack` (optional, not looping, 30 ticks) is played on the player while a skill
is in its phases (spec 05), instead of the idle or walk clip: its tick is `min(phase_tick, 5)` during the startup,
`5 + min(phase_tick, 4)` while the blow is active and `9 + min(phase_tick, 21)` during the recovery. The arm goes back,
comes down and returns. Presentation only: the hitbox and the timing are those of the skill.

A part may have `art_back` and `z_back`: the recipe and the draw order used when the figure is **seen from behind**; a part
without them uses `art` and `z`. The pose is the same in both views. The clients show the player from behind while the last
movement was mostly upward (`facing.y < 0` and `|facing.y| > |facing.x|`), and the other people always from the front.

A **clip** has `loop`, `length_ticks` and per-part `tracks`: `rot [[tick, degrees], ...]` and
`pos [[tick, x, y], ...]` keyframes, linearly interpolated and clamped outside the key range. `events` mark
ticks (footsteps...). Time inside a clip: looping clips use `tick mod length_ticks`, others `min(tick, length)`.

Pose of a part: `local = offset + pos`, `world_pos = parent_pos + R(parent_rot) * local`,
`world_rot = parent_rot + rot` (degrees, clockwise on screen because y points down).
A **mirrored** pose (facing left) negates every `x` and every rotation.

## Scale buckets and caching

The renderer asks for `tile_px` pixels per tile and rasterizes at `s = tile_px / 32`. `tile_px` is rounded up to a
bucket `{32, 48, 64, 96, 128, 192, 256}` (the base size of a tile on screen is 64 pixels times the density of the screen) and the texture is drawn scaled to the exact size. Textures are cached by
`(recipe id, variant, bucket)`; a change of bucket (zoom, screen density) re-bakes in the background. After a lost
graphics context (Android) all textures are re-created from the CPU bitmaps.

**Baking in instalments.** The first three frames of a game bake everything they show. After them a frame bakes until it
has spent a few milliseconds (6 on desktop, 8 on Android), always at least one recipe; what is not baked yet is not drawn
in that frame and appears in one of the next. Walking into a new place thus never freezes the game: new things pop in
over a few frames instead.

## Overrides

A file `data/<pack>/overrides/<recipe id with / replaced by ->.png|svg` replaces a recipe. Not implemented in M2.
