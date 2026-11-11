"""Conformance suite `profile` (spec 12, "Profile"): what a game adds to the profile that all games share."""
from __future__ import annotations

import json

from reference import profile


def _case(name: str, text, bestiary: dict, titles: list) -> dict:
    merged = profile.merge_profile(profile.parse_profile(text), bestiary, titles)
    return {"name": name, "input": {"text": text, "bestiary": bestiary, "titles": titles}, "expect": {**merged, "echo_pct": profile.echo_pct(merged)}}


def _claim(name: str, text) -> dict:
    """A new game takes the heirloom of the profile: the gold it gets, and the profile after."""
    before = profile.parse_profile(text)
    gold, after = profile.claim_heirloom(before)
    return {"name": name, "input": {"text": text, "bestiary": {}, "titles": [], "claim": True},
            "expect": {**after, "echo_pct": profile.echo_pct(after), "claimed": gold, "claimed_item": before["heirloom_item"]}}


def _rebirth(name: str, text, level: int, gold: int = 0, weapon: str = "") -> dict:
    """A game of `level` is reincarnated: the profile after it (unchanged when the level is too low), whether it was allowed, and the echoes."""
    before = profile.parse_profile(text)
    after = profile.reincarnate(before, level, gold, weapon)
    result = after if after is not None else before
    return {"name": name, "input": {"text": text, "bestiary": {}, "titles": [], "rebirth_level": level, "rebirth_gold": gold, "rebirth_weapon": weapon},
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
        _rebirth("heirloom_half_of_the_gold", None, 15, 1001),
        _rebirth("heirloom_adds_up", json.dumps({"profile_version": 1, "bestiary": {}, "titles": [], "lives": 1, "heirloom": 300}), 20, 4000),
        _rebirth("heirloom_not_when_too_early", json.dumps({"profile_version": 1, "bestiary": {}, "titles": [], "heirloom": 70}), 5, 900),
        _claim("claim_the_heirloom", json.dumps({"profile_version": 1, "bestiary": {}, "titles": ["hero"], "lives": 2, "heirloom": 2300})),
        _claim("claim_nothing", json.dumps({"profile_version": 1, "bestiary": {}, "titles": [], "lives": 1})),
        _rebirth("heirloom_weapon", None, 12, 100, "base:item/steel_sword"),
        _rebirth("heirloom_weapon_replaces", json.dumps({"profile_version": 1, "bestiary": {}, "titles": [], "heirloom_item": "base:item/pike"}), 14, 0, "base:item/moon_blade"),
        _rebirth("heirloom_no_weapon_keeps", json.dumps({"profile_version": 1, "bestiary": {}, "titles": [], "heirloom_item": "base:item/pike"}), 14, 0, ""),
        _rebirth("heirloom_weapon_not_when_too_early", None, 3, 0, "base:item/steel_sword"),
        _claim("claim_the_weapon", json.dumps({"profile_version": 1, "bestiary": {}, "titles": [], "heirloom": 40, "heirloom_item": "base:item/steel_sword"})),
        _case("bad_heirloom_item_is_none", json.dumps({"profile_version": 1, "bestiary": {}, "titles": [], "heirloom_item": 7}), {}, []),
        _case("bad_heirloom_is_zero", json.dumps({"profile_version": 1, "bestiary": {}, "titles": [], "heirloom": -50}), {}, []),
    ]
