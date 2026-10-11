# Project management - olemiss-fm

How we drive work on GitHub. Full detail in `../WAYS-OF-WORKING.md`.

- **The board is the source of truth.** Every work item is an Issue on the one
  Projects v2 board, with a Status, one Assignee (current owner), and a Handoff.
- **A handoff is a state change**, not an @mention: set Assignee + Owner +
  Handoff + Status, and request the CODEOWNERS reviewer on a PR.
- **Done = a green Actions run.** No session or human merges on a red or missing
  run.

> Phase 4 fills this out: the gh status script, the board views, the retro job,
> and one paragraph on scaling to fm-utilities-next (which starts with a
> triage-and-cull of its ~148-issue ceremony backlog, not a backfill).
