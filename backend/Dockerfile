# Blue Velvet backend image.
# The `dev` target runs uvicorn with --reload for use with Docker Compose binds.
# The `prod` target runs a plain server; migrations run as a deploy step, not
# baked into image startup.

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS base

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies first so they layer-cache independently of source.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project

COPY app ./app

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

FROM base AS dev

CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8080"]

FROM base AS prod

RUN uv sync --frozen --no-install-project --no-dev

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
