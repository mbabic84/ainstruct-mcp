# Database & Code Migration Guide

This document details all database and code changes required for the REST/MCP API separation.

---

## Overview

### Terminology Change

**"API Key"** renamed to **"CAT" (Collection Access Token)**

Rationale:
- Better reflects the token's purpose (collection-scoped access)
- Distinguishes from PAT (Personal Access Token)
- Clearer naming for users

### Token Prefix Change

| Current | New |
|---------|-----|
| `ak_live_xxx` | `cat_live_xxx` |

### Migration Strategy

**Clean Break** (recommended):
- Rename table from `api_keys` to `cats`
- Invalidate all existing `ak_live_` tokens
- Users create new `cat_live_` tokens after update
- No backward compatibility layer

---

## Database Changes

### Table Rename

```sql
ALTER TABLE api_keys RENAME TO cats;
```

### Column Changes

No column changes required. The table structure remains the same:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `label` | VARCHAR | User-defined label |
| `collection_id` | UUID | Foreign key to collections |
| `key_hash` | VARCHAR(64) | SHA256 hash of token |
| `permission` | VARCHAR | `read` or `read_write` |
| `expires_at` | DATETIME | Optional expiry |
| `created_at` | DATETIME | Creation timestamp |
| `is_active` | BOOLEAN | Active status |

### New Tables Required

**PAT Tokens Table** (if not exists):

```sql
CREATE TABLE pats (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    label VARCHAR NOT NULL,
    token_hash VARCHAR(64) NOT NULL,
    expires_at DATETIME,
    created_at DATETIME NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
```

---

## Code Changes

### File Renames

| Current Path | New Path |
|--------------|----------|
| `src/app/db/api_key_repository.py` | `src/app/db/cat_repository.py` |
| `src/app/tools/key_tools.py` | `src/app/tools/cat_tools.py` |

### Model Rename

**File**: `src/app/db/models.py`

```python
# Before
class ApiKey(Base):
    __tablename__ = "api_keys"
    # ...

# After
class Cat(Base):
    __tablename__ = "cats"
    # ...
```

### Token Prefix Change

**File**: `src/app/tools/auth.py`

```python
# Before
API_KEY_PREFIX = "ak_live_"

# After  
CAT_PREFIX = "cat_live_"
```

### Repository Rename

**File**: `src/app/db/cat_repository.py` (renamed from `api_key_repository.py`)

```python
# Before
class ApiKeyRepository:
    def validate(self, api_key: str) -> dict | None:
        if not api_key.startswith("ak_live_"):
            return None
        # ...

# After
class CatRepository:
    def validate(self, cat: str) -> dict | None:
        if not cat.startswith("cat_live_"):
            return None
        # ...
```

### Tool Rename

**File**: `src/app/tools/cat_tools.py` (renamed from `key_tools.py`)

```python
# Before
@mcp.tool()
def create_api_key_tool(...) -> dict:
    ...

@mcp.tool()
def list_api_keys_tool(...) -> list:
    ...

@mcp.tool()
def revoke_api_key_tool(...) -> dict:
    ...

@mcp.tool()
def rotate_api_key_tool(...) -> dict:
    ...

# After
@mcp.tool()
def create_cat_tool(...) -> dict:
    ...

@mcp.tool()
def list_cats_tool(...) -> list:
    ...

@mcp.tool()
def revoke_cat_tool(...) -> dict:
    ...

@mcp.tool()
def rotate_cat_tool(...) -> dict:
    ...
```

---

## Files to Update

### Core Files

| File | Change Required |
|------|-----------------|
| `src/app/db/models.py` | Rename `ApiKey` → `Cat`, update `__tablename__` |
| `src/app/db/__init__.py` | Update imports and `get_cat_repository()` function |
| `src/app/tools/auth.py` | Change prefix to `cat_live_`, update variable names |
| `src/app/tools/cat_tools.py` | Rename file, update function names |
| `src/app/tools/context.py` | Update variable names (`api_key_info` → `cat_info`) |
| `src/app/mcp/server.py` | Update tool registrations |

### Reference Updates

Search and replace across all files:

| Search | Replace |
|--------|---------|
| `api_key` (variable) | `cat` |
| `api_keys` (table ref) | `cats` |
| `ApiKey` (class) | `Cat` |
| `api_key_repository` | `cat_repository` |
| `ApiKeyRepository` | `CatRepository` |
| `get_api_key_repository` | `get_cat_repository` |
| `ak_live_` | `cat_live_` |
| `API_KEY_PREFIX` | `CAT_PREFIX` |
| `create_api_key_tool` | `create_cat_tool` |
| `list_api_keys_tool` | `list_cats_tool` |
| `revoke_api_key_tool` | `revoke_cat_tool` |
| `rotate_api_key_tool` | `rotate_cat_tool` |

---

## Migration Script

### Alembic Migration

**File**: `alembic/versions/xxx_rename_api_keys_to_cats.py`

```python
"""rename api_keys to cats

Revision ID: xxx
Revises: yyy
Create Date: 2024-03-05 10:30:00.000000

"""
from alembic import op

revision = 'xxx'
down_revision = 'yyy'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table('api_keys', 'cats')


def downgrade() -> None:
    op.rename_table('cats', 'api_keys')
```

### Clean Break Script (Optional)

If you want to clean up old tokens:

```python
"""Clean break - invalidate old ak_live_ tokens

Run this after table rename to clear out old tokens.
Users will need to create new cat_live_ tokens.

"""
from app.db import get_session
from app.db.models import Cat


def clean_break():
    """Delete all existing CATs (old ak_live_ tokens)."""
    with get_session() as session:
        session.query(Cat).delete()
        session.commit()
    print("All existing tokens deleted. Users must create new cat_live_ tokens.")


if __name__ == "__main__":
    clean_break()
```

---

## Testing Checklist

After migration, verify:

- [ ] `cats` table exists
- [ ] `Cat` model works with renamed table
- [ ] `cat_live_` prefix validation works
- [ ] `ak_live_` tokens are rejected
- [ ] CAT creation generates `cat_live_` prefix
- [ ] CAT validation works correctly
- [ ] All imports updated
- [ ] All tool names updated
- [ ] Tests pass

---

## Rollback Plan

If issues arise, rollback:

```sql
ALTER TABLE cats RENAME TO api_keys;
```

Then revert code changes.

---

## Migration Timeline

1. **Backup database** before migration
2. **Run Alembic migration** to rename table
3. **Deploy code changes** with new naming
4. **Verify** all functionality works
5. **Communicate** to users about token regeneration

---

## User Communication

Inform users:

> **Breaking Change**: API Keys have been renamed to Collection Access Tokens (CATs).
> 
> - Old token prefix: `ak_live_` → New prefix: `cat_live_`
> - All existing `ak_live_` tokens are invalid after this update
> - Please create new CATs via REST API or MCP tools
> 
> No data is lost — your documents and collections remain intact.