# Testing Guide

## Prerequisites

- uv package manager installed
- Python 3.14+

## Running Tests

### Full Test Suite (lint, typecheck, test)

```bash
./scripts/test.sh
```

### Individual Commands

```bash
uv sync --all-packages --frozen              # Install dependencies (frozen)
uv run --frozen ruff check packages/ services/ tests/   # Linting
uv run --frozen mypy packages/ services/     # Type checking
uv run --frozen pytest tests/ -v             # Run all tests
```

### Run Specific Tests

```bash
uv run --frozen pytest tests/unit/ -v                    # Unit tests only
uv run --frozen pytest tests/unit/shared/ -v             # Shared package tests
uv run --frozen pytest tests/unit/mcp/ -v                # MCP server tests
uv run --frozen pytest tests/unit/rest/ -v              # REST API tests
uv run --frozen pytest tests/unit/test_file.py::test_fn -v  # Specific test
```

### Development (unfrozen)

If you need to update dependencies, omit `--frozen`:

```bash
uv sync --all-packages
uv run pytest tests/ -v
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── shared/              # ainstruct-shared tests
│   ├── mcp/                 # ainstruct-mcp-server tests
│   └── rest/                # ainstruct-rest-api tests
├── integration/             # Integration tests
└── e2e/                     # End-to-end tests
```

## Test Fixtures (tests/conftest.py)

- mock_settings - Environment variables for testing
- mock_qdrant - Mock Qdrant vector store
- sample_user_data - Test user data
- sample_collection_data - Test collection data
- sample_document_data - Test document data
- sample_chunk_data - Test chunk data

## Environment Variables for Testing

- `USE_MOCK_EMBEDDINGS=true` - Use deterministic vectors (no API calls)
- `JWT_SECRET_KEY=test-secret-key` - JWT signing for tests

## The `--frozen` Flag

The `--frozen` flag ensures reproducible builds by using exact versions from `uv.lock`:

| Command | Purpose |
|---------|---------|
| `uv sync --all-packages --frozen` | Install dependencies from lockfile only (no updates) |
| `uv run --frozen <command>` | Run command with frozen dependencies |

Use `--frozen` for CI and testing scripts. Omit `--frozen` when you need to update dependencies.

## CI/CD Integration

Tests run automatically on pull requests to main branch.
See `.github/workflows/test.yml`.

## Writing New Tests

- Place tests in appropriate directory under `tests/unit/`, `tests/integration/`, or `tests/e2e/`
- Use existing fixtures from `tests/conftest.py`
- Follow naming convention: `test_<module>.py`
- Run linting before committing: `uv run --frozen ruff check tests/`
