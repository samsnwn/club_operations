#!/usr/bin/env bash
# The repo's checks. Exit 0 only when the branch is fit to review.
#
# The gate runs this script from the main checkout with the job's worktree as
# the working directory. Keep it fast, deterministic and non-interactive: no
# watch modes, no prompts, nothing that rewrites files.
#
# Mirrors .github/workflows/ci.yml: formatting, compose validation, lint,
# migrations and tests for both Python services, then frontend lint and build.
set -euo pipefail

# Formatting (Prettier + ruff format, check only)
pnpm install --frozen-lockfile
pnpm format:check

# Compose file parses
docker compose -f infra/docker-compose.yml config --quiet

# Backend
(
  cd backend
  uv sync
  uv run ruff check .
  # Migrations only need to prove the chain applies; no database file left behind.
  DATABASE_URL='sqlite:///:memory:' uv run alembic upgrade head
  uv run pytest --strict-markers --strict-config
)

# Invoice service
(
  cd invoice-service
  uv sync
  uv run ruff check .
  INVOICE_DATABASE_URL='sqlite:///:memory:' uv run alembic upgrade head
  uv run pytest --strict-markers --strict-config
)

# Frontend
(
  cd frontend
  pnpm install --frozen-lockfile
  pnpm run lint
  pnpm run build
)
