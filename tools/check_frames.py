#!/usr/bin/env python3
"""Checks the frames of the desktop smoke tests (spec 16, "Checks of the frames"): the automatic checks of the graphics.

    python tools/check_frames.py <screenshots folder> [...]           check every folder against tests/frames/<folder name>.json
    python tools/check_frames.py --write <screenshots folder> [...]   write the references from these frames

For every frame the reference lists it checks that the PNG is there, is at least 640 x 360, is not blank (a spread of brightness), is
not black and has enough colours; then it compares a fingerprint, the mean colour of every cell of a 16 x 9 grid, with the reference:
the mean difference must stay under `TOLERANCE` (out of 255). The tolerance is wide on purpose: a new text, a new prop or the light of
another hour passes, a black screen, a missing world, a panel drawn over everything or a broken palette does not. After a change that
moves the frames on purpose, write the references again from the screenshots of the CI (`gh run download <id> -n screenshots-windows-msvc`).
Only the standard library: it reads the PNGs itself.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "tests" / "frames"
GRID_W, GRID_H = 16, 9
TOLERANCE = 38          # the mean difference of the cells, out of 255
MIN_SPREAD = 10         # the standard deviation of the brightness
MAX_BLACK = 0.85        # the share of pixels darker than 12
MIN_COLOURS = 24        # distinct colours, with every channel cut to 3 bits


def read_png(path: Path) -> tuple[int, int, int, list[bytes], bytes]:
    """Width, height, the bytes of a pixel and the rows of an 8-bit PNG without interlace (grey, RGB, palette, grey with alpha or RGBA),
    unfiltered; and the palette (empty when there is none). A row of filter 0 (the frames of SDL have no other) costs nothing."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")
    pos, idat, palette = 8, [], b""
    width = height = depth = colour = interlace = 0
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, depth, colour, _c, _f, interlace = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            palette = body
        elif kind == b"IDAT":
            idat.append(body)
        elif kind == b"IEND":
            break
    if depth != 8 or interlace != 0:
        raise ValueError(f"{path}: only 8-bit PNGs without interlace are read")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[colour]
    raw = zlib.decompress(b"".join(idat))
    stride = width * channels
    rows: list[bytes] = []
    prev = bytes(stride)
    at = 0
    for _ in range(height):
        kind = raw[at]
        line = raw[at + 1:at + 1 + stride]
        at += 1 + stride
        if kind == 2:
            line = bytes((x + y) & 0xFF for x, y in zip(line, prev))
        elif kind != 0:
            out = bytearray(line)
            for i in range(stride):
                a = out[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                if kind == 1:
                    out[i] = (out[i] + a) & 0xFF
                elif kind == 3:
                    out[i] = (out[i] + (a + b) // 2) & 0xFF
                elif kind == 4:
                    p = a + b - c
                    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                    out[i] = (out[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 0xFF
            line = bytes(out)
        rows.append(line)
        prev = line
    return width, height, channels if colour != 3 else 1, rows, palette if colour == 3 else b""


def _rgb(line: bytes, channels: int, palette: bytes) -> tuple[bytes, bytes, bytes]:
    """The red, green and blue bytes of a row, each as one bytes object."""
    if palette:
        return (line.translate(bytes(palette[3 * i] if 3 * i < len(palette) else 0 for i in range(256))),
                line.translate(bytes(palette[3 * i + 1] if 3 * i + 1 < len(palette) else 0 for i in range(256))),
                line.translate(bytes(palette[3 * i + 2] if 3 * i + 2 < len(palette) else 0 for i in range(256))))
    if channels <= 2:
        grey = line[0::channels]
        return grey, grey, grey
    return line[0::channels], line[1::channels], line[2::channels]


SHIFT5 = bytes(i >> 5 for i in range(256))
SAMPLE = 2  # the brightness and the colours are counted on every second pixel of every second row: they only face wide limits


def measure(path: Path) -> dict:
    """The size, the fingerprint and the plain checks of a frame. The fingerprint (the mean colour of every cell) counts every pixel."""
    width, height, channels, rows, palette = read_png(path)
    edges = [(x * width + GRID_W - 1) // GRID_W for x in range(GRID_W + 1)]  # the first x of every column of cells
    sums = [[0, 0, 0] for _ in range(GRID_W * GRID_H)]
    counts = [0] * (GRID_W * GRID_H)
    lum_sum = lum_sq = black = n = 0
    colours = set()
    for y, line in enumerate(rows):
        red, green, blue = _rgb(line, channels, palette)
        cy = min(GRID_H - 1, y * GRID_H // height)
        for cx in range(GRID_W):
            x0, x1 = edges[cx], edges[cx + 1]
            cell = sums[cy * GRID_W + cx]
            cell[0] += sum(red[x0:x1])
            cell[1] += sum(green[x0:x1])
            cell[2] += sum(blue[x0:x1])
            counts[cy * GRID_W + cx] += x1 - x0
        if y % SAMPLE == 0:
            r_s, g_s, b_s = red[::SAMPLE], green[::SAMPLE], blue[::SAMPLE]
            for r, g, b in zip(r_s, g_s, b_s):
                lum = (299 * r + 587 * g + 114 * b) // 1000
                lum_sum += lum
                lum_sq += lum * lum
                black += lum < 12
            n += len(r_s)
            colours.update(zip(r_s.translate(SHIFT5), g_s.translate(SHIFT5), b_s.translate(SHIFT5)))
    mean = lum_sum / n
    return {"size": [width, height], "spread": round((lum_sq / n - mean * mean) ** 0.5, 1), "black": round(black / n, 3),
            "colours": len(colours), "grid": [[c[0] // k, c[1] // k, c[2] // k] for c, k in zip(sums, counts)]}


def check(folder: Path) -> list[str]:
    ref_path = REFS / f"{folder.name}.json"
    if not ref_path.exists():
        return [f"{folder.name}: no reference {ref_path.relative_to(ROOT)} (write it with --write)"]
    refs = json.loads(ref_path.read_text(encoding="utf-8"))["frames"]
    problems = []
    for name, ref in refs.items():
        path = folder / name
        if not path.exists():
            problems.append(f"{folder.name}/{name}: missing")
            continue
        got = measure(path)
        where = f"{folder.name}/{name}"
        if got["size"][0] < 640 or got["size"][1] < 360:
            problems.append(f"{where}: too small, {got['size']}")
        if got["spread"] < MIN_SPREAD:
            problems.append(f"{where}: blank (spread {got['spread']})")
        if got["black"] > MAX_BLACK:
            problems.append(f"{where}: black ({got['black']:.0%} of the pixels)")
        if got["colours"] < MIN_COLOURS:
            problems.append(f"{where}: only {got['colours']} colours")
        diff = sum(abs(a - b) for cell, ref_cell in zip(got["grid"], ref["grid"]) for a, b in zip(cell, ref_cell)) / (GRID_W * GRID_H * 3)
        if diff > TOLERANCE:
            problems.append(f"{where}: far from its reference (mean difference {diff:.1f} > {TOLERANCE})")
        print(f"  {where}: spread {got['spread']}, colours {got['colours']}, difference {diff:.1f}")
    return problems


def write(folder: Path) -> None:
    frames = {path.name: {"grid": measure(path)["grid"]} for path in sorted(folder.glob("*.png"))}
    REFS.mkdir(parents=True, exist_ok=True)
    doc = {"$comment": "Written by tools/check_frames.py --write from the smoke-test screenshots of the CI; never edit by hand.",
           "grid": [GRID_W, GRID_H], "frames": frames}
    text = json.dumps(doc, separators=(",", ":")).replace('},"', '},\n"') + "\n"
    (REFS / f"{folder.name}.json").write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {len(frames)} references for {folder.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folders", nargs="+", type=Path)
    parser.add_argument("--write", action="store_true", help="write the references from these frames")
    args = parser.parse_args()
    if args.write:
        for folder in args.folders:
            write(folder)
        return 0
    problems = [p for folder in args.folders for p in check(folder)]
    for p in problems:
        print(f"FAIL {p}")
    print("OK: the frames look like their references" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
