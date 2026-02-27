# Promote User to Admin

Promotes an existing user to superuser (admin). This endpoint is intended for bootstrapping the first admin user when no admin exists yet.

**Note:** This endpoint only works when there are no existing admin users. Once an admin exists, use `PATCH /users/{user_id}` to modify user roles.

```
POST /api/v1/admin/users/{user_id}/promote
```

## Authentication

This endpoint uses the `ADMIN_API_KEY` environment variable as a custom header:

```
X-Admin-API-Key: <admin_api_key>
```

## Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | string | The ID of the user to promote |

## Responses

| Status Code | Description |
|-------------|-------------|
| 200 | User promoted successfully |
| 401 | Invalid admin API key |
| 404 | User not found |
| 409 | Admin user already exists |
| 422 | Missing required header |
| 503 | Admin API key not configured |

## Example Request

```bash
curl -X POST http://localhost:8000/api/v1/admin/users/user-123/promote \
  -H "X-Admin-API-Key: your_admin_api_key"
```

## Example Response (200)

```json
{
  "id": "user-123",
  "email": "user@example.com",
  "username": "newadmin",
  "is_active": true,
  "is_superuser": true,
  "created_at": "2024-01-01T00:00:00"
}
```

## Example Response (409 - Admin Exists)

```json
{
  "detail": {
    "code": "ADMIN_EXISTS",
    "message": "An admin user already exists. Use PATCH /users/{user_id} to modify user roles."
  }
}
```

## First-Time Setup

To create the first admin user:

1. Register a new user:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@example.com", "username": "admin", "password": "yourpassword"}'
   ```

2. Promote the user to admin:
   ```bash
   curl -X POST http://localhost:8000/api/v1/admin/users/<user_id>/promote \
     -H "X-Admin-API-Key: $ADMIN_API_KEY"
   ```

3. The user can now login and access admin endpoints using JWT authentication.
