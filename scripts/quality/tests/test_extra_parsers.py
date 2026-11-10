"""Behaviour lock for the parsers repos once kept beside ratchet.py (landing_page, fm-utilities-next, FMAPI,
fm-comp-time, utility_billing)."""
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


def test_every_tool_full_fits_one_comment():
    """The shared workflow can post 7 gates plus eslint, knip, mypy, tsc, uncovered and coverage in one comment."""
    long_msg = "x" * 400
    body = None
    for tool in [*ratchet.PARSERS, ratchet.COVERAGE]:
        fs = [ratchet.Finding(f"a/very/long/path/to/{tool}/file_{i}.py", i, "RULE123", long_msg) for i in range(60)]
        body = ratchet.merge_comment(body, tool, ratchet.render_section(tool, fs, 10**6, "enforce"))
    assert len(ratchet.PARSERS) + 1 == 13
    assert len(body) < 65536


def test_unparseable_json_keeps_the_workflows_reason():
    with pytest.raises(ToolOutputError, match="shellcheck did not run cleanly"):
        ratchet.parse_shellcheck("shellcheck did not run cleanly (exit 2)\n")


# ---- what FMAPI ratchet_ext.py, fm-comp-time extra_gates.py and utility_billing changed_lines.py did ----
COVERAGE_JSON = json.dumps({
    "totals": {"percent_covered": 50.0, "covered_lines": 3, "num_statements": 6},
    "files": {"app/x.py": {"missing_lines": [7, 3, 4, 9], "summary": {"percent_covered": 50.0, "num_statements": 6}}},
})


def test_uncovered_is_one_finding_per_run():
    assert ratchet.parse_uncovered(COVERAGE_JSON, "mock suite") == [
        Finding("app/x.py", 3, "uncovered", "2 line(s) not run by the mock suite", 4),
        Finding("app/x.py", 7, "uncovered", "1 line(s) not run by the mock suite", 7),
        Finding("app/x.py", 9, "uncovered", "1 line(s) not run by the mock suite", 9),
    ]


def test_cli_uncovered_is_report_only_and_takes_the_subfolder(tmp_path, monkeypatch, capsys):
    """fm-comp-time runs its tests in api/, so coverage paths need api/ put back to meet the diff."""
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    (tmp_path / "in").write_text(COVERAGE_JSON)
    (tmp_path / "d.diff").write_text(
        "diff --git a/api/app/x.py b/api/app/x.py\n+++ b/api/app/x.py\n@@ -0,0 +4,1 @@\n+x\n"
    )
    rc = ratchet.main(["--tool", "uncovered", "--input", str(tmp_path / "in"), "--diff-file", str(tmp_path / "d.diff"),
                       "--mode", "enforce", "--add-prefix", "api/", "--coverage-suite", "api tests"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "### uncovered: 1 finding on changed lines (report only)" in out
    assert "`api/app/x.py:3` uncovered: 2 line(s) not run by the api tests" in out
    assert "Mode: report." in out


def test_uncovered_bad_report_is_an_error():
    with pytest.raises(ToolOutputError):
        ratchet.parse_uncovered("{}")


def test_add_prefix_follows_strip():
    """FMAPI runs knip inside sync_ui/, fm-comp-time runs tsc and knip inside web/."""
    found = ratchet.normalize([Finding("/repo/./src/a.ts", 1, "r", "m")], ["/repo/"], "sync_ui/")
    assert found == [Finding("sync_ui/src/a.ts", 1, "r", "m")]


def test_knip_per_issue_files_do_not_crash():
    """knip 5.6x lists an unused file under its own issue (FMAPI sync_ui fixture)."""
    text = json.dumps({"issues": [
        {"file": "src/jobHistory.ts", "exports": [{"name": "strip", "line": 23}],
         "types": [{"name": "Freq", "line": 12}], "files": []},
        {"file": "src/orphan.ts", "files": [{"name": "src/orphan.ts"}]},
    ]})
    assert [(f.path, f.line, f.rule) for f in ratchet.parse_knip(text)] == [
        ("src/jobHistory.ts", 23, "knip:exports"),
        ("src/jobHistory.ts", 12, "knip:types"),
        ("src/orphan.ts", 1, "knip:files"),
    ]


def test_mypy_reads_warnings_and_no_column():
    text = "fm_api/crud.py:42: error: Bad return  [return-value]\nfm_api/crud.py:50: warning: Unused section\n"
    assert ratchet.parse_mypy(text) == [
        Finding("fm_api/crud.py", 42, "return-value", "Bad return"),
        Finding("fm_api/crud.py", 50, "mypy", "Unused section"),
    ]


def test_tsc_skips_continuation_lines():
    text = (
        "sync_ui/src/A.tsx(769,24): error TS2375: Type is not assignable to type 'X'.\n"
        "  Types of property 'title' are incompatible.\n"
        "sync_ui/src/App.tsx(12,7): error TS6133: 'envLabel' is declared but its value is never read.\n"
    )
    got = [(f.path, f.line) for f in ratchet.parse_tsc(text)]
    assert got == [("sync_ui/src/A.tsx", 769), ("sync_ui/src/App.tsx", 12)]


def test_tsc_global_error_is_not_a_pass():
    """A broken tsconfig checks nothing, even when another line looks like a finding."""
    text = (
        "error TS5058: The specified path does not exist: 'x.json'.\n"
        "web/a.ts(1,1): error TS2304: Cannot find name 'y'.\n"
    )
    with pytest.raises(ToolOutputError, match="TS5058"):
        ratchet.parse_tsc(text)


def test_eslint_fatal_message_with_null_line():
    fatal = {"ruleId": None, "fatal": True, "message": "Parsing error", "line": None, "endLine": None}
    text = json.dumps([{"filePath": "/repo/a.js", "messages": [fatal]}])
    assert ratchet.parse_eslint(text) == [Finding("/repo/a.js", 1, "eslint", "Parsing error", 0)]


# ---- round 2: real output shapes ----
def test_mypy_clean_default_summary_is_clean():
    """mypy 1.18.2 without --no-error-summary prints a note (if any) and then this line when clean."""
    text = (
        "api/app/x.py:2: note: By default the bodies of untyped functions are not checked  [annotation-unchecked]\n"
        "Success: no issues found in 12 source files\n"
    )
    assert ratchet.parse_mypy(text) == []
    assert ratchet.parse_mypy("Success: no issues found in 1 source file\n") == []


def test_mypy_error_summary_with_no_readable_error_is_not_a_pass():
    with pytest.raises(ToolOutputError):
        ratchet.parse_mypy("Found 3 errors in 2 files (checked 12 source files)\n")


def test_mypy_errors_with_summary():
    text = "a.py:1: error: Bad  [misc]\nFound 1 error in 1 file (checked 3 source files)\n"
    assert ratchet.parse_mypy(text) == [Finding("a.py", 1, "misc", "Bad")]


def test_knip5_owners_and_member_dicts():
    """knip 5.43.6 with a CODEOWNERS file: owners is a list of strings, enum and class members are dicts."""
    text = json.dumps({"files": [], "issues": [{
        "file": "src/a.ts", "owners": ["@olemiss-fm/eng"], "dependencies": [], "exports": [],
        "enumMembers": {"Color": [{"name": "Blue", "line": 3, "col": 3, "pos": 40}]},
        "classMembers": {},
    }]})
    assert ratchet.parse_knip(text) == [Finding("src/a.ts", 3, "knip:enumMembers", "unused enumMembers: Blue")]
