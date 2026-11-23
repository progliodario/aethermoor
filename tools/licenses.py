#!/usr/bin/env python3
"""The licenses of the dependencies (risk R10 of the plan; ADR 0010): every dependency of the build has a row in tools/licenses.json
with a license allowed for its scope, and THIRD_PARTY_NOTICES.md is written from that table.

Usage: python tools/licenses.py [--check]
  (no flag)  write THIRD_PARTY_NOTICES.md from tools/licenses.json, and report the problems.
  --check    write nothing; fail on a problem or when THIRD_PARTY_NOTICES.md is not current.

The dependencies are read from the manifests: `dependencies` of desktop/vcpkg.json (source `vcpkg`), the `[libraries]` and
`[plugins]` of android/gradle/libs.versions.toml and the coordinates written in the build.gradle.kts files (`gradle`,
`gradle-plugin`), the packages of tools/requirements.txt (`pip`) and the tools the workflows download from GitHub releases (`ci`).
A problem is a dependency without a row, a row whose dependency is gone, or a license not allowed for the scope of the row
(`ship`: in the game; `build`: builds it; `test`: only in the tests; `tools`: development only). The code is GPL-3.0-or-later:
EPL-2.0 is allowed in the tests only. The GitHub Actions of the workflows run on GitHub's machines and are not listed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLE = ROOT / "tools" / "licenses.json"
NOTICES = ROOT / "THIRD_PARTY_NOTICES.md"

GRADLE_COORD = re.compile(r'"([\w.\-]+):([\w.\-]+):[^"]*"')
CI_RELEASE = re.compile(r"https://github\.com/([\w.\-]+)/([\w.\-]+)/releases/download/")
PIP_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._\-]*)")


def find_dependencies(root: Path = ROOT) -> set[tuple[str, str]]:
    """Every (source, name) the manifests of the build name."""
    found: set[tuple[str, str]] = set()
    vcpkg = json.loads((root / "desktop" / "vcpkg.json").read_text(encoding="utf-8"))
    for dep in vcpkg.get("dependencies", []):
        found.add(("vcpkg", dep if isinstance(dep, str) else dep["name"]))
    toml = tomllib.loads((root / "android" / "gradle" / "libs.versions.toml").read_text(encoding="utf-8"))
    for lib in toml.get("libraries", {}).values():
        found.add(("gradle", lib["module"] if isinstance(lib, dict) and "module" in lib else str(lib).rsplit(":", 1)[0]))
    for plugin in toml.get("plugins", {}).values():
        found.add(("gradle-plugin", plugin["id"] if isinstance(plugin, dict) else str(plugin).split(":")[0]))
    for path in sorted((root / "android").rglob("*.gradle.kts")):
        for group, artifact in GRADLE_COORD.findall(path.read_text(encoding="utf-8")):
            found.add(("gradle", f"{group}:{artifact}"))
    for line in (root / "tools" / "requirements.txt").read_text(encoding="utf-8").splitlines():
        match = PIP_NAME.match(line)
        if match and not line.lstrip().startswith("#"):
            found.add(("pip", match.group(1).lower()))
    for path in sorted((root / ".github" / "workflows").glob("*.yml")):
        for owner, repo in CI_RELEASE.findall(path.read_text(encoding="utf-8")):
            found.add(("ci", f"{owner}/{repo}"))
    return found


def problems(found: set[tuple[str, str]], table: dict) -> list[str]:
    out = []
    rows = {(row["source"], row["name"]): row for row in table["dependencies"]}
    for source, name in sorted(found - set(rows)):
        out.append(f"the dependency {name} ({source}) has no row in tools/licenses.json: add it, with its license and scope")
    for source, name in sorted(set(rows) - found):
        out.append(f"tools/licenses.json lists {name} ({source}), which no manifest of the build names any more: remove the row")
    for row in table["dependencies"]:
        scopes = table["allowed"].get(row["license"])
        if scopes is None:
            out.append(f"{row['name']}: the license {row['license']} is not one the project allows (tools/licenses.json, `allowed`)")
        elif row["scope"] not in scopes:
            out.append(f"{row['name']}: the license {row['license']} is allowed only for {', '.join(scopes)}, not for {row['scope']}")
    return out


SECTIONS = [
    ("Desktop (`desktop/vcpkg.json`)", ("vcpkg",)),
    ("Android (`android/gradle/libs.versions.toml`, `android/*/build.gradle.kts`)", ("gradle", "gradle-plugin")),
    ("Tools (`tools/requirements.txt` and the workflows; development only, not shipped)", ("pip", "ci")),
]
SCOPE_NAMES = {"ship": "in the game", "build": "build only", "test": "tests only", "tools": "development only"}


def notices(table: dict) -> str:
    lines = [
        "# Third-party notices",
        "",
        "Written by `tools/licenses.py` from `tools/licenses.json`: do not edit by hand. These are the dependencies the build uses; any new",
        "one must have a row in the table, with a license compatible with GPL-3.0-or-later (`ci-data` runs `tools/licenses.py --check`).",
        "",
    ]
    for title, sources in SECTIONS:
        lines += [f"## {title}", "", "| Component | License | Where | Used for |", "|---|---|---|---|"]
        for row in table["dependencies"]:
            if row["source"] in sources:
                lines.append(f"| {row['component']} (`{row['name']}`) | {row['license']} | {SCOPE_NAMES[row['scope']]} | {row['used_for']} |")
        lines.append("")
    lines += [
        "Vector art uses an in-house software rasterizer (ADR 0012). ThorVG, SDL3_ttf and miniz, named in the early plan, are not used.",
        "",
        "## Fonts and art",
        "",
        "The game ships no image file: the art is JSON recipes drawn by the game. The font of the interface is `data/base/fonts/aether.json`,",
        "written by the project's own tool (`tools/make_font.py`) as strokes, not a font of another author. Art and font are content under",
        "CC BY-SA 4.0 (see `LICENSE-CONTENT.md`). The debug font of SDL is only a fallback on desktop; Android builds a libGDX bitmap font",
        "from the pack font.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    table = json.loads(TABLE.read_text(encoding="utf-8"))
    found = problems(find_dependencies(), table)
    for problem in found:
        print("ERROR:", problem)
    text = notices(table)
    current = NOTICES.read_text(encoding="utf-8") if NOTICES.exists() else ""
    if args.check:
        if current != text:
            print(f"OUT OF DATE: {NOTICES.relative_to(ROOT)} (run: python tools/licenses.py)")
            return 1
        if not found:
            print(f"OK: {len(table['dependencies'])} dependencies, every license allowed")
    elif current != text:
        with open(NOTICES, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"wrote {NOTICES.relative_to(ROOT)}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
