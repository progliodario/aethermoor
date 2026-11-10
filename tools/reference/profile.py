"""Reference for the profile (spec 12, "Profile"): what is kept across games in `profile.json`, next to the settings."""
from __future__ import annotations

import json

FORMAT = 1


def parse_profile(text: str | None) -> dict:
    """The profile in a text: `{"bestiary": {id: kills}, "titles": [ids]}`. A missing or broken text gives an empty profile; entries that do not make sense are left out."""
    empty = {"bestiary": {}, "titles": []}
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
    return {"bestiary": dict(sorted(bestiary.items())), "titles": titles}


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
    return {"bestiary": dict(sorted(merged.items())), "titles": out_titles}


def profile_to_json(profile: dict) -> str:
    return json.dumps({"profile_version": FORMAT, "bestiary": profile["bestiary"], "titles": profile["titles"]}, ensure_ascii=False, separators=(",", ":"))
