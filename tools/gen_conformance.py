#!/usr/bin/env python3
"""Generate the shared conformance vectors in tests/conformance/ from the Python reference.

Usage: python tools/gen_conformance.py [--check]
  --check   do not write, fail if the committed vectors differ from the generated ones.

Never edit the generated files by hand (see CLAUDE.md). 64-bit values are written as hex strings
because many JSON parsers lose precision above 2^53.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conformance_audio  # noqa: E402
import conformance_music  # noqa: E402
import conformance_m2  # noqa: E402
import conformance_m3  # noqa: E402
import conformance_m4  # noqa: E402
import conformance_m5  # noqa: E402
from reference import numerics as nm  # noqa: E402
from reference import rules  # noqa: E402
from reference.i18n import format_message  # noqa: E402
from reference.ids import valid_id  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tests" / "conformance"
SPEC_VERSION = 1
SEED = 20261101


def h64(value: int) -> str:
    return f"0x{value & nm.M64:016x}"


def case(name: str, inp: dict, expect: dict) -> dict:
    return {"name": name, "input": inp, "expect": expect}


# --------------------------------------------------------------------------------------- rng

def suite_rng() -> list[dict]:
    cases = []
    for seed in (0, 1, 0xDEADBEEF, nm.M64):
        sm = nm.SplitMix64(seed)
        cases.append(case(f"splitmix64_{h64(seed)}", {"op": "splitmix64", "seed": h64(seed), "count": 5},
                          {"values": [h64(sm.next()) for _ in range(5)]}))
    for init_state, init_seq in ((42, 54), (0, 0), (123456789, 987654321), (nm.M64, nm.M64)):
        p = nm.Pcg32(init_state, init_seq)
        cases.append(case(f"pcg32_{init_state}_{init_seq}",
                          {"op": "pcg32", "init_state": h64(init_state), "init_seq": h64(init_seq), "count": 8},
                          {"values": [p.next_u32() for _ in range(8)]}))
    for bound in (1, 2, 6, 100, 1000, 4_000_000_000):
        p = nm.Pcg32(777, 31)
        cases.append(case(f"pcg32_bounded_{bound}",
                          {"op": "pcg32_bounded", "init_state": h64(777), "init_seq": h64(31),
                           "bound": bound, "count": 16},
                          {"values": [p.next_bounded(bound) for _ in range(16)]}))
    for master in (0x1234, nm.M64):
        for name in ("world", "combat", "loot", "quest", "weather", "cosmetic", "ai"):
            p = nm.derive_stream(master, name)
            cases.append(case(f"stream_{h64(master)}_{name}",
                              {"op": "derive_stream", "master_seed": h64(master), "name": name, "count": 4},
                              {"values": [p.next_u32() for _ in range(4)]}))
    for i, text in enumerate(("", "a", "foobar", "world", "base:enemy/slime_green", "perché")):
        cases.append(case(f"fnv1a64_{i}", {"op": "fnv1a64", "text": text},
                          {"value": h64(nm.fnv1a64(text.encode("utf-8")))}))
    return cases


# -------------------------------------------------------------------------------------- hash

def suite_hash() -> list[dict]:
    rnd = random.Random(SEED + 1)
    cases = []
    fixed = [(0, 0, 0, 0), (1, 1, 2, 3), (nm.M64, -1, -1, -1), (42, 2**40, -(2**40), 7)]
    for _ in range(12):
        fixed.append((rnd.getrandbits(64), rnd.randint(-10**6, 10**6), rnd.randint(-10**6, 10**6),
                      rnd.randint(-100, 100)))
    for i, (seed, a, b, c) in enumerate(fixed):
        cases.append(case(f"hash64_{i}", {"op": "hash64", "seed": h64(seed), "a": a, "b": b, "c": c},
                          {"value": h64(nm.hash64(seed, a, b, c))}))
    for i in range(8):
        seed = rnd.getrandbits(64)
        xi, yi = rnd.randint(-5000, 5000), rnd.randint(-5000, 5000)
        cases.append(case(f"lattice_{i}", {"op": "lattice", "seed": h64(seed), "x": xi, "y": yi},
                          {"value": nm.lattice(seed, xi, yi)}))
    return cases


# ------------------------------------------------------------------------------------- noise

def suite_noise() -> list[dict]:
    rnd = random.Random(SEED + 2)
    cases = []
    coords = [(0, 0), (65536, 65536), (32768, 32768), (-1, -1), (-65536 * 5 - 123, 65536 * 9 + 4567),
              (2**40 + 17, -(2**40) + 99)]
    coords += [(rnd.randint(-2**28, 2**28), rnd.randint(-2**28, 2**28)) for _ in range(14)]
    for i, (x, y) in enumerate(coords):
        seed = rnd.getrandbits(64)
        cases.append(case(f"noise2_{i}", {"op": "noise2", "seed": h64(seed), "x": x, "y": y},
                          {"value": nm.noise2(seed, x, y)}))
    for i, octaves in enumerate((1, 2, 3, 4, 5, 6)):
        seed = rnd.getrandbits(64)
        x, y = rnd.randint(-2**26, 2**26), rnd.randint(-2**26, 2**26)
        cases.append(case(f"fbm2_{i}", {"op": "fbm2", "seed": h64(seed), "x": x, "y": y, "octaves": octaves},
                          {"value": nm.fbm2(seed, x, y, octaves)}))
    return cases


# ------------------------------------------------------------------------------------ stats

def suite_stats() -> list[dict]:
    rnd = random.Random(SEED + 3)
    keys = ("str", "vit", "dex", "agi", "int", "wis", "luk")
    rows = [(1, (0,) * 7, (0,) * 6), (99, (999,) * 7, (500, 500, 300, 300, 200, 200)),
            (10, (6, 7, 8, 8, 7, 7, 9), (0, 0, 5, 0, 2, 1))]
    for _ in range(30):
        rows.append((rnd.randint(1, 99), tuple(rnd.randint(0, 150) for _ in range(7)),
                     tuple(rnd.randint(0, 80) for _ in range(6))))
    cases = []
    for i, (level, prim, eq) in enumerate(rows):
        p = rules.Primary(*prim)
        e = rules.Equipment(*eq)
        cases.append(case(f"derived_{i}",
                          {"op": "derived_stats", "level": level, "primary": dict(zip(keys, prim)),
                           "equipment": dict(zip(("hp", "mp", "weapon_atk", "weapon_matk", "armor_def",
                                                  "armor_mdef"), eq))},
                          rules.derived_stats(level, p, e)))
    return cases


# ----------------------------------------------------------------------------------- damage

def suite_damage() -> list[dict]:
    rnd = random.Random(SEED + 4)
    rows = [
        (20, 100, 0, 1000, 0, 1, 1, 1000, False, 1500, 1000),
        (1, 1, 1000, 500, 900, 1, 99, 950, False, 1500, 100),
        (500, 300, 20, 1500, 0, 50, 1, 1050, True, 2500, 3000),
    ]
    for _ in range(60):
        rows.append((rnd.randint(1, 800), rnd.choice((50, 80, 100, 120, 150, 250, 400)),
                     rnd.randint(0, 600), rnd.choice((500, 1000, 1500)), rnd.choice((0, 0, 250, 500)),
                     rnd.randint(1, 99), rnd.randint(1, 99), rnd.randint(950, 1050),
                     rnd.random() < 0.3, rnd.randint(1500, 2500), rnd.choice((1000, 1000, 800, 1250, 1500))))
    names = ("atk", "power_pct", "def_target", "elem_mult_pm", "pen_pm", "lvl_attacker", "lvl_target",
             "variance_pm", "crit", "crit_mult_pm", "buff_mod_pm")
    cases = []
    for i, row in enumerate(rows):
        cases.append(case(f"damage_{i}", {"op": "damage", **dict(zip(names, row))},
                          {"damage": rules.damage(*row)}))
    return cases


# -------------------------------------------------------------------------------------- xp

def suite_xp() -> list[dict]:
    table = rules.generate_xp_table()
    cases = [case(f"xp_table_{lv}", {"op": "xp_table", "table": "base:table/xp", "level": lv},
                  {"value": table[lv - 1]}) for lv in (1, 2, 10, 25, 50, 75, 98)]
    for i, (exp, le, lp) in enumerate(((6, 1, 1), (6, 5, 1), (6, 1, 20), (100, 30, 30), (100, 99, 1),
                                       (1000, 10, 99), (7, 3, 2), (1, 1, 99))):
        cases.append(case(f"xp_gain_{i}", {"op": "xp_gain", "enemy_xp": exp, "lvl_enemy": le, "lvl_player": lp},
                          {"value": rules.xp_gain(exp, le, lp)}))
    return cases


# ---------------------------------------------------------------------------------- i18n

I18N_CASES = [
    ("plain", "it", "Nessun segnaposto", {}),
    ("placeholder_string", "it", "Versione {version}", {"version": "0.1.0"}),
    ("placeholder_int", "en", "You have {gold} gold", {"gold": 1250}),
    ("placeholder_missing", "en", "Hello {who}!", {}),
    ("escaped_braces", "en", "Use {{name}} as a template", {}),
    ("plural_one_it", "it", "{n, plural, one {# pane} other {# pani}}", {"n": 1}),
    ("plural_other_it", "it", "{n, plural, one {# pane} other {# pani}}", {"n": 3}),
    ("plural_zero_exact", "it", "{n, plural, =0 {Nessun pane} one {# pane} other {# pani}}", {"n": 0}),
    ("plural_one_en", "en", "{count, plural, one {# apple} other {# apples}} for {who}", {"count": 1, "who": "Ren"}),
    ("plural_nested_arg", "en", "{n, plural, one {{who} has # coin} other {{who} has # coins}}",
     {"n": 2, "who": "Lena"}),
    ("plural_negative", "en", "{n, plural, one {# thing} other {# things}}", {"n": -1}),
    ("select_match", "en", "{kind, select, sword {A blade} bow {A bow} other {Something}}", {"kind": "bow"}),
    ("select_other", "en", "{kind, select, sword {A blade} other {Something}}", {"kind": "axe"}),
    ("unicode", "it", "Perché {name}? Più {n, plural, one {# volta} other {# volte}}", {"name": "è", "n": 2}),
    ("pound_outside_plural", "en", "Item #1 costs {gold}", {"gold": 5}),
    ("unclosed_brace", "en", "Broken {name", {"name": "x"}),
]


def suite_i18n() -> list[dict]:
    return [case(name, {"op": "format", "lang": lang, "message": msg, "args": args},
                 {"text": format_message(msg, lang, args)}) for name, lang, msg, args in I18N_CASES]


# ------------------------------------------------------------------------------------- ids

def suite_ids() -> list[dict]:
    texts = ["base:enemy/slime_green", "base:skill/ren/analyze", "mymod:item/fancy_hat", "a:b/c",
             "a1_b:c2/d_3", "Base:enemy/slime", "base:enemy", "base:/slime", "base:enemy/", "base:enemy//slime",
             "base:Enemy/slime", "1base:enemy/slime", "base:enemy/Slime", "base:enemy/sl ime", ":enemy/slime",
             "base:enemy/slime:x", "base", "", "base:9enemy/slime", "base:enemy/9slime", "base:enemy/sl-ime"]
    return [case(f"id_{i}", {"op": "valid_id", "text": t}, {"valid": valid_id(t)}) for i, t in enumerate(texts)]


SUITES = {
    "rng": suite_rng,
    "hash": suite_hash,
    "noise": suite_noise,
    "stats": suite_stats,
    "damage": suite_damage,
    "xp": suite_xp,
    "i18n_format": suite_i18n,
    "ids": suite_ids,
    "rig_pose": conformance_m2.suite_rig_pose,
    "movement": conformance_m2.suite_movement,
    "raster": conformance_m2.suite_raster,
    "audio": conformance_audio.suite_audio,
    "audio_director": conformance_audio.suite_audio_director,
    "audio_ambience": conformance_audio.suite_audio_ambience,
    "music": conformance_music.suite_music,
    "music_director": conformance_music.suite_music_director,
    "combat": conformance_m3.suite_combat,
    "story": conformance_m4.suite_story,
    "save": conformance_m4.suite_save,
    "worldgen": conformance_m5.suite_worldgen,
    "worldgen_chunks": conformance_m5.suite_worldgen_chunks,
    "chunk_window": conformance_m5.suite_chunk_window,
    "worldtime": conformance_m5.suite_worldtime,
    "worldmap": conformance_m5.suite_worldmap,
    "settlements": conformance_m5.suite_settlements,
    "fauna": conformance_m5.suite_fauna,
    "routines": conformance_m5.suite_routines,
    "guild": conformance_m5.suite_guild,
}


# The suites that take the longest, started first so the pool finishes sooner.
SLOW_SUITES = {"worldgen_chunks", "chunk_window", "worldgen", "settlements", "fauna", "combat", "story", "save", "worldmap"}


def build_suite(name: str) -> tuple[str, str, int]:
    """Builds one suite (a worker of the pool): its name, the text of the file and the number of cases."""
    cases = SUITES[name]()
    return name, render(name, cases), len(cases)


def render(suite: str, cases: list[dict]) -> str:
    doc = {"suite": suite, "spec_version": SPEC_VERSION, "generated_by": "tools/gen_conformance.py",
           "cases": cases}
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--serial", action="store_true", help="build the suites one after the other (no worker processes)")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    stale = 0
    if args.serial:
        built = [build_suite(name) for name in SUITES]
    else:  # the suites are independent: one worker process each, the slowest ones first
        from concurrent.futures import ProcessPoolExecutor

        order = sorted(SUITES, key=lambda name: name not in SLOW_SUITES)
        with ProcessPoolExecutor() as pool:
            done = {name: (name, text, count) for name, text, count in pool.map(build_suite, order)}
        built = [done[name] for name in SUITES]
    for name, text, count in built:
        path = OUT / f"{name}.json"
        if args.check:
            current = path.read_text(encoding="utf-8") if path.exists() else ""
            if current != text:
                print(f"OUT OF DATE: {path.relative_to(ROOT)}")
                stale += 1
        else:
            current = path.read_bytes().decode("utf-8") if path.exists() else ""
            if current != text:
                path.write_bytes(text.encode("utf-8"))
            print(f"wrote {path.relative_to(ROOT)} ({count} cases{'' if current != text else ', unchanged'})")
    if args.check:
        if stale:
            print("run: python tools/gen_conformance.py")
            return 1
        print("OK: conformance vectors are up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
