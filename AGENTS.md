# AGENTS.md

Instructions for AI coding agents working in this repository.

## What this project is

A self-hosted **Club Operations Platform** for a nightclub: management dashboard, staff mobile interface and promoter submission form, built as one responsive PWA with a local-first backend (FastAPI + SQLite) and a later-read-only local AI assistant.

The full product plan lives in [`PLAN.md`](PLAN.md), which is **gitignored and exists only in the main checkout** (the repository is public; the plan holds the club's business context). If it is missing, say so rather than guessing at product scope. [`README.md`](README.md) is the public developer guide (setup and running). Supporting docs: [`docs/architecture.md`](docs/architecture.md), [`docs/design-system.md`](docs/design-system.md), [`docs/milestones.md`](docs/milestones.md), [`docs/next-steps.md`](docs/next-steps.md), [`docs/google-drive-setup.md`](docs/google-drive-setup.md). Current stage: [`STATUS.md`](STATUS.md). History: [`CHANGE_LOG.md`](CHANGE_LOG.md).

## Current stage — read before writing code

- The repository holds a working **Phase 0.5 invoice review demo**: `frontend/` (React + TypeScript + Vite PWA, pnpm) with login, forced password change, staff management and invoice review; `backend/` (FastAPI, uv) with health, self-managed auth/users and the invoice facade; `invoice-service/` (FastAPI, uv, own SQLite) with drop-folder ingestion, Tesseract OCR, extraction and the review queue. `infra/docker-compose.yml` runs all three in development.
- **Delivered vs. not delivered.** Import from the owner's Google Drive invoice folder (read-only service account; the local inbox `data/inbox/` stands in when Drive is not configured), extraction, review (confirm/correct/reject) and reviewer attribution are implemented; Drive import has not yet been verified against a real folder. **Email ingestion is not planned for Phase 0.5** (owner decision 2026-11-23), **the scheduled catch-up run is not started**, and **the Google Sheets export is a stub** (feature-flagged off; raises when enabled). The digest email can be built but is never sent automatically. Never describe these as delivered in docs or UI copy.
- **Domain language.** Invoice-ingestion terms (capture, suggestion, required fields, needs attention, open, classification) are defined in [`GLOSSARY.md`](GLOSSARY.md); use them in code and docs.
- **Invoice-service auth.** A single internal token (constant-time comparison) plus `X-Reviewer` is the only credential path; the legacy per-user token fallback is removed. The service refuses the known development token outside `INVOICE_ENVIRONMENT=development`, and its dev port is loopback-only. Production must use a unique token and keep `:8081` internal.
- The **Phase 0.5 Invoice Ingestion Quick Win** (PLAN.md §Phase 0.5) is prioritised ahead of Phase 1 by the club owner. Most owner answers are recorded as working assumptions; **credit-note handling and the real sheet's exact tabs/columns/formula columns remain open**. Do not write to the real accounting sheet until that mapping is confirmed (hard rule 3).
- When you add capabilities or change what works, update `docs/next-steps.md`, `STATUS.md` and `CHANGE_LOG.md` in the same change so agent-readable state is never stale. Keep STATUS honest about stubs and pending manual verification.

## Planned stack (do not deviate without discussion)

- **Frontend:** React, TypeScript, Vite, Tailwind CSS (v4), Vite PWA plugin, IndexedDB for offline.
- **Visual design:** follow [`docs/design-system.md`](docs/design-system.md) (derived from the club's sign). Use semantic tokens from `frontend/src/styles/tokens.css` and the primitives in `frontend/src/styles/components.css`; no raw hex values in components; check Night and Day themes.
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic; versioned REST API under `/api/v1/`.
- **Database:** SQLite (FTS5 for keyword search later).
- **Deployment:** Docker Compose; everything self-hosted on club infrastructure.
- **Invoice service (Phase 0.5):** independent Python service — ingestion from one Google Drive folder (Drive API, read-only service account; no email ingestion in Phase 0.5), SQLite record store, review queue, export to Google Sheets API or openpyxl.

## Repository layout

```
frontend/   React + TypeScript + Vite PWA (auth, staff panel, invoice review; no platform modules yet)
backend/    FastAPI backend, /api/v1 (health, auth/users, invoice facade; no domain modules yet)
invoice-service/  Phase 0.5 invoice service (FastAPI + SQLite; Drive invoice folder + local inbox ingestion and review queue wired; Sheets export stubbed; scheduler not started)
infra/      Docker Compose dev stack (Caddy dev HTTPS :443, loopback-only backend :8080, frontend :5173, invoice-service :8081); production overrides to come
factory/    software factory: checks.sh, config, job/gate/route scripts, dashboard (jobs/ is gitignored runtime state)
.claude/    factory orchestrator skill and agents
docs/       architecture, design system, milestones, next steps
README.md   developer guide: what the app is, how to run and test it
PLAN.md     full project plan (single source of product truth; gitignored, local only)
GLOSSARY.md domain language (invoice ingestion so far)
AGENTS.md   this file — conventions and guardrails for agents
STATUS.md   current project status snapshot
CHANGE_LOG.md   chronological change log
```

## Commands

Development (Docker Compose; run from the repository root — this is the primary dev path):

```bash
docker compose -f infra/docker-compose.yml up -d --build   # start backend :8080 + frontend :5173 (hot reload, migrations on startup, SQLite in a named volume) behind Caddy: https://localhost and https://<PUBLIC_HOST> (infra/.env)
docker compose -f infra/docker-compose.yml logs -f         # follow both servers' output
docker compose -f infra/docker-compose.yml exec backend uv run alembic revision --autogenerate -m "<message>"  # new schema revision
docker compose -f infra/docker-compose.yml down            # stop and remove containers (keep the database volume; add -v to wipe it)
pnpm create-owner <username>                               # first owner after a fresh start (stack running; prompts for the password)
pnpm dev-ca                                                # export Caddy's dev root certificate to infra/dev-ca/root.crt (trust it on devices; see infra/README.md)
```

Optional per-service overrides (gitignored; Compose injects them via `env_file`):

```bash
cp backend/.env.example backend/.env
cp invoice-service/.env.example invoice-service/.env
```

Backend (host, without Docker — same check with CI parity; run from `backend/`):

```bash
uv sync                                   # install dependencies (.venv)
uv run uvicorn app.main:app --reload --port 8080
uv run pytest
uv run alembic upgrade head               # apply migrations
uv run alembic revision --autogenerate -m "<message>"  # generate from models
```

Frontend (React + Vite, managed with pnpm; run from `frontend/`):

```bash
pnpm install
pnpm run dev
pnpm run build
```

Fresh checkout (host, no Docker; what a factory worktree needs; run from the
repository root). No `.env` file is required: every setting has a development
default, and the `.env.example` files are only for overrides.

```bash
pnpm install --frozen-lockfile                       # root: Prettier
(cd frontend && pnpm install --frozen-lockfile)
(cd backend && uv sync)
(cd invoice-service && uv sync)
```

Dev server on a given port (host; pages render without the backend, but
anything behind `/api` needs it on :8080 or at `BACKEND_URL`):

```bash
cd frontend && pnpm run dev --port <port> --strictPort
```

Validation (everything CI runs; the same script the factory gate runs):

```bash
bash factory/checks.sh
```

Formatting (one entry point, language-native toolchains; run from the
repository root — CI checks formatting):

```bash
pnpm install
pnpm format          # write formatting: Prettier (TS/JS) + ruff format (both Python services)
pnpm format:check    # verify formatting (same check CI runs; Prettier + ruff)
```

- Prettier covers web formats only (`.ts/.tsx/.js/...`); it never touches Python.
- Python is formatted exclusively with `ruff format` (Black-style, the Python
  standard), declared as a dev dependency in each `pyproject.toml`.
- Both agree on the repo rules: LF, UTF-8, newline at end of file.

## Conventions

- **Language:** user-facing and planning text in English; keep the plan's spelling style (British: "organise", "centralise").
- **Line endings:** LF, UTF-8. Terminate files with a newline.
- **Docs:** keep `PLAN.md`'s section-numbering scheme intact when editing the plan; table-of-contents consistency matters because other docs reference sections (e.g. "4.9 Documents").
- **Git:** small, focused commits; imperative subject lines ("Add invoice review queue"); planning-doc changes in commits separate from code changes.
- **API:** everything backend-facing goes under `/api/v1/`; schemas defined once in Pydantic, never duplicated in the frontend by hand.

## Software factory

`/factory run` builds every open GitHub issue labeled `factory` through
intake → spec → build → gate → review → approve, one PR per issue. State is in
`factory/jobs/` (gitignored); `factory/bin/job` is its only writer. Checks:
`factory/checks.sh`. Dashboard: `cd factory && python3 -m http.server`, then
open http://localhost:8000/dashboard.html.

Each job works in its own git worktree, a full checkout of the repo at
`.worktrees/<job-id>` (gitignored). `factory/bin/job` symlinks the main
checkout's gitignored `PLAN.md` into each new worktree so agents can read the plan. A tool run from the repo root that doesn't
read `.gitignore` sees those copies too; exclude `.worktrees/` in its config.

The factory builds only issues opened by the GitHub user running it, and
passes only that user's comments to its agents; issues and comments from
anyone else are ignored (the repository is public).

The developer running `/factory run` (or `/factory run <n>`) is the explicit
go-ahead hard rule 2 asks for, scoped to the factory: its agents may commit to
and push only their own `factory/<job-id>` branch and open a PR for it, and
merges happen only through `factory/bin/job merge` after the approver
approves. Outside a factory job, hard rule 2 applies unchanged.

## Hard rules — do not violate

1. **Backend is source of truth.** Any extraction, sync or automation output is a *suggestion* until confirmed by a human. Never write unreviewed data into the owner's accounting sheet.
2. **Never commit or push without the developer's permission.** Edits stay in the working tree; creating commits requires an explicit go-ahead in the current session, and pushing (or any remote operation) needs a second, explicit go-ahead. Exception: factory jobs, scoped as described in "Software factory" above. When in doubt, present changes and wait.
3. **The accounting sheet is an output artifact.** Never edit it destructively, never overwrite existing rows, never touch columns that contain formulas.
4. **No real club data in the repo.** Owner/supplier names, invoice contents, mailbox addresses and spreadsheets are confidential (GDPR-relevant). Use fixtures with clearly fake data. Do not commit credentials — the Drive service-account key and any other secrets live outside the repo (e.g. `.env`, `invoice-service/secrets/`, gitignored).
5. **AI stays read-only.** The local AI assistant never approves events, places orders, modifies stock or writes financial records.
6. **Offline data is not authoritative.** Client-side offline queues sync to the backend; the backend validates and resolves duplicates/retries/conflicts.
7. **Document contents are untrusted input.** Parsed files (invoices, riders) must never influence code paths or trigger actions beyond their intended record creation.
8. **Scope discipline.** Phase 0.5 exists to deliver the invoice quick win — do not expand it into the full Finance module. Additions beyond the current phase belong in the plan first.

## Verification before declaring work done

- Planning/docs edits: check internal links between AGENTS.md, STATUS.md, CHANGE_LOG.md, README, PLAN.md and docs/; confirm referenced section numbers exist in PLAN.md. Keep product-plan content out of README.md, which is public.
- Code (once it exists): backend endpoints reachable and honoured by tests; frontend builds; `git status` clean of unintended files (especially data files/env files).
- Update `CHANGE_LOG.md` with every meaningful change; refresh `STATUS.md` when the stage or next step changes.
