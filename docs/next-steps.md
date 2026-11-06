# Next Steps

1. ~~Scaffold `frontend/` with React + TypeScript + Vite and PWA plugin.~~ — done (2026-11-04).
2. ~~Scaffold `backend/` with FastAPI, routing, and `/api/v1/health` endpoint.~~ — done (2026-11-05), uv-managed with CI pipeline.
3. ~~Add initial SQLite schema and Alembic migration baseline.~~ — done (2026-11-05); schema migrations follow with the first models.
4. ~~Add Docker Compose for backend/frontend/database/file storage.~~ — development stack done (2026-11-05, `infra/docker-compose.yml` + Dockerfiles with `dev`/`prod` targets); production compose overrides and HTTPS still to come.
5. ~~Create the invoice-focused frontend and thin backend facade.~~ — done (2026-11-05): frontend calls the main backend only; backend proxies to the separate invoice service.
6. ~~Define authentication and role permissions for internal users.~~ — done (2026-11-06): backend-owned users and database-backed cookie sessions, Argon2id hashes, owner/admin/staff roles with administrator-created accounts, CLI bootstrap for the first owner, invoice review restricted to owners and administrators, and per-user reviewer attribution through to the invoice service.
7. ~~Implement invoice detail and confirm/correct workflow in the frontend.~~ — done (2026-11-05).
8. ~~Add local drop-folder ingestion and original invoice preview for the owner demo.~~ — done (2026-11-05).
9. Implement first broader vertical slice: event creation + dashboard listing.
