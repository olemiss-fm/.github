# Project management - olemiss-fm

How Sam and Dean drive work through Claude sessions. Full protocol:
[`../WAYS-OF-WORKING.md`](../WAYS-OF-WORKING.md). Session rules each repo imports:
[`../CLAUDE.shared.md`](../CLAUDE.shared.md).

## How we drive the board

- **The board is the source of truth.** Every work item is an Issue on one
  Projects v2 board (fm-comp-time: org project #19), with a Status, exactly one
  Assignee (the current owner), an Owner field, and a `needs:*` label when it
  waits on a person.
- **Done = a green Actions run.** No session and no human merges or approves a
  PR whose Actions run is red or missing. Before go-live the reviewing session
  squash-merges its own PR (WAYS-OF-WORKING section 5).
- **A per-person cap of 3** on what waits on each human (`needs:<person>`
  labels, their own `needs:human-decision` cards, and issues they own in In
  Review). A PR its own session will merge does not count. Full means no new
  work starts for that person until one clears.

## How a handoff works

A handoff is a state change, never an @mention:

1. set the **Assignee** and **Owner** field to who it now waits on,
2. add the label `needs:sam` / `needs:dean` / `needs:human-decision`,
3. set **Status** (In Review or Blocked) and, on a PR, request the CODEOWNERS
   reviewer.

Acting on a handoff removes the label. The other person sees it on
their plate automatically - no message is sent.

## In this folder

- [`plate.sh`](plate.sh) - run it in a terminal to see what is on your plate
  (owned, waiting on your review, blocked, backlog to groom) and your WIP count.
- [`SETUP.md`](SETUP.md) - the few one-time board steps the API cannot do
  (turn on auto-add and the status workflows; create the five views).
- [`watcher-redesign.md`](watcher-redesign.md) - how the handoff watcher moves
  from regexing @mentions to reading the board's Handoff field, with each old
  failure mapped to its fix. A design to review before any code change.
- [`retro.md`](retro.md) - the weekly automated retro (draft-to-Sam first two
  weeks).

## For Dean

Dean has a one-page guide in the fm-comp-time repo:
`docs/process/for-dean-the-board.md`. One morning view, what each column means,
how to make a decision, how to accept finished work, and the stop-for-human
list in plain words.

## Scaling to the next repo

The pilot is fm-comp-time only. The next candidate, `fm-utilities-next`, starts
differently: it already carries ~148 open issues, almost all F-numbered
epics/spikes created in one burst on 2026-06-25 and left unlabeled. That is a
ceremony backlog, not real queued work, so the first move there is a
**triage-and-cull** (close or merge the stale cards, keep the few that are real,
then apply this labels/board/CODEOWNERS set to what remains) - NOT a backfill of
all 148 onto a board. Do that triage with Sam and Dean before syncing any
config to it.
