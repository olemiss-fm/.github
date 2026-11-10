# Quality gates

Goal: agent-written code gets what a senior engineer's review would give it, and the PR
shows the proof. Tracking issues: olemiss-fm/ops#751, olemiss-fm/ops#769 (one shared workflow).

## How the gate works

Workflow: `.github/workflows/quality-gates.yml` in this repo (`on: workflow_call`). Every repo
calls it from a thin caller pinned to a commit SHA of this repo, and its job runs in the calling
repo, on that repo's runners (`fm-ci` by default, so 0 GitHub minutes). Each tool runs in a
digest-pinned container. `scripts/quality/ratchet.py`, fetched from this repo at the same SHA
as the workflow, then keeps only the
findings that sit on lines the PR adds or edits (`git diff -U0 origin/<base branch>...HEAD`). Old code
the PR does not touch never fails the PR. That is the "ratchet": quality can only go up.

All tools share ONE sticky PR comment, headed `Quality ratchet (changed lines only)`, with one
section per tool. It is updated in place on every push, never added to.

### Reading a section

```
### ruff: 3 findings on changed lines (report only)
Whole repo: 6197 existing. Only lines this PR adds or edits are judged. Mode: report.
- `automation/x/y.py:42` S608: Possible SQL injection via string-based query construction
```

- `3 findings on changed lines`: these are yours. Fix each one in the PR.
- `Whole repo: N existing`: the backlog. Not your concern, shown only so the trend is visible.
  A repo that lints only the PR's SQL files (`sqlfluff-changed-only`) sees
  `In the SQL files this PR changes: N existing` instead.
- Status `ok`, `report only` or `FAIL`. `FAIL` appears only in `enforce` mode.
- The lines under the heading are `file:line RULE: message`. Open the file at that line.

### Modes

One input, `mode:` in the repo's caller. Any value other than `report` or `enforce` is an error (exit 2).

| Mode | Findings on changed lines | Check result |
|---|---|---|
| `report` (now) | comment | green |
| `enforce` | comment | red |

Flip a repo to `enforce` with a one-line PR to its caller after the report-only week. If a tool cannot produce
readable output (crash, empty file, wrong format) the step fails with exit 2 in either mode,
and its section in the comment says "could not evaluate": a gate that silently stops checking
is worse than a red one. Vulture prints nothing when it is clean, so its step also checks the
exit code (0 clean, 3 dead code found, 1 a file it could not read or parse; anything else
fails). Vulture skips a file it cannot read or parse, so the ratchet reports that file as
"file not checked" on any line a PR changes in it.
Each section lists at most 18 findings, each line cut at 240 characters, so the one comment
stays under GitHub's size limit.

### Fixing a finding you disagree with

- Real false positive for one line: `# noqa: <RULE>` (ruff; vulture also honours `# noqa`),
  `# shellcheck disable=SCxxxx`, or `# hadolint ignore=DLxxxx`, with a short reason on the same line.
- A rule that is wrong for the whole repo: change `pyproject.toml` in a PR that says why.

## The gates

| Gate | Checks | Typical fix |
|---|---|---|
| ruff | Python: bugs (B, F), security (S, e.g. S608 SQL built from strings), simplification (SIM, RET, PIE, C4), performance (PERF), modern syntax (UP), complexity (C90, McCabe 10), style (E, line length 120). `assert` is allowed in tests. | Follow the message; `ruff` docs for the rule code: https://docs.astral.sh/ruff/rules/ |
| vulture | Dead code at 80%+ confidence: unused imports, arguments, unreachable code. | Delete it. If it is used dynamically, add `# noqa` on that line. |
| jscpd | Copy-paste: 15+ lines and 150+ tokens duplicated (python, bash, yaml, sql). Reported on both copies; the message names the other location. | Extract a function or shared file, or delete one copy. |
| shellcheck | Shell bugs: unquoted variables, bad tests, unused variables (`*.sh`). | Quote it; follow https://www.shellcheck.net/wiki/SCxxxx |
| hadolint | Dockerfile practice: unpinned base image or packages, missing cleanup. | Pin the version; https://github.com/hadolint/hadolint#rules |
| actionlint | GitHub Actions workflow errors: bad expressions, unknown inputs, script injection, shell issues in `run:`. Self-hosted labels are declared in `.github/actionlint.yaml`. | Follow the message. |
| sqlfluff | SQL style in `migrations/*.sql` and `*/migrations/*.sql` (Postgres dialect). | Reformat as the message says. |

Containers (all pinned by digest in the workflow `env:`): ruff 0.14.3, python 3.13-slim with
vulture 2.14 (a caller may pass another `python-image`), node 22-slim with jscpd 4.0.5,
shellcheck v0.10.0, hadolint v2.12.0, actionlint 1.7.7, sqlfluff 3.4.2. To bump one, change
the digest and the comment here in one PR, then move each caller's pin.

Tool config stays in each repo: ruff reads its `pyproject.toml` `[tool.ruff]`, actionlint its
`.github/actionlint.yaml` (self-hosted labels) when it has one.

## Calling it from a repo

`.github/workflows/quality-gates.yml` in the repo is a thin caller:

```yaml
name: Quality gates
on:
  pull_request:
permissions:
  contents: read
  pull-requests: write
jobs:
  gates:
    uses: olemiss-fm/.github/.github/workflows/quality-gates.yml@<full commit sha> # <date or note>
    with:
      tools: ruff vulture jscpd shellcheck hadolint actionlint sqlfluff
      mode: report
```

The org requires actions pinned to a full commit SHA; pin the workflow the same way. The
caller sets no `concurrency` (the shared job has its own group; the same group in the caller
would deadlock).

| Input | Default | Meaning |
|---|---|---|
| `tools` | all seven | space-separated gates to run |
| `mode` | `report` | `report` or `enforce` |
| `runs-on` | `["self-hosted", "fm-ci"]` | runner labels, JSON. A public repo passes `["ubuntu-latest"]`: the fm-ci group serves private repos only |
| `python-image` | python 3.13-slim digest | image for vulture and the extra gates |
| `jscpd-paths` | `.` | space-separated paths jscpd scans |
| `jscpd-formats` | `python,bash,yaml,sql` | jscpd `--format` |
| `jscpd-ignore` | `**/node_modules/**,**/secrets/**,**/.git/**` | jscpd `--ignore`; empty passes none |
| `sqlfluff-paths` | `migrations/*.sql */migrations/*.sql` | git pathspecs sqlfluff lints (a git `*` also matches `/`, so these reach nested folders) |
| `sqlfluff-changed-only` | `false` | `true` lints only the files in `sqlfluff-paths` the PR adds or changes (a repo with hundreds of migrations); the count line then says so |
| `vulture-exclude` | `secrets/*,*/secrets/*` | vulture `--exclude` globs, comma-separated; empty passes none |
| `timeout-minutes` | `25` | job timeout |
| `extra-gates` | none | a bash script in the repo for its own gates, see below |

### A repo's own gates (eslint, tsc, knip, mypy, coverage)

Commands that only fit one repo (its eslint config and globs, its tsc project, its test suite)
live in a bash script in that repo, named by `extra-gates:`. It runs last, in the same job,
under `bash --noprofile --norc -uo pipefail`, with:

- `$RATCHET`: the shared ratchet with `--repo`, `--pr`, `--base` and `--strip-prefix /repo/` set,
  so `"$RATCHET" --tool eslint --input "$QUALITY_DIR/eslint.json"` adds a section to the sticky comment;
- `$RATCHET_PY` and `PYTHONPATH`: the ratchet file and its folder, for a repo's own adapter
  script that does `import ratchet` (for a tool format the ratchet does not read);
- `$DR` / `$DRT`: the `docker run` flags every tool shares (repo read-only at `/repo`, the
  runner's user; `$DRT` adds a writable `/tmp`);
- `$PYTHON_IMAGE`, `$NODE_IMAGE`, `$QUALITY_DIR` (a scratch directory).

The ratchet reads `eslint` (JSON), `knip` (JSON), `mypy` and `tsc` (text) besides the seven
shared tools. Two more read a pytest-cov / `coverage json` report and are always report only,
whatever the mode:

- `--tool coverage --coverage-label api --coverage-suite "api tests"`: total coverage and the
  least covered files;
- `--tool uncovered --coverage-suite "api tests"`: one finding per run of lines no test ran,
  judged on changed lines like any tool, so the section lists the lines this PR adds that no
  test runs.

A tool that ran in a subfolder reports paths relative to it; `--add-prefix web/` puts the
folder back (after `--strip-prefix`), so the paths meet the diff.

Rules for the script:

- Run every tool even when one fails. The step fails with the worst exit code of the script
  and of every `$RATCHET` call it made, so a crash early in the script cannot end green.
- A clean mypy prints nothing (with `--no-error-summary`) or only notes and its
  `Success: no issues found` line, and a clean tsc prints nothing, so the ratchet reads that
  output as a pass. Check their exit codes (mypy 0 or 1, tsc 0, 1 or 2) and, on any other,
  write the reason into the output file instead, as the shared steps do; the ratchet then
  reports the section as FAIL.

### Where each repo's own add-on goes

| Repo | Add-on it kept beside the vendored ratchet | In the shared setup |
|---|---|---|
| FMAPI | `ratchet_ext.py`: eslint, tsc, mypy, knip, coverage | shared parsers; mypy, eslint, tsc and knip (`--add-prefix sync_ui/`) in its `extra-gates` script; the mock-suite coverage as `--tool uncovered` in its own job, which fetches the ratchet; `sqlfluff-changed-only: true`, `vulture-exclude: '*/secrets/*,*/archive/*,*/.claude/*,*/node_modules/*'`, `timeout-minutes: 60` |
| fm-comp-time | `extra_gates.py`: mypy, tsc, eslint, knip, coverage | shared parsers; `--add-prefix web/` and `api/`; coverage as `--tool coverage` plus `--tool uncovered` in its separate coverage job; `vulture-exclude: 'secrets/*,*/secrets/*,web/*'` |
| utility_billing | `changed_lines.py`: mypy and `eslint -f unix` text, job summary only | shared `mypy` parser; eslint switches to `-f json` for the shared `eslint` parser; `vulture-exclude: 'secrets/*,*/secrets/*,*/staticfiles/*,*/static/pdfjs/*'` |
| landing_page, fm-utilities-next | `extra_tools.py`: eslint, knip, mypy, tsc, coverage | the same parsers, now in the shared ratchet |
| fm-display-console | whole-repo eslint, stylelint, knip and tsc counts in the job summary | its own second job in the caller file, beside the `uses:` job; not a ratchet section |

A caller file is an ordinary workflow: next to the `gates` job that `uses:` this workflow it may
keep jobs of its own (counts, coverage on a heavier runner). Those jobs run the repo's own
steps; only the `gates` job is shared.

### A separate job that needs the ratchet

A job outside the shared one (for example coverage on a heavier runner) fetches the ratchet at
the same SHA as the caller's `uses:` pin, from this public repo, with no token:

```
curl -fsSL -o "$RUNNER_TEMP/ratchet.py" \
  https://raw.githubusercontent.com/olemiss-fm/.github/<the same sha>/scripts/quality/ratchet.py
```

Keep the two SHAs in the caller identical; the monthly quality-metrics run reports a caller
whose pins disagree.

## Running it by hand

On fm-devdock (the engineering VMs have no docker): run the tool the way the workflow does,
write its output to a file, then, from the repo:

```
python3 path/to/ratchet.py --tool ruff --input ruff.json --strip-prefix /repo/ --mode report
```

Without `--repo` and `--pr` it only prints; nothing is posted. `--diff-file` replaces the
`git diff`. Interface: `--tool NAME --input FILE [--mode report|enforce] [--base REF]
[--diff-file F] [--strip-prefix P] [--add-prefix P] [--repo OWNER/NAME --pr N]
[--coverage-label L] [--coverage-suite S]`; the tool name is also the output format (`coverage`
and `uncovered` read a pytest-cov JSON report). Exit 0 ok, 1 enforce failed, 2 unreadable output. `GITHUB_STEP_SUMMARY` is also
written when set. Tests: `scripts/quality/tests` (pytest; fixtures are real tool output),
run on every PR here by `.github/workflows/gates.yml`.

## Changing the gates

1. PR here. `gates.yml` runs this repo's gates through the workflow and ratchet the PR carries,
   plus the ratchet tests.
2. Merge, then move each caller's `@<sha>` to the merge commit, one PR per repo. A repo on an
   older SHA keeps working on the older gates until it moves; the monthly quality-metrics run
   (ops `automation/quality-metrics`) reports which repos are behind.

## Trust and limits

- A caller runs on `pull_request` in its own repo, and a PR there runs the PR's own caller. So
  a PR can change its own `tools`, `mode` or pin, as it could edit a vendored workflow before;
  the review sees that change in the diff. What it cannot do is change the shared steps or the
  ratchet at a given SHA. Its `extra-gates` script and tool config are its own, and run on the
  fm-ci host, the same exposure every fm-ci workflow has. The calling repos are private and the
  pool takes no fork PRs.
- This repo is public, so the ratchet is fetched from `raw.githubusercontent.com` at the pinned
  SHA with no token.
- The tool containers are pinned by digest. `pip` (pytest, vulture) and `npx` (jscpd) packages
  are pinned by version, not by hash, and are fetched when the step runs.
- The sticky comment is the first comment by a bot that holds the marker. A person pasting the
  marker cannot take its place.
