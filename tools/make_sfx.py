#!/usr/bin/env python3
"""Writes the sound effect recipes of the base pack (data/base/audio/sfx/*.json). Spec 14. Run it after changing a recipe here."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "base" / "audio" / "sfx"


def layer(wave: str, f0: int, f1: int, vol: int, attack: int, decay: int, duty: int | None = None) -> dict:
    out = {"wave": wave, "freq_start": f0, "freq_end": f1, "volume_pm": vol, "attack_ms": attack, "decay_ms": decay}
    if duty is not None:
        out["duty_pm"] = duty
    return out


SOUNDS: dict[str, tuple[int, int, list[dict]]] = {
    # name: (duration_ms, master volume, layers)
    "swing": (130, 500, [layer("noise", 5200, 1400, 800, 12, 110), layer("triangle", 520, 180, 250, 4, 100)]),
    "hit": (170, 800, [layer("noise", 3200, 380, 800, 1, 150), layer("square", 240, 70, 550, 0, 140, 500)]),
    "crit": (300, 850, [layer("noise", 4200, 500, 800, 1, 220), layer("square", 330, 80, 600, 0, 200, 250), layer("sine", 1320, 880, 400, 2, 260)]),
    "hurt": (260, 800, [layer("saw", 330, 90, 700, 0, 230), layer("noise", 1800, 300, 450, 1, 160)]),
    "dodge": (190, 450, [layer("noise", 2200, 700, 650, 20, 160), layer("sine", 300, 700, 250, 20, 160)]),
    "level_up": (700, 700, [layer("square", 523, 523, 450, 0, 160, 250), layer("square", 659, 659, 450, 160, 160, 250),
                            layer("square", 784, 784, 450, 320, 160, 250), layer("square", 1047, 1047, 500, 480, 220, 250)]),
    "pickup": (180, 600, [layer("square", 880, 1320, 500, 0, 150, 300), layer("sine", 1760, 1760, 250, 0, 120)]),
    "coin": (240, 600, [layer("square", 1318, 1318, 500, 0, 70, 250), layer("square", 1976, 1976, 500, 70, 160, 250)]),
    "open": (150, 500, [layer("triangle", 330, 660, 650, 5, 130), layer("noise", 1500, 600, 150, 2, 80)]),
    "close": (140, 500, [layer("triangle", 560, 280, 650, 5, 120), layer("noise", 1200, 500, 150, 2, 70)]),
    "confirm": (110, 500, [layer("square", 740, 988, 500, 0, 95, 400)]),
    "power": (420, 850, [layer("saw", 120, 460, 600, 40, 360), layer("noise", 900, 3200, 400, 80, 300), layer("sine", 90, 60, 500, 0, 380)]),
    "death": (900, 800, [layer("saw", 392, 98, 600, 0, 880), layer("square", 196, 49, 450, 0, 880, 500), layer("noise", 800, 120, 200, 0, 700)]),
    "enemy_die": (320, 700, [layer("square", 440, 80, 500, 0, 300, 500), layer("noise", 2400, 300, 450, 0, 250)]),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (duration, volume, layers) in SOUNDS.items():
        doc = {"$schema": "../../../../schemas/sfx_recipe.schema.json", "id": f"base:audio/sfx/{name}", "duration_ms": duration, "volume_pm": volume, "layers": layers}
        (OUT / f"{name}.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(SOUNDS)} sound effects")


if __name__ == "__main__":
    main()
