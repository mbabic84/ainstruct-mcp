# Testing

## Quick Start

```bash
# Run all tests and cleanup (always runs cleanup)
docker compose up --abort-on-container-exit --exit-code-from test_runner; docker compose down

# Or detached (manual cleanup)
docker compose up -d test_runner
docker compose logs -f test_runner
docker compose down
```

## Run Specific Tests

```bash
# Unit tests only
docker compose run --rm test_runner pytest tests/unit -v

# Specific test file
docker compose run --rm test_runner pytest tests/unit/test_auth.py -v

# Specific function
docker compose run --rm test_runner pytest tests/unit/test_auth.py::test_function -v

# Pattern match
docker compose run --rm test_runner pytest -k "test_auth" -v
```

## Lint and Type Check

```bash
docker compose run --rm test_runner sh -c "ruff check src/ && mypy src/"
```

## Test Structure

| Directory | Type | Description | External Services |
|-----------|------|-------------|-------------------|
| `tests/unit/` | Unit | Mock-based tests | None |
| `tests/integration/` | Integration | Migration tests (SQLite) | None |
| `tests/e2e/` | E2E | Live MCP protocol tests | Qdrant |

## Cleanup

```bash
# Remove everything
docker compose down -v

# Remove including test data
docker compose down -v --rmi local
```

## Why This Approach?

1. **One command**: `docker compose up --abort-on-container-exit`
2. **No profiles**: Simple service list, no flags needed
3. **Auto-cleanup**: `--abort-on-container-exit` stops qdrant when tests finish
4. **Fast iteration**: Source mounted as volumes, no rebuild
5. **CI-friendly**: `docker compose up --abort-on-container-exit --exit-code-from test_runner`
