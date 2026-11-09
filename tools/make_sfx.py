#!/usr/bin/env python3
"""Writes the sound effects of the base pack (data/base/audio/sfx/*.json) and the table that says when each plays
(data/base/audio/events.json). Spec 14. Run it after changing a recipe here.

A sound is a few layers (a wave, a glide in pitch, an envelope); the families below build many sounds from a few ideas: one
footstep per ground, four voices per creature, a set of interface sounds, the ambience of each region...
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "base" / "audio"

Sound = tuple[int, int, list[dict], bool]  # duration_ms, master volume, layers, loop
SOUNDS: dict[str, Sound] = {}


def L(wave: str, f0: int, f1: int, vol: int, attack: int, decay: int, duty: int | None = None, am: tuple[int, int] | None = None) -> dict:
    out = {"wave": wave, "freq_start": max(20, min(10000, f0)), "freq_end": max(20, min(10000, f1)), "volume_pm": vol, "attack_ms": attack, "decay_ms": max(1, decay)}
    if duty is not None:
        out["duty_pm"] = duty
    if am is not None:
        out["am_dhz"], out["am_depth_pm"] = am
    return out


def add(name: str, duration: int, volume: int, layers: list[dict], loop: bool = False) -> None:
    assert name not in SOUNDS, name
    SOUNDS[name] = (duration, volume, layers, loop)


def shift(layers: list[dict], pct: int) -> list[dict]:
    """The same layers a few percent higher or lower in pitch: a variant."""
    out = []
    for layer in layers:
        copy = dict(layer)
        copy["freq_start"] = max(20, min(10000, layer["freq_start"] * (100 + pct) // 100))
        copy["freq_end"] = max(20, min(10000, layer["freq_end"] * (100 + pct) // 100))
        out.append(copy)
    return out


def variants(name: str, duration: int, volume: int, layers: list[dict], count: int = 3) -> None:
    for i, pct in enumerate((0, 9, -8, 14, -13)[:count]):
        add(f"{name}_{'abcde'[i]}", duration, volume, shift(layers, pct))


# ------------------------------------------------------------------------------------------------ the player
variants("swing", 130, 500, [L("noise", 5200, 1400, 800, 12, 110), L("triangle", 520, 180, 250, 4, 100)])
add("power", 420, 850, [L("saw", 120, 460, 600, 40, 360), L("noise", 900, 3200, 400, 80, 300), L("sine", 90, 60, 500, 0, 380)])
add("dodge", 190, 450, [L("noise", 2200, 700, 650, 20, 160), L("sine", 300, 700, 250, 20, 160)])
variants("hurt", 260, 800, [L("saw", 330, 90, 700, 0, 230), L("noise", 1800, 300, 450, 1, 160)])
add("parry", 320, 850, [L("noise", 4500, 1800, 700, 0, 120), L("triangle", 1500, 1500, 500, 0, 260), L("triangle", 2250, 2250, 300, 0, 200), L("sine", 90, 60, 450, 0, 180)])
add("death", 900, 800, [L("saw", 392, 98, 600, 0, 880), L("square", 196, 49, 450, 0, 880, 500), L("noise", 800, 120, 200, 0, 700)])
add("crit", 300, 850, [L("noise", 4200, 500, 800, 1, 220), L("square", 330, 80, 600, 0, 200, 250), L("sine", 1320, 880, 400, 2, 260)])
add("weak", 380, 700, [L("sine", 1568, 1568, 500, 0, 300), L("sine", 2093, 2093, 400, 40, 330), L("triangle", 784, 784, 300, 0, 260)])
add("level_up", 700, 700, [L("square", 523, 523, 450, 0, 160, 250), L("square", 659, 659, 450, 160, 160, 250), L("square", 784, 784, 450, 320, 160, 250), L("square", 1047, 1047, 500, 480, 220, 250)])
add("heartbeat", 420, 800, [L("sine", 70, 45, 900, 2, 110), L("sine", 62, 40, 700, 190, 140)])
add("death_save", 900, 700, [L("sine", 523, 523, 400, 0, 800), L("sine", 659, 659, 350, 60, 780), L("sine", 784, 784, 350, 120, 760), L("sine", 1047, 1047, 300, 180, 700)])

# ------------------------------------------------------------------------------------------------ footsteps
STEPS = {
    "grass": [L("noise", 1300, 600, 450, 4, 70), L("sine", 95, 70, 300, 0, 60)],
    "dirt": [L("noise", 900, 380, 500, 3, 65), L("sine", 110, 75, 350, 0, 60)],
    "sand": [L("noise", 2600, 1500, 330, 12, 95)],
    "snow": [L("noise", 3600, 1200, 380, 6, 105), L("noise", 1500, 700, 250, 20, 100)],
    "stone": [L("noise", 2200, 700, 420, 1, 40), L("triangle", 190, 120, 380, 0, 55)],
    "wood": [L("triangle", 210, 150, 480, 0, 70), L("noise", 1500, 600, 300, 1, 45)],
    "water": [L("noise", 900, 2400, 400, 12, 130), L("sine", 620, 280, 260, 0, 120)],
    "moss": [L("noise", 700, 350, 400, 6, 85), L("sine", 85, 60, 280, 0, 70)],
    "ash": [L("noise", 1500, 520, 400, 3, 75), L("square", 90, 60, 160, 0, 50, 500)],
}
for ground, layers in STEPS.items():
    variants(f"step_{ground}", 110, 600, layers)

# ------------------------------------------------------------------------------------------------ creatures
# name -> (aggro, attack, hit, die), each a (duration, volume, layers)
CREATURES: dict[str, list[tuple[int, int, list[dict]]]] = {
    "slime": [(260, 500, [L("sine", 260, 420, 600, 40, 220, am=(60, 500)), L("noise", 700, 1200, 150, 40, 200)]),
              (200, 600, [L("sine", 210, 80, 700, 5, 190), L("noise", 1200, 300, 300, 0, 130)]),
              (170, 650, [L("sine", 520, 190, 650, 0, 160), L("square", 260, 140, 200, 0, 120, 500)]),
              (380, 650, [L("sine", 420, 55, 700, 0, 360), L("noise", 1600, 250, 350, 0, 220)])],
    "matron": [(340, 600, [L("sine", 150, 210, 650, 60, 280, am=(50, 400)), L("triangle", 300, 420, 250, 60, 270)]),
               (260, 700, [L("sine", 160, 60, 750, 5, 240), L("noise", 900, 250, 350, 0, 160)]),
               (220, 700, [L("sine", 330, 130, 650, 0, 200), L("triangle", 660, 260, 250, 0, 160)]),
               (620, 750, [L("sine", 260, 40, 700, 0, 600), L("triangle", 520, 80, 300, 0, 550), L("noise", 1200, 150, 300, 0, 350)])],
    "king": [(520, 750, [L("sine", 90, 130, 700, 80, 440, am=(40, 500)), L("saw", 180, 260, 250, 80, 430)]),
             (360, 800, [L("saw", 110, 45, 700, 5, 320), L("noise", 700, 150, 400, 0, 250)]),
             (260, 800, [L("sine", 220, 90, 700, 0, 240), L("saw", 140, 70, 350, 0, 220)]),
             (1000, 850, [L("sine", 180, 30, 700, 0, 960), L("saw", 90, 30, 400, 0, 900), L("noise", 800, 100, 350, 0, 700)])],
    "wolf": [(420, 600, [L("saw", 110, 85, 600, 60, 360, am=(70, 500)), L("noise", 400, 300, 160, 50, 330)]),
             (210, 700, [L("saw", 360, 160, 700, 0, 190), L("noise", 2500, 600, 450, 0, 120)]),
             (230, 700, [L("saw", 520, 220, 650, 0, 210), L("sine", 780, 300, 300, 0, 160)]),
             (560, 750, [L("saw", 430, 70, 650, 0, 540), L("sine", 215, 60, 300, 0, 520)])],
    "alpha": [(800, 800, [L("sine", 220, 520, 700, 150, 640, am=(40, 300)), L("saw", 110, 260, 300, 150, 640)]),
              (260, 800, [L("saw", 260, 100, 750, 0, 240), L("noise", 2000, 400, 450, 0, 160)]),
              (260, 800, [L("saw", 400, 150, 700, 0, 240), L("sine", 600, 200, 300, 0, 200)]),
              (900, 850, [L("saw", 380, 50, 700, 0, 880), L("sine", 190, 40, 350, 0, 800)])],
    "knight": [(300, 600, [L("square", 90, 80, 500, 10, 280, 400), L("noise", 3000, 1500, 200, 0, 140)]),
               (240, 750, [L("noise", 2800, 500, 550, 0, 140), L("triangle", 740, 520, 450, 0, 220)]),
               (220, 750, [L("sine", 1250, 980, 500, 0, 220), L("noise", 3500, 900, 350, 0, 100), L("triangle", 625, 490, 300, 0, 200)]),
               (700, 800, [L("noise", 2600, 200, 550, 0, 600), L("square", 160, 40, 450, 0, 650, 500), L("triangle", 900, 300, 250, 0, 300)])],
    "bat": [(200, 450, [L("sine", 3500, 4800, 500, 5, 170, am=(180, 600))]),
            (180, 550, [L("saw", 2600, 1500, 450, 0, 160), L("noise", 4500, 2500, 200, 0, 100)]),
            (150, 550, [L("sine", 3200, 1700, 500, 0, 140)]),
            (320, 600, [L("sine", 4200, 600, 500, 0, 300), L("noise", 4000, 800, 200, 0, 200)])],
    "spider": [(260, 450, [L("noise", 6000, 4200, 400, 40, 210)]),
               (150, 600, [L("noise", 5000, 1500, 500, 0, 110), L("square", 1800, 900, 250, 0, 90, 300)]),
               (130, 600, [L("square", 1500, 700, 450, 0, 110, 250)]),
               (360, 600, [L("noise", 4200, 500, 450, 0, 340), L("square", 900, 200, 200, 0, 260, 250)])],
    "scorpion": [(220, 450, [L("square", 900, 800, 400, 0, 200, 300, am=(220, 900))]),
                 (150, 650, [L("noise", 4000, 1500, 550, 0, 120), L("square", 1200, 500, 300, 0, 100, 250)]),
                 (140, 600, [L("square", 1100, 600, 450, 0, 120, 300)]),
                 (340, 650, [L("noise", 3000, 400, 450, 0, 320), L("square", 800, 150, 250, 0, 280, 300)])],
    "crab": [(200, 450, [L("triangle", 800, 800, 450, 0, 180, am=(200, 1000))]),
             (140, 600, [L("square", 700, 350, 550, 0, 120, 200), L("noise", 3000, 1500, 250, 0, 80)]),
             (130, 600, [L("triangle", 1000, 500, 500, 0, 110), L("noise", 2500, 900, 250, 0, 70)]),
             (360, 600, [L("triangle", 600, 120, 450, 0, 340), L("noise", 2000, 300, 300, 0, 250)])],
    "owl": [(520, 550, [L("sine", 420, 380, 600, 30, 200), L("sine", 400, 340, 600, 280, 220)]),
            (220, 600, [L("noise", 2000, 900, 400, 40, 180), L("sine", 800, 500, 250, 20, 170)]),
            (200, 600, [L("sine", 760, 420, 550, 0, 190)]),
            (460, 650, [L("sine", 520, 130, 550, 0, 440), L("noise", 1400, 300, 200, 0, 300)])],
    "myconid": [(280, 450, [L("noise", 700, 500, 350, 80, 190), L("sine", 140, 170, 350, 60, 200)]),
                (200, 600, [L("noise", 1200, 300, 450, 0, 150), L("sine", 180, 90, 450, 0, 150)]),
                (170, 600, [L("sine", 380, 160, 500, 0, 160), L("noise", 900, 400, 250, 0, 120)]),
                (420, 600, [L("sine", 300, 60, 500, 0, 400), L("noise", 800, 200, 300, 0, 300)])],
    "golem": [(480, 600, [L("saw", 55, 45, 700, 80, 400), L("noise", 200, 150, 250, 80, 380)]),
              (300, 850, [L("saw", 70, 40, 750, 0, 280), L("noise", 600, 120, 500, 0, 220)]),
              (240, 800, [L("noise", 1400, 200, 550, 0, 220), L("square", 110, 60, 450, 0, 200, 500)]),
              (900, 850, [L("noise", 900, 100, 550, 0, 860), L("saw", 60, 30, 500, 0, 880)])],
    "wisp": [(400, 450, [L("sine", 1200, 1800, 450, 60, 330, am=(80, 700)), L("sine", 1800, 2400, 250, 80, 300)]),
             (220, 550, [L("sine", 1500, 600, 500, 0, 200, am=(120, 600))]),
             (180, 550, [L("sine", 2000, 1100, 450, 0, 170)]),
             (500, 600, [L("sine", 1800, 300, 450, 0, 480, am=(100, 800)), L("sine", 2400, 600, 200, 0, 450)])],
}
for family, rows in CREATURES.items():
    for kind, (duration, volume, layers) in zip(("aggro", "attack", "hit", "die"), rows, strict=True):
        add(f"{family}_{kind}", duration, volume, layers)

# ------------------------------------------------------------------------------------------------ the bag and the shops
add("pickup", 180, 600, [L("square", 880, 1320, 500, 0, 150, 300), L("sine", 1760, 1760, 250, 0, 120)])
add("coin", 240, 600, [L("square", 1318, 1318, 500, 0, 70, 250), L("square", 1976, 1976, 500, 70, 160, 250)])
add("buy", 420, 600, [L("square", 1318, 1318, 450, 0, 60, 250), L("square", 1976, 1976, 450, 60, 80, 250), L("square", 1318, 1318, 400, 160, 60, 250), L("square", 1976, 1976, 450, 220, 190, 250)])
add("sell", 320, 600, [L("square", 1976, 1976, 450, 0, 70, 250), L("square", 1318, 1318, 450, 70, 70, 250), L("square", 1760, 1760, 400, 140, 180, 250)])
add("equip_weapon", 260, 650, [L("noise", 4500, 2500, 450, 10, 160), L("triangle", 1500, 900, 300, 0, 230), L("sine", 2300, 2300, 200, 80, 170)])
add("equip_armor", 280, 600, [L("noise", 1500, 500, 500, 20, 220), L("triangle", 260, 180, 350, 0, 150), L("noise", 3000, 1500, 150, 150, 100)])
add("use_heal", 520, 600, [L("sine", 523, 523, 350, 0, 200), L("sine", 659, 659, 350, 100, 200), L("sine", 784, 784, 350, 200, 200), L("sine", 1047, 1047, 350, 300, 220)])
add("use_mana", 560, 600, [L("sine", 1200, 2000, 350, 20, 500, am=(90, 700)), L("sine", 1800, 2600, 200, 60, 480, am=(130, 700))])
add("use_other", 220, 550, [L("noise", 1600, 800, 350, 10, 120), L("sine", 440, 660, 300, 0, 180)])
add("eat", 300, 500, [L("noise", 1800, 700, 450, 0, 70), L("noise", 1800, 700, 450, 110, 70), L("noise", 1800, 700, 350, 210, 70)])

# ------------------------------------------------------------------------------------------------ the interface
add("ui_move", 60, 400, [L("square", 1200, 1200, 400, 0, 55, 500)])
add("ui_confirm", 110, 500, [L("square", 740, 988, 500, 0, 95, 400)])
add("ui_back", 110, 450, [L("square", 740, 494, 450, 0, 95, 400)])
add("ui_error", 200, 450, [L("square", 150, 150, 500, 0, 180, 500), L("square", 155, 155, 400, 0, 180, 500)])
add("open_bag", 260, 500, [L("noise", 1800, 700, 350, 10, 120), L("triangle", 300, 520, 400, 5, 200), L("noise", 3500, 2000, 150, 140, 100)])
add("close_bag", 200, 500, [L("triangle", 520, 280, 400, 5, 170), L("noise", 1400, 500, 300, 5, 100)])
add("open_map", 380, 500, [L("noise", 2200, 900, 350, 40, 320, am=(60, 600)), L("triangle", 400, 600, 150, 40, 300)])
add("close_map", 280, 500, [L("noise", 1800, 700, 350, 20, 240, am=(60, 600))])
add("open_journal", 320, 500, [L("noise", 3200, 1500, 400, 10, 100), L("noise", 2800, 1200, 350, 140, 150), L("triangle", 350, 480, 200, 0, 260)])
add("close_journal", 220, 500, [L("noise", 2600, 1000, 400, 5, 160), L("triangle", 480, 300, 250, 0, 150)])
add("open_shop", 400, 550, [L("triangle", 1568, 1568, 300, 0, 300), L("triangle", 2093, 2093, 300, 80, 300), L("noise", 3500, 2500, 150, 0, 200)])
add("close_shop", 240, 500, [L("triangle", 1568, 1568, 300, 0, 180), L("triangle", 1175, 1175, 300, 70, 160)])
add("open_board", 360, 500, [L("noise", 2400, 1000, 350, 10, 200), L("square", 392, 392, 250, 0, 220, 300), L("square", 523, 523, 250, 100, 240, 300)])
add("close_board", 220, 500, [L("square", 523, 523, 250, 0, 120, 300), L("square", 392, 392, 250, 80, 140, 300)])
add("open_travel", 600, 600, [L("sine", 392, 392, 350, 40, 560), L("sine", 523, 523, 300, 80, 520), L("sine", 784, 784, 250, 120, 480, am=(60, 500))])
add("close_travel", 300, 500, [L("sine", 523, 392, 350, 0, 280)])
add("dialogue_open", 200, 450, [L("triangle", 440, 660, 450, 0, 180)])
add("dialogue_close", 180, 450, [L("triangle", 660, 440, 450, 0, 160)])
variants("dialogue_next", 70, 400, [L("square", 520, 520, 450, 0, 60, 500)])
add("tab", 80, 400, [L("square", 900, 1100, 400, 0, 70, 400)])

# ------------------------------------------------------------------------------------------------ quests and the world
add("quest_accept", 420, 650, [L("square", 523, 523, 450, 0, 140, 300), L("square", 784, 784, 450, 140, 260, 300)])
add("quest_progress", 260, 600, [L("sine", 1319, 1319, 450, 0, 240), L("sine", 1760, 1760, 300, 60, 200)])
add("quest_complete", 1100, 750, [L("square", 523, 523, 450, 0, 200, 250), L("square", 659, 659, 450, 200, 200, 250), L("square", 784, 784, 450, 400, 200, 250),
                                   L("square", 1047, 1047, 500, 600, 500, 250), L("sine", 1568, 1568, 300, 600, 480)])
add("region_enter", 900, 500, [L("sine", 392, 392, 300, 100, 780), L("sine", 494, 494, 250, 200, 680), L("sine", 587, 587, 250, 300, 580)])
add("stone_wake", 1400, 700, [L("sine", 220, 220, 400, 100, 1300), L("sine", 330, 330, 350, 150, 1250), L("sine", 440, 440, 300, 200, 1200, am=(40, 400)), L("sine", 660, 660, 250, 300, 1100)])
add("stone_travel", 900, 700, [L("noise", 400, 3000, 450, 200, 650), L("sine", 200, 1600, 450, 100, 780)])
add("rain_start", 700, 400, [L("noise", 3000, 4000, 350, 300, 400)])
add("rain_stop", 700, 400, [L("noise", 4000, 2000, 350, 20, 650)])
add("thunder_a", 2200, 800, [L("noise", 220, 60, 800, 80, 2100, am=(25, 700)), L("saw", 50, 30, 400, 0, 2000)])
add("thunder_b", 1700, 800, [L("noise", 300, 80, 800, 40, 1600, am=(35, 700)), L("saw", 60, 35, 350, 0, 1500)])
add("dawn", 1400, 450, [L("sine", 2400, 3000, 250, 0, 160), L("sine", 2800, 2200, 250, 300, 160), L("sine", 3200, 3600, 250, 650, 160), L("sine", 2600, 3100, 250, 950, 160)])
add("nightfall", 1600, 450, [L("sine", 196, 196, 400, 0, 1500), L("sine", 294, 294, 250, 0, 1400), L("sine", 392, 392, 150, 0, 1300)])

# ------------------------------------------------------------------------------------------------ the ambience (loops)
# Each lasts a whole number of cycles of its slow modulation, so that it repeats without a click.
AMBIENCE = {
    "amb_wind_soft": (8000, 600, [L("noise", 350, 350, 700, 0, 1, am=(25, 650)), L("noise", 700, 700, 250, 0, 1, am=(15, 800))]),
    "amb_wind_strong": (8000, 700, [L("noise", 450, 450, 800, 0, 1, am=(25, 700)), L("noise", 900, 900, 400, 0, 1, am=(35, 800))]),
    "amb_wind_desert": (8000, 600, [L("noise", 1100, 1100, 600, 0, 1, am=(25, 750)), L("noise", 600, 600, 300, 0, 1, am=(15, 600))]),
    "amb_wind_snow": (8000, 500, [L("noise", 600, 600, 450, 0, 1, am=(25, 800)), L("sine", 300, 340, 150, 0, 1, am=(25, 900))]),
    "amb_rain_light": (4000, 450, [L("noise", 2200, 2200, 600, 0, 1, am=(50, 200)), L("noise", 1300, 1300, 350, 0, 1, am=(75, 300))]),
    "amb_rain_heavy": (4000, 550, [L("noise", 1800, 1800, 800, 0, 1, am=(50, 250)), L("noise", 900, 900, 500, 0, 1, am=(25, 300))]),
    "amb_waves": (8000, 600, [L("noise", 600, 600, 650, 0, 1, am=(10, 950)), L("noise", 1800, 1800, 300, 0, 1, am=(10, 900))]),
    "amb_crickets": (4000, 250, [L("triangle", 2300, 2300, 400, 0, 1, am=(80, 950)), L("triangle", 2600, 2600, 250, 0, 1, am=(60, 950))]),
    "amb_birds": (8000, 250, [L("triangle", 1500, 2100, 450, 0, 1, am=(10, 990)), L("triangle", 1300, 1800, 300, 0, 1, am=(15, 990))]),
    "amb_leaves": (8000, 300, [L("noise", 900, 900, 500, 0, 1, am=(25, 600)), L("noise", 1500, 1500, 250, 0, 1, am=(35, 700))]),
    "amb_crowd": (8000, 400, [L("noise", 380, 380, 600, 0, 1, am=(35, 500)), L("noise", 520, 520, 350, 0, 1, am=(15, 600))]),
    "amb_fire": (4000, 450, [L("noise", 1800, 1800, 500, 0, 1, am=(100, 900)), L("noise", 2500, 2500, 250, 0, 1, am=(175, 990))]),
    "amb_ash": (8000, 500, [L("noise", 220, 220, 700, 0, 1, am=(25, 500)), L("sine", 55, 55, 450, 0, 1, am=(25, 400))]),
    "amb_magic": (8000, 400, [L("sine", 330, 330, 400, 0, 1, am=(25, 600)), L("sine", 495, 495, 300, 0, 1, am=(15, 700)), L("sine", 660, 660, 200, 0, 1, am=(35, 700))]),
    "amb_cave": (8000, 500, [L("noise", 120, 120, 600, 0, 1, am=(25, 400)), L("sine", 80, 80, 350, 0, 1, am=(25, 300))]),
}
for name, (duration, volume, layers) in AMBIENCE.items():
    add(name, duration, volume, layers, loop=True)

# ------------------------------------------------------------------------------------------------ when each plays
FAMILIES = list(CREATURES)
EVENTS: dict[str, dict] = {
    "swing": {"sounds": ["swing_a", "swing_b", "swing_c"], "volume_pm": 900, "cooldown": 6},
    "power": {"sounds": ["power"], "volume_pm": 1000},
    "dodge": {"sounds": ["dodge"], "volume_pm": 900},
    "player.hurt": {"sounds": ["hurt_a", "hurt_b", "hurt_c"], "volume_pm": 1000, "cooldown": 8},
    "player.death": {"sounds": ["death"], "volume_pm": 1000},
    "player.parry": {"sounds": ["parry"], "volume_pm": 1000},
    "crit": {"sounds": ["crit"], "volume_pm": 900},
    "weak": {"sounds": ["weak"], "volume_pm": 800},
    "level_up": {"sounds": ["level_up"], "volume_pm": 1000},
    "heartbeat": {"sounds": ["heartbeat"], "volume_pm": 800},
    "death_save": {"sounds": ["death_save"], "volume_pm": 1000},
    "pickup": {"sounds": ["pickup"], "volume_pm": 900},
    "coin": {"sounds": ["coin"], "volume_pm": 900},
    "shop.buy": {"sounds": ["buy"], "volume_pm": 900},
    "shop.sell": {"sounds": ["sell"], "volume_pm": 900},
    "equip.weapon": {"sounds": ["equip_weapon"], "volume_pm": 900},
    "equip.armor": {"sounds": ["equip_armor"], "volume_pm": 900},
    "use.heal": {"sounds": ["use_heal"], "volume_pm": 900},
    "use.mana": {"sounds": ["use_mana"], "volume_pm": 900},
    "use.other": {"sounds": ["use_other"], "volume_pm": 800},
    "ui.move": {"sounds": ["ui_move"], "volume_pm": 700, "cooldown": 2},
    "dialogue.open": {"sounds": ["dialogue_open"], "volume_pm": 800},
    "dialogue.close": {"sounds": ["dialogue_close"], "volume_pm": 800},
    "dialogue.next": {"sounds": ["dialogue_next_a", "dialogue_next_b", "dialogue_next_c"], "volume_pm": 700},
    "quest.accept": {"sounds": ["quest_accept"], "volume_pm": 1000},
    "quest.complete": {"sounds": ["quest_complete"], "volume_pm": 1000},
    "stone.wake": {"sounds": ["stone_wake"], "volume_pm": 1000},
    "region.enter": {"sounds": ["region_enter"], "volume_pm": 700},
    "rain.start": {"sounds": ["rain_start"], "volume_pm": 700},
    "rain.stop": {"sounds": ["rain_stop"], "volume_pm": 700},
    "thunder": {"sounds": ["thunder_a", "thunder_b"], "volume_pm": 900},
    "dawn": {"sounds": ["dawn"], "volume_pm": 700},
    "nightfall": {"sounds": ["nightfall"], "volume_pm": 700},
}
for ground in STEPS:
    EVENTS[f"step.{ground}"] = {"sounds": [f"step_{ground}_{c}" for c in "abc"], "volume_pm": 700}
for family in FAMILIES:
    for kind in ("aggro", "attack", "hit", "die"):
        EVENTS[f"enemy.{family}.{kind}"] = {"sounds": [f"{family}_{kind}"], "volume_pm": 1000, **({"cooldown": 20} if kind == "aggro" else {})}
for panel, sounds in {"bag": ("open_bag", "close_bag"), "map": ("open_map", "close_map"), "journal": ("open_journal", "close_journal"),
                      "shop": ("open_shop", "close_shop"), "board": ("open_board", "close_board"), "travel": ("open_travel", "close_travel")}.items():
    EVENTS[f"ui.open.{panel}"] = {"sounds": [sounds[0]], "volume_pm": 800}
    EVENTS[f"ui.close.{panel}"] = {"sounds": [sounds[1]], "volume_pm": 800}

# What loops where: each region has its own air. `when` is `day`, `night` or `always`; `gain_pm` the loudness of the loop.
AMBIENCE_RULES = {
    "rain": {"light": "amb_rain_light", "heavy": "amb_rain_heavy", "silences": ["amb_birds", "amb_crickets"]},
    "regions": {
        "verdalis": [{"sound": "amb_birds", "when": "day", "gain_pm": 220}, {"sound": "amb_leaves", "gain_pm": 250}, {"sound": "amb_wind_soft", "gain_pm": 300},
                     {"sound": "amb_crickets", "when": "night", "gain_pm": 200}],
        "whisperwood": [{"sound": "amb_leaves", "gain_pm": 350}, {"sound": "amb_magic", "gain_pm": 250}, {"sound": "amb_crickets", "when": "night", "gain_pm": 200},
                        {"sound": "amb_birds", "when": "day", "gain_pm": 180}],
        "ironspine": [{"sound": "amb_wind_strong", "gain_pm": 650}, {"sound": "amb_cave", "gain_pm": 200}],
        "sunscar": [{"sound": "amb_wind_desert", "gain_pm": 650}, {"sound": "amb_crickets", "when": "night", "gain_pm": 200}],
        "frostveil": [{"sound": "amb_wind_snow", "gain_pm": 700}],
        "tidehaven": [{"sound": "amb_waves", "gain_pm": 700}, {"sound": "amb_wind_soft", "gain_pm": 350}, {"sound": "amb_birds", "when": "day", "gain_pm": 150}],
        "ashen_wastes": [{"sound": "amb_ash", "gain_pm": 650}, {"sound": "amb_fire", "gain_pm": 250}],
        "lumeria": [{"sound": "amb_magic", "gain_pm": 600}, {"sound": "amb_wind_soft", "gain_pm": 300}, {"sound": "amb_crickets", "when": "night", "gain_pm": 200}],
    },
}


def write() -> None:
    sfx = OUT / "sfx"
    sfx.mkdir(parents=True, exist_ok=True)
    for old in sfx.glob("*.json"):
        old.unlink()
    for name, (duration, volume, layers, loop) in SOUNDS.items():
        doc = {"$schema": "../../../../schemas/sfx_recipe.schema.json", "id": f"base:audio/sfx/{name}", "duration_ms": duration, "volume_pm": volume}
        if loop:
            doc["loop"] = True
        doc["layers"] = layers
        (sfx / f"{name}.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    for event, entry in EVENTS.items():
        for sound in entry["sounds"]:
            assert sound in SOUNDS, (event, sound)
    for rule in AMBIENCE_RULES["regions"].values():
        for entry in rule:
            assert entry["sound"] in SOUNDS
    table = {"$schema": "../../../schemas/audio_events.schema.json", "id": "base:audio/events", "events": EVENTS, "ambience": AMBIENCE_RULES}
    (OUT / "events.json").write_text(json.dumps(table, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(SOUNDS)} sounds and {len(EVENTS)} events")


if __name__ == "__main__":
    write()
