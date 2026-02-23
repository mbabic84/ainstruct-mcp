# Testing the AI Document Memory MCP Server

This guide explains how to run tests locally, matching the GitHub Actions workflow.

## Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)

## Test Structure

```
tests/
├── unit/              # Mock-based tests, no external dependencies
├── integration/       # Database tests (SQLite, migrations)
├── e2e/               # End-to-end tests (requires Qdrant)
└── __init__.py
```

| Phase | What it runs | Requirements |
|-------|--------------|--------------|
| **Lint & Unit + Integration** | Ruff, MyPy, 104 unit + 9 migration tests | Docker only |
| **E2E** | 9 live MCP protocol tests | Docker Compose with Qdrant |

## Quick Start

### Run All Tests (Same as CI)

```bash
# 1. Lint, unit, and integration tests
docker build -f Dockerfile.test -t ainstruct-test .
docker run --rm ainstruct-test

# 2. E2E tests
cat > .env << 'EOF'
API_KEYS=test_key_123
ADMIN_API_KEY=admin_secret_key
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
QDRANT_URL=http://qdrant:6333
DATABASE_URL=sqlite:///./data/mcp_server.db
EOF

docker compose --profile test up --build --abort-on-container-exit
```

### Run Specific Test Phase

**Lint, Unit, and Integration Tests:**

```bash
docker build -f Dockerfile.test -t ainstruct-test .
docker run --rm ainstruct-test
```

This runs:
- `ruff check src/` - Code linting
- `mypy src/` - Type checking
- `pytest tests/unit tests/integration -v` - 104 unit + 9 migration tests

**E2E Tests Only:**

```bash
# Create test environment
cat > .env << 'EOF'
API_KEYS=test_key_123
ADMIN_API_KEY=admin_secret_key
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
QDRANT_URL=http://qdrant:6333
DATABASE_URL=sqlite:///./data/mcp_server.db
EOF

docker compose --profile test up --build --abort-on-container-exit
```

This starts:
- `qdrant` - Vector database
- `mcp_server_test` - MCP server (ephemeral, no volume mount)
- `mcp_client_test` - Test client running live protocol tests

## Test Files Reference

| Directory | Type | Description |
|-----------|------|-------------|
| `tests/unit/` | Unit | Mock-based tests (104 tests) |
| `tests/integration/` | Integration | Migration tests with real SQLite (9 tests) |
| `tests/e2e/` | E2E | Live MCP protocol tests (9 tests) |

## Advanced Usage

### Run Local Development Server

For local development with persistent storage:

```bash
docker compose up -d
```

This starts `mcp_server` with volume mount (`./data:/app/data`) on port 8001.

### Run Tests Against Local Server

```bash
# Start development server
docker compose up -d

# Run tests locally against it
export MCP_SERVER_URL=http://localhost:8001/mcp
pip install fastmcp>=3.0.0 httpx pytest pytest-asyncio
pytest tests/e2e/mcp_live_test.py -v
```

## Troubleshooting

### Database Errors in E2E Tests

```
sqlite3.OperationalError: unable to open database file
```

This error occurs when running `docker compose up` instead of `docker compose --profile test up`. The E2E tests use `mcp_server_test` which has no volume mount, avoiding permission issues.

**Solution:** Always use `--profile test` for E2E tests:
```bash
docker compose --profile test up --build --abort-on-container-exit
```

### Authentication Errors

```
Missing or invalid Authorization header
```

- Ensure `.env` file has `API_KEYS=test_key_123`
- For JWT auth, pass the access token: `auth=access_token`
- For API key auth, pass the key: `auth="test_key_123"`

### Connection Refused

```
Connection refused / All connection attempts failed
```

- Wait for server to be ready (takes a few seconds)
- Check containers are running: `docker compose ps`
- Verify network connectivity: `docker compose logs mcp_server_test`

### Clean Up After Tests

```bash
# Stop all containers
docker compose --profile test down

# Remove volumes (fresh state)
docker compose --profile test down -v
```

## CI/CD Reference

The GitHub Actions workflow (`.github/workflows/test.yml`) runs two jobs:

**Job 1: lint-and-unit**
```yaml
- docker build -f Dockerfile.test -t ainstruct-test .
- docker run --rm ainstruct-test
```

**Job 2: integration** (runs after lint-and-unit passes)
```yaml
- cat > .env << EOF
    API_KEYS=test_key_123
    ADMIN_API_KEY=admin_secret_key
    JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
    QDRANT_URL=http://qdrant:6333
    DATABASE_URL=sqlite:///./data/mcp_server.db
    EOF
- docker compose --profile test up --build --abort-on-container-exit
```

## See Also

- [API Reference](./API_REFERENCE.md) - Full API documentation
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment
- [Architecture](./ARCHITECTURE.md) - System architecture overview
