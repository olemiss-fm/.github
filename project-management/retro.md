# Weekly retro - automated, draft-to-Sam first

A scheduled session on the weekly reset day reads the board and the dashboard
and posts one short note: **what moved, what went red, and one change to try.**
A mirror, not a meeting.

## When

Sam's weekly Claude usage resets on Wednesday. Run the retro **Wednesday
evening, after the reset**, so the note covers the week that just closed.

## What it does

1. Read board #19: count cards that reached Done this week, cards still In
   Review or Blocked, and anything that sat untouched.
2. Read the fm-comp-time slice of the engineering inbox / dashboard: PRs merged,
   any Actions run that went red, any PR that stalled waiting on a person.
3. Write three short lines:
   - **Moved:** what got to Done.
   - **Went red:** any failed CI run or stalled PR, named.
   - **One change:** a single concrete thing to try next week.

## The draft-first rule (first two weeks)

For its first two runs it does NOT post. It drafts the note to Sam (a message or
a file), Sam reads it, and only after two weeks of the draft looking right does
it post on its own. This is deliberate: a retro that posts noise trains people
to ignore it.

## How to enable it

It is a recurring cloud agent and costs a little of the weekly token budget each
run, so it is Sam's to switch on. The prompt is the three steps above, with
"draft to Sam, do not post" set for the first two runs. Create it with the
scheduling tool (weekly, Wednesday evening, America/Chicago), or ask a session
to set it up.

Until it is enabled, the same note can be produced on demand: run `plate.sh` and
skim the board's Done and In Review columns for the week.
