# CHANGE_LOG

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project currently has no runtime releases, so entries are dated by change.

## [2026-11-05]

### Added
- `vite-plugin-pwa` registered as a dev dependency in `frontend/` (pnpm).
- FastAPI backend scaffold in `backend/` (uv-managed, Python ≥3.12): app factory, versioned router under `/api/v1/`, health endpoint with a SQLite round-trip check (SQLAlchemy 2.0), pydantic-settings config (`.env` gitignored), pytest suite, `backend/README.md`; `backend/app/.gitkeep` removed.
- Alembic migrations wired to application settings via `app.core.config`; empty baseline migration created and applied.
- Single CI workflow `.github/workflows/ci.yml` — lint, format, test and build as one sequential job with a concurrency group, same shape as the owner's NotAnotherCards CI: root `pnpm format:check`, backend (`uv sync` → `uv run alembic upgrade head` → `uv run pytest`), frontend (`pnpm install --frozen-lockfile` → `pnpm run lint` → `pnpm run build`). Runs on every push to `main` and every PR; replaced the earlier separate `backend.yml`/`frontend.yml` workflows.
- Prettier formatting at the repository root, mirroring NotAnotherCards: `.prettierrc` (`singleQuote`, `trailingComma: "all"`), `.prettierignore`, root `pnpm format` / `pnpm format:check` scripts over `**/*.{ts,tsx,mts,mjs,js,cjs,cts}`, committed root `pnpm-lock.yaml`; the four template TS files were reformatted.
- Root `.gitignore` covering `node_modules/`, env files and OS artifacts (previously only `backend/` and `frontend/` had ignores).

### Changed
- `frontend/vite.config.ts`: `VitePWA` plugin configured — `autoUpdate` service-worker registration and a Web App manifest (`name`: "Blue Velvet", `short_name`: "Velvet").
- `frontend/vite.config.ts`: dev-server proxy added — same-origin `/api` requests are forwarded to `http://localhost:8000` (no path rewrite; backend routes already start with `/api`). No CORS middleware needed in dev.
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
