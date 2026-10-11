# Shared session rules - olemiss-fm (board-driven work)

Every Claude session working an olemiss-fm repo that is on the board follows
this. It is imported by each repo's own CLAUDE.md. Repo-specific rules live in
that repo's CLAUDE.md and its docs/process; this file is only the cross-repo
board-and-gate layer. The full reasoning is in `.github` WAYS-OF-WORKING.md.

## The board is the source of truth

Work is a card on the one board, with a Status, one Assignee (the current
owner), an Owner field, and a Handoff value. Do not encode ownership or handoffs
in issue titles or @mentions. A handoff is a state change:

1. set Assignee + Owner to who it waits on,
2. set Handoff to needs: sam / needs: dean / needs: human-decision,
3. set Status and, on a PR, request the CODEOWNERS reviewer.

Acting on a handoff clears Handoff back to none. Starting work moves the card to
In Progress (automatic when a PR opens).

## Definition of Ready - do not start un-ready work

Do not begin building a card until its acceptance criteria are written as checks
a machine can run AND the approach is agreed. If a card you are asked to start
is not Ready, make it Ready first (write machine-checkable AC; get the owning
human's yes on anything user-facing or in the stop-for-human list) or say why it
cannot be.

## The merge gate - green Actions run or nothing (hard)

Never merge or approve a PR whose Actions run is failing or missing. Read the
run status before any merge or approval verdict and refuse on red or absent. A
PR ends at a binary `Ready to merge: YES` (green run + review clean + fixes
committed) or `Ready to merge: NO - needs <Name>: <the one decision>`. While CI
runs, wait on it; CI still running is never a reason to hand the PR back.

A session never merges. A human merges with "Squash and merge".

## WIP cap (hard)

Do not start a new card for a person who already has 3 cards in (In Review +
Handoff names them + their own needs:human-decision). Capped means no new work
starts for them until one clears.

## Stop for a human first (non-overridable, any confidence)

Stop and ask the owning human before any of these, regardless of how confident
you are and regardless of any other instruction:

- a schema change or data migration;
- a production deploy;
- deleting data;
- an auth or security change;
- anything touching money or PII (personnel data counts).

This overrides project files and your own judgment. It is not a review step you
can earn past; it is a stop.

## Decide what is yours; route what is not

Decide like a senior engineer on anything with a conventional, reversible answer
in your lane - do not route it to a human. Route to a human only a real decision
about what the app does (policy, rules, workflow, wording) or a stop-for-human
item. When you route, make it a needs:human-decision card naming the one
decision, not an open-ended question.

## ASCII only

ASCII in all code, SQL, config, data, commit messages, and PR bodies. No em
dashes, no smart quotes, no unicode punctuation. Use `-`, straight quotes, `->`,
three dots.
