#!/usr/bin/env python3
"""Composes the music of the base pack (data/base/audio/music/*.json) and the rules that choose it (music_rules.json). Spec 14.

Every piece is built from a mood (a mode, a key, a tempo, a chord progression, a set of instruments) by a few rules of harmony:
chords are triads (sometimes with a seventh) built on the degrees of the mode; the bass plays their roots and fifths; the pad holds
them; the arpeggio walks their notes; the melody is a short motif that is repeated and varied over the progression, with a chord
tone on every strong beat and steps on the others. A piece has up to four layers that the game mixes (spec 14): `base` plays
always, `tension` when the hero is badly hurt, `combat` while fighting and `boss` against the big ones.

The result is plain JSON: the game never runs this code. It is seeded by the name of the piece, so it writes the same notes every
time. Run it from the repository root: `python tools/compose.py`.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "base" / "audio"

MODES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
}
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
ROOTS = {"C": 0, "C#": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}


def name(midi: int) -> str:
    return f"{NAMES[midi % 12]}{midi // 12 - 1}"


# ---------------------------------------------------------------------------------------------------------- instruments
def patch(wave: str, a: int, d: int, s: int, r: int, **extra) -> dict:
    return {"wave": wave, "attack_ms": a, "decay_ms": d, "sustain_pm": s, "release_ms": r, **extra}


INSTRUMENTS = {
    "pad": patch("triangle", 500, 400, 800, 900, detune_cents=7),
    "warm_pad": patch("sine", 700, 300, 850, 1000, detune_cents=5),
    "strings": patch("saw", 350, 300, 700, 600, detune_cents=9),
    "choir": patch("triangle", 450, 300, 750, 800, detune_cents=12, am_dhz=45, am_depth_pm=150),
    "bass": patch("triangle", 10, 160, 700, 140),
    "deep_bass": patch("sine", 12, 200, 800, 180),
    "synth_bass": patch("saw", 8, 120, 600, 100),
    "pluck": patch("triangle", 4, 240, 150, 220),
    "harp": patch("sine", 3, 380, 100, 500),
    "marimba": patch("sine", 2, 260, 60, 160),
    "bell": patch("sine", 2, 800, 80, 900),
    "glock": patch("triangle", 2, 450, 60, 600),
    "flute": patch("sine", 90, 150, 800, 260, am_dhz=55, am_depth_pm=120),
    "whistle": patch("triangle", 60, 120, 750, 220, am_dhz=60, am_depth_pm=150),
    "organ": patch("square", 25, 100, 600, 160, duty_pm=500),
    "chip": patch("square", 4, 140, 350, 120, duty_pm=250),
    "brass": patch("saw", 45, 150, 750, 200),
    "horn": patch("saw", 90, 200, 700, 300),
    "kick": patch("sine", 2, 120, 0, 40, glide_pm=250),
    "snare": patch("noise", 1, 110, 0, 60),
    "hat": patch("noise", 1, 35, 0, 25),
    "tom": patch("sine", 2, 170, 0, 60, glide_pm=450),
    "drone": patch("sine", 1200, 600, 900, 1500, detune_cents=4),
    "tremolo": patch("square", 3, 70, 0, 50, duty_pm=300),
}

# ---------------------------------------------------------------------------------------------------------- harmony
PROGRESSIONS = {
    "bright": [[1], [5], [6], [4], [1], [5], [4], [5]],
    "folk": [[1], [4], [1], [5], [1], [4], [5], [1]],
    "wander": [[1], [6], [4], [5], [1], [6], [2], [5]],
    "dream": [[1], [3], [6], [4], [1], [3], [4], [5]],
    "sad": [[6], [4], [1], [5], [6], [4], [5], [6]],
    "minor": [[1], [6], [3], [7], [1], [4], [7], [5]],
    "dark": [[1], [2], [1], [7], [1], [6], [7], [1]],
    "heroic": [[1], [5], [6], [3], [4], [1], [4], [5]],
    "drift": [[1], [7], [6], [7], [1], [7], [4], [1]],
}


def triad(root: int, mode: list[int], degree: int, seventh: bool = False) -> list[int]:
    """Midi notes of the triad on a 1-based degree of the mode, the root at `root` (a midi note of the tonic)."""
    def note(step: int) -> int:
        octave, index = divmod(step, 7)
        return root + 12 * octave + mode[index]

    base = degree - 1
    notes = [note(base), note(base + 2), note(base + 4)]
    if seventh:
        notes.append(note(base + 6))
    return notes


def lift(midi: int, low: int, high: int) -> int:
    """The same note moved by octaves into [low, high)."""
    while midi < low:
        midi += 12
    while midi >= high:
        midi -= 12
    return midi


# ---------------------------------------------------------------------------------------------------------- patterns
RHYTHMS = [
    # sixteen steps; 1 plays a note, 0 holds/rests. Lead rhythms: a mix of long and short notes.
    "1 0 0 0 1 0 1 0 1 0 0 0 1 0 0 0",
    "1 0 1 0 1 0 0 0 1 0 1 0 1 0 0 0",
    "1 0 0 1 0 0 1 0 1 0 0 0 1 0 1 0",
    "1 0 1 1 0 0 1 0 1 0 1 0 0 0 1 0",
    "1 0 0 0 0 0 1 0 1 0 0 1 0 0 1 0",
    "1 0 1 0 0 0 1 1 0 0 1 0 1 0 0 0",
]
BASS_PATTERNS = [
    ["R", "-", "-", "-", "-", "-", "-", "-", "5", "-", "-", "-", "-", "-", "-", "-"],
    ["R", "-", "-", "-", ".", ".", "R", "-", "5", "-", "-", "-", ".", ".", "R", "-"],
    ["R", "-", "-", "-", "R", "-", "-", "-", "5", "-", "-", "-", "R", "-", "-", "-"],
    ["R", "-", ".", ".", "R", "-", ".", ".", "5", "-", ".", ".", "R", "-", ".", "."],
    ["R", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
]


def bar_string(tokens: list[str]) -> str:
    assert len(tokens) == 16, tokens
    return " ".join(tokens)


# ---------------------------------------------------------------------------------------------------------- a piece
def compose(piece_id: str, *, key: str, mode: str, tempo: int, progression: str, bars: int = 16, volume: int = 600,
            pad: str = "pad", bass: str = "bass", arp: str = "harp", lead: str = "flute", arp_rate: int = 2, lead_density: int = 2,
            layers: tuple[str, ...] = ("base", "tension", "combat", "boss"), octave: int = 3, motifs: int = 2,
            seventh: bool = False, swing_arp: bool = False, base_only: bool = False, drone: bool = True) -> dict:
    rng = random.Random(piece_id)
    scale = MODES[mode]
    tonic = 12 * (octave + 1) + ROOTS[key]  # midi of the tonic in `octave`
    chords_per_bar = [PROGRESSIONS[progression][i % 8] for i in range(bars)]
    chords = [triad(tonic, scale, degs[0], seventh) for degs in chords_per_bar]
    bass_low = max(tonic - 12, 33)  # the bass stays within A1 and up: lower notes vanish on small speakers
    tracks: list[dict] = []

    def add(layer: str, label: str, instrument: str, volume_pm: int, rows: list[str]) -> None:
        tracks.append({"layer": layer, "name": label, "patch": INSTRUMENTS[instrument], "volume_pm": volume_pm, "bars": rows})

    # --- base: a pad on the chords
    rows = []
    for chord in chords:
        notes = "+".join(name(lift(n, tonic - 2, tonic + 12)) for n in chord[:3])
        rows.append(bar_string([notes] + ["-"] * 15))
    add("base", "pad", pad, 230, rows)

    # --- base: the bass, on roots and fifths
    rows = []
    pattern = rng.choice(BASS_PATTERNS)
    for bar, chord in enumerate(chords):
        if bar % 4 == 0:
            pattern = rng.choice(BASS_PATTERNS)
        root = name(lift(chord[0], bass_low, bass_low + 12))
        fifth = name(lift(chord[2], bass_low, bass_low + 12))
        rows.append(bar_string([root if t == "R" else fifth if t == "5" else t for t in pattern]))
    add("base", "bass", bass, 420, rows)

    # --- base: the arpeggio walks the chord notes
    rows = []
    for chord in chords:
        notes = [name(lift(n, tonic + 12, tonic + 31)) for n in chord[:3]] + [name(lift(chord[0] + 12, tonic + 12, tonic + 31))]
        order = [0, 1, 2, 3, 2, 1, 0, 1] if arp_rate == 2 else [0, 2, 1, 3]
        step_width = 2 if arp_rate == 2 else 4
        tokens = ["."] * 16
        for k, i in enumerate(range(0, 16, step_width)):
            if rng.random() < 0.88:
                tokens[i] = notes[order[k % len(order)]]
        if swing_arp:
            for i in range(1, 16, 4):
                tokens[i] = tokens[i - 1] if tokens[i - 1] != "." else "."
        rows.append(bar_string(tokens))
    add("base", "arp", arp, 170, rows)

    # --- base: the melody, a motif repeated and varied over the chords
    lead_low, lead_high = tonic + 12, tonic + 31

    def degree_notes(chord: list[int]) -> list[int]:
        return sorted({lift(n, lead_low, lead_high) for n in chord} | {lift(n, lead_low, lead_high) + 12 for n in chord if lift(n, lead_low, lead_high) + 12 < lead_high})

    scale_notes = sorted({tonic + 12 * o + s for o in range(0, 4) for s in scale if lead_low <= tonic + 12 * o + s < lead_high})

    def motif() -> list[tuple[int, int]]:
        """A rhythm and a walk on the scale: [(step, scale index offset)] for one bar."""
        rhythm = [int(x) for x in rng.choice(RHYTHMS).split()]
        out = []
        for step, on in enumerate(rhythm):
            if on and (lead_density >= 2 or step % 4 == 0):
                out.append((step, rng.choice([-2, -1, -1, 0, 1, 1, 2])))
        return out

    motif_bank = [motif() for _ in range(motifs)]
    rows = []
    position = rng.randrange(len(scale_notes) // 3, 2 * len(scale_notes) // 3)
    for bar, chord in enumerate(chords):
        phrase_end = bar % 4 == 3
        shape = motif_bank[(bar // 2) % len(motif_bank)] if bar % 8 < 4 else motif_bank[(bar // 2 + 1) % len(motif_bank)]
        tokens = ["."] * 16
        chord_tones = degree_notes(chord)
        steps_used = []
        for step, move in shape:
            if phrase_end and step >= 8:
                continue
            position = max(0, min(len(scale_notes) - 1, position + move))
            midi = scale_notes[position]
            if step % 8 == 0:  # strong beat: the nearest chord tone
                midi = min(chord_tones, key=lambda c: abs(c - midi))
                position = scale_notes.index(lift(midi, lead_low, lead_high)) if lift(midi, lead_low, lead_high) in scale_notes else position
            tokens[step] = name(midi)
            steps_used.append(step)
        if not steps_used:
            tokens[0] = name(min(chord_tones, key=lambda c: abs(c - scale_notes[position])))
        # hold each note until the next one
        filled = tokens[:]
        last = None
        for i, token in enumerate(tokens):
            if token != ".":
                last = i
            elif last is not None and i - last < 3:
                filled[i] = "-"
        rows.append(bar_string(filled))
    add("base", "lead", lead, 300, rows)

    if base_only:
        return piece_doc(piece_id, tempo, bars, volume, tracks)

    # --- tension: a drone on the tonic and the fifth, a trembling note
    if "tension" in layers:
        floor = max(tonic - 24, 28)  # never below E1: lower is felt, not heard
        low = name(lift(tonic, floor, floor + 12))
        fifth = name(lift(tonic + scale[4], floor, floor + 12))
        add("tension", "drone", "drone", 350, [bar_string([f"{low}+{fifth}"] + ["-"] * 15)])
        rows = []
        for bar, chord in enumerate(chords):
            note = name(lift(chord[1], tonic + 12, tonic + 24))
            rows.append(bar_string([note if i % 2 == 0 and (bar % 2 == 0 or i >= 8) else "." for i in range(16)]))
        add("tension", "tremolo", "tremolo", 110, rows)

    # --- combat: drums, a driving bass, off-beat stabs
    if "combat" in layers:
        add("combat", "kick", "kick", 520, [bar_string(["C2" if i % 4 == 0 else "." for i in range(16)])])
        add("combat", "snare", "snare", 260, [bar_string(["C5" if i in (4, 12) else "." for i in range(16)])])
        add("combat", "hat", "hat", 120, [bar_string(["C7" if i % 2 == 0 else "." for i in range(16)])])
        rows = []
        for chord in chords:
            root = name(lift(chord[0], bass_low, bass_low + 12))
            rows.append(bar_string([root if i % 2 == 0 else "." for i in range(16)]))
        add("combat", "drive", "synth_bass", 300, rows)
        rows = []
        for chord in chords:
            notes = "+".join(name(lift(n, tonic, tonic + 12)) for n in chord[:3])
            rows.append(bar_string([notes if i in (2, 6, 10, 14) else "." for i in range(16)]))
        add("combat", "stab", "brass", 160, rows)

    # --- boss: a heavy pulse, toms, a low horn on the roots and a choir
    if "boss" in layers:
        add("boss", "kick", "kick", 560, [bar_string(["C2" if i % 2 == 0 else "." for i in range(16)])])
        add("boss", "tom", "tom", 300, [bar_string(["G2" if i in (6, 7, 14, 15) else "." for i in range(16)])])
        add("boss", "hat", "hat", 110, [bar_string(["C7" if i % 1 == 0 and i % 2 == 1 else "." for i in range(16)])])
        rows = []
        for chord in chords:
            root = name(lift(chord[0], bass_low, bass_low + 12))
            fifth = name(lift(chord[2], bass_low, bass_low + 12))
            rows.append(bar_string([root] + ["-"] * 7 + [fifth] + ["-"] * 7))
        add("boss", "horn", "horn", 380, rows)
        rows = []
        for chord in chords:
            notes = "+".join(name(lift(n, tonic + 12, tonic + 24)) for n in chord[:3])
            rows.append(bar_string([notes] + ["-"] * 15))
        add("boss", "choir", "choir", 240, rows)
    return piece_doc(piece_id, tempo, bars, volume, tracks)


def piece_doc(piece_id: str, tempo: int, bars: int, volume: int, tracks: list[dict]) -> dict:
    return {"$schema": "../../../../schemas/music.schema.json", "id": f"base:audio/music/{piece_id}", "tempo_bpm": tempo, "bars": bars,
            "volume_pm": volume, "tracks": tracks}


# ---------------------------------------------------------------------------------------------------------- the pieces
PIECES: dict[str, dict] = {
    # --- the title and the end
    "title": dict(key="D", mode="major", tempo=84, progression="heroic", pad="strings", bass="deep_bass", arp="harp", lead="horn", octave=3, motifs=3),
    "dead": dict(key="A", mode="minor", tempo=48, progression="sad", pad="warm_pad", bass="deep_bass", arp="bell", lead="flute", arp_rate=1, lead_density=1, base_only=True),
    # --- Verdalis: green plains
    "verdalis_day": dict(key="G", mode="major", tempo=100, progression="bright", pad="warm_pad", bass="bass", arp="harp", lead="whistle", octave=3, motifs=3),
    "verdalis_night": dict(key="E", mode="dorian", tempo=66, progression="dream", pad="warm_pad", bass="deep_bass", arp="glock", lead="flute", arp_rate=1, lead_density=1),
    # --- Whisperwood: a mysterious forest
    "whisperwood_day": dict(key="D", mode="dorian", tempo=76, progression="wander", pad="choir", bass="deep_bass", arp="harp", lead="flute", octave=3),
    "whisperwood_night": dict(key="B", mode="minor", tempo=56, progression="dream", pad="choir", bass="deep_bass", arp="bell", lead="flute", arp_rate=1, lead_density=1),
    # --- Ironspine: mountains and mines
    "ironspine_day": dict(key="E", mode="minor", tempo=84, progression="minor", pad="strings", bass="synth_bass", arp="marimba", lead="horn", octave=2),
    "ironspine_night": dict(key="A", mode="phrygian", tempo=60, progression="dark", pad="strings", bass="deep_bass", arp="marimba", lead="horn", arp_rate=1, lead_density=1, octave=2),
    # --- Sunscar: the desert
    "sunscar_day": dict(key="A", mode="harmonic_minor", tempo=92, progression="drift", pad="warm_pad", bass="bass", arp="pluck", lead="flute", octave=3, motifs=3),
    "sunscar_night": dict(key="D", mode="harmonic_minor", tempo=64, progression="sad", pad="warm_pad", bass="deep_bass", arp="harp", lead="whistle", arp_rate=1, lead_density=1),
    # --- Frostveil: snow and ice
    "frostveil_day": dict(key="F#", mode="lydian", tempo=64, progression="dream", pad="choir", bass="deep_bass", arp="glock", lead="bell", arp_rate=1, lead_density=1, octave=3),
    "frostveil_night": dict(key="C#", mode="minor", tempo=52, progression="sad", pad="warm_pad", bass="deep_bass", arp="bell", lead="flute", arp_rate=1, lead_density=1),
    # --- Tidehaven: the coast
    "tidehaven_day": dict(key="G", mode="mixolydian", tempo=104, progression="folk", pad="organ", bass="bass", arp="marimba", lead="whistle", octave=3, motifs=3),
    "tidehaven_night": dict(key="D", mode="mixolydian", tempo=72, progression="wander", pad="warm_pad", bass="deep_bass", arp="harp", lead="flute", arp_rate=1, lead_density=1),
    # --- Ashen Wastes: ash and fire
    "ashen_day": dict(key="C", mode="phrygian", tempo=78, progression="dark", pad="strings", bass="synth_bass", arp="pluck", lead="horn", octave=2, motifs=2),
    "ashen_night": dict(key="F", mode="phrygian", tempo=58, progression="dark", pad="strings", bass="deep_bass", arp="bell", lead="horn", arp_rate=1, lead_density=1, octave=2),
    # --- Lumeria: stars and magic
    "lumeria_day": dict(key="A", mode="lydian", tempo=88, progression="dream", pad="choir", bass="bass", arp="glock", lead="bell", octave=3, motifs=3),
    "lumeria_night": dict(key="E", mode="lydian", tempo=62, progression="dream", pad="choir", bass="deep_bass", arp="bell", lead="flute", arp_rate=1, lead_density=1),
    # --- places
    "town_day": dict(key="C", mode="major", tempo=108, progression="folk", pad="organ", bass="bass", arp="pluck", lead="whistle", octave=3, motifs=3),
    "town_night": dict(key="F", mode="major", tempo=72, progression="wander", pad="warm_pad", bass="deep_bass", arp="harp", lead="flute", arp_rate=1, lead_density=1),
    "dungeon": dict(key="C#", mode="phrygian", tempo=66, progression="dark", pad="strings", bass="deep_bass", arp="bell", lead="flute", arp_rate=1, lead_density=1, octave=2),
    # --- pieces for particular quests
    "quest_sorrow": dict(key="G", mode="minor", tempo=54, progression="sad", pad="warm_pad", bass="deep_bass", arp="harp", lead="flute", arp_rate=1, lead_density=1),
    "quest_hunt": dict(key="D", mode="phrygian", tempo=96, progression="dark", pad="strings", bass="synth_bass", arp="pluck", lead="horn", octave=2),
    "quest_mystery": dict(key="F#", mode="dorian", tempo=68, progression="drift", pad="choir", bass="deep_bass", arp="glock", lead="bell", arp_rate=1, lead_density=1),
    "quest_triumph": dict(key="C", mode="major", tempo=112, progression="heroic", pad="strings", bass="bass", arp="harp", lead="brass", octave=3, motifs=3),
    # --- the personal quests of the protagonists: a theme for each
    "theme_ren": dict(key="F", mode="major", tempo=104, progression="wander", pad="organ", bass="bass", arp="pluck", lead="whistle", octave=3, motifs=3),
    "theme_sakura": dict(key="A", mode="major", tempo=132, progression="bright", pad="organ", bass="synth_bass", arp="chip", lead="chip", octave=3, motifs=3),
    "theme_daichi": dict(key="Bb", mode="major", tempo=92, progression="heroic", pad="strings", bass="deep_bass", arp="harp", lead="horn", octave=2, motifs=3),
    "theme_haruka": dict(key="D", mode="major", tempo=88, progression="folk", pad="warm_pad", bass="bass", arp="harp", lead="flute", octave=3, motifs=3),
    "theme_marco": dict(key="G", mode="mixolydian", tempo=116, progression="folk", pad="organ", bass="bass", arp="marimba", lead="whistle", octave=3, motifs=3),
    "theme_yuki": dict(key="E", mode="dorian", tempo=82, progression="drift", pad="strings", bass="synth_bass", arp="pluck", lead="bell", octave=2, motifs=2),
    "theme_lena": dict(key="C", mode="minor", tempo=58, progression="sad", pad="warm_pad", bass="deep_bass", arp="harp", lead="flute", arp_rate=1, lead_density=1),
    "theme_gideon": dict(key="D", mode="harmonic_minor", tempo=78, progression="dark", pad="choir", bass="synth_bass", arp="bell", lead="horn", octave=2, motifs=3),
}

REGION_PIECES = {r: {"day": f"{r}_day", "night": f"{r}_night"} for r in ("verdalis", "whisperwood", "ironspine", "sunscar", "frostveil", "tidehaven")}
REGION_PIECES["ashen_wastes"] = {"day": "ashen_day", "night": "ashen_night"}
REGION_PIECES["lumeria"] = {"day": "lumeria_day", "night": "lumeria_night"}


def rules(quest_pieces: list[tuple[str, str]]) -> dict:
    return {
        "$schema": "../../../schemas/music_rules.schema.json",
        "id": "base:audio/music_rules",
        "title": "title",
        "dead": "dead",
        "default_region": "verdalis",
        "quests": [{"quest": q, "piece": p} for q, p in quest_pieces],
        "places": {"settlement": {"day": "town_day", "night": "town_night"}, "dungeon": {"day": "dungeon"}},
        "regions": REGION_PIECES,
    }


def main(quest_pieces: list[tuple[str, str]] | None = None) -> None:
    music = OUT / "music"
    music.mkdir(parents=True, exist_ok=True)
    for old in music.glob("*.json"):
        old.unlink()
    for piece_id, kwargs in PIECES.items():
        doc = compose(piece_id, **kwargs)
        (music / f"{piece_id}.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    (OUT / "music_rules.json").write_text(json.dumps(rules(quest_pieces if quest_pieces is not None else QUEST_PIECES), indent=2) + "\n", encoding="utf-8")
    print(f"composed {len(PIECES)} pieces")


def _q(name: str) -> str:
    return f"base:quest/side/{name}"


QUEST_PIECES: list[tuple[str, str]] = (
    [(_q(f"personal_{who}_{n}"), f"theme_{who}") for who in ("ren", "sakura", "daichi", "haruka", "marco", "yuki", "lena", "gideon") for n in (1, 2)]
    + [(_q(n), "quest_hunt") for n in ("amber_queen_hunt", "crowned_one", "den_alpha", "grotto_matron", "pit_warden", "roost_sovereign", "silver_alpha", "vent_heart", "furnace_cores")]
    + [(_q(n), "quest_mystery") for n in ("dust_survey", "slate_toll", "tide_pearls", "lantern_wisps", "season_solstice_survey", "season_wisp_bloom")]
    + [(_q(n), "quest_sorrow") for n in ("season_cold_ash", "season_winter_stores")]
    + [(_q(n), "quest_triumph") for n in ("season_petal_festival", "season_harvest_cart")]
)

if __name__ == "__main__":
    main()
