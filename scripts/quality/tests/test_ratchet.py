"""Behaviour lock for scripts/quality/ratchet.py. Fixtures are real tool output shapes."""
import json
import os
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ratchet  # noqa: E402

FX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def fx(name):
    with open(os.path.join(FX, name), encoding="utf-8") as fh:
        return fh.read()


ADDED = ratchet.parse_diff(fx("pr.diff"))


# ---- diff parsing -------------------------------------------------------------
def test_diff_added_lines_for_edited_file():
    assert ADDED["app/old.py"] == {11, 12, 32}


def test_diff_pure_deletion_hunk_adds_nothing():
    assert 51 not in ADDED["app/old.py"]


def test_diff_new_file_all_lines():
    assert ADDED["app/new.py"] == {1, 2, 3}


def test_diff_deleted_file_absent():
    assert "app/removed.py" not in ADDED


def test_diff_rename_uses_new_path():
    assert ADDED["docs/b.py"] == {4}
    assert "docs/a.py" not in ADDED


def test_diff_path_with_space_and_trailing_tab():
    assert ADDED["with space/f.sh"] == {1}


def test_diff_binary_ignored():
    assert "img.png" not in ADDED


def test_diff_added_line_that_looks_like_a_file_header():
    d = ("diff --git a/a.md b/a.md\n--- a/a.md\n+++ b/a.md\n@@ -1,0 +2,2 @@\n+--- x\n+++ title\n"
         "@@ -9,0 +12 @@\n+more\n")
    assert ratchet.parse_diff(d) == {"a.md": {2, 3, 12}}


def test_diff_empty():
    assert ratchet.parse_diff("") == {}


# ---- parsers ------------------------------------------------------------------
def rules(findings):
    return [(f.path, f.line, f.rule) for f in findings]


def test_ruff_parser():
    fs = ratchet.PARSERS["ruff"](fx("ruff.json"))
    assert ("/repo/app/old.py", 11, "E501") in rules(fs)
    assert len(fs) == 4
    assert fs[0].message.startswith("Line too long")


def test_ruff_empty_array_ok():
    assert ratchet.PARSERS["ruff"]("[]") == []


def test_shellcheck_parser():
    a = ratchet.PARSERS["shellcheck"](fx("shellcheck.json"))
    assert rules(a)[0] == ("with space/f.sh", 1, "SC2086")


def test_hadolint_parser():
    assert rules(ratchet.PARSERS["hadolint"](fx("hadolint.json")))[0] == ("app/new.py", 2, "DL3006")


def test_sqlfluff_parser_uses_end_line():
    fs = ratchet.PARSERS["sqlfluff"](fx("sqlfluff.json"))
    assert rules(fs) == [("app/new.py", 3, "LT01"), ("app/new.py", 20, "LT02")]


def test_actionlint_parser_and_null():
    assert len(ratchet.PARSERS["actionlint"](fx("actionlint.json"))) == 2
    assert ratchet.PARSERS["actionlint"](fx("actionlint_null.json")) == []
    with pytest.raises(ratchet.ToolOutputError):
        ratchet.PARSERS["actionlint"]("")


def test_jscpd_reports_both_sides_with_other_location():
    fs = ratchet.PARSERS["jscpd"](fx("jscpd.json"))
    assert len(fs) == 4
    first = fs[0]
    assert (first.path, first.line, first.end_line) == ("app/new.py", 1, 3)
    assert "app/untouched.py:50-62" in first.message


def test_vulture_text_parser_skips_noise():
    fs = ratchet.PARSERS["vulture"](fx("vulture.txt"))
    assert rules(fs) == [("app/old.py", 11, "vulture"), ("app/old.py", 200, "vulture"), ("app/new.py", 2, "vulture")]
    assert "unused function 'helper'" in fs[0].message


def test_vulture_file_it_could_not_read_or_parse_counts_on_any_changed_line():
    """vulture skips such a file (stderr, merged in by the workflow), so none of its lines were checked."""
    text = (
        'app/old.py:106: invalid syntax at "x = 1  # type: row dropped"\n'
        'app/new.py: invalid source code "source code string cannot contain null bytes"\n'
        "Error: Could not read file app/gone.py - bad byte\nTry to change the encoding to UTF-8.\n"
    )
    fs = ratchet.PARSERS["vulture"](text)
    assert [f.path for f in fs] == ["app/old.py", "app/new.py", "app/gone.py"]
    assert all("not checked" in f.message for f in fs)
    # old.py changed lines 11, 12, 32 (not 106) and new.py 1-3: both files count; gone.py is untouched
    assert [f.path for f in ratchet.on_changed_lines(fs, ADDED)] == ["app/new.py", "app/old.py"]


def test_vulture_null_byte_file_on_python_3_12_plus_is_a_skipped_file():
    text = ("app/nul.py:None: source code string cannot contain null bytes\n"
            "app/ok.py:1: unused import 'os' (90% confidence)\n")
    nul = ratchet.PARSERS["vulture"](text)[0]
    assert (nul.path, nul.end_line) == ("app/nul.py", ratchet.WHOLE_FILE) and "not checked" in nul.message


def test_vulture_unreadable_path_with_a_dash_is_kept_whole():
    text = "Error: Could not read file docs/a - b.py - \nTry to change the encoding to UTF-8.\n"
    assert [f.path for f in ratchet.PARSERS["vulture"](text)] == ["docs/a - b.py"]


def test_vulture_python_warning_on_stderr_is_not_a_skipped_file():
    text = "app/old.py:12: SyntaxWarning: invalid escape sequence '\\d'\n  x = re.compile(\"\\d\")\n"
    assert ratchet.PARSERS["vulture"](text + "app/old.py:11: unused import 're' (90% confidence)\n") == [
        ratchet.Finding("app/old.py", 11, "vulture", "unused import 're' (90% confidence)")
    ]
    assert ratchet.PARSERS["vulture"](text) == []  # a clean run that only warned is not unreadable output


@pytest.mark.parametrize("name", sorted(ratchet.PARSERS))
def test_every_parser_rejects_garbage(name):
    with pytest.raises(ratchet.ToolOutputError):
        ratchet.PARSERS[name]("<html>boom</html>" if name != "vulture" else "\x00\x01")


# ---- paths and filtering ------------------------------------------------------
def test_normalize_path():
    p = ["/repo/"]
    assert ratchet.normalize_path("/repo/app/x.py", p) == "app/x.py"
    assert ratchet.normalize_path("./app/x.py", p) == "app/x.py"
    assert ratchet.normalize_path("app/x.py", p) == "app/x.py"


def test_keep_only_changed_lines():
    fs = ratchet.normalize(ratchet.PARSERS["ruff"](fx("ruff.json")), ["/repo/"])
    kept = ratchet.on_changed_lines(fs, ADDED)
    # old.py:5 is untouched code; 11, 32 and new.py:1 are in the diff
    assert rules(kept) == [("app/new.py", 1, "F401"), ("app/old.py", 11, "E501"), ("app/old.py", 32, "S608")]


def test_range_finding_kept_when_any_line_overlaps():
    f = ratchet.Finding("app/old.py", 10, "X", "m", 11)
    assert ratchet.on_changed_lines([f], ADDED) == [f]
    g = ratchet.Finding("app/old.py", 13, "X", "m", 20)
    assert ratchet.on_changed_lines([g], ADDED) == []


def test_finding_on_unchanged_file_dropped():
    assert ratchet.on_changed_lines([ratchet.Finding("zzz.py", 1, "X", "m", 1)], ADDED) == []


def test_duplicates_collapsed():
    f = ratchet.Finding("app/new.py", 1, "X", "m", 1)
    assert ratchet.on_changed_lines([f, f], ADDED) == [f]


# ---- rendering and sticky comment --------------------------------------------
def test_section_clean():
    s = ratchet.render_section("ruff", [], 6026, "report")
    assert "ruff" in s and "0 findings on changed lines" in s and "6026" in s


def test_section_lists_findings_and_caps():
    fs = [ratchet.Finding("a.py", i, "E1", "msg", i) for i in range(1, 80)]
    s = ratchet.render_section("ruff", fs, 100, "report", limit=50)
    assert all(len(x) <= ratchet.MAX_LINE for x in s.splitlines())
    assert "79 findings on changed lines" in s
    assert s.count("`a.py:") == 50
    assert "29 more" in s


def test_section_is_ascii_and_escapes_markers():
    f = ratchet.Finding("a.py", 1, "E1", "caf\u00e9 <!-- ratchet-sticky --> \u2014 x", 1)
    s = ratchet.render_section("ruff", [f], 1, "enforce")
    s.encode("ascii")
    assert s.count("<!-- ratchet-sticky -->") == 0
    assert "@sam" not in s and s.count("`") == 2


def test_enforce_section_says_failing():
    f = ratchet.Finding("a.py", 1, "E1", "m", 1)
    assert "FAIL" in ratchet.render_section("ruff", [f], 1, "enforce")
    assert "FAIL" not in ratchet.render_section("ruff", [f], 1, "report")


def test_merge_comment_new():
    body = ratchet.merge_comment(None, "ruff", "<S1>")
    assert body.startswith(ratchet.STICKY)
    assert "<S1>" in body


def test_merge_comment_replaces_own_section_keeps_others():
    b = ratchet.merge_comment(None, "ruff", "OLD-RUFF")
    b = ratchet.merge_comment(b, "vulture", "VULT")
    b = ratchet.merge_comment(b, "ruff", "NEW-RUFF")
    assert "OLD-RUFF" not in b and "NEW-RUFF" in b and "VULT" in b
    assert b.count(ratchet.STICKY) == 1
    assert b.index("NEW-RUFF") < b.index("VULT")


class FakeGh:
    """Stands in for gh: the list call returns one JSON comment per line, as `--jq .[]` does."""

    def __init__(self, comments):
        self.comments = comments
        self.calls = []

    def __call__(self, args, body=None):
        self.calls.append((args, body))
        if args[:2] == ["api", "--paginate"]:
            return "\n".join(json.dumps(c) for c in self.comments)
        return "{}"


BOT = {"type": "Bot"}


def test_post_creates_when_absent():
    gh = FakeGh([{"id": 1, "body": "unrelated"}])
    ratchet.post_comment("o/r", 7, "ruff", "S", gh)
    method_calls = [c for c in gh.calls if "POST" in c[0]]
    assert len(method_calls) == 1
    assert "repos/o/r/issues/7/comments" in method_calls[0][0]
    assert ratchet.STICKY in method_calls[0][1]


def test_post_ignores_marker_pasted_by_a_human():
    pasted = ratchet.merge_comment(None, "ruff", "X")
    gh = FakeGh([{"id": 5, "body": pasted, "user": {"type": "User"}}])
    ratchet.post_comment("o/r", 7, "ruff", "S", gh)
    assert [c for c in gh.calls if "POST" in c[0]] and not [c for c in gh.calls if "PATCH" in c[0]]


def test_post_updates_existing_in_place():
    existing = ratchet.merge_comment(None, "vulture", "VULT")
    gh = FakeGh([{"id": 1, "body": "x"}, {"id": 42, "body": existing, "user": BOT}])
    ratchet.post_comment("o/r", 7, "ruff", "S", gh)
    patch = [c for c in gh.calls if "PATCH" in c[0]]
    assert len(patch) == 1 and "repos/o/r/issues/comments/42" in patch[0][0]
    assert "VULT" in patch[0][1] and "S" in patch[0][1]
    assert not [c for c in gh.calls if "POST" in c[0]]


# ---- end to end (main) --------------------------------------------------------
@pytest.fixture
def run(tmp_path, monkeypatch):
    diff = tmp_path / "pr.diff"
    diff.write_text(fx("pr.diff"))

    def _run(mode, tool="ruff", src="ruff.json"):
        out = tmp_path / "out.md"
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(out))
        rc = ratchet.main(
            ["--tool", tool, "--input", os.path.join(FX, src), "--mode", mode,
             "--diff-file", str(diff), "--strip-prefix", "/repo/"]
        )
        return rc, (out.read_text() if out.exists() else "")

    return _run


def test_main_report_exit_zero_with_findings(run):
    rc, text = run("report")
    assert rc == 0 and "3 findings on changed lines" in text


def test_main_enforce_exit_one_with_findings(run):
    rc, _ = run("enforce")
    assert rc == 1


def test_main_enforce_clean_exit_zero(run):
    rc, text = run("enforce", tool="actionlint", src="actionlint_null.json")
    assert rc == 0 and "0 findings" in text


def test_main_unparseable_exit_two_in_both_modes(run):
    for mode in ("report", "enforce"):
        rc, _ = run(mode, src="pr.diff")
        assert rc == 2


def test_main_missing_input_exit_two(tmp_path):
    rc = ratchet.main(["--tool", "ruff", "--input", str(tmp_path / "nope"), "--mode", "report",
                       "--diff-file", os.path.join(FX, "pr.diff")])
    assert rc == 2


def test_main_non_utf8_input_does_not_crash(tmp_path):
    f = tmp_path / "r.json"
    f.write_bytes(b'[{"filename": "caf\xe9.py", "location": {"row": 1}, "end_location": {"row": 1}, '
                  b'"code": "E1", "message": "m"}]')
    assert ratchet.main(["--tool", "ruff", "--input", str(f), "--diff-file", os.path.join(FX, "pr.diff")]) == 0


def test_main_wrong_shape_exit_two(tmp_path):
    f = tmp_path / "r.json"
    f.write_text('["not a dict"]')
    assert ratchet.main(["--tool", "ruff", "--input", str(f), "--diff-file", os.path.join(FX, "pr.diff")]) == 2


def test_main_vulture_empty_is_clean(tmp_path):
    f = tmp_path / "v.txt"
    f.write_text("")
    assert ratchet.main(["--tool", "vulture", "--input", str(f), "--diff-file", os.path.join(FX, "pr.diff")]) == 0


def test_bad_quality_mode_env_is_an_error(tmp_path, monkeypatch):
    monkeypatch.setenv("QUALITY_MODE", "enforced")
    with pytest.raises(SystemExit) as e:
        ratchet.main(["--tool", "ruff", "--input", os.path.join(FX, "ruff.json"),
                      "--diff-file", os.path.join(FX, "pr.diff")])
    assert e.value.code == 2


def test_main_empty_input_exit_two(tmp_path):
    empty = tmp_path / "e.json"
    empty.write_text("")
    rc = ratchet.main(["--tool", "ruff", "--input", str(empty), "--mode", "report",
                       "--diff-file", os.path.join(FX, "pr.diff")])
    assert rc == 2


def test_main_unreadable_output_replaces_the_stale_section(tmp_path, monkeypatch):
    stale = ratchet.merge_comment(None, "ruff", "### ruff: 0 findings on changed lines (ok)")
    gh = FakeGh([{"id": 42, "body": stale, "user": BOT}])
    monkeypatch.setattr(ratchet, "run_gh", gh)
    empty = tmp_path / "e.json"
    empty.write_text("")
    rc = ratchet.main(["--tool", "ruff", "--input", str(empty), "--mode", "report",
                       "--diff-file", os.path.join(FX, "pr.diff"), "--repo", "o/r", "--pr", "9"])
    body = json.loads([c for c in gh.calls if "PATCH" in c[0]][0][1])["body"]
    assert rc == 2
    assert "ruff: could not evaluate" in body and "(ok)" not in body


def test_main_posts_when_pr_given(tmp_path, monkeypatch):
    gh = FakeGh([])
    monkeypatch.setattr(ratchet, "run_gh", gh)
    rc = ratchet.main(["--tool", "ruff", "--input", os.path.join(FX, "ruff.json"),
                       "--mode", "report", "--diff-file", os.path.join(FX, "pr.diff"), "--strip-prefix", "/repo/",
                       "--repo", "o/r", "--pr", "9"])
    assert rc == 0 and any("POST" in c[0] for c in gh.calls)


def test_main_comment_failure_does_not_fail_report(tmp_path, monkeypatch):
    def boom(args, body=None):
        raise ratchet.GhError("403")

    monkeypatch.setattr(ratchet, "run_gh", boom)
    rc = ratchet.main(["--tool", "ruff", "--input", os.path.join(FX, "ruff.json"),
                       "--mode", "report", "--diff-file", os.path.join(FX, "pr.diff"), "--strip-prefix", "/repo/",
                       "--repo", "o/r", "--pr", "9"])
    assert rc == 0


@pytest.mark.skipif(shutil.which("git") is None, reason="git not in this image")
def test_main_git_diff_default(tmp_path):
    """Without --diff-file it runs git diff -U0 <base>...HEAD in the given root."""
    def git(*a):
        subprocess.run(  # noqa: S603
            ["git", "-c", "user.email=a@b", "-c", "user.name=t", *a],  # noqa: S607
            cwd=tmp_path, check=True, capture_output=True)

    git("init", "-q", "-b", "main")
    (tmp_path / "a.py").write_text("x = 1\n")
    git("add", ".")
    git("commit", "-qm", "base")
    git("checkout", "-qb", "feat")
    (tmp_path / "a.py").write_text("x = 1\ny = 2\n")
    git("commit", "-qam", "edit")
    git("config", "diff.noprefix", "true")  # must not change the paths we parse
    added = ratchet.git_added_lines("main", str(tmp_path))
    assert added == {"a.py": {2}}
