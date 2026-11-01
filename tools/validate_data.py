#!/usr/bin/env python3
"""Validate project metadata, content packs and localization.

Checks:
  1. Every schema in schemas/ is a valid JSON Schema.
  2. project.json matches schemas/project.schema.json.
  3. Every JSON file under data/ parses; files with "$schema" are validated against it.
  4. Every pack has a pack.json; its declared languages have i18n folders.
  5. i18n keys are identical across languages and placeholders ({name}) agree.
  6. Every "$i18n:key" used in the data exists in every language of the pack.

Exit code 0 when everything passes, 1 otherwise.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reference.ids import valid_id  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER_NAME = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")
I18N_REF = re.compile(r"^\$i18n:([a-z0-9_]+(?:\.[a-z0-9_]+)*)$")


def placeholders(text: str) -> set[str]:
    """Names of top-level {placeholders}; text nested inside plural/select branches is ignored."""
    names: set[str] = set()
    depth = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "{":
            if depth == 0:
                match = PLACEHOLDER_NAME.match(text, i + 1)
                if match:
                    names.add(match.group(0))
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        i += 1
    return names


def load_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: cannot parse JSON: {exc}")
        return None


def validate_against(instance, schema_path: Path, label: str, errors: list[str]) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(instance), key=lambda e: list(e.path)):
        where = "/".join(str(p) for p in err.path) or "<root>"
        errors.append(f"{label}: {where}: {err.message}")


def collect_i18n_refs(node, out: set[str]) -> None:
    if isinstance(node, str):
        match = I18N_REF.match(node)
        if match:
            out.add(match.group(1))
    elif isinstance(node, list):
        for item in node:
            collect_i18n_refs(item, out)
    elif isinstance(node, dict):
        for key, value in node.items():
            if key != "$schema":
                collect_i18n_refs(value, out)


def collect_id_refs(node, out: set[str], top_level_id: str | None = None) -> None:
    """Strings that look like content IDs (namespace:category/name). The file's own id is skipped."""
    if isinstance(node, str):
        if node != top_level_id and valid_id(node):
            out.add(node)
    elif isinstance(node, list):
        for item in node:
            collect_id_refs(item, out)
    elif isinstance(node, dict):
        for key, value in node.items():
            if key != "$schema":
                collect_id_refs(value, out)


def check_graphs(path: Path, data: dict, errors: list[str]) -> None:
    """Dialogue and quest graphs: every `next` must point to an existing node/stage or 'end'."""
    rel = path.relative_to(ROOT)
    nodes = data.get("nodes")
    if isinstance(nodes, dict) and "start" in data:
        if data["start"] not in nodes:
            errors.append(f"{rel}: start node '{data['start']}' does not exist")
        for name, node in nodes.items():
            targets = [node.get("next")] if "next" in node else []
            targets += [c.get("next") for c in node.get("choices", [])]
            for target in targets:
                if target != "end" and target not in nodes:
                    errors.append(f"{rel}: node '{name}' points to missing node '{target}'")
    stages = data.get("stages")
    if isinstance(stages, list):
        names = {s.get("id") for s in stages}
        if len(names) != len(stages):
            errors.append(f"{rel}: duplicate stage ids")
        for stage in stages:
            if stage.get("next") != "end" and stage.get("next") not in names:
                errors.append(f"{rel}: stage '{stage.get('id')}' points to missing stage '{stage.get('next')}'")


def check_schemas(errors: list[str]) -> None:
    for path in sorted((ROOT / "schemas").glob("*.json")):
        data = load_json(path, errors)
        if data is None:
            continue
        try:
            Draft202012Validator.check_schema(data)
        except SchemaError as exc:
            errors.append(f"{path.relative_to(ROOT)}: invalid schema: {exc}")


def check_project(errors: list[str]) -> None:
    path = ROOT / "project.json"
    data = load_json(path, errors)
    if data is not None:
        validate_against(data, ROOT / "schemas" / "project.schema.json", "project.json", errors)


def check_pack(pack_dir: Path, errors: list[str]) -> None:
    rel = pack_dir.relative_to(ROOT)
    manifest_path = pack_dir / "pack.json"
    if not manifest_path.exists():
        errors.append(f"{rel}: missing pack.json")
        return

    manifest = load_json(manifest_path, errors)
    if manifest is None:
        return
    validate_against(manifest, ROOT / "schemas" / "pack.schema.json", f"{rel}/pack.json", errors)

    refs: set[str] = set()
    defined: dict[str, Path] = {}
    id_refs: dict[str, Path] = {}
    pack_id = manifest.get("id", "")
    for path in sorted(pack_dir.rglob("*.json")):
        data = load_json(path, errors)
        if data is None:
            continue
        in_i18n = "i18n" in path.relative_to(pack_dir).parts
        if not in_i18n and path != manifest_path and isinstance(data, dict):
            own_id = data.get("id")
            if own_id is not None:
                if not isinstance(own_id, str) or not valid_id(own_id):
                    errors.append(f"{path.relative_to(ROOT)}: invalid id {own_id!r}")
                else:
                    if own_id.split(":")[0] != pack_id:
                        errors.append(f"{path.relative_to(ROOT)}: id '{own_id}' is not in namespace '{pack_id}'")
                    if own_id in defined:
                        errors.append(f"{path.relative_to(ROOT)}: duplicate id '{own_id}' "
                                      f"(also in {defined[own_id].relative_to(ROOT)})")
                    defined[own_id] = path
            found: set[str] = set()
            collect_id_refs(data, found, own_id if isinstance(own_id, str) else None)
            for ref in found:
                id_refs.setdefault(ref, path)
            check_graphs(path, data, errors)
        declared = data.get("$schema") if isinstance(data, dict) else None
        if declared:
            schema_path = (path.parent / declared).resolve()
            if not schema_path.exists():
                errors.append(f"{path.relative_to(ROOT)}: $schema not found: {declared}")
            else:
                validate_against(data, schema_path, str(path.relative_to(ROOT)), errors)
        if not in_i18n:
            collect_i18n_refs(data, refs)

    for ref, source in sorted(id_refs.items()):
        if ref not in defined:
            errors.append(f"{source.relative_to(ROOT)}: reference to undefined id '{ref}'")

    languages = manifest.get("languages", [])
    tables: dict[str, dict[str, str]] = {}
    for lang in languages:
        lang_dir = pack_dir / "i18n" / lang
        if not lang_dir.is_dir():
            errors.append(f"{rel}: language '{lang}' has no folder i18n/{lang}")
            continue
        table: dict[str, str] = {}
        for path in sorted(lang_dir.rglob("*.json")):
            data = load_json(path, errors)
            if not isinstance(data, dict):
                continue
            for key, value in data.items():
                if key == "$schema":
                    continue
                if key in table:
                    errors.append(f"{path.relative_to(ROOT)}: duplicate key '{key}'")
                table[key] = value
        tables[lang] = table

    if len(tables) > 1:
        base_lang = languages[0]
        base = tables.get(base_lang, {})
        for lang, table in tables.items():
            if lang == base_lang:
                continue
            for key in sorted(set(base) - set(table)):
                errors.append(f"{rel}: key '{key}' missing in '{lang}'")
            for key in sorted(set(table) - set(base)):
                errors.append(f"{rel}: key '{key}' missing in '{base_lang}'")
            for key in sorted(set(base) & set(table)):
                if placeholders(base[key]) != placeholders(table[key]):
                    errors.append(f"{rel}: placeholders of '{key}' differ between '{base_lang}' and '{lang}'")

    for lang, table in tables.items():
        for ref in sorted(refs - set(table)):
            errors.append(f"{rel}: $i18n:{ref} used in data but missing in '{lang}'")


def main() -> int:
    errors: list[str] = []
    check_schemas(errors)
    check_project(errors)
    data_dir = ROOT / "data"
    packs = sorted(p for p in data_dir.iterdir() if p.is_dir() and p.name != "examples") if data_dir.is_dir() else []
    if not packs:
        errors.append("data/: no packs found")
    for pack in packs:
        check_pack(pack, errors)

    if errors:
        print(f"FAILED: {len(errors)} problem(s)")
        for line in errors:
            print(f"  - {line}")
        return 1
    print(f"OK: {len(packs)} pack(s) validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
