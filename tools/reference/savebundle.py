"""Reference for the save bundle (spec 12, "Export and import"): the files of a slot packed into one `.aethersave` text."""
from __future__ import annotations

import json

ALLOWED = ("auto.json", "quick.json", "protagonist.txt", "goal.txt")
FORMAT = 1


def export_bundle(files: dict[str, str], game_version: str) -> str:
    """The bundle of the files of a slot (only the files with an allowed name are packed)."""
    packed = {name: files[name] for name in ALLOWED if name in files}
    return json.dumps({"aethersave": FORMAT, "game_version": game_version, "files": packed}, ensure_ascii=False, separators=(",", ":"))


def import_bundle(text: str) -> dict[str, str] | None:
    """The files of a bundle, or None when it is not a valid one."""
    try:
        doc = json.loads(text)
    except ValueError:
        return None
    if not isinstance(doc, dict) or type(doc.get("aethersave")) is not int or doc["aethersave"] != FORMAT:
        return None
    files = doc.get("files")
    if not isinstance(files, dict):
        return None
    out: dict[str, str] = {}
    for name, content in files.items():
        if name not in ALLOWED or not isinstance(content, str):
            return None
        out[name] = content
    saves = [name for name in ("auto.json", "quick.json") if name in out]
    if not saves:
        return None
    for name in saves:
        try:
            save = json.loads(out[name])
        except ValueError:
            return None
        if not isinstance(save, dict) or type(save.get("save_version")) is not int:
            return None
    return out
