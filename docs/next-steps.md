# Next Steps

1. ~~Scaffold `frontend/` with React + TypeScript + Vite and PWA plugin.~~ — done (2026-11-04).
2. ~~Scaffold `backend/` with FastAPI, routing, and `/api/v1/health` endpoint.~~ — done (2026-11-05), uv-managed with CI pipeline.
3. ~~Add initial SQLite schema and Alembic migration baseline.~~ — done (2026-11-05); schema migrations follow with the first models.
4. ~~Add Docker Compose for backend/frontend/database/file storage.~~ — development stack done (2026-11-05, `infra/docker-compose.yml` + Dockerfiles with `dev`/`prod` targets); production compose overrides and HTTPS still to come.
5. ~~Create the invoice-focused frontend and thin backend facade.~~ — done (2026-11-05): frontend calls the main backend only; backend proxies to the separate invoice service.
6. ~~Define authentication and role permissions for internal users.~~ — done (2026-11-06): backend-owned users and database-backed cookie sessions, Argon2id hashes, owner/admin/staff roles with administrator-created accounts, CLI bootstrap for the first owner, invoice review restricted to owners and administrators, and per-user reviewer attribution through to the invoice service.
7. ~~Implement invoice detail and confirm/correct workflow in the frontend.~~ — done (2026-11-05).
8. ~~Add local drop-folder ingestion and original invoice preview for the owner demo.~~ — done (2026-11-05).
9. ~~Add Python lint and invoice-service migrations to CI.~~ — done (2026-11-09): `ruff check` for both services and `alembic upgrade head` for the invoice service.
10. ~~Run an API-level smoke pass on the dev flow.~~ — done (2026-11-09): health, owner bootstrap/login, origin guard, staff lifecycle, drop-folder import, confirm-with-corrections, reviewer attribution, staff role gate and logout invalidation. A browser-level pass on the Docker stack is still pending.
11. Run a real-invoice accuracy pass (10–20 representative invoices kept outside the repo) through the drop-folder demo and measure field-suggestion accuracy before automating ingestion.
12. Confirm the accounting-sheet contract with the owner (tabs, columns, formula columns, correction rules), then implement the append-only Sheets export with a dry run and export status/history. Keep `INVOICE_EXPORT_ENABLED=false` until the dry run matches the real sheet.
13. Wire Drive and Gmail ingestion, then add the scheduled catch-up run (single-run lock) and automatic digest sending.
14. Add production hardening: HTTPS, `SESSION_COOKIE_SECURE=true`, real `ALLOWED_ORIGINS`, invoice service internal-only, backups, log retention, login rate limiting.
15. Implement the first broader vertical slice: event creation + dashboard listing (README §8, Phase 1), with the first domain schema migration.
