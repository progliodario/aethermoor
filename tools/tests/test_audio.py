"""The reference synthesizer (spec 14) and the sound effects of the base pack."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reference import audio  # noqa: E402

SFX = Path(__file__).resolve().parent.parent.parent / "data" / "base" / "audio" / "sfx"


def test_length_and_range():
    recipe = {"id": "t:audio/sfx/x", "duration_ms": 100, "volume_pm": 1000,
              "layers": [{"wave": "sine", "freq_start": 440, "freq_end": 440, "volume_pm": 1000, "attack_ms": 0, "decay_ms": 100}]}
    samples = audio.render(recipe)
    assert len(samples) == 2205
    assert max(samples) <= 32767 and min(samples) >= -32767
    assert samples[0] == 0


def test_every_pack_sound_renders_audible_and_unclipped():
    files = sorted(SFX.glob("*.json"))
    assert files
    for path in files:
        samples = audio.render(json.loads(path.read_text(encoding="utf-8")))
        peak = max(abs(s) for s in samples)
        assert 3000 < peak <= 32767, path.name


def test_noise_is_deterministic():
    recipe = {"id": "t:audio/sfx/n", "duration_ms": 30, "volume_pm": 1000,
              "layers": [{"wave": "noise", "freq_start": 2000, "freq_end": 2000, "volume_pm": 1000, "attack_ms": 0, "decay_ms": 30}]}
    assert audio.render(recipe) == audio.render(recipe)
