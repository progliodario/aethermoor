"""The checks of the repository that ci-data runs: the licenses of the dependencies (tools/licenses.py), the parity matrix of the
two clients (tools/make_parity.py)."""
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import licenses  # noqa: E402
import make_parity  # noqa: E402
import make_suites_map  # noqa: E402


def table() -> dict:
    return json.loads(licenses.TABLE.read_text(encoding="utf-8"))


def test_every_dependency_has_an_allowed_license():
    assert licenses.problems(licenses.find_dependencies(), table()) == []


def test_a_dependency_without_a_row_fails_the_check():
    found = licenses.find_dependencies() | {("vcpkg", "some-new-library")}
    assert any("some-new-library" in p and "no row" in p for p in licenses.problems(found, table()))


def test_a_row_whose_dependency_is_gone_fails_the_check():
    found = licenses.find_dependencies() - {("vcpkg", "catch2")}
    assert any("catch2" in p and "remove the row" in p for p in licenses.problems(found, table()))


def test_a_license_outside_its_scope_fails_the_check():
    t = table()
    t["dependencies"] = [{**row, "license": "EPL-2.0"} if row["name"] == "sdl3" else row for row in t["dependencies"]]
    assert any("sdl3" in p and "EPL-2.0" in p for p in licenses.problems(licenses.find_dependencies(), t))
    t["dependencies"][0] = {**t["dependencies"][0], "license": "GPL-2.0-only"}
    assert any("not one the project allows" in p for p in licenses.problems(licenses.find_dependencies(), t))


def test_the_notices_are_written_from_the_table():
    assert licenses.NOTICES.read_text(encoding="utf-8") == licenses.notices(table())


def test_both_clients_run_every_suite():
    text, problems = make_parity.matrix()
    assert problems == []
    assert make_parity.OUT.read_text(encoding="utf-8") == text


def test_a_suite_a_client_does_not_run_fails_the_check(tmp_path, monkeypatch):
    source = 'TEST_CASE("conformance: rng", "[conformance]") {\n    const Json doc = load_suite("rng");\n}\n'
    (tmp_path / "x_test.cpp").write_text(source, encoding="utf-8", newline="\n")
    monkeypatch.setattr(make_parity, "DESKTOP_TESTS", tmp_path)
    _, problems = make_parity.matrix()
    assert any("desktop" in p and "'hash'" in p for p in problems)
    assert not any("desktop" in p and "'rng'" in p for p in problems)


def test_every_category_of_the_plan_has_its_cases():
    text, problems = make_suites_map.build()
    assert problems == []
    assert make_suites_map.OUT.read_text(encoding="utf-8") == text
