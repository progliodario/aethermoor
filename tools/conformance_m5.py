"""Conformance suite added in M5: world generation (spec 09). Generated worlds are compared through digests."""
from __future__ import annotations

import json
from pathlib import Path

from reference import numerics as nm
from reference import worldgen

ROOT = Path(__file__).resolve().parent.parent
PARAMS = json.loads((ROOT / "data" / "base" / "worlds" / "overworld.json").read_text(encoding="utf-8"))


def h64(value: int) -> str:
    return f"0x{value & nm.M64:016x}"


def digest_pairs(pairs: list[list[int]]) -> int:
    h = 0
    for x, y in pairs:
        h = nm.hash64(h, x, y)
    return h


def suite_worldgen() -> list[dict]:
    cases = []
    for name, seed, overrides in (
        ("seed_1", 1, {}),
        ("seed_c0ffee_small_border", 0xC0FFEE, {"width": 80, "height": 72, "border": 2}),
        ("seed_max_u64", nm.M64, {"width": 88, "height": 96}),
    ):
        params = {**PARAMS, "width": 96, "height": 80, **overrides}
        world = worldgen.generate(seed, params)
        w, h = params["width"], params["height"]
        probes = []
        for i in range(120):
            x = nm.hash64(seed, i, 1) % w
            y = nm.hash64(seed, i, 2) % h
            probes.append([x, y, world["tiles"][y * w + x]])
        rows = [[y, h64(worldgen.digest_tiles(world["tiles"], w, y))] for y in range(0, h, 8)]
        cases.append({
            "name": f"worldgen_{name}",
            "input": {"op": "worldgen", "seed": h64(seed), "params": params},
            "expect": {
                "probes": probes,
                "row_digests": rows,
                "tile_count": len(world["tiles"]),
                "prop_count": len(world["props"]),
                "prop_digest": h64(worldgen.digest_props(world["props"])),
                "spawner_count": len(world["spawners"]),
                "spawner_digest": h64(digest_pairs(world["spawners"])),
                "spawn": world["spawn"],
                "npcs": [[n["key"], n["x256"], n["y256"]] for n in world["npcs"]],
                "gid_histogram": {str(g): world["tiles"].count(g) for g in sorted(set(world["tiles"]))},
            },
        })
    return cases
