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


# ------------------------------------------------------------------------------- a pack of its own (a mod)

def _copy_example(tmp_path):
    import shutil

    target = tmp_path / "mod"
    shutil.copytree(TOOLS.parent / "examples" / "mod-example", target)
    return target


def test_the_example_mod_is_valid():
    assert validate_data.main([str(TOOLS.parent / "examples" / "mod-example")]) == 0


def test_a_mod_outside_the_repository_is_valid(tmp_path):
    assert validate_data.main([str(_copy_example(tmp_path))]) == 0


def test_a_mod_that_names_a_missing_thing_fails(tmp_path, capsys):
    import json

    mod = _copy_example(tmp_path)
    path = mod / "quests" / "side" / "honey_hunt.json"
    quest = json.loads(path.read_text(encoding="utf-8"))
    quest["stages"][0]["objectives"][0]["enemy"] = "example:enemy/slime_nowhere"
    path.write_text(json.dumps(quest), encoding="utf-8", newline="\n")
    assert validate_data.main([str(mod)]) == 1
    assert "example:enemy/slime_nowhere" in capsys.readouterr().out


def test_a_mod_that_defines_a_thing_of_the_base_again_fails(tmp_path, capsys):
    import json

    mod = _copy_example(tmp_path)
    path = mod / "enemies" / "slime_honey.json"
    enemy = json.loads(path.read_text(encoding="utf-8"))
    enemy["id"] = "base:enemy/slime_green"
    path.write_text(json.dumps(enemy), encoding="utf-8", newline="\n")
    assert validate_data.main([str(mod)]) == 1
    out = capsys.readouterr().out
    assert "already defined by a pack it depends on" in out and "not in namespace 'example'" in out


def test_a_mod_without_a_text_fails(tmp_path, capsys):
    import json

    mod = _copy_example(tmp_path)
    path = mod / "i18n" / "it" / "content.json"
    texts = json.loads(path.read_text(encoding="utf-8"))
    del texts["quest.honey_hunt.task"]
    path.write_text(json.dumps(texts), encoding="utf-8", newline="\n")
    assert validate_data.main([str(mod)]) == 1
    assert "quest.honey_hunt.task" in capsys.readouterr().out
