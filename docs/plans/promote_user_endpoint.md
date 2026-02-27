# Plan: Add Promote User to Admin Endpoint (Option A)

## Goal
Add an endpoint to promote an existing user to superuser using `ADMIN_API_KEY` authentication, enabling creation of the first admin user without requiring an existing admin. This endpoint only works when there are no existing admin users.

---

## Implementation

### 1. Add Admin API Key Dependency in `services/rest-api/src/rest_api/deps.py`

Added a new dependency function to verify the admin API key from a header:

```python
async def require_admin_api_key(
    x_admin_api_key: str = Header(..., alias="X-Admin-API-Key"),
) -> str:
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "ADMIN_API_KEY_NOT_CONFIGURED", "message": "Admin API key not configured"},
        )
    if x_admin_api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_ADMIN_API_KEY", "message": "Invalid admin API key"},
        )
    return x_admin_api_key


AdminApiKeyDep = Annotated[str, Depends(require_admin_api_key)]
```

### 2. Add count_superusers Method in `packages/shared/src/shared/db/repository.py`

Added a method to count existing superusers:

```python
async def count_superusers(self) -> int:
    async with self.async_session() as session:
        result = await session.execute(
            select(func.count(UserModel.id)).where(UserModel.is_superuser.is_(True))
        )
        return result.scalar() or 0
```

### 3. Add Endpoint in `services/rest-api/src/rest_api/routes/admin.py`

Added promote endpoint that checks for existing admins before promoting:

```python
@router.post(
    "/users/{user_id}/promote",
    response_model=UserResponse,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        401: {"model": ErrorResponse, "description": "Invalid admin API key"},
        503: {"model": ErrorResponse, "description": "Admin API key not configured"},
        409: {"model": ErrorResponse, "description": "Admin user already exists"},
    },
)
async def promote_user(
    user_id: str,
    admin_api_key: AdminApiKeyDep,
    db: DbDep,
):
    user_repo = get_user_repository()

    existing_superusers = await user_repo.count_superusers()
    if existing_superusers > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ADMIN_EXISTS", "message": "An admin user already exists. Use PATCH /users/{user_id} to modify user roles."},
        )

    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    await user_repo.update(user_id, is_superuser=True)

    updated = await user_repo.get_by_id(user_id)
    return UserResponse(
        id=updated.id,
        email=updated.email,
        username=updated.username,
        is_active=updated.is_active,
        is_superuser=updated.is_superuser,
        created_at=updated.created_at,
    )
```

### 4. Add Tests in `tests/unit/admin/test_routes.py`

Added test cases:
- ✅ Successful promotion with valid admin API key (when no admin exists)
- ✅ Invalid admin API key returns 401
- ✅ Missing admin API key header returns 422
- ✅ Non-existent user returns 404
- ✅ Admin API key not configured returns 503
- ✅ Admin already exists returns 409

---

## API Contract

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/admin/users/{user_id}/promote` | `X-Admin-API-Key` header | Promote user to superuser |

**Request Headers:**
```
X-Admin-API-Key: <admin_api_key>
```

**Responses:**
- `200` - User promoted successfully, returns `UserResponse`
- `401` - Invalid admin API key
- `404` - User not found
- `409` - Admin user already exists
- `422` - Missing header
- `503` - Admin API key not configured on server

---

## Files Modified

| File | Change |
|------|--------|
| `services/rest-api/src/rest_api/deps.py` | Added `require_admin_api_key` dependency and `AdminApiKeyDep` type alias |
| `packages/shared/src/shared/db/repository.py` | Added `count_superusers` method |
| `services/rest-api/src/rest_api/routes/admin.py` | Added `promote_user` endpoint |
| `tests/unit/admin/test_routes.py` | Added tests for promote endpoint |

---

## Usage Flow

1. User registers via `POST /api/v1/auth/register`
2. Admin uses `POST /api/v1/admin/users/{user_id}/promote` with `X-Admin-API-Key` header
3. User can now login and access admin endpoints

**Note:** This endpoint only works when there are no existing admin users. Once an admin exists, use `PATCH /api/v1/admin/users/{user_id}` with `is_superuser: true/false` to modify user roles.

---

## Notes

- Demotion can be done using the existing `PATCH /api/v1/admin/users/{user_id}` endpoint with `is_superuser: false`
- This approach mirrors the MCP server's current capability where ADMIN_API_KEY can access `update_user_tool` to set `is_superuser=true`
