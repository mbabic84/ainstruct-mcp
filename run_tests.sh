#!/bin/bash
set -e

echo "=== Building test base image ==="
docker build -f Dockerfile.test-base -t ainstruct-test-base .

echo "=== Running linting and unit tests ==="
docker run --rm \
    --mount type=bind,source="$(pwd)"/src,target=/app/src \
    --mount type=bind,source="$(pwd)"/tests,target=/app/tests \
    --mount type=bind,source="$(pwd)"/pyproject.toml,target=/app/pyproject.toml \
    --mount type=bind,source="$(pwd)"/alembic.ini,target=/app/alembic.ini \
    --mount type=bind,source="$(pwd)"/migrations,target=/app/migrations \
    -w /app \
    -e PYTHONPATH=/app \
    -e USE_MOCK_EMBEDDINGS=true \
    ainstruct-test-base \
    sh -c "ruff check src/ && mypy src/ && pytest tests/unit tests/integration -v"

echo "=== All tests passed ==="
