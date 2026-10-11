#!/usr/bin/env bash
# plate.sh - what is on your plate on the fm-comp-time board.
#
# Usage:
#   ./plate.sh            # for you (maps your gh login to Sam or Dean)
#   ./plate.sh Dean       # for a named person
#
# Read-only. Uses the gh CLI you are already logged in with. No tokens.
set -euo pipefail

OWNER_ORG="olemiss-fm"
PROJECT_NUMBER="19"
WIP_CAP="3"

who="${1:-}"
if [ -z "$who" ]; then
  login="$(gh api user --jq .login 2>/dev/null || true)"
  case "$login" in
    sstubbs-olemiss) who="Sam" ;;
    dlh515)          who="Dean" ;;
    *)               who="Sam" ;;  # default; pass a name to override
  esac
fi
needs_me="needs: $(printf '%s' "$who" | tr '[:upper:]' '[:lower:]')"

items="$(gh project item-list "$PROJECT_NUMBER" --owner "$OWNER_ORG" --format json --limit 200)"

section () { # $1 = heading, $2 = jq filter over .items[]
  local rows
  rows="$(printf '%s' "$items" | jq -r --arg who "$who" --arg needs "$needs_me" \
    ".items[] | select($2) | \"  #\(.content.number)  [\(.status // \"-\")]  \(.content.title)\"")"
  printf '\n%s\n' "$1"
  if [ -n "$rows" ]; then printf '%s\n' "$rows"; else printf '  (nothing)\n'; fi
}

active='(.status=="Ready" or .status=="In Progress" or .status=="In Review" or .status=="Blocked")'

printf '== %s on the fm-comp-time board ==\n' "$who"

section "On your plate (you own it, in flight):" \
  "(.owner==\$who) and $active"

section "Waiting on your review / decision:" \
  "(.status==\"In Review\" or .handoff==\$needs) and (.owner==\$who or .handoff==\$needs)"

section "Blocked (yours):" \
  "(.owner==\$who) and (.status==\"Blocked\")"

section "Backlog (check these have machine-checkable AC before starting):" \
  "(.status==\"Backlog\")"

# WIP: In Review owned by you, plus anything whose Handoff names you.
wip="$(printf '%s' "$items" | jq -r --arg who "$who" --arg needs "$needs_me" \
  '[.items[] | select((.status=="In Review" and .owner==$who) or .handoff==$needs)] | length')"
printf '\nWIP waiting on %s: %s of %s' "$who" "$wip" "$WIP_CAP"
if [ "$wip" -ge "$WIP_CAP" ]; then
  printf '  <- CAP FULL: start no new work for %s until one clears.\n' "$who"
else
  printf '  (room for %s more)\n' "$((WIP_CAP - wip))"
fi
