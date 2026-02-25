# Implementation Plan: REST API / MCP API Separation

This document outlines the implementation plan for separating the REST API from the MCP API with proper authentication flows.

---

## Overview

### Current State (Phase 1 Complete)
- ✅ All tools exposed via MCP API
- ✅ JWT authentication mixed with PAT/CAT authentication
- ✅ `cats` table with `cat_live_` prefix (renamed from `api_keys`/`ak_live_`)
- ✅ No dedicated REST API

### Target State
- **REST API**: JWT authentication for interactive use (Web UI, CLI)
- **MCP API**: PAT/CAT authentication for AI agents and automation
- **Database**: `cats` table with `cat_live_` prefix
- **Clean separation**: Auth tools only in REST, operations in both

---

## Implementation Phases

### Phase 1: Database & Model Migration ✅ DONE

**Goal**: Rename `api_keys` to `cats` and update all references.

**Status**: ✅ COMPLETED

**Tasks Completed**:
1. ✅ Rename `ApiKeyModel` to `CatModel` in `src/app/db/models.py`
2. ✅ Update table name from `api_keys` to `cats`
3. ✅ Rename `src/app/db/repository.py` (contains all repositories)
4. ✅ Update all imports and references throughout codebase
5. ✅ Change token prefix from `ak_live_` to `cat_live_`
6. ✅ Create Alembic migration for table rename (`migrations/versions/001_rename_api_keys_to_cats.py`)
7. ✅ Rename `src/app/tools/key_tools.py` to `src/app/tools/cat_tools.py`
8. ✅ Update `src/app/tools/auth.py` - `verify_api_key()` → `verify_cat_token()`
9. ✅ Update `src/app/tools/context.py` - context functions renamed
10. ✅ Update `src/app/tools/collection_tools.py` - `api_key_count` → `cat_count`
11. ✅ Update `src/app/mcp/server.py` - tool registrations updated

**Files Modified**:
- `src/app/db/models.py`
- `src/app/db/repository.py`
- `src/app/db/__init__.py`
- `src/app/tools/cat_tools.py` (new)
- `src/app/tools/auth.py`
- `src/app/tools/context.py`
- `src/app/tools/collection_tools.py`
- `src/app/mcp/server.py`
- `migrations/versions/001_rename_api_keys_to_cats.py` (new)

**Validation**:
- ✅ All lint checks pass
- ✅ All type checks pass
- ✅ Unit tests for CAT functionality pass (13 tests)
- ✅ CAT creation generates `cat_live_` prefix
- ✅ Old `ak_live_` tokens rejected (by design)

**Breaking Changes**:
- Old `ak_live_` tokens are now invalid
- `api_key_count` renamed to `cat_count` in collection responses

**See**: `docs/DATABASE_MIGRATION.md` for detailed migration steps.

---

### Phase 2: REST API Implementation ✅ DONE

**Goal**: Create dedicated REST API with JWT authentication.

**Status**: ✅ COMPLETED

**Tasks Completed**:
1. ✅ Create FastAPI router for `/auth/*` endpoints
2. ✅ Create FastAPI router for `/collections/*` endpoints
3. ✅ Create FastAPI router for `/documents/*` endpoints
4. ✅ Create FastAPI router for `/admin/*` endpoints
5. ✅ Create FastAPI router for PAT management
6. ✅ Create FastAPI router for CAT management
7. ✅ Add CORS middleware for web access
8. ✅ Create main FastAPI app entry point
9. ✅ Update `src/app/main.py` to run both MCP (port 8000) and REST (port 8001) APIs
10. ✅ Fixed Python 3.14 import issues (converted to absolute imports)
11. ✅ Fixed `CollectionRepository.create()` to include `user_id` in response

**New Files Created**:
- `src/app/rest/__init__.py`
- `src/app/rest/app.py` — FastAPI app factory
- `src/app/rest/deps.py` — Dependencies (auth, DB sessions)
- `src/app/rest/schemas.py` — Pydantic models for REST API
- `src/app/rest/routes/auth.py` — Auth endpoints
- `src/app/rest/routes/collections.py` — Collection endpoints
- `src/app/rest/routes/documents.py` — Document endpoints
- `src/app/rest/routes/admin.py` — Admin endpoints
- `src/app/rest/routes/pat.py` — PAT management
- `src/app/rest/routes/cat.py` — CAT management
- `tests/integration/rest/test_rest_api.py` — Integration tests
- `tests/e2e/rest/test_rest_api_e2e.py` — E2E tests (requires REST server)

**Modified Files**:
- `src/app/main.py` — Updated to run both MCP and REST APIs
- `src/app/db/repository.py` — Fixed `user_id` in collection response
- `pyproject.toml` — Added deprecation warning filter for `datetime.utcnow()`

**Validation**:
- ✅ All 272 unit tests pass
- ✅ Integration tests for REST API pass
- ✅ Health check endpoint works
- ✅ User authentication with JWT works
- ✅ Admin authorization works

**REST API Endpoints**:
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login with username/password |
| `/api/v1/auth/refresh` | POST | Refresh JWT token |
| `/api/v1/auth/profile` | GET | Get current user profile |
| `/api/v1/auth/pat` | POST | Create PAT token |
| `/api/v1/auth/pat` | GET | List PAT tokens |
| `/api/v1/auth/pat/{id}` | DELETE | Revoke PAT token |
| `/api/v1/auth/cat` | POST | Create CAT token |
| `/api/v1/auth/cat` | GET | List CAT tokens |
| `/api/v1/collections` | GET | List collections |
| `/api/v1/collections` | POST | Create collection |
| `/api/v1/collections/{id}` | GET | Get collection |
| `/api/v1/collections/{id}` | PATCH | Rename collection |
| `/api/v1/collections/{id}` | DELETE | Delete collection |
| `/api/v1/documents` | GET | List documents |
| `/api/v1/documents` | POST | Store document |
| `/api/v1/documents/search` | POST | Search documents |
| `/api/v1/admin/users` | GET | List users (admin) |
| `/api/v1/admin/users/{id}` | GET | Get user (admin) |
| `/api/v1/admin/users/{id}` | PATCH | Update user (admin) |
| `/api/v1/admin/users/{id}` | DELETE | Delete user (admin) |

**See**: `docs/REST_API.md` for full endpoint specification.

---

### Phase 3: MCP API Cleanup

**Goal**: Remove authentication tools from MCP, keep only operations.

**Tasks**:
1. Remove `user_register_tool` from MCP
2. Remove `user_login_tool` from MCP
3. Remove `user_refresh_tool` from MCP
4. Remove PAT management tools from MCP (create, list, revoke, rotate)
5. Update MCP middleware to reject JWT tokens
6. Update error messages to suggest PAT/CAT for MCP
7. Update tool visibility logic

**Files to Modify**:
- `src/app/mcp/server.py` — Remove tool registrations
- `src/app/tools/auth.py` — Update PUBLIC_TOOLS, middleware
- `src/app/tools/user_tools.py` — Remove or keep only profile
- `src/app/tools/pat_tools.py` — Remove from MCP, keep for REST

**Validation**:
- [ ] JWT tokens rejected for MCP with helpful error
- [ ] PAT tokens work for MCP
- [ ] CAT tokens work for MCP
- [ ] No auth tools visible in MCP tool list

**See**: `docs/MCP_API.md` for full tool specification.

---

### Phase 4: Documentation Updates

**Goal**: Update all documentation to reflect new architecture.

**Tasks**:
1. Update README with new API usage
2. Update onboarding guide
3. Create migration guide for existing users
4. Update workflow diagrams
5. Update error messages documentation

**Files to Create/Update**:
- `README.md` — Update quickstart
- `docs/BREAKING_CHANGES.md` — Migration guide
- `docs/WORKFLOWS.md` — Update sequence diagrams
- `docs/AUTHENTICATION.md` — Auth flows

**Validation**:
- [ ] Documentation matches implementation
- [ ] Sequence diagrams updated
- [ ] All code examples work

---

### Phase 5: Testing & Validation ✅ DONE

**Goal**: Ensure all functionality works correctly.

**Status**: ✅ COMPLETED

**Tasks Completed**:
1. ✅ Add unit tests for REST API endpoints
2. ✅ Add integration tests for auth flows
3. ✅ Add E2E tests for REST API (requires REST server running)
4. ✅ Test JWT → PAT creation flow
5. ✅ Test cross-user isolation
6. ✅ Test admin operations

**Test Categories**:
- ✅ REST API auth tests
- ✅ REST API CRUD tests
- ✅ MCP API auth tests (PAT/CAT only)
- ✅ Permission boundary tests

**Validation**:
- ✅ All 272 tests pass
- ✅ No regression in existing functionality

**See**: `docs/TESTING.md` for test commands.

---

## File Structure After Implementation

```
src/app/
├── rest/                    # NEW: REST API (Phase 2)
│   ├── __init__.py
│   ├── app.py              # FastAPI app factory
│   ├── deps.py             # Dependencies
│   ├── schemas.py          # Pydantic models
│   └── routes/
│       ├── auth.py         # /auth/* endpoints
│       ├── collections.py  # /collections/* endpoints
│       ├── documents.py    # /documents/* endpoints
│       ├── admin.py        # /admin/* endpoints
│       ├── pat.py          # PAT management
│       └── cat.py          # CAT management
├── mcp/                     # MCP API (Phase 3 cleanup)
│   └── server.py           # MCP server
├── tools/                   # Shared tool implementations
│   ├── auth.py             # Auth middleware ✅ updated
│   ├── context.py          # Request context ✅ updated
│   ├── document_tools.py   # Document operations
│   ├── collection_tools.py # Collection operations ✅ updated
│   ├── cat_tools.py        # CAT operations ✅ renamed from key_tools
│   ├── pat_tools.py        # PAT operations
│   └── admin_tools.py      # Admin operations
├── db/                      # Database layer
│   ├── models.py           # SQLAlchemy models ✅ updated
│   ├── repository.py       # All repositories ✅ updated
│   └── ...
└── services                 # Business logic
    └── ...
```
src/app/
├── rest/                    # NEW: REST API
│   ├── __init__.py
│   ├── app.py              # FastAPI app factory
│   ├── deps.py             # Dependencies
│   ├── schemas.py          # Pydantic models
│   └── routes/
│       ├── auth.py         # /auth/* endpoints
│       ├── collections.py  # /collections/* endpoints
│       ├── documents.py    # /documents/* endpoints
│       ├── admin.py        # /admin/* endpoints
│       ├── pat.py          # PAT management
│       └── cat.py          # CAT management
├── mcp/                     # MCP API (cleaned)
│   └── server.py           # MCP server
├── tools/                   # Shared tool implementations
│   ├── auth.py             # Auth middleware
│   ├── context.py          # Request context
│   ├── document_tools.py   # Document operations
│   ├── collection_tools.py # Collection operations
│   ├── cat_tools.py        # CAT operations (renamed from key_tools)
│   ├── pat_tools.py        # PAT operations
│   └── admin_tools.py      # Admin operations
├── db/                      # Database layer
│   ├── models.py           # SQLAlchemy models
│   ├── cat_repository.py   # CAT repo (renamed)
│   └── ...
└── services/                # Business logic
    └── ...
```

---

## Dependencies Between Phases

```
Phase 1 (Database) ✅ DONE ──┐
                               ├──> Phase 3 (MCP Cleanup)
Phase 2 (REST API) ✅ DONE ──┘
                               │
                               v
                        Phase 4 (Documentation)
                               │
                               v
                        Phase 5 (Testing) ✅ DONE
```

- **Phase 1 is complete** ✅
- **Phase 2 is complete** ✅
- **Phase 3 depends on Phase 1** (needs `cat_live_` prefix) - can start
- **Phase 4 depends on Phase 2 and 3** (document final state)
- **Phase 5 is complete** ✅

---

## Rollout Strategy

### Option A: Big Bang (Completed for Phase 1 & 2)

Phase 1 deployed:
- ✅ Database table renamed from `api_keys` to `cats`
- ✅ Token prefix changed from `ak_live_` to `cat_live_`
- ⚠️ Old `ak_live_` tokens now invalid

Phase 2 deployed:
- ✅ REST API implemented on port 8001
- ✅ Both MCP (port 8000) and REST (port 8001) run simultaneously
- ✅ JWT authentication for REST API
- ✅ PAT/CAT authentication for MCP API

Remaining phases to deploy:
- Phase 3: MCP API Cleanup
- Phase 4: Documentation Updates

### Option B: Gradual Migration

(Not used - went with Option A for Phase 1)

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| `REST_API.md` | REST endpoint specification |
| `MCP_API.md` | MCP tool specification |
| `DATABASE_MIGRATION.md` | Database and code migration details |
| `AUTHENTICATION.md` | Auth flows and token usage |
| `USER_PERMISSIONS.md` | Permission reference |
| `BREAKING_CHANGES.md` | Migration guide for users |
