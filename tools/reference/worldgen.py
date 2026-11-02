"""World generation (docs/spec/09-worldgen.md). Integer arithmetic only (spec 01), no floating point.

The world is a pure function of (seed, parameters): every tile and prop depends only on its own coordinates.
"""
from __future__ import annotations

import json
from pathlib import Path

from .numerics import M64, fbm2, fnv1a64, hash64, noise2

GID_BORDER = "water"
CHUNK_SIZE = 32
ROOT = Path(__file__).resolve().parent.parent.parent


def load_params(world_id: str = "overworld") -> dict:
    """The parameters of a world of the base pack with the stamps of its settlements resolved into `stamp_defs`."""
    params = json.loads((ROOT / "data" / "base" / "worlds" / f"{world_id}.json").read_text(encoding="utf-8"))
    stamps = {}
    wanted = [stamp_id for kind in params["settlements"]["kinds"] for stamp_id in kind["stamps"]]
    if "home" in params:
        wanted.append(params["home"]["stamp"])
    for stamp_id in wanted:
        path = ROOT / "data" / "base" / "stamps" / f"{stamp_id.rsplit('/', 1)[-1]}.json"
        stamps[stamp_id] = json.loads(path.read_text(encoding="utf-8"))
    return {**params, "stamp_defs": stamps}


# ---------------------------------------------------------------------------- regions

def region_at(params: dict, x: int, y: int) -> int:
    """Index of the region of tile (x, y): the nearest region center (squared distance, the lower index wins a tie)."""
    w, h = params["width"], params["height"]
    best, best_d = 0, None
    for index, region in enumerate(params["regions"]):
        dx = x - region["x_pm"] * w // 1000
        dy = y - region["y_pm"] * h // 1000
        d = dx * dx + dy * dy
        if best_d is None or d < best_d:
            best, best_d = index, d
    return best


# ---------------------------------------------------------------------------- settlements

SITE_CELL = 256  # tiles per side of a settlement site cell
SITE_MARGIN = 40  # a site lies at least this far from the border of its cell
SITE_SPAN = SITE_CELL - 2 * SITE_MARGIN  # 176 positions
SITE_BIOMES = ("plains", "forest")


class Sites:
    """The settlement of each site cell of a world (spec 09, "Settlements"), computed on demand."""

    def __init__(self, seed: int, params: dict) -> None:
        self.seed, self.params = seed, params
        self._cells: dict[tuple[int, int], dict | None] = {}

    def site(self, sx: int, sy: int) -> dict | None:
        key = (sx, sy)
        if key not in self._cells:
            self._cells[key] = self._compute(sx, sy)
        return self._cells[key]

    def _compute(self, sx: int, sy: int) -> dict | None:
        seed, params = self.seed, self.params
        cfg = params["settlements"]
        home = params.get("home")
        if home is not None:
            hx, hy = params["width"] // 2 + home["dx"], params["height"] // 2 + home["dy"]
            if (hx // SITE_CELL, hy // SITE_CELL) == (sx, sy):
                return self._home(sx, sy, hx, hy, home["stamp"])
        h = hash64(seed, sx, sy, 41)
        if (h >> 40) % 1000 >= cfg["per_mille"]:
            return None
        px = sx * SITE_CELL + SITE_MARGIN + (h >> 8) % SITE_SPAN
        py = sy * SITE_CELL + SITE_MARGIN + (h >> 24) % SITE_SPAN
        k = hash64(seed, sx, sy, 42)
        kinds = cfg["kinds"]
        roll = (k >> 20) % sum(kind["weight"] for kind in kinds)
        acc = 0
        kind = kinds[-1]
        for candidate in kinds:
            acc += candidate["weight"]
            if roll < acc:
                kind = candidate
                break
        stamp_id = kind["stamps"][(k >> 40) % len(kind["stamps"])]
        stamp = params["stamp_defs"][stamp_id]
        ox, oy = px - stamp["anchor"][0], py - stamp["anchor"][1]
        # The whole footprint must lie on plains or forest, and not touch the spawn clearing.
        mid_x, mid_y = params["width"] // 2, params["height"] // 2
        keep_out = params["spawn_clear_radius"] + 48
        if (px - mid_x) ** 2 + (py - mid_y) ** 2 < keep_out * keep_out:
            return None
        for x, y in ((px, py), (ox, oy), (ox + stamp["w"] - 1, oy), (ox, oy + stamp["h"] - 1),
                     (ox + stamp["w"] - 1, oy + stamp["h"] - 1)):
            if biome_at(seed, params, x, y) not in SITE_BIOMES:
                return None
        n = hash64(seed, sx, sy, 43)
        names = cfg["names"]
        name = names["start"][n % len(names["start"])] + names["mid"][(n >> 16) % len(names["mid"])] \
            + names["end"][(n >> 32) % len(names["end"])]
        return self._with_slots({"x": ox, "y": oy, "px": px, "py": py, "w": stamp["w"], "h": stamp["h"], "stamp": stamp_id,
                                 "kind": kind["id"], "name": name, "region": region_at(params, px, py)}, sx, sy)

    def _home(self, sx: int, sy: int, px: int, py: int, stamp_id: str) -> dict:
        """The home village: a settlement of fixed position, stamp and kind near the spawn (spec 09, "The home village")."""
        params = self.params
        stamp = params["stamp_defs"][stamp_id]
        names = params["settlements"]["names"]
        n = hash64(self.seed, sx, sy, 43)
        name = names["start"][n % len(names["start"])] + names["mid"][(n >> 16) % len(names["mid"])] \
            + names["end"][(n >> 32) % len(names["end"])]
        kind = next((k["id"] for k in params["settlements"]["kinds"] if stamp_id in k["stamps"]), "village")
        return self._with_slots({"x": px - stamp["anchor"][0], "y": py - stamp["anchor"][1], "px": px, "py": py, "w": stamp["w"],
                                 "h": stamp["h"], "stamp": stamp_id, "kind": kind, "name": name, "region": region_at(params, px, py)},
                                sx, sy)

    def _with_slots(self, site: dict, sx: int, sy: int) -> dict:
        """Adds the cell and the NPC slots of the stamp (its characters with an `npc` role, in scan order)."""
        stamp = self.params["stamp_defs"][site["stamp"]]
        slots: dict[tuple[int, int], tuple[int, str]] = {}
        for ly, row in enumerate(stamp["rows"]):
            for lx, ch in enumerate(row):
                entry = stamp["legend"].get(ch)
                if entry is not None and "npc" in entry:
                    slots[(site["x"] + lx, site["y"] + ly)] = (len(slots), entry["npc"])
        return {**site, "sx": sx, "sy": sy, "slots": slots}

    def at(self, x: int, y: int) -> tuple[dict, dict | None] | None:
        """(settlement, legend entry of the stamp character) when tile (x, y) lies in a settlement footprint."""
        site = self.site(x // SITE_CELL, y // SITE_CELL)
        if site is None:
            return None
        lx, ly = x - site["x"], y - site["y"]
        if not (0 <= lx < site["w"] and 0 <= ly < site["h"]):
            return None
        stamp = self.params["stamp_defs"][site["stamp"]]
        return site, stamp["legend"].get(stamp["rows"][ly][lx])


def person_at(seed: int, params: dict, site: dict, x: int, y: int) -> dict:
    """The settlement NPC that stands on slot tile (x, y) of the settlement (spec 09, "Settlement people")."""
    index, role = site["slots"][(x, y)]
    cfg = params["settlements"]
    h = hash64(seed, site["sx"], site["sy"], 100 + index)
    people = cfg["people"]
    region = params["regions"][site["region"]]
    return {
        "key": f"settle:{site['sx']}:{site['sy']}:{index}",
        "role": role,
        "x256": x * 256 + 128,
        "y256": y * 256 + 160,
        "name": people["start"][h % len(people["start"])] + people["end"][(h >> 16) % len(people["end"])],
        "variant": cfg["variants"][(h >> 32) % len(cfg["variants"])],
        "tone": region["tone"],
        "dialogue": cfg["dialogue"].replace("{role}", role).replace("{tone}", region["tone"]),
        "place": site["name"],
        "region": region["name"],
        "quirk": cfg["quirks"][hash64(seed, site["sx"], site["sy"], 44) % len(cfg["quirks"])],
    }


def settlements_in(seed: int, params: dict, sx0: int, sy0: int, sx1: int, sy1: int) -> list[dict]:
    """The settlements of the site cells sx0..sx1, sy0..sy1 (inclusive), row-major."""
    sites = Sites(seed, params)
    found = []
    for sy in range(sy0, sy1 + 1):
        for sx in range(sx0, sx1 + 1):
            site = sites.site(sx, sy)
            if site is not None:
                found.append(site)
    return found


def settlement_marker(seed: int, params: dict, cell_x: int, cell_y: int) -> dict | None:
    """The settlement shown on world map cell (cell_x, cell_y): the one whose site point lies in the cell."""
    per_site = SITE_CELL // MAP_CELL
    site = Sites(seed, params).site(cell_x // per_site, cell_y // per_site)
    if site is not None and site["px"] // MAP_CELL == cell_x and site["py"] // MAP_CELL == cell_y:
        return site
    return None


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
    home = params.get("home")
    if home is not None and (x - cx) ** 2 + (y - cy) ** 2 < home["radius"] ** 2:
        return "plains"  # the home meadow
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


LAND = ("plains", "forest", "desert", "snow", "beach")
MID = 32768


def overlay_at(seed: int, params: dict, biome: str, x: int, y: int) -> str | None:
    """River, ford, road or bridge on a land tile, or None (spec 09, "Rivers and roads").

    Rivers and roads are the places where a noise field crosses its middle value; a ford is a part of a river
    that can be crossed; a road over a river is a bridge. Never in the spawn clearing.
    """
    if biome not in LAND:
        return None
    w, h = params["width"], params["height"]
    mid_x, mid_y = w // 2, h // 2
    r = params["spawn_clear_radius"]
    if (x - mid_x) ** 2 + (y - mid_y) ** 2 < r * r:
        return None
    river, road = params["river"], params["road"]
    is_river = abs(field(seed, river, x, y) - MID) < river["half_width"]
    is_road = abs(field(seed, road, x, y) - MID) < road["half_width"]
    if is_river:
        if is_road:
            return "bridge"
        scale = river["ford_scale"]
        ford = noise2(hash64(seed, river["ford_salt"]), (x << 16) // scale, (y << 16) // scale) >= river["ford_min"]
        return "ford" if ford else "river"
    return "road" if is_road else None


def gid_for(seed: int, params: dict, biome: str, x: int, y: int, overlay: str | None = None) -> int:
    tiles = params["tiles"]
    if overlay is not None:
        return tiles[overlay]
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


def pick_weighted(entries: list, r: int) -> dict:
    """The entry that the number `r` falls on when the entries share `sum(weight)` slots in order."""
    r %= sum(e["weight"] for e in entries)
    for entry in entries:
        if r < entry["weight"]:
            return entry
        r -= entry["weight"]
    raise AssertionError("unreachable")


def fauna_at(seed: int, params: dict, x: int, y: int) -> dict:
    """The fauna entry ({enemy, drop, weight}) of the spawner on tile (x, y): a weighted pick among the fauna of its region (spec 09)."""
    entries = params["regions"][region_at(params, x, y)]["fauna"]
    return pick_weighted(entries, hash64(seed, x, y, 12) >> 20)


def spawner_at(seed: int, params: dict, biome: str, x: int, y: int) -> bool:
    s = params["spawners"]
    if biome not in s["biomes"]:
        return False
    cx, cy = params["width"] // 2, params["height"] // 2
    if (x - cx) ** 2 + (y - cy) ** 2 < s["min_distance"] ** 2:
        return False
    return (hash64(seed, x, y, 11) >> 20) % 10000 < s["per_10000"]


def _tile(seed: int, params: dict, sites: Sites, x: int, y: int, tiles: list, props: list, spawners: list, people: list) -> None:
    """Appends tile (x, y): its gid, and its prop or spawner (spec 09). Settlements replace everything under their footprint."""
    biome = biome_at(seed, params, x, y)
    found = sites.at(x, y)
    if found is not None:
        entry = found[1]
        tiles.append(entry["tile"] if entry is not None and "tile" in entry else gid_for(seed, params, biome, x, y))
        if entry is not None and "prop" in entry:
            props.append({"art": entry["prop"], "radius_x100": entry["radius_x100"], "x256": x * 256 + 128, "y256": y * 256 + 192})
        if entry is not None and "npc" in entry:
            people.append(person_at(seed, params, found[0], x, y))
        return
    overlay = overlay_at(seed, params, biome, x, y)
    tiles.append(gid_for(seed, params, biome, x, y, overlay))
    mid_x, mid_y = params["width"] // 2, params["height"] // 2
    if overlay is None and (x - mid_x) ** 2 + (y - mid_y) ** 2 >= params["spawn_clear_radius"] ** 2:
        prop = prop_at(seed, params, biome, x, y)
        if prop is not None:
            props.append(prop)
        if spawner_at(seed, params, biome, x, y):
            spawners.append([x, y])


def generate(seed: int, params: dict) -> dict:
    """Tiles (row-major gids), props and spawners (both in scan order), the spawn point and the NPCs."""
    w, h = params["width"], params["height"]
    tiles: list[int] = []
    props: list[dict] = []
    spawners: list[list[int]] = []
    people: list[dict] = []
    sites = Sites(seed, params)
    for y in range(h):
        for x in range(w):
            _tile(seed, params, sites, x, y, tiles, props, spawners, people)
    cx, cy = w // 2, h // 2
    return {"tiles": tiles, "props": props, "spawners": spawners, "people": people,
            "spawn": [cx * 256 + 128, cy * 256 + 128],
            "npcs": [{**npc, "x256": (cx + npc["dx"]) * 256 + 128, "y256": (cy + npc["dy"]) * 256 + 128}
                     for npc in params["npcs"]]}


def generate_chunk(seed: int, params: dict, cx: int, cy: int) -> dict:
    """The CHUNK_SIZE x CHUNK_SIZE window of tiles starting at tile (cx * CHUNK_SIZE, cy * CHUNK_SIZE).

    Chunk coordinates may be any integers: tiles outside the world are water. Tiles are row-major; props and
    spawners are in scan order inside the chunk. The result is exactly the restriction of `generate` to the window.
    """
    tiles: list[int] = []
    props: list[dict] = []
    spawners: list[list[int]] = []
    people: list[dict] = []
    sites = Sites(seed, params)
    for y in range(cy * CHUNK_SIZE, (cy + 1) * CHUNK_SIZE):
        for x in range(cx * CHUNK_SIZE, (cx + 1) * CHUNK_SIZE):
            _tile(seed, params, sites, x, y, tiles, props, spawners, people)
    return {"tiles": tiles, "props": props, "spawners": spawners, "people": people}


# ---------------------------------------------------------------------------- exploration and the world map

MAP_CELL = 128  # tiles per side of a world map cell
BIOME_CODES = ("water", "beach", "mountain", "snow", "desert", "forest", "plains")


def biome_code(seed: int, params: dict, cell_x: int, cell_y: int) -> int:
    """Biome shown on the world map for a cell: the biome of the tile at the center of the cell."""
    biome = biome_at(seed, params, cell_x * MAP_CELL + MAP_CELL // 2, cell_y * MAP_CELL + MAP_CELL // 2)
    return BIOME_CODES.index(biome)


def explore(cells: set, params: dict, tile_x: int, tile_y: int) -> None:
    """Marks the cell of the tile and its eight neighbours that lie inside the world as explored."""
    columns = (params["width"] + MAP_CELL - 1) // MAP_CELL
    rows = (params["height"] + MAP_CELL - 1) // MAP_CELL
    cx, cy = tile_x // MAP_CELL, tile_y // MAP_CELL
    for y in range(cy - 1, cy + 2):
        for x in range(cx - 1, cx + 2):
            if 0 <= x < columns and 0 <= y < rows:
                cells.add((x, y))


def digest_cells(cells: set) -> int:
    """Fold hash64(h, x, y) over the explored cells ordered by row then column."""
    h = 0
    for x, y in sorted(cells, key=lambda c: (c[1], c[0])):
        h = hash64(h, x, y)
    return h


# ---------------------------------------------------------------------------- streaming window

def chunk_spawners(seed: int, params: dict, cx: int, cy: int) -> list[list[int]]:
    """Same result as generate_chunk(...)["spawners"], faster: the (rare) hash test runs before the biome is computed."""
    s = params["spawners"]
    w, h = params["width"], params["height"]
    mid_x, mid_y = w // 2, h // 2
    clear = params["spawn_clear_radius"] ** 2
    result: list[list[int]] = []
    sites = Sites(seed, params)
    for y in range(cy * CHUNK_SIZE, (cy + 1) * CHUNK_SIZE):
        for x in range(cx * CHUNK_SIZE, (cx + 1) * CHUNK_SIZE):
            if (hash64(seed, x, y, 11) >> 20) % 10000 >= s["per_10000"]:
                continue
            d2 = (x - mid_x) ** 2 + (y - mid_y) ** 2
            if d2 < clear or d2 < s["min_distance"] ** 2:
                continue
            if sites.at(x, y) is not None:
                continue
            biome = biome_at(seed, params, x, y)
            if biome in s["biomes"] and overlay_at(seed, params, biome, x, y) is None:
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
    the others never changes. A killed enemy stays in the list (dead) until its chunk leaves, and its spawner is cleared with the
    world tick of the death; a cleared spawner whose enemy has been dead for `respawn_ticks` is ready and, when its chunk
    enters the window, it is uncleared and creates an enemy again (spec 08, "Respawn").
    """

    def __init__(self, seed: int, params: dict, cx: int, cy: int):
        self.seed, self.params = seed, params
        self.now = params["time"]["start_tick"]  # world ticks
        self.cleared: dict[tuple[int, int], int] = {}  # spawner tile -> world tick of the death
        self.enemies: list[dict] = []  # {"x", "y", "dead"} by spawner tile
        self.cx, self.cy = cx, cy
        for chunk in window_chunks(cx, cy):
            self._enter(chunk)

    def _enter(self, chunk: tuple[int, int]) -> None:
        for x, y in chunk_spawners(self.seed, self.params, chunk[0], chunk[1]):
            died = self.cleared.get((x, y))
            if died is not None:
                if self.now - died < self.params["spawners"]["respawn_ticks"]:
                    continue
                del self.cleared[(x, y)]
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

    def wait(self, ticks: int) -> None:
        self.now += ticks

    def kill(self, index: int) -> None:
        enemy = self.enemies[index]
        enemy["dead"] = True
        self.cleared[(enemy["x"], enemy["y"])] = self.now

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
