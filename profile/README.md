# Ole Miss - Facilities Management

We are the technology team behind **UM Facilities Management**. We build and run the software
that keeps campus space, assets, work orders, utilities, and staff time in sync across Workday,
Planon, Banner, StarRez, and the other systems Facilities depends on.

[facilitiesmanagement.olemiss.edu](https://facilitiesmanagement.olemiss.edu) | [api.fm.olemiss.edu](https://api.fm.olemiss.edu)

---

## What we work on

- **Integration as a service.** Sync between the systems of record (Workday HR, Banner SIS,
  StarRez housing, ArcGIS) and our operational system (Planon), so every system sees the same
  people, spaces, and assets.
- **Read APIs for campus.** One FastAPI surface (`api.fm.olemiss.edu`) that other UM apps call
  instead of reaching into Planon.
- **Business applications.** Comp time for exempt staff, utility billing, the FM landing page,
  and the wall displays and kiosks.
- **Operations.** Runbooks, audits, monitoring, and the shared design system that keep the
  platform healthy and consistent.

## Repositories

Every repository has a README written to the [README standard](https://github.com/olemiss-fm/.github/blob/main/README-STANDARD.md). Statuses
use the standard's four values. Most repositories are private; this list is the map.

### Production

| Repo | What it is |
|---|---|
| [`FMAPI`](https://github.com/olemiss-fm/FMAPI) | Integration-as-a-service middleware connecting Workday, Planon, Banner, and StarRez, with the read APIs on top |
| [`landing_page`](https://github.com/olemiss-fm/landing_page) | The FM landing page: quick access to the apps, tools, and services FM runs |
| [`utility_billing`](https://github.com/olemiss-fm/utility_billing) | Utility billing application and vendor-report automation; being replaced by `fm-utilities-next` |
| [`fm-display-console`](https://github.com/olemiss-fm/fm-display-console) | Admin console for the display control plane: assign dashboards to wall screens and supervise kiosks |
| [`fm-ui-kit`](https://github.com/olemiss-fm/fm-ui-kit) | The FM design system: tokens, components, and agent-readable rules; apps copy it in |
| [`ops`](https://github.com/olemiss-fm/ops) | Org-wide infrastructure, runbooks, audits, and automation |

### In development

| Repo | What it is |
|---|---|
| [`fm-comp-time`](https://github.com/olemiss-fm/fm-comp-time) | Comp Time Manager: weekly timecards and comp time balances for salaried staff. Replaces the Access app; cutover planned for November 2026 |
| [`fm-utilities-next`](https://github.com/olemiss-fm/fm-utilities-next) | Consolidated utility billing platform. Replaces the FM-Utilities Access app and `utility_billing` |
| [`planon`](https://github.com/olemiss-fm/planon) | Source of the Ole Miss Planon AppBuilder app (business rules and endpoints that run inside Planon) |
| [`network_scanner`](https://github.com/olemiss-fm/network_scanner) | Network discovery for building-automation devices; does not run yet |

### Reference

| Repo | What it is |
|---|---|
| [`.github`](https://github.com/olemiss-fm/.github) | This organization's front door: this page, the README standard, ways of working, security policy and shared labels |
| [`fm-corpus`](https://github.com/olemiss-fm/fm-corpus) | Curated knowledge that has no other git home, indexed for the FM knowledge search |
| [`postman`](https://github.com/olemiss-fm/postman) | Version-controlled copy of the olemiss-fm Postman workspace |
| [`CompTimeManager_FE_Master.accdb.src`](https://github.com/olemiss-fm/CompTimeManager_FE_Master.accdb.src) | Exported source of the Comp Time Manager Access front end, kept for reading |
| [`FM-Utilities_fe.accdb.src`](https://github.com/olemiss-fm/FM-Utilities_fe.accdb.src) | Exported source of the FM-Utilities Access front end |
| [`FM-Utilities_be.accdb.src`](https://github.com/olemiss-fm/FM-Utilities_be.accdb.src) | Exported source of the FM-Utilities Access back-end database |

Retired repositories (`uptime`, `fmapiv2`, `docs`, and others) are archived or removed and are
not listed here.

## Architecture, in one diagram

```
 Workday RaaS    Planon REST    Banner    StarRez    ArcGIS
      |              |            |          |          |
      +--------------+-----+------+----------+----------+
                           v
                +------------------------+
                |         FMAPI          |   scheduled syncs
                |   pipelines + cache    |   + read APIs
                +-----------+------------+
                            v
                   api.fm.olemiss.edu
                            |
        +-------------------+-------------------+
        v                   v                   v
   FM business apps    display console     other consumers
 (comp time, utilities, (wall screens)     (campus apps, ArcGIS)
   landing page)
```

## How we work

- **The board is the source of truth.** Work is an issue on a project board, not a chat message.
  The full protocol is in [`WAYS-OF-WORKING.md`](https://github.com/olemiss-fm/.github/blob/main/WAYS-OF-WORKING.md).
- **Pull requests** target `main` and are squash-merged, with conventional commit titles. A pull
  request that changes what a README describes updates the README in the same change.
- **READMEs follow one standard**: [`README-STANDARD.md`](https://github.com/olemiss-fm/.github/blob/main/README-STANDARD.md).
- **Migrations** are numbered SQL files; the file is the source of truth.
- **Docs that change with the code** live next to the code, not in a wiki.
- **Credentials never live in source.** They come from the environment or a secrets manager.

## Get in touch

FM Technology Resources, University of Mississippi, Oxford, MS. To report a security issue, see
[`SECURITY.md`](https://github.com/olemiss-fm/.github/blob/main/SECURITY.md).
