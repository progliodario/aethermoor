"""Reference music renderer and music director (spec 14, "Music"): pieces of a few tracks and layers, played as seamless loops."""
from __future__ import annotations

import math

SAMPLE_RATE = 22050
STEPS_PER_BAR = 16
LAYERS = ("base", "tension", "combat", "boss")
SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
BOSS_FAMILIES = ("king", "matron", "alpha", "knight")
FIGHT_FRAMES = 420
BOSS_FRAMES = 600
FIGHT_RANGE_TILES = 10.0


def note_frequency(name: str) -> float:
    """`C4`, `F#3`, `Bb2`: the pitch in Hz (A4 = 440)."""
    semitone = SEMITONES[name[0]]
    i = 1
    while name[i] in "#b":
        semitone += 1 if name[i] == "#" else -1
        i += 1
    octave = int(name[i:])
    midi = 12 * (octave + 1) + semitone
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def _xorshift(state: int) -> int:
    state ^= (state << 13) & 0xFFFFFFFF
    state ^= state >> 17
    state ^= (state << 5) & 0xFFFFFFFF
    return state & 0xFFFFFFFF


def _events(track: dict, bars: int) -> list[tuple[int, int, list[str]]]:
    """The notes of a track: (first step, length in steps, chord) for a loop of `bars` bars."""
    tokens: list[str] = []
    patterns = track["bars"]
    for bar in range(bars):
        tokens += patterns[bar % len(patterns)].split()
    notes: list[tuple[int, int, list[str]]] = []
    for step, token in enumerate(tokens):
        if token == "-" and notes and notes[-1][0] + notes[-1][1] == step:
            first, length, chord = notes[-1]
            notes[-1] = (first, length + 1, chord)
        elif token not in (".", "-"):
            notes.append((step, 1, token.split("+")))
    return notes


def _voice(patch: dict, freq: float, length: int, total: int, state_seed: int) -> list[float]:
    """One note of a patch: `length` samples held, then the release; returns `total` samples."""
    wave = patch["wave"]
    attack = max(1.0, float(patch["attack_ms"]))
    decay = max(1.0, float(patch["decay_ms"]))
    sustain = patch["sustain_pm"] / 1000.0
    release = max(1.0, float(patch["release_ms"]))
    detune = patch.get("detune_cents", 0)
    glide = patch.get("glide_pm", 1000)
    am_hz = patch.get("am_dhz", 0) / 10.0
    am_depth = patch.get("am_depth_pm", 0) / 1000.0
    duty = patch.get("duty_pm", 500)
    length_ms = length * 1000.0 / SAMPLE_RATE
    out = [0.0] * total
    oscillators = [1.0] if detune == 0 else [2.0 ** (detune / 1200.0), 2.0 ** (-detune / 1200.0)]
    for ratio in oscillators:
        f = freq * ratio
        state = state_seed if state_seed else 1
        held = 0.0
        prev_cycle = -1
        for i in range(total):
            t = i / SAMPLE_RATE
            if glide != 1000 and length > 0:
                g = glide / 1000.0
                lg = math.log(g)
                phase_total = f * (length / SAMPLE_RATE) / lg * (g ** (min(i, length) / length) - 1.0) if i <= length else f * (length / SAMPLE_RATE) / lg * (g - 1.0) + f * g * (t - length / SAMPLE_RATE)
            else:
                phase_total = f * t
            phase = phase_total - math.floor(phase_total)
            if wave == "sine":
                w = math.sin(2.0 * math.pi * phase)
            elif wave == "square":
                w = 1.0 if phase * 1000.0 < duty else -1.0
            elif wave == "saw":
                w = 2.0 * phase - 1.0
            elif wave == "triangle":
                w = 4.0 * abs(phase - 0.5) - 1.0
            else:
                cycle = math.floor(phase_total)
                if cycle != prev_cycle:
                    state = _xorshift(state)
                    held = (state - 0x100000000 if state >= 0x80000000 else state) / 2147483648.0
                    prev_cycle = cycle
                w = held
            ms = i * 1000.0 / SAMPLE_RATE
            held_ms = min(ms, length_ms)
            if held_ms < attack:
                level = held_ms / attack
            elif held_ms < attack + decay:
                level = 1.0 - (1.0 - sustain) * (held_ms - attack) / decay
            else:
                level = sustain
            if i >= length:
                level = level * max(0.0, 1.0 - (ms - length_ms) / release)
            gain = 1.0 - am_depth * (0.5 - 0.5 * math.cos(2.0 * math.pi * am_hz * t)) if am_depth > 0.0 else 1.0
            out[i] += w * level * gain / len(oscillators)
    return out


def render(piece: dict) -> dict[str, list[int]]:
    """Renders every layer of a piece to 16 bit samples; all have the same length (the loop)."""
    bars = piece["bars"]
    step_samples = SAMPLE_RATE * 60.0 / (piece["tempo_bpm"] * 4)
    n = int(math.floor(bars * STEPS_PER_BAR * step_samples))
    master = piece["volume_pm"] / 1000.0
    mixes: dict[str, list[float]] = {}
    for track in piece["tracks"]:
        layer = track["layer"]
        buf = mixes.setdefault(layer, [0.0] * n)
        volume = track["volume_pm"] / 1000.0
        patch = track["patch"]
        release_samples = int(patch["release_ms"] * SAMPLE_RATE / 1000)
        for index, (first, length, chord) in enumerate(_events(track, bars)):
            start = int(math.floor(first * step_samples))
            held = int(math.floor((first + length) * step_samples)) - start
            total = held + release_samples
            seed = (2463534242 + 2654435761 * index) & 0xFFFFFFFF
            for name in chord:
                voice = _voice(patch, note_frequency(name), held, total, seed)
                for i, v in enumerate(voice):
                    buf[(start + i) % n] += v * volume / len(chord) ** 0.5
    out: dict[str, list[int]] = {}
    for layer, buf in mixes.items():
        out[layer] = [math.floor(max(-1.0, min(1.0, v * master)) * 32767.0 + 0.5) for v in buf]
    return out


class MusicDirector:
    """Which piece plays and which layers are on (spec 14, "The music director")."""

    def __init__(self, rules: dict) -> None:
        self.rules = rules
        self.last_fight = -10**9
        self.last_boss = -10**9

    def update(self, ctx: dict) -> dict:
        frame = ctx["frame"]
        for cue in ctx["cues"]:
            if cue["kind"] == "gather":
                continue
            near = math.hypot(cue["x"] - ctx["x"], cue["y"] - ctx["y"]) <= FIGHT_RANGE_TILES
            if cue["kind"] in ("hit", "hurt") or near:
                self.last_fight = frame
                if cue["family"] in BOSS_FAMILIES and cue["kind"] != "die":
                    self.last_boss = frame
        fight = frame - self.last_fight < FIGHT_FRAMES
        boss = frame - self.last_boss < BOSS_FRAMES
        layers = ["base"]
        if ctx["low_hp"]:
            layers.append("tension")
        if fight or boss:
            layers.append("combat")
        if boss:
            layers.append("boss")
        return {"piece": self._piece(ctx), "layers": layers}

    def _piece(self, ctx: dict) -> str:
        rules = self.rules
        if ctx["screen"] == "title":
            return rules["title"]
        if ctx["screen"] == "dead":
            return rules["dead"]
        for entry in rules["quests"]:
            if entry["quest"] in ctx["quests"] and ctx["place"] != "dungeon":
                return entry["piece"]
        day = 250 <= ctx["tod_pm"] <= 750
        place = rules["places"].get(ctx["place"])
        if place is not None:
            return place["day"] if day or "night" not in place else place["night"]
        region = rules["regions"].get(ctx["region"], rules["regions"][rules["default_region"]])
        return region["day"] if day else region["night"]
