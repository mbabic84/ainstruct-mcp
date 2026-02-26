#!/bin/bash
set -e

echo "=== Running linting, type checking and tests ==="
uv sync --all-packages
uv run ruff check packages/ services/ tests/
uv run mypy packages/ services/
uv run pytest tests/ -v

echo "=== All tests passed ==="
