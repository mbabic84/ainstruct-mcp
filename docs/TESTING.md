# Testing

## Run All Tests

```bash
docker compose --profile test up test_runner
```

This starts:
- `qdrant` - Vector database
- `mcp_server` - MCP server
- `test_runner` - Runs linting, type checking, and all tests (unit + integration + e2e)

## Run Specific Tests

```bash
# Unit tests only
docker compose run --rm test_runner pytest tests/unit -v

# Specific test file
docker compose run --rm test_runner pytest tests/unit/test_auth.py -v

# Specific test
docker compose run --rm test_runner pytest tests/unit/test_auth.py::test_function -v
```

## Lint and Type Check

```bash
docker compose run --rm test_runner sh -c "ruff check src/ && mypy src/"
```

## Test Structure

| Directory | Type | Description |
|-----------|------|-------------|
| `tests/unit/` | Unit | Mock-based tests |
| `tests/integration/` | Integration | Migration tests (SQLite) |
| `tests/e2e/` | E2E | Live MCP protocol tests (requires Qdrant) |

## Cleanup

```bash
docker compose --profile test down -v
```
