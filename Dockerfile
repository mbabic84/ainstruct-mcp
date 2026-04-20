# syntax=docker/dockerfile:1.4
FROM python:3.14-alpine AS base

RUN apk add --no-cache curl git

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN addgroup -g 1000 appgroup && \
    adduser -u 1000 -G appgroup -D appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appgroup /app

# Copy dependency files FIRST (for cache efficiency)
COPY --chown=appuser:appgroup pyproject.toml uv.lock* ./

# Install dependencies using cache mount (reuses uv cache across builds)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Copy source code AFTER dependencies (cached unless dependencies change)
COPY --chown=appuser:appgroup packages/ ./packages/
COPY --chown=appuser:appgroup services/ ./services/

# Runtime stage - inherits everything from base, no extra installs needed
FROM base AS runtime

COPY --chown=appuser:appgroup migrations/ ./migrations/
COPY --chown=appuser:appgroup alembic.ini ./
COPY --chown=appuser:appgroup docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER appuser
ENTRYPOINT ["/entrypoint.sh"]
