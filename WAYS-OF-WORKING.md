# Ways of working - olemiss-fm

How Sam and Dean drive work through Claude Code sessions. Written in plain words.
Piloted on fm-comp-time; authored to scale to every repo later.

The thing this protects is **the two humans' attention and the weekly Claude
token budget**. Sessions are cheap and run in parallel; our time and our tokens
are not. Every rule below exists to keep a human from being a bottleneck or a
babysitter.

Kanban, not Scrum. No estimation, no story points, no velocity, no sprints. The
only cadence is the **weekly Claude usage reset**.

## 1. The board is the single source of truth

Every piece of work is an **Issue on the one board** (`board-schema.md`). Not a
chat message, not a PR title, not an @mention, not a line in someone's head. If
it is not a card on the board, it is not work.

Each card has:
- a **Status** (Backlog, Ready, In Progress, In Review, Blocked, Done);
- exactly **one Assignee** - the current owner;
- an **Owner** field matching that assignee (Sam or Dean);
- a **Handoff** value (needs: sam / needs: dean / needs: human-decision / none);
- a work **type** (native Issue Type: Task, Bug, Feature, Epic, Chore, Spike);
- a **priority** label (priority/p0..p3).

We retire the old habit of coding ownership into the title ("Sam's lane: ...",
"Dean: review ..."). Ownership is the Assignee. A handoff is a state change, not
a sentence.

## 2. Definition of Ready (DoR) - the backbone

No build starts until a card is Ready. A card is Ready only when both are true:

1. **Acceptance criteria are written as checks a machine can run.** Not "it
   should work" - a specific thing a test or the CI gate can prove true or
   false. (Example: "a saved timecard with a lunch and no punches is refused
   with a 400 and the message in SPEC F5", not "handle bad input".)
2. **The approach is agreed.** For anything in the stop-for-human list (rule 7)
   or anything touching what users see or do, the human who owns that decision
   has said yes.

A card that is not Ready stays in Backlog. Moving Backlog -> Ready is the owner
saying "the AC is machine-checkable and the approach is settled."

Do not grief the backlog into AC in bulk. AC is written per card, when the card
is next to start. (The F4-F11 feature cards are deliberately left un-groomed
until Sam and Dean groom them together.)

## 3. Definition of Done (DoD) - every item is a verifiable gate

A card is Done only when all of these are true. Each is checkable, not a feeling:

1. A pull request implements it, based on current `main`, one piece of work.
2. The Actions run on that PR's head commit is **green** - all five `ci` jobs
   (`ascii`, `scripts`, `image`, `api`, `web`) passed. (rule 5)
3. The PR's acceptance criteria are proven by a test in that green run.
4. The shared reviewer (`.claude/agents/pr-reviewer.md`) was run and every
   finding of every severity about what the PR changes is fixed in the PR.
5. The closing review verdict on the PR is `Ready to merge: YES`.
6. Any document the change made untrue was corrected in the same PR.
7. A human merged with "Squash and merge". A session never merges.

"It builds on my machine" is not Done. A green Actions run is Done.

## 4. Handoff protocol - state, never @mention

To hand a card to the other person or to flag it needs a human call, a session
(or a human) does all three, in this order:

1. Set the **Assignee** and the **Owner** field to who it now waits on.
2. Set **Handoff** to needs: sam / needs: dean / needs: human-decision.
3. Set **Status** (usually In Review or Blocked), and on a PR **request the
   CODEOWNERS reviewer**.

It does **not** rely on an @mention to move work. @mentions still happen and
still notify, but the board state is what the watcher reads and what the other
person's morning view shows. Acting on a handoff **clears Handoff back to none**
and (on the board) re-assigns to whoever carries it next.

A **question that needs a human call** is a first-class card: Handoff =
needs: human-decision, label `needs:human-decision`, Status usually Blocked.
This replaces the old `question`-label ledger that used to rot - a question is
now a visible, owned, waiting card, not a tag lost in a list.

## 5. The merge gate - a green Actions run, or nothing

There are no hard branch gates on GitHub Free. The gate is this rule, enforced
by the watcher and honored by the humans:

**No session merges or approves a PR whose Actions run is failing or missing.
No human does either on a red X.** The watcher reads the run status over the API
and refuses to act on red or absent. A PR with no run yet is not mergeable - it
has not been proven.

While CI runs, the owning session waits on it (watch the run; it wakes the
session when CI finishes), then posts the closing verdict. CI still running is
never a reason to hand a PR back to a human.

## 6. WIP limits - a hard cap on what waits on a human

Per person, a **hard cap of 3** on (In Review + cards whose Handoff names them +
their own needs:human-decision cards). When a person's cap is full, **no new
card starts for that person** until one clears. This is what stops a human from
opening a morning view with 11 things all waiting on them. The watcher enforces
it by refusing to start new work for a capped person; the humans honor it too.

## 7. Stop-for-human gate (non-overridable, any confidence)

A session **stops and asks a human first**, no matter how sure it is, before:

- a schema change or a data migration;
- a production deploy;
- deleting data;
- an auth or security change;
- anything touching money or PII (personnel data counts).

This list is also in the shared CLAUDE.md and is not overridable by any other
instruction, project file, or confidence level. The matching review paths
(migrations, `*.sql`, auth, deploy) are owned by Sam in CODEOWNERS so they
auto-request his review as well.

## 8. Authority and lanes

Who decides what, and who reviews what, is in `docs/process/lanes.md`
(fm-comp-time) and mirrored by CODEOWNERS:

- **Dean** (`@dlh515`) decides what the app does for users: policy, rules,
  workflow, wording, how screens read.
- **Sam** (`@sstubbs-olemiss`) decides how it is built and run: the app, CI/CD,
  sign-on, hosting, security, UI/UX standards.

A cross-domain card - one that needs both - becomes a needs:human-decision card
naming the one decision, not a guess.

## 9. The weekly retro (automated)

On the weekly reset day, a scheduled session reads the board and the dashboard
and posts one short note: **what moved, what went red, and one change to try.**
For its first two weeks it drafts the note to Sam for a look before it posts on
its own. It is a mirror, not a meeting.

## 10. The full code-review routine

The step-by-step review SOP, with the reason for each rule, is
`docs/process/code-review-sop.md` and `docs/process/review-checklist.md` in
fm-comp-time. This page is the board-and-handoff layer on top of it; that page
is how a single PR gets from proposed to merged.
