# Plan: Add search_users REST Endpoint

## Goal
Add a REST API endpoint to search users by username or email, matching the existing MCP tool functionality.

## Current State
- **MCP tool**: `search_users` exists in `services/mcp-server/src/mcp_server/tools/admin_tools.py:45`
  - Searches by username/email with case-insensitive partial match
  - Requires admin scope
- **Repository**: `UserRepository.search()` exists in `packages/shared/src/shared/db/repository.py:407`
  - Already implements the database query using `ILIKE`
- **REST API**: Missing this endpoint

## Implementation

### 1. Add endpoint to `services/rest-api/src/rest_api/routes/admin.py`

Add after the existing `list_users` endpoint (around line 56):

```python
@router.get(
    "/users/search",
    response_model=UserListResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Query parameter required"},
    },
)
async def search_users(
    query: str = Query(..., min_length=1, description="Search query"),
    db: DbDep,
    admin: AdminDep,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    user_repo = get_user_repository()
    users = await user_repo.search(query=query, limit=limit, offset=offset)
    
    items = [
        UserListItem(
            id=u.id,
            email=u.email,
            username=u.username,
            is_active=u.is_active,
            is_superuser=u.is_superuser,
            created_at=u.created_at,
        )
        for u in users
    ]
    return UserListResponse(users=items, total=len(users), limit=limit, offset=offset)
```

### 2. Add tests

Create or extend test file for admin routes. Test cases:
- ✅ Successful search by username
- ✅ Successful search by email  
- ✅ Empty results for non-matching query
- ❌ Unauthorized access (non-admin) - should return 403
- ❌ Missing query parameter - should return 422

## Dependencies
- No new schemas needed - reuses `UserListResponse` and `UserListItem`
- No new imports needed - `get_user_repository` already imported in admin.py

## Route Path Considerations
- Chose `/admin/users/search` to avoid conflict with `/admin/users/{user_id}`
- Query parameter is required (`...`) to match MCP tool behavior
- Returns same response format as `list_users` for consistency
