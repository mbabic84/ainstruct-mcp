# MCP API Specification

This document specifies all MCP tools available in the ainstruct system.

---

## Connection

**URL**: `https://ainstruct.example.com/mcp`

**Transport**: SSE or Streamable HTTP

**Authentication**: PAT or CAT (NOT JWT)

```
Authorization: Bearer <pat_token_or_cat_token>
```

---

## Authentication

MCP API accepts **only** PAT or CAT tokens.

| Token Type | Prefix | Scope | Use Case |
|------------|--------|-------|----------|
| PAT | `pat_live_` | User's scopes (READ, WRITE, ±ADMIN) | Full MCP access |
| CAT | `cat_live_` | Single collection (`read` or `read_write`) | Limited collection access |

> **Important**: JWT tokens are NOT accepted for MCP. Use REST API to create a PAT first.

---

## Tool Categories

| Category | Auth Required | Tools |
|----------|---------------|-------|
| Document | PAT or CAT | Store, search, get, list, update, delete |
| Collection | PAT only | Create, list, get, delete, rename |
| CAT Management | PAT only | Create, list, revoke, rotate |
| Admin | PAT (ADMIN scope) | List, search, get, update, delete users |

---

## Document Tools

### store_document_tool

Store a document with automatic chunking and embedding.

**Auth**: PAT or CAT (read_write)

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | Yes | Document title |
| `content` | string | Yes | Markdown content |
| `document_type` | string | No | Type: `markdown`, `pdf`, `docx`, `html`, `text`, `json` |
| `doc_metadata` | object | No | Custom metadata |

**Returns**:
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440004",
  "chunk_count": 5,
  "token_count": 1850,
  "message": "Document stored successfully with 5 chunks"
}
```

**Error Examples**:
- `"Insufficient permissions: write access required"` — CAT has `read` only
- `"Not authenticated"` — Missing or invalid token

---

### search_documents_tool

Semantic search across documents.

**Auth**: PAT or CAT (any permission)

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query |
| `max_results` | int | No | 5 | Maximum results |
| `max_tokens` | int | No | 2000 | Token budget for response |

**Returns**:
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

### get_document_tool

Retrieve a document by ID.

**Auth**: PAT or CAT (any permission)

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_id` | string | Yes | Document UUID |

**Returns**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "title": "Project Documentation",
  "content": "# Overview\n\nThis document describes...",
  "collection_id": "550e8400-e29b-41d4-a716-446655440002",
  "document_type": "markdown",
  "metadata": {},
  "created_at": "2024-03-05T10:30:00Z"
}
```

---

### list_documents_tool

List documents in collection(s).

**Auth**: PAT or CAT (any permission)

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | int | No | 50 | Max results |
| `offset` | int | No | 0 | Pagination offset |

**Returns**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440004",
    "title": "Project Documentation",
    "collection_id": "550e8400-e29b-41d4-a716-446655440002",
    "document_type": "markdown",
    "created_at": "2024-03-05T10:30:00Z"
  }
]
```

---

### update_document_tool

Update an existing document.

**Auth**: PAT or CAT (read_write)

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_id` | string | Yes | Document UUID |
| `title` | string | No | New title |
| `content` | string | No | New content |
| `document_type` | string | No | New document type |
| `doc_metadata` | object | No | New metadata |

**Returns**:
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440004",
  "chunk_count": 7,
  "token_count": 2100,
  "message": "Document updated successfully"
}
```

---

### delete_document_tool

Delete a document.

**Auth**: PAT or CAT (read_write)

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_id` | string | Yes | Document UUID |

**Returns**:
```json
{
  "message": "Document deleted successfully"
}
```

---

## Collection Tools

> Collection tools require PAT authentication (not available with CAT).

### create_collection_tool

Create a new collection.

**Auth**: PAT only

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Collection name |

**Returns**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "name": "work",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-03-05T10:30:00Z"
}
```

---

### list_collections_tool

List user's collections.

**Auth**: PAT only

**Parameters**: None

**Returns**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "default",
    "created_at": "2024-03-05T10:30:00Z"
  }
]
```

---

### get_collection_tool

Get collection details.

**Auth**: PAT only (owner or admin)

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `collection_id` | string | Yes | Collection UUID |

**Returns**:
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

### delete_collection_tool

Delete a collection.

**Auth**: PAT only (owner or admin)

**Prerequisite**: No active CATs associated with collection.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `collection_id` | string | Yes | Collection UUID |

**Returns**:
```json
{
  "message": "Collection deleted successfully"
}
```

**Error**: `"Cannot delete collection with active CATs"` — Revoke all CATs first.

---

### rename_collection_tool

Rename a collection.

**Auth**: PAT only (owner or admin)

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `collection_id` | string | Yes | Collection UUID |
| `name` | string | Yes | New name |

**Returns**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "name": "personal",
  "created_at": "2024-03-05T10:30:00Z"
}
```

---

## CAT Management Tools

> CAT tools require PAT authentication. CAT holders cannot manage CATs.

### create_cat_tool

Create a new Collection Access Token.

**Auth**: PAT only (collection owner or admin)

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `label` | string | Yes | Descriptive label |
| `collection_id` | string | Yes | Collection UUID |
| `permission` | string | Yes | `"read"` or `"read_write"` |
| `expires_in_days` | int | No | Expiry in days |

**Returns**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "label": "Work Laptop",
  "key": "cat_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "collection_id": "550e8400-e29b-41d4-a716-446655440002",
  "permission": "read_write",
  "created_at": "2024-03-05T10:30:00Z"
}
```

> **Warning**: Token is shown only once. Store it securely.

---

### list_cats_tool

List CATs for user's collections.

**Auth**: PAT only

**Parameters**: None

**Returns**:
```json
[
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
```

> **Note**: Actual token values are not returned. Admins see all tokens.

---

### revoke_cat_tool

Revoke a CAT.

**Auth**: PAT only (owner or admin)

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key_id` | string | Yes | CAT UUID |

**Returns**:
```json
{
  "message": "CAT revoked successfully"
}
```

---

### rotate_cat_tool

Rotate a CAT (generate new token, revoke old one).

**Auth**: PAT only (owner or admin)

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key_id` | string | Yes | CAT UUID |

**Returns**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "label": "Work Laptop",
  "key": "cat_live_newtokenhere1234567890123456",
  "collection_id": "550e8400-e29b-41d4-a716-446655440002",
  "permission": "read_write"
}
```

> **Warning**: New token is shown only once. Old token is immediately invalidated.

---

## Admin Tools

> Admin tools require PAT with ADMIN scope (superuser status).

### list_users_tool

List all users.

**Auth**: PAT (ADMIN scope)

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | int | No | 50 | Max results |
| `offset` | int | No | 0 | Pagination offset |

**Returns**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "alice",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2024-03-05T10:30:00Z"
  }
]
```

---

### search_users_tool

Search users by username or email.

**Auth**: PAT (ADMIN scope)

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query |
| `limit` | int | No | 50 | Max results |
| `offset` | int | No | 0 | Pagination offset |

**Returns**: Same as `list_users_tool`

---

### get_user_tool

Get user details by ID.

**Auth**: PAT (ADMIN scope)

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string | Yes | User UUID |

**Returns**:
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

### update_user_tool

Update user details.

**Auth**: PAT (ADMIN scope)

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string | Yes | User UUID |
| `email` | string | No | New email |
| `username` | string | No | New username |
| `password` | string | No | New password |
| `is_active` | bool | No | Active status |
| `is_superuser` | bool | No | Superuser status |

**Returns**: Updated user object

---

### delete_user_tool

Delete a user.

**Auth**: PAT (ADMIN scope)

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string | Yes | User UUID |

**Returns**:
```json
{
  "message": "User deleted successfully"
}
```

---

## Tools NOT in MCP API

The following tools are available **only** via REST API:

| Tool | REST Endpoint | Reason |
|------|---------------|--------|
| User registration | `POST /auth/register` | Interactive auth |
| User login | `POST /auth/login` | Interactive auth |
| Token refresh | `POST /auth/refresh` | JWT-specific |
| Create PAT | `POST /auth/pat` | Account-level, requires JWT |
| List PATs | `GET /auth/pat` | Account-level, requires JWT |
| Revoke PAT | `DELETE /auth/pat/:id` | Account-level, requires JWT |
| Rotate PAT | `POST /auth/pat/:id/rotate` | Account-level, requires JWT |

---

## Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `"Missing or invalid Authorization header"` | No auth provided | Add `Authorization: Bearer <token>` |
| `"Invalid PAT token"` | PAT invalid or revoked | Create new PAT via REST API |
| `"Invalid CAT"` | CAT invalid or revoked | Create new CAT |
| `"Insufficient permissions: write access required"` | CAT has `read` only | Use CAT with `read_write` permission |
| `"JWT tokens not accepted for MCP"` | Using JWT for MCP | Create PAT via REST API first |
| `"Cannot delete collection with active CATs"` | Collection has tokens | Revoke all CATs first |
| `"Not authenticated"` | Token missing or invalid | Provide valid PAT or CAT |

---

## Tool Visibility by Auth

| Auth State | Visible Tools |
|------------|---------------|
| No auth | None (MCP requires PAT or CAT) |
| CAT (read) | Document tools (read-only) |
| CAT (read_write) | Document tools |
| PAT (regular user) | Documents, Collections, CAT tools |
| PAT (admin) | All MCP tools |

---

## Token Format Reference

```
PAT Token:   pat_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
             └──────┘ └────────────────────────────────────┘
             prefix   32 urlsafe characters

CAT Token:   cat_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
             └──────┘ └────────────────────────────────────┘
             prefix   32 urlsafe characters
```