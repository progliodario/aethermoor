#!/usr/bin/env python3
"""Generate data tables from the reference formulas (docs/spec/04-stats-and-combat.md).

Usage: python tools/gen_tables.py [--check]
  --check   do not write, fail if the committed tables differ from the generated ones.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reference.rules import generate_xp_table  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
XP_TABLE = ROOT / "data" / "base" / "tables" / "xp_table.json"


def build_xp_table() -> dict:
    return {
        "$schema": "../../../schemas/table.schema.json",
        "id": "base:table/xp",
        "kind": "int_list",
        "start_level": 1,
        "generated_by": "tools/gen_tables.py",
        "values": generate_xp_table(),
    }


def render(table: dict) -> str:
    return json.dumps(table, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    expected = render(build_xp_table())
    if args.check:
        current = XP_TABLE.read_text(encoding="utf-8") if XP_TABLE.exists() else ""
        if current != expected:
            print(f"OUT OF DATE: {XP_TABLE.relative_to(ROOT)} (run python tools/gen_tables.py)")
            return 1
        print("OK: tables are up to date")
        return 0

    XP_TABLE.parent.mkdir(parents=True, exist_ok=True)
    XP_TABLE.write_text(expected, encoding="utf-8", newline="\n")
    print(f"wrote {XP_TABLE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
