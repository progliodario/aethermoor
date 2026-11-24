"""The contrast of the texts of the interface (docs/dev/accessibility.md): every pair of the table reaches its minimum ratio (WCAG 2.1)."""
import re
from pathlib import Path

DOC = Path(__file__).resolve().parents[2] / "docs" / "dev" / "accessibility.md"
ROW = re.compile(r"^\| `(#[0-9A-Fa-f]{6})` \| `(#[0-9A-Fa-f]{6})` \| [^|]+ \| ([0-9.]+) \|$")


def luminance(color: str) -> float:
    channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def ratio(a: str, b: str) -> float:
    light, dark = sorted((luminance(a), luminance(b)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def test_the_known_ratios():
    assert round(ratio("#FFFFFF", "#000000"), 2) == 21.0
    assert ratio("#777777", "#777777") == 1.0


def test_every_pair_of_the_table_reaches_its_minimum():
    rows = [m.groups() for m in map(ROW.match, DOC.read_text(encoding="utf-8").splitlines()) if m]
    assert len(rows) >= 8
    for foreground, background, minimum in rows:
        assert ratio(foreground, background) >= float(minimum), (foreground, background, round(ratio(foreground, background), 2))
