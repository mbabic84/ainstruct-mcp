# User Types and Permissions Overview

This document describes all user types, their capabilities, and permission requirements for each tool in the ainstruct system.

---

## Terminology Note

**CAT (Collection Access Token)** — Formerly known as "API Key". 

The naming was changed from "API Key" to "Collection Access Token (CAT)" to better reflect the token's purpose:
- Tokens are scoped to a specific collection
- Each token grants access to documents within that collection only
- Users can create multiple CATs with different permissions for the same collection

Token prefix: `cat_live_` (e.g., `cat_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)

---

## Architecture: Two Separate APIs

The system exposes two APIs with different authentication requirements but overlapping functionality:

| API | Purpose | Auth Method | Use Case |
|-----|---------|-------------|----------|
| **REST API** | Auth & all operations | JWT (short-lived) | Web UI, interactive sessions |
| **MCP API** | All operations (except auth) | PAT or CAT (long-lived) | AI agents, automation, integrations |

### Why JWT is NOT for MCP

- MCP clients load configuration once at startup
- JWT expires in 30 minutes
- No mechanism to auto-refresh in static MCP config
- **JWT should NOT be used for MCP** — use PAT instead

### API Overlap

Most operations are available via both APIs for convenience:

| Operation | REST API | MCP API |
|-----------|----------|---------|
| User registration | ✅ | ❌ |
| User login | ✅ | ❌ |
| PAT management | ✅ | ❌ |
| CAT management | ✅ | ✅ |
| Collection management | ✅ | ✅ |
| Document operations | ✅ | ✅ |
| Admin user management | ✅ | ✅ |

**Convenience for AI agents**: Users can instruct AI agents to create collections, generate CATs for sharing, and manage their account — all via MCP without needing WebUI.

---

## User Types

| Type | Identifier | Properties |
|------|------------|------------|
| **Regular User** | `is_superuser=False, is_active=True` | Default user with read/write scopes |
| **Admin/Superuser** | `is_superuser=True` | Full admin access, implicit all scopes |
| **Inactive User** | `is_active=False` | Account disabled, cannot authenticate |

---

## Scopes

| Scope | Value | Description |
|-------|-------|-------------|
| `READ` | `"read"` | Read-only access to documents |
| `WRITE` | `"write"` | Write access to create/update/delete |
| `ADMIN` | `"admin"` | Admin scope for user management |

---

## Permissions (CAT - Collection Access Token)

| Permission | Value | Description |
|------------|-------|-------------|
| `READ` | `"read"` | Search and retrieve documents only |
| `READ_WRITE` | `"read_write"` | Full document access (create, update, delete) |

---

## Authentication Methods

| Method | Prefix | Scope | Use Case |
|--------|--------|-------|----------|
| **JWT Token** | 3 parts (dot-separated) | User's scopes (READ, WRITE, ADMIN if superuser) | User sessions, full API access |
| **PAT Token** | `pat_live_` | Inherits user's scopes | Long-lived user-level access |
| **CAT (Collection Access Token)** | `cat_live_` | Collection-specific (`read` or `read_write`) | Single collection document operations |
| **Admin CAT** | Env var `ADMIN_API_KEY` | Admin | Service-level admin access |

---

## Tool Categories & Permissions

### REST API Endpoints (JWT Authentication)

**Authentication (Public):**

| Endpoint | Auth | Description |
|----------|------|-------------|
| `POST /auth/register` | None | Create new user account |
| `POST /auth/login` | None | Authenticate and get JWT tokens |
| `POST /auth/refresh` | Refresh token | Refresh access token |

**User & Token Operations (JWT):**

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /auth/profile` | JWT | Get current user profile |
| `POST /auth/pat` | JWT | Create PAT token |
| `GET /auth/pat` | JWT | List PAT tokens |
| `DELETE /auth/pat/:id` | JWT | Revoke PAT token |
| `POST /auth/cat` | JWT | Create CAT for collection |
| `GET /auth/cat` | JWT | List CATs |
| `DELETE /auth/cat/:id` | JWT | Revoke CAT |

**Collection Operations (JWT):**

| Endpoint | Auth | Description |
|----------|------|-------------|
| `POST /collections` | JWT | Create collection |
| `GET /collections` | JWT | List user's collections |
| `GET /collections/:id` | JWT | Get collection details |
| `PATCH /collections/:id` | JWT | Rename collection |
| `DELETE /collections/:id` | JWT | Delete collection |

**Document Operations (JWT):**

| Endpoint | Auth | Description |
|----------|------|-------------|
| `POST /documents` | JWT | Store document |
| `GET /documents` | JWT | List documents |
| `GET /documents/:id` | JWT | Get document by ID |
| `PATCH /documents/:id` | JWT | Update document |
| `DELETE /documents/:id` | JWT | Delete document |
| `POST /documents/search` | JWT | Semantic search |

**Admin Operations (JWT with ADMIN scope):**

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /admin/users` | JWT (ADMIN) | List all users |
| `GET /admin/users/:id` | JWT (ADMIN) | Get user details |
| `PATCH /admin/users/:id` | JWT (ADMIN) | Update user |
| `DELETE /admin/users/:id` | JWT (ADMIN) | Delete user |

---

### MCP API Tools (PAT or CAT Authentication)

**Document Tools (PAT or CAT):**

| Tool | Description | Permission Check |
|------|-------------|------------------|
| `store_document_tool` | Store document | Requires `write` scope or `read_write` CAT |
| `search_documents_tool` | Semantic search | Any valid PAT/CAT |
| `get_document_tool` | Get document by ID | Any valid PAT/CAT |
| `list_documents_tool` | List documents | Any valid PAT/CAT |
| `delete_document_tool` | Delete document | Requires `write` scope or `read_write` CAT |
| `update_document_tool` | Update document | Requires `write` scope or `read_write` CAT |

**Collection Tools (PAT Only):**

| Tool | Description | Additional Check |
|------|-------------|------------------|
| `create_collection_tool` | Create new collection | Must be authenticated |
| `list_collections_tool` | List user's collections | Must be authenticated |
| `get_collection_tool` | Get collection details | Owner or superuser |
| `delete_collection_tool` | Delete collection | Owner or superuser |
| `rename_collection_tool` | Rename collection | Owner or superuser |

**CAT Management Tools (PAT Only):**

| Tool | Description | Additional Check |
|------|-------------|------------------|
| `create_cat_tool` | Create CAT for collection | Owner or superuser |
| `list_cats_tool` | List user's CATs | Non-admins see only their own |
| `revoke_cat_tool` | Revoke CAT | Owner or superuser |
| `rotate_cat_tool` | Rotate CAT | Owner or superuser |

> **Note**: PAT management tools are NOT available via MCP — use REST API with JWT

**Admin Tools (PAT with ADMIN scope):**

| Tool | Description |
|------|-------------|
| `list_users_tool` | List all users |
| `search_users_tool` | Search users |
| `get_user_tool` | Get user by ID |
| `update_user_tool` | Update user |
| `delete_user_tool` | Delete user |

---

## User Capabilities by Type

### Interactive User (JWT via REST API)

**Purpose**: Account management and token creation

**Can Access (REST API)**:
- Register account
- Login and get JWT tokens
- Create and manage PAT tokens
- Create and manage CATs
- Admin operations (if ADMIN scope)

**Cannot Access**:
- MCP tools directly (use PAT or CAT)

---

### MCP Client User (PAT Authentication)

**Default Scopes**: `[READ, WRITE]` (inherited from user)

**Can Access (MCP API)**:
- All document operations (all own collections)
- All collection management (own collections only)
- Create and manage CATs for own collections
- List, revoke, rotate own PATs

**Cannot Access**:
- Create PAT tokens (requires REST API with JWT)
- Other users' collections, documents, or tokens

---

### Admin/Superuser (PAT with ADMIN scope)

**Default Scopes**: `[READ, WRITE, ADMIN]`

**Can Access (MCP API)**:
- All document operations (all users' collections)
- All collection management (all users' collections)
- All CAT management (all users' tokens)
- All PAT management (all users' tokens)

**Can Access (REST API)**:
- All admin operations (user management)

---

### CAT Holder (Collection Access Token)

**Scope**: Collection-specific (`read` or `read_write`)

**Can Access with `read` permission**:
- `search_documents_tool` — Semantic search
- `get_document_tool` — Get document by ID
- `list_documents_tool` — List documents

**Can Access with `read_write` permission**:
- All `read` operations
- `store_document_tool` — Store new documents
- `delete_document_tool` — Delete documents
- `update_document_tool` — Update documents

**Cannot Access**:
- User profile tools
- Collection management tools
- CAT/PAT management tools
- Admin tools

---

### Inactive User (`is_active=False`)

**Capabilities**: None

- Cannot login (REST API returns error)
- PAT/CAT validation fails (MCP API returns error)
- Account is effectively disabled

**Admin Override**:
- Admins can reactivate via REST API `PATCH /admin/users/:id` with `is_active=true`

---

## MCP API Authorization Flow

### Token Validation

1. **Extract token** from `Authorization: Bearer <token>` header
2. **Detect token type**:
   - `pat_live_` prefix → PAT validation
   - `cat_live_` prefix → CAT validation
   - 3 parts (dots) → JWT validation (should NOT be used for MCP)
3. **Validate token**: Check database for PAT/CAT, verify user is active
4. **Set context**: Store user/token info for request

### Tool Visibility (MCP API)

| Auth State | Visible Tools |
|------------|---------------|
| No auth | None (MCP requires PAT or CAT) |
| CAT (read) | Document tools (read-only) |
| CAT (read_write) | Document tools |
| PAT (regular) | Document + Collection + CAT tools |
| PAT (admin) | All MCP tools |

### REST API Authorization Flow

| Endpoint | Auth Required |
|----------|---------------|
| `POST /auth/register` | None |
| `POST /auth/login` | None |
| `POST /auth/refresh` | Valid refresh token |
| All other `/auth/*` | JWT access token |
| All `/admin/*` | JWT with ADMIN scope |

---

## Permission Checking (MCP API)

| Function | Logic |
|----------|-------|
| `has_scope(required_scope)` | Checks if PAT has scope; superusers bypass |
| `has_write_permission()` | Checks `write` scope OR `read_write` CAT permission |
| `is_authenticated()` | Returns true if valid PAT or CAT |

---

## Related Documentation

| Document | Description |
|----------|-------------|
| `IMPLEMENTATION_PLAN.md` | Implementation phases and timeline |
| `REST_API.md` | REST API endpoint specification |
| `MCP_API.md` | MCP API tool specification |
| `AUTHENTICATION.md` | Authentication flows and token details |
| `DATABASE_MIGRATION.md` | Database and code migration |
| `BREAKING_CHANGES.md` | Migration guide for existing users |
