# Bitwarden conventions for the Ole Miss FM org vault

_Drafted 2026-05-08 by Sam. This document is the standard for how every
secret used by FM infrastructure is recorded in our shared Bitwarden
vault (`Ole Miss - Facilities Management`). Companion to
[INVENTORY.md](INVENTORY.md), which is the running list of what must be
recorded._

## Why

We currently can't recover from a host loss without guesswork. If
`pvedev110` (or `130.74.51.11`, `130.74.51.220`, etc.) died tomorrow,
the engineer rebuilding it would not be able to populate every `.env`
file from the vault — items are named inconsistently, some are missing,
and the link between a Bitwarden item and the env var or `.env` line it
fills is implicit. This document fixes that by setting one rule for
every part of an entry: name, collection, fields.

The standard is **DR-recoverability:** any FM engineer with vault
access can rebuild any host or repo from the working `.env`s plus
Bitwarden alone, with no tribal knowledge.

## Item naming

Every item is renamed to `[scope]/[env]/[purpose]`.

- **`scope`** — what the credential belongs to. Use one of:
  - `vm/<host>` for host-level credentials (SSH, console, hypervisor admin)
  - `<repo>` for an application that lives in an `olemiss-fm/<repo>` GitHub repo (e.g. `FMAPI`, `utility_billing`, `landing_page`, `uptime`, `network_scanner`, `docs`, `fmapiv2`)
  - `keycloak`, `planon`, `workday`, `banner`, `box`, `slack`, `arcgis` for external/vendor systems FM uses across multiple apps
  - `personal/<user>` for individual GitHub PATs, MFA backups, etc. — kept in the org vault for handoff but clearly tagged
- **`env`** — `prod`, `dev`, `acc`, or `n/a` (for things like SSH passwords that aren't tier-scoped). Omit the `env` segment entirely if `n/a` would have been the value.
- **`purpose`** — short, lowercase-with-dashes label for what the credential does. Examples:
  - `ssh-root`, `ssh-fmapi` (host SSH credentials)
  - `pg-apiadmin`, `pg-uptime` (Postgres user passwords)
  - `oidc-client-secret`, `django-secret-key` (web-app secrets)
  - `api-key`, `webhook-failures`, `sftp-oxford`

### Examples of renames

| Today's name | Proposed name |
|---|---|
| `docs vm` | `vm/docs/ssh-root` |
| `Dev Server via ProxMox` | `vm/pvedev110/proxmox-console` |
| `fmapiv1 vm 110` | `vm/pvedev110/ssh-fmapi` |
| `keycloak db` | `keycloak/pg-keycloak` |
| `keycloak itself` | `keycloak/admin-console` |
| `postgres VM DB superuser` | `vm/postgres/pg-superuser` |
| `oxford bills sftp creds` | `utility_billing/prod/sftp-oxford` |
| `openssl wildcard challenge pw` | `vm/<host>/ssl-wildcard-challenge` |
| `GH dev key` and `github dev key` | merge into `personal/<owner>/github-pat` |

### Don't

- Don't include the credential value (or any part of it) in the name.
- Don't use spaces — use lowercase-with-dashes.
- Don't put the env tier in the purpose segment (`pg-apiadmin-prod` is wrong; use `FMAPI/prod/pg-apiadmin`).
- Don't create new top-level item types ("Card", "Identity", "SSH Key") for secrets that fit inside a Login. Logins with custom fields are the standard. SSH Key items are fine for actual SSH keypairs.

## Collections (shared across the org)

Five collections, one axis: where the credential is consumed.

| Collection | Contains |
|---|---|
| `infra` | VMs, hypervisor, NAS, network gear, SSL/PKI, DNS, anything host-level. Recovery for the hosts themselves |
| `prod` | Every secret a production-running application reads (FMAPI prod env, utility_billing Django prod, uptime prod, landing_page backend prod, etc.) |
| `dev` | Same as `prod` but for dev/acc tier |
| `vendor` | Planon/Workday/Banner/SAP/StarRez tenant API keys, vendor SFTP credentials (Oxford, Delta, Lafayette, MaxxSouth, Hopewell, TwinEagle), Box, ArcGIS, Slack |
| `personal` | Individual GitHub PATs, MFA backups, employee-bound secrets that don't survive a person leaving — kept here so the next person can revoke and reissue |

Folders (the vertical list under "Folders" in the Bitwarden UI) are
**per-user, not shared**. Don't rely on them for anything that another
engineer needs to find. Use collections only.

## Required custom fields

Every Bitwarden Login item gets four custom fields filled in. Without
these, the entry passes its DR test by accident; with them, anyone can
rebuild a host without asking questions.

| Field name | Type | Example value | What it's for |
|---|---|---|---|
| `env_var_name` | Text | `OIDC_RP_CLIENT_SECRET` | Exact env var the value lands in. Empty string if the credential isn't read from an env var (e.g. an SSH password used interactively) |
| `repo` | Text | `olemiss-fm/utility_billing` | GitHub repo that consumes it. `n/a` for infra-only secrets like a hypervisor admin password |
| `server_path` | Text | `pvedev110:/home/utilities/files/utilities/.env` | Fully qualified path to the `.env` file the value belongs in. `n/a` if not env-var driven |
| `rotated_on` | Text (ISO date) | `2026-05-08` | Last rotation date. Lets a quarterly audit script find stale credentials |

### Other fields

- **URI** — set when the item is for a URL-based login (Bitwarden, Keycloak admin, Box, Slack, etc.). Leave blank for SSH/DB/env-var-only credentials.
- **Notes** — free-form. Use it to record what fails if this credential leaks, plus any quirks (rotation procedure, regen script path, where the credential is also embedded if anywhere).

## Lifecycle

### When you add a new credential

1. Create the credential first (rotate or generate the value).
2. Create a Bitwarden Login item using the naming convention.
3. Fill in the four required custom fields.
4. Move it into the correct collection.
5. Update [INVENTORY.md](INVENTORY.md) to add a row for the new credential.
6. If a repo's `.env.example` doesn't already list the matching env var, add it in the same PR that introduces the consumer code.

### When you rotate a credential

1. Update the value in Bitwarden first.
2. Update `rotated_on` to today's ISO date.
3. Push the new value to the consumer (`.env` on the relevant host, plus any backup copies).
4. Verify the consumer comes back up.
5. Revoke the old value at the source (Keycloak admin, Slack admin, Planon admin, etc.).

### When a credential is retired

Don't delete the item immediately — it may still be in a backup `.env`
or a coworker's local notes. Move the item into a `legacy/` collection
(create one alongside the others), keep it for 30 days, then purge.
Note the date of retirement and the reason in the notes field.

## Audit cadence

Every quarter, paired with the patch audit:

1. Re-grep every `.env.example` and `os.environ[...]` / `process.env.X` / `os.Getenv(...)` site across all olemiss-fm active repos to rebuild the "must be recoverable" list.
2. Compare against [INVENTORY.md](INVENTORY.md). Anything new is a finding.
3. Filter Bitwarden by `rotated_on < (today - 1 year)`. Anything that's a year stale is a finding (rotate or document why it's exempt).
4. Add findings to the next CLEANUP_PLAN cycle.

## What lives outside Bitwarden

A short list of things that intentionally do not get a Bitwarden item:

- The contents of an `.env` file checked into git as `.env.example` —
  these are the *names* of what Bitwarden holds, not the values.
- Public certificates and CA bundles. Public keys are not secrets.
- Per-repo `requirements.txt` / `package.json` lockfiles. These are
  inputs to the build, not credentials.
- Anything stored in GitHub Actions secrets (`secrets.JENKINS_USER`,
  `secrets.JENKINS_TOKEN`, etc.) — those are managed in the GitHub UI,
  not duplicated in Bitwarden, but the Bitwarden item for the
  underlying account should reference the GitHub secret name in its
  notes field so the link survives a forgotten Action.
