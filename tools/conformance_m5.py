"""Conformance suite added in M5: world generation (spec 09). Generated worlds are compared through digests."""
from __future__ import annotations

import json
from pathlib import Path

from reference import numerics as nm
from reference import worldgen, worldtime

ROOT = Path(__file__).resolve().parent.parent
PARAMS = json.loads((ROOT / "data" / "base" / "worlds" / "overworld.json").read_text(encoding="utf-8"))


def h64(value: int) -> str:
    return f"0x{value & nm.M64:016x}"


def digest_pairs(pairs: list[list[int]]) -> int:
    h = 0
    for x, y in pairs:
        h = nm.hash64(h, x, y)
    return h


def suite_worldgen_chunks() -> list[dict]:
    """Chunks of a huge world (16384 x 16384 tiles), far from the origin and across the world edge."""
    params = {**PARAMS, "width": 16384, "height": 16384}
    cases = []
    for name, seed, chunks in (
        ("seed_7", 7, [[0, 0], [255, 255], [256, 256], [100, 400], [511, 511], [512, 3], [-1, 5]]),
        ("seed_max_u64", nm.M64, [[1, 1], [256, 255], [333, 17], [3, 500]]),
    ):
        results = []
        for cx, cy in chunks:
            chunk = worldgen.generate_chunk(seed, params, cx, cy)
            size = worldgen.CHUNK_SIZE
            probes = []
            for i in range(12):
                lx = nm.hash64(seed, cx * 1000 + i, 1) % size
                ly = nm.hash64(seed, cy * 1000 + i, 2) % size
                probes.append([lx, ly, chunk["tiles"][ly * size + lx]])
            results.append({
                "chunk": [cx, cy],
                "probes": probes,
                "tile_digest": h64(worldgen.digest_all(chunk["tiles"])),
                "prop_count": len(chunk["props"]),
                "prop_digest": h64(worldgen.digest_props(chunk["props"])),
                "spawner_count": len(chunk["spawners"]),
                "spawner_digest": h64(digest_pairs(chunk["spawners"])),
                "gid_histogram": {str(g): chunk["tiles"].count(g) for g in sorted(set(chunk["tiles"]))},
            })
        cases.append({
            "name": f"worldgen_chunks_{name}",
            "input": {"op": "worldgen_chunks", "seed": h64(seed), "chunk_size": worldgen.CHUNK_SIZE, "params": params},
            "expect": {"chunks": results},
        })
    return cases


def suite_chunk_window() -> list[dict]:
    """Scripted walks through a huge world: the enemies that exist after each step (spec 09, "Streaming")."""
    params = {**PARAMS, "width": 16384, "height": 16384}
    scripts = {
        "walk_and_kill": (7, (256, 256), [
            ["move", 257, 256], ["move", 258, 258], ["kill", 0], ["kill", 1], ["move", 256, 256],
            ["move", 300, 300], ["move", 300, 299], ["move", 258, 258], ["move", 256, 256],
            # Too early: the killed spawners stay cleared. Then enough time passes and they respawn on re-entering.
            ["wait", 20000], ["move", 300, 300], ["move", 258, 258], ["wait", 20000], ["move", 300, 300], ["move", 258, 258],
        ]),
        "long_jumps": (0xBEEF, (100, 400), [
            ["move", 101, 400], ["move", 101, 401], ["kill", 0], ["move", 0, 0], ["move", 511, 511], ["move", 100, 400],
            ["move", 101, 401], ["wait", 36000], ["move", 0, 0], ["move", 101, 401],
        ]),
    }
    cases = []
    for name, (seed, start, steps) in scripts.items():
        window = worldgen.ChunkWindow(seed, params, start[0], start[1])
        results = [{"op": "start", "count": len(window.enemies), "digest": h64(window.digest())}]
        for step in steps:
            if step[0] == "move":
                window.move_to(step[1], step[2])
            elif step[0] == "wait":
                window.wait(step[1])
            else:
                assert len(window.enemies) > step[1], f"{name}: no enemy {step[1]} to kill"
                window.kill(step[1])
            results.append({"op": step[0], "count": len(window.enemies), "digest": h64(window.digest())})
        cases.append({
            "name": f"chunk_window_{name}",
            "input": {"op": "chunk_window", "seed": h64(seed), "start": list(start), "steps": steps, "params": params},
            "expect": {"after": results},
        })
    return cases


def suite_worldtime() -> list[dict]:
    """Day, light and weather at a list of world ticks (spec 08)."""
    t = PARAMS["time"]
    ticks = [0, 1, 17999, 18000, 18001, 18300, 18599, 18600, 24000, 35999, 36000, 71999, 72000, 100000, 1_000_000, 123_456_789, 2**40]
    cases = []
    for name, seed in (("seed_1", 1), ("seed_c0ffee", 0xC0FFEE), ("seed_max_u64", nm.M64)):
        samples = []
        for tick in ticks:
            samples.append({"ticks": tick, **worldtime.sample(seed, t, tick)})
        cases.append({"name": f"worldtime_{name}", "input": {"op": "worldtime", "seed": h64(seed), "time": t},
                      "expect": {"samples": samples}})
    return cases


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
