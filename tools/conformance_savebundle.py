"""Conformance suite `savebundle` (spec 12, "Export and import"): bundles of the files of a slot."""
from __future__ import annotations

import json

from reference import savebundle

SAVE = json.dumps({"save_version": 1, "seed": "0x00000000DEADBEEF", "map": "world", "player": {"hp": 100, "level": 3}})


def _import_case(name: str, text: str) -> dict:
    files = savebundle.import_bundle(text)
    return {"name": name, "input": {"op": "import", "text": text}, "expect": {"files": files}}


def _roundtrip_case(name: str, files: dict[str, str]) -> dict:
    return {"name": name, "input": {"op": "roundtrip", "files": files}, "expect": {"files": savebundle.import_bundle(savebundle.export_bundle(files, "0.0.1"))}}


def suite_savebundle() -> list[dict]:
    def bundle(files, version=1, extra=None):
        return json.dumps({"aethersave": version, "game_version": "0.0.1", "files": files, **(extra or {})})

    return [
        _roundtrip_case("roundtrip_all_files", {"auto.json": SAVE, "quick.json": SAVE, "protagonist.txt": "base:protagonist/sakura", "goal.txt": "8200 8150\n"}),
        _roundtrip_case("roundtrip_only_auto", {"auto.json": SAVE}),
        _roundtrip_case("roundtrip_text_with_escapes", {"auto.json": SAVE, "protagonist.txt": "café \"quoted\" \\ back\nline\ttab ☃"}),
        _roundtrip_case("roundtrip_drops_unknown_names", {"auto.json": SAVE, "notes.txt": "not packed"}),
        _import_case("import_valid", bundle({"auto.json": SAVE, "protagonist.txt": "base:protagonist/ren"})),
        _import_case("import_valid_quick_only", bundle({"quick.json": SAVE})),
        _import_case("import_wrong_version", bundle({"auto.json": SAVE}, version=2)),
        _import_case("import_version_not_a_number", bundle({"auto.json": SAVE}, version="1")),
        _import_case("import_unknown_file", bundle({"auto.json": SAVE, "other.json": SAVE})),
        _import_case("import_path_traversal", bundle({"auto.json": SAVE, "../auto.json": SAVE})),
        _import_case("import_without_a_save", bundle({"protagonist.txt": "base:protagonist/ren"})),
        _import_case("import_save_not_json", bundle({"auto.json": "not json"})),
        _import_case("import_save_not_an_object", bundle({"auto.json": "[1, 2]"})),
        _import_case("import_save_without_version", bundle({"auto.json": json.dumps({"seed": "0x1"})})),
        _import_case("import_file_not_a_string", json.dumps({"aethersave": 1, "files": {"auto.json": {"a": 1}}})),
        _import_case("import_files_not_an_object", json.dumps({"aethersave": 1, "files": [1]})),
        _import_case("import_not_json", "this is not a bundle"),
        _import_case("import_not_an_object", "[1]"),
    ]
