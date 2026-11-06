"""The composed music of the base pack (spec 14)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import compose  # noqa: E402
from reference import music  # noqa: E402

AUDIO = Path(__file__).resolve().parent.parent.parent / "data" / "base" / "audio"


def test_every_piece_has_sixteen_step_bars_and_known_notes():
    files = sorted((AUDIO / "music").glob("*.json"))
    assert len(files) >= 30
    for path in files:
        piece = json.loads(path.read_text(encoding="utf-8"))
        layers = {t["layer"] for t in piece["tracks"]}
        assert "base" in layers, path.name
        for track in piece["tracks"]:
            assert len(track["bars"]) in (1, piece["bars"]), (path.name, track["name"])
            for bar in track["bars"]:
                tokens = bar.split()
                assert len(tokens) == 16, (path.name, track["name"], bar)
                for token in tokens:
                    if token not in (".", "-"):
                        for note in token.split("+"):
                            assert 20 < music.note_frequency(note) < 12000, (path.name, note)


def test_rules_name_existing_pieces():
    rules = json.loads((AUDIO / "music_rules.json").read_text(encoding="utf-8"))
    wanted = {rules["title"], rules["dead"]}
    wanted |= {q["piece"] for q in rules["quests"]}
    for table in (rules["places"], rules["regions"]):
        for choice in table.values():
            wanted |= set(choice.values())
    for piece in wanted:
        assert (AUDIO / "music" / f"{piece}.json").exists(), piece


def test_the_composer_is_deterministic():
    one = compose.compose("verdalis_day", **compose.PIECES["verdalis_day"])
    two = compose.compose("verdalis_day", **compose.PIECES["verdalis_day"])
    assert one == two
