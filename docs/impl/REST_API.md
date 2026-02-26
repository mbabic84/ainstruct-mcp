# REST API Specification

This document specifies all REST API endpoints for the ainstruct system.

---

## Base URL

```
https://ainstruct.example.com/api/v1
```

---

## Authentication

| Endpoint Category | Auth Method |
|-------------------|-------------|
| Public endpoints | None |
| Protected endpoints | JWT Bearer token |
| Admin endpoints | JWT Bearer token + ADMIN scope |

**Header Format**:
```
Authorization: Bearer <jwt_token>
```

---

## Response Format

### Success Response

```json
{
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": { ... }  // Optional
  }
}
```

---

## Endpoints

### Authentication

#### POST /auth/register

Create a new user account.

**Auth**: None (public)

**Request Body**:
```json
{
  "email": "user@example.com",
  "username": "alice",
  "password": "securepassword123"
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "alice",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-03-05T10:30:00Z"
}
```

**Errors**:
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `USERNAME_EXISTS` | 400 | Username already registered |
| `EMAIL_EXISTS` | 400 | Email already registered |

---

#### POST /auth/login

Authenticate user and receive JWT tokens.

**Auth**: None (public)

**Request Body**:
```json
{
  "username": "alice",
  "password": "securepassword123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors**:
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_CREDENTIALS` | 401 | Wrong username or password |
| `ACCOUNT_DISABLED` | 403 | User account is inactive |

---

#### POST /auth/refresh

Refresh access token using refresh token.

**Auth**: Valid refresh token

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors**:
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REFRESH_TOKEN` | 401 | Refresh token invalid or expired |

---

#### GET /auth/profile

Get current user profile.

**Auth**: JWT required

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "alice",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-03-05T10:30:00Z"
}
```

---

### PAT (Personal Access Token) Management

#### POST /auth/pat

Create a new PAT.

**Auth**: JWT required

**Request Body**:
```json
{
  "label": "My MCP Client",
  "expires_in_days": 365  // Optional
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "label": "My MCP Client",
  "token": "pat_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "created_at": "2024-03-05T10:30:00Z",
  "expires_at": "2025-03-05T10:30:00Z"
}
```

> **Warning**: Token is shown only once. Store it securely.

---

#### GET /auth/pat

List all PATs for current user.

**Auth**: JWT required

**Response** (200 OK):
```json
{
  "tokens": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "label": "My MCP Client",
      "created_at": "2024-03-05T10:30:00Z",
      "expires_at": "2025-03-05T10:30:00Z",
      "is_active": true
    }
  ]
}
```

> **Note**: Actual token values are not returned.

---

#### DELETE /auth/pat/:id

Revoke a PAT.

**Auth**: JWT required

**Response** (200 OK):
```json
{
  "message": "PAT revoked successfully"
}
```

**Errors**:
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `PAT_NOT_FOUND` | 404 | PAT not found or not owned by user |

---

#### POST /auth/pat/:id/rotate

Rotate a PAT (generate new token, revoke old one).

**Auth**: JWT required

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "label": "My MCP Client",
  "token": "pat_live_newtokenhere1234567890123456",
  "created_at": "2024-03-05T10:30:00Z",
  "expires_at": "2025-03-05T10:30:00Z"
}
```

> **Warning**: New token is shown only once. Old token is immediately invalidated.

---

### CAT (Collection Access Token) Management

#### POST /auth/cat

Create a new CAT for a collection.

**Auth**: JWT required

**Request Body**:
```json
{
  "label": "Work Laptop",
  "collection_id": "550e8400-e29b-41d4-a716-446655440002",
  "permission": "read_write",
  "expires_in_days": 90  // Optional
}
```

**Permission Values**: `"read"` | `"read_write"`

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "label": "Work Laptop",
  "token": "cat_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "collection_id": "550e8400-e29b-41d4-a716-446655440002",
  "permission": "read_write",
  "created_at": "2024-03-05T10:30:00Z",
  "expires_at": "2024-06-05T10:30:00Z"
}
```

> **Warning**: Token is shown only once. Store it securely.

---

#### GET /auth/cat

List all CATs for current user.

**Auth**: JWT required

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `collection_id` | UUID | Filter by collection (optional) |

**Response** (200 OK):
```json
{
  "tokens": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "label": "Work Laptop",
      "collection_id": "550e8400-e29b-41d4-a716-446655440002",
      "collection_name": "default",
      "permission": "read_write",
      "created_at": "2024-03-05T10:30:00Z",
      "expires_at": "2024-06-05T10:30:00Z",
      "is_active": true
    }
  ]
}
```

---

#### DELETE /auth/cat/:id

Revoke a CAT.

**Auth**: JWT required

**Response** (200 OK):
```json
{
  "message": "CAT revoked successfully"
}
```

---

### Collection Management

#### POST /collections

Create a new collection.

**Auth**: JWT required

**Request Body**:
```json
{
  "name": "work"
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "name": "work",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-03-05T10:30:00Z"
}
```

---

#### GET /collections

List all collections for current user.

**Auth**: JWT required

**Response** (200 OK):
```json
{
  "collections": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "default",
      "document_count": 15,
      "cat_count": 2,
      "created_at": "2024-03-05T10:30:00Z"
    }
  ]
}
```

---

#### GET /collections/:id

Get collection details.

**Auth**: JWT required (owner or admin)

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "name": "default",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_count": 15,
  "cat_count": 2,
  "created_at": "2024-03-05T10:30:00Z"
}
```

---

#### PATCH /collections/:id

Rename a collection.

**Auth**: JWT required (owner or admin)

**Request Body**:
```json
{
  "name": "personal"
}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "name": "personal",
  "updated_at": "2024-03-05T11:00:00Z"
}
```

---

#### DELETE /collections/:id

Delete a collection.

**Auth**: JWT required (owner or admin)

**Prerequisite**: No active CATs associated with collection.

**Response** (200 OK):
```json
{
  "message": "Collection deleted successfully"
}
```

**Errors**:
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `COLLECTION_HAS_ACTIVE_CATS` | 400 | Cannot delete collection with active CATs |
| `COLLECTION_NOT_FOUND` | 404 | Collection not found |

---

### Document Operations

#### POST /documents

Store a new document.

**Auth**: JWT required

**Request Body**:
```json
{
  "title": "Project Documentation",
  "content": "# Overview\n\nThis document describes...",
  "document_type": "markdown",
  "collection_id": "550e8400-e29b-41d4-a716-446655440002",
  "metadata": {
    "project": "ainstruct",
    "version": "1.0"
  }
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "title": "Project Documentation",
  "collection_id": "550e8400-e29b-41d4-a716-446655440002",
  "chunk_count": 5,
  "token_count": 1850,
  "created_at": "2024-03-05T10:30:00Z"
}
```

---

#### GET /documents

List documents.

**Auth**: JWT required

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `collection_id` | UUID | all | Filter by collection |
| `limit` | int | 50 | Max results |
| `offset` | int | 0 | Pagination offset |

**Response** (200 OK):
```json
{
  "documents": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440004",
      "title": "Project Documentation",
      "collection_id": "550e8400-e29b-41d4-a716-446655440002",
      "document_type": "markdown",
      "created_at": "2024-03-05T10:30:00Z"
    }
  ],
  "total": 15,
  "limit": 50,
  "offset": 0
}
```

---

#### GET /documents/:id

Get document by ID.

**Auth**: JWT required

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "title": "Project Documentation",
  "content": "# Overview\n\nThis document describes...",
  "collection_id": "550e8400-e29b-41d4-a716-446655440002",
  "document_type": "markdown",
  "metadata": {
    "project": "ainstruct",
    "version": "1.0"
  },
  "created_at": "2024-03-05T10:30:00Z",
  "updated_at": null
}
```

---

#### PATCH /documents/:id

Update document.

**Auth**: JWT required

**Request Body** (all fields optional):
```json
{
  "title": "Updated Title",
  "content": "New content...",
  "document_type": "markdown",
  "metadata": {
    "version": "2.0"
  }
}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "title": "Updated Title",
  "chunk_count": 7,
  "token_count": 2100,
  "updated_at": "2024-03-05T11:00:00Z"
}
```

---

#### DELETE /documents/:id

Delete document.

**Auth**: JWT required

**Response** (200 OK):
```json
{
  "message": "Document deleted successfully"
}
```

---

#### POST /documents/search

Semantic search across documents.

**Auth**: JWT required

**Request Body**:
```json
{
  "query": "how to configure authentication",
  "collection_id": "550e8400-e29b-41d4-a716-446655440002",  // Optional
  "max_results": 5,
  "max_tokens": 2000
}
```

**Response** (200 OK):
```json
{
  "results": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440004",
      "title": "Project Documentation",
      "chunk_index": 0,
      "content": "Authentication is configured via...",
      "score": 0.85,
      "collection": "default"
    }
  ],
  "total_results": 10,
  "tokens_used": 1500,
  "formatted_context": "## Project Documentation\n\n..."
}
```

---

### Admin Operations

> All admin endpoints require JWT with ADMIN scope.

#### GET /admin/users

List all users.

**Auth**: JWT + ADMIN scope

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 50 | Max results |
| `offset` | int | 0 | Pagination offset |

**Response** (200 OK):
```json
{
  "users": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "username": "alice",
      "is_active": true,
      "is_superuser": false,
      "created_at": "2024-03-05T10:30:00Z"
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

---

#### GET /admin/users/:id

Get user details.

**Auth**: JWT + ADMIN scope

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "alice",
  "is_active": true,
  "is_superuser": false,
  "collection_count": 3,
  "pat_count": 2,
  "cat_count": 5,
  "created_at": "2024-03-05T10:30:00Z"
}
```

---

#### PATCH /admin/users/:id

Update user.

**Auth**: JWT + ADMIN scope

**Request Body** (all fields optional):
```json
{
  "email": "newemail@example.com",
  "username": "newusername",
  "password": "newpassword",
  "is_active": true,
  "is_superuser": false
}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "newemail@example.com",
  "username": "newusername",
  "is_active": true,
  "is_superuser": false,
  "updated_at": "2024-03-05T11:00:00Z"
}
```

---

#### DELETE /admin/users/:id

Delete user.

**Auth**: JWT + ADMIN scope

**Restriction**: Cannot delete self.

**Response** (200 OK):
```json
{
  "message": "User deleted successfully"
}
```

**Errors**:
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `CANNOT_DELETE_SELF` | 400 | Cannot delete your own account |

---

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |

---

## Rate Limiting (Recommended)

| Endpoint | Rate Limit | Reason |
|----------|------------|--------|
| `POST /auth/register` | 5/hour/IP | Prevent bot registration |
| `POST /auth/login` | 10/minute/IP | Prevent brute force |
| `POST /auth/refresh` | 20/minute/user | Normal refresh patterns |
| `POST /documents/search` | 100/minute/user | Prevent abuse |
| `POST /documents` | 50/minute/user | Reasonable storage rate |