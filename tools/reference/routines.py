"""Daily routines of settlement people (docs/spec/08-world-time.md, "Routines"). Integer arithmetic only."""
from __future__ import annotations


def state(params: dict, role: str, tod_pm: int) -> str:
    """`work`, `plaza` or `away`: the state of the last keyframe of the role that starts at or before the time of day.

    A role with no routine is always at work.
    """
    frames = params.get("routines", {}).get("roles", {}).get(role)
    if not frames:
        return "work"
    current = frames[0][1]
    for from_pm, frame_state in frames:
        if from_pm <= tod_pm:
            current = frame_state
    return current


def placement(params: dict, person: dict, tod_pm: int) -> tuple[str, int, int] | None:
    """(state, x256, y256) of a person at a time of day, or None while the person is away.

    At the plaza the person stands on its gathering spot; a settlement without spots keeps its people at work.
    """
    current = state(params, person["role"], tod_pm)
    if current == "away":
        return None
    if current == "plaza" and person["plaza_x256"] >= 0:
        return "plaza", person["plaza_x256"], person["plaza_y256"]
    return "work", person["x256"], person["y256"]
