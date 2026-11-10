"""Conformance suite `profile` (spec 12, "Profile"): what a game adds to the profile that all games share."""
from __future__ import annotations

import json

from reference import profile


def _case(name: str, text, bestiary: dict, titles: list) -> dict:
    merged = profile.merge_profile(profile.parse_profile(text), bestiary, titles)
    return {"name": name, "input": {"text": text, "bestiary": bestiary, "titles": titles}, "expect": merged}


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
    ]
