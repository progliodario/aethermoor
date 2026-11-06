# 13. Vector art

Status: **v1**. Schemas: `art_recipe`, `rig`, `clip`, `tileset`. Conformance suites: `raster`, `rig_pose`.
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
- **Stroke** (optional): `{"color": c, "width": w}` in art units, round joins and round caps.
- **alpha** (optional, default 1): layer opacity.
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
4. **Paint.** For every pixel with coverage `c > 0`, evaluate the paint at the pixel center `((x+0.5)/s, (y+0.5)/s)`
   in art units. `a = c * layer_alpha * paint.a`. Composite *source over* in premultiplied float
   (`dst = src_premul + dst * (1 - a)`).
   - Linear: `t = clamp(((px-x0)*dx + (py-y0)*dy) / (dx*dx + dy*dy), 0, 1)` with `dx = x1-x0`, `dy = y1-y0`.
   - Radial: `t = clamp(sqrt((px-cx)^2 + (py-cy)^2) / r, 0, 1)`.
   - Stop colors are interpolated linearly in straight RGBA.
5. **Output.** `alpha8 = floor(a * 255 + 0.5)`. If `alpha8 == 0` the pixel is `(0,0,0,0)`. Otherwise each
   channel is `floor(premul / a * 255 + 0.5)`, clamped to 0..255.

Tolerances in the conformance suite are +/-2 per channel for probes and a relative area tolerance for shapes.
The two clients must agree with the *geometry*, not bit by bit.

## Rigs and clips

A **rig** lists parts (parents first): `id`, `parent` (or null), `offset [x, y]` (joint position in the parent's
space, art units), `z` (draw order) and `art` (the recipe of the part; the recipe `canvas.origin` is the pivot).

A **clip** has `loop`, `length_ticks` and per-part `tracks`: `rot [[tick, degrees], ...]` and
`pos [[tick, x, y], ...]` keyframes, linearly interpolated and clamped outside the key range. `events` mark
ticks (footsteps...). Time inside a clip: looping clips use `tick mod length_ticks`, others `min(tick, length)`.

Pose of a part: `local = offset + pos`, `world_pos = parent_pos + R(parent_rot) * local`,
`world_rot = parent_rot + rot` (degrees, clockwise on screen because y points down).
A **mirrored** pose (facing left) negates every `x` and every rotation.

## Scale buckets and caching

The renderer asks for `tile_px` pixels per tile and rasterizes at `s = tile_px / 32`. `tile_px` is rounded up to a
bucket `{32, 48, 64, 96, 128, 192, 256}` and the texture is drawn scaled to the exact size. Textures are cached by
`(recipe id, variant, bucket)`; a change of bucket (zoom, screen density) re-bakes in the background. After a lost
graphics context (Android) all textures are re-created from the CPU bitmaps.

## Overrides

A file `data/<pack>/overrides/<recipe id with / replaced by ->.png|svg` replaces a recipe. Not implemented in M2.
