# Quality gates

Tracking issue: olemiss-fm/ops#751. Full design and the other tools: ops
`docs/quality-gates.md`.

This repo holds org config, docs and one shell script (`project-management/plate.sh`). It
has no Python, TypeScript, CSS, SQL or Dockerfiles, so only two gates apply:

| Gate | Checks | Scope |
|---|---|---|
| shellcheck | Shell bugs: unquoted variables, bad tests | `*.sh` |
| actionlint | Workflow errors, script injection | `.github/workflows/*.yml`, `*.yaml` |

Workflow: `.github/workflows/quality-gates.yml`. It runs on a GitHub-hosted runner, not
`fm-ci`: this repo is public (free minutes) and the org runner group does not serve public
repos. Each tool runs in a digest-pinned container. `scripts/quality/ratchet.py` (vendored
unchanged from ops, see its `ratchet-version` header; do not edit it here) keeps only
findings on lines the PR adds or edits and posts one sticky PR comment.

`QUALITY_MODE` at the top of the workflow is the switch: `report` (now) comments and
passes, `enforce` fails the check on a changed-line finding. It flips to `enforce` after
the report-only week.

False positive on one line: `# shellcheck disable=SCxxxx` with a reason.
Bump a tool: change its digest and version comment in the workflow, in one PR.
