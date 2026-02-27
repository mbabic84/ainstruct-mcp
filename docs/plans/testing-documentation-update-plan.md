# Testing Documentation Update Plan

## Executive Summary

Update the testing documentation to reflect the current uv-based workflow. The existing documentation describes Docker-based testing, but the actual workflow now uses `uv` directly with `--frozen` flags for reproducible builds.

---

## Current State Analysis

| File | Status | Issues |
|------|--------|--------|
| `README.md` (lines 366-378) | Outdated | References non-existent `docs/TESTING.md` and `docs/DEVELOPMENT.md` |
| `docs/TESTING.md` | **Missing** | Referenced in README but doesn't exist |
| `docs/DEVELOPMENT.md` | **Missing** | Referenced in README but doesn't exist |
| `.kilocode/rules/testing.md` | **Outdated** | Describes Docker-based testing, but actual workflow uses `uv` directly |
| `scripts/test.sh` | Current | Uses `uv sync --all-packages --frozen` and `uv run --frozen` |
| `.github/workflows/test.yml` | Needs review | Missing `--frozen` flags for consistency |

---

## Key Changes to Document

### The `--frozen` Flag

The `--frozen` flag ensures reproducible builds by using exact versions from `uv.lock`:

| Command | Purpose |
|---------|---------|
| `uv sync --all-packages --frozen` | Install dependencies from lockfile only (no updates) |
| `uv run --frozen <command>` | Run command with frozen dependencies |

Use `--frozen` for CI and testing scripts. Omit `--frozen` when you need to update dependencies.

---

## Proposed Changes

### 1. Create `docs/TESTING.md`

New comprehensive testing guide:

```markdown
# Testing Guide

## Prerequisites
- uv package manager installed
- Python 3.14+

## Running Tests

### Full Test Suite (lint, typecheck, test)
./scripts/test.sh

### Individual Commands
uv sync --all-packages --frozen              # Install dependencies (frozen)
uv run --frozen ruff check packages/ services/ tests/   # Linting
uv run --frozen mypy packages/ services/     # Type checking
uv run --frozen pytest tests/ -v             # Run all tests

### Run Specific Tests
uv run --frozen pytest tests/unit/ -v                    # Unit tests only
uv run --frozen pytest tests/unit/shared/ -v             # Shared package tests
uv run --frozen pytest tests/unit/mcp/ -v                # MCP server tests
uv run --frozen pytest tests/unit/rest/ -v              # REST API tests
uv run --frozen pytest tests/unit/test_file.py::test_fn -v  # Specific test

### Development (unfrozen)
If you need to update dependencies, omit --frozen:
uv sync --all-packages
uv run pytest tests/ -v

## Test Structure
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── shared/              # ainstruct-shared tests
│   ├── mcp/                 # ainstruct-mcp-server tests
│   └── rest/                # ainstruct-rest-api tests
├── integration/             # Integration tests
└── e2e/                     # End-to-end tests

## Test Fixtures (tests/conftest.py)
- mock_settings - Environment variables for testing
- mock_qdrant - Mock Qdrant vector store
- sample_user_data - Test user data
- sample_collection_data - Test collection data
- sample_document_data - Test document data
- sample_chunk_data - Test chunk data

## Environment Variables for Testing
- USE_MOCK_EMBEDDINGS=true - Use deterministic vectors (no API calls)
- JWT_SECRET_KEY=test-secret-key - JWT signing for tests

## CI/CD Integration
Tests run automatically on pull requests to main branch.
See .github/workflows/test.yml

## Writing New Tests
- Place tests in appropriate directory under tests/unit/, tests/integration/, or tests/e2e/
- Use existing fixtures from tests/conftest.py
- Follow naming convention: test_<module>.py
- Run linting before committing: uv run --frozen ruff check tests/
```

### 2. Update `.kilocode/rules/testing.md`

Replace Docker-based instructions with uv workflow. Key changes:

| Old (Remove) | New (Add) |
|--------------|-----------|
| Docker-based testing | uv-based testing |
| `docker compose --profile test run test_runner` | `./scripts/test.sh` or `uv run --frozen pytest tests/` |
| Pre-built test container concept | Direct uv usage |

### 3. Update `README.md` (lines 366-378)

Fix broken references:

```markdown
## Development

### Testing
```bash
./scripts/test.sh
```
Runs linting, type checking, and tests using uv.

For more details, see [Testing Guide](./docs/TESTING.md).
```

### 4. Update `.github/workflows/test.yml` (Optional)

Consider adding `--frozen` flags for consistency:

```yaml
# Current
- run: uv sync --all-packages
- run: uv run ruff check packages/ services/ tests/
- run: uv run mypy packages/ services/
- run: uv run pytest tests/ -v

# With --frozen (optional)
- run: uv sync --all-packages --frozen
- run: uv run --frozen ruff check packages/ services/ tests/
- run: uv run --frozen mypy packages/ services/
- run: uv run --frozen pytest tests/ -v
```

---

## Implementation Priority

| Priority | File | Action |
|----------|------|--------|
| 1 | `docs/TESTING.md` | Create new file |
| 2 | `.kilocode/rules/testing.md` | Update to use uv workflow |
| 3 | `README.md` | Fix broken references |
| 4 | `.github/workflows/test.yml` | Consider adding --frozen (optional) |
| 5 | `docs/DEVELOPMENT.md` | Create if needed (low priority) |

---

## Files Summary

| File | Current State | After Change |
|------|---------------|--------------|
| `docs/TESTING.md` | Does not exist | Created with uv workflow documentation |
| `.kilocode/rules/testing.md` | Describes Docker testing | Updated to describe uv workflow |
| `README.md` | Broken references | Fixed to point to docs/TESTING.md |
| `.github/workflows/test.yml` | No --frozen flags | Optionally updated for consistency |
