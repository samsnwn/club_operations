# STATUS

Last updated: 2026-11-09

## Stage: Phase 0.5 invoice quick win — manual review demo and internal authentication complete; Drive/Gmail ingestion, scheduling and sheet export are stubs

## Snapshot

| Area | State |
| --- | --- |
| Product plan | Complete — full plan in `README.md`, including Phase 0.5 Invoice Ingestion Quick Win |
| Owner questions | Phase 0.5 working assumptions recorded (README §Phase 0.5). Still open: credit-note handling and the real sheet's exact tabs/columns/formula columns. Broader Phase 0 discovery still open |
| Backend code | FastAPI (uv): `/api/v1/health` with DB round-trip, SQLAlchemy 2.0 settings/session, Alembic migrations; self-managed `users` + `auth_sessions` (Argon2id, opaque HttpOnly cookie sessions), auth routes (`/api/v1/auth/login|logout|me|password`), origin-check middleware, admin account-management API (`/api/v1/users`) with owner/admin/staff permissions, and the invoice facade (owner/admin only) forwarding the signed-in username as `X-Reviewer`. 46 tests passing |
| Invoice service (Phase 0.5) | Independent `invoice-service/` (uv, FastAPI :8081, own SQLite + Alembic). **Wired:** local drop-folder + fixture ingestion, settle detection, catch-up watermarks, content-hash dedupe, PDF-text/UTF-8/Tesseract extraction with confidence, review queue API with internal token and `X-Reviewer` attribution, digest builder. **Stubs:** Drive and Gmail adapters (`NotImplementedError` once configured), scheduled catch-up run (nothing periodic), Sheets export (`INVOICE_EXPORT_ENABLED=false`, raises when enabled), digest sending (built but never triggered). 21 tests passing |
| Frontend code | React + TypeScript + Vite PWA (pnpm): login, forced first-sign-in password change, invoice review workspace (owner/admin), and a staff-account panel (owner/admin); staff accounts land on a no-modules home and cannot reach invoice data; session-expiry handling; responsive styling |
| CI | Single GitHub Actions workflow `ci.yml`: Prettier `format:check`, compose config validation, Python lint (`ruff check` for both services), backend (uv sync → ruff check → alembic upgrade → pytest), invoice service (uv sync → ruff check → alembic upgrade → pytest), frontend (pnpm lint + build) — runs as one check on every push to `main` and PR |
| Authentication | Self-managed: no external identity provider, no JWT, no public registration. Administrator-created accounts with temporary passwords and forced first change; CLI bootstrap for the first owner (`python -m app.cli create-user`). Owner manages all accounts, admin manages staff, staff sign in and change their own password only; invoice review is owner/admin only |
| Formatting | One command, two language-native formatters: `pnpm format` / `pnpm format:check` run Prettier (TS/JS) **and** Ruff (Black-style) over `backend/` + `invoice-service/` — Prettier never touches Python, Ruff never touches TS |
| Infra (Docker/HTTPS) | Development stack defined: `infra/docker-compose.yml` with backend on 8080, Vite on 5173, and the invoice service on 8081 (Tesseract installed in its image; invoice store + files in their own volumes). Compose config validates. An API-level smoke pass on temporary host databases passed (2026-11-09); a full browser pass on the running Docker stack is still pending because the daemon was not running. Production compose overrides not yet written |
| Hosting hardware | Unknown — interim plan A: invoice service runs on demand (pull-based ingestion + watermark catch-up); upgrades to a dedicated box without rework |

## Done

- Complete project plan written and committed (README.md): modules 4.1–4.10, technical architecture, security, access, 10-phase roadmap, first-usable-version scope, product principles.
- Phase 0.5 — Invoice Ingestion Quick Win defined and expanded (email + Google Drive ingestion, OCR decision, review queue with trust levels, Google Sheets API vs. local `.xlsx`, architecture notes, owner questions).
- Initial repository skeleton and planning docs committed (docs/architecture.md, docs/milestones.md, docs/next-steps.md).
- Phase 0.5 unblocked: owner's working assumptions recorded in README §Phase 0.5 (Drive, local Tesseract OCR, assumed v1 column set, owner and admin reviewers, email digest with review instructions; credit notes still open). Interim hosting = plan A: on-demand runs with watermark catch-up; upgrades to dedicated hardware without rework.
- Phase 0.5 `invoice-service/` scaffolded (uv, FastAPI on :8081, own SQLite + Alembic baseline): pull-based ingestion with per-source watermarks (only drop-folder and fixture sources are wired; Drive/Gmail adapters are placeholders), content-hash de-duplication, extraction as suggestions with per-field confidence and first-pass trust, review queue (`/api/v1/queue`: list/get/confirm-with-corrections/reject, bearer-token auth for owner + admin), collapsed digest builder (SMTP-configurable, log-only fallback; not yet scheduled), Sheets export behind the `INVOICE_EXPORT_ENABLED=false` flag (stub). Runs as `invoice-service` in the dev compose, with Tesseract baked into its image.
- AGENTS.md, STATUS.md, CHANGE_LOG.md added.
- React + TypeScript + Vite scaffold created in `frontend/` (pnpm as package manager).
- PWA baseline configured: `vite-plugin-pwa` dependency added and `VitePWA` set up in `vite.config.ts` (autoUpdate registration, Web App manifest).
- FastAPI backend scaffolded in `backend/` (uv-managed, Python ≥3.12): app factory in `app/main.py`, versioned router under `/api/v1/` with a health endpoint including a database round-trip check (SQLite via SQLAlchemy 2.0), pydantic-settings config with gitignored `.env`, pytest suite for the health endpoint.
- Alembic wired to application settings (`alembic/env.py` reads `DATABASE_URL`); empty baseline migration created and applied.
- CI is green: single workflow `.github/workflows/ci.yml` (formatting check, backend tests via uv/Alembic/pytest, frontend pnpm lint + build) — first full `main` run passed after pull request #2 fixed a duplicate pnpm version pin; `pnpm/action-setup` now resolves pnpm from the root `packageManager` field (`pnpm@9.12.0`).
- Internal authentication (2026-11-06, committed): `User` and `AuthSession` models with an Alembic migration; Argon2id hashing; opaque database sessions in an HttpOnly `SameSite=Lax` cookie (only the token hash is stored); `login`/`logout`/`me`/`password` routes; origin-check middleware for state-changing requests; `authenticated_user`/`current_user`/`require_role` dependencies.
- Account management (2026-11-06): CLI `create-user`/`reset-password` for bootstrap and recovery; `/api/v1/users` CRUD-style API (owner manages everyone, admin manages staff only) with self-change and last-owner guards plus session revocation on role change, deactivation and password reset.
- Invoice reviewer attribution (2026-11-06): the backend facade sends the authenticated username as `X-Reviewer` on every invoice-service call; the invoice service trusts it only with the internal token and records it in `reviewed_by`.
- Frontend authentication (2026-11-06): API client + typed auth calls, login screen, forced first-sign-in password change, signed-in header/navigation, staff-account management, and session-expiry handling across invoice and staff views. Staff accounts get a no-modules home and no invoice navigation; the owner/admin invoice workspace remains unchanged.
- Invoice review demo (2026-11-05/06): local drop-folder import from `invoice-service/data/inbox/` with settle detection, per-capture size/PDF-page limits, content-hash dedupe, extracted-text inspection and original-file preview, confirm-with-corrections and reject, through the backend facade.
- CI hardening (2026-11-09): `ruff check` now runs for both Python services, the invoice-service Alembic chain is applied in CI, and the compose file is validated, closing the gap where only formatting was enforced.
- API-level smoke pass (2026-11-09) against temporary SQLite databases on the host: both health checks, owner CLI bootstrap + login, cross-origin rejection, staff creation, forced staff password change, drop-folder fixture import, confirm-with-corrections with `reviewed_by` attribution, duplicate-confirm 409, staff invoice-role gate, and logout invalidation all passed.
- Agent-facing docs refreshed (2026-11-09): `AGENTS.md` current stage, `STATUS.md`, `docs/next-steps.md` and the service READMEs now distinguish implemented functionality from stubs; `frontend/README.md` replaced the Vite template boilerplate with project instructions.

## In progress / not started

- A browser-level pass on the running Docker stack (visual layout, feedback messages, original preview) has not been recorded; Docker was unavailable during the 2026-11-09 review. The API flow itself is verified.
- No real-invoice accuracy pass has been run yet — extraction quality on actual PDFs/scans is unproven.
- Drive and Gmail ingestion, the scheduled catch-up run, automatic digest sending and the Sheets export are not implemented (stubs as described above).
- No platform domain modules yet: events, dashboard, staff mobile interface, promoter form, inventory, documents and the local AI assistant.

## Next steps (ordered)

1. Start the dev stack and do a browser-level pass (the API flow already passed on 2026-11-09): login, forced password change, staff creation, invoice import from `data/inbox/`, review, original preview, confirm.
2. Run a real-invoice accuracy pass (10–20 representative invoices kept outside the repo) through the drop-folder demo; measure correct field suggestions before investing in automation.
3. Lock the accounting-sheet contract with the owner (tabs, columns, formula columns, correction/supersede rules) and implement the append-only Sheets export with a dry run and export status/history; flip `INVOICE_EXPORT_ENABLED` on only after the dry run matches the real sheet.
4. Wire Drive and Gmail ingestion, then add the scheduled catch-up run (with a single-run lock) and automatic digest sending.
5. Add production hardening: HTTPS, `SESSION_COOKIE_SECURE=true`, real `ALLOWED_ORIGINS`, invoice service internal-only, backups, log retention and login rate limiting.
6. Implement the first broader vertical slice: event creation + dashboard listing (README §8, Phase 1), with the first domain schema migration.
7. Revisit the two deferred invoice-service review findings: drop-folder settle logic based on mtime, and the first-click-imports-nothing UX in the drop-folder demo.

## Open questions blocking Phase 0.5

1. Credit-note/correction handling: are there credit notes that reverse earlier invoices, and how are they represented in the sheet today?
2. The real sheet's exact tabs, columns and formula-vs-value columns (the assumed v1 column set is recorded in README §Phase 0.5, but the mapping must be confirmed before the first write).

All other Phase 0.5 questions are answered as working assumptions in README §Phase 0.5 ("Owner answers"), and should be revisited if reality differs.

## Risks

- **Stubs mistaken for delivered automation:** Drive/Gmail/scheduler/export are placeholders; keep STATUS, docs and UI copy explicit so nobody expects invoices to flow automatically or reach the sheet.
- **Extraction quality:** generic regex plus Tesseract is unproven on real scans; if accuracy is poor, supplier templates or OCR tuning are needed before automation is worth enabling.
- **Email access friction:** personal Gmail OAuth verification or app-password setup can take days; a dedicated forwarding mailbox is the fallback.
- **OCR/cloud trade-off:** if most invoices are scans, local-only extraction may be too weak; cloud OCR raises local-first/GDPR questions the owner must decide (owner currently chose Tesseract only).
- **Excel file locking/monolith drift:** mitigated by the Google Sheets API path; and by keeping the sheet as an output artifact with SQLite records as source of truth.
- **Plan-vs-reality drift:** the plan describes the full platform while only the invoice review demo and auth exist; avoid ambiguity by keeping STATUS.md and docs/next-steps.md current.
- **Production gap:** dev compose only, invoice service published on :8081 and a known default internal token; the service must stay internal-only and use a non-default token in every real deployment.
