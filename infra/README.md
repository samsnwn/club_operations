# Infra — how the Blue Velvet platform is deployed

Everything is self-hosted on club infrastructure (PLAN.md §5 Technical Architecture).
This directory owns Docker Compose definitions for both development and, later,
production.

## Development (current)

Compose file: `docker-compose.yml` (project name `blue-velvet`).

    docker compose -f infra/docker-compose.yml up -d --build   # start all services
    docker compose -f infra/docker-compose.yml logs -f         # follow output
    docker compose -f infra/docker-compose.yml down            # stop + remove containers (keep the database volume)

The three application services build from `dev` targets of their Dockerfiles;
`proxy` runs the pinned upstream Caddy image.

### Fresh start (after `down -v`)

1. `docker compose -f infra/docker-compose.yml up -d --build` — both Python
   services run `alembic upgrade head` on startup, so no manual migration is
   needed.
2. `pnpm create-owner <username>` (repository root) — the wiped database has no
   accounts and there is no public registration. Prompts twice for a password
   (min. 12 characters).
3. Sign in at https://localhost (or http://localhost:5173); create further
   accounts from the Staff tab.

Migrations need a manual run only when a new revision arrives while the stack
is already running: `pnpm migrate` (or restart the two Python services).

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
| `proxy` | image `caddy:2.11.9`, config `infra/Caddyfile` (`tls internal`) | `:443` (HTTPS), `:80` (redirects to HTTPS) | `Caddyfile` (read-only) | `caddy-data:/data` (local CA + certificates), `caddy-config:/config` |
| `backend` | `backend/Dockerfile` — uv-based, `alembic upgrade head` runs at start; uvicorn `--proxy-headers --forwarded-allow-ips='*'` | `127.0.0.1:8080` | `app/`, `tests/`, `alembic/`, `pyproject.toml`, `uv.lock` | `db-data:/data` (SQLite) |
| `frontend` | `frontend/Dockerfile` — node:22 + pinned `pnpm@9.12.0` (corepack activate) | `127.0.0.1:5173` | `src/`, `public/`, `index.html`, configs | `frontend-vite-cache` (Vite pre-bundle cache) |
| `invoice-service` | `invoice-service/Dockerfile` — uv-based + Tesseract, `alembic upgrade head` runs at start | `127.0.0.1:8081` (development only) | `app/`, `tests/`, `alembic/`, `pyproject.toml`, `uv.lock` | `invoice-data:/app/data` (SQLite + originals); `data/inbox` bind for the demo |

Wiring: phones and other LAN devices reach the stack only through Caddy on
`:443` (`https://localhost`, `https://<PUBLIC_HOST>`); plain HTTP on `:80`
redirects to HTTPS. Caddy sends `/api/*` straight to `backend:8080` and
everything else, including the Vite HMR WebSocket, to `frontend:5173`. The
backend and Vite ports are published on loopback only, which is why uvicorn may
trust `X-Forwarded-*` from any peer: only Caddy and the host itself can reach
it. On the host, `http://localhost:5173` still works as before: the Vite
dev-server proxy (configured via `BACKEND_URL`, default `http://localhost:8080`
on the host, `http://backend:8080` in compose) forwards `/api/*` same-origin.
The invoice service is called only by the backend facade on the compose
network. No CORS middleware is needed in dev.

Known dev limitation: behind Docker Desktop (macOS) Caddy may see the Docker
NAT gateway instead of the phone's address, so the per-address sign-in throttle
can treat every LAN client as one address.

### HTTPS for phones (dev)

Service workers and PWA install need a secure origin, so phones use Caddy's
HTTPS. Verified on an iPhone (2026-11-26): the app installs to the home screen
and opens full-screen. Android is not verified yet.

1. Set `PUBLIC_HOST` (optional; without it only `https://localhost` is
   served):

       cp infra/.env.example infra/.env   # then set PUBLIC_HOST=<this machine's LAN IP>

   Use the LAN IP (for example `192.168.1.50`), not a `.local` name: Android
   resolves `.local` names unreliably. After changing it, run
   `docker compose -f infra/docker-compose.yml up -d` to recreate `proxy` and
   `frontend`.
2. Start the stack (`pnpm dev:up`), then export Caddy's root certificate from
   the repository root:

       pnpm dev-ca   # writes infra/dev-ca/root.crt (gitignored)

3. Trust `infra/dev-ca/root.crt` on each device:
   - **macOS:** open it in Keychain Access, add it to the System keychain and
     set it to Always Trust, or run
     `sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain infra/dev-ca/root.crt`.
   - **iOS:** send the file to the device (AirDrop or mail), install the
     downloaded profile under Settings, then turn on full trust under
     Settings → General → About → Certificate Trust Settings.
   - **Android:** install it as a CA certificate under Settings → Security
     (or Encryption & credentials) → Install a certificate → CA certificate.
4. Open `https://<PUBLIC_HOST>` on the phone and sign in.
5. Install it:
   - **iOS:** use **Safari** (Brave and other browsers on iOS don't offer a
     proper install). Share → Add to Home Screen → Add; on iOS 26 the Share
     button sits behind the ⋯ button next to the address bar.
   - **Android:** Chrome menu → Add to Home screen / Install app.

Bare IP addresses carry no TLS SNI, so the Caddyfile sets `default_sni` to
`PUBLIC_HOST`; without it the handshake to `https://<LAN IP>` fails with an
internal-error alert while `https://localhost` still works.

The certificate authority lives in the `caddy-data` volume, so it survives
`down`/`up` and restarts. `pnpm dev:clean` (`down -v`) wipes it: Caddy creates a
new authority on the next start, and every device must re-trust the new root
(run `pnpm dev-ca` again). `SESSION_COOKIE_SECURE` stays false in dev.

A real domain later means swapping `tls internal` for a DNS-01 issuer in
`infra/Caddyfile` only; nothing else in the stack changes.

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
4. **Single origin with HTTPS at the edge**: a reverse proxy terminates TLS
   and serves the PWA plus `/api/*` from one origin. Dev already does this
   with Caddy and `tls internal`; the production proxy (Caddy or nginx) and
   certificate scheme are still open. This replaces the Vite dev proxy entirely; there
   is no `api.example.com` split origin.
5. **Migrations as a deploy step, not image startup**: production deployment
   runs `alembic upgrade head` before the new server takes traffic, so schema
   and code change together and a failed migration never strands the old
   server (backend-is-source-of-truth discipline hardens once real booking
   tables exist).
6. **Backups**: scheduled export or file-level copy of the SQLite volume.
   Redis/Postgres-style stores can arrive later without changing this pattern.

### Runbook: account bootstrap and recovery

The account CLI (`backend/app/cli.py`) is not an HTTP endpoint; it runs only
from a shell on the host with access to the Docker daemon. That host access
**is** the security boundary: anyone who has it can already read the SQLite
volume and the `.env` secrets, so the CLI adds no new exposure. Protect the
host, not the command:

- Shell access only for the operators (owner + technical admin), SSH keys
  only, no password login. Docker group membership is root-equivalent — grant
  it to nobody else.
- Only the reverse proxy is published; `:8080` and `:8081` stay internal.

`pnpm create-owner` is a development shortcut (it targets the dev compose file
and needs Node on the host). On the production host, call the CLI directly in
the `prod` image (the virtualenv is on `PATH`, no `uv` needed). The production
override file below is still planned; adjust the `-f` flags once it exists.

**First install** (once, after migrations have run):

    docker compose -f infra/docker-compose.yml -f infra/docker-compose.production.yml \
      exec backend python -m app.cli create-user --username <owner> --role owner

The password is prompted twice without echo (min. 12 characters). Do not pass
it through `NEW_USER_PASSWORD` on a production host — it would land in shell
history or process listings. Every further account (admins, staff) is created
in the app's Staff tab, never with the CLI.

**Owner locked out / forgotten password:**

    docker compose -f infra/docker-compose.yml -f infra/docker-compose.production.yml \
      exec backend python -m app.cli reset-password --username <owner>

This revokes every session of that account and forces a new password at the
next sign-in.

**Suspected compromise:** reset the affected account's password as above,
deactivate unknown accounts in the Staff tab (deactivation revokes their
sessions), review the account list for owners you did not create, and rotate
`INVOICE_SERVICE_TOKEN` / `INVOICE_INTERNAL_TOKEN` if host access is in doubt.

Open decisions, gated on the Phase 0 owner answers (PLAN.md §Phase 0):

- Host runtime: Docker Desktop vs Linux daemon on club hardware (affects the
  production compose details only).
- Production reverse proxy (dev uses Caddy; Caddy vs nginx for production is
  open) and HTTPS scheme: LAN-only vs public domain. If club data must never leave the building, a public domain is out.
- Production packaging and network policy for the Phase 0.5 invoice service:
  it already runs as its own container in development, but production must not
  publish `:8081`, and the scheduler/single-run lock still needs a home.
- Whether a scheduled worker container runs the nightly invoice catch-up and
  digest, or an import is triggered manually (interim).
- File-storage volume layout for uploaded documents (invoices, riders) once
  document workflow arrives.
