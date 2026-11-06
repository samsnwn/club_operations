# STATUS

Last updated: 2026-11-06

## Stage: Phase 0.5 invoice quick win — internal authentication and reviewer attribution implemented (uncommitted)

## Snapshot

| Area | State |
| --- | --- |
| Product plan | Complete — full plan in `README.md`, including Phase 0.5 Invoice Ingestion Quick Win |
| Owner questions | Phase 0.5 working assumptions recorded (README §Phase 0.5); remaining Phase 0.5 details (credit notes, exact sheet columns) and broader Phase 0 discovery still open |
| Backend code | FastAPI (uv): `/api/v1/health` with DB round-trip, SQLAlchemy 2.0 settings/session, Alembic migrations; self-managed `users` + `auth_sessions` (Argon2id, opaque HttpOnly cookie sessions), auth routes (`/api/v1/auth/login|logout|me|password`), origin-check middleware, admin account-management API (`/api/v1/users`) with owner/admin/staff permissions, and the invoice facade (owner/admin only) forwarding the signed-in username as `X-Reviewer` |
| Invoice service (Phase 0.5) | Independent `invoice-service/` (uv, FastAPI :8081, own SQLite + Alembic): ingestion sources (Drive/Gmail degrade cleanly until credentials; fixture source), catch-up watermarks, extraction with confidence + first-pass trust, review queue API with internal token (records `X-Reviewer` when the facade supplies it), digest notifier, Sheets export feature-flagged OFF; runs in dev compose with Tesseract |
| Frontend code | React + TypeScript + Vite PWA (pnpm): login, forced first-sign-in password change, invoice review workspace (owner/admin), and a staff-account panel (owner/admin); staff accounts land on a no-modules home and cannot reach invoice data; session-expiry handling; responsive styling |
| CI | Single GitHub Actions workflow `ci.yml`: Prettier `format:check`, backend (uv sync → alembic upgrade → pytest), frontend (pnpm lint + build) — runs as one check on every push to `main` and PR |
| Authentication | Self-managed: no external identity provider, no JWT, no public registration. Administrator-created accounts with temporary passwords and forced first change; CLI bootstrap for the first owner (`python -m app.cli create-user`). Owner manages all accounts, admin manages staff, staff sign in and change their own password only; invoice review is owner/admin only |
| Formatting | One command, two language-native formatters: `pnpm format` / `pnpm format:check` run Prettier (TS/JS; same config + CI check as the owner's NotAnotherCards project) **and** Ruff (Black-style) over `backend/` + `invoice-service/` — Prettier never touches Python, Ruff never touches TS |
| Infra (Docker/HTTPS) | Development stack live: `infra/docker-compose.yml` with backend on 8080, Vite on 5173, and the invoice service on 8081 (Tesseract installed in its image; invoice store + files in their own volumes). Production compose overrides not yet written |
| Hosting hardware | Unknown — interim plan A: invoice service runs on demand on the owner's workstation (pull-based ingestion + watermark catch-up); upgrades to a dedicated box without rework |

## Done

- Complete project plan written and committed (README.md): modules 4.1–4.10, technical architecture, security, access, 10-phase roadmap, first-usable-version scope, product principles.
- Phase 0.5 — Invoice Ingestion Quick Win defined and expanded (email + Google Drive ingestion, OCR decision, review queue with trust levels, Google Sheets API vs. local `.xlsx`, architecture notes, owner questions).
- Initial repository skeleton and planning docs committed (docs/architecture.md, docs/milestones.md, docs/next-steps.md).
- Phase 0.5 unblocked: owner's working assumptions recorded in README §Phase 0.5 (Drive, Gmail + dedicated forwarding mailbox, 50/50 photo/scan mix with local Tesseract OCR, assumed v1 column set, owner + one admin as reviewers, ~20 invoices/month, email digest with review instructions; credit notes still open). Interim hosting = plan A: on-demand runs on the owner's workstation with watermark catch-up; upgrades to dedicated hardware without rework.
- Phase 0.5 `invoice-service/` scaffolded (uv, FastAPI on :8081, own SQLite + Alembic baseline): pull-based ingestion with per-source watermarks (Drive/Gmail adapters degrade cleanly until real credentials; fixtures for dev/tests), content-hash de-duplication, extraction as suggestions with per-field confidence and first-pass trust, review queue (`/api/v1/queue`: list/get/confirm-with-corrections/reject, bearer-token auth for owner + admin), collapsed digest notifier (SMTP-configurable, log-only fallback), Sheets export behind the `INVOICE_EXPORT_ENABLED=false` flag. 6/6 tests pass; runs as `invoice-service` in the dev compose, with Tesseract baked into its image.
- AGENTS.md, STATUS.md, CHANGE_LOG.md added.
- React + TypeScript + Vite scaffold created in `frontend/` (pnpm as package manager).
- PWA baseline configured: `vite-plugin-pwa` dependency added and `VitePWA` set up in `vite.config.ts` (autoUpdate registration, Web App manifest).
- FastAPI backend scaffolded in `backend/` (uv-managed, Python ≥3.12): app factory in `app/main.py`, versioned router under `/api/v1/` with a health endpoint including a database round-trip check (SQLite via SQLAlchemy 2.0), pydantic-settings config with gitignored `.env`, pytest suite for the health endpoint.
- Alembic wired to application settings (`alembic/env.py` reads `DATABASE_URL`); empty baseline migration created and applied.
- CI is green: single workflow `.github/workflows/ci.yml` (formatting check, backend tests via uv/Alembic/pytest, frontend pnpm lint + build) — first full `main` run passed after pull request #2 fixed a duplicate pnpm version pin; `pnpm/action-setup` now resolves pnpm from the root `packageManager` field (`pnpm@9.12.0`).
- Internal authentication (2026-11-06): `User` and `AuthSession` models with an Alembic migration; Argon2id hashing; opaque database sessions in an HttpOnly `SameSite=Lax` cookie (only the token hash is stored); `login`/`logout`/`me`/`password` routes; origin-check middleware for state-changing requests; `authenticated_user`/`current_user`/`require_role` dependencies.
- Account management (2026-11-06): CLI `create-user`/`reset-password` for bootstrap and recovery; `/api/v1/users` CRUD-style API (owner manages everyone, admin manages staff only) with self-change and last-owner guards plus session revocation on role change, deactivation and password reset.
- Invoice reviewer attribution (2026-11-06): the backend facade sends the authenticated username as `X-Reviewer` on every invoice-service call; the invoice service trusts it only with the internal token and records it in `reviewed_by`.
- Frontend authentication (2026-11-06): API client + typed auth calls, login screen, forced first-sign-in password change, signed-in header/navigation, staff-account management, and session-expiry handling across invoice and staff views. Staff accounts get a no-modules home and no invoice navigation; the owner/admin invoice workspace remains unchanged.

## In progress / uncommitted

- Internal authentication work (steps 1–7): backend users/sessions/auth routes/account-management API and migration, `X-Reviewer` forwarding through the facade, invoice-service trust contract, and the frontend login/staff/password UI. Tests: backend 44 passing, invoice-service 21 passing; frontend lint and build clean. Not committed yet.

## Next steps (ordered)

1. Review and commit the authentication work (after the developer's explicit go-ahead).
2. Run a manual pass through login → forced password change → staff creation → invoice review with the dev stack running.
3. Add production hardening to the compose override: HTTPS, `SESSION_COOKIE_SECURE=true`, real `ALLOWED_ORIGINS`, and invoice service remained internal-only.
4. Implement the first broader vertical slice: event creation + dashboard listing (README §10 Phase 1), with the first domain schema migration.
5. Revisit the two deferred invoice-service review findings: drop-folder settle logic based on mtime, and first-click-imports-nothing UX in the drop-folder demo.

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
- **Plan-vs-reality drift:** the plan describes the full platform while only Phase 0.5 code exists; avoid ambiguity by keeping STATUS.md and docs/next-steps.md current.
- **Uncommitted auth work:** the authentication change is broad (backend, invoice service, frontend, docs) and touches the trust boundary; review it before committing and keep the invoice service internal-only in every deployment.
