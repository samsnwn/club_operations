# Initial Architecture Skeleton

This repository uses a modular-monolith direction with separate frontend and backend workspaces.

## Planned top-level structure

- `frontend/` — React + TypeScript + Vite PWA
- `backend/` — FastAPI backend (`/api/v1`)
- `infra/` — deployment and environment scaffolding (Docker Compose, HTTPS setup)
- `docs/` — product, architecture, milestones, and implementation notes

## Data and integration direction

- Backend is source of truth for operational data.
- Offline actions (especially stock counts) are queued client-side and synchronised to backend.
- AI assistant is read-only and references source records/documents.
