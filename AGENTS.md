# AGENTS.md

Instructions for AI coding agents working in this repository.

## What this project is

A self-hosted **Club Operations Platform** for a nightclub: management dashboard, staff mobile interface and promoter submission form, built as one responsive PWA with a local-first backend (FastAPI + SQLite) and a later-read-only local AI assistant.

The full product plan lives in [`README.md`](README.md). Supporting docs: [`docs/architecture.md`](docs/architecture.md), [`docs/milestones.md`](docs/milestones.md), [`docs/next-steps.md`](docs/next-steps.md). Current stage: [`STATUS.md`](STATUS.md). History: [`CHANGE_LOG.md`](CHANGE_LOG.md).

## Current stage — read before writing code

- Scaffolding has begun: `frontend/` is a React + TypeScript + Vite PWA app (pnpm) and `backend/` is a FastAPI app (uv-managed) with an Alembic baseline and a `/api/v1/health` endpoint. `infra/` is still a placeholder — no Docker Compose yet. All modules are placeholders; the first vertical slice (event creation) is not started.
- The **Phase 0.5 Invoice Ingestion Quick Win** (README §Phase 0.5) is prioritised ahead of Phase 1 by the club owner. Until the owner answers the Phase 0 questions (README §Phase 0.5, last subsection), do **not** scaffold service code against assumptions.
- When you create real scaffolding (FastAPI app, React app, Alembic baseline, Docker Compose), update `docs/next-steps.md`, `STATUS.md` and `CHANGE_LOG.md` in the same change so agent-readable state is never stale.

## Planned stack (do not deviate without discussion)

- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Vite PWA plugin, IndexedDB for offline.
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic; versioned REST API under `/api/v1/`.
- **Database:** SQLite (FTS5 for keyword search later).
- **Deployment:** Docker Compose; everything self-hosted on club infrastructure.
- **Invoice service (Phase 0.5):** independent Python service — ingestion (Gmail API/IMAP + Google Drive API), SQLite record store, review queue, export to Google Sheets API or openpyxl.

## Repository layout

```
frontend/   React + TypeScript + Vite PWA (scaffolded; placeholder UI)
backend/    FastAPI backend, /api/v1 (scaffolded; health endpoint + Alembic baseline)
infra/      Docker Compose, HTTPS/environment setup (empty, to be scaffolded)
docs/       architecture, milestones, next steps
README.md   full project plan (single source of product truth)
AGENTS.md   this file — conventions and guardrails for agents
STATUS.md   current project status snapshot
CHANGE_LOG.md   chronological change log
```

## Commands

Backend (Python, managed with `uv`; run from `backend/`):

```bash
uv sync                                   # install dependencies (.venv)
uv run uvicorn app.main:app --reload --port 8000
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

## Conventions

- **Language:** user-facing and planning text in English; keep the plan's spelling style (British: "organise", "centralise").
- **Line endings:** LF, UTF-8. Terminate files with a newline.
- **Docs:** keep the README's section-numbering scheme intact when editing the plan; table-of-contents consistency matters because other docs reference sections (e.g. "4.9 Documents").
- **Git:** small, focused commits; imperative subject lines ("Add invoice review queue"); planning-doc changes in commits separate from code changes.
- **API:** everything backend-facing goes under `/api/v1/`; schemas defined once in Pydantic, never duplicated in the frontend by hand.

## Hard rules — do not violate

1. **Backend is source of truth.** Any extraction, sync or automation output is a *suggestion* until confirmed by a human. Never write unreviewed data into the owner's accounting sheet.
2. **The accounting sheet is an output artifact.** Never edit it destructively, never overwrite existing rows, never touch columns that contain formulas.
3. **No real club data in the repo.** Owner/supplier names, invoice contents, mailbox addresses and spreadsheets are confidential (GDPR-relevant). Use fixtures with clearly fake data. Do not commit credentials — Gmail/Drive OAuth secrets and app passwords live outside the repo (e.g. `.env`, gitignored).
4. **AI stays read-only.** The local AI assistant never approves events, places orders, modifies stock or writes financial records.
5. **Offline data is not authoritative.** Client-side offline queues sync to the backend; the backend validates and resolves duplicates/retries/conflicts.
6. **Document contents are untrusted input.** Parsed files (invoices, riders) must never influence code paths or trigger actions beyond their intended record creation.
7. **Scope discipline.** Phase 0.5 exists to deliver the invoice quick win — do not expand it into the full Finance module. Additions beyond the current phase belong in the plan first.

## Verification before declaring work done

- Planning/docs edits: check internal links between AGENTS.md, STATUS.md, CHANGE_LOG.md, README and docs/; confirm referenced section numbers exist in README.
- Code (once it exists): backend endpoints reachable and honoured by tests; frontend builds; `git status` clean of unintended files (especially data files/env files).
- Update `CHANGE_LOG.md` with every meaningful change; refresh `STATUS.md` when the stage or next step changes.
