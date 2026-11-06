"""Conformance suites added in M2: rig_pose, movement, raster. Imported by gen_conformance.py.

The raster expectations are computed analytically (the Python reference has no rasterizer), so they
check both clients against geometry instead of against each other.
"""
from __future__ import annotations

import math

from reference import movement, pose


def case(name: str, inp: dict, expect: dict) -> dict:
    return {"name": name, "input": inp, "expect": expect}


# -------------------------------------------------------------------------------------- pose

POSE_RIG = {
    "id": "test:art/rig/arm_chain",
    "parts": [
        {"id": "torso", "parent": None, "offset": [0, 0], "z": 0, "art": "test:art/part/torso"},
        {"id": "arm", "parent": "torso", "offset": [2, -1], "z": 1, "art": "test:art/part/arm"},
        {"id": "hand", "parent": "arm", "offset": [0, 3], "z": 2, "art": "test:art/part/hand"},
    ],
}
POSE_CLIP = {
    "id": "test:art/clip/wave",
    "rig": "test:art/rig/arm_chain",
    "loop": True,
    "length_ticks": 24,
    "tracks": {
        "torso": {"rot": [[0, 0], [12, 10], [24, 0]], "pos": [[0, 0, 0], [12, 0, -1], [24, 0, 0]]},
        "arm": {"rot": [[0, -30], [12, 60], [24, -30]]},
    },
}


def suite_rig_pose() -> list[dict]:
    cases = []
    for loop, ticks in ((True, (0, 6, 12, 18, 24, 30)), (False, (0, 12, 24, 40))):
        clip = dict(POSE_CLIP, loop=loop)
        for mirror in (False, True):
            for tick in ticks:
                cases.append(case(
                    f"pose_{'loop' if loop else 'once'}_{'mirror' if mirror else 'plain'}_{tick}",
                    {"op": "pose", "rig": POSE_RIG, "clip": clip, "tick": tick, "mirror": mirror},
                    {"parts": pose.evaluate_pose(POSE_RIG, clip, tick, mirror), "tol": 0.001}))
    return cases


# ----------------------------------------------------------------------------------- movement

GRID_ROWS = ["########",
             "#......#",
             "#..#...#",
             "#......#",
             "#......#",
             "########"]
PROPS = [(5.5, 3.5, 0.4)]


def suite_movement() -> list[dict]:
    scripts = {
        "axis_moves": ((1.5, 1.5), [(1, 0, 60), (0, 1, 60), (-1, 0, 30), (0, -1, 60)]),
        "diagonals": ((1.5, 1.5), [(1, 1, 90), (-1, 1, 40), (1, -1, 100)]),
        "deadzone_and_half_stick": ((2.5, 3.5), [(0.1, 0.05, 30), (0.5, 0, 60)]),
        "walls": ((1.5, 1.5), [(1, 0, 200), (0, 1, 200), (-1, 0, 200), (0, -1, 200)]),
        "prop_blocks": ((1.5, 3.5), [(1, 0, 200)]),
        "prop_slide": ((5.5, 1.5), [(0, 1, 120), (0.3, 1, 60)]),
        "inner_wall": ((1.5, 2.5), [(1, 0, 120), (0, 1, 30), (1, 0, 60)]),
    }
    cases = []
    for name, (start, script) in scripts.items():
        positions = movement.run_script(GRID_ROWS, PROPS, start, 4.0, script)
        cases.append(case(
            f"move_{name}",
            {"op": "movement", "grid": GRID_ROWS, "props": [list(p) for p in PROPS], "start": list(start),
             "speed": 4.0, "script": [list(s) for s in script]},
            {"positions": [list(p) for p in positions], "tol": 0.002}))
    for x, y in ((0, 0), (0.1, 0.1), (0.2, 0), (1, 1), (-1, 0.5), (0.5, 0.5), (3, 4)):
        nx, ny = movement.normalize_input(x, y)
        cases.append(case(f"normalize_{x}_{y}", {"op": "normalize_input", "x": x, "y": y},
                          {"x": nx, "y": ny, "tol": 0.0001}))
    return cases


# -------------------------------------------------------------------------------------- raster

def _rnd(value: float) -> int:
    return int(math.floor(value + 0.5))


def _recipe(w: int, h: int, layers: list[dict], palette: dict | None = None,
            variants: dict | None = None) -> dict:
    recipe = {"id": "test:art/probe", "canvas": {"w": w, "h": h, "origin": [0, 0]}, "layers": layers}
    if palette:
        recipe["palette"] = palette
    if variants:
        recipe["variants"] = variants
    return recipe


def _probe(x: int, y: int, rgba: list[int], tol: int = 2) -> dict:
    return {"x": x, "y": y, "rgba": rgba, "tol": tol}


def _quad_flatten(p0, p1, p2, segments=12):
    points = []
    for i in range(segments + 1):
        t = i / segments
        a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t ** 2
        points.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))
    return points


def _shoelace(points) -> float:
    n = len(points)
    total = 0.0
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        total += x0 * y1 - x1 * y0
    return abs(total) / 2


def suite_raster() -> list[dict]:
    red = {"color": "#FF0000"}
    cases: list[dict] = []

    def add(name, recipe, scale, expect, variant=None):
        cases.append(case(name, {"op": "raster", "recipe": recipe, "scale": scale, "variant": variant}, expect))

    add("rect_full", _recipe(8, 8, [{"shape": {"rect": [2, 2, 4, 4]}, "fill": red}]), 1.0,
        {"width": 8, "height": 8,
         "probes": [_probe(3, 3, [255, 0, 0, 255]), _probe(2, 2, [255, 0, 0, 255]), _probe(5, 5, [255, 0, 0, 255]),
                    _probe(1, 1, [0, 0, 0, 0]), _probe(6, 6, [0, 0, 0, 0]), _probe(0, 7, [0, 0, 0, 0])]})
    add("rect_half_pixel", _recipe(8, 8, [{"shape": {"rect": [2.5, 2, 3, 4]}, "fill": red}]), 1.0,
        {"width": 8, "height": 8,
         "probes": [_probe(2, 3, [255, 0, 0, 128]), _probe(5, 3, [255, 0, 0, 128]),
                    _probe(3, 3, [255, 0, 0, 255]), _probe(1, 3, [0, 0, 0, 0])]})
    add("layer_alpha", _recipe(4, 4, [{"shape": {"rect": [0, 0, 4, 4]}, "fill": red, "alpha": 0.5}]), 1.0,
        {"width": 4, "height": 4, "probes": [_probe(1, 1, [255, 0, 0, 128], 1)]})
    add("color_alpha", _recipe(4, 4, [{"shape": {"rect": [0, 0, 4, 4]}, "fill": {"color": "#00FF0080"}}]), 1.0,
        {"width": 4, "height": 4, "probes": [_probe(2, 2, [0, 255, 0, 128], 1)]})
    add("scale_two", _recipe(8, 8, [{"shape": {"rect": [2, 2, 4, 4]}, "fill": red}]), 2.0,
        {"width": 16, "height": 16,
         "probes": [_probe(4, 4, [255, 0, 0, 255]), _probe(11, 11, [255, 0, 0, 255]),
                    _probe(3, 3, [0, 0, 0, 0]), _probe(12, 12, [0, 0, 0, 0])]})
    add("scale_fractional_size", _recipe(10, 6, [{"shape": {"rect": [0, 0, 10, 6]}, "fill": red}]), 1.5,
        {"width": 15, "height": 9,
         "probes": [_probe(14, 8, [255, 0, 0, 255]), _probe(0, 0, [255, 0, 0, 255])]})
    add("ellipse_area", _recipe(32, 32, [{"shape": {"ellipse": [16, 16, 12, 12]}, "fill": red}]), 1.0,
        {"width": 32, "height": 32,
         "probes": [_probe(16, 16, [255, 0, 0, 255]), _probe(0, 0, [0, 0, 0, 0]), _probe(31, 31, [0, 0, 0, 0])],
         "sum_alpha": {"value": math.pi * 144, "rel_tol": 0.02}})
    grad = {"linear": {"x0": 0, "y0": 0, "x1": 16, "y1": 0, "stops": [[0, "#FF0000"], [1, "#0000FF"]]}}
    probes = []
    for x in (0, 7, 15):
        tt = (x + 0.5) / 16
        probes.append(_probe(x, 1, [_rnd(255 * (1 - tt)), 0, _rnd(255 * tt), 255]))
    add("linear_gradient", _recipe(16, 4, [{"shape": {"rect": [0, 0, 16, 4]}, "fill": grad}]), 1.0,
        {"width": 16, "height": 4, "probes": probes})
    radial = {"radial": {"cx": 8, "cy": 8, "r": 8, "stops": [[0, "#FFFFFF"], [1, "#000000"]]}}
    v = _rnd(255 * (1 - math.sqrt(0.5) / 8))
    add("radial_gradient", _recipe(16, 16, [{"shape": {"rect": [0, 0, 16, 16]}, "fill": radial}]), 1.0,
        {"width": 16, "height": 16, "probes": [_probe(7, 7, [v, v, v, 255], 3), _probe(0, 0, [0, 0, 0, 255])]})
    add("stroke_polygon",
        _recipe(16, 16, [{"shape": {"polygon": [[4, 4], [12, 4], [12, 12], [4, 12]]},
                          "stroke": {"color": "#00FF00", "width": 2}}]), 1.0,
        {"width": 16, "height": 16,
         "probes": [_probe(4, 8, [0, 255, 0, 255]), _probe(8, 4, [0, 255, 0, 255]), _probe(8, 8, [0, 0, 0, 0]),
                    _probe(2, 8, [0, 0, 0, 0])]})
    palette = {"c": "#FF0000"}
    variants = {"blue": {"c": "#0000FF"}}
    layer = [{"shape": {"rect": [0, 0, 4, 4]}, "fill": {"color": "$p.c"}}]
    add("palette_default", _recipe(4, 4, layer, palette, variants), 1.0,
        {"width": 4, "height": 4, "probes": [_probe(1, 1, [255, 0, 0, 255], 0)]})
    add("palette_variant", _recipe(4, 4, layer, palette, variants), 1.0,
        {"width": 4, "height": 4, "probes": [_probe(1, 1, [0, 0, 255, 255], 0)]}, variant="blue")
    # layers that belong to some variants only (spec 13: `only` and `except`)
    filtered = [{"shape": {"rect": [0, 0, 4, 4]}, "fill": {"color": "#808080"}},
                {"shape": {"rect": [0, 0, 2, 4]}, "fill": {"color": "#00FF00"}, "only": ["blue"]},
                {"shape": {"rect": [2, 0, 2, 4]}, "fill": {"color": "#FF0000"}, "except": ["blue"]}]
    grey, green, red_px = [128, 128, 128, 255], [0, 255, 0, 255], [255, 0, 0, 255]
    add("layer_only_except_base", _recipe(4, 4, filtered, palette, variants), 1.0,
        {"width": 4, "height": 4, "probes": [_probe(1, 1, grey, 0), _probe(3, 1, red_px, 0)]})
    add("layer_only_except_variant", _recipe(4, 4, filtered, palette, variants), 1.0,
        {"width": 4, "height": 4, "probes": [_probe(1, 1, green, 0), _probe(3, 1, grey, 0)]}, variant="blue")
    add("path_square", _recipe(8, 8, [{"shape": {"path": "M 2 2 L 6 2 L 6 6 L 2 6 Z"}, "fill": red}]), 1.0,
        {"width": 8, "height": 8,
         "probes": [_probe(3, 3, [255, 0, 0, 255]), _probe(1, 1, [0, 0, 0, 0]), _probe(6, 6, [0, 0, 0, 0])]})
    add("path_hv_commands", _recipe(8, 8, [{"shape": {"path": "M 1 1 H 7 V 7 H 1 Z"}, "fill": red}]), 1.0,
        {"width": 8, "height": 8, "probes": [_probe(4, 4, [255, 0, 0, 255]), _probe(0, 0, [0, 0, 0, 0])]})
    curve_area = _shoelace(_quad_flatten((2, 8), (8, 0), (14, 8)))
    add("path_quadratic_area", _recipe(16, 16, [{"shape": {"path": "M 2 8 Q 8 0 14 8 Z"}, "fill": red}]), 1.0,
        {"width": 16, "height": 16, "probes": [_probe(8, 6, [255, 0, 0, 255]), _probe(8, 12, [0, 0, 0, 0])],
         "sum_alpha": {"value": curve_area, "rel_tol": 0.03}})
    return cases
