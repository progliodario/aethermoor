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
