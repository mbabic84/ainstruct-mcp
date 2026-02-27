#!/bin/bash
set -e

echo "=== Running linting, type checking and tests ==="
uv sync --all-packages --frozen
uv run --frozen ruff check packages/ services/ tests/
uv run --frozen mypy packages/ services/
uv run --frozen pytest tests/ -v

echo "=== All tests passed ==="
