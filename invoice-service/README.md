# Phase 0.5 — Invoice Ingestion service

Independent service implementing the plan in `README.md` §Phase 0.5:
**ingest (Drive folder + forwarding mailbox) → classify → extract (Tesseract
OCR for photos/scans, text layer for PDFs) → review queue → Google Sheets API
as an append-only output artifact.**

Stands on the owner's recorded answers (README §Phase 0.5, "Owner answers
(working assumptions)"): Google Drive, local OCR only, owner and admin reviewers, digest email with review instructions. Credit-note handling is
still an open question — corrections go through the review queue only.

**Interim hosting (plan A):** until the dedicated club hardware exists, the
service runs on demand. Ingestion is pull-based:
the forwarding mailbox and the Drive folder buffer everything, and per-source
sync watermarks make each catch-up run ingest the full backlog. A quiet period
produces one collapsed digest email instead of daily silence-breaking ones.

## Current implementation status

| Capability | State |
| --- | --- |
| Local drop-folder ingestion (`data/inbox/`) | **Working** — settle detection, size/page limits, content-hash dedupe |
| Fixture ingestion (`tests/fixtures/`) | **Working** — used by tests; deliberately fake data |
| Drive folder ingestion | **Stub** — adapter returns "not configured" without credentials and raises `NotImplementedError` when configured |
| Gmail forwarding-mailbox ingestion | **Stub** — same behaviour as Drive |
| Text/OCR extraction + field suggestions | **Working** — PDF text layer, UTF-8 text, local Tesseract; generic regex fields |
| Review queue (list/detail/confirm/reject, attribution) | **Working** |
| Scheduled catch-up run | **Stub** — nothing periodic runs; import is triggered manually |
| Digest email | **Builder working** — not scheduled or triggered automatically |
| Google Sheets export | **Stub** — feature-flagged off; raises when enabled |

The end-to-end demo today is therefore: drop files into `data/inbox/`, click
**Import invoices**, review/confirm. Confirmed invoices are recorded but not
yet exported anywhere.

## Layout

- `app/ingestion/` — capture sources (Drive, Gmail, fixtures for tests), the
  content-hash de-duplication and ingest pipeline.
- `app/extraction/` — text/OCR extraction and field parsing (output is always
  a *suggestion*, never a written fact).
- `app/review/` — the queue API: pending items, confirm/correct/reject.
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

Until real Gmail/Drive credentials exist, the ingestion command-line/test path
uses the fixture source (`tests/fixtures/`, deliberately fake club data); the
Gmail/Drive adapters log a clear "not configured" and skip cleanly. Note that
supplying credentials today would reach `NotImplementedError`: the adapters are
placeholders, not a working integration.

For a real-invoice demonstration, copy PDFs or images into
`data/inbox/` and click **Import invoices** in the frontend. The folder is
gitignored and bind-mounted into Docker. Imported originals remain in the
service's data volume and can be previewed from the review screen.

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
