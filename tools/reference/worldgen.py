"""World generation v1 (docs/spec/09-worldgen.md). Integer arithmetic only (spec 01), no floating point.

The world is a pure function of (seed, parameters): every tile and prop depends only on its own coordinates.
"""
from __future__ import annotations

from .numerics import M64, fbm2, fnv1a64, hash64

GID_BORDER = "water"
CHUNK_SIZE = 32


def _coord(x: int, scale: int) -> int:
    """Q16.16 noise coordinate of tile coordinate x >= 0 for a noise whose first octave has period `scale` tiles."""
    return (x << 16) // scale


def field(seed: int, spec: dict, x: int, y: int) -> int:
    """One noise field (0..65535) at tile (x, y)."""
    salted = hash64(seed, spec["salt"])
    return fbm2(salted, _coord(x, spec["scale"]), _coord(y, spec["scale"]), spec["octaves"])


def biome_at(seed: int, params: dict, x: int, y: int) -> str:
    """Biome of the tile: water, beach, mountain, snow, desert, forest or plains."""
    w, h = params["width"], params["height"]
    border = params["border"]
    if x < border or y < border or x >= w - border or y >= h - border:
        return "water"
    cx, cy = w // 2, h // 2
    r = params["spawn_clear_radius"]
    if (x - cx) ** 2 + (y - cy) ** 2 < r * r:
        return "plains"
    t = params["thresholds"]
    e = field(seed, params["elevation"], x, y)
    if e < t["water"]:
        return "water"
    if e < t["beach"]:
        return "beach"
    if e >= t["mountain"]:
        return "mountain"
    temp = field(seed, params["temperature"], x, y)
    if temp < t["snow"]:
        return "snow"
    moist = field(seed, params["moisture"], x, y)
    if temp >= t["desert_heat"] and moist < t["desert_dry"]:
        return "desert"
    if moist >= t["forest_wet"]:
        return "forest"
    return "plains"


def gid_for(seed: int, params: dict, biome: str, x: int, y: int) -> int:
    tiles = params["tiles"]
    if biome == "plains":
        variants = tiles["plains"]
        return variants[(hash64(seed, x, y, 5) >> 40) % len(variants)]
    return tiles[biome]


def prop_at(seed: int, params: dict, biome: str, x: int, y: int) -> dict | None:
    """The prop standing on tile (x, y), or None. Positions are in 1/256 tile units."""
    options = params["props"].get(biome, [])
    if not options:
        return None
    h = hash64(seed, x, y, 7)
    roll = (h >> 20) % 1000
    total = 0
    for option in options:
        total += option["per_mille"]
        if roll < total:
            return {"art": option["art"], "radius_x100": option["radius_x100"],
                    "x256": x * 256 + 48 + ((h >> 8) & 0x7F), "y256": y * 256 + 128 + ((h >> 16) & 0x7F)}
    return None


def spawner_at(seed: int, params: dict, biome: str, x: int, y: int) -> bool:
    s = params["spawners"]
    if biome not in s["biomes"]:
        return False
    cx, cy = params["width"] // 2, params["height"] // 2
    if (x - cx) ** 2 + (y - cy) ** 2 < s["min_distance"] ** 2:
        return False
    return (hash64(seed, x, y, 11) >> 20) % 10000 < s["per_10000"]


def generate(seed: int, params: dict) -> dict:
    """Tiles (row-major gids), props and spawners (both in scan order), the spawn point and the NPCs."""
    w, h = params["width"], params["height"]
    tiles: list[int] = []
    props: list[dict] = []
    spawners: list[list[int]] = []
    for y in range(h):
        for x in range(w):
            biome = biome_at(seed, params, x, y)
            tiles.append(gid_for(seed, params, biome, x, y))
            cx, cy = w // 2, h // 2
            if (x - cx) ** 2 + (y - cy) ** 2 >= params["spawn_clear_radius"] ** 2:
                prop = prop_at(seed, params, biome, x, y)
                if prop is not None:
                    props.append(prop)
                if spawner_at(seed, params, biome, x, y):
                    spawners.append([x, y])
    cx, cy = w // 2, h // 2
    return {"tiles": tiles, "props": props, "spawners": spawners,
            "spawn": [cx * 256 + 128, cy * 256 + 128],
            "npcs": [{**npc, "x256": (cx + npc["dx"]) * 256 + 128, "y256": (cy + npc["dy"]) * 256 + 128}
                     for npc in params["npcs"]]}


def generate_chunk(seed: int, params: dict, cx: int, cy: int) -> dict:
    """The CHUNK_SIZE x CHUNK_SIZE window of tiles starting at tile (cx * CHUNK_SIZE, cy * CHUNK_SIZE).

    Chunk coordinates may be any integers: tiles outside the world are water. Tiles are row-major; props and
    spawners are in scan order inside the chunk. The result is exactly the restriction of `generate` to the window.
    """
    w, h = params["width"], params["height"]
    clear = params["spawn_clear_radius"] ** 2
    mid_x, mid_y = w // 2, h // 2
    tiles: list[int] = []
    props: list[dict] = []
    spawners: list[list[int]] = []
    for y in range(cy * CHUNK_SIZE, (cy + 1) * CHUNK_SIZE):
        for x in range(cx * CHUNK_SIZE, (cx + 1) * CHUNK_SIZE):
            biome = biome_at(seed, params, x, y)
            tiles.append(gid_for(seed, params, biome, x, y))
            if (x - mid_x) ** 2 + (y - mid_y) ** 2 >= clear:
                prop = prop_at(seed, params, biome, x, y)
                if prop is not None:
                    props.append(prop)
                if spawner_at(seed, params, biome, x, y):
                    spawners.append([x, y])
    return {"tiles": tiles, "props": props, "spawners": spawners}


# ---------------------------------------------------------------------------- streaming window

def chunk_spawners(seed: int, params: dict, cx: int, cy: int) -> list[list[int]]:
    """Same result as generate_chunk(...)["spawners"], faster: the (rare) hash test runs before the biome is computed."""
    s = params["spawners"]
    w, h = params["width"], params["height"]
    mid_x, mid_y = w // 2, h // 2
    clear = params["spawn_clear_radius"] ** 2
    result: list[list[int]] = []
    for y in range(cy * CHUNK_SIZE, (cy + 1) * CHUNK_SIZE):
        for x in range(cx * CHUNK_SIZE, (cx + 1) * CHUNK_SIZE):
            if (hash64(seed, x, y, 11) >> 20) % 10000 >= s["per_10000"]:
                continue
            d2 = (x - mid_x) ** 2 + (y - mid_y) ** 2
            if d2 < clear or d2 < s["min_distance"] ** 2:
                continue
            if biome_at(seed, params, x, y) in s["biomes"]:
                result.append([x, y])
    return result


ACTIVE_RADIUS = 2  # chunks around the player's chunk (Chebyshev distance) that are active: a 5 x 5 window


def window_chunks(cx: int, cy: int) -> list[tuple[int, int]]:
    """The active chunks around chunk (cx, cy), row-major (rows from the top, columns left to right)."""
    return [(i, j) for j in range(cy - ACTIVE_RADIUS, cy + ACTIVE_RADIUS + 1)
            for i in range(cx - ACTIVE_RADIUS, cx + ACTIVE_RADIUS + 1)]


class ChunkWindow:
    """Which enemies exist while the player moves through a streamed world (spec 09, "Streaming").

    An enemy exists iff its spawner lies in an active chunk and the spawner is not cleared. Chunks entering the window add
    their enemies at the end of the list (chunks row-major, spawners in scan order); chunks leaving remove theirs; the order of
    the others never changes. A killed enemy stays in the list (dead) until its chunk leaves, and its spawner is cleared.
    """

    def __init__(self, seed: int, params: dict, cx: int, cy: int):
        self.seed, self.params = seed, params
        self.cleared: set[tuple[int, int]] = set()
        self.enemies: list[dict] = []  # {"x", "y", "dead"} by spawner tile
        self.cx, self.cy = cx, cy
        for chunk in window_chunks(cx, cy):
            self._enter(chunk)

    def _enter(self, chunk: tuple[int, int]) -> None:
        for x, y in chunk_spawners(self.seed, self.params, chunk[0], chunk[1]):
            if (x, y) not in self.cleared:
                self.enemies.append({"x": x, "y": y, "dead": False})

    def move_to(self, cx: int, cy: int) -> None:
        old = set(window_chunks(self.cx, self.cy))
        new = window_chunks(cx, cy)
        new_set = set(new)
        leaving = old - new_set
        self.enemies = [e for e in self.enemies if (e["x"] // CHUNK_SIZE, e["y"] // CHUNK_SIZE) not in leaving]
        for chunk in new:
            if chunk not in old:
                self._enter(chunk)
        self.cx, self.cy = cx, cy

    def kill(self, index: int) -> None:
        enemy = self.enemies[index]
        enemy["dead"] = True
        self.cleared.add((enemy["x"], enemy["y"]))

    def digest(self) -> int:
        h = 0
        for e in self.enemies:
            h = hash64(h, e["x"], e["y"], 1 if e["dead"] else 0)
        return h


# ---------------------------------------------------------------------------- digests (vectors)

def digest_all(tiles: list[int]) -> int:
    """Hash of a whole tile array: fold hash64 over the gids."""
    h = 0
    for gid in tiles:
        h = hash64(h, gid)
    return h


def digest_tiles(tiles: list[int], width: int, row: int) -> int:
    """Hash of one row of tiles: fold hash64 over the gids."""
    h = 0
    for gid in tiles[row * width:(row + 1) * width]:
        h = hash64(h, gid)
    return h


def digest_props(props: list[dict]) -> int:
    h = 0
    for p in props:
        h = hash64(h, p["x256"], p["y256"], p["radius_x100"] * 4294967296 + (fnv1a64(p["art"].encode("utf-8")) >> 32))
    return h & M64
