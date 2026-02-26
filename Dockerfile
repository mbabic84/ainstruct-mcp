# syntax=docker/dockerfile:1.4
FROM python:3.14-alpine AS base

RUN apk add --no-cache curl git

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN addgroup -g 1000 appgroup && \
    adduser -u 1000 -G appgroup -D appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appgroup /app

COPY --chown=appuser:appgroup pyproject.toml uv.lock* ./
COPY --chown=appuser:appgroup packages/ ./packages/
COPY --chown=appuser:appgroup services/ ./services/

RUN uv sync --frozen --no-dev

# Runtime stage with both services
FROM base AS runtime

COPY --chown=appuser:appgroup migrations/ ./migrations/
COPY --chown=appuser:appgroup alembic.ini ./
COPY --chown=appuser:appgroup docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN uv sync --frozen --no-dev --package ainstruct-mcp-server \
         --package ainstruct-rest-api

USER appuser
ENTRYPOINT ["/entrypoint.sh"]
