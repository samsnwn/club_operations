# CHANGE_LOG

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project currently has no runtime releases, so entries are dated by change.

## [2026-11-05]

### Added
- Docker development stack under `infra/`: `docker-compose.yml` (project `blue-velvet`) running both services hot-reloading from bind-mounted sources — backend on `:8080` (uv-based image, migrations applied on startup, SQLite in the `db-data` named volume) and frontend on `:5173` (dependencies in an image-level volume so host/container installs don't clash, `.vite` cache in its own volume). `backend/Dockerfile` and `frontend/Dockerfile` each define `dev` and `prod` targets for later production use, with per-context `.dockerignore` files. Container fix: corepack's `enable` alone fell back to pnpm 12 in the Node image, whose default supply-chain policy (`minimumReleaseAge`) rejected lockfile entries published within 8 hours — the image now activates the pinned `pnpm@9.12.0` explicitly.
- `vite-plugin-pwa` registered as a dev dependency in `frontend/` (pnpm).
- FastAPI backend scaffold in `backend/` (uv-managed, Python ≥3.12): app factory, versioned router under `/api/v1/`, health endpoint with a SQLite round-trip check (SQLAlchemy 2.0), pydantic-settings config (`.env` gitignored), pytest suite, `backend/README.md`; `backend/app/.gitkeep` removed.
- Alembic migrations wired to application settings via `app.core.config`; empty baseline migration created and applied.
- Single CI workflow `.github/workflows/ci.yml` — lint, format, test and build as one sequential job with a concurrency group, same shape as the owner's NotAnotherCards CI: root `pnpm format:check`, backend (`uv sync` → `uv run alembic upgrade head` → `uv run pytest`), frontend (`pnpm install --frozen-lockfile` → `pnpm run lint` → `pnpm run build`). Runs on every push to `main` and every PR; replaced the earlier separate `backend.yml`/`frontend.yml` workflows.
- Prettier formatting at the repository root, mirroring NotAnotherCards: `.prettierrc` (`singleQuote`, `trailingComma: "all"`), `.prettierignore`, root `pnpm format` / `pnpm format:check` scripts over `**/*.{ts,tsx,mts,mjs,js,cjs,cts}`, committed root `pnpm-lock.yaml`; the four template TS files were reformatted.
- Root `.gitignore` covering `node_modules/`, env files and OS artifacts (previously only `backend/` and `frontend/` had ignores).
- `infra/README.md` — documents development vs production Docker usage: how the services wire together (binds, volumes, Vite proxy), data-discipline rules, check parity with CI, the production roadmap (compose override, prod targets, reverse proxy with HTTPS at a single origin, migrations as deploy step, backups), and the deployment decisions still gated on Phase 0 owner answers.
- Phase 0.5 unblocked: owner's working assumptions recorded in README §Phase 0.5 (Drive sheet, Gmail + dedicated forwarding mailbox, 50/50 photo/scan mix with local Tesseract OCR — no cloud OCR, assumed v1 column set, owner + one admin as reviewers, ~20 invoices/month, email digest with review instructions; credit-note handling still open). Interim hosting = plan A: on-demand runs on the owner's workstation with watermark catch-up, upgrading to dedicated hardware without rework.
- Phase 0.5 `invoice-service/` scaffolded (uv, FastAPI on :8081, own SQLite via SQLAlchemy 2.0 with Alembic baseline): pull-based ingestion with per-source sync watermarks (Drive and Gmail adapters degrade cleanly until credentials live outside the repo; a fixture source feeds the pipeline with deliberately fake club data), content-hash de-duplication, text-layer routing (PDF text layer → plain UTF-8 → else Tesseract OCR), field extraction as suggestions with per-field confidence, first-pass trust statuses (`pending_review` / `needs_attention`), review queue API (`/api/v1/queue` list/get/confirm-with-corrections/reject) with per-user bearer tokens for owner and admin, collapsed digest notifier (SMTP-configurable with log-only fallback), and Google Sheets export behind the `INVOICE_EXPORT_ENABLED=false` feature flag until the column mapping is confirmed against the real sheet (hard rule 2). Runs as `invoice-service` in the dev compose (Tesseract baked into its image, invoice store and files in named volumes); 6/6 tests pass (health, catch-up + dedupe, needs-attention handling, auth, review flow, digest).

- Ruff (Black-style formatter) added as a dev dependency to both Python services (`backend/`, `invoice-service/`); the root `pnpm format` / `pnpm format:check` scripts now run Prettier **and** `ruff format` in one command, giving the repo a single unified formatting entry point while keeping language-native toolchains (Prettier has no Python parser, and the community's output standard for Python is Black-style, so a Prettier plugin would fight the Python ecosystem). First pass reformatted 10 Python files; backend and invoice-service test suites still green.

### Changed
- `frontend/vite.config.ts`: Vite proxy target now reads `BACKEND_URL` (defaults to `http://localhost:8080` on the host; docker compose sets `http://backend:8080`), so the same config wires same-origin `/api` requests correctly on host and in Docker. The proxy forwards to `http://localhost:8000` initially (no path rewrite; backend routes already start with `/api`); no CORS middleware needed in dev.
- `AGENTS.md` Command section reorganised: Docker Compose dev commands are now the primary documented dev path (`up -d --build` / `logs -f` / in-container `alembic revision` / `down`), with the host `uv` workflow kept below for CI-parity checks.
- Backend dev port moved from `8000` to `8080` (`uvicorn --port 8080`, `backend/README.md`, `AGENTS.md`, frontend Vite proxy target): OpenCode's built-in vLLM provider discovery probes `http://127.0.0.1:8000/v1` by default, which spammed the dev server with `/health` + `/v1/models` requests. The temporary 404-logging diagnostic middleware was removed again; port `8080` is outside OpenCode's local-discovery defaults.
- `app/main.py`: added (then removed) a root-level `/health` alias — it masked 404 spam from the OpenCode vLLM discovery probe while the backend sat on port 8000; the port move to 8080 made the alias unnecessary, and only the canonical `/api/v1/health` remains.
- Frontend TypeScript pinned to `~5.9.3` (from the template's `~7.0.2`): `typescript-eslint` 8.x supports TS < 6.1, so `pnpm run lint` failed on the template pin. Both lint and build pass on 5.9.3. Revisit when typescript-eslint adds TS 7 support.
- CI pnpm configuration cleaned up via pull request #2 (Copilot agent branch `copilot/fix-lint-and-build`): the conflicting duplicate `version` pin was removed from the `pnpm/action-setup` step, which now resolves pnpm from the root `packageManager` field (`pnpm@9.12.0`). First full CI runs on `main` and the PR both completed successfully.

## [2026-11-04]

### Added
- React + TypeScript + Vite scaffold in `frontend/`: Vite app (`App.tsx`, `main.tsx`, styles, assets), ESLint config, split `tsconfig.*` files, `index.html`, public assets, `.gitignore`, pnpm lockfile.
- `AGENTS.md` — conventions, stack constraints and hard rules for AI coding agents.
- `STATUS.md` — current project status snapshot.
- `CHANGE_LOG.md` — this file.

### Changed
- Project plan expanded and moved into `README.md` with the **Phase 0.5 — Invoice Ingestion Quick Win**: dual ingestion channels (Google Drive folder as primary, email as automated secondary), Gmail/Drive access considerations including the dedicated-forwarding-mailbox alternative, text-PDF vs. scanned-invoice OCR strategy with local-first/GDPR trade-off, a review queue with staged trust levels, Google Sheets API vs. local `.xlsx` output guidance, architecture notes (independent FastAPI service, SQLite record store), and an expanded Phase 0.5 owner question set (8 questions).

## [2026-10-31]

### Added
- Repository skeleton and planning documentation merged via pull request #1: top-level layout (`backend/`, `frontend/`, `infra/`, `docs/`), `docs/architecture.md` (modular monolith direction), `docs/milestones.md` (M0–M5 milestones), `docs/next-steps.md` (first scaffolding tasks).
- Initial commit (LICENSE).

## [2026-10-30]

### Added
- Initial project plan drafted and refined (as `INITIAL_PLAN.md`, later merged into `README.md`): Phase 0–9 roadmap, main functional modules (4.1–4.10), PWA architecture, technical architecture (React/TS/Vite + FastAPI/SQLAlchemy/SQLite + Ollama later), security and access considerations, and the first-usable-version scope.
- Plan updated for the project skeleton direction (separate frontend/backend workspaces, `/api/v1` REST boundary).
