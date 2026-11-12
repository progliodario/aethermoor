## A big batch: the rest of the anime art list, rain that matters, new scenery to gather

Closes #181.

### Rules
- **Rain hides you** (spec 08): `aggro = aggro_x100 * gift.aggro_pct / 100 * (1000 - rain_pm * rain_aggro_cut_pm / 1000) / 1000`. Reference, three conformance scenarios (`rain_hides`, `rain_light`, `rain_and_gift`), desktop and Android. The base world cuts 30 percent in full rain.

### Content
- Seven new props that the world generation scatters (flowers, stump, fern, log, driftwood, ice shard, dry shrub), all gatherable; four materials, two dishes, four recipes (50). The world vectors are regenerated: props are not where they were.

### Presentation (both clients)
- **Android draws its text with the font of the pack** (`PackFont.kt`: every glyph baked into one texture, a libGDX `BitmapFont` built from the metrics of the font).
- **The blow**: a third clip, `humanoid_attack`, played during the phases of a skill.
- **Water moves**: the water picture drawn twice more, shifted by whole tiles, fading in and out.
- **Round corners** in the ground blending (diagonal neighbours).
- **Panels and bars** redrawn.

### Checked
- `validate_data.py`, `ruff`, `pytest tools/tests`, `gen_conformance.py --check`: run locally. The new props were looked at with `tools/art_preview.py`.
- Desktop and Android were **not** built locally: CI is the build. The Android font, in particular, has only been compiled, never seen on a device.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
