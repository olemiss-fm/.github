"""Behaviour lock for the ratchet parsers landing_page and fm-utilities-next once kept in ratchet.py."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ratchet  # noqa: E402
from ratchet import Finding, ToolOutputError  # noqa: E402

ESLINT = json.dumps([
    {"filePath": "/repo/web/a.js", "messages": [
        {"ruleId": "sonarjs/cognitive-complexity", "message": "Too complex", "line": 10, "endLine": 40},
        {"ruleId": None, "message": "Parsing error", "line": 3},
    ]},
    {"filePath": "/repo/web/b.js", "messages": []},
])
KNIP = json.dumps({
    "files": ["web/dead.js"],
    "issues": [{"file": "tests/e2e/package.json", "dependencies": [{"name": "left-pad"}], "exports": []}],
})


def test_eslint():
    got = ratchet.parse_eslint(ESLINT)
    assert got == [
        Finding("/repo/web/a.js", 10, "sonarjs/cognitive-complexity", "Too complex", 40),
        Finding("/repo/web/a.js", 3, "eslint", "Parsing error", 0),
    ]


def test_knip():
    assert ratchet.parse_knip(KNIP) == [
        Finding("web/dead.js", 1, "knip:files", "unused file"),
        Finding("tests/e2e/package.json", 1, "knip:dependencies", "unused dependencies: left-pad"),
    ]


def test_mypy_keeps_errors_only():
    text = "backend/x.py:12:5: error: Incompatible types  [assignment]\nbackend/x.py:12:5: note: see docs\n"
    assert ratchet.parse_mypy(text) == [Finding("backend/x.py", 12, "assignment", "Incompatible types")]


def test_tsc():
    text = "web/x.js(4,9): error TS2304: Cannot find name 'Fuse'.\n"
    assert ratchet.parse_tsc(text) == [Finding("web/x.js", 4, "TS2304", "Cannot find name 'Fuse'.")]


@pytest.mark.parametrize("parse", [ratchet.parse_mypy, ratchet.parse_tsc])
def test_unreadable_output_is_an_error(parse):
    with pytest.raises(ToolOutputError):
        parse("Traceback (most recent call last):\n")


def test_coverage_section():
    data = {
        "totals": {"percent_covered": 61.234, "covered_lines": 61, "num_statements": 100},
        "files": {
            "backend/big.py": {"summary": {"percent_covered": 12.0, "num_statements": 80}},
            "backend/tiny.py": {"summary": {"percent_covered": 0.0, "num_statements": 3}},
        },
    }
    out = ratchet.coverage_section(json.dumps(data), "api", "api tests")
    assert "61.2% of api lines" in out
    assert "`backend/big.py` 12%" in out
    assert "tiny" not in out


def test_knip_repo_relative_path_reaches_changed_line():
    """The workflow runs knip from a workspace root, so its paths match the diff's web/src/... paths."""
    text = json.dumps({"files": [], "issues": [{"file": "web/src/api.js", "exports": [{"name": "x", "line": 8}]}]})
    found = ratchet.normalize(ratchet.parse_knip(text), ["/repo/"])
    kept = ratchet.on_changed_lines(found, {"web/src/api.js": {8}})
    assert [f.rule for f in kept] == ["knip:exports"]


def test_knip_duplicates_are_groups():
    """knip reports each duplicate export as a list of the names it goes by (knip 5.43.6, seen on devdock)."""
    text = json.dumps({"files": [], "issues": [{"file": "web/src/api.js", "duplicates": [
        [{"name": "getJSON", "line": 1, "col": 1}, {"name": "default", "line": 9, "col": 15}],
    ]}]})
    assert ratchet.parse_knip(text) == [
        Finding("web/src/api.js", 1, "knip:duplicates", "duplicate export: getJSON, default"),
        Finding("web/src/api.js", 9, "knip:duplicates", "duplicate export: getJSON, default"),
    ]


def test_mypy_notes_only_is_clean():
    """mypy exits 0 and prints only a note for an annotated local in an untyped function (mypy 1.18.2)."""
    text = (
        "api/app/x.py:2: note: By default the bodies of untyped functions are not checked, consider using"
        " --check-untyped-defs  [annotation-unchecked]\n"
    )
    assert ratchet.parse_mypy(text) == []


def test_coverage_section_wording_follows_the_labels():
    data = {"totals": {"percent_covered": 50.0, "covered_lines": 1, "num_statements": 2}, "files": {}}
    out = ratchet.coverage_section(json.dumps(data), "backend", "backend unit tests")
    assert out == (
        "### coverage: 50.0% of backend lines (report only)\n"
        "1 of 2 statements run by the backend unit tests."
    )


def _run(tmp_path, monkeypatch, tool, text, *extra):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    inp = tmp_path / "in"
    inp.write_text(text)
    diff = tmp_path / "d.diff"
    diff.write_text("")
    return ratchet.main(["--tool", tool, "--input", str(inp), "--diff-file", str(diff), *extra])


def test_cli_coverage_reports_and_passes_even_in_enforce(tmp_path, monkeypatch, capsys):
    data = {"totals": {"percent_covered": 10.0, "covered_lines": 1, "num_statements": 10}, "files": {}}
    rc = _run(tmp_path, monkeypatch, "coverage", json.dumps(data), "--mode", "enforce",
              "--coverage-label", "api", "--coverage-suite", "api tests")
    assert rc == 0
    assert "10.0% of api lines" in capsys.readouterr().out


def test_cli_coverage_bad_report_is_a_failed_section(tmp_path, monkeypatch, capsys):
    assert _run(tmp_path, monkeypatch, "coverage", "{}") == 2
    assert "### coverage: could not evaluate (FAIL)" in capsys.readouterr().out


@pytest.mark.parametrize("tool", ["mypy", "tsc"])
def test_cli_clean_run_prints_nothing_and_passes(tmp_path, monkeypatch, tool):
    assert _run(tmp_path, monkeypatch, tool, "", "--mode", "enforce") == 0


def test_twelve_full_sections_fit_one_comment():
    """The shared workflow can post 7 gates plus eslint, knip, mypy, tsc and coverage in one sticky comment."""
    long_msg = "x" * 400
    body = None
    for tool in [*ratchet.PARSERS, ratchet.COVERAGE]:
        fs = [ratchet.Finding(f"a/very/long/path/to/{tool}/file_{i}.py", i, "RULE123", long_msg) for i in range(60)]
        body = ratchet.merge_comment(body, tool, ratchet.render_section(tool, fs, 10**6, "enforce"))
    assert len(ratchet.PARSERS) + 1 == 12
    assert len(body) < 65536


def test_unparseable_json_keeps_the_workflows_reason():
    with pytest.raises(ToolOutputError, match="shellcheck did not run cleanly"):
        ratchet.parse_shellcheck("shellcheck did not run cleanly (exit 2)\n")
