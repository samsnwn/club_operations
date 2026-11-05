# Infra — how the Blue Velvet platform is deployed

Everything is self-hosted on club infrastructure (README §technical architecture).
This directory owns Docker Compose definitions for both development and, later,
production.

## Development (current)

Compose file: `docker-compose.yml` (project name `blue-velvet`).

    docker compose -f infra/docker-compose.yml up -d --build   # start both services
    docker compose -f infra/docker-compose.yml logs -f         # follow output
    docker compose -f infra/docker-compose.yml down            # stop + remove containers (keep the database volume)

Both services build from `dev` targets of their Dockerfiles.

| Service | Build context | Port | Binds (hot reload) | Volumes |
| --- | --- | --- | --- | --- |
| `backend` | `backend/Dockerfile` — uv-based, `alembic upgrade head` runs at start | `:8080` | `app/`, `tests/`, `alembic/`, `pyproject.toml`, `uv.lock` | `db-data:/data` (SQLite) |
| `frontend` | `frontend/Dockerfile` — node:22 + pinned `pnpm@9.12.0` (corepack activate) | `:5173` | `src/`, `public/`, `index.html`, configs | `frontend-node-modules`, `frontend-vite-cache` |

Wiring: the browser talks only to `:5173`; the Vite dev-server proxy
(configured via `BACKEND_URL`, default `http://localhost:8080` on the host,
`http://backend:8080` in compose) forwards `/api/*` same-origin to the
backend. No CORS middleware is needed in dev.

Data discipline:

- SQLite lives in the `db-data` named volume, **never** a host bind — the
  database is not a shared file or a sink for external writes.
- `docker compose ... down -v` **wipes the database volume**; `down` alone
  keeps it. Treat `down -v` as a fresh-install action, not a debugging step.
- Real club data stays out of the repository (AGENTS.md hard rule 3); the
  accounting sheet is an output artifact and nothing in the stack ever gets
  write access to it (hard rule 1).

Check parity with CI: tests, lint and formatting run the same commands on the
host (`uv run pytest`, `pnpm lint`, `pnpm format:check`) or on the bind-mounted
sources inside the containers (`docker compose ... exec backend uv run pytest`).
Use one or the other consistently — never edit inside a container.

Rebuild only when dependencies or Dockerfiles change (`up -d --build`); plain
`up -d` reuses the built image. Source edits need no rebuild — both servers
hot-reload from the binds.

## Production (planned — not wired yet)

Reuse of the same images at `prod` targets is the roadmap:

1. **`docker-compose.production.yml`** override file (same repo pattern as the
   owner's NotAnotherCards project): `prod` build targets, restart policies,
   healthchecks against `/api/v1/health`, pinned image digests, no source
   binds.
2. **Backend prod target**: dependencies baked via
   `uv sync --frozen --no-dev`; plain uvicorn, no reload.
3. **Frontend prod target**: static PWA build (`pnpm run build`) baked into
   the image; content served by the reverse proxy, not by node.
4. **Single origin with HTTPS at the edge**: a reverse proxy (Caddy or nginx —
   both supported, decision open) terminates TLS and serves the PWA plus
   `/api/*` from one origin. This replaces the Vite dev proxy entirely; there
   is no `api.example.com` split origin.
5. **Migrations as a deploy step, not image startup**: production deployment
   runs `alembic upgrade head` before the new server takes traffic, so schema
   and code change together and a failed migration never strands the old
   server (backend-is-source-of-truth discipline hardens once real booking
   tables exist).
6. **Backups**: scheduled export or file-level copy of the SQLite volume.
   Redis/Postgres-style stores can arrive later without changing this pattern.

Open decisions, gated on the Phase 0 owner answers (README §Phase 0):

- Host runtime: Docker Desktop vs Linux daemon on club hardware (affects the
  production compose details only).
- Reverse proxy choice (Caddy vs nginx) and HTTPS scheme: LAN-only vs public
  domain. If club data must never leave the building, a public domain is out.
- Whether the Phase 0.5 invoice service ships as its own container in the same
  compose network (planned: independent FastAPI service, same patterns,
  separate runtime).
- File-storage volume layout for uploaded documents (invoices, riders) once
  document workflow arrives.
