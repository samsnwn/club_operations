# Club Operations Platform

A self-hosted operations platform for a nightclub, built as one responsive PWA
with a local-first backend. The current release is an **invoice review
workflow**: invoices are imported from a Google Drive folder (or a local inbox
folder in development), their fields are extracted as suggestions, and an owner
or admin confirms, corrects or rejects each one. It also includes internal
sign-in and staff-account management.

Not implemented yet: export to the accounting sheet (feature-flagged off),
scheduled imports, automatic digest emails, and the wider platform modules
(events, dashboard, inventory, promoter form).

## Stack

| Part | Path | Tech |
| --- | --- | --- |
| Frontend | [`frontend/`](frontend/README.md) | React, TypeScript, Vite, Tailwind CSS v4, PWA (pnpm) |
| Backend | [`backend/`](backend/README.md) | FastAPI, SQLAlchemy, Alembic, SQLite (uv); API under `/api/v1/` |
| Invoice service | [`invoice-service/`](invoice-service/README.md) | FastAPI, SQLite, Tesseract OCR, Google Drive API (uv) |
| Infra | [`infra/`](infra/README.md) | Docker Compose dev stack behind Caddy (dev HTTPS) |

The frontend talks only to the backend; the backend forwards invoice calls to
the invoice service, which is internal-only.

## Requirements

- Docker with Compose (recommended path), or for running on the host:
- Node 22 and pnpm 9 (`corepack enable`)
- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Tesseract (only for OCR of scanned invoices on the host; the Docker image
  includes it)

## Quick start (Docker)

From the repository root:

```bash
pnpm install                 # root tooling (Prettier)
pnpm dev:up                  # build and start all services; migrations run on startup
pnpm create-owner <username> # first account (prompts for a password, min. 12 characters)
```

Then open https://localhost (Caddy's local certificate) or
http://localhost:5173 and sign in. Create further accounts from the Staff tab.

| Service | Address |
| --- | --- |
| App (HTTPS, via Caddy) | https://localhost |
| Frontend (Vite) | http://localhost:5173 |
| Backend | http://localhost:8080 (loopback only) |
| Invoice service | http://localhost:8081 (loopback only) |

Other commands:

```bash
pnpm dev:logs    # follow output
pnpm dev:down    # stop (keeps the databases)
pnpm dev:clean   # stop and wipe the databases
pnpm migrate     # apply new migrations to a running stack
pnpm dev-ca      # export the dev root certificate to trust it on a phone
```

To try the invoice flow without Google Drive, drop PDF or image files into
`invoice-service/data/inbox/` and click **Import invoices** in the invoices view.
Testing on a phone over the LAN is covered in
[`infra/README.md`](infra/README.md#https-for-phones-dev).

## Running on the host (without Docker)

No `.env` file is needed: every setting has a development default.

```bash
pnpm install --frozen-lockfile
(cd frontend && pnpm install --frozen-lockfile)
(cd backend && uv sync)
(cd invoice-service && uv sync)

# each in its own terminal
(cd backend && uv run alembic upgrade head && uv run uvicorn app.main:app --reload --port 8080)
(cd invoice-service && uv run alembic upgrade head && uv run uvicorn app.main:app --reload --port 8081)
(cd frontend && pnpm run dev)
```

Create the first owner with
`(cd backend && uv run python -m app.cli create-user --role owner --username <username>)`.

## Configuration

Each service reads an optional, gitignored `.env`; copy the example to
override defaults:

```bash
cp backend/.env.example backend/.env
cp invoice-service/.env.example invoice-service/.env
cp infra/.env.example infra/.env   # optional LAN address for phones
```

The backend's `INVOICE_SERVICE_TOKEN` must match the invoice service's
`INVOICE_INTERNAL_TOKEN`. The development default is refused outside
`INVOICE_ENVIRONMENT=development`, so set a unique token anywhere else.
Connecting a real Google Drive folder is described in
[`docs/google-drive-setup.md`](docs/google-drive-setup.md). Never commit
`.env` files, service-account keys or real invoices.

## Tests and checks

```bash
pnpm test            # backend + invoice-service pytest
pnpm lint            # ESLint + ruff
pnpm format          # Prettier (TS/JS) + ruff format (Python)
bash factory/checks.sh  # everything CI runs
```

## Further documentation

- [`docs/architecture.md`](docs/architecture.md): how the services fit together
- [`docs/design-system.md`](docs/design-system.md): visual design tokens and components
- [`GLOSSARY.md`](GLOSSARY.md): domain terms for invoice ingestion
- [`STATUS.md`](STATUS.md) and [`CHANGE_LOG.md`](CHANGE_LOG.md): current state and history
- [`AGENTS.md`](AGENTS.md): conventions for contributors and coding agents
