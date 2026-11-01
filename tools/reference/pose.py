"""Rig pose evaluation (docs/spec/13-vector-art.md). Floating point, compared with a tolerance."""
from __future__ import annotations

import math


def _interp(keys: list[list[float]], t: float, width: int) -> list[float]:
    """Linear interpolation of keyframes [[tick, v...], ...]; clamps outside the key range."""
    if not keys:
        return [0.0] * width
    if t <= keys[0][0]:
        return [float(v) for v in keys[0][1:1 + width]]
    if t >= keys[-1][0]:
        return [float(v) for v in keys[-1][1:1 + width]]
    for a, b in zip(keys, keys[1:]):
        if a[0] <= t <= b[0]:
            span = b[0] - a[0]
            u = 0.0 if span == 0 else (t - a[0]) / span
            return [a[i] + (b[i] - a[i]) * u for i in range(1, width + 1)]
    return [0.0] * width


def clip_time(clip: dict, tick: float) -> float:
    length = clip["length_ticks"]
    if clip.get("loop", False):
        return tick % length
    return min(tick, float(length))


def evaluate_pose(rig: dict, clip: dict, tick: float, mirror: bool) -> list[dict]:
    """World placement of every rig part at `tick`. Parts must be listed parents first."""
    t = clip_time(clip, tick)
    tracks = clip.get("tracks", {})
    world: dict[str, tuple[float, float, float]] = {}
    out = []
    for part in rig["parts"]:
        track = tracks.get(part["id"], {})
        rot = _interp(track.get("rot", []), t, 1)[0]
        px, py = _interp(track.get("pos", []), t, 2)
        lx = part["offset"][0] + px
        ly = part["offset"][1] + py
        parent = part.get("parent")
        if parent is None:
            wx, wy, wrot = lx, ly, rot
        else:
            pwx, pwy, pwrot = world[parent]
            r = math.radians(pwrot)
            wx = pwx + math.cos(r) * lx - math.sin(r) * ly
            wy = pwy + math.sin(r) * lx + math.cos(r) * ly
            wrot = pwrot + rot
        world[part["id"]] = (wx, wy, wrot)
        out.append({
            "part": part["id"],
            "x": -wx if mirror else wx,
            "y": wy,
            "rot": -wrot if mirror else wrot,
            "z": part.get("z", 0),
        })
    return out
