# CHANGE_LOG

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project currently has no runtime releases, so entries are dated by change.

## [2026-11-05]

### Added
- `vite-plugin-pwa` registered as a dev dependency in `frontend/` (pnpm).

### Changed
- `frontend/vite.config.ts`: `VitePWA` plugin configured — `autoUpdate` service-worker registration and a Web App manifest (`name`: "Blue Velvet", `short_name`: "Velvet").
- Frontend TypeScript pinned to `~5.9.3` (down from the template's `~7.0.2`): `typescript-eslint` 8.x does not support TS 7, so `pnpm run lint` failed. Both `lint` and `build` pass on 5.9.3.

### Added
- FastAPI backend scaffold in `backend/` (uv-managed, Python ≥3.12): app factory, versioned router under `/api/v1/`, health endpoint with a SQLite round-trip check (SQLAlchemy 2.0), pydantic-settings config (`.env` gitignored), pytest suite, `backend/README.md`.
- Alembic migrations wired to application settings via `app.core.config`; empty baseline migration created and applied.
- CI: single workflow `.github/workflows/ci.yml` running everything as one sequential job with a concurrency group (same shape as the owner's NotAnotherCards CI): root `pnpm format:check`, backend (`uv sync` → `uv run alembic upgrade head` → `uv run pytest`), frontend (`pnpm install --frozen-lockfile` → `pnpm run lint` → `pnpm run build`). Runs on every push to `main` and every PR; replaces the earlier separate backend/frontend workflows (also merged the second formatting-only job into CI).
- Frontend TypeScript pinned to `~5.9.3` (from the template's `~7.0.2`); `typescript-eslint` currently supports TS < 6.1, so lint was failing on the template pin. Revisit when typescript-eslint adds TS 7 support.

- Prettier formatting added at the repository root, mirroring the owner's NotAnotherCards project: `.prettierrc` (`singleQuote`, `trailingComma: "all"`) and `.prettierignore`; root `pnpm format` / `pnpm format:check` scripts over `**/*.{ts,tsx,mts,mjs,js,cjs,cts}`; template TS files reformatted; formatting check as a CI job in `frontend.yml`.

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
