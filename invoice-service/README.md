# Phase 0.5 — Invoice Ingestion service

Independent service implementing the plan in `PLAN.md` §Phase 0.5:
**ingest (the owner's Google Drive invoice folder) → extract (Tesseract
OCR for photos/scans, text layer for PDFs) → review queue → Google Sheets API
as an append-only output artifact.**

Scope: a single Google Drive invoice folder as the only source (no email
ingestion in Phase 0.5), local OCR only, owner and admin accounts as
reviewers, and a digest email with review instructions. Credit-note handling
is still an open question — corrections go through the review queue only.

**Interim hosting:** until dedicated hardware exists, the service runs on
demand. Ingestion is pull-based:
the invoice folder buffers everything, and each import lists the whole folder
and takes every file not imported yet. A quiet period produces one collapsed
digest email instead of daily silence-breaking ones.

## Current implementation status

| Capability | State |
| --- | --- |
| Invoice folder (Google Drive) ingestion | **Working** — read-only service account; PDF/JPEG/PNG/WebP directly in the folder; known files skipped by MD5 before download; files stay in place. Not yet verified against a real Drive folder |
| Local inbox (`data/inbox/`, development) | **Working** — settle detection, size/page limits, content-hash dedupe; used when Drive is not configured |
| Email ingestion | **Not planned for Phase 0.5** |
| Text/OCR extraction + field suggestions | **Working** — PDF text layer, UTF-8 text, local Tesseract; generic regex fields; `needs_attention` when a required field is not suggested |
| Review queue (list/detail/confirm/reject, attribution) | **Working** |
| Scheduled catch-up run | **Not started** — nothing periodic runs; import is triggered manually |
| Digest email | **Builder working** — not scheduled or triggered automatically |
| Google Sheets export | **Stub** — feature-flagged off; raises when enabled |

The owner workflow is: upload invoices to the invoice folder, click **Import
invoices**, review/confirm. Without Drive credentials (development), Import
reads `data/inbox/` instead. Confirmed invoices are recorded but not
yet exported anywhere.

## Layout

- `app/ingestion/` — the invoice folder (`drive.py`) and local inbox
  (`drop_folder.py`) channels, the `CapturedFile` shape, and the ingest
  pipeline (de-duplication, storage, extraction).
- `app/extraction/` — text/OCR extraction and field parsing (output is always
  a *suggestion*, never a written fact).
- `app/review/` — the queue API: open invoices, confirm/correct/reject.
  Only confirmed invoices can ever be exported.
- `app/export/` — Google Sheets writer, **feature-flagged off** until the
  column mapping is confirmed against the real sheet (hard rule 3).
- `app/notify/` — digest builder/sender (email to the owner).
- `alembic/` — migrations for this service's own SQLite store.

## Run (dev, on this machine)

```bash
uv sync
INVOICE_ENVIRONMENT=development uv run uvicorn app.main:app --reload --port 8081
```

API docs: `http://localhost:8081/docs` — health under `/api/v1/health`.

The service fails closed: `INVOICE_ENVIRONMENT` defaults to `production`, and
startup refuses the known development token in that mode. Local runs must opt
into development explicitly (as above or via `.env`).

**Import invoices** reads the invoice folder when `INVOICE_DRIVE_FOLDER_ID`
and `INVOICE_DRIVE_CREDENTIALS_FILE` are both set, and the local inbox
otherwise. Tests run the local inbox over `tests/fixtures/invoices/`
(deliberately fake club data) and a fake Drive. If Drive cannot be reached the
import fails with 503 "Google Drive unavailable"; wrong credentials or an
unshared folder fail with 502 and say so. It never reports "0 new" for a
broken connection.

For a local demonstration without Drive, copy PDFs or images into
`data/inbox/` and click **Import invoices** in the frontend. The folder is
gitignored and bind-mounted into Docker. Imported originals remain in the
service's data volume and can be previewed from the review screen.

## Google Drive setup (once, with the owner)

Step-by-step guide, including why to use a dedicated club Google account:
[`docs/google-drive-setup.md`](../docs/google-drive-setup.md). In short: a
read-only service account, shared on the invoice folder as **Viewer**, with
its key in `invoice-service/secrets/drive-service-account.json` and these in
`invoice-service/.env`:

```bash
INVOICE_DRIVE_FOLDER_ID=<ID>
INVOICE_DRIVE_CREDENTIALS_FILE=./secrets/drive-service-account.json
```

The service only reads: Viewer access and the `drive.readonly` scope. Files
stay in the folder as the owner's archive; only files directly in the folder
(not subfolders) are imported.

## Environment

Every setting has a development-safe default. To override anything, copy
`.env.example` to `.env` in this directory; the service adds the `INVOICE_`
prefix automatically. `INVOICE_INTERNAL_TOKEN` must match the backend's
`INVOICE_SERVICE_TOKEN`. Keep `INVOICE_EXPORT_ENABLED=false` until the sheet
mapping is confirmed. Never commit `.env`.

`INVOICE_ENVIRONMENT` defaults to `production`. In production, startup refuses
the known development token and requires a unique `INVOICE_INTERNAL_TOKEN`; the
development compose file sets `INVOICE_ENVIRONMENT=development` explicitly.
There is no per-user review-token fallback: the internal token plus the
`X-Reviewer` header is the only service credential path.

## Security boundary

The internal token grants full access to invoice data (queue, originals,
confirm/reject) and bypasses the platform facade, so it must be a unique secret
outside development. The dev compose publishes the service on
`127.0.0.1:8081` only; production must keep `:8081` internal to the compose
network and never expose it to the LAN or internet.

## Review rules

Ingestion marks an invoice `needs_attention` when extraction did not suggest
every required field (`supplier`, `invoice_date`, `gross`) and
`pending_review` otherwise; queue items list them in `missing_fields`.
`GET /api/v1/queue` defaults to `status=open` (both statuses), needs attention
first, then oldest first. Terms are defined in the root `GLOSSARY.md`.

Confirm and reject are only accepted while an invoice is open
(`pending_review` or `needs_attention`); any later attempt returns 409, so a rejected invoice cannot
be confirmed and two reviewers cannot both decide the same invoice. Confirm
requires `supplier`, `invoice_date` and `gross` (422 otherwise) — a confirmed
row is export-eligible and must never be blank. Only one import runs at a
time; a second request while one is in progress returns 409.

## Reviewer attribution

`POST /api/v1/queue/{id}/confirm` and `/reject` record a `reviewed_by` value.
The internal bearer token alone attributes the action to `backend`; when the
backend facade also sends an `X-Reviewer` header, that username is used
instead. The header is trusted **only** alongside a valid internal token —
never for unauthenticated or browser-direct calls. Through the main platform,
the facade derives `X-Reviewer` from the signed-in session, so reviewers are
attributed to their own accounts. Per-user bearer tokens are no longer
supported; direct API use requires the internal token.

## Tests

```bash
uv run pytest
```
