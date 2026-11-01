"""Player movement and collision (docs/spec/02-entities-and-movement.md). Floating point, tolerance."""
from __future__ import annotations

import math

TICK_DT = 1.0 / 60.0
DEADZONE = 0.15
PLAYER_RADIUS = 0.3


def normalize_input(x: float, y: float) -> tuple[float, float]:
    """Dead zone then clamp to the unit circle (diagonals are not faster)."""
    length = math.sqrt(x * x + y * y)
    if length < DEADZONE:
        return 0.0, 0.0
    if length > 1.0:
        return x / length, y / length
    return x, y


class Grid:
    def __init__(self, rows: list[str]) -> None:
        self.rows = rows
        self.height = len(rows)
        self.width = len(rows[0]) if rows else 0

    def solid(self, tx: int, ty: int) -> bool:
        if tx < 0 or ty < 0 or tx >= self.width or ty >= self.height:
            return True
        return self.rows[ty][tx] == "#"


def _clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v


def resolve(x: float, y: float, grid: Grid, props: list[tuple[float, float, float]]) -> tuple[float, float]:
    r = PLAYER_RADIUS
    for _ in range(4):
        moved = False
        for ty in range(math.floor(y - r), math.floor(y + r) + 1):
            for tx in range(math.floor(x - r), math.floor(x + r) + 1):
                if not grid.solid(tx, ty):
                    continue
                cx = _clamp(x, tx, tx + 1)
                cy = _clamp(y, ty, ty + 1)
                dx, dy = x - cx, y - cy
                d2 = dx * dx + dy * dy
                if d2 < r * r:
                    if d2 > 0:
                        d = math.sqrt(d2)
                        k = (r - d) / d
                        x += dx * k
                        y += dy * k
                    else:
                        left, right, top, bottom = x - tx, tx + 1 - x, y - ty, ty + 1 - y
                        m = min(left, right, top, bottom)
                        if m == left:
                            x = tx - r
                        elif m == right:
                            x = tx + 1 + r
                        elif m == top:
                            y = ty - r
                        else:
                            y = ty + 1 + r
                    moved = True
        for ex, ey, er in props:
            dx, dy = x - ex, y - ey
            d2 = dx * dx + dy * dy
            md = r + er
            if d2 < md * md:
                if d2 > 0:
                    d = math.sqrt(d2)
                    k = (md - d) / d
                    x += dx * k
                    y += dy * k
                else:
                    x = ex + md
                moved = True
        if not moved:
            break
    return x, y


def step(x: float, y: float, vx: float, vy: float, speed: float, grid: Grid,
         props: list[tuple[float, float, float]]) -> tuple[float, float]:
    """One 1/60 s tick: move along X, resolve, move along Y, resolve."""
    x += vx * speed * TICK_DT
    x, y = resolve(x, y, grid, props)
    y += vy * speed * TICK_DT
    return resolve(x, y, grid, props)


def run_script(rows: list[str], props: list[tuple[float, float, float]], start: tuple[float, float],
               speed: float, script: list[tuple[float, float, int]]) -> list[tuple[float, float]]:
    """Run segments (raw_x, raw_y, ticks); return the position after each segment."""
    grid = Grid(rows)
    x, y = start
    out = []
    for raw_x, raw_y, ticks in script:
        vx, vy = normalize_input(raw_x, raw_y)
        for _ in range(ticks):
            x, y = step(x, y, vx, vy, speed, grid, props)
        out.append((x, y))
    return out
