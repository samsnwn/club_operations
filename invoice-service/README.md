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

## Layout

- `app/ingestion/` — capture sources (Drive, Gmail, fixtures for tests), the
  content-hash de-duplication and ingest pipeline.
- `app/extraction/` — text/OCR extraction and field parsing (output is always
  a *suggestion*, never a written fact).
- `app/review/` — the queue API: pending items, confirm/correct/reject.
  Only confirmed invoices can ever be exported.
- `app/export/` — Google Sheets writer, **feature-flagged off** until the
  column mapping is confirmed against the real sheet (hard rule 2).
- `app/notify/` — digest builder/sender (email to the owner).
- `alembic/` — migrations for this service's own SQLite store.

## Run (dev, on this machine)

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8081
```

API docs: `http://localhost:8081/docs` — health under `/api/v1/health`.

Until real Gmail/Drive credentials exist, the ingestion command-line/test path
uses the fixture source (`tests/fixtures/`, deliberately fake club data); the
Gmail/Drive adapters log a clear "not configured" and skip cleanly.

For a real-invoice demonstration, copy PDFs or images into
`data/inbox/` and click **Import invoices** in the frontend. The folder is
gitignored and bind-mounted into Docker. Imported originals remain in the
service's data volume and can be previewed from the review screen.

## Reviewer attribution

`POST /api/v1/queue/{id}/confirm` and `/reject` record a `reviewed_by` value.
The internal bearer token alone attributes the action to `backend`; when the
backend facade also sends an `X-Reviewer` header, that username is used
instead. The header is trusted **only** alongside a valid internal token —
never for unauthenticated or browser-direct calls. Through the main platform,
the facade derives `X-Reviewer` from the signed-in session, so reviewers are
attributed to their own accounts.

## Tests

```bash
uv run pytest
```
