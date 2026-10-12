# Weekly retro - automated, emailed to Sam

A scheduled session on the weekly reset day reads the board and the dashboard
and writes one short note: **what moved, what went red, and one change to try.**
It emails the note to Sam so he sees it in his inbox. A mirror, not a meeting.

## When

Sam's weekly Claude usage resets on Wednesday. The retro runs **Wednesday
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
4. Append the three lines to `~/Obsidian/Reference/Weekly Retro.md` as the
   durable archive, and **email them to Sam** (via `mail.olemiss.edu`, from
   `fmsupport@olemiss.edu`, to `FM_RETRO_EMAIL_TO`, default `sstubbs@olemiss.edu`).

## Sharing with Dean

Sam sees the email first and shares with Dean on his own terms - forward the
email, or ask a session to post it to the board. The board status update (which
Dean sees on the board) is **opt-in and off by default**; set
`FM_RETRO_POST_BOARD=1` to make every run also post it. There is no two-week
draft-only hold: the retro is active from its first run.

## How it is wired

It is a systemd user timer on Sam's agent VM (`ops/automation/retro`), scheduled
weekly for Wednesday evening Central. The implementation and operation (pause a
week, enable the board post, logs) are documented in that folder's `README.md`.
On demand, the same picture comes from `plate.sh` in this folder and the board's
Done and In Review columns.
