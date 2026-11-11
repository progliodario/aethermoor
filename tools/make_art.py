#!/usr/bin/env python3
"""Writes the art recipes of data/base/art/ that are made by code: the terrain tiles and the props (more kinds come with the next steps).

    python tools/make_art.py [tiles] [props] [--show]

The recipes are plain JSON (`schemas/art_recipe.schema.json`); this script only builds them with `tools/artkit.py` so that the
details (hundreds of blades, pebbles, planks) do not have to be written by hand. The style rules are in `docs/design/art-style.md`.
Run `python tools/art_preview.py <pattern>` to look at the result, `python tools/validate_data.py` to check it.
"""
from __future__ import annotations

import sys

from art_props import build_props  # noqa: E402
from art_tiles import build_tiles  # noqa: E402
from artkit import ART  # noqa: E402

def main() -> int:
    what = [a for a in sys.argv[1:] if not a.startswith("--")] or ["tiles"]
    count = 0
    if "tiles" in what:
        for r in build_tiles():
            r.write(ART / "tiles" / (r.id.rsplit("/", 1)[1] + ".json"))
            count += 1
    if "props" in what:
        for r in build_props():
            r.write(ART / "props" / (r.id.rsplit("/", 1)[1] + ".json"))
            count += 1
    print(f"wrote {count} recipes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
