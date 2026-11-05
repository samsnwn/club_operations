# Phase 0.5 — Invoice Ingestion service image.
# Dev target: source bind-mounted, uvicorn --reload, Tesseract available for
# the photo/scan share (~50% per owner answer #3).
# Prod target: same, without reload — the migrate step runs before serving.

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS base

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-deu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project

COPY app ./app

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8081

FROM base AS dev

CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8081"]

FROM base AS prod

RUN uv sync --frozen --no-install-project --no-dev

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
