import re
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

from reference import numerics as nm  # noqa: E402
from reference import rules  # noqa: E402
from reference.i18n import format_message  # noqa: E402
from reference.ids import valid_id  # noqa: E402


def test_splitmix64_known_answers():
    sm = nm.SplitMix64(0)
    assert sm.next() == 0xE220A8397B1DCDAF
    assert sm.next() == 0x6E789E6AA1B965F4


def test_pcg32_known_answers():
    p = nm.Pcg32(42, 54)
    assert [p.next_u32() for _ in range(6)] == [
        0xA15C02B7, 0x7B47F409, 0xBA1D3330, 0x83D2F293, 0xBFA4784B, 0xCBED606E]


def test_fnv1a64_known_answers():
    assert nm.fnv1a64(b"") == 0xCBF29CE484222325
    assert nm.fnv1a64(b"a") == 0xAF63DC4C8601EC8C


def test_bounded_stays_in_range():
    p = nm.Pcg32(1, 2)
    assert all(0 <= p.next_bounded(7) < 7 for _ in range(1000))


def test_streams_are_independent_and_reproducible():
    a = [nm.derive_stream(5, "combat").next_u32() for _ in range(1)]
    b = [nm.derive_stream(5, "combat").next_u32() for _ in range(1)]
    c = [nm.derive_stream(5, "loot").next_u32() for _ in range(1)]
    assert a == b and a != c


def test_noise_range_and_continuity():
    for x in range(-200000, 200000, 7919):
        for y in (-123456, 0, 98765):
            assert 0 <= nm.noise2(3, x, y) <= 65535
            assert 0 <= nm.fbm2(3, x, y, 5) <= 65535
    # neighbouring samples differ by a small amount
    assert abs(nm.noise2(9, 100000, 100000) - nm.noise2(9, 100001, 100000)) < 8


def test_noise_is_exact_on_lattice():
    assert nm.noise2(11, 5 * 65536, -3 * 65536) == nm.lattice(11, 5, -3)


def test_negative_shift_is_floor():
    assert (-1 >> 16) == -1
    assert nm.mulq(-3, 32768) == -2  # floor(-1.5)


def test_damage_minimum_is_one():
    assert rules.damage(1, 1, 1000, 500, 0, 1, 99, 950, False, 1500, 100) == 1


def test_damage_basic():
    assert rules.damage(20, 100, 0, 1000, 0, 1, 1, 1000, False, 1500, 1000) == 20


def test_xp_table_shape():
    table = rules.generate_xp_table()
    assert len(table) == 98
    assert table[0] == 50 and table[1] == 130
    assert all(b > a for a, b in zip(table, table[1:]))


def test_xp_gain_bounds():
    assert rules.xp_gain(100, 1, 99) == 10      # floor of 10%
    assert rules.xp_gain(100, 99, 1) == 150     # cap of 150%


@pytest.mark.parametrize("text,expected", [
    ("{n, plural, one {# apple} other {# apples}}", {1: "1 apple", 2: "2 apples", 0: "0 apples"}),
])
def test_plural(text, expected):
    for n, out in expected.items():
        assert format_message(text, "en", {"n": n}) == out


def test_missing_argument_is_kept():
    assert format_message("Hi {who}", "en", {}) == "Hi {who}"


def test_valid_id_matches_regex():
    pattern = re.compile(r"[a-z][a-z0-9_]*:[a-z][a-z0-9_]*(?:/[a-z0-9_]+)+")
    for text in ["base:enemy/slime", "a:b/c/d", "Base:enemy/x", "base:enemy", "base:enemy/", "x:y/Z", ""]:
        assert valid_id(text) == bool(pattern.fullmatch(text)), text


def test_generated_files_are_current():
    for script in ("gen_conformance.py", "gen_tables.py", "make_demo_map.py"):
        result = subprocess.run([sys.executable, str(TOOLS / script), "--check"],
                                capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stdout + result.stderr


def test_saves_in_the_vectors_match_the_schema():
    import json

    from jsonschema import Draft202012Validator

    root = TOOLS.parent
    schema = json.loads((root / "schemas" / "save.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    doc = json.loads((root / "tests" / "conformance" / "save.json").read_text(encoding="utf-8"))
    assert doc["cases"]
    for case in doc["cases"]:
        errors = list(validator.iter_errors({"save_version": 1, **case["input"]["save"]}))
        assert not errors, (case["name"], errors[:1])


def test_world_chunks_are_the_restriction_of_the_world():

    from reference import worldgen

    params = worldgen.load_params()
    params = {**params, "width": 80, "height": 72, "border": 2}
    world = worldgen.generate(5, params)
    size = worldgen.CHUNK_SIZE
    props, spawners = [], []
    for cy in range(-1, 4):
        for cx in range(-1, 4):
            chunk = worldgen.generate_chunk(5, params, cx, cy)
            for i, gid in enumerate(chunk["tiles"]):
                x, y = cx * size + i % size, cy * size + i // size
                inside = 0 <= x < params["width"] and 0 <= y < params["height"]
                assert gid == (world["tiles"][y * params["width"] + x] if inside else params["tiles"]["water"])
            props += chunk["props"]
            spawners += chunk["spawners"]
    for cy in range(0, 3):
        for cx in range(0, 3):
            assert worldgen.chunk_spawners(5, params, cx, cy) == worldgen.generate_chunk(5, params, cx, cy)["spawners"]
    key = lambda p: (p["y256"], p["x256"])  # noqa: E731
    assert sorted(props, key=key) == sorted(world["props"], key=key)
    assert sorted(spawners) == sorted(world["spawners"])


def test_world_time_light_and_weather():

    from reference import worldgen, worldtime

    t = worldgen.load_params()["time"]
    assert worldtime.tod_pm(t, t["day_ticks"] * 3 + t["day_ticks"] // 2) == 500
    assert worldtime.day_of(t, t["day_ticks"] * 3) == 4
    assert [worldtime.light_pm(t, tod) for tod in (0, 200, 250, 300, 500, 700, 750, 800, 1000)] == [180, 180, 590, 1000, 1000, 1000, 590, 180, 180]
    for ticks in range(0, 5 * t["weather"]["period_ticks"], 997):
        s = worldtime.sample(42, t, ticks)
        assert 0 <= s["rain_pm"] <= 1000 and 0 <= s["dim_pm"] <= 1000 and 0 <= s["effective_light_pm"] <= 1000
    # The weather only depends on the seed and the period: same period, same kind.
    period = t["weather"]["period_ticks"]
    assert worldtime.weather_at(9, t, 7 * period + 5000)["kind"] == worldtime.weather_at(9, t, 7 * period + 17000)["kind"]


def test_rivers_and_roads_are_overlays_on_land():

    from reference import worldgen

    params = worldgen.load_params()
    seen = set()
    for y in range(8100, 8300, 3):
        for x in range(8100, 8300, 3):
            biome = worldgen.biome_at(3, params, x, y)
            overlay = worldgen.overlay_at(3, params, biome, x, y)
            if overlay is not None:
                assert biome in worldgen.LAND
                assert worldgen.gid_for(3, params, biome, x, y, overlay) == params["tiles"][overlay]
                seen.add(overlay)
    assert {"river", "road"} <= seen
    # Nothing inside the spawn clearing.
    cx = cy = 8192
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            if dx * dx + dy * dy < params["spawn_clear_radius"] ** 2:
                assert worldgen.overlay_at(3, params, "plains", cx + dx, cy + dy) is None


def test_world_map_exploration():

    from reference import worldgen

    params = worldgen.load_params()
    cells: set = set()
    worldgen.explore(cells, params, 8192, 8192)
    assert len(cells) == 9 and (64, 64) in cells and (63, 63) in cells and (65, 65) in cells
    worldgen.explore(cells, params, 8193, 8200)  # same cell: nothing new
    assert len(cells) == 9
    corner: set = set()
    worldgen.explore(corner, params, 0, 0)
    assert corner == {(0, 0), (1, 0), (0, 1), (1, 1)}
    far: set = set()
    worldgen.explore(far, params, 16383, 16383)
    assert far == {(126, 126), (127, 126), (126, 127), (127, 127)}
    assert 0 <= worldgen.biome_code(1, params, 64, 64) < 7


def test_settlements_are_inside_their_cells_and_deterministic():
    from reference import worldgen

    params = worldgen.load_params()
    found = worldgen.settlements_in(7, params, 0, 0, 31, 31)
    assert found and worldgen.settlements_in(7, params, 0, 0, 31, 31) == found
    assert worldgen.settlements_in(8, params, 0, 0, 31, 31) != found
    for site in found:
        cell_x, cell_y = site["px"] // worldgen.SITE_CELL, site["py"] // worldgen.SITE_CELL
        # The footprint lies completely inside the site cell of its site point.
        assert site["x"] // worldgen.SITE_CELL == cell_x and (site["x"] + site["w"] - 1) // worldgen.SITE_CELL == cell_x
        assert site["y"] // worldgen.SITE_CELL == cell_y and (site["y"] + site["h"] - 1) // worldgen.SITE_CELL == cell_y
        assert site["name"] and 0 <= site["region"] < len(params["regions"])
    # The stamp is drawn: the road gid of a village crosses its footprint, and nothing random grows inside it.
    site = next(s for s in found if s["kind"] == "village")
    sites = worldgen.Sites(7, params)
    inside = [sites.at(site["x"] + dx, site["y"] + dy) for dy in range(site["h"]) for dx in range(site["w"])]
    assert all(entry is not None and entry[0]["name"] == site["name"] for entry in inside)
    chunk = worldgen.generate_chunk(7, params, site["px"] // 32, site["py"] // 32)
    assert 13 in chunk["tiles"] and 14 in chunk["tiles"]
    assert all(not (site["x"] <= s[0] < site["x"] + site["w"] and site["y"] <= s[1] < site["y"] + site["h"]) for s in chunk["spawners"])


def test_regions_follow_the_nearest_center():
    from reference import worldgen

    params = worldgen.load_params()
    assert params["regions"][worldgen.region_at(params, 8192, 8192)]["id"] == "verdalis"
    assert params["regions"][worldgen.region_at(params, 0, 16383)]["id"] == "tidehaven"
    assert params["regions"][worldgen.region_at(params, 16383, 8000)]["id"] == "ashen_wastes"
