# kobo-sync

Pulls KoboToolbox submissions + form, assigns Store IDs / derives the 9-state
status / flags duplicates (reusing `store_master/`), and writes them to a Google
Sheet (`_raw` · `_form` · `master` · `_media` · `_status`) plus real photo files
to Google Drive — with a guarded, **OFF-by-default** rolling-delete of synced
Kobo submissions. Runs on GitHub Actions (schedule + manual). Idempotent by Kobo `_uuid`.

## Run

- **GitHub Actions:** Actions → *Kobo sync* → *Run workflow* (or the hourly schedule).
- **Local / offline test:** `python -m kobo_sync.run --fake kobo_sync/fake.json`
- **Local / live:** set the env vars below, then `python -m kobo_sync.run`

## Configuration (GitHub → Settings → Secrets and variables → Actions)

**Secrets** (sensitive):

| Secret | Value |
|---|---|
| `KOBO_TOKEN` | KoboToolbox API token |
| `KOBO_ASSET_UID` | the form's asset UID |
| `SHEET_ID` | Google Sheet ID (from its URL) |
| `DRIVE_FOLDER_ID` | Drive photos folder ID (from its URL) |
| `GOOGLE_SA_JSON` | the service-account JSON key (whole file contents) |

**Variables** (non-sensitive):

| Variable | Default | Meaning |
|---|---|---|
| `ARCHIVE_MODE` | `off` | `off` (sync only) → `dry_run` (log would-delete) → `delete` (delete from Kobo) |
| `ARCHIVE_AFTER_DAYS` | `30` | only delete submissions older than this (grace window) |

## Safety

`delete` is irreversible. Roll out in order: `off` → verify Sheet/Drive → set up a
local backup + test a restore → `dry_run` → `delete`. The service account must be
shared (Editor) on both the Sheet and the Drive folder.

See the full design at `docs/superpowers/specs/2026-06-26-store-data-pipeline-phaseA-design.md`
in the parent project.
