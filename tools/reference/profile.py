"""Reference for the profile (spec 12, "Profile"): what is kept across games in `profile.json`, next to the settings."""
from __future__ import annotations

import json

FORMAT = 1
ECHO_TITLES_MAX = 15   # an echo for each title, up to this many (spec 11, "Echoes")
ECHO_PER_LIFE = 3      # percent for each past life
ECHO_LIVES_MAX = 10    # past lives that count
REBIRTH_LEVEL = 10     # the level a game needs to be reincarnated
HEIRLOOM_PCT = 50      # the share of a reincarnated game's gold that waits for the next new game (spec 11, "Heirloom")


def parse_profile(text: str | None) -> dict:
    """The profile in a text: `{"bestiary": {id: kills}, "titles": [ids]}`. A missing or broken text gives an empty profile; entries that do not make sense are left out."""
    empty = {"bestiary": {}, "titles": [], "lives": 0, "heirloom": 0}
    if not text:
        return empty
    try:
        doc = json.loads(text)
    except ValueError:
        return empty
    if not isinstance(doc, dict) or type(doc.get("profile_version")) is not int or doc["profile_version"] != FORMAT:
        return empty
    bestiary = {}
    if isinstance(doc.get("bestiary"), dict):
        for name, count in doc["bestiary"].items():
            if type(count) is int and count >= 1:
                bestiary[name] = count
    titles: list[str] = []
    if isinstance(doc.get("titles"), list):
        for title in doc["titles"]:
            if isinstance(title, str) and title not in titles:
                titles.append(title)
    lives = doc["lives"] if type(doc.get("lives")) is int and doc["lives"] >= 0 else 0
    heirloom = doc["heirloom"] if type(doc.get("heirloom")) is int and doc["heirloom"] >= 0 else 0
    return {"bestiary": dict(sorted(bestiary.items())), "titles": titles, "lives": lives, "heirloom": heirloom}


def merge_profile(profile: dict, bestiary: dict[str, int], titles: list[str]) -> dict:
    """The profile after a game reports its bestiary and titles: the best count of every creature, and every title ever earned (in the order they were first earned)."""
    merged = dict(profile["bestiary"])
    for name, count in bestiary.items():
        if count >= 1:
            merged[name] = max(merged.get(name, 0), count)
    out_titles = list(profile["titles"])
    for title in titles:
        if title not in out_titles:
            out_titles.append(title)
    return {"bestiary": dict(sorted(merged.items())), "titles": out_titles, "lives": profile.get("lives", 0), "heirloom": profile.get("heirloom", 0)}


def reincarnate(profile: dict, level: int, gold: int = 0) -> dict | None:
    """The profile after a game of that level, with that gold, is reincarnated: one more past life, and half of the gold kept as the heirloom
    of the next new game. None when the level is too low (spec 11, "Reincarnation", "Heirloom")."""
    if level < REBIRTH_LEVEL:
        return None
    return {**profile, "lives": profile.get("lives", 0) + 1, "heirloom": profile.get("heirloom", 0) + max(0, gold) * HEIRLOOM_PCT // 100}


def claim_heirloom(profile: dict) -> tuple[int, dict]:
    """A new game takes the heirloom: the gold it starts with, and the profile with nothing left waiting."""
    return profile.get("heirloom", 0), {**profile, "heirloom": 0}


def echo_pct(profile: dict) -> int:
    """The percent of maximum health that the profile gives to every game (spec 11, "Echoes")."""
    return min(len(profile["titles"]), ECHO_TITLES_MAX) + ECHO_PER_LIFE * min(profile.get("lives", 0), ECHO_LIVES_MAX)


def profile_to_json(profile: dict) -> str:
    return json.dumps({"profile_version": FORMAT, "bestiary": profile["bestiary"], "titles": profile["titles"], "lives": profile.get("lives", 0), "heirloom": profile.get("heirloom", 0)}, ensure_ascii=False, separators=(",", ":"))
