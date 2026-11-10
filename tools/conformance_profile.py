"""Conformance suite `profile` (spec 12, "Profile"): what a game adds to the profile that all games share."""
from __future__ import annotations

import json

from reference import profile


def _case(name: str, text, bestiary: dict, titles: list) -> dict:
    merged = profile.merge_profile(profile.parse_profile(text), bestiary, titles)
    return {"name": name, "input": {"text": text, "bestiary": bestiary, "titles": titles}, "expect": {**merged, "echo_pct": profile.echo_pct(merged)}}


def _rebirth(name: str, text, level: int) -> dict:
    """A game of `level` is reincarnated: the profile after it (unchanged when the level is too low), whether it was allowed, and the echoes."""
    before = profile.parse_profile(text)
    after = profile.reincarnate(before, level)
    result = after if after is not None else before
    return {"name": name, "input": {"text": text, "bestiary": {}, "titles": [], "rebirth_level": level},
            "expect": {**result, "echo_pct": profile.echo_pct(result), "reborn": after is not None}}


def suite_profile() -> list[dict]:
    def doc(bestiary=None, titles=None, version=1):
        return json.dumps({"profile_version": version, "bestiary": bestiary or {}, "titles": titles or []})

    return [
        _case("first_game", None, {"base:enemy/slime_green": 3, "base:enemy/wolf_grey": 1}, ["newcomer", "pest_control"]),
        _case("nothing_to_add", doc({"base:enemy/slime_green": 5}, ["newcomer"]), {}, []),
        _case("best_count_wins", doc({"base:enemy/slime_green": 5, "base:enemy/wolf_grey": 9}), {"base:enemy/slime_green": 8, "base:enemy/wolf_grey": 2}, []),
        _case("titles_keep_their_order", doc(titles=["hero", "newcomer"]), {}, ["newcomer", "veteran", "hero"]),
        _case("broken_text_is_empty", "not json", {"base:enemy/slime_green": 1}, ["newcomer"]),
        _case("wrong_version_is_empty", doc({"base:enemy/slime_green": 9}, ["hero"], version=2), {}, []),
        _case("not_an_object_is_empty", "[1, 2]", {}, ["newcomer"]),
        _case("bad_entries_are_dropped", json.dumps({"profile_version": 1, "bestiary": {"a": 0, "b": -3, "c": "7", "d": 2.5, "e": 4}, "titles": ["x", 3, "x", None, "y"]}), {}, []),
        _case("zero_counts_ignored", doc(), {"base:enemy/slime_green": 0}, []),
        _case("lives_are_kept", json.dumps({"profile_version": 1, "bestiary": {}, "titles": ["hero"], "lives": 2}), {}, ["newcomer"]),
        _case("bad_lives_are_zero", json.dumps({"profile_version": 1, "bestiary": {}, "titles": [], "lives": -4}), {}, []),
        _case("lives_not_a_number", json.dumps({"profile_version": 1, "bestiary": {}, "titles": [], "lives": "3"}), {}, []),
        _case("echoes_stop_at_fifteen_titles", doc(titles=[f"t{i}" for i in range(20)]), {}, []),
        _rebirth("rebirth_first_life", doc(titles=["newcomer"]), 10),
        _rebirth("rebirth_too_early", doc(titles=["newcomer"]), 9),
        _rebirth("rebirth_third_life", json.dumps({"profile_version": 1, "bestiary": {"base:enemy/slime_green": 7}, "titles": ["hero", "veteran"], "lives": 2}), 31),
        _rebirth("rebirth_echoes_stop_at_ten_lives", json.dumps({"profile_version": 1, "bestiary": {}, "titles": [], "lives": 14}), 50),
        _rebirth("rebirth_from_nothing", None, 12),
    ]
