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
must match the invoice service's `INVOICE_INTERNAL_TOKEN`. Never commit `.env`.

## Tests

```bash
uv run pytest
```
