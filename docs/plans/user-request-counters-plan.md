# User Request Counters per Month Implementation Plan

## Overview
Track document-related requests (REST API + MCP tools) per user per month using PostgreSQL with atomic upsert operations.

## Goals
- Track how many document-related requests each user makes per month
- Distinguish between REST API and MCP tool requests
- Provide admin endpoints to view usage statistics
- Support historical data across multiple months

---

## Components

### 1. Database Model
**File:** `packages/shared/src/shared/db/models.py`

Add `UsageRecordModel` class:
```python
class UsageRecordModel(Base):
    __tablename__ = "usage_records"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    year_month: Mapped[str] = mapped_column(String(7), nullable=False)  # "2026-03"
    source: Mapped[str] = mapped_column(String(10), nullable=False)  # "api" or "mcp"
    request_count: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint("user_id", "year_month", "source", name="uq_user_month_source"),)
```

---

### 2. Usage Repository
**File:** `packages/shared/src/shared/db/usage_repository.py` (new file)

Create `UsageRepository` class with:
- `increment(user_id, source)` - Atomic upsert using PostgreSQL `INSERT ... ON CONFLICT DO UPDATE`
- `get_monthly_usage(user_id, year_month)` - Returns dict with api_requests, mcp_requests, total_requests
- `get_usage_history(user_id, months=6)` - Returns usage across multiple months

Follow existing repository patterns from `repository.py`.

---

### 3. Export Repository
**File:** `packages/shared/src/shared/db/__init__.py`

Add exports:
```python
from .usage_repository import UsageRepository, get_usage_repository
__all__ = [..., "UsageRepository", "get_usage_repository"]
```

---

### 4. REST API Middleware
**File:** `services/rest-api/src/rest_api/app.py`

Add HTTP middleware to track document-related requests:
- **Track paths:** `/api/v1/documents/*`, `/api/v1/collections/*`
- **Skip paths:** health checks, auth endpoints
- Extract user_id from JWT Bearer token
- Call `usage_repo.increment(user_id, "api")`

---

### 5. MCP Auth Middleware Tracking
**File:** `services/mcp-server/src/mcp_server/tools/auth.py`

Modify `AuthMiddleware.on_call_tool`:
- After successful auth, check if tool is in `DOCUMENT_TOOLS` set
- Document tools: `store_document_tool`, `search_documents_tool`, `get_document_tool`, `list_documents_tool`, `delete_document_tool`, `update_document_tool`, `move_document_tool`
- Extract user_id from `user_info`, `pat_info`, or `cat_info`
- Call `usage_repo.increment(user_id, "mcp")`

---

### 6. Admin Endpoints
**File:** `services/rest-api/src/rest_api/routes/admin.py`

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/admin/usage/{user_id}?year_month=2026-03` | Single month stats |
| `GET /api/v1/admin/usage/{user_id}/history?months=6` | History across multiple months |

**Single month response:**
```json
{
  "year_month": "2026-03",
  "api_requests": 150,
  "mcp_requests": 75,
  "total_requests": 225
}
```

**History response:**
```json
{
  "history": [
    {"year_month": "2026-03", "api_requests": 150, "mcp_requests": 75, "total": 225},
    {"year_month": "2026-02", "api_requests": 100, "mcp_requests": 50, "total": 150}
  ]
}
```

Note: `user_id` is not included in responses since it's already specified in the URL path.

---

### 7. Database Migration
**File:** `migrations/versions/add_usage_records.py`

Auto-generated via alembic - creates `usage_records` table with unique constraint.

---

## Test-First Approach

Tests will be created first to define expected behavior:

### Test Files

| Test File | Tests |
|-----------|-------|
| `tests/unit/shared/test_usage_repository.py` | `increment()` upsert behavior, `get_monthly_usage()`, `get_usage_history()` |
| `tests/unit/rest/test_usage_middleware.py` | Middleware tracks document/collection paths, skips others, extracts user from JWT |
| `tests/unit/mcp/test_usage_tracking.py` | MCP tracks document tools only, extracts user_id from JWT/PAT/CAT |

---

## Key Design Decisions

1. **Atomic upsert** - Uses PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` to prevent race conditions with concurrent requests
2. **Month-based grouping** - `year_month` string (e.g., "2026-03") enables easy querying by month
3. **Source distinction** - Tracks "api" vs "mcp" separately for billing/analytics
4. **Document-only scope** - Only tracks document/collection operations, not auth/PAT endpoints
5. **No user_id in response** - User ID is already in the URL path, no need to repeat in response

---

## Dependencies
- No new external dependencies required
- Uses existing SQLAlchemy async patterns
- Uses existing PostgreSQL database

---

## Execution Order
1. Create test files (define expected behavior)
2. Implement model, repository, exports
3. Implement middleware and MCP tracking
4. Implement admin endpoints
5. Create database migration
6. Run tests to verify

---

## Status
- [ ] Create test files
- [ ] Implement UsageRecordModel
- [ ] Implement UsageRepository
- [ ] Export UsageRepository
- [ ] Add REST API middleware
- [ ] Add MCP tracking
- [ ] Add admin endpoints
- [ ] Create migration
- [ ] Run tests
