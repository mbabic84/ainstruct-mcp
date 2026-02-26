# syntax=docker/dockerfile:1.4

FROM python:3.14-alpine

RUN apk add --no-cache curl

WORKDIR /app

RUN addgroup -g 1000 appgroup && \
    adduser -u 1000 -G appgroup -D appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appgroup /app/data

ENV PYTHONPATH=/app/src

COPY --chown=appuser:appgroup pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -e .

COPY --chown=appuser:appgroup entrypoint.sh /app/entrypoint.sh

COPY --chown=appuser:appgroup src/ ./src/

COPY --chown=appuser:appgroup alembic.ini .
COPY --chown=appuser:appgroup migrations/ ./migrations/

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["--mcp"]
