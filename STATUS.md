# STATUS

Last updated: 2026-11-05

## Stage: Frontend scaffold (Vite PWA baseline) + backend scaffold (FastAPI) — Phase 0.5 discovery still blocking the invoice service

## Snapshot

| Area | State |
| --- | --- |
| Product plan | Complete — full plan in `README.md`, including Phase 0.5 Invoice Ingestion Quick Win |
| Owner questions | Not yet answered — Phase 0 (discovery) and Phase 0.5 questions outstanding |
| Backend code | FastAPI scaffold (uv): `/api/v1/health` with DB round-trip check, SQLAlchemy 2.0 settings/session, Alembic wired to app settings with empty baseline migration; no models yet |
| Invoice service (Phase 0.5) | Scaffolded as independent `invoice-service/` (uv, FastAPI :8081, own SQLite + Alembic): ingestion sources (Drive/Gmail degrade cleanly until credentials; fixture source), catch-up watermarks, extraction with confidence + first-pass trust, review queue API with owner/admin tokens, digest notifier, Sheets export feature-flagged OFF; runs in dev compose with Tesseract |
| Frontend code | React + TypeScript + Vite scaffold with PWA plugin configured (pnpm); placeholder UI, no real modules yet |
| CI | Single GitHub Actions workflow `ci.yml`: Prettier `format:check`, backend (uv sync → alembic upgrade → pytest), frontend (pnpm lint + build) — runs as one check on every push to `main` and PR |
| Formatting | Prettier at the repo root (`pnpm format` / `pnpm format:check`, same config + CI check as the owner's NotAnotherCards project) |
| Infra (Docker/HTTPS) | Development stack live: `infra/docker-compose.yml` with backend on 8080, Vite on 5173, and the invoice service on 8081 (Tesseract installed in its image; invoice store + files in their own volumes). Production compose overrides not yet written |
| Hosting hardware | Unknown — interim plan A: invoice service runs on demand (pull-based ingestion + watermark catch-up); upgrades to a dedicated box without rework |

## Done

- Complete project plan written and committed (README.md): modules 4.1–4.10, technical architecture, security, access, 10-phase roadmap, first-usable-version scope, product principles.
- Phase 0.5 — Invoice Ingestion Quick Win defined and expanded (email + Google Drive ingestion, OCR decision, review queue with trust levels, Google Sheets API vs. local `.xlsx`, architecture notes, owner questions).
- Initial repository skeleton and planning docs committed (docs/architecture.md, docs/milestones.md, docs/next-steps.md).
- Phase 0.5 unblocked: owner's working assumptions recorded in README §Phase 0.5 (Drive, local Tesseract OCR, assumed v1 column set, owner and admin reviewers, email digest with review instructions; credit notes still open). Interim hosting = plan A: on-demand runs with watermark catch-up; upgrades to dedicated hardware without rework.
- Phase 0.5 `invoice-service/` scaffolded (uv, FastAPI on :8081, own SQLite + Alembic baseline): pull-based ingestion with per-source watermarks (Drive/Gmail adapters degrade cleanly until real credentials; fixtures for dev/tests), content-hash de-duplication, extraction as suggestions with per-field confidence and first-pass trust, review queue (`/api/v1/queue`: list/get/confirm-with-corrections/reject, bearer-token auth for owner + admin), collapsed digest notifier (SMTP-configurable, log-only fallback), Sheets export behind the `INVOICE_EXPORT_ENABLED=false` flag. 6/6 tests pass; runs as `invoice-service` in the dev compose, with Tesseract baked into its image.
- AGENTS.md, STATUS.md, CHANGE_LOG.md added.
- React + TypeScript + Vite scaffold created in `frontend/` (pnpm as package manager).
- PWA baseline configured: `vite-plugin-pwa` dependency added and `VitePWA` set up in `vite.config.ts` (autoUpdate registration, Web App manifest).
- FastAPI backend scaffolded in `backend/` (uv-managed, Python ≥3.12): app factory in `app/main.py`, versioned router under `/api/v1/` with a health endpoint including a database round-trip check (SQLite via SQLAlchemy 2.0), pydantic-settings config with gitignored `.env`, pytest suite for the health endpoint.
- Alembic wired to application settings (`alembic/env.py` reads `DATABASE_URL`); empty baseline migration created and applied.
- CI is green: single workflow `.github/workflows/ci.yml` (formatting check, backend tests via uv/Alembic/pytest, frontend pnpm lint + build) — first full `main` run passed after pull request #2 fixed a duplicate pnpm version pin; `pnpm/action-setup` now resolves pnpm from the root `packageManager` field (`pnpm@9.12.0`).

## In progress / uncommitted

- None — working tree clean; all of today's scaffolding, formatting and CI work is committed, and `main` is up to date with `origin/main` (including merged pull request #2).

## Next steps (ordered)

1. Ask the owner the Phase 0.5 question set (8 questions, README §Phase 0.5) — highest priority, it unblocks the quick win.
2. Ask the owner the broader Phase 0 discovery questions (module workflows, hardware, hosting, access, users).
3. Based on owner answers, scaffold the Phase 0.5 invoice-ingestion service (independent Python service; mechanisms decided by the sheet-location + email-access answers).
4. Meanwhile, without depending on owner answers: add Docker Compose (`infra/`), then the first vertical slice (event creation + dashboard listing) with the first Alembic schema migration per `docs/next-steps.md`.

## Open questions blocking Phase 0.5

1. Is the accounting sheet on Google Drive, or must it remain a local `.xlsx`?
2. Email provider; OAuth/app-password feasibility; is a dedicated forwarding mailbox acceptable?
3. Proportion of clean PDF invoices vs. scans/photos (decides OCR approach; GDPR trade-off if cloud OCR).
4. Exact sheet columns, formula vs. value columns, tab structure.
5. Who opens the sheet, when, from where (incl. accountant)?
6. Monthly invoice volume and number of suppliers.
7. Credit-note/correction handling.
8. Notification preference for processed invoices / items needing attention.

## Risks

- **Email access friction:** personal Gmail OAuth verification or app-password setup can take days; a dedicated forwarding mailbox is the fallback.
- **OCR quality:** if most invoices are scans, local-only extraction may be too weak; cloud OCR raises local-first/GDPR questions the owner must decide.
- **Excel file locking/monolith drift:** mitigated by Google Sheets API path; and by keeping the sheet as output artifact with SQLite records as source of truth.
- **Plan-vs-reality drift:** the plan describes the full platform while no code exists; avoid ambiguity by keeping STATUS.md and docs/next-steps.md current.
