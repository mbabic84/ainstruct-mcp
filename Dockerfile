FROM python:3.14-alpine

RUN apk add --no-cache curl

WORKDIR /app

RUN addgroup -g 1000 appgroup && \
    adduser -u 1000 -G appgroup -D appuser && \
    mkdir -p /app/data

ENV PYTHONPATH=/app/src

COPY --chown=appuser:appgroup pyproject.toml .

RUN pip install --no-cache-dir -e .

USER appuser

COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup alembic.ini .
COPY --chown=appuser:appgroup migrations/ ./migrations/

EXPOSE 8000

CMD ["python", "-m", "app.main"]
