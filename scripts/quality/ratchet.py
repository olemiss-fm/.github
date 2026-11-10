#!/usr/bin/env python3
# ratchet-version: 1
"""Changed-lines quality ratchet.

Reads the output of one lint/analysis tool (JSON or vulture text), keeps only the
findings that sit on lines this PR adds or edits (`git diff -U0 <base>...HEAD`), and
reports them in one sticky PR comment with a section per tool.

  report   always exits 0 (a broken tool run still exits 2)
  enforce  exits 1 when any finding is on a changed line

Exit codes: 0 ok, 1 enforce failed, 2 the tool output could not be read or parsed.

Canonical copy: olemiss-fm/ops scripts/quality/ratchet.py. Other repos vendor a copy
and keep the `ratchet-version` header; do not edit a vendored copy in place.
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
DEFAULT_LIMIT = 25  # 8 sections x 25 lines x 240 chars stays under the 65536 char comment limit
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
        raise ToolOutputError(f"not JSON: {exc}") from exc


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


_VULTURE = re.compile(r"^(?P<path>.+?):(?P<line>\d+): (?P<msg>.+)$")


def parse_vulture(text):
    out = []
    for raw in text.splitlines():
        m = _VULTURE.match(raw)
        if m:
            out.append(Finding(m.group("path"), int(m.group("line")), "vulture", m.group("msg")))
    if text.strip() and not out:
        raise ToolOutputError("no vulture findings could be read from non-empty output")
    return out


PARSERS = {
    "ruff": parse_ruff,
    "shellcheck": parse_shellcheck,
    "hadolint": parse_hadolint,
    "sqlfluff": parse_sqlfluff,
    "actionlint": parse_actionlint,
    "jscpd": parse_jscpd,
    "vulture": parse_vulture,
}
# Vulture prints nothing on a clean run; the workflow checks its exit code so a crash is not a pass.
EMPTY_OK = {"vulture"}


# ---- filtering ------------------------------------------------------------------
def normalize_path(p, prefixes=()):
    for pre in prefixes:
        if p.startswith(pre):
            p = p[len(pre):]
            break
    while p.startswith("./"):
        p = p[2:]
    return p


def normalize(findings, prefixes=()):
    return [Finding(normalize_path(f.path, prefixes), f.line, f.rule, f.message, f.end_line) for f in findings]


def on_changed_lines(findings, added):
    """Keep findings whose line range touches a line the PR added or edited."""
    kept = set()
    for f in findings:
        lines = added.get(f.path)
        if lines and any(n in lines for n in range(f.line, max(f.line, f.end_line) + 1)):
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
    ap.add_argument("--tool", required=True, choices=sorted(PARSERS), help="tool name; also the output format")
    ap.add_argument("--input", required=True, help="file holding the tool output")
    ap.add_argument("--mode", choices=("report", "enforce"), default=os.environ.get("QUALITY_MODE", "report"))
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--diff-file", help="use this unified-0 diff instead of running git diff")
    ap.add_argument("--strip-prefix", action="append", default=[], help="path prefix to drop (e.g. /repo/)")
    ap.add_argument("--repo", help="owner/name; with --pr, post the sticky comment")
    ap.add_argument("--pr", type=int)
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
        every = normalize(PARSERS[a.tool](text), a.strip_prefix)
        if a.diff_file:
            with open(a.diff_file, encoding="utf-8", errors="replace") as fh:
                added = parse_diff(fh.read())
        else:
            added = git_added_lines(a.base)
    except (ToolOutputError, KeyError, TypeError, AttributeError, ValueError, OSError) as exc:
        print(f"ratchet: {a.tool}: cannot evaluate: {exc!r}", file=sys.stderr)
        return 2

    kept = on_changed_lines(every, added)
    section = render_section(a.tool, kept, len(every), a.mode)
    print(section)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(section + "\n\n")
    if a.repo and a.pr:
        try:
            post_comment(a.repo, a.pr, a.tool, section, run_gh)
        except (GhError, ValueError, OSError) as exc:
            print(f"ratchet: warning: could not post the PR comment: {exc}", file=sys.stderr)
    return 1 if (a.mode == "enforce" and kept) else 0


if __name__ == "__main__":
    sys.exit(main())
