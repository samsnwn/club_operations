# Infra — how the Blue Velvet platform is deployed

Everything is self-hosted on club infrastructure (README §technical architecture).
This directory owns Docker Compose definitions for both development and, later,
production.

## Development (current)

Compose file: `docker-compose.yml` (project name `blue-velvet`).

    docker compose -f infra/docker-compose.yml up -d --build   # start all three services
    docker compose -f infra/docker-compose.yml logs -f         # follow output
    docker compose -f infra/docker-compose.yml down            # stop + remove containers (keep the database volume)

All three services build from `dev` targets of their Dockerfiles.

### Environment and secrets

Each service loads an optional, gitignored `.env` through Compose `env_file`:

    cp backend/.env.example backend/.env
    cp invoice-service/.env.example invoice-service/.env

Neither file is required (`required: false`): without them the services use
development-safe defaults. When present they carry overrides such as the shared
service token, SMTP credentials and cookie/origin settings.
`backend/.env` `INVOICE_SERVICE_TOKEN` must equal `invoice-service/.env`
`INVOICE_INTERNAL_TOKEN`; the token is deliberately **not** hard-coded in the
compose file. The `.env` files are read on the host and injected into the
containers — they are never bind-mounted or committed.

The dev compose explicitly sets `INVOICE_ENVIRONMENT=development` for the
invoice service and publishes it on `127.0.0.1:8081` only. Production must set
`INVOICE_ENVIRONMENT=production` with a unique `INVOICE_INTERNAL_TOKEN` (the
service refuses to start with the known development default) and must not
publish `:8081` at all.

| Service | Build context | Port | Binds (hot reload) | Volumes |
| --- | --- | --- | --- | --- |
| `backend` | `backend/Dockerfile` — uv-based, `alembic upgrade head` runs at start | `:8080` | `app/`, `tests/`, `alembic/`, `pyproject.toml`, `uv.lock` | `db-data:/data` (SQLite) |
| `frontend` | `frontend/Dockerfile` — node:22 + pinned `pnpm@9.12.0` (corepack activate) | `:5173` | `src/`, `public/`, `index.html`, configs | `frontend-vite-cache` (Vite pre-bundle cache) |
| `invoice-service` | `invoice-service/Dockerfile` — uv-based + Tesseract, `alembic upgrade head` runs at start | `127.0.0.1:8081` (development only) | `app/`, `tests/`, `alembic/`, `pyproject.toml`, `uv.lock` | `invoice-data:/app/data` (SQLite + originals); `data/inbox` bind for the demo |

Wiring: the browser talks only to `:5173` for the PWA and to `:8080` for the
API (the Vite dev-server proxy, configured via `BACKEND_URL`, default
`http://localhost:8080` on the host, `http://backend:8080` in compose, forwards
`/api/*` same-origin). The invoice service is called only by the backend facade
on the compose network. No CORS middleware is needed in dev.

Data discipline:

- SQLite lives in the `db-data` named volume, **never** a host bind — the
  database is not a shared file or a sink for external writes.
- `docker compose ... down -v` **wipes the database volume**; `down` alone
  keeps it. Treat `down -v` as a fresh-install action, not a debugging step.
- Real club data stays out of the repository (AGENTS.md hard rule 4); the
  accounting sheet is an output artifact and nothing in the stack writes to it
  until the export is deliberately enabled against a confirmed column mapping
  (hard rule 3).
- The invoice service's store and captured originals live in the
  `invoice-data` volume, never a host bind. Its `:8081` port is published only
  for development; production must keep it internal because its token bypasses
  facade authentication.

Check parity with CI: tests, lint and formatting run the same commands on the
host (`uv run pytest`, `pnpm lint`, `pnpm format:check`) or on the bind-mounted
sources inside the containers (`docker compose ... exec backend uv run pytest`).
Use one or the other consistently — never edit inside a container.

Rebuild only when dependencies or Dockerfiles change (`up -d --build`); plain
`up -d` reuses the built image. Source edits need no rebuild — both servers
hot-reload from the binds. Frontend dependencies come from the image, not a
named volume, so a rebuild always picks up lockfile changes; the Vite cache
volume only stores regenerable pre-bundle output.

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
- Production packaging and network policy for the Phase 0.5 invoice service:
  it already runs as its own container in development, but production must not
  publish `:8081`, and the scheduler/single-run lock still needs a home.
- Whether a scheduled worker container runs the nightly invoice catch-up and
  digest, or an import is triggered manually (interim plan A).
- File-storage volume layout for uploaded documents (invoices, riders) once
  document workflow arrives.
