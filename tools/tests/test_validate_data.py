import importlib.util
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("validate_data", TOOLS / "validate_data.py")
validate_data = importlib.util.module_from_spec(spec)
sys.modules["validate_data"] = validate_data
spec.loader.exec_module(validate_data)


def test_repository_data_is_valid():
    assert validate_data.main() == 0


def test_collect_i18n_refs_finds_nested_refs():
    refs = set()
    validate_data.collect_i18n_refs({"a": "$i18n:x.y", "b": [{"c": "$i18n:z"}], "$schema": "$i18n:ignored"}, refs)
    assert refs == {"x.y", "z"}


def test_placeholders_ignore_text_inside_plural_branches():
    text = "Hi {name}, {count, plural, one {apple} other {apples}}"
    assert validate_data.placeholders(text) == {"name", "count"}


def test_placeholders_plain_text_has_none():
    assert validate_data.placeholders("No placeholders here") == set()
