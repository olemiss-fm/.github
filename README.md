# .github

**The olemiss-fm organization profile and shared GitHub configuration, for everyone who works in
the org's repositories.**

GitHub reads this repository for the organization front page and for defaults that apply to every
repo. It also holds the rules the org follows: how READMEs are written, how work is driven, and
how to report a security issue.

**Status:** Production. The profile is live on the org page and the standards are in daily use.
**Owner:** Sam Stubbs.
**Board:** none. The shared rules were piloted on the [fm-comp-time board](https://github.com/orgs/olemiss-fm/projects/19).

## What it does

- **Org front page.** `profile/README.md` is what visitors see at
  [github.com/olemiss-fm](https://github.com/olemiss-fm): who we are, the repository map, and how
  we work.
- **README standard.** `README-STANDARD.md` is the shape every repository README follows.
- **Ways of working.** `WAYS-OF-WORKING.md` is how Sam and Dean drive work through Claude
  sessions; `CLAUDE.shared.md` is the session rules each repo imports.
- **Security policy.** `SECURITY.md` says how to report a vulnerability in any org repo.
- **Shared labels.** `labels.yml` is the label set, authored org-wide and so far applied to
  fm-comp-time only.

## Repository layout

| Path | What is in it |
|---|---|
| `profile/README.md` | The org front page |
| `README-STANDARD.md` | The README standard |
| `WAYS-OF-WORKING.md` | The work protocol: board, owners, handoffs |
| `CLAUDE.shared.md` | Cross-repo session rules, imported by each repo's `CLAUDE.md` |
| `SECURITY.md` | The security policy for every org repo |
| `labels.yml` | Shared label taxonomy |
| `project-management/` | Board setup, the `plate.sh` helper, the weekly retro, the handoff watcher design |
| `CODEOWNERS` | Maintainer review is required for every change |
| `.github/dependabot.yml` | Dependency updates for this repo |

## Development

There is nothing to build or run. Change a file on a branch and open a pull request; a maintainer
reviews it. This repository is **public**, so write nothing in it that is not safe for the
internet: no hostnames of internal machines, no addresses, no credentials.

When the repository list changes (a repo is added, archived, or changes status), update the table
in `profile/README.md` in the same pull request:

```bash
gh repo list olemiss-fm --no-archived --json name,description
```

## Deploy

Merging to `main` publishes the change: GitHub renders `profile/README.md` on the org page
immediately. There are no workflows and no releases.

## Documentation

| Read | For |
|---|---|
| [`README-STANDARD.md`](README-STANDARD.md) | Writing or checking a repository README |
| [`WAYS-OF-WORKING.md`](WAYS-OF-WORKING.md) | How work moves from request to done |
| [`project-management/README.md`](project-management/README.md) | Running the board |
| [`SECURITY.md`](SECURITY.md) | Reporting a vulnerability |

---

## Across the org

- [Org overview and repository list](https://github.com/olemiss-fm)
- [All open issues](https://github.com/issues?q=is%3Aissue+is%3Aopen+org%3Aolemiss-fm+sort%3Aupdated)
- [All open pull requests](https://github.com/pulls?q=is%3Apr+is%3Aopen+org%3Aolemiss-fm+sort%3Aupdated)
- [README standard](https://github.com/olemiss-fm/.github/blob/main/README-STANDARD.md)
