# ADR 0015: Realistic painted art, from the same recipes

- Status: accepted (supersedes the look chosen in ADR 0013; keeps its recipes, rasterizer and tools)
- Date: 2026-11-26

## Context

ADR 0013 gave the game the look of an anime: flat tones, a hard shade, a dark outline, painted backgrounds. The owner wants the
graphics to look much more detailed and real, less drawn, and sharp. Three things made the old look read as a drawing:

1. **The ground** was large soft clouds of three tones (a noise with its finest octave at 4 art units) with a few tufts: at a tile of
   64 pixels it looked blurred and blotchy, and nothing in it was smaller than a few pixels.
2. **Every object, person and creature** had a dark outline and a hard shade: the signs of a cartoon.
3. **Matter** (wood, bark, stone, cloth, hair, fur, water) was a tint broken by soft clouds, never a grain, a fibre or a strand.

Painted bitmaps would answer all three, but they bring back everything ADR 0013 refused (a decoder, tens of megabytes, one size, no
palette variants).

## Decision

The art stays vector recipes drawn by the same rasterizers, and becomes realistic in three steps:

- **The rasterizer gains two options of the noise fill** (spec 13, v3), in the reference and in both clients, with probes of their
  own: `scale_y` (and `period_y`) **stretches** the clouds along one axis, which gives the fibres of wood, the blades of grass, the
  strands of hair, the fur of a beast and the ripples of sand and water; `ridged` **folds** every octave around its middle into thin
  creases, which gives cracks, veins, the furrows of bark and the net of light on the bottom of water.
- **The ground is painted again** (`tools/art_tiles.py`): five noise layers shared by every variant of a ground (the land, its patches,
  its matter, the lit tips of that matter, a grain finer than a pixel), then hundreds of small things per tile (blades, grit, pebbles,
  leaves, flowers) drawn in **batches** (one layer holds every blade of one tone of a tile), each with its contact shadow. The tiles
  have fewer layers than before and far more detail.
- **A finish** (`artkit.finish`) turns every object, person and creature into a painted picture without drawing it again: the outline
  of a filled shape becomes a faint edge, hard shades and lights get a soft edge, the colours lose a part of their saturation, a soft
  light from the top left and its shade give the picture a volume, and a fine grain covers it. On top of it the generators add the
  matter of what they draw: leaves and bark for the trees, strands for the hair, a weave for the cloth, fur for the beasts, scratches and
  rust for the armours. Faces have the proportions of a real face (smaller almond eyes, a nose, lips).
- **People have the proportions of a real body**, a little short and with a generous head so that they stay pleasant (six heads
  instead of 4.6, 56 units tall): every part of the rig and every look of it is
  drawn as before and then warped (`PROPORTIONS` in `tools/art_chars.py`): a smaller head, a neck, shoulders that slope, a waist,
  arms to the middle of the thigh, legs of half the height; the joints of the rig follow. The clips do not change.

## Consequences

- No new dependency and no bitmap: the pack grows by a few hundred kilobytes of recipes, the art still scales with the screen and the
  variants still work.
- The noise of v3 is specified to the bit like that of v2; old recipes draw as before (the defaults of the new options are the old
  behaviour).
- Baking costs a little more per pixel (more octaves of noise) and less per recipe (fewer layers); the budget of the textures of every
  quality level does not change, because no canvas grows.
- The smoke-test frames of the desktop CI are written again from the frames of the new art.
- A new recipe follows `docs/design/art-style.md`: a ground is the five layers and batches of small things; an object, a person or a
  creature gets the finish of its generator and the matter of what it is.
