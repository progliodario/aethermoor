"""Conformance suite for the sound synthesizer (spec 14). Imported by gen_conformance.py.

Each case is a sound effect recipe and what its rendering must look like: the number of samples, the loudest sample, the mean of the
absolute values, and the value of a few samples. The clients compare with a small tolerance.
"""
from __future__ import annotations

from reference import audio


def _layer(wave: str, f0: int, f1: int, vol: int, attack: int, decay: int, duty: int | None = None) -> dict:
    out = {"wave": wave, "freq_start": f0, "freq_end": f1, "volume_pm": vol, "attack_ms": attack, "decay_ms": decay}
    if duty is not None:
        out["duty_pm"] = duty
    return out


def _case(name: str, duration: int, volume: int, layers: list[dict]) -> dict:
    recipe = {"id": f"test:audio/sfx/{name}", "duration_ms": duration, "volume_pm": volume, "layers": layers}
    samples = audio.render(recipe)
    n = len(samples)
    probes = [{"i": i, "value": samples[i]} for i in (0, n // 7, n // 4, n // 3, n // 2, (2 * n) // 3, (3 * n) // 4, n - 1)]
    return {
        "name": name,
        "input": {"op": "sfx", "recipe": recipe},
        "expect": {
            "samples": n,
            "peak": max(abs(s) for s in samples),
            "mean_abs": sum(abs(s) for s in samples) / n,
            "probes": probes,
        },
    }


def suite_audio() -> list[dict]:
    return [
        _case("sine_flat", 100, 1000, [_layer("sine", 440, 440, 1000, 0, 100)]),
        _case("sine_glide", 120, 800, [_layer("sine", 200, 1600, 900, 10, 110)]),
        _case("square_half", 80, 1000, [_layer("square", 330, 330, 800, 0, 80, 500)]),
        _case("square_thin", 80, 1000, [_layer("square", 330, 330, 800, 0, 80, 250)]),
        _case("saw_fall", 150, 700, [_layer("saw", 600, 100, 1000, 5, 145)]),
        _case("triangle_rise", 150, 700, [_layer("triangle", 100, 900, 1000, 20, 130)]),
        _case("noise_steps", 100, 900, [_layer("noise", 2000, 500, 1000, 0, 100)]),
        _case("noise_slow", 100, 900, [_layer("noise", 150, 150, 1000, 5, 95)]),
        _case("mix_clip", 90, 1000, [_layer("sine", 220, 220, 1000, 0, 90), _layer("square", 220, 220, 1000, 0, 90, 500), _layer("saw", 220, 220, 1000, 0, 90)]),
        _case("silent", 50, 0, [_layer("sine", 440, 440, 1000, 0, 50)]),
    ]
