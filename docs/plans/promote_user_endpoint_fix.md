# Plan: Fix Promote User Endpoint - Remove Admin Exists Restriction

## Goal

Modify the `POST /admin/users/{user_id}/promote` endpoint to work even when admin users already exist. Currently it returns 409 Conflict if any admin exists.

---

## Problem

The current implementation restricts promotion to only work when no admin users exist:
- First promotion: Works (no admin exists)
- Subsequent promotions: Fails with 409 Conflict

This is unnecessarily restrictive. The endpoint should allow promoting users to admin regardless of how many admins already exist.

---

## Changes

### 1. `services/rest-api/src/rest_api/routes/admin.py`

**Remove lines 228-236** (the superuser count check):

```python
# REMOVE THIS BLOCK:
existing_superusers = await user_repo.count_superusers()
if existing_superusers > 0:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "code": "ADMIN_EXISTS",
            "message": "An admin user already exists. Use PATCH /users/{user_id} to modify user roles.",
        },
    )
```

**Also fix line 234 error message path:**
```python
# Before:
"message": "An admin user already exists. Use PATCH /users/{user_id} to modify user roles."

# After:
"message": "An admin user already exists. Use PATCH /admin/users/{user_id} to modify user roles."
```

**Update response documentation (line 218)** - Remove 409 from responses since it will no longer be returned.

### 2. `README.md`

**Replace lines 149-150:**

```markdown
# Before:
- First promotion: No admin API key needed
- Subsequent promotions: Requires `ADMIN_API_KEY` environment variable

# After:
- Requires valid `X-Admin-API-Key` header for all promotions
- Works regardless of existing admin users
```

### 3. `tests/unit/admin/test_routes.py`

**Remove test `test_promote_user_admin_already_exists`** (lines 251-267) - This test verifies the 409 behavior which no longer exists.

**Update existing tests** - Remove `count_superusers` mock from:
- `test_promote_user_success` (line 178)
- `test_promote_user_not_found` (line 222)

**Add new test `test_promote_user_success_with_existing_admin`:**

```python
def test_promote_user_success_with_existing_admin(self, app, client):
    """Test successful promotion even when an admin already exists."""
    mock_user = type(
        "User",
        (),
        {
            "id": "user-456",
            "email": "newadmin@example.com",
            "username": "newadmin",
            "is_active": True,
            "is_superuser": True,
            "created_at": "2024-01-01T00:00:00",
        },
    )()

    with patch("rest_api.routes.admin.get_user_repository") as mock_repo:
        mock_repository = AsyncMock()
        mock_repository.get_by_id = AsyncMock(return_value=mock_user)
        mock_repository.update = AsyncMock(return_value=True)
        mock_repo.return_value = mock_repository

        with patch("rest_api.deps.settings") as mock_settings:
            mock_settings.admin_api_key = "test-admin-key"

            response = client.post(
                "/api/v1/admin/users/user-456/promote",
                headers={"X-Admin-API-Key": "test-admin-key"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newadmin"
    assert data["is_superuser"] is True
```

---

## Behavior After Fix

| Scenario | Result |
|----------|--------|
| No admins exist | ✅ Promote works (requires valid `ADMIN_API_KEY`) |
| Admin(s) already exist | ✅ Promote works (requires valid `ADMIN_API_KEY`) |
| User not found | ❌ 404 |
| Invalid `X-Admin-API-Key` | ❌ 401 |
| Missing `X-Admin-API-Key` | ❌ 422 |
| `ADMIN_API_KEY` not configured | ❌ 503 |

---

## Files Modified

| File | Change |
|------|--------|
| `services/rest-api/src/rest_api/routes/admin.py` | Remove superuser count check, update response docs |
| `README.md` | Update documentation |
| `tests/unit/admin/test_routes.py` | Remove obsolete test, update mocks, add new test |

---

## Test Summary

| Test | Action |
|------|--------|
| `test_promote_user_success` | Update: Remove `count_superusers` mock |
| `test_promote_user_invalid_api_key` | Keep as-is |
| `test_promote_user_missing_api_key` | Keep as-is |
| `test_promote_user_not_found` | Update: Remove `count_superusers` mock |
| `test_promote_user_api_key_not_configured` | Keep as-is |
| `test_promote_user_admin_already_exists` | **Remove** |
| `test_promote_user_success_with_existing_admin` | **Add** |

---

## Notes

- The `count_superusers` method in the repository can be kept for potential future use
- Demotion can still be done via `PATCH /api/v1/admin/users/{user_id}` with `is_superuser: false`
