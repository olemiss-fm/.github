# Board setup - the few steps the API cannot do

Most of the board was set up from the command line (fields, labels, backfill).
Three things GitHub only lets you set in the web UI. They are one-time and take
about two minutes. Board: https://github.com/orgs/olemiss-fm/projects/19

## 1. Turn on the board workflows

Open the board, click the "..." menu (top right) -> Workflows. Turn on:

- **Auto-add to project** -> repository `olemiss-fm/fm-comp-time`, items: Issues
  and Pull requests. (So every new issue/PR lands on the board with no manual
  add.)
- **Item added to project** -> set Status = Backlog.
- **Pull request merged** -> set Status = Done.
- **Item closed** -> set Status = Done.

If the UI offers "pull request opened -> In Progress" and "review requested ->
In Review", turn those on too. If it does not (the available triggers change),
sessions set those two statuses by hand as part of the handoff protocol, so
nothing breaks - the board still moves.

## 2. Create the five views

Click the "+" beside the view tabs and add each (New view -> Table or Board,
then set the filter). The filter syntax is the same bar the board uses.

| View name | Layout | Filter |
|---|---|---|
| My plate | Table | `assignee:@me -status:Done -status:Backlog` |
| Dean's plate | Table | `assignee:dlh515 -status:Done -status:Backlog` |
| In Review | Board | `status:"In Review"` |
| Blocked | Table | `status:Blocked` |
| Backlog needing AC | Table | `status:Backlog` |

"Backlog needing AC" is every Backlog card; the human check is whether its
acceptance criteria are written as machine-runnable checks before it moves to
Ready (there is no board field for "has AC", on purpose - it is a judgment).

## 3. Nothing else

The command line already did: the six Status columns, the Owner / Handoff / Size
fields, linking the repo, and putting the 10 open issues in Backlog. The
`plate.sh` script in this folder shows each person's plate from the terminal
without opening the board at all.
