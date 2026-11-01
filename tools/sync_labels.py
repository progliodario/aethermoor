#!/usr/bin/env python3
"""Create or update the GitHub labels defined in .github/labels.json using the gh CLI.

Usage: python tools/sync_labels.py [--repo OWNER/NAME]
Requires `gh` authenticated with access to the repository. Existing labels are updated (--force).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

LABELS = Path(__file__).resolve().parent.parent / ".github" / "labels.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", help="OWNER/NAME (defaults to the current repository)")
    args = parser.parse_args()

    failures = 0
    for label in json.loads(LABELS.read_text(encoding="utf-8")):
        cmd = ["gh", "label", "create", label["name"], "--color", label["color"],
               "--description", label["description"], "--force"]
        if args.repo:
            cmd += ["--repo", args.repo]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            failures += 1
            print(f"FAILED {label['name']}: {result.stderr.strip()}")
        else:
            print(f"ok {label['name']}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
