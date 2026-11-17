"""The documents stay true: links resolve, every tool is described, the numbers come from the data, the generators write LF."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"


def markdown_files() -> list[Path]:
    """The Markdown files of the repository (the tracked ones and the new ones not ignored)."""
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.md"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [ROOT / line for line in out.stdout.splitlines() if (ROOT / line).exists()]


def slug(heading: str) -> str:
    """The anchor GitHub gives a heading: lower case, punctuation dropped (letters, digits, `-` and `_` kept), spaces to `-`."""
    text = re.sub(r"[`*]", "", heading.strip().lower())
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
    return {slug(m.group(1)) for m in re.finditer(r"^#{1,6}\s+(.*?)\s*$", text, re.M)}


def test_every_link_of_the_documents_resolves():
    broken = []
    for path in markdown_files():
        text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
        for match in re.finditer(r"\]\(([^)\s]+)\)", text):
            link = match.group(1)
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            target_text, _, anchor = link.partition("#")
            target = (path.parent / target_text).resolve() if target_text else path
            rel = path.relative_to(ROOT)
            if not target.exists():
                broken.append(f"{rel}: {link} (no such file)")
            elif anchor and target.suffix == ".md" and anchor not in anchors(target):
                broken.append(f"{rel}: {link} (no such heading)")
    assert not broken, "\n".join(broken)


def test_every_tool_is_described_in_the_tools_readme():
    readme = (TOOLS / "README.md").read_text(encoding="utf-8")
    missing = [p.name for p in sorted(TOOLS.glob("*.py")) if p.name not in readme]
    assert not missing, f"describe these scripts in tools/README.md: {missing}"


def test_the_numbers_of_the_documents_come_from_the_data():
    run = subprocess.run([sys.executable, str(TOOLS / "make_facts.py"), "--check"], cwd=ROOT, capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr


def test_the_generators_write_lf_line_endings():
    """`Path.write_text` without `newline=` writes CRLF on Windows: every file the tools write must be LF (`.gitattributes`)."""
    offenders = []
    for path in sorted(TOOLS.rglob("*.py")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if ".write_text(" in line and "newline=" not in line:
                offenders.append(f"{path.relative_to(ROOT)}:{number}")
    assert not offenders, "add newline=\"\\n\" to: " + ", ".join(offenders)
