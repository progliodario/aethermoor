#!/usr/bin/env python3
"""Writes the seasonal visitors of the fauna (spec 09, "Seasonal visitors") into the world data.

A fauna entry may have `seasons`: a list of `{season, enemy, pm}`. On a day of that season, the spawners whose pick is that entry make the
visitor instead, those whose `(hash64(seed, x, y, 13) >> 20) % 1000 < pm`; the others make the creature of the entry. The visitors are
creatures that already live somewhere in the world (the slimes of the cold come down to Verdalis in winter, the bloom slimes open in the
short summer of Frostveil...), or the two creatures that live only in a season (the snow slime of winter, the sun slime of summer),
so that a quest that asks for the creature of the entry can always be done: at most 400 per mille swap.

It changes `data/base/worlds/overworld.json` in place, entry by entry (the lines of the regions keep their form). It can be run any number
of times. Then run `gen_conformance.py` (the vectors carry the world data), `make_catalog.py` and `make_facts.py`.
"""
from __future__ import annotations

import json
import re

from make_towns import DATA

WORLD = DATA / "worlds" / "overworld.json"
PM = 400
# region: [(creature of the entry, season, visitor)]
VISITORS = {
    "verdalis": [("slime_green", "winter", "slime_blue"), ("wolf_tawny", "autumn", "wolf_grey"), ("slime_bloom", "winter", "slime_snow"),
                 ("slime_bloom", "summer", "slime_sun")],
    "whisperwood": [("wolf_grey", "winter", "wolf_frost"), ("slime_green", "spring", "slime_bloom")],
    "ironspine": [("slime_blue", "winter", "slime_ice"), ("wolf_grey", "winter", "wolf_frost")],
    "sunscar": [("slime_green", "summer", "slime_sand"), ("dune_fox", "winter", "wolf_grey"), ("slime_sand", "summer", "slime_sun")],
    "frostveil": [("slime_green", "summer", "slime_bloom"), ("slime_blue", "spring", "slime_tide"), ("slime_blue", "winter", "slime_snow")],
    "tidehaven": [("wild_boar", "summer", "shore_crab"), ("slime_green", "winter", "slime_blue")],
    "ashen_wastes": [("slime_green", "summer", "slime_ember"), ("dune_fox", "autumn", "wolf_ember")],
    "lumeria": [("slime_green", "spring", "slime_bloom"), ("wolf_grey", "winter", "wolf_storm"), ("slime_blue", "winter", "slime_snow"),
                ("slime_blue", "summer", "slime_sun")],
}


def main() -> None:
    raw = WORLD.read_text(encoding="utf-8", newline="")
    count = 0
    for region, visitors in VISITORS.items():
        start = raw.index(f'{{ "id": "{region}", "name": "$i18n:region.')
        end = raw.index("\n", start)
        line = raw[start:end]
        for creature, season, visitor in visitors:
            pattern = re.compile(r'\{ "enemy": "base:enemy/' + creature + r'", "drop": "([^"]+)", "weight": (\d+)(, "seasons": \[[^\]]*\])? \}')
            found = pattern.search(line)
            assert found is not None, (region, creature)
            seasons = json.loads(found.group(3)[len(', "seasons": '):]) if found.group(3) else []
            seasons = [s for s in seasons if s["season"] != season] + [{"season": season, "enemy": f"base:enemy/{visitor}", "pm": PM}]
            text = ", ".join(f'{{ "season": "{s["season"]}", "enemy": "{s["enemy"]}", "pm": {s["pm"]} }}' for s in seasons)
            entry = f'{{ "enemy": "base:enemy/{creature}", "drop": "{found.group(1)}", "weight": {found.group(2)}, "seasons": [{text}] }}'
            line = line[:found.start()] + entry + line[found.end():]
            count += 1
        raw = raw[:start] + line + raw[end:]
    WORLD.write_text(raw, encoding="utf-8", newline="")
    print(f"wrote {count} seasonal visitors in {len(VISITORS)} regions")


if __name__ == "__main__":
    main()
