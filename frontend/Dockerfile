# Blue Velvet frontend image.
# The `dev` target runs the Vite dev server (needed for the PWA dev workflow).
# The `prod` target builds static assets; serving happens in the reverse proxy.

FROM node:22-slim AS base

WORKDIR /app

COPY package.json pnpm-lock.yaml ./

RUN corepack enable \
    && corepack prepare pnpm@9.12.0 --activate

RUN pnpm install --frozen-lockfile

FROM base AS dev

COPY . .

EXPOSE 5173

CMD ["pnpm", "run", "dev", "--host"]

FROM base AS prod

COPY . .

RUN pnpm run build
