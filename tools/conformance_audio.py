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


def _case(name: str, duration: int, volume: int, layers: list[dict], loop: bool = False) -> dict:
    recipe = {"id": f"test:audio/sfx/{name}", "duration_ms": duration, "volume_pm": volume, "layers": layers}
    if loop:
        recipe["loop"] = True
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
        _case("am_swell", 200, 900, [{**_layer("sine", 300, 300, 1000, 0, 200), "am_dhz": 50, "am_depth_pm": 800}]),
        _case("loop_wind", 400, 800, [{**_layer("noise", 300, 300, 1000, 0, 1), "am_dhz": 25, "am_depth_pm": 600}], loop=True),
        _case("silent", 50, 0, [_layer("sine", 440, 440, 1000, 0, 50)]),
    ]


# ---------------------------------------------------------------------------------------------- the director (spec 14)
BASE_SNAPSHOT = {
    "frame": 0,
    "player": {"hp": 100, "max_hp": 100, "level": 1, "phase": 0, "strike": False, "dodge": False, "moving": False,
               "x": 10.0, "y": 10.0, "surface": "grass", "save_cd": 0},
    "cues": [], "items": 5, "gold": 100, "mp": 50, "weapon": "w0", "armor": "a0",
    "panels": {"bag": False, "map": False, "journal": False, "shop": False, "board": False, "travel": False},
    "dialogue": False, "line": 0, "cursor": 0, "quests_started": 0, "quests_done": 0, "stones": 0,
    "region": "verdalis", "tod_pm": 500, "rain_pm": 0,
}


def _apply(snapshot: dict, patch: dict, index: int) -> dict:
    """The next snapshot: a patch over the previous one (the cues of a frame are not kept; `frame` counts up unless given)."""
    out = {**snapshot, "cues": [], "frame": index}
    for key, value in patch.items():
        if key in ("player", "panels"):
            out[key] = {**snapshot[key], **value}
        else:
            out[key] = value
    return out


def _director_case(name: str, patches: list[dict]) -> dict:
    from reference import audio_director

    director = audio_director.Director()
    snapshot = BASE_SNAPSHOT
    events = []
    for index, patch in enumerate(patches):
        snapshot = _apply(snapshot, patch, index)
        events.append(director.update(snapshot))
    return {"name": name, "input": {"op": "director", "base": BASE_SNAPSHOT, "patches": patches}, "expect": {"events": events}}


def _cue(kind: str, family: str = "slime", x: float = 12.0, y: float = 10.0, **extra) -> dict:
    return {"kind": kind, "family": family, "x": x, "y": y, **extra}


def suite_audio_director() -> list[dict]:
    walk = [{"player": {"moving": True, "x": 10.0 + 0.3 * i}} for i in range(1, 10)]
    return [
        _director_case("combat", [
            {}, {"player": {"phase": 1}}, {"player": {"phase": 2}}, {"player": {"phase": 3}}, {"player": {"phase": 0}},
            {"player": {"phase": 1, "strike": True}},
            {"cues": [_cue("hit", crit=True, weak=True), _cue("die", "wolf"), _cue("aggro", "knight", x=30.0), _cue("attack", "bat", x=15.0)]},
            {"cues": [_cue("hurt", "slime")]},
            {"cues": [_cue("parry", "wolf")]},
            {"cues": [_cue("gather", "plant", x=10.0), _cue("gather", "stone", x=10.0)]},
            {"player": {"dodge": True}}, {"player": {"dodge": True}}, {"player": {"dodge": False}},
            {"player": {"level": 2}}, {"player": {"save_cd": 1800}},
            {"player": {"hp": 0}},
        ]),
        _director_case("steps", [{}, *walk, {"player": {"moving": False}}, {"player": {"moving": True, "surface": "stone", "x": 20.0}},
                                 {"player": {"x": 21.0}}, {"player": {"surface": "sand", "x": 22.0}}]),
        _director_case("heartbeat", [{}, {"player": {"hp": 20}}, *({} for _ in range(139)), {"player": {"hp": 90}}, {}]),
        _director_case("bag_and_shop", [
            {}, {"items": 6}, {"gold": 130}, {"gold": 100, "items": 7},
            {"panels": {"shop": True}}, {"items": 6, "gold": 150}, {"items": 7, "gold": 110},
            {"panels": {"shop": False}}, {"items": 6, "player": {"hp": 90}}, {"items": 5, "mp": 80}, {"items": 4},
            {"weapon": "w1"}, {"armor": "a1"},
        ]),
        _director_case("panels_and_dialogue", [
            {}, {"panels": {"bag": True}}, {"cursor": 1}, {"cursor": 2}, {"panels": {"bag": False}}, {"cursor": 3},
            {"panels": {"map": True}}, {"panels": {"map": False, "journal": True}}, {"panels": {"journal": False, "board": True, "travel": True}},
            {"panels": {"board": False, "travel": False}},
            {"dialogue": True}, {"line": 1}, {"line": 1, "cursor": 4}, {"line": 2}, {"dialogue": False},
        ]),
        _director_case("world", [
            {"tod_pm": 240}, {"tod_pm": 260}, {"tod_pm": 700}, {"tod_pm": 760},
            {"region": "frostveil"}, {"region": "frostveil"}, {"quests_started": 1}, {"quests_done": 1}, {"stones": 1},
            {"rain_pm": 300}, {"rain_pm": 800}, {"frame": 1800, "rain_pm": 800}, {"rain_pm": 0},
        ]),
    ]


AMBIENCE_RULES = {
    "rain": {"light": "amb_rain_light", "heavy": "amb_rain_heavy", "silences": ["amb_birds"]},
    "regions": {
        "verdalis": [{"sound": "amb_birds", "when": "day", "gain_pm": 600}, {"sound": "amb_wind_soft", "gain_pm": 300},
                     {"sound": "amb_crickets", "when": "night", "gain_pm": 500}],
        "frostveil": [{"sound": "amb_wind_snow", "gain_pm": 700}],
    },
}


def suite_audio_ambience() -> list[dict]:
    from reference import audio_director

    cases = []
    for name, region, tod, rain in (("verdalis_day", "verdalis", 500, 0), ("verdalis_night", "verdalis", 0, 0), ("verdalis_light_rain", "verdalis", 500, 300),
                                    ("verdalis_storm", "verdalis", 500, 900), ("frostveil_storm", "frostveil", 100, 600), ("unknown_region", "nowhere", 500, 0)):
        gains = audio_director.ambience(region, tod, rain, AMBIENCE_RULES)
        cases.append({"name": name, "input": {"op": "ambience", "region": region, "tod_pm": tod, "rain_pm": rain, "rules": AMBIENCE_RULES},
                      "expect": {"gains": gains}})
    return cases
