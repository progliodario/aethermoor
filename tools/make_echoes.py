#!/usr/bin/env python3
"""Writes the personal bosses of the protagonists, the Echoes: one creature for each protagonist, the shape of their old world's worst
moment, waiting in a sanctum of the ring of eight around the start (spec 18, "Personal bosses").

For each Echo: an art recipe (the art of a guardian, recoloured pale and violet: `ECHO_TINT`), an enemy, its names, and a landmark in the world
data. The sanctum stamps are built by `make_stamps.py` from `ECHOES` (the legend character of each boss). Run this, then `make_stamps.py`,
then `make_stories.py` (the fourth act sends each protagonist to their Echo), then `gen_conformance.py`."""
from __future__ import annotations

import json
import re

from make_towns import DATA, WORLD, set_texts

ECHO_TINT = (184, 166, 255)  # every colour of the art is mixed with this lavender, then lightened: the Echoes look like ghosts
TINT_PCT = 45
LIGHTEN_PCT = 20

# protagonist: (legend char, art of the guardian it copies, sound family, element, level, hp, atk, def, mdef, speed_x100, radius_x100,
#               sanctum (dx, dy), name en, name it, sanctum name)
ECHOES = {
    "ren": ("<", "vault_warden", "knight", "none", 24, 1140, 52, 24, 18, 260, 60, (-640, -384), "The Overtime", "Lo Straordinario", "Sanctum of Numbers"),
    "sakura": (">", "nebula_heart", "matron", "light", 24, 1220, 50, 16, 26, 260, 56, (-640, 384), "The Unfinished Equation", "L'Equazione Incompiuta", "Sanctum of Light"),
    "daichi": ("[", "magma_heart", "matron", "fire", 24, 1170, 54, 20, 14, 250, 58, (-384, -640), "The Third Floor", "Il Terzo Piano", "Sanctum of Embers"),
    "haruka": ("]", "moonshade_alpha", "alpha", "water", 24, 1200, 50, 18, 18, 340, 52, (-384, 640), "The Rain on the Road", "La Pioggia sulla Strada", "Sanctum of Rain"),
    "marco": ("{", "forge_tyrant", "knight", "fire", 24, 1150, 53, 23, 12, 260, 60, (384, -640), "The Sealed Pot", "La Pentola Sigillata", "Sanctum of Steam"),
    "yuki": ("}", "pearl_empress", "matron", "dark", 24, 1210, 52, 17, 20, 280, 54, (384, 640), "The Last Frame", "L'Ultima Cornice", "Sanctum of Frames"),
    "lena": ("|", "rime_revenant", "knight", "water", 24, 1160, 52, 21, 20, 250, 58, (640, -384), "The Final Report", "Il Referto Finale", "Sanctum of Silence"),
    "gideon": ("`", "char_tyrant", "king", "dark", 24, 1160, 55, 22, 18, 260, 62, (640, 384), "The Throne That Was", "Il Trono che Fu", "Sanctum of Ash"),
}
DROPS = [("potion_large", 2, 3, 1000), ("potion_mana_medium", 1, 2, 1000)]


def tint(match: re.Match) -> str:
    value = match.group(0)
    r, g, b = (int(value[i:i + 2], 16) for i in (1, 3, 5))
    out = []
    for c, t in zip((r, g, b), ECHO_TINT):
        mixed = c + (t - c) * TINT_PCT // 100
        out.append(min(255, mixed + (255 - mixed) * LIGHTEN_PCT // 100))
    return "#{:02X}{:02X}{:02X}".format(*out) + value[7:]


def main() -> None:
    names_en, names_it = {}, {}
    for who, (_, art, sound, element, level, hp, atk, df, mdf, speed, radius, _, name_en, name_it, _) in ECHOES.items():
        source = (DATA / "art" / "creatures" / f"{art}.json").read_text(encoding="utf-8")
        recipe = json.loads(re.sub(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?\b", tint, source))
        recipe["id"] = f"base:art/creature/echo_{who}"
        (DATA / "art" / "creatures" / f"echo_{who}.json").write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        enemy = {
            "$schema": "../../../schemas/enemy.schema.json", "id": f"base:enemy/echo_{who}", "name": f"$i18n:enemy.echo_{who}.name", "level": level,
            "stats": {"hp": hp, "atk": atk, "def": df, "mdef": mdf, "speed_x100": speed}, "element": element, "stagger_pct": 20, "sound": sound,
            "xp": level * 60,
            "drops": [{"item": f"base:item/{item}", "qty_min": lo, "qty_max": hi, "weight_pm": w} for item, lo, hi, w in DROPS],
            "radius_x100": radius, "behavior": "base:behavior/guardian", "art": f"base:art/creature/echo_{who}",
        }
        (DATA / "enemies" / f"echo_{who}.json").write_text(json.dumps(enemy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        names_en[f"enemy.echo_{who}.name"], names_it[f"enemy.echo_{who}.name"] = name_en, name_it
    set_texts("content.json", "en", names_en)
    set_texts("content.json", "it", names_it)

    # the sanctums in `landmarks` of the world data: replaced when there, added after the last landmark otherwise
    raw = WORLD.read_text(encoding="utf-8", newline="")
    newline = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.replace("\r\n", "\n").split("\n")
    for who, entry in ECHOES.items():
        dx, dy = entry[11]
        landmark = {"id": f"sanctum_{who}", "name": entry[14], "stamp": f"base:stamp/sanctum_{who}", "kind": "dungeon", "dx": dx, "dy": dy}
        text = "    { " + ", ".join(f"{json.dumps(k)}: {json.dumps(v)}" for k, v in landmark.items()) + " }"
        found = [k for k, line in enumerate(lines) if f'"id": "sanctum_{who}"' in line]
        if found:
            lines[found[0]] = text + ("," if lines[found[0]].rstrip().endswith(",") else "")
            continue
        start = next(k for k, line in enumerate(lines) if line.strip().startswith('"landmarks": ['))
        last = next(k for k in range(start, len(lines)) if lines[k].strip().startswith("]")) - 1
        lines[last] = lines[last].rstrip() + ","
        lines.insert(last + 1, text)
    WORLD.write_text(newline.join(lines), encoding="utf-8", newline="")
    print(f"wrote {len(ECHOES)} Echoes")


if __name__ == "__main__":
    main()
