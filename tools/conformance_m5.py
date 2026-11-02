"""Conformance suite added in M5: world generation (spec 09). Generated worlds are compared through digests."""
from __future__ import annotations

from pathlib import Path

from reference import numerics as nm
from reference import guild, routines, worldgen, worldtime

ROOT = Path(__file__).resolve().parent.parent
PARAMS = worldgen.load_params()


def h64(value: int) -> str:
    return f"0x{value & nm.M64:016x}"


def digest_pairs(pairs: list[list[int]]) -> int:
    h = 0
    for x, y in pairs:
        h = nm.hash64(h, x, y)
    return h


def settlement_chunks(params: dict, seed: int) -> list[list[int]]:
    """Chunks over the center of a hamlet, a village and a town of the world (and one next to a footprint edge)."""
    chunks: list[list[int]] = []
    seen: set[str] = set()
    for site in worldgen.settlements_in(seed, params, 0, 0, 63, 63):
        if site["kind"] in seen:
            continue
        seen.add(site["kind"])
        chunks.append([site["px"] // worldgen.CHUNK_SIZE, site["py"] // worldgen.CHUNK_SIZE])
        chunks.append([(site["x"] + site["w"] - 1) // worldgen.CHUNK_SIZE, (site["y"] + site["h"] - 1) // worldgen.CHUNK_SIZE])
    return chunks


def suite_worldgen_chunks() -> list[dict]:
    """Chunks of a huge world (16384 x 16384 tiles), far from the origin and across the world edge."""
    params = {**PARAMS, "width": 16384, "height": 16384}
    cases = []
    for name, seed, chunks in (
        ("seed_7", 7, [[0, 0], [255, 255], [256, 256], [100, 400], [511, 511], [512, 3], [-1, 5]]),
        ("seed_max_u64", nm.M64, [[1, 1], [256, 255], [333, 17], [3, 500]]),
        ("settlements_seed_7", 7, settlement_chunks(params, 7)),
        ("settlements_seed_c0ffee", 0xC0FFEE, settlement_chunks(params, 0xC0FFEE)),
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
                "people": [[p["key"], p["role"], p["x256"], p["y256"], p["name"], p["variant"], p["tone"], p["dialogue"], p["place"],
                            p["region"], p["quirk"], p["plaza_x256"], p["plaza_y256"]] for p in chunk["people"]],
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


def suite_settlements() -> list[dict]:
    """Regions of tiles and the settlements of blocks of site cells (spec 09, "Regions" and "Settlements")."""
    params = {**PARAMS, "width": 16384, "height": 16384}
    cases = []
    for name, seed, block in (("seed_7", 7, [0, 0, 63, 63]), ("seed_c0ffee", 0xC0FFEE, [8, 8, 31, 31]),
                              ("seed_max_u64", nm.M64, [20, 20, 43, 43])):
        found = worldgen.settlements_in(seed, params, *block)
        regions = []
        for i in range(40):
            x = nm.hash64(seed, i, 51) % params["width"]
            y = nm.hash64(seed, i, 52) % params["height"]
            regions.append([x, y, worldgen.region_at(params, x, y)])
        markers = []
        for site in found[:30]:
            markers.append([site["px"] // worldgen.MAP_CELL, site["py"] // worldgen.MAP_CELL, site["name"]])
        cases.append({
            "name": f"settlements_{name}",
            "input": {"op": "settlements", "seed": h64(seed), "block": block, "params": params},
            "expect": {
                "count": len(found),
                "settlements": [[s["x"], s["y"], s["px"], s["py"], s["kind"], s["stamp"], s["name"], s["region"]] for s in found],
                "regions": regions,
                "markers": markers,
            },
        })
    return cases


def suite_routines() -> list[dict]:
    """Who is present, and where, over a day in the chunks of a few settlements (spec 08, "Routines")."""
    params = {**PARAMS, "width": 16384, "height": 16384}
    cases = []
    for name, seed in (("seed_7", 7), ("seed_c0ffee", 0xC0FFEE)):
        sites = [worldgen.Sites(seed, params).site(32, 32)]
        seen: set[str] = set()
        for site in worldgen.settlements_in(seed, params, 0, 0, 63, 63):
            if site["kind"] not in seen:
                seen.add(site["kind"])
                sites.append(site)
        chunks = set()
        for site in sites:
            for cy in range(site["y"] // worldgen.CHUNK_SIZE, (site["y"] + site["h"] - 1) // worldgen.CHUNK_SIZE + 1):
                for cx in range(site["x"] // worldgen.CHUNK_SIZE, (site["x"] + site["w"] - 1) // worldgen.CHUNK_SIZE + 1):
                    chunks.add((cx, cy))
        ordered = sorted(chunks, key=lambda c: (c[1], c[0]))  # row-major
        times = [0, 100, 249, 250, 279, 280, 299, 300, 500, 699, 700, 759, 760, 799, 800, 899, 900, 999]
        people = [person for cx, cy in ordered for person in worldgen.generate_chunk(seed, params, cx, cy)["people"]]
        present = []
        for tod in times:
            row = []
            for person in people:
                found = routines.placement(params, person, tod)
                if found is not None:
                    row.append([person["key"], found[0], found[1], found[2]])
            present.append(row)
        cases.append({
            "name": f"routines_{name}",
            "input": {"op": "routines", "seed": h64(seed), "chunks": [list(c) for c in ordered], "times": times, "params": params},
            "expect": {"present": present},
        })
    return cases


def suite_fauna() -> list[dict]:
    """The enemy of spawners in every region: a weighted pick among the fauna of the region (spec 09, "Fauna")."""
    params = {**PARAMS, "width": 16384, "height": 16384}
    cases = []
    for name, seed in (("seed_7", 7), ("seed_c0ffee", 0xC0FFEE)):
        tiles = []
        for region in params["regions"]:
            cx = region["x_pm"] * params["width"] // 1000 // 32
            cy = region["y_pm"] * params["height"] // 1000 // 32
            found = []
            for j in range(cy - 2, cy + 3):
                for i in range(cx - 2, cx + 3):
                    found.extend(worldgen.chunk_spawners(seed, params, i, j))
            tiles.extend(found[:12])
        expect = [[x, y, worldgen.region_at(params, x, y), worldgen.fauna_at(seed, params, x, y)["enemy"],
                   worldgen.fauna_at(seed, params, x, y)["drop"]] for x, y in tiles]
        cases.append({
            "name": f"fauna_{name}",
            "input": {"op": "fauna", "seed": h64(seed), "tiles": tiles, "params": params},
            "expect": {"spawners": expect},
        })
    return cases


def suite_guild() -> list[dict]:
    """Ranks, the board offers of settlements on several days and the quests they become (spec 07, "Guild")."""
    params = {**PARAMS, "width": 16384, "height": 16384}
    cases = []
    for name, seed in (("seed_7", 7), ("seed_c0ffee", 0xC0FFEE), ("seed_max_u64", nm.M64)):
        found = worldgen.settlements_in(seed, params, 0, 0, 63, 63)
        sites = [[32, 32]] + [[s["sx"], s["sy"]] for s in found[:5]]
        days = [1, 2, 9, 400]
        listed = []
        quests = []
        for sx, sy in sites:
            for day in days:
                for offer in guild.offers(seed, params, sx, sy, day):
                    listed.append([offer["id"], offer["min_rank"], offer["template"], offer["type"], offer["target"], offer["count"],
                                   offer["gold"], offer["xp"], offer["points"], offer["place"], offer["tone"]])
                    quests.append(guild.quest_def(offer))
        points = [0, 1, 99, 100, 299, 300, 699, 700, 1499, 1500, 2999, 3000, 5999, 6000, 99999]
        cases.append({
            "name": f"guild_{name}",
            "input": {"op": "guild", "seed": h64(seed), "sites": sites, "days": days, "points": points, "params": params},
            "expect": {"offers": listed, "quests": quests, "ranks": [[x, guild.rank_index(params["guild"], x)] for x in points]},
        })
    return cases


def suite_worldmap() -> list[dict]:
    """The biome of world map cells and the cells explored along a walk (spec 09, "Exploration and the world map")."""
    params = {**PARAMS, "width": 16384, "height": 16384}
    cases = []
    walks = {
        "from_the_spawn": (7, [[8192, 8192], [8200, 8192], [8350, 8192], [8350, 8400], [8100, 8100], [8100, 7800], [8192, 8192]]),
        "corners_and_edges": (0xBEEF, [[0, 0], [16383, 0], [16383, 16383], [0, 16383], [64, 8192], [8192, 16000], [127, 128]]),
    }
    for name, (seed, positions) in walks.items():
        cells: set = set()
        for x, y in positions:
            worldgen.explore(cells, params, x, y)
        samples = []
        for i in range(40):
            cx = nm.hash64(seed, i, 31) % 128
            cy = nm.hash64(seed, i, 32) % 128
            samples.append([cx, cy, worldgen.biome_code(seed, params, cx, cy)])
        cases.append({
            "name": f"worldmap_{name}",
            "input": {"op": "worldmap", "seed": h64(seed), "cell": worldgen.MAP_CELL, "positions": positions, "params": params},
            "expect": {"explored_count": len(cells), "explored_digest": h64(worldgen.digest_cells(cells)), "biomes": samples},
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
        params = {k: v for k, v in {**PARAMS, "width": 96, "height": 80, **overrides}.items() if k != "home"}
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
