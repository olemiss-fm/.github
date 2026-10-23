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
case "$who" in
  Sam)  who_login="sstubbs-olemiss" ;;
  Dean) who_login="dlh515" ;;
  *)    who_login="" ;;
esac
needs_lbl="needs:$(printf '%s' "$who" | tr '[:upper:]' '[:lower:]')"

LIMIT=2000
items="$(gh project item-list "$PROJECT_NUMBER" --owner "$OWNER_ORG" --format json --limit "$LIMIT")"
# The list is in board order, newest cards last, so a cut-off read would drop them and undercount.
if [ "$(printf '%s' "$items" | jq '.items | length')" -ge "$LIMIT" ]; then
  echo "plate.sh: the board has $LIMIT or more items; raise LIMIT" >&2; exit 1
fi

# What waits on a person (WAYS-OF-WORKING section 6): a card labelled needs:<them>, their
# own needs:human-decision card (by Owner, or by Assignee when Owner is empty, as on PRs),
# or an issue they own in In Review. A PR its own session
# will merge (no needs:* label) waits on no person.
waits='(.status != "Done") and (((.labels // []) | index($lbl))
  or (((.owner==$who) or (.owner==null and ((.assignees // []) | index($login))))
      and ((.labels // []) | index("needs:human-decision")))
  or (.status=="In Review" and .owner==$who and .content.type=="Issue"))'

section () { # $1 = heading, $2 = jq filter over .items[]
  local rows
  rows="$(printf '%s' "$items" | jq -r --arg who "$who" --arg lbl "$needs_lbl" --arg login "$who_login" \
    ".items[] | select($2) | \"  #\(.content.number)  [\(.status // \"-\")]  \(.content.title)\"")"
  printf '\n%s\n' "$1"
  if [ -n "$rows" ]; then printf '%s\n' "$rows"; else printf '  (nothing)\n'; fi
}

active='(.status=="Ready" or .status=="In Progress" or .status=="In Review" or .status=="Blocked")'

printf '== %s on the fm-comp-time board ==\n' "$who"

section "On your plate (you own it, in flight):" \
  "(.owner==\$who) and $active"

section "Waiting on you (counts toward your cap):" "$waits"

section "Blocked (yours):" \
  "(.owner==\$who) and (.status==\"Blocked\")"

section "Backlog (check these have machine-checkable AC before starting):" \
  "(.status==\"Backlog\")"

wip="$(printf '%s' "$items" | jq -r --arg who "$who" --arg lbl "$needs_lbl" --arg login "$who_login" \
  "[.items[] | select($waits)] | length")"
printf '\nWIP waiting on %s: %s of %s' "$who" "$wip" "$WIP_CAP"
if [ "$wip" -ge "$WIP_CAP" ]; then
  printf '  <- CAP FULL: start nothing new for %s until one clears, unless %s asks for it.\n' "$who" "$who"
else
  printf '  (room for %s more)\n' "$((WIP_CAP - wip))"
fi
