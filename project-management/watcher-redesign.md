# Handoff watcher - redesign to key off board state, not text

How the watcher should detect a handoff once the board is the source of truth,
and how that closes each failure of today's text-matching approach. This is a
design to review before any code changes. It does NOT change the running
automation; see "Rollout" at the end.

## Today (what runs now)

Two pieces in `olemiss-fm/ops` under `automation/`:

- `eng-inbox/` - feeds the inbox page every 2 minutes, read-only. Already
  half-declarative: it decides who a PR waits on from the verdict line
  (`Ready to merge: NO - needs <Name>:`), standing assignments, and review
  requests.
- `tag-responder/respond.py` - the unattended responder. It finds a "tag" by
  regexing `@login` out of the description, comments, and reviews, plus the
  `needs <Name>:` verdict line, plus standing assignment/review-request events.

The @mention + name-parse heuristic is the fragile part.

## The change

Make the **board the primary trigger** and text the fallback:

1. **Primary trigger (declarative).** A GraphQL query over board #19 for items
   where `Assignee = <me>` AND `Handoff = needs: <me>` AND not yet handled.
   This is a state read, not a text guess. Acting on the item clears Handoff to
   `none` and adds the `claude:handled` marker, which makes the trigger
   idempotent: once handled, the query no longer returns it.
2. **Low-latency nudge (unchanged in spirit).** Keep `/notifications` filtered
   to `reason in {review_requested, assign}` so a handoff is noticed within
   seconds rather than at the next board poll. Mark the notification read after
   handling. This only *prompts* a board read; the board state is what decides.
3. **Dedup** on `item node_id + updatedAt` in the existing state file, so the
   same unchanged card is never acted on twice.
4. **On close**, drop `claude:handled`.

The verdict-line and @mention parsing stays only as a compatibility fallback
for threads not yet on the board, and is retired once auto-add is on and every
thread is a board item.

## Each Phase-0 failure, and the fix that closes it

| Failure today | Cause | Closed by |
|---|---|---|
| Miss: "Sam, can you look?" with no @ and no verdict line | detection is text patterns | primary trigger reads the Handoff field; a handoff is a field, not a sentence |
| Miss: legacy title handoffs ("Sam's lane: ...") | titles are never scanned | titles carry no meaning now; Assignee + Handoff do |
| Miss: cross-repository threads skipped | `isCrossRepository -> continue` | board items carry their repo; the query is per-board, not per-thread-heuristic |
| Miss: "needs sam to..." lowercase / no colon | `NEEDS_PERSON_RE` shape | no name parsing on the primary path; Handoff is an enum |
| Double-fire: `@login` in a code span/fence | mentions matched inside code | the primary path does not read prose at all |
| Double-fire: lost dedup state re-fires everything | state file is the only guard | Handoff=none after handling is a second, durable guard in the data itself |
| Misread: `needs CI:` parsed as a person "CI" | capitalized-word name parse | Handoff is one of four fixed values; "CI" cannot be a value |
| Misread: name identity across @handle / "Sam" / NAMES | three spellings, by convention | Owner/Handoff are enums with one spelling each; the login map is one table |

## Rollout (do not hot-swap)

This is live automation on Sam's VM. The change lands as a reviewed PR to
`olemiss-fm/ops` that Sam merges and deploys, not an in-place edit of the
running timers. Order:

1. Turn on board auto-add (so every thread is an item) and let it settle a day.
2. Add the board-state query as an ADDITIONAL trigger beside the existing ones,
   behind a flag, and run it read-only (log what it would do) for a few days.
3. Compare its decisions against the current detector on the same threads.
4. When they agree, make the board query primary and demote the text parse to
   the compatibility fallback.

No step removes the working detector until the board query has matched it on
real threads.
