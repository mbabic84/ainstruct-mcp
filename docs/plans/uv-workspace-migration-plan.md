# UV Workspace Migration Plan for ainstruct-mcp

## Executive Summary

This plan details the migration from a single-package structure to a **uv workspace** with three packages:

- `ainstruct-shared` - Common code (db, services, config)
- `ainstruct-mcp-server` - MCP server service
- `ainstruct-rest-api` - REST API service

---

## Current State Analysis

Your codebase already has good foundations:

- Services already run separately via `entrypoint.sh` (`--mcp` / `--rest`)
- Docker Compose runs them as independent containers
- Shared code is well-organized: `config/`, `db/`, `services/`, `tools/`
- Single `pyproject.toml` with unified dependency management

**Current Structure:**

```
src/app/
├── config/
├── db/
├── services/
├── tools/
├── mcp/
│   └── server.py
├── rest/
│   ├── app.py
│   ├── deps.py
│   ├── schemas.py
│   ├── run.py
│   └── routes/
└── main.py
```

---

## Phase 1: Preparation ✅

### 1.1 Install UV Package Manager ✅

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

### 1.2 Create Directory Structure ✅

```bash
# Create new directories
mkdir -p packages/shared/src/shared/{config,db,services,auth}
mkdir -p services/mcp-server/src/mcp_server/tools
mkdir -p services/rest-api/src/rest_api/routes

# Create __init__.py files
touch packages/shared/src/shared/__init__.py
touch packages/shared/src/shared/config/__init__.py
touch packages/shared/src/shared/db/__init__.py
touch packages/shared/src/shared/services/__init__.py
touch packages/shared/src/shared/auth/__init__.py
touch services/mcp-server/src/mcp_server/__init__.py
touch services/mcp-server/src/mcp_server/tools/__init__.py
touch services/rest-api/src/rest_api/__init__.py
touch services/rest-api/src/rest_api/routes/__init__.py
```

### 1.3 Backup Current State ✅

```bash
# Create a migration branch
git checkout -b refactor/uv-workspace-migration

# Tag current state
git tag pre-workspace-migration
```

---

## Phase 2: Workspace Configuration ✅

### 2.1 Root `pyproject.toml` ✅

```toml
[project]
name = "ainstruct-mcp-workspace"
version = "3.4.1"
description = "Monorepo for ainstruct services - MCP server and REST API"
requires-python = ">=3.14"

[tool.uv.workspace]
members = ["packages/*", "services/*"]

[tool.uv.sources]
ainstruct-shared = { workspace = true }
ainstruct-mcp-server = { workspace = true }
ainstruct-rest-api = { workspace = true }

# Tool configurations (shared across workspace)
[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.14"
strict = false
warn_return_any = false
warn_unused_configs = false
disallow_untyped_defs = false
namespace_packages = true
explicit_package_bases = true

[[tool.mypy.overrides]]
module = [
    "fastmcp.*",
    "qdrant_client.*",
    "tiktoken",
    "httpx",
    "pydantic_settings",
]
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
filterwarnings = [
    "error",
    "ignore:datetime.datetime.utcnow:DeprecationWarning",
]
```

### 2.2 Shared Package ✅

### 2.3 MCP Server Package ✅

### 2.4 REST API Package ✅

---

## Phase 3: Target Directory Structure ✅

---

## Phase 4: Code Migration ✅

### 4.1 Migration Commands ✅

### 4.2 Import Path Updates ✅

### 4.3 Import Update Script ✅

---

## Phase 5: Shared Auth Context ✅

---

## Phase 6: Docker Configuration ✅

---

## Phase 7: Test Structure ✅

### 7.1 Updated Test Directory ✅

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── shared/              # Tests for shared package
│   │   ├── test_config.py
│   │   ├── test_auth_service.py
│   │   ├── test_auth_context.py
│   │   └── test_chunking.py
│   ├── mcp/                 # MCP-specific tests
│   │   └── test_server.py
│   └── rest/                # REST-specific tests
│       └── test_app.py
├── integration/
│   └── shared/
│       └── test_services.py
└── e2e/
```

### 7.2 Test Results ✅

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test suite
uv run pytest tests/unit/shared/ -v
uv run pytest tests/unit/mcp/ -v
uv run pytest tests/unit/rest/ -v
```

All tests passing: **40 passed**

### 7.3 Removed SQLite references ✅
- Removed `aiosqlite` dependencies
- Removed SQLite test fixtures
- Tests now use PostgreSQL or mock services

---

## Phase 8: Validation ✅

### 8.1 Post-Migration Validation ✅

- [x] `uv sync` completes without errors
- [x] `uv run ruff check .` passes
- [x] `uv run mypy packages/shared/src services/*/src` passes

### 8.2 Functional Validation

```bash
# Test MCP server
uv run mcp-server

# Test REST API
uv run rest-api
```

```bash
# Test MCP server
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'

# Test REST API
curl http://localhost:8001/health
```

---

## Phase 9: Rollback Plan

If migration fails:

```bash
# Reset to pre-migration state
git checkout pre-workspace-migration

# Delete migration branch
git branch -D refactor/uv-workspace-migration

# Remove workspace directories
rm -rf packages/ services/

# Reinstall dependencies
pip install -e .
```

---

## Timeline Estimate

| Phase | Duration | Risk Level |
|-------|----------|------------|
| 1. Preparation | 30 min | Low |
| 2. Workspace Config | 1 hour | Low |
| 3. Code Migration | 2 hours | Medium |
| 4. Shared Refactoring | 2 hours | Medium |
| 5. Docker Updates | 1 hour | Medium |
| 6. Test Structure | 1 hour | Low |
| 7. Migration Script | 1 hour | Low |
| 8. Import Updates | 2 hours | High |
| 9. Validation | 2 hours | Medium |
| **Total** | **~12 hours** | |

---

## Benefits After Migration

| Aspect | Before | After |
|--------|--------|-------|
| **Docker image size** | ~500MB (all deps) | ~300MB MCP / ~250MB REST |
| **Dependency isolation** | Shared, implicit | Explicit per-package |
| **Testing** | All-or-nothing | Package-specific |
| **Deployment** | Both services together | Independent |
| **Import clarity** | Relative, fragile | Absolute, explicit |
| **CI/CD** | Single pipeline | Per-service possible |

---

## Key Benefits of UV Workspaces

1. **Explicit Dependency Boundaries**: Each package declares what it needs
2. **Independent Deployment**: Each service installs only its dependencies
3. **Single Version Policy**: One lockfile ensures version consistency
4. **Atomic Commits**: Changes across services in one commit
5. **Independent Testing**: Test each service in isolation
6. **Smaller Docker Images**: Install only required packages

This approach is the industry standard for Python monorepos in 2026 and provides a clean path for future microservices extraction if needed.
