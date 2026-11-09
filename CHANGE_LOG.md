# CHANGE_LOG

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project currently has no runtime releases, so entries are dated by change.

## [2026-11-09]

### Added
- Invoice-service startup security guard: the service now refuses to start
  with an empty internal token, or with the known development token outside
  `INVOICE_ENVIRONMENT=development`. The environment defaults to `production`,
  so an unconfigured deployment fails closed instead of inheriting the public
  default. Token checks use `secrets.compare_digest`.
- Five invoice-service tests cover the startup guards, the removed legacy
  token path and unknown bearer tokens.

### Changed
- Development compose binds the invoice service to `127.0.0.1:8081` instead of
  all host interfaces, and explicitly sets `INVOICE_ENVIRONMENT=development`.
  The service README, infra README, backend README, architecture doc and
  `.env.example` files document the production token/environment requirements.
- CI now lints both Python services with `ruff check`, validates the compose
  file with `docker compose config --quiet`, and applies the invoice-service
  Alembic chain (`alembic upgrade head` against an in-memory SQLite URL) before
  running its tests. Previously CI enforced Python formatting only, and
  invoice-service migration drift or a broken compose file could pass
  unnoticed.
- `frontend/README.md` replaced the Vite template boilerplate with
  project-specific instructions (dev servers, API proxy, auth and invoice
  review flows, build/lint commands).
- Documentation refresh to separate delivered functionality from stubs:
  `AGENTS.md` current stage, `STATUS.md`, `docs/next-steps.md` and the invoice
  service README now state explicitly that Drive/Gmail ingestion, the scheduled
  catch-up run, automatic digest sending and the Sheets export are not
  implemented. The manual drop-folder → review → confirm flow is described as
  the current, working demo.
- `backend/README.md` documents the auth/user routes, roles, CLI bootstrap and
  invoice facade, which were missing.

### Removed
- The legacy per-user `INVOICE_REVIEW_TOKENS` bearer-token fallback in the
  invoice service. The internal service token plus `X-Reviewer` is now the only
  credential path; the old environment variable is ignored.

### Fixed
- `STATUS.md` no longer claims the internal-authentication work is uncommitted
  (it was committed on 2026-11-06), and its test counts now match the suites
  (46 backend, 26 invoice service).
- `docs/next-steps.md` no longer implies the invoice service has automatic
  ingestion; the remaining Phase 0.5 work is listed explicitly.
- `infra/README.md` now describes all three dev services (including the invoice
  service and its volumes), corrects the browser/API wiring description, and
  reflects that the invoice service port is development-only.
- Hard-rule references in code comments and docs now match the numbering in
  `AGENTS.md` (accounting sheet = rule 3, no real club data/credentials = rule
  4, untrusted document contents = rule 7). Historical CHANGE_LOG entries were
  left unchanged.

### Verified
- API-level smoke pass against temporary host SQLite databases (Docker was
  unavailable): both `/api/v1/health` checks, owner CLI bootstrap and login,
  cross-origin rejection, staff creation, forced staff password change,
  drop-folder fixture import, confirm-with-corrections with
  `reviewed_by=smoke-owner`, duplicate-confirm `409`, staff invoice-role
  `403`, and logout session invalidation. A browser-level pass on the Docker
  stack remains pending.

Application runtime behaviour changed only for invoice-service authentication
hardening (startup guard, loopback-only dev binding, legacy token removal);
there are no schema or database migration changes in this entry.

## [2026-11-06]

### Fixed
- Backend invoice facade queue: the merged `"all"` view was sorted ascending
  by confidence — the reverse of the invoice service's own order ("confident
  captures first") and inconsistent with the single-status path of the same
  endpoint. It now mirrors the service ordering exactly (confidence
  descending, oldest first within a confidence tie).
- Invoice-service drop-folder ingestion (`data/inbox/`) hardened against the
  realistic demonstration race: a file that is still being written (mid-copy
  into the folder) is normally not ingested truncated. A file is captured
  once observed with an unchanged size and modification time twice, or once
  untouched for longer than a short settle window (`SETTLE_SECONDS = 5`).
  This is best-effort, not a guarantee: a copy that stalls between polls, or
  one whose modification time is preserved by the producer (`cp -p`, `rsync`,
  `unzip`), can still be captured mid-flight and produce a second row when it
  completes (documented in the module's known-limitation note). A file copied
  less than the settle window before an Import click is withheld until a
  later poll. Hidden files (`.DS_Store` etc.) and subdirectories are never
  captured, files above `INVOICE_MAX_ATTACHMENT_BYTES` are skipped before
  being read into memory, and files that vanish between stat and read are
  tolerated (warned and skipped). The per-directory-and-size-limit source
  instance is reused between import calls so its observed state survives
  across Import clicks.

### Removed
- Unused `poll_fixture_source()` helper from the ingestion pipeline (no
  caller; the test path builds its sources directly).

### Added
- Per-service environment templates: `backend/.env.example` and
  `invoice-service/.env.example` document every supported setting with
  development-safe defaults and note the token that must match between the
  two services. Both READMEs gained an Environment section. The root
  `.gitignore` now re-includes `.env.example` while still ignoring real
  `.env` files.
- Internal authentication for the platform: `User` and `AuthSession` models
  with an Alembic migration (`5ea31f09edc2`), Argon2id password hashing,
  opaque database-backed sessions (only the SHA-256 token hash is stored) in
  an HttpOnly, `SameSite=Lax` cookie, and an Origin-check middleware for
  state-changing requests. Auth routes: `POST /api/v1/auth/login`,
  `POST /api/v1/auth/logout`, `GET /api/v1/auth/me`,
  `POST /api/v1/auth/password`. Dependencies `authenticated_user` (any active
  session), `current_user` (blocks `must_change_password` with `403`) and
  `require_role(...)`.
- CLI `python -m app.cli create-user` / `reset-password` (`backend/app/cli.py`)
  for first-owner bootstrap and password recovery; no environment auto-seeding.
- Account-management API under `/api/v1/users` (list, create, patch, reset
  password): owners manage every account, admins manage `staff` only, no one
  changes their own role or deactivates themselves, and the last active owner
  cannot be removed or demoted. Role changes, deactivation and password resets
  revoke existing sessions.
- Frontend authentication flow: `api.ts` (typed fetch + `ApiError`), `auth.ts`
  (typed auth/user calls), `Login.tsx`, `ChangePassword.tsx` (forced and
  voluntary), `StaffPanel.tsx` (create accounts, change roles, activate/
  deactivate, reset passwords) and `InvoiceWorkspace.tsx` (existing review UI
  extracted). `App.tsx` restores the session on load, enforces the first-sign-in
  password change, exposes role-aware navigation, and returns to the login
  screen on session expiry.
- Invoice-service reviewer attribution: confirm/reject record `reviewed_by`
  from `X-Reviewer` **only** when the request also carries a valid internal
  token; token-only calls remain attributed to `backend`. The backend facade
  derives the header from the authenticated session.
- Backend tests for auth, account management, CLI and facade identity
  forwarding (`test_auth.py`, `test_users.py`, `test_cli.py`,
  `test_invoices_facade.py`, including staff denial and admin access on every
  invoice route) plus a shared `tests/conftest.py`.
- Backend facade tests (`backend/tests/test_invoices_facade.py`) exercising
  the real HTTP behaviour via `httpx.MockTransport` through a `_client()` test
  seam: merged-queue ordering (including confidence ties), status pass-through,
  internal-token forwarding, import route mapping, 503 on an unreachable
  service, upstream error-status pass-through, and inline streaming of the
  original attachment.
- Invoice-service tests: drop-folder settle rules (`tests/test_drop_folder.py`
  — partial-write race, hidden/non-file entries, double-observation capture,
  size skip) and internal endpoint coverage (`/internal/invoices/import`
  requiring the internal token + hash dedupe, `/internal/invoices/{id}/original`
  serving stored captures with sniffed media type, 401/404 paths, and the
  internal-token reviewer contract).

### Changed
- `infra/docker-compose.yml`: removed the redundant `frontend-node-modules`
  named volume. Frontend dependencies now come from the image (so
  `up --build` picks up lockfile changes without a stale volume shadowing
  them); only the regenerable Vite pre-bundle cache remains volume-backed.
  `infra/README.md` documents the change.
- `infra/docker-compose.yml`: the shared invoice-service token is no longer
  hard-coded. Both services load an optional, gitignored per-service `.env`
  through Compose `env_file` (`backend/.env`, `invoice-service/.env`), keeping
  the token and other overrides out of the compose file. `infra/README.md` and
  `AGENTS.md` document the copy step and the matching-token requirement.
- Invoice routes are now authenticated and role-gated: every frontend call
  goes through the backend facade, which requires an owner or admin
  (`require_role("owner", "admin")`) and forwards that user's username to the
  invoice service as `X-Reviewer`, ignoring any client-supplied header. Staff
  accounts receive `403` on every `/api/v1/invoices/*` route, and the frontend
  hides invoice navigation from them. Direct service calls still work with the
  internal token but are attributed to `backend`. The invoice service (`:8081`)
  must therefore stay internal-only.
- README §Phase 0.5 documents the implemented internal authentication,
  roles and production requirements; `docs/architecture.md` gains an
  authentication/trust-boundary section; `invoice-service/README.md` documents
  the `X-Reviewer` contract; `docs/next-steps.md` marks the authentication item
  done.
- `frontend/src/App.tsx`: queue loading runs through a single `useCallback`
  `loadQueue()` instead of a duplicated inline fetch in the mount effect, and
  the header button label reflects actual import runs only (a dedicated
  `importing` state instead of sharing the generic busy flag).

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
- Phase 0.5 unblocked: owner's working assumptions recorded in README §Phase 0.5 (Drive sheet, local Tesseract OCR — no cloud OCR, assumed v1 column set, owner and admin reviewers, email digest with review instructions; credit-note handling still open). Interim hosting = plan A: on-demand runs with watermark catch-up, upgrading to dedicated hardware without rework.
- Phase 0.5 `invoice-service/` scaffolded (uv, FastAPI on :8081, own SQLite via SQLAlchemy 2.0 with Alembic baseline): pull-based ingestion with per-source sync watermarks (Drive and Gmail adapters degrade cleanly until credentials live outside the repo; a fixture source feeds the pipeline with deliberately fake club data), content-hash de-duplication, text-layer routing (PDF text layer → plain UTF-8 → else Tesseract OCR), field extraction as suggestions with per-field confidence, first-pass trust statuses (`pending_review` / `needs_attention`), review queue API (`/api/v1/queue` list/get/confirm-with-corrections/reject) with per-user bearer tokens for owner and admin, collapsed digest notifier (SMTP-configurable with log-only fallback), and Google Sheets export behind the `INVOICE_EXPORT_ENABLED=false` feature flag until the column mapping is confirmed against the real sheet (hard rule 2). Runs as `invoice-service` in the dev compose (Tesseract baked into its image, invoice store and files in named volumes); 6/6 tests pass (health, catch-up + dedupe, needs-attention handling, auth, review flow, digest).

- Ruff (Black-style formatter) added as a dev dependency to both Python services (`backend/`, `invoice-service/`); the root `pnpm format` / `pnpm format:check` scripts now run Prettier **and** `ruff format` in one command, giving the repo a single unified formatting entry point while keeping language-native toolchains (Prettier has no Python parser, and the community's output standard for Python is Black-style, so a Prettier plugin would fight the Python ecosystem). First pass reformatted 10 Python files; backend and invoice-service test suites still green.

### Changed
- Added a gitignored local drop folder at `invoice-service/data/inbox/` for
  real-invoice demonstrations. The import flow now reads new PDFs/images from
  that folder, stores originals in the invoice volume, and previews them in
  the review screen.
- Completed the invoice review UI: the queue includes both pending and
  attention-needed items, and reviewers can inspect extracted text, correct
  fields, confirm invoices, or reject them through the backend facade.
- Fixed the invoice-service Alembic baseline by adding the missing invoice and
  sync-watermark tables, allowing the Docker startup migration to create the
  schema before the proxy serves requests.
- Added the first invoice-focused application slice: the frontend calls a thin
  backend invoice facade, which proxies to the separate invoice service using
  an internal development token. The frontend supports importing, the review
  queue with extracted-text inspection, confirming/correcting, and rejecting
  invoices; end-user authentication and role permissions remain next steps.
- `frontend/vite.config.ts`: Vite proxy target now reads `BACKEND_URL` (defaults to `http://localhost:8080` on the host; docker compose sets `http://backend:8080`), so the same config wires same-origin `/api` requests correctly on host and in Docker. The proxy forwards to `http://localhost:8000` initially (no path rewrite; backend routes already start with `/api`); no CORS middleware needed in dev.
- `AGENTS.md` Command section reorganised: Docker Compose dev commands are now the primary documented dev path (`up -d --build` / `logs -f` / in-container `alembic revision` / `down`), with the host `uv` workflow kept below for CI-parity checks.
- Backend dev port moved from `8000` to `8080` (`uvicorn --port 8080`, `backend/README.md`, `AGENTS.md`, frontend Vite proxy target): OpenCode's built-in vLLM provider discovery probes `http://127.0.0.1:8000/v1` by default, which spammed the dev server with `/health` + `/v1/models` requests. The temporary 404-logging diagnostic middleware was removed again; port `8080` is outside OpenCode's local-discovery defaults.
- `app/main.py`: added (then removed) a root-level `/health` alias — it masked 404 spam from the OpenCode vLLM discovery probe while the backend sat on port 8000; the port move to 8080 made the alias unnecessary, and only the canonical `/api/v1/health` remains.
- `invoice-service/app/ingestion/pipeline.py`: `_status_for()` now returns `"needs_attention"` when average extraction confidence is below 0.5 (in addition to zero extracted fields), so low-confidence captures surface distinctly in the review queue instead of grouping with confident `pending_review` items.
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
