# README standard - olemiss-fm

Every repository in the org has a `README.md` at its root, written to this standard. The
README is the front door: a person who has never seen the repo should learn what it is, who
uses it, whether it is live, and where to go next, in under a minute. Engineering detail lives
in `docs/`; the README points at it.

The model is [`fm-comp-time`](https://github.com/olemiss-fm/fm-comp-time#readme).

## Who reads it

Write for the least technical reader first. Dean, an FM supervisor, or an auditor opens a
README to find out what a system does and who owns it. An engineer (or a Claude session)
reads on for how it is built and run. Put the plain-language sections first, the engineering
sections after.

## Sections, in this order

Use the sections that apply, in this order, with these exact headings. Leave out a section
that has nothing to say (a library has no Deploy section); do not add an empty one.

| # | Heading | What goes in it |
|---|---|---|
| 1 | `# <repo-name>` | The repository name exactly as GitHub shows it. |
| 2 | Badges | Only for workflows that exist on `main`: deploy first, then secret scan, then others. None if there are none. |
| 3 | Summary (no heading) | One bold sentence: what it is and who it is for. Then two to four sentences of plain context: what it replaces or connects, why it exists. |
| 4 | Facts block (no heading) | One line each, bold label: **Status:**, **Production:** (URL, if any), **Owner:** (the person who decides what it does), **Board:** (project board, if any). |
| 5 | `## What it does` | What a user or the business gets, in plain words. Bullets that start with a bold noun. No code. |
| 6 | `## How it is built` | Stack, data sources, where it runs, and a small ASCII diagram if one helps. |
| 7 | `## Repository layout` | A table of top-level directories (`Path` / `What is in it`), or a short tree. Only paths that exist. |
| 8 | `## Development` | How to run it and test it. Docker, databases and test stacks run on fm-devdock, never the engineering VM. Commands in fenced `bash` blocks. |
| 9 | `## Deploy` | How a change reaches production: the workflow, the image registry, the stack file. Releases, if the repo cuts them. |
| 10 | `## Documentation` | A table (`Read` / `For`) of the docs worth opening, most important first. |
| 11 | Org links | The standard footer below, verbatim. |

Repository-specific sections (a security boundary, a secrets policy, a sync schedule) go
between `## Deploy` and `## Documentation`, with a sentence-case heading.

### Status values

Use exactly one of:

- **Production** - in daily use; changes deploy from `main`.
- **In development** - being built; not yet relied on. Say what it will replace and the target date if there is one.
- **Reference** - not deployed; data, docs, or source kept for reading (a corpus, a mirror, exported Access source).
- **Legacy** - superseded; say by what, and whether it is still read or written.

## Style

- **ASCII only.** No em or en dashes, curly quotes, arrows, bullet glyphs, emoji, or box-drawing
  characters (ASCII diagrams use `+`, `-`, `|`, `v`, `>`). Check with
  `LC_ALL=C grep -nP '[^\x00-\x7F]' README.md`; it must print nothing.
- **Sentence-case headings.** `## How it is built`, not `## How It Is Built`.
- **Plain, active words.** Name who does what. Absolute dates (`2026-11-02`), never "next week".
- **Code font** for paths, commands, identifiers, hostnames, and URLs used as values; bold for
  UI names and for labels in the facts block. Relative links for files in the repo.
- **True today.** Every path, command, URL, workflow, and number must match `main`. A README
  that describes a plan says so ("planned", "not built yet").
- **No credentials** and no credential values, ever. Name the secret, not its value.
- **Short.** Aim for one to two screens. Move anything longer into `docs/` and link it.
- **Wrap at about 100 columns** or not at all, consistently within a file.

## Footer

Every README ends with this block, verbatim:

```markdown
---

## Across the org

- [Org overview and repository list](https://github.com/olemiss-fm)
- [All open issues](https://github.com/issues?q=is%3Aissue+is%3Aopen+org%3Aolemiss-fm+sort%3Aupdated)
- [All open pull requests](https://github.com/pulls?q=is%3Apr+is%3Aopen+org%3Aolemiss-fm+sort%3Aupdated)
- [README standard](https://github.com/olemiss-fm/.github/blob/main/README-STANDARD.md)
```

## Keeping it true

A pull request that changes what the README describes (a directory, a command, a URL, a
workflow, the status) updates the README in the same pull request. A reviewer treats a stale
README line as a finding on that PR.
