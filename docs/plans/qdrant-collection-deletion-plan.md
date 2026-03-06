# Fix Plan: Delete Qdrant Collection When Deleting from Postgres

**Date:** 2026-03-02
**Status:** Draft
**Priority:** High

## Issue Description

When a collection is deleted from the application (via REST API or MCP tool), only the Postgres database record is removed. The Qdrant collection with all its vector data remains orphaned, consuming storage resources.

## Root Cause Analysis

The current deletion flow only removes the database record:

1. **REST API** (`services/rest-api/src/rest_api/routes/collections.py:161-192`): Calls `collection_repo.delete(collection_id)` but never touches Qdrant
2. **MCP Tool** (`services/mcp-server/src/mcp_server/tools/collection_tools.py:101-122`): Same issue - only deletes DB record
3. **Repository** (`packages/shared/src/shared/db/repository.py:532-542`): Only deletes the SQLAlchemy model

The `QdrantService` class lacks a method to delete entire collections - it only has `delete_by_document_id()` for removing individual documents.

## Affected Code Locations

- `packages/shared/src/shared/db/qdrant.py` - Missing `delete_collection` method
- `services/rest-api/src/rest_api/routes/collections.py:191` - Delete endpoint
- `services/mcp-server/src/mcp_server/tools/collection_tools.py:119` - Delete tool

## Proposed Fix

### 1. Add `delete_collection` method to QdrantService

**File:** `packages/shared/src/shared/db/qdrant.py`

Add a new async method to the `QdrantService` class:

```python
async def delete_collection(self, collection_name: str) -> None:
    """Delete an entire Qdrant collection.

    Args:
        collection_name: The name of the Qdrant collection to delete

    Raises:
        Exception: If deletion fails (caller should handle and prevent Postgres deletion)
    """
    await self.client.delete_collection(collection_name=collection_name)
```

### 2. Update REST API collection deletion

**File:** `services/rest-api/src/rest_api/routes/collections.py`
**Line:** ~191

Change:
```python
await collection_repo.delete(collection_id)
return MessageResponse(message="Collection deleted successfully")
```

To:
```python
# Delete Qdrant collection first (contains the vector data)
qdrant_service = get_qdrant_service(collection["qdrant_collection"])
await qdrant_service.delete_collection(collection["qdrant_collection"])

# Then delete the database record
await collection_repo.delete(collection_id)
return MessageResponse(message="Collection deleted successfully")
```

### 3. Update MCP tool collection deletion

**File:** `services/mcp-server/src/mcp_server/tools/collection_tools.py`
**Line:** ~119

Change:
```python
await repo.delete(input_data.collection_id)
return {"success": True, "message": "Collection deleted successfully"}
```

To:
```python
# Delete Qdrant collection first
qdrant_service = get_qdrant_service(collection.qdrant_collection)
await qdrant_service.delete_collection(collection.qdrant_collection)

# Then delete the database record
await repo.delete(input_data.collection_id)
return {"success": True, "message": "Collection deleted successfully"}
```

## Error Handling Strategy

The deletion must be atomic - both Qdrant and Postgres must succeed, or neither should be deleted:

1. **Delete from Qdrant first** - if this fails, raise exception and do NOT delete from Postgres
2. **Then delete from Postgres** - if this fails, the Qdrant collection is already deleted (acceptable state)
3. **Both succeed** - return success

This ensures we never have a state where Postgres record exists but Qdrant collection doesn't (which would cause search errors). The reverse (Qdrant exists without Postgres record) is acceptable as it's just orphaned data.

### REST API Error Handling

```python
# Delete Qdrant collection first
qdrant_service = get_qdrant_service(collection["qdrant_collection"])
try:
    await qdrant_service.delete_collection(collection["qdrant_collection"])
except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"code": "QDRANT_DELETE_FAILED", "message": f"Failed to delete collection from vector store: {e}"}
    )

# Then delete the database record (only if Qdrant succeeded)
await collection_repo.delete(collection_id)
return MessageResponse(message="Collection deleted successfully")
```

### MCP Tool Error Handling

```python
# Delete Qdrant collection first
qdrant_service = get_qdrant_service(collection.qdrant_collection)
try:
    await qdrant_service.delete_collection(collection.qdrant_collection)
except Exception as e:
    return {"success": False, "error": f"Failed to delete collection from vector store: {e}"}

# Then delete the database record (only if Qdrant succeeded)
await repo.delete(input_data.collection_id)
return {"success": True, "message": "Collection deleted successfully"}
```

## Testing Checklist

- [ ] Test deleting collection via REST API - verify Qdrant collection removed
- [ ] Test deleting collection via MCP tool - verify Qdrant collection removed
- [ ] Test when Qdrant collection already doesn't exist (idempotent behavior)
- [ ] Verify documents can no longer be searched after collection deletion
- [ ] Test error handling when Qdrant is temporarily unavailable

## Implementation Notes

- Import `logger` from `shared.logging` or use standard logging
- The `get_qdrant_service` function is already imported in both files
- Collection's `qdrant_collection` field contains the actual Qdrant collection name
- No database migration needed - this is pure code change

## Follow-up Improvements (Optional)

1. **Background cleanup job**: Periodically scan for orphaned Qdrant collections and remove them
2. **Transactional safety**: Consider implementing a two-phase commit or outbox pattern for true consistency
3. **Audit logging**: Log collection deletions with metadata about vector count, etc.
