#!/usr/bin/env python3
"""Writes a sound effect or a piece of music of the base pack to a WAV file, to listen to it (spec 14). Uses the Python reference
synthesizer, so a long piece takes a while (about 3 seconds of work per second of music).

    python tools/audio_wav.py sfx hit_a --out hit.wav
    python tools/audio_wav.py music verdalis_day --layers base,combat --bars 4 --out verdalis.wav
"""
from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reference import audio, music  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
AUDIO = ROOT / "data" / "base" / "audio"


def write_wav(path: Path, samples: list[int]) -> None:
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(audio.SAMPLE_RATE)
        out.writeframes(b"".join(int(s).to_bytes(2, "little", signed=True) for s in samples))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("kind", choices=["sfx", "music"])
    parser.add_argument("name")
    parser.add_argument("--out", default="")
    parser.add_argument("--layers", default="base", help="music: the layers to mix, e.g. base,combat,boss")
    parser.add_argument("--bars", type=int, default=0, help="music: render only this many bars")
    parser.add_argument("--loops", type=int, default=1, help="repeat the result this many times")
    args = parser.parse_args()
    if args.kind == "sfx":
        samples = audio.render(json.loads((AUDIO / "sfx" / f"{args.name}.json").read_text(encoding="utf-8")))
    else:
        piece = json.loads((AUDIO / "music" / f"{args.name}.json").read_text(encoding="utf-8"))
        if args.bars:
            piece["bars"] = args.bars
        layers = music.render(piece)
        wanted = [name for name in args.layers.split(",") if name in layers]
        if not wanted:
            print("no such layer; the piece has", ", ".join(layers))
            return 1
        samples = [max(-32767, min(32767, sum(layers[name][i] for name in wanted))) for i in range(len(layers[wanted[0]]))]
    out = Path(args.out or f"{args.name}.wav")
    write_wav(out, samples * args.loops)
    print(f"wrote {out} ({len(samples) * args.loops / audio.SAMPLE_RATE:.1f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
