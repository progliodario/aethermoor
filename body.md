## Another big batch: the night hides you, four creatures, long shadows, snow, no more baking freezes

### Rules
- **The night hides you** (spec 08): `aggro *= (1000 - (1000 - light_pm) * night_aggro_cut_pm / 1000) / 1000`, after the rain. Reference, three scenarios (`night_hides`, `night_dusk`, `night_and_rain`), desktop and Android. 250 in the base world.

### Content
- `tools/make_wildlife.py`: blossom slime, hollow armor, frost wisp, cinder wolf (enemies, art by family in `art_creatures.py`, names it/en, fauna of five regions), the ember pelt and the cinder cloak with its recipe. 75 creatures, 187 items, 51 recipes. Catalog and balance report regenerated.

### Presentation (both clients)
- **Long shadows** of props and creatures at dawn and dusk (`shadow_pm`).
- **Snow** instead of rain in the regions of `snow_regions` (Frostveil).
- **Baking in instalments** (spec 13): after three warm frames a frame bakes for 6 ms (desktop) or 8 ms (Android) at most; what is not ready appears in a later frame.

### Checked
- `validate_data.py`, `ruff`, `pytest tools/tests`, `gen_conformance.py --check` locally; the new creatures were looked at with `tools/art_preview.py`.
- Desktop and Android **not** built locally: CI is the build. Shadows, snow and the night are not in the smoke-test screenshots (they are taken by day in Verdalis): not seen on screen.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
