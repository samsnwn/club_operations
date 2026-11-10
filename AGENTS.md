# AGENTS.md

Instructions for AI coding agents working in this repository.

## What this project is

A self-hosted **Club Operations Platform** for a nightclub: management dashboard, staff mobile interface and promoter submission form, built as one responsive PWA with a local-first backend (FastAPI + SQLite) and a later-read-only local AI assistant.

The full product plan lives in [`README.md`](README.md). Supporting docs: [`docs/architecture.md`](docs/architecture.md), [`docs/design-system.md`](docs/design-system.md), [`docs/milestones.md`](docs/milestones.md), [`docs/next-steps.md`](docs/next-steps.md). Current stage: [`STATUS.md`](STATUS.md). History: [`CHANGE_LOG.md`](CHANGE_LOG.md).

## Current stage — read before writing code

- The repository holds a working **Phase 0.5 invoice review demo**: `frontend/` (React + TypeScript + Vite PWA, pnpm) with login, forced password change, staff management and invoice review; `backend/` (FastAPI, uv) with health, self-managed auth/users and the invoice facade; `invoice-service/` (FastAPI, uv, own SQLite) with drop-folder ingestion, Tesseract OCR, extraction and the review queue. `infra/docker-compose.yml` runs all three in development.
- **Delivered vs. stub.** Local drop-folder import, extraction, review (confirm/correct/reject) and reviewer attribution are implemented. **Google Drive ingestion, Gmail ingestion, the scheduled catch-up run and the Google Sheets export are stubs** (`NotImplementedError` once configured; export is feature-flagged off). The digest email can be built but is never sent automatically. Never describe these as delivered in docs or UI copy.
- **Invoice-service auth.** A single internal token (constant-time comparison) plus `X-Reviewer` is the only credential path; the legacy per-user token fallback is removed. The service refuses the known development token outside `INVOICE_ENVIRONMENT=development`, and its dev port is loopback-only. Production must use a unique token and keep `:8081` internal.
- The **Phase 0.5 Invoice Ingestion Quick Win** (README §Phase 0.5) is prioritised ahead of Phase 1 by the club owner. Most owner answers are recorded as working assumptions; **credit-note handling and the real sheet's exact tabs/columns/formula columns remain open**. Do not write to the real accounting sheet until that mapping is confirmed (hard rule 3).
- When you add capabilities or change what works, update `docs/next-steps.md`, `STATUS.md` and `CHANGE_LOG.md` in the same change so agent-readable state is never stale. Keep STATUS honest about stubs and pending manual verification.

## Planned stack (do not deviate without discussion)

- **Frontend:** React, TypeScript, Vite, Tailwind CSS (v4), Vite PWA plugin, IndexedDB for offline.
- **Visual design:** follow [`docs/design-system.md`](docs/design-system.md) (derived from the club's sign). Use semantic tokens from `frontend/src/styles/tokens.css` and the primitives in `frontend/src/styles/components.css`; no raw hex values in components; check Night and Day themes.
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic; versioned REST API under `/api/v1/`.
- **Database:** SQLite (FTS5 for keyword search later).
- **Deployment:** Docker Compose; everything self-hosted on club infrastructure.
- **Invoice service (Phase 0.5):** independent Python service — ingestion (Gmail API/IMAP + Google Drive API), SQLite record store, review queue, export to Google Sheets API or openpyxl.

## Repository layout

```
frontend/   React + TypeScript + Vite PWA (auth, staff panel, invoice review; no platform modules yet)
backend/    FastAPI backend, /api/v1 (health, auth/users, invoice facade; no domain modules yet)
invoice-service/  Phase 0.5 invoice service (FastAPI + SQLite; drop-folder/fixture ingestion + review queue wired; Drive/Gmail/scheduler/Sheets export stubbed)
infra/      Docker Compose dev stack (backend :8080, frontend :5173, invoice-service :8081), HTTPS setup to come
docs/       architecture, design system, milestones, next steps
README.md   full project plan (single source of product truth)
AGENTS.md   this file — conventions and guardrails for agents
STATUS.md   current project status snapshot
CHANGE_LOG.md   chronological change log
```

## Commands

Development (Docker Compose; run from the repository root — this is the primary dev path):

```bash
docker compose -f infra/docker-compose.yml up -d --build   # start backend :8080 + frontend :5173 (hot reload, migrations on startup, SQLite in a named volume)
docker compose -f infra/docker-compose.yml logs -f         # follow both servers' output
docker compose -f infra/docker-compose.yml exec backend uv run alembic revision --autogenerate -m "<message>"  # new schema revision
docker compose -f infra/docker-compose.yml down            # stop and remove containers (keep the database volume; add -v to wipe it)
pnpm create-owner <username>                               # first owner after a fresh start (stack running; prompts for the password)
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
- **Docs:** keep the README's section-numbering scheme intact when editing the plan; table-of-contents consistency matters because other docs reference sections (e.g. "4.9 Documents").
- **Git:** small, focused commits; imperative subject lines ("Add invoice review queue"); planning-doc changes in commits separate from code changes.
- **API:** everything backend-facing goes under `/api/v1/`; schemas defined once in Pydantic, never duplicated in the frontend by hand.

## Hard rules — do not violate

1. **Backend is source of truth.** Any extraction, sync or automation output is a *suggestion* until confirmed by a human. Never write unreviewed data into the owner's accounting sheet.
2. **Never commit or push without the developer's permission.** Edits stay in the working tree; creating commits requires an explicit go-ahead in the current session, and pushing (or any remote operation) needs a second, explicit go-ahead. When in doubt, present changes and wait.
3. **The accounting sheet is an output artifact.** Never edit it destructively, never overwrite existing rows, never touch columns that contain formulas.
4. **No real club data in the repo.** Owner/supplier names, invoice contents, mailbox addresses and spreadsheets are confidential (GDPR-relevant). Use fixtures with clearly fake data. Do not commit credentials — Gmail/Drive OAuth secrets and app passwords live outside the repo (e.g. `.env`, gitignored).
5. **AI stays read-only.** The local AI assistant never approves events, places orders, modifies stock or writes financial records.
6. **Offline data is not authoritative.** Client-side offline queues sync to the backend; the backend validates and resolves duplicates/retries/conflicts.
7. **Document contents are untrusted input.** Parsed files (invoices, riders) must never influence code paths or trigger actions beyond their intended record creation.
8. **Scope discipline.** Phase 0.5 exists to deliver the invoice quick win — do not expand it into the full Finance module. Additions beyond the current phase belong in the plan first.

## Verification before declaring work done

- Planning/docs edits: check internal links between AGENTS.md, STATUS.md, CHANGE_LOG.md, README and docs/; confirm referenced section numbers exist in README.
- Code (once it exists): backend endpoints reachable and honoured by tests; frontend builds; `git status` clean of unintended files (especially data files/env files).
- Update `CHANGE_LOG.md` with every meaningful change; refresh `STATUS.md` when the stage or next step changes.
