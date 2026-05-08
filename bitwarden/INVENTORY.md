# Bitwarden inventory — what must be recoverable

_Drafted 2026-05-08 by Sam, after a sweep of every active `olemiss-fm`
repo. Companion to [CONVENTIONS.md](CONVENTIONS.md), which sets the
naming + structure standard. This file is the running list of what
belongs in Bitwarden._

The DR test: if every FM host died tomorrow, an FM engineer with vault
access should be able to rebuild every `.env` file from this list. A
row whose **Bitwarden item** column is empty is a gap.

Tom: this is the worksheet for the cleanup. As you rotate a
credential, fill in the proposed Bitwarden item name, do the rename in
the vault per [CONVENTIONS.md](CONVENTIONS.md), populate the four
required custom fields, and tick off the row. When the table has zero
empty cells, the cleanup is done.

## Status legend

- **`existing`** — the credential is already in Bitwarden under some name; just needs the rename + custom fields per CONVENTIONS.md
- **`new`** — the credential is in source code but NOT yet in Bitwarden; needs to be added during rotation
- **`rotate-then-add`** — the credential is exposed in source/git history, listed in [FMAPI/CLEANUP_PLAN.md](https://github.com/olemiss-fm/FMAPI/blob/main/CLEANUP_PLAN.md) Phase 1 for rotation; Bitwarden item gets created with the new value during the same rotation

## Infrastructure (collection: `infra`)

Hosts and host-level access. Recovery for the hosts themselves.

| Proposed Bitwarden item | Status | What it is | Source |
|---|---|---|---|
| `vm/pvedev110/proxmox-console` | existing | ProxMox web console for the dev hypervisor | already in vault |
| `vm/pvedev110/ssh-fmapi` | rotate-then-add | SSH `fmapi@130.74.51.3` — FMAPI prod host | was in deleted vmc repo; on FMAPI/CLEANUP_PLAN.md Phase 1 |
| `vm/docs/ssh-root` | rotate-then-add | SSH `docs@130.74.51.11` — docs vm | was in deleted vmc repo; on rotation list |
| `vm/130-74-51-220/ssh-root` | rotate-then-add | SSH `user@130.74.51.220` | was in deleted vmc repo; on rotation list |
| `vm/samba/ssh-root` | rotate-then-add | SSH `samba@130.74.51.200` — Samba host | was in deleted vmc repo; on rotation list |
| `vm/130-74-51-24/ssh-root` | rotate-then-add | SSH on `130.74.51.24` | was in deleted vmc repo; on rotation list |
| `vm/postgres/pg-superuser` | existing | Postgres VM superuser | already in vault as "postgres VM DB superuser" |
| `vm/postgres/pg-apiadmin` | rotate-then-add | Postgres `apiadmin@130.74.51.3` (`Ppf22`) | hardcoded in many retired files; on rotation list |
| `vm/<host>/ssl-wildcard-challenge` | existing | OpenSSL wildcard challenge password | already in vault as "openssl wildcard challenge pw" — confirm which host |
| `vm/fm-nas/admin` | existing | FM NAS admin (Synology) | already in vault as "FM NAS" |
| `keycloak/admin-console` | existing | Keycloak admin console | already in vault as "keycloak itself" |
| `keycloak/pg-keycloak` | existing | Postgres role for Keycloak | already in vault as "keycloak db" |
| `vm/fmapiv1-110/ssh-fmapi` | existing | SSH for the legacy fmapiv1 host | already in vault as "fmapiv1 vm 110" |

## FMAPI (collection: `prod` and `dev`)

Driven by [`FMAPI/.env.example`](https://github.com/olemiss-fm/FMAPI/blob/main/.env.example). One row per env var. ACC tier shown as `dev`; PROD tier as `prod`.

| Proposed Bitwarden item | Env var | Status | Notes |
|---|---|---|---|
| `FMAPI/prod/pg-apiadmin` | `PGPASSWORD` | rotate-then-add | Same Postgres user as `vm/postgres/pg-apiadmin` — link via notes |
| `FMAPI/dev/pg-apiadmin` | `PGPASSWORD` | new | If FMAPI dev runs against a different DB user |
| `FMAPI/dev/planon-api-key` | `ACC_PLANON_API_KEY` | rotate-then-add | FM_API_ACC user-group key in acc-planon |
| `FMAPI/prod/planon-api-key` | `PROD_PLANON_API_KEY` | rotate-then-add | FM_API_PROD user-group key in prod-planon |
| `FMAPI/wip/planon-test-api-key` | `TEST_PLANON_API_KEY` | rotate-then-add | UM_SAP_INTEGRATION key in test-planon, used only by `troubleshooting/arc/wip/` scripts |
| `FMAPI/dev/workday-raas` | `ACC_WORKDAY_USER` + `ACC_WORKDAY_PASSWORD` | existing | Likely already in vault under some name; verify |
| `FMAPI/prod/slack-webhook-failures` | `FMAPI_SLACK_WEBHOOK_URL_FAILURES` | rotate-then-add | Webhook in `#fmapi-failures` (or wherever it points) |
| `vendor/arcgis/oauth-client` | `ARCGIS_CLIENT_ID` + `ARCGIS_CLIENT_SECRET` | rotate-then-add | OAuth app on `um-facilities.maps.arcgis.com` |
| `vendor/arcgis/api-key` | `ARCGIS_API_KEY` | rotate-then-add | Long-lived API key (separate from the OAuth app) |
| `vendor/planon/webdav` | `PLANON_WEBDAV_USER` + `PLANON_WEBDAV_PASSWORD` | rotate-then-add | Service account on `umiss-acc.planoncloud.com` |

## utility_billing (collection: `prod`, `dev`, `vendor`)

Houses the Django billing app, the vendor parser/refactor scripts, and
the daily cron scripts. Most credentials are still hardcoded — these
all need rotation + Bitwarden + scrubbing in source. Tracked in
[FMAPI/CLEANUP_PLAN.md](https://github.com/olemiss-fm/FMAPI/blob/main/CLEANUP_PLAN.md)
Phase 1 (the OIDC client secret) but the rest are NEW findings from
this sweep.

**Note**: actual credential values are deliberately omitted from the
table — read them from the source location given in column 2. This
file lives in git, so embedding the values would defeat the cleanup.

| Proposed Bitwarden item | Source location | Status | Notes |
|---|---|---|---|
| `utility_billing/prod/oidc-client-secret` | `utilities/utilities/settings.py:25` (`OIDC_RP_CLIENT_SECRET`) | rotate-then-add | Keycloak `utilities-django` client. **Highest priority** — live prod credential |
| `utility_billing/prod/django-secret-key` | `utilities/utilities/settings.py:11` (`SECRET_KEY`) | rotate-then-add | Django session/CSRF/cookie signer. Currently uses the `django-insecure-` prefix indicating a generated default — must be rotated regardless |
| `utility_billing/prod/utilities-app-password` | `utilities/app/views.py:1486,1564,1691` | rotate-then-add | Same value repeated three times in `views.py`; figure out what login it's for as part of rotation |
| `utility_billing/prod/sftp-oxford` | `automation_scripts/oxford_v3/csv_and_bills.py:44` (`sftp_password`) | rotate-then-add | Oxford bills SFTP |
| `vendor/fm-nas/automation` | `automation_scripts/refactors/{twineagle,delta,lafayette,maxxsouth,hopewell}/*_send_*.py` AND `automation_scripts/refactors/download_archive_upload_signed_reports.py` AND `automation_scripts/download_archive_upload_signed_reports.py` (`nas_password` / `NAS_PASSWORD`) | rotate-then-add | Single NAS password reused across all vendor refactors — rotate once, update every consumer |
| `utility_billing/prod/cron-password` | `automation_scripts/cron/{current_data_porting,dean_monthly_email}.py` (`password`) | rotate-then-add | Used by both daily-cron scripts; figure out which system it authenticates against during rotation |

## landing_page (collection: `prod`)

| Proposed Bitwarden item | Source location | Status | Notes |
|---|---|---|---|
| `landing_page/prod/admin-username` + `landing_page/prod/admin-password` | `admin-auth.js` (`ADMIN_USERNAME`, `ADMIN_PASSWORD` constants) | rotate-then-add | **Critical: this auth is in the delivered frontend JS, so the password is visible to anyone who loads the admin page.** Move this auth server-side OR replace with Keycloak before recording in Bitwarden |
| `landing_page/prod/pg-landing` | `backend/main.py:103` (`password=`) | rotate-then-add | Postgres password — appears identical to the value used in uptime. Confirm whether it's one shared DB user or coincidence |

## uptime (collection: `prod`)

| Proposed Bitwarden item | Source location | Status | Notes |
|---|---|---|---|
| `uptime/prod/pg-uptime` | `server.js:28` | rotate-then-add | Same Postgres value as landing_page; confirm whether it's one shared DB user or coincidence |
| `uptime/prod/admin-password` | `server.js:250` | rotate-then-add | `admin` login for the uptime web UI |
| `uptime/prod/session-secret` | `server.js:128` | rotate-then-add | express-session cookie secret. Currently set to the same value as the admin password — must be split into two distinct values during rotation |
| `uptime/prod/slack-webhook` | `slackNotifier.js:4` (`SLACK_WEBHOOK_URL`) | rotate-then-add | Rotate by deleting and re-creating the webhook in Slack |

## network_scanner (collection: `prod`)

| Proposed Bitwarden item | Source location | Status | Notes |
|---|---|---|---|
| `network_scanner/prod/jwt-secret` | `api/authentication.py:18` | new | `JWT_SECRET` env var; `os.environ.get(...)` falls back to a random `secrets.token_hex(32)` if unset (which means restarts invalidate sessions). Rotate so a stable JWT_SECRET is in Bitwarden + on the host |
| `network_scanner/prod/snmp-community` | `config.example.json` | new | `snmp_community: "public"` is the default; confirm the actual prod value lives in `.env` or the deployed `config.json` |
| `network_scanner/prod/fm-domain-account` | `config.example.json` (`fm_username: fmsupport@webid.olemiss.edu`) | new | The password isn't in source — find it on the host's deployed config and record |
| `network_scanner/prod/pg-fm-network` | `config.example.json` (`db_config`) | new | Postgres `postgres@localhost:5432/fm_network`; password lives on the deployed host |

## fmapiv2 (collection: `dev`)

Future-state. Currently development-only. Worth recording the credentials it'll need so DR planning anticipates the cutover.

| Proposed Bitwarden item | Env var | Status | Notes |
|---|---|---|---|
| `fmapiv2/dev/mongo-uri` | `MONGO_URI` | new | `mongodb://mongo:27017` is the in-cluster value (no auth) — record the URI itself, plus any auth string when prod is provisioned |
| `fmapiv2/dev/planon-test-api-key` | (currently hardcoded in `main.py:18`) | rotate-then-add | UM_SAP_INTEGRATION JWT, same value as FMAPI's `TEST_PLANON_API_KEY`; the two repos can share the Bitwarden item via notes |

## docs (collection: `prod`)

Tom's legacy custom docs site. Sweep didn't surface hardcoded
credentials, but the host (`docs@130.74.51.11`) does need an SSH entry —
that's covered under `infra` above.

## fmapiv1 / planon_and_arc / vmc / planon / misc_scripts / archived

Already retired (repos deleted, content archived to Samba). Anything
those scripts referenced is captured in the `rotate-then-add` rows
above. After rotation, no further Bitwarden work is needed for these.

## Vendor / external (collection: `vendor`)

For vendors that span multiple FM apps, one Bitwarden item per service
account, referenced by every consumer.

| Proposed Bitwarden item | Status | Notes |
|---|---|---|
| `vendor/box/admin-account` | existing | If FM has a Box admin account distinct from individual user accounts |
| `vendor/box/oxford-bills-sftp` | existing | `oxford bills sftp creds` rename target |
| `vendor/sap/sap-integration-account` | existing | Whatever account `automation_scripts/cron/current_data_porting.py` uses to talk to SAP |
| `vendor/maxxsouth/sftp` | new | If MaxxSouth requires SFTP credentials separate from `vendor/fm-nas/automation` |
| `vendor/slack/api-token` | existing | Tom's `slackNotifier` would-be admin tokens, beyond just webhooks |
| `vendor/arcgis/oauth-client` | rotate-then-add | (also listed under FMAPI above — ONE item, multiple consumers) |
| `vendor/arcgis/api-key` | rotate-then-add | (same — ONE item) |
| `vendor/planon/webdav` | rotate-then-add | (same — ONE item) |

## Personal (collection: `personal`)

These exist in the vault for handoff continuity, not because they're
shared. When the named person leaves, the next maintainer revokes and
reissues; the Bitwarden item is the marker that the reissue has to
happen.

| Proposed Bitwarden item | Status | Notes |
|---|---|---|
| `personal/thomasedgemon/github-pat` | existing | merge of `GH dev key` + `github dev key` (same person, same purpose) |
| `personal/sstubbs/github-pat` | new | If applicable |

## How to work this list

1. Start with the **rotate-then-add** rows in `utility_billing` (highest density of live exposures), then move outward to `uptime` and `landing_page`.
2. For each row: rotate the credential at its source, create the Bitwarden item per [CONVENTIONS.md](CONVENTIONS.md), populate all four required custom fields, push the new value to the host's `.env`, verify the consumer comes back up, then strike the row.
3. **existing** rows can be done in any order — they're just renames + custom-field backfills, no rotation pressure.
4. **new** rows are credentials we know the system uses but aren't in source — find them on the live host's config, rotate if practical, record.
5. As rows get done, strike them through (`~~vm/docs/ssh-root~~`) rather than deleting — leaves a complete audit trail.
