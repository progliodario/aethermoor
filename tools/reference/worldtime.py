"""World time, light and weather (docs/spec/08-world-time.md). Integer arithmetic only (spec 01).

`t` is the `time` object of the world parameters (data/base/worlds/overworld.json).
"""
from __future__ import annotations

from .numerics import hash64


def day_of(t: dict, ticks: int) -> int:
    return ticks // t["day_ticks"] + 1


def tod_pm(t: dict, ticks: int) -> int:
    """Time of day in permille: 0 = midnight, 500 = noon."""
    return (ticks % t["day_ticks"]) * 1000 // t["day_ticks"]


def season_index(t: dict, day: int) -> int:
    """Index of the season of a day (the year is the seasons in order, repeating), or -1 when the world has no seasons."""
    seasons = t.get("seasons")
    if not seasons:
        return -1
    d = (day - 1) % sum(s["days"] for s in seasons)
    for i, season in enumerate(seasons):
        if d < season["days"]:
            return i
        d -= season["days"]
    raise AssertionError("unreachable")


def light_pm(t: dict, tod: int, season: int = -1) -> int:
    """Daylight in permille, interpolated linearly between the keyframes (rounding toward zero in the changed part).

    A season may have keyframes of its own (shorter or longer days).
    """
    keys = t["seasons"][season].get("light", t["light"]) if season >= 0 else t["light"]
    for (p0, l0), (p1, l1) in zip(keys, keys[1:]):
        if p0 <= tod <= p1:
            span, d = p1 - p0, tod - p0
            if l1 >= l0:
                return l0 + (l1 - l0) * d // span
            return l0 - (l0 - l1) * d // span
    return keys[-1][1]


def weather_kind(seed: int, t: dict, period: int) -> dict:
    """The kind of a weather period; the weights come from the season of the first tick of the period when it has its own."""
    kinds = t["weather"]["kinds"]
    season = season_index(t, day_of(t, period * t["weather"]["period_ticks"]))
    weights = t["seasons"][season].get("weights", {}) if season >= 0 else {}
    total = sum(weights.get(k["id"], k["weight"]) for k in kinds)
    roll = (hash64(seed, period, 21) >> 20) % total
    acc = 0
    for kind in kinds:
        acc += weights.get(kind["id"], kind["weight"])
        if roll < acc:
            return kind
    return kinds[-1]


def weather_at(seed: int, t: dict, ticks: int) -> dict:
    """Kind id of the period, and the rain and dimming in permille (with the cross-fade at the start of a period)."""
    w = t["weather"]
    period = ticks // w["period_ticks"]
    cur = weather_kind(seed, t, period)
    prev = weather_kind(seed, t, max(period - 1, 0))
    since = ticks % w["period_ticks"]
    fade = w["fade_ticks"]
    if since >= fade:
        rain, dim = cur["rain_pm"], cur["dim_pm"]
    else:
        rain = (prev["rain_pm"] * (fade - since) + cur["rain_pm"] * since) // fade
        dim = (prev["dim_pm"] * (fade - since) + cur["dim_pm"] * since) // fade
    return {"kind": cur["id"], "rain_pm": rain, "dim_pm": dim}


def sample(seed: int, t: dict, ticks: int) -> dict:
    tod = tod_pm(t, ticks)
    weather = weather_at(seed, t, ticks)
    day = day_of(t, ticks)
    season = season_index(t, day)
    light = light_pm(t, tod, season)
    return {"day": day, "tod_pm": tod, "light_pm": light, **weather,
            "effective_light_pm": light * (1000 - weather["dim_pm"]) // 1000,
            "season": t["seasons"][season]["id"] if season >= 0 else ""}
