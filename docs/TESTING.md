# Testing

## Static Testing Environment

The test environment uses a persistent container with all runtime and dev dependencies pre-installed. Source code is mounted as volumes for fast iteration without rebuilding.

### Start Environment

```bash
# Start all test services (runs once)
docker compose -f docker-compose.test.yml up -d
```

This starts:
- `qdrant` - Vector database
- `mcp_server` - MCP server with test dependencies (persistent container)

## Run Tests

```bash
# Run all tests
docker compose -f docker-compose.test.yml exec mcp_server pytest tests/ -v

# Run specific test directory
docker compose -f docker-compose.test.yml exec mcp_server pytest tests/unit -v

# Run specific test file
docker compose -f docker-compose.test.yml exec mcp_server pytest tests/unit/test_auth.py -v

# Run specific test function
docker compose -f docker-compose.test.yml exec mcp_server pytest tests/unit/test_auth.py::test_function -v

# Run tests matching a pattern
docker compose -f docker-compose.test.yml exec mcp_server pytest -k "test_auth" -v
```

### Lint and Type Check

```bash
# Run linting
docker compose -f docker-compose.test.yml exec mcp_server ruff check src/

# Run type checking
docker compose -f docker-compose.test.yml exec mcp_server mypy src/

# Run both
docker compose -f docker-compose.test.yml exec mcp_server sh -c "ruff check src/ && mypy src/"
```

### Stop Environment

```bash
# Stop all test services
docker compose -f docker-compose.test.yml down
```

## Test Structure

| Directory | Type | Description |
|-----------|------|-------------|
| `tests/unit/` | Unit | Mock-based tests |
| `tests/integration/` | Integration | Migration tests (SQLite) |
| `tests/e2e/` | E2E | Live MCP protocol tests (requires Qdrant) |

## Cleanup

```bash
docker compose -f docker-compose.test.yml down -v
```
