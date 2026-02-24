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
| **Lint & Unit + Integration** | Ruff, MyPy, 113 tests | Docker only |
| **E2E** | 14 live MCP protocol tests | Docker Compose with Qdrant |

## Quick Start

### Run All Tests (Same as CI)

**Option 1: Using the test script (recommended)**
```bash
./run_tests.sh
```

**Option 2: Manual steps**
```bash
# 1. Lint, unit, and integration tests
docker build -f Dockerfile.test-base -t ainstruct-test-base .
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
# Build base image once (installs dependencies only)
docker build -f Dockerfile.test-base -t ainstruct-test-base .

# Run with volume mounts (code changes reflected immediately)
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
```

This runs:
- `ruff check src/` - Code linting
- `mypy src/` - Type checking
- `pytest tests/unit tests/integration -v` - 113 tests

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

## Development Workflow (Recommended)

For rapid iteration during development, use the `test_runner` service with volume mounts. This allows you to edit code locally and immediately run tests without rebuilding the container.

```bash
# Build the test base image once
docker build -f Dockerfile.test-base -t ainstruct-test-base .

# Run tests with volume mounts (code changes reflected immediately)
docker compose run --rm test_runner

# Run specific test file
docker compose run --rm -e PYTHONPATH=/app test_runner pytest tests/unit/test_auth.py -v

# Run specific test
docker compose run --rm -e PYTHONPATH=/app test_runner pytest tests/unit/test_auth.py::TestUserProfile::test_profile_success -v

# Run with linting
docker compose run --rm -e PYTHONPATH=/app test_runner ruff check src/

# Run with type checking
docker compose run --rm -e PYTHONPATH=/app test_runner mypy src/

# Run all three (lint + type check + tests)
docker compose run --rm -e PYTHONPATH=/app test_runner sh -c "ruff check src/ && mypy src/ && pytest tests/unit tests/integration -v"
```

The `test_runner` service mounts:
- `./src:/app/src` - Source code
- `./tests:/app/tests` - Test files
- `./pyproject.toml:/app/pyproject.toml` - Project config
- `./alembic.ini:/app/alembic.ini` - Alembic config
- `./migrations:/app/migrations` - Database migrations

### Using docker-compose.yml test_runner Service

The `test_runner` service is defined in `docker-compose.yml` with the `test` profile:

```yaml
test_runner:
  build:
    context: .
    dockerfile: Dockerfile.test-base
  volumes:
    - ./src:/app/src
    - ./tests:/app/tests
    - ./pyproject.toml:/app/pyproject.toml
    - ./alembic.ini:/app/alembic.ini
    - ./migrations:/app/migrations
  environment:
    - PYTHONPATH=/app
    - USE_MOCK_EMBEDDINGS=true
  working_dir: /app
  profiles:
    - test
  command: ["sh", "-c", "ruff check src/ && mypy src/ && pytest tests/unit tests/integration -v"]
```

To use it:

```bash
# Activate test profile (allows docker compose to find test_runner)
export COMPOSE_PROFILES=test

# Or prefix all commands with COMPOSE_PROFILES
COMPOSE_PROFILES=test docker compose run --rm test_runner
```

## Test Files Reference

| Directory | Type | Description |
|-----------|------|-------------|
| `tests/unit/` | Unit | Mock-based tests (104 tests) |
| `tests/integration/` | Integration | Migration tests with real SQLite (9 tests) |
| `tests/e2e/` | E2E | Live MCP protocol tests (14 tests) |

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
- docker build -f Dockerfile.test-base -t ainstruct-test-base .
- docker run --rm
    --mount type=bind,source=${{ github.workspace }}/src,target=/app/src
    --mount type=bind,source=${{ github.workspace }}/tests,target=/app/tests
    --mount type=bind,source=${{ github.workspace }}/pyproject.toml,target=/app/pyproject.toml
    --mount type=bind,source=${{ github.workspace }}/alembic.ini,target=/app/alembic.ini
    --mount type=bind,source=${{ github.workspace }}/migrations,target=/app/migrations
    -w /app
    -e PYTHONPATH=/app
    -e USE_MOCK_EMBEDDINGS=true
    ainstruct-test-base
    sh -c "ruff check src/ && mypy src/ && pytest tests/unit tests/integration -v"
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
