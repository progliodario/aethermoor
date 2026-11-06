"""Reference sound synthesizer (spec 14): renders a sound effect recipe to 16 bit samples at 22050 Hz."""
from __future__ import annotations

import math

SAMPLE_RATE = 22050


def _xorshift(state: int) -> int:
    state ^= (state << 13) & 0xFFFFFFFF
    state ^= state >> 17
    state ^= (state << 5) & 0xFFFFFFFF
    return state & 0xFFFFFFFF


def render(recipe: dict) -> list[int]:
    n = recipe["duration_ms"] * SAMPLE_RATE // 1000
    master = recipe["volume_pm"] / 1000.0
    mix = [0.0] * n
    for layer in recipe["layers"]:
        wave = layer["wave"]
        fs, fe = float(layer["freq_start"]), float(layer["freq_end"])
        ratio_log = math.log(fe / fs)
        duty = layer.get("duty_pm", 500)
        attack, decay = float(layer["attack_ms"]), float(layer["decay_ms"])
        volume = layer["volume_pm"] / 1000.0
        phase = 0.0
        state = 2463534242
        held = 0.0
        wrapped = True
        for i in range(n):
            t = i / n
            freq = fs if fs == fe else fs * math.exp(t * ratio_log)
            if wave == "sine":
                w = math.sin(2.0 * math.pi * phase)
            elif wave == "square":
                w = 1.0 if phase * 1000.0 < duty else -1.0
            elif wave == "saw":
                w = 2.0 * phase - 1.0
            elif wave == "triangle":
                w = 4.0 * abs(phase - 0.5) - 1.0
            else:
                if wrapped:
                    state = _xorshift(state)
                    held = (state - 0x100000000 if state >= 0x80000000 else state) / 2147483648.0
                w = held
            phase += freq / SAMPLE_RATE
            wrapped = phase >= 1.0
            if wrapped:
                phase -= 1.0
            ms = i * 1000.0 / SAMPLE_RATE
            env = ms / attack if ms < attack else max(0.0, 1.0 - (ms - attack) / decay)
            mix[i] += w * env * volume
    out = []
    for v in mix:
        x = max(-1.0, min(1.0, v * master))
        out.append(math.floor(x * 32767.0 + 0.5))
    return out
