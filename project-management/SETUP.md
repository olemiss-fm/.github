# Board setup - the few steps the API cannot do

Almost all of the board was set up from the command line (fields, labels,
backfill, and all seven views). The one thing GitHub does not expose to the API
is the board workflows, so that single step is manual - about one minute, one
time. Board: https://github.com/orgs/olemiss-fm/projects/19

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

## 2. The views (already created)

These were created from the API, so there is nothing to do here - they are the
tabs across the top of the board:

| View name | Layout | Filter |
|---|---|---|
| Board | Kanban (grouped by Status) | (all) |
| All | Table | (all) |
| My plate | Table | `assignee:@me -status:Done` |
| Dean's plate | Table | `assignee:dlh515 -status:Done` |
| In Review | Table | `status:"In Review"` |
| Blocked | Table | `status:Blocked` |
| Backlog to groom | Table | `status:Backlog` |

**Board** is the Kanban view - the cards as columns, Backlog through Done. It is
the main way to see the work. "Backlog to groom" is every Backlog card; the human
check is whether its acceptance criteria are machine-runnable before it moves to
Ready (there is no board field for "has AC", on purpose - it is a judgment).

## 3. Nothing else

The command line already did everything else: the six Status columns, the Owner /
Handoff / Size fields, linking the repo, putting the 10 open issues in Backlog,
and all seven views above. The `plate.sh` script in this folder shows each
person's plate from the terminal without opening the board at all.
