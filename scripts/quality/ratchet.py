#!/usr/bin/env python3
# ratchet-version: 3
"""Changed-lines quality ratchet.

Reads the output of one lint/analysis tool (JSON, or the text vulture, mypy and tsc print),
keeps only the findings that sit on lines this PR adds or edits (`git diff -U0 <base>...HEAD`),
and reports them in one sticky PR comment with a section per tool. `--tool coverage` reads a
pytest-cov JSON report and adds a report-only coverage section instead; `--tool uncovered` reads
the same report and lists the changed lines no test ran, also report only.

  report   always exits 0 (a broken tool run still exits 2, and says so in the comment)
  enforce  exits 1 when any finding is on a changed line

Exit codes: 0 ok, 1 enforce failed, 2 the tool output could not be read or parsed.

Canonical and only copy: olemiss-fm/.github scripts/quality/ratchet.py, run by the shared
workflow .github/workflows/quality-gates.yml there. Repos call that workflow; none vendors it.
Python 3 stdlib only.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass

STICKY = "<!-- ratchet-sticky -->"
DEFAULT_LIMIT = 18  # 13 sections x 18 lines x 240 chars, plus headers, stays under the 65536 char comment limit
MAX_LINE = 240


class ToolOutputError(Exception):
    """The tool output is missing, empty or not in the expected format."""


class GhError(Exception):
    """A gh CLI call failed."""


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str
    message: str
    end_line: int = 0


# ---- diff -----------------------------------------------------------------------
_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def parse_diff(text):
    """Return {path: set(added line numbers)} from a `git diff -U0` text."""
    added = {}
    path = None
    in_header = False  # "+++ " is a file header only between "diff --git" and the first "@@"
    for raw in text.splitlines():
        if raw.startswith("diff --git "):
            path, in_header = None, True
        elif in_header and raw.startswith("+++ "):
            p = raw[4:].rstrip("\t").strip('"')
            path = None if p == "/dev/null" else (p[2:] if p.startswith("b/") else p)
        elif raw.startswith("@@"):
            in_header = False
            m = _HUNK.match(raw)
            if path is None or not m:
                continue
            start = int(m.group(1))
            count = 1 if m.group(2) is None else int(m.group(2))
            if count:
                added.setdefault(path, set()).update(range(start, start + count))
    return added


def git_added_lines(base, root="."):
    argv = ["git", "-c", "core.quotepath=off", "diff", "-U0", "--no-color", "--no-ext-diff",
            "--src-prefix=a/", "--dst-prefix=b/", f"{base}...HEAD"]  # fixed prefixes, whatever diff.noprefix says
    out = subprocess.run(  # noqa: S603 - fixed argv, no shell
        argv, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    if out.returncode != 0:
        raise ToolOutputError(f"git diff failed: {out.stderr.strip()}")
    return parse_diff(out.stdout)


# ---- parsers --------------------------------------------------------------------
def _json(text):
    try:
        return json.loads(text)
    except ValueError as exc:
        # the start of the text carries the workflow's reason when a tool did not run cleanly
        raise ToolOutputError(f"not JSON: {exc}: {text.strip()[:200]!r}") from exc


def _list(text, name):
    data = _json(text)
    if not isinstance(data, list):
        raise ToolOutputError(f"{name} output must be a JSON list")
    return data


def parse_ruff(text):
    return [
        Finding(d["filename"], d["location"]["row"], d["code"] or "ruff", d["message"], d["end_location"]["row"])
        for d in _list(text, "ruff")
    ]


def parse_shellcheck(text):
    return [
        Finding(d["file"], d["line"], f"SC{d['code']}", d["message"], d["endLine"])
        for d in _list(text, "shellcheck")
    ]


def parse_hadolint(text):
    return [Finding(d["file"], d["line"], d["code"], d["message"]) for d in _list(text, "hadolint")]


def parse_sqlfluff(text):
    return [
        Finding(f["filepath"], v["start_line_no"], v["code"], v["description"], v["end_line_no"])
        for f in _list(text, "sqlfluff")
        for v in f["violations"]
    ]


def parse_actionlint(text):
    data = _json(text)  # a clean run prints `null`
    if data is None:
        return []
    if not isinstance(data, list):
        raise ToolOutputError("actionlint output must be a JSON list")
    return [Finding(d["filepath"], d["line"], d["kind"], d["message"]) for d in data]


def parse_jscpd(text):
    data = _json(text)
    if not isinstance(data, dict) or "duplicates" not in data:
        raise ToolOutputError("jscpd report needs a 'duplicates' key")
    out = []
    for d in data["duplicates"]:
        a, b = d["firstFile"], d["secondFile"]
        for me, other in ((a, b), (b, a)):
            msg = f"duplicate of {other['name']}:{other['start']}-{other['end']} ({d['lines']} lines)"
            out.append(Finding(me["name"], me["start"], "jscpd", msg, me["end"]))
    return out


# line is "None" for a syntax error with no line, such as a null byte on Python 3.12+
_VULTURE = re.compile(r"^(?P<path>.+?):(?P<line>\d+|None): (?P<msg>.+)$")
# vulture skips a file it cannot read or parse and says so on stderr (the workflow merges it in);
# its read error text is empty, so the last " - " ends the path
_VULTURE_SKIPPED = re.compile(r"^(?:Error: Could not read file (?P<unread>.+) - |(?P<bad>.+?): invalid source code )")
_PY_WARNING = re.compile(r"^\w+Warning: ")
WHOLE_FILE = sys.maxsize  # end_line of a finding that covers every line of its file


def parse_vulture(text):
    out, recognized = [], False
    for raw in text.splitlines():
        m = _VULTURE.match(raw)
        if m and raw.endswith("% confidence)"):
            out.append(Finding(m.group("path"), int(m.group("line")), "vulture", m.group("msg")))
            continue
        s = _VULTURE_SKIPPED.match(raw)
        recognized |= bool(m or s)
        if s:
            path = s.group("unread") or s.group("bad")
        else:  # a syntax error; a Python warning ("SyntaxWarning: ...") has the same shape but skips nothing
            path = m.group("path") if m and not _PY_WARNING.match(m.group("msg")) else None
        if path:
            out.append(Finding(path, 1, "vulture", f"file not checked, vulture could not parse it: {raw}", WHOLE_FILE))
    if text.strip() and not (out or recognized):
        raise ToolOutputError(f"no vulture findings in its output: {text.strip().splitlines()[0][:200]!r}")
    return out


def parse_eslint(text):
    return [
        # a fatal message (a file eslint could not parse) may carry a null line
        Finding(f["filePath"], m.get("line") or 1, m.get("ruleId") or "eslint", m["message"], m.get("endLine") or 0)
        for f in _list(text, "eslint")
        for m in f["messages"]
    ]


_MYPY = re.compile(
    r"^(?P<path>[^:\n]+):(?P<line>\d+)(?::\d+)?: (?:error|warning): (?P<msg>.*?)(?:  \[(?P<code>[\w-]+)\])?$"
)
# a mypy note on its own (exit 0) is a clean run, e.g. [annotation-unchecked] in an untyped function
_MYPY_NOTE = re.compile(r"^[^:\n]+:\d+(?::\d+)?: note: ")
_TSC = re.compile(r"^(?P<path>.+?)\((?P<line>\d+),\d+\): error (?P<code>TS\d+): (?P<msg>.*)$")
_TSC_GLOBAL = re.compile(r"^error TS\d+.*$", re.M)  # a config or global error: tsc checked nothing


def _parse_lines(text, pattern, name):
    """mypy and tsc print one finding per line; output with no finding and a line that is not a note is an error."""
    out, unread = [], False
    for raw in text.splitlines():
        m = pattern.match(raw)
        if m:
            out.append(Finding(m["path"], int(m["line"]), m["code"] or name, m["msg"]))
        elif raw.strip() and not _MYPY_NOTE.match(raw):
            unread = True
    if unread and not out:
        raise ToolOutputError(f"no {name} findings could be read from non-empty output")
    return out


def parse_mypy(text):
    return _parse_lines(text, _MYPY, "mypy")


def parse_tsc(text):
    glob = _TSC_GLOBAL.search(text)
    if glob:
        raise ToolOutputError(f"tsc reported a global error: {glob[0][:200]}")
    return _parse_lines(text, _TSC, "tsc")


def parse_knip(text):
    """knip --reporter json: {"files": [path], "issues": [{"file": path, "<kind>": [{"name", "line"}]}]}."""
    data = _json(text)
    if not isinstance(data, dict):
        raise ToolOutputError("knip output must be a JSON object")
    out = [Finding(p, 1, "knip:files", "unused file") for p in data.get("files", [])]
    for issue in data.get("issues", []):
        for kind, items in issue.items():
            if kind == "file" or not isinstance(items, list):
                continue
            for it in items:
                group = it if isinstance(it, list) else [it]  # duplicates: one group of names per export
                names = ", ".join(d["name"] for d in group)
                msg = f"duplicate export: {names}" if isinstance(it, list) else f"unused {kind}: {names}"
                out.extend(Finding(issue["file"], d.get("line") or 1, f"knip:{kind}", msg) for d in group)
    return out


def coverage_section(text, label, suite, floor_files=8):
    """Report-only coverage summary from a `coverage json` / pytest-cov report."""
    data = _json(text)
    total = data["totals"]
    lines = [
        f"### coverage: {total['percent_covered']:.1f}% of {_clean(label)} lines (report only)",
        f"{total['covered_lines']} of {total['num_statements']} statements run by the {_clean(suite)}.",
    ]
    worst = sorted(
        (f for f in data["files"].items() if f[1]["summary"]["num_statements"] >= 50),
        key=lambda f: f[1]["summary"]["percent_covered"],
    )[:floor_files]
    if worst:
        lines += ["", "Least covered files (50+ statements):"]
        lines += [f"- `{_clean(p)}` {s['summary']['percent_covered']:.0f}%" for p, s in worst]
    return "\n".join(lines)


def parse_uncovered(text, suite="tests"):
    """`coverage json` / pytest-cov report: one finding per run of lines no test ran."""
    data = _json(text)
    if not isinstance(data, dict) or "files" not in data:
        raise ToolOutputError("coverage report needs a 'files' key")
    out = []
    for path, info in data["files"].items():
        run = []
        for n in [*sorted(info["missing_lines"]), None]:
            if run and n != run[-1] + 1:
                out.append(Finding(path, run[0], "uncovered", f"{len(run)} line(s) not run by the {suite}", run[-1]))
                run = []
            if n is not None:
                run.append(n)
    return out


PARSERS = {
    "ruff": parse_ruff,
    "shellcheck": parse_shellcheck,
    "hadolint": parse_hadolint,
    "sqlfluff": parse_sqlfluff,
    "actionlint": parse_actionlint,
    "jscpd": parse_jscpd,
    "vulture": parse_vulture,
    "eslint": parse_eslint,
    "knip": parse_knip,
    "mypy": parse_mypy,
    "tsc": parse_tsc,
    "uncovered": parse_uncovered,
}
# These print nothing on a clean run; the workflow checks their exit codes so a crash is not a pass.
EMPTY_OK = {"vulture", "mypy", "tsc"}
COVERAGE = "coverage"  # not a finding parser: a report-only section, never judged
UNCOVERED = "uncovered"  # judged on changed lines like any tool, but always report only


# ---- filtering ------------------------------------------------------------------
def normalize_path(p, prefixes=(), add=""):
    """Drop the first matching prefix and any "./", then prepend `add` (the folder a tool ran in)."""
    for pre in prefixes:
        if p.startswith(pre):
            p = p[len(pre):]
            break
    while p.startswith("./"):
        p = p[2:]
    return add + p


def normalize(findings, prefixes=(), add=""):
    return [Finding(normalize_path(f.path, prefixes, add), f.line, f.rule, f.message, f.end_line) for f in findings]


def on_changed_lines(findings, added):
    """Keep findings whose line range touches a line the PR added or edited."""
    kept = set()
    for f in findings:
        lines, hi = added.get(f.path, ()), max(f.line, f.end_line)
        if any(f.line <= n <= hi for n in lines):
            kept.add(f)
    return sorted(kept, key=lambda f: (f.path, f.line, f.end_line, f.rule, f.message))


# ---- rendering ------------------------------------------------------------------
def _clean(s):
    """One line of ASCII that cannot ping anyone, break a code span or forge the sticky marker."""
    s = s.replace("<!--", "&lt;!--").replace("\n", " ").replace("|", "/").replace("`", "'").replace("@", "&#64;")
    return s.encode("ascii", "replace").decode("ascii")


def _plural(n):
    return f"{n} finding" + ("" if n == 1 else "s")


def render_section(tool, kept, total, mode, limit=DEFAULT_LIMIT):
    status = "ok" if not kept else ("FAIL" if mode == "enforce" else "report only")
    lines = [
        f"### {_clean(tool)}: {_plural(len(kept))} on changed lines ({status})",
        f"Whole repo: {total} existing. Only lines this PR adds or edits are judged. Mode: {mode}.",
    ]
    if kept:
        lines.append("")
        lines.extend(
            f"- `{_clean(f.path)}:{f.line}` {_clean(f.rule)}: {_clean(f.message)}"[:MAX_LINE] for f in kept[:limit]
        )
        if len(kept) > limit:
            lines.append(f"- ... and {len(kept) - limit} more")
    return "\n".join(lines)


def _markers(tool):
    s = re.sub(r"[^a-z0-9_-]", "-", tool.lower())
    return f"<!-- ratchet-section:{s} -->", f"<!-- /ratchet-section:{s} -->"


def merge_comment(existing, tool, section):
    """Return the sticky body with `tool`'s section replaced or appended."""
    start, end = _markers(tool)
    block = f"{start}\n{section}\n{end}"
    if not existing or STICKY not in existing:
        existing = f"{STICKY}\n## Quality ratchet (changed lines only) - Claude-generated by scripts/quality/ratchet.py"
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if pat.search(existing):
        return pat.sub(lambda _m: block, existing)
    return f"{existing}\n\n{block}"


# ---- GitHub ---------------------------------------------------------------------
def run_gh(args, body=None):
    p = subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["gh", *args], input=body, capture_output=True, text=True, encoding="utf-8", errors="replace",  # noqa: S607
        check=False)
    if p.returncode != 0:
        raise GhError(p.stderr.strip() or f"gh exited {p.returncode}")
    return p.stdout


def post_comment(repo, pr, tool, section, gh=run_gh):
    base = f"repos/{repo}/issues"
    out = gh(["api", "--paginate", f"{base}/{pr}/comments", "--jq", ".[]"])  # one JSON comment per line
    comments = [json.loads(line) for line in out.splitlines() if line.strip()]
    # only our own bot's comment counts, so a pasted marker in a human comment cannot capture the slot
    found = next(
        (c for c in comments if STICKY in (c.get("body") or "") and (c.get("user") or {}).get("type") == "Bot"), None
    )
    body = merge_comment(found["body"] if found else None, tool, section)
    payload = json.dumps({"body": body})
    if found:
        gh(["api", "-X", "PATCH", f"{base}/comments/{found['id']}", "--input", "-"], payload)
    else:
        gh(["api", "-X", "POST", f"{base}/{pr}/comments", "--input", "-"], payload)


# ---- cli ------------------------------------------------------------------------
def _args(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--tool", required=True, choices=sorted([*PARSERS, COVERAGE]),
                    help="tool name; also the output format")
    ap.add_argument("--input", required=True, help="file holding the tool output")
    ap.add_argument("--mode", choices=("report", "enforce"), default=os.environ.get("QUALITY_MODE", "report"))
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--diff-file", help="use this unified-0 diff instead of running git diff")
    ap.add_argument("--strip-prefix", action="append", default=[], help="path prefix to drop (e.g. /repo/)")
    ap.add_argument("--add-prefix", default="", help="path prefix to add after stripping, when the tool ran in a subfolder")
    ap.add_argument("--repo", help="owner/name; with --pr, post the sticky comment")
    ap.add_argument("--pr", type=int)
    ap.add_argument("--coverage-label", default="backend", help="coverage: what the lines are, e.g. backend")
    ap.add_argument("--coverage-suite", default="backend unit tests",
                    help="coverage and uncovered: the suite that ran them")
    a = ap.parse_args(argv)
    if a.mode not in ("report", "enforce"):  # argparse does not check a default (QUALITY_MODE) against choices
        ap.error(f"invalid mode {a.mode!r}: use report or enforce")
    return a


def main(argv=None):
    a = _args(argv)
    try:
        try:
            with open(a.input, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as exc:
            raise ToolOutputError(f"cannot read {a.input}: {exc}") from exc
        if not text.strip() and a.tool not in EMPTY_OK:
            raise ToolOutputError(f"{a.input} is empty: the tool produced no output")
        if a.tool == COVERAGE:
            section, rc = coverage_section(text, a.coverage_label, a.coverage_suite), 0
        else:
            if a.tool == UNCOVERED:
                found, mode = parse_uncovered(text, a.coverage_suite), "report"
            else:
                found, mode = PARSERS[a.tool](text), a.mode
            every = normalize(found, a.strip_prefix, a.add_prefix)
            if a.diff_file:
                with open(a.diff_file, encoding="utf-8", errors="replace") as fh:
                    added = parse_diff(fh.read())
            else:
                added = git_added_lines(a.base)
            kept = on_changed_lines(every, added)
            section = render_section(a.tool, kept, len(every), mode)
            rc = 1 if (mode == "enforce" and kept) else 0
    except (ToolOutputError, KeyError, TypeError, AttributeError, ValueError, OSError) as exc:
        print(f"ratchet: {a.tool}: cannot evaluate: {exc!r}", file=sys.stderr)
        # replace this tool's section too, so the comment never keeps an older run's "ok"
        section, rc = f"### {_clean(a.tool)}: could not evaluate (FAIL)\n{_clean(repr(exc))[:MAX_LINE]}", 2
    print(section)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(section + "\n\n")
    if a.repo and a.pr:
        try:
            post_comment(a.repo, a.pr, a.tool, section, run_gh)
        except (GhError, ValueError, OSError) as exc:
            print(f"ratchet: warning: could not post the PR comment: {exc}", file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
