# Ole Miss — Facilities Management

We're the technology team behind **UM Facilities Management**. We build and maintain the software that keeps campus space, assets, work orders, and operational data in sync across Workday, Planon, Banner, StarRez, and the rest of the systems Facilities depends on.

🌐 [facilitiesmanagement.olemiss.edu](https://facilitiesmanagement.olemiss.edu) · 🔌 [api.fm.olemiss.edu](https://api.fm.olemiss.edu)

---

## What we work on

- **Integration as a Service** — Bidirectional sync between systems of record (Workday HR, Banner SIS, StarRez Housing) and our operational system (Planon IWMS), so every system sees the same people, spaces, and assets.
- **Read APIs for campus** — A single FastAPI surface (`api.fm.olemiss.edu`) other UM apps call instead of hitting Planon directly.
- **Operational tooling** — A landing page, utility billing automation, uptime monitoring, and infrastructure scanning that keep the lights on.

## Repositories

### Production

| Repo | What it is | Stack |
|---|---|---|
| [`FMAPI`](https://github.com/olemiss-fm/FMAPI) | Integration middleware + read APIs. The system of integration for FM. | Python · FastAPI · Postgres · Docker |
| [`landing_page`](https://github.com/olemiss-fm/landing_page) | Centralized landing page for FM tools and resources. | JavaScript · Docker |
| [`utility_billing`](https://github.com/olemiss-fm/utility_billing) | Utility billing app + automation scripts for Oxford, Delta, Hopewell, Lafayette, MaxxSouth, NEMEPA, and Twin Eagle. | Python · Django |
| [`uptime`](https://github.com/olemiss-fm/uptime) | Uptime monitor for FM services with Slack notifications. | Node.js · Postgres · Docker |
| [`network_scanner`](https://github.com/olemiss-fm/network_scanner) | Network scanning for FM systems — Nmap, SNMP, BACnet, WMI. | Python |

### In progress

| Repo | What it is | Stack |
|---|---|---|
| [`fmapiv2`](https://github.com/olemiss-fm/fmapiv2) | Planned next-generation FMAPI rewrite. | Python · MongoDB · RabbitMQ · GraphQL |

### Legacy / audit pending

| Repo | What it is | Stack |
|---|---|---|
| [`planon_and_arc_working_scripts`](https://github.com/olemiss-fm/planon_and_arc_working_scripts) | Pre-FMAPI Planon + ArcGIS scratch scripts; audit pending before consolidation. | Python |
| [`docs`](https://github.com/olemiss-fm/docs) | Legacy internal documentation site; superseded by per-repo `docs/`. | HTML · Docker |

## Architecture, in one diagram

```
Workday RaaS    Planon REST    Banner    StarRez
      │              │            │         │
      └──────────────┴─────┬──────┴─────────┘
                           ▼
                ┌──────────────────────┐
                │       FMAPI          │  scheduled syncs
                │  pipelines + cache   │  +  read APIs
                └──────────┬───────────┘
                           ▼
                  api.fm.olemiss.edu
                           │
              ┌────────────┴────────────┐
              ▼            ▼            ▼
          campus apps   ArcGIS    other consumers
```

## How we work

- **Issues** are typed (Task / Feature / Bug), labeled, and milestoned by phase. We use GitHub `blockedBy` relationships for dependencies.
- **PRs** target `main`, squash-merge by default. Commit messages explain the *why*, not just the *what*.
- **Migrations** are numbered SQL files — the file is the source of truth.
- **Docs that change with the code** live alongside the code, not in a wiki.
- **Credentials never live in source.** Read from environment variables, gitignored `.env` files, or a secrets manager.

## Get in touch

FM Technology Resources · University of Mississippi · Oxford, MS
