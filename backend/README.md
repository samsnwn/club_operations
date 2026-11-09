# Blue Velvet Backend

FastAPI backend exposing the versioned REST API under `/api/v1/`. SQLite for
storage, SQLAlchemy 2.0 ORM, Alembic for migrations. Managed with `uv`.

## Setup

```bash
uv sync            # create .venv and install dependencies
```

## Run

```bash
uv run uvicorn app.main:app --reload --port 8080
```

Interactive API docs: `http://localhost:8080/docs`.

## API surface

- `/api/v1/health` — service + database round-trip.
- `/api/v1/auth/*` — `login`, `logout`, `me`, `password`.
- `/api/v1/users` — account management (owner manages everyone; admin manages
  `staff`; no self-registration).
- `/api/v1/invoices/*` — thin facade over the independent invoice service.
  Owner/admin only; the browser never talks to the invoice service directly.

## Accounts and roles

Accounts are created by an administrator inside the app; there is no public
registration. The first owner is bootstrapped from the CLI (the password is
prompted for, or read from `NEW_USER_PASSWORD`):

```bash
uv run python -m app.cli create-user --username owner --role owner
uv run python -m app.cli reset-password --username owner
```

Roles are `owner` (manages every account), `admin` (manages `staff` accounts)
and `staff` (sign-in and own password only). Administrator-created and reset
accounts must change their password at first sign-in. Sessions are opaque
HttpOnly cookies; only their SHA-256 hash is stored.

## Migrations

```bash
uv run alembic upgrade head                              # apply
uv run alembic revision --autogenerate -m "<message>"    # generate from models
```

The database URL comes from `app.core.config` (`DATABASE_URL` env var overrides
the SQLite default). The SQLite file (`blue_velvet.db`) is gitignored — real
club data lives only outside the repo.

## Environment

Every setting has a development-safe default, so a `.env` is optional locally.
To override anything, copy `.env.example` to `.env` in this directory (the
service loads `.env` from its working directory) and edit it. `INVOICE_SERVICE_TOKEN`
must match the invoice service's `INVOICE_INTERNAL_TOKEN`, and must be a unique
secret outside development — the invoice service refuses to start with the
known development default in production. Never commit `.env`.

## Tests

```bash
uv run pytest
```
