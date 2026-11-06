"""Conformance suites for the music (spec 14): the renderer (`music`) and the director that chooses the piece (`music_director`)."""
from __future__ import annotations

from reference import music


def _patch(wave: str, a: int, d: int, s: int, r: int, **extra) -> dict:
    return {"wave": wave, "attack_ms": a, "decay_ms": d, "sustain_pm": s, "release_ms": r, **extra}


def _bar(tokens: str) -> str:
    assert len(tokens.split()) == 16, tokens
    return tokens


def _piece(name: str, tempo: int, bars: int, tracks: list[dict], volume: int = 900) -> dict:
    return {"id": f"test:audio/music/{name}", "tempo_bpm": tempo, "bars": bars, "volume_pm": volume, "tracks": tracks}


def _track(layer: str, patch: dict, volume: int, rows: list[str]) -> dict:
    return {"layer": layer, "patch": patch, "volume_pm": volume, "bars": [_bar(r) for r in rows]}


def _render_case(name: str, piece: dict) -> dict:
    layers = music.render(piece)
    expect = {}
    for layer, samples in layers.items():
        n = len(samples)
        expect[layer] = {
            "samples": n,
            "peak": max(abs(s) for s in samples),
            "mean_abs": sum(abs(s) for s in samples) / n,
            "probes": [{"i": i, "value": samples[i]} for i in (0, n // 9, n // 5, n // 3, n // 2, (2 * n) // 3, (4 * n) // 5, n - 1)],
        }
    return {"name": name, "input": {"op": "music", "piece": piece}, "expect": {"layers": expect}}


def suite_music() -> list[dict]:
    held = "C4 - - - . . . . E4+G4 - - - - - . ."
    return [
        _render_case("sine_notes", _piece("sine_notes", 240, 1, [_track("base", _patch("sine", 20, 100, 700, 120), 800, [held])])),
        _render_case("triangle_detuned_chord", _piece("chord", 240, 1, [_track("base", _patch("triangle", 60, 200, 800, 300, detune_cents=9), 700,
                                                                               ["C3+E3+G3 - - - - - - - A2+C3+E3 - - - - - - -"])])),
        _render_case("square_duty_wrap", _piece("wrap", 240, 1, [_track("base", _patch("square", 5, 60, 500, 400, duty_pm=250), 600,
                                                                          [". . . . . . . . . . . . . . G4 -"])])),
        _render_case("kick_glide", _piece("kick", 240, 1, [_track("combat", _patch("sine", 2, 120, 0, 40, glide_pm=250), 900,
                                                                  ["C2 . . . C2 . . . C2 . . . C2 . . ."])])),
        _render_case("noise_hats", _piece("hats", 240, 1, [_track("combat", _patch("noise", 1, 35, 0, 25), 700,
                                                                  ["C7 . C7 . C7 . C7 . C7 . C7 . C7 . C7 ."])])),
        _render_case("layers_and_loops", _piece("layers", 240, 2, [
            _track("base", _patch("saw", 30, 100, 600, 150), 500, ["A3 - - - C4 - - - E4 - - - C4 - - -", "G3 - - - B3 - - - D4 - - - B3 - - -"]),
            _track("combat", _patch("noise", 1, 80, 0, 40), 400, ["C5 . . . C5 . . . C5 . . . C5 . . ."]),
            _track("tension", _patch("sine", 300, 100, 900, 300, am_dhz=40, am_depth_pm=500), 300, ["E2+B2 - - - - - - - - - - - - - - -"]),
        ])),
    ]


RULES = {
    "title": "title", "dead": "dead", "default_region": "verdalis",
    "quests": [{"quest": "q:one", "piece": "quest_one"}, {"quest": "q:two", "piece": "quest_two"}],
    "places": {"settlement": {"day": "town_day", "night": "town_night"}, "dungeon": {"day": "dungeon"}},
    "regions": {"verdalis": {"day": "verdalis_day", "night": "verdalis_night"}, "frostveil": {"day": "frost_day", "night": "frost_night"}},
}

BASE_CTX = {"frame": 0, "screen": "game", "region": "verdalis", "tod_pm": 500, "place": "wild", "quests": [], "low_hp": False, "cues": [], "x": 10.0, "y": 10.0}


def _cue(kind: str, family: str = "slime", x: float = 12.0, y: float = 10.0) -> dict:
    return {"kind": kind, "family": family, "x": x, "y": y}


def _director_case(name: str, patches: list[dict]) -> dict:
    director = music.MusicDirector(RULES)
    ctx = BASE_CTX
    outputs = []
    for index, patch in enumerate(patches):
        ctx = {**ctx, "cues": [], "frame": index, **patch}
        outputs.append(director.update(ctx))
    return {"name": name, "input": {"op": "music_director", "rules": RULES, "base": BASE_CTX, "patches": patches}, "expect": {"outputs": outputs}}


def suite_music_director() -> list[dict]:
    return [
        _director_case("pieces", [{}, {"tod_pm": 100}, {"tod_pm": 250}, {"tod_pm": 750}, {"tod_pm": 751}, {"region": "frostveil"}, {"region": "unknown"},
                                  {"place": "settlement"}, {"place": "settlement", "tod_pm": 0}, {"place": "dungeon", "tod_pm": 0},
                                  {"screen": "title"}, {"screen": "dead"}]),
        _director_case("quests", [{}, {"quests": ["q:two"]}, {"quests": ["q:two", "q:one"]}, {"quests": ["q:one"], "place": "dungeon"},
                                  {"quests": ["q:one"], "place": "settlement"}, {"quests": ["q:none"]}]),
        _director_case("fight_and_boss", [
            {}, {"cues": [_cue("aggro", x=30.0)]}, {"cues": [_cue("aggro", x=15.0)]}, {}, {"frame": 200}, {"frame": 420}, {"frame": 440},
            {"frame": 441, "cues": [_cue("hurt", "wolf", x=50.0)]}, {"frame": 900}, {"frame": 1000, "cues": [_cue("attack", "knight", x=14.0)]},
            {"frame": 1100}, {"frame": 1599}, {"frame": 1600}, {"frame": 1700}, {"frame": 1800, "low_hp": True}, {"frame": 1801, "low_hp": False},
            {"frame": 1900, "cues": [_cue("die", "king", x=12.0)]}, {"frame": 2000},
        ]),
    ]
