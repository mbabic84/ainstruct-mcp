# AI Document Memory MCP Server - Workflows Documentation

This document provides a comprehensive explanation of all user workflows in the ainstruct-mcp system.

## Architecture Summary

The system is a **Remote MCP Server** for storing and searching markdown documents with semantic embeddings. It uses a **dual authentication model** (JWT + API Keys) with **collection-based data isolation**.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Authentication Layer                          │
├────────────────────────────┬────────────────────────────────────────┤
│       JWT Token Auth       │           API Key Auth                 │
│  ┌──────────────────────┐  │  ┌──────────────────────────────────┐  │
│  │ • User Registration  │  │  │ • Document Storage               │  │
│  │ • User Login         │  │  │ • Document Search                │  │
│  │ • Collection Mgmt    │  │  │ • Document CRUD Operations       │  │
│  │ • API Key Mgmt       │  │  │ • Semantic Search                │  │
│  └──────────────────────┘  │  └──────────────────────────────────┘  │
└────────────────────────────┴────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Data Layer                                  │
├────────────────────────────┬────────────────────────────────────────┤
│      SQLite Database       │           Qdrant Vector DB             │
│  ┌──────────────────────┐  │  ┌──────────────────────────────────┐  │
│  │ • Users              │  │  │ • Document embeddings            │  │
│  │ • Collections        │  │  │ • Semantic search index          │  │
│  │ • API Keys (hashed)  │  │  │ • Collection-isolated data       │  │
│  │ • Document metadata  │  │  │                                  │  │
│  └──────────────────────┘  │  └──────────────────────────────────┘  │
└────────────────────────────┴────────────────────────────────────────┘
```

---

## 1. User Registration Workflow

### Sequence Diagram

```
User                MCP Server              SQLite DB
 │                      │                       │
 │──user_register_tool──>│                       │
 │  {email, username,   │                       │
 │   password}          │                       │
 │                      │                       │
 │                      │──Check username───────>│
 │                      │<──Not found───────────│
 │                      │                       │
 │                      │──Check email──────────>│
 │                      │<──Not found───────────│
 │                      │                       │
 │                      │──Hash password        │
 │                      │  (bcrypt)             │
 │                      │                       │
 │                      │──Create user─────────>│
 │                      │<──User UUID───────────│
 │                      │                       │
 │                      │──Create "default"────>│
 │                      │  collection           │
 │                      │<──Collection UUID─────│
 │                      │                       │
 │<──UserResponse───────│                       │
 │  {id, email,         │                       │
 │   username, ...}     │                       │
```

### Key Points

- **Public tool** - no authentication required
- Automatic "default" collection creation for every new user
- Password hashed with bcrypt before storage
- Returns user ID for future operations

### API Reference

**Tool:** `user_register_tool`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email` | string | Yes | User's email address |
| `username` | string | Yes | Unique username |
| `password` | string | Yes | User's password (will be hashed) |

**Returns:**
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "username": "alice",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-03-05T10:30:00Z"
}
```

**Errors:**
- `"Username already exists"` - Username is taken
- `"Email already exists"` - Email is registered

---

## 2. User Login Workflow

### Sequence Diagram

```
User                MCP Server              SQLite DB
 │                      │                       │
 │──user_login_tool─────>│                       │
 │  {username, password}│                       │
 │                      │                       │
 │                      │──Find user by username>│
 │                      │<──User record─────────│
 │                      │                       │
 │                      │──Verify password      │
 │                      │  (bcrypt compare)     │
 │                      │                       │
 │                      │   ┌───────────────────┤
 │                      │   │ Invalid creds?    │
 │                      │   │ ─────────────────>│ Error
 │                      │   │ Account disabled? │
 │                      │   │ ─────────────────>│ Error
 │                      │   └───────────────────┤
 │                      │                       │
 │                      │──Determine scopes     │
 │                      │  Regular: [read,write]│
 │                      │  Admin: [read,write,  │
 │                      │         admin]        │
 │                      │                       │
 │                      │──Create access token  │
 │                      │  (expires: 30 min)    │
 │                      │                       │
 │                      │──Create refresh token │
 │                      │  (expires: 7 days)    │
 │                      │                       │
 │<──TokenResponse──────│                       │
 │  {access_token,      │                       │
 │   refresh_token,     │                       │
 │   token_type,        │                       │
 │   expires_in}        │                       │
```

### JWT Token Payload Structure

```json
{
  "sub": "user-uuid",
  "username": "alice",
  "email": "alice@example.com",
  "is_superuser": false,
  "scopes": ["read", "write"],
  "exp": 1709654321,
  "iat": 1709652521,
  "type": "access"
}
```

### API Reference

**Tool:** `user_login_tool`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | string | Yes | User's username |
| `password` | string | Yes | User's password |

**Returns:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `"Invalid username or password"` - Wrong credentials
- `"User account is disabled"` - Account deactivated

---

## 3. Token Refresh Workflow

### Sequence Diagram

```
User                MCP Server              SQLite DB
 │                      │                       │
 │──user_refresh_tool───>│                       │
 │  {refresh_token}     │                       │
 │                      │                       │
 │                      │──Validate refresh token
 │                      │  (decode + check type)│
 │                      │                       │
 │                      │──Get user by ID───────>│
 │                      │<──User record─────────│
 │                      │                       │
 │                      │──Create new access    │
 │                      │  token                │
 │                      │                       │
 │                      │──Create new refresh   │
 │                      │  token                │
 │                      │                       │
 │<──TokenResponse──────│                       │
```

### API Reference

**Tool:** `user_refresh_tool`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `refresh_token` | string | Yes | Valid refresh token from login |

**Returns:** Same as `user_login_tool`

---

## 4. Collection Management Workflow

### Data Model

```
User "alice" (user_id: abc123):
├── Collection "default" → Qdrant: docs_xxxx1234
│   ├── API Key "work-laptop" → read_write
│   └── API Key "mobile" → read
├── Collection "personal" → Qdrant: docs_yyyy5678
│   └── API Key "personal-key" → read_write
└── Collection "work" → Qdrant: docs_zzzz9012
    └── API Key "readonly-colleague" → read
```

### Create Collection

```
User (JWT)          MCP Server              SQLite DB
 │                      │                       │
 │──create_collection───>│                       │
 │  {name: "work"}      │                       │
 │  Auth: Bearer JWT    │                       │
 │                      │                       │
 │                      │──Extract user_id      │
 │                      │  from JWT             │
 │                      │                       │
 │                      │──Create collection────>│
 │                      │<──Collection UUID─────│
 │                      │                       │
 │<──CollectionResponse─│                       │
```

### List Collections

```
User (JWT)          MCP Server              SQLite DB
 │                      │                       │
 │──list_collections────>│                       │
 │  Auth: Bearer JWT    │                       │
 │                      │                       │
 │                      │──Get collections──────>│
 │                      │  by user_id           │
 │                      │<──List of collections─│
 │                      │                       │
 │<──[CollectionList]───│                       │
```

### Delete Collection

```
User (JWT)          MCP Server              SQLite DB
 │                      │                       │
 │──delete_collection───>│                       │
 │  {collection_id}     │                       │
 │                      │                       │
 │                      │──Verify ownership─────>│
 │                      │<──Collection data─────│
 │                      │                       │
 │                      │──Check for active─────>│
 │                      │  API keys             │
 │                      │                       │
 │                      │   ┌───────────────────┤
 │                      │   │ Has active keys?  │
 │                      │   │ ─────────────────>│ Error: Cannot delete
 │                      │   └───────────────────┤
 │                      │                       │
 │                      │──Delete collection────>│
 │                      │                       │
 │<──{success: true}────│                       │
```

### API Reference

| Tool | Parameters | Auth | Description |
|------|------------|------|-------------|
| `create_collection_tool` | `name` | JWT | Create new collection |
| `list_collections_tool` | - | JWT | List user's collections |
| `get_collection_tool` | `collection_id` | JWT | Get collection details |
| `delete_collection_tool` | `collection_id` | JWT | Delete collection (no active keys) |
| `rename_collection_tool` | `collection_id`, `name` | JWT | Rename collection |

---

## 5. API Key Management Workflow

### Create API Key

```
User (JWT)          MCP Server              SQLite DB
 │                      │                       │
 │──create_api_key_tool─>│                       │
 │  {label,             │                       │
 │   collection_id,     │                       │
 │   permission,        │                       │
 │   expires_in_days}   │                       │
 │  Auth: Bearer JWT    │                       │
 │                      │                       │
 │                      │──Validate JWT auth    │
 │                      │                       │
 │                      │──Verify collection────>│
 │                      │  ownership            │
 │                      │<──Collection data─────│
 │                      │                       │
 │                      │──Generate API key     │
 │                      │  ak_live_{random}     │
 │                      │                       │
 │                      │──Hash key (SHA256)    │
 │                      │                       │
 │                      │──Store hash only──────>│
 │                      │<──Key ID──────────────│
 │                      │                       │
 │<──ApiKeyResponse─────│                       │
 │  {id, label,         │                       │
 │   key: "ak_live_..." │  ⚠️ SHOWN ONLY ONCE!  │
 │   collection_id, ...}│                       │
```

### API Key Format

```
ak_live_{32_urlsafe_characters}

Example:
ak_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

### Key Storage Security

- Only the **SHA256 hash** of the API key is stored in the database
- The plain key is shown **only once** during creation
- Similar to password storage - keys cannot be recovered, only rotated

### API Reference

| Tool | Parameters | Auth | Description |
|------|------------|------|-------------|
| `create_api_key_tool` | `label`, `collection_id`, `permission`, `expires_in_days?` | JWT | Create new API key |
| `list_api_keys_tool` | - | JWT | List user's API keys (without actual keys) |
| `revoke_api_key_tool` | `key_id` | JWT | Deactivate an API key |
| `rotate_api_key_tool` | `key_id` | JWT | Generate new key, revoke old one |

**Permission Values:**
- `"read"` - Search, get, list documents only
- `"read_write"` - Full document operations

---

## 6. Document Storage Workflow

### Sequence Diagram

```
Client (API Key)    MCP Server         SQLite DB    Chunking    Embedding    Qdrant
 │                     │                   │           │           │          │
 │──store_document─────>│                   │           │           │          │
 │  {title, content,   │                   │           │           │          │
 │   document_type,    │                   │           │           │          │
 │   metadata}         │                   │           │           │          │
 │  Auth: Bearer       │                   │           │           │          │
 │  ak_live_xxx        │                   │           │           │          │
 │                     │                   │           │           │          │
 │                     │──Validate API key │           │           │          │
 │                     │──Check write perm │           │           │          │
 │                     │                   │           │           │          │
 │                     │──Create document──>│           │           │          │
 │                     │<──Document ID─────│           │           │          │
 │                     │                   │           │           │          │
 │                     │──Chunk content───────────────>│           │          │
 │                     │<──Chunks──────────────────────│           │          │
 │                     │  [{index, content,            │           │          │
 │                     │    token_count}, ...]         │           │          │
 │                     │                   │           │           │          │
 │                     │──Generate embeddings─────────────────────>│          │
 │                     │<──Embedding vectors───────────────────────│          │
 │                     │                   │           │           │          │
 │                     │──Upsert chunks + embeddings─────────────────────────>│
 │                     │<──Point IDs──────────────────────────────────────────│
 │                     │                   │           │           │          │
 │                     │──Update qdrant_id─>│           │           │          │
 │                     │                   │           │           │          │
 │<──StoreDocumentOut──│                   │           │           │          │
 │  {document_id,      │                   │           │           │          │
 │   chunk_count,      │                   │           │           │          │
 │   token_count}      │                   │           │           │          │
```

### Document Processing Pipeline

1. **Storage** - Document metadata and content saved to SQLite
2. **Chunking** - Content split into chunks (max 400 tokens, 50 token overlap)
3. **Embedding** - Each chunk converted to vector (4096 dimensions)
4. **Indexing** - Chunks + embeddings stored in Qdrant for semantic search

### Chunking Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `CHUNK_MAX_TOKENS` | 400 | Maximum tokens per chunk |
| `CHUNK_OVERLAP_TOKENS` | 50 | Overlap between consecutive chunks |

### API Reference

**Tool:** `store_document_tool`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | Yes | Document title |
| `content` | string | Yes | Markdown content |
| `document_type` | string | No | Type: `markdown`, `pdf`, `docx`, `html`, `text`, `json` |
| `doc_metadata` | object | No | Custom metadata |

**Returns:**
```json
{
  "document_id": "uuid-string",
  "chunk_count": 5,
  "token_count": 1850,
  "message": "Document stored successfully with 5 chunks"
}
```

---

## 7. Document Search Workflow

### Sequence Diagram

```
Client (API Key)    MCP Server         Embedding Service    Qdrant
 │                     │                      │               │
 │──search_documents───>│                      │               │
 │  {query,            │                      │               │
 │   max_results,      │                      │               │
 │   max_tokens}       │                      │               │
 │  Auth: Bearer       │                      │               │
 │                     │                      │               │
 │                     │──Validate auth       │               │
 │                     │                      │               │
 │                     │──Embed query────────>│               │
 │                     │<──Query vector───────│               │
 │                     │                      │               │
 │                     │──Search vectors─────────────────────>│
 │                     │  (collection-specific or all)        │
 │                     │<──Search results─────────────────────│
 │                     │  [{doc_id, title, chunk,             │
 │                     │    content, score}, ...]             │
 │                     │                      │               │
 │                     │──Format as markdown  │               │
 │                     │                      │               │
 │<──SearchResults─────│                      │               │
 │  {results,          │                      │               │
 │   total_results,    │                      │               │
 │   tokens_used,      │                      │               │
 │   formatted_context}│                      │               │
```

### Search Result Format

The `formatted_context` field returns markdown-formatted results:

```markdown
## Document Title

*Collection: default*

### Section 1 (relevance: 0.85)

Content of the first matching chunk...

---

### Section 3 (relevance: 0.72)

Content of another matching chunk...

---

## Another Document

*Collection: work*

### Section 2 (relevance: 0.68)

More matching content...
```

### API Reference

**Tool:** `search_documents_tool`

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query |
| `max_results` | int | No | 5 | Maximum results |
| `max_tokens` | int | No | 2000 | Token budget for response |

**Returns:**
```json
{
  "results": [
    {
      "document_id": "uuid",
      "title": "Document Title",
      "chunk_index": 0,
      "content": "Matching content...",
      "score": 0.85,
      "collection": "default"
    }
  ],
  "total_results": 10,
  "tokens_used": 1500,
  "formatted_context": "## Document Title\n\n..."
}
```

---

## 8. Document CRUD Operations

### Get Document

```
Client (API Key)    MCP Server              SQLite DB
 │                      │                       │
 │──get_document_tool───>│                       │
 │  {document_id}       │                       │
 │                      │                       │
 │                      │──Validate auth        │
 │                      │                       │
 │                      │──Get document─────────>│
 │                      │<──Document data───────│
 │                      │                       │
 │<──GetDocumentOutput──│                       │
```

### Update Document

```
Client (API Key)    MCP Server              SQLite DB      Qdrant
 │                      │                       │           │
 │──update_document──────>│                       │           │
 │  {document_id,       │                       │           │
 │   title, content,    │                       │           │
 │   document_type,     │                       │           │
 │   metadata}          │                       │           │
 │                      │                       │           │
 │                      │──Validate write perm  │           │
 │                      │                       │           │
 │                      │──Delete old vectors──────────────>│
 │                      │                       │           │
 │                      │──Update document─────>│           │
 │                      │                       │           │
 │                      │──Re-chunk + re-embed │           │
 │                      │                       │           │
 │                      │──Store new vectors───────────────>│
 │                      │                       │           │
 │<──UpdateDocumentOut──│                       │           │
```

### Delete Document

```
Client (API Key)    MCP Server              SQLite DB      Qdrant
 │                      │                       │           │
 │──delete_document─────>│                       │           │
 │  {document_id}       │                       │           │
 │                      │                       │           │
 │                      │──Validate write perm  │           │
 │                      │                       │           │
 │                      │──Delete vectors──────────────────>│
 │                      │                       │           │
 │                      │──Delete document─────>│           │
 │                      │                       │           │
 │<──{success: true}────│                       │           │
```

### API Reference

| Tool | Parameters | Auth Required | Write Permission |
|------|------------|---------------|------------------|
| `get_document_tool` | `document_id` | Yes (any) | No |
| `list_documents_tool` | `limit`, `offset` | Yes (any) | No |
| `update_document_tool` | `document_id`, `title`, `content`, `document_type`, `doc_metadata` | Yes (API Key) | Yes |
| `delete_document_tool` | `document_id` | Yes (API Key) | Yes |

---

## 9. Authentication Middleware Flow

### Request Processing

```
                    Incoming Request
                          │
                          ▼
               ┌─────────────────────┐
               │ Check Auth Header   │
               └─────────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
        Missing/Empty            Bearer Token
              │                       │
              ▼                       ▼
     ┌─────────────────┐     ┌─────────────────┐
     │ Is Public Tool? │     │ JWT or API Key? │
     └─────────────────┘     └─────────────────┘
              │                       │
       ┌──────┴──────┐         ┌──────┴──────┐
       │             │         │             │
      Yes           No       JWT (3 parts)  API Key
       │             │         │             │
       ▼             ▼         ▼             ▼
   Allow        Reject     Validate      Validate
   Request      Request    JWT Token     API Key
                           │             │
                    ┌──────┴──────┐      │
                    │             │      │
                Valid         Invalid  Valid
                    │             │      │
                    ▼             ▼      ▼
              Set User      Reject   Set API Key
              Context       Request  Context
                    │                      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Check Permissions   │
                    └─────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                Has Permission      Missing Permission
                    │                     │
                    ▼                     ▼
                Allow Request      Reject Request
```

### Public Tools (No Auth Required)

| Tool | Description |
|------|-------------|
| `user_register_tool` | User registration |
| `user_login_tool` | User login |
| `promote_to_admin_tool` | Admin promotion (conditional) |

---

## 10. Permission Model

### Authentication Types

| Auth Type | Identifier | Storage | Use Case |
|-----------|------------|---------|----------|
| JWT Token | User ID | SQLite (users table) | User management, collection/key management |
| API Key | Key hash | SQLite (api_keys table) | Document operations |
| Admin API Key | Env variable | Environment variable | Full system access |

### Permission Matrix

| Operation | JWT User | API Key (read) | API Key (read_write) | Admin |
|-----------|----------|----------------|----------------------|-------|
| Register/Login | ✅ | ❌ | ❌ | ❌ |
| View Profile | ✅ | ❌ | ❌ | ✅ |
| Create Collection | ✅ | ❌ | ❌ | ✅ |
| List Collections | ✅ | ❌ | ❌ | ✅ |
| Delete Collection | ✅ | ❌ | ❌ | ✅ |
| Create API Key | ✅ | ❌ | ❌ | ✅ |
| List API Keys | ✅ | ❌ | ❌ | ✅ |
| Revoke API Key | ✅ | ❌ | ❌ | ✅ |
| Store Document | ❌ | ❌ | ✅ | ✅ |
| Search Documents | ❌ | ✅ | ✅ | ✅ |
| Get Document | ❌ | ✅ | ✅ | ✅ |
| List Documents | ❌ | ✅ | ✅ | ✅ |
| Update Document | ❌ | ❌ | ✅ | ✅ |
| Delete Document | ❌ | ❌ | ✅ | ✅ |

### Scope Values

```python
class Scope(str, Enum):
    READ = "read"      # Read operations
    WRITE = "write"    # Write operations
    ADMIN = "admin"    # Admin operations (user management)
```

### Permission Values

```python
class Permission(str, Enum):
    READ = "read"           # Search, get, list documents
    READ_WRITE = "read_write"  # Full document CRUD
```

---

## 11. Complete Onboarding Flow

### Step-by-Step Guide

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Create Initial Config                                    │
│ ─────────────────────────────────────────────────────────────── │
│ Create config file with placeholder token:                      │
│                                                                  │
│ {                                                                │
│   "mcp": {                                                       │
│     "ainstruct": {                                               │
│       "type": "remote",                                          │
│       "url": "https://ainstruct.example.com/mcp",               │
│       "headers": {                                               │
│         "Authorization": "Bearer placeholder"                    │
│       }                                                          │
│     }                                                            │
│   }                                                              │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Register Account                                         │
│ ─────────────────────────────────────────────────────────────── │
│ Call: user_register_tool                                         │
│ Parameters: {email, username, password}                          │
│                                                                  │
│ Result: User created + "default" collection auto-created        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Login                                                    │
│ ─────────────────────────────────────────────────────────────── │
│ Call: user_login_tool                                            │
│ Parameters: {username, password}                                 │
│                                                                  │
│ Result: {access_token, refresh_token}                            │
│ ⚠️ Save these tokens!                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: List Collections (Optional)                              │
│ ─────────────────────────────────────────────────────────────── │
│ Call: list_collections_tool                                      │
│ Auth: Bearer {access_token}                                      │
│                                                                  │
│ Result: [{id: "uuid", name: "default"}]                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Create API Key                                           │
│ ─────────────────────────────────────────────────────────────── │
│ Call: create_api_key_tool                                        │
│ Auth: Bearer {access_token}                                      │
│ Parameters: {                                                    │
│   label: "My Client",                                            │
│   collection_id: "uuid-from-step-4",                            │
│   permission: "read_write"                                       │
│ }                                                                │
│                                                                  │
│ Result: {key: "ak_live_xxx"}                                     │
│ ⚠️ Save this key - shown only once!                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Update Config                                            │
│ ─────────────────────────────────────────────────────────────── │
│ Replace placeholder with API key:                                │
│                                                                  │
│ {                                                                │
│   "mcp": {                                                       │
│     "ainstruct": {                                               │
│       "headers": {                                               │
│         "Authorization": "Bearer ak_live_YOUR_KEY_HERE"         │
│       }                                                          │
│     }                                                            │
│   }                                                              │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 7: Use Document Tools                                       │
│ ─────────────────────────────────────────────────────────────── │
│ Now you can use:                                                 │
│ • store_document_tool - Store documents                          │
│ • search_documents_tool - Semantic search                        │
│ • get_document_tool - Retrieve by ID                             │
│ • list_documents_tool - List documents                           │
│ • update_document_tool - Update documents                        │
│ • delete_document_tool - Delete documents                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 12. Admin Workflows

### Admin Promotion

```
┌─────────────────────────────────────────────────────────────────┐
│ Scenario 1: First Admin (No Admins Exist)                       │
│ ─────────────────────────────────────────────────────────────── │
│ Call: promote_to_admin_tool                                      │
│ Parameters: {user_id: "uuid", admin_api_key: null}              │
│                                                                  │
│ Result: User promoted to superuser (is_superuser: true)         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Scenario 2: Subsequent Admin (Admin Exists)                     │
│ ─────────────────────────────────────────────────────────────── │
│ Prerequisite: ADMIN_API_KEY configured in environment           │
│                                                                  │
│ Call: promote_to_admin_tool                                      │
│ Parameters: {user_id: "uuid", admin_api_key: "secret_key"}      │
│                                                                  │
│ Result: User promoted to superuser                               │
└─────────────────────────────────────────────────────────────────┘
```

### Admin Tools (Require `admin` Scope)

| Tool | Parameters | Description |
|------|------------|-------------|
| `list_users_tool` | `limit`, `offset` | List all users |
| `get_user_tool` | `user_id` | Get user details |
| `update_user_tool` | `user_id`, `email?`, `username?`, `password?`, `is_active?`, `is_superuser?` | Update user |
| `delete_user_tool` | `user_id` | Delete user |

---

## 13. Error Handling

### Common Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `"Missing or invalid Authorization header"` | No auth provided | Add `Authorization: Bearer <token>` header |
| `"Invalid or expired JWT token"` | JWT expired or invalid | Refresh token or re-login |
| `"Invalid API key"` | Unknown or revoked API key | Create new API key |
| `"Insufficient permissions: write access required"` | Read-only API key | Use `read_write` permission |
| `"JWT users cannot store documents directly"` | Using JWT for document ops | Create and use API key |
| `"Collection not found"` | Wrong collection ID or not owned | Check collection ID and ownership |
| `"Cannot delete collection with active API keys"` | Collection has keys | Revoke all API keys first |
| `"Username already exists"` | Duplicate username | Choose different username |
| `"Email already exists"` | Duplicate email | Use different email |

---

## 14. Data Isolation Model

### Collection-Based Isolation

```
┌─────────────────────────────────────────────────────────────────┐
│                         SQLite Database                          │
├─────────────────────────────────────────────────────────────────┤
│  Users                      Collections                          │
│  ┌─────────────────┐       ┌─────────────────┐                  │
│  │ id: user-1      │◄──────│ user_id: user-1 │                  │
│  │ username: alice │       │ id: coll-1      │                  │
│  │ ...             │       │ name: "default" │                  │
│  └─────────────────┘       └─────────────────┘                  │
│                                    │                             │
│  API Keys                          │                             │
│  ┌─────────────────┐               │                             │
│  │ id: key-1       │               │                             │
│  │ collection_id: ─┼───────────────┘                             │
│  │   coll-1        │                                             │
│  │ permission:     │                                             │
│  │   read_write    │                                             │
│  └─────────────────┘                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Qdrant Vector DB                           │
├─────────────────────────────────────────────────────────────────┤
│  Collection: docs_abc123 (derived from coll-1)                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Point ID: point-1                                         │   │
│  │ Vector: [0.1, 0.2, ...] (4096 dimensions)                │   │
│  │ Payload: {document_id, chunk_index, content, title}       │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Point ID: point-2                                         │   │
│  │ ...                                                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Benefits

1. **Lost Key Recovery**: If you lose an API key, create a new key for the same collection - no data loss
2. **Granular Access**: Give read-only keys to colleagues, keep read_write for yourself
3. **Organization**: Separate documents into different collections by topic/project
4. **Security**: Each user's data is isolated - users cannot access each other's collections

---

## 15. Environment Configuration

### Required Variables

```bash
# Database
DB_PATH=./data/documents.db

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=                    # Optional

# Embeddings (Required)
OPENROUTER_API_KEY=your-key        # Required for embeddings
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B
EMBEDDING_DIMENSIONS=4096

# JWT Authentication
JWT_SECRET_KEY=change-this-secret  # Important: Change in production!
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# API Keys (Optional)
API_KEYS=                          # Legacy: comma-separated keys
ADMIN_API_KEY=                     # Admin key for full access
API_KEY_DEFAULT_EXPIRY_DAYS=       # Default expiry for new keys
```

### Chunking Settings

```bash
CHUNK_MAX_TOKENS=400               # Max tokens per chunk
CHUNK_OVERLAP_TOKENS=50            # Overlap between chunks
```

### Search Settings

```bash
SEARCH_MAX_RESULTS=5               # Default max results
SEARCH_MAX_TOKENS=2000             # Default token budget
```

---

## Appendix: Quick Reference

### Tool Categories

| Category | Tools | Auth Type |
|----------|-------|-----------|
| **User Auth** | `user_register_tool`, `user_login_tool`, `user_profile_tool`, `user_refresh_tool` | Public/JWT |
| **Admin** | `promote_to_admin_tool`, `list_users_tool`, `get_user_tool`, `update_user_tool`, `delete_user_tool` | Admin |
| **Collections** | `create_collection_tool`, `list_collections_tool`, `get_collection_tool`, `delete_collection_tool`, `rename_collection_tool` | JWT |
| **API Keys** | `create_api_key_tool`, `list_api_keys_tool`, `revoke_api_key_tool`, `rotate_api_key_tool` | JWT |
| **Documents** | `store_document_tool`, `search_documents_tool`, `get_document_tool`, `list_documents_tool`, `update_document_tool`, `delete_document_tool` | API Key |

### Authentication Quick Reference

```
JWT Token Format: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOi...
                  └─────────────────────────────────────────────┘
                            3 parts separated by dots

API Key Format:   ak_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
                  └──────┘ └────────────────────────────────────┘
                  prefix   32 urlsafe characters
```

### HTTP Header Format

```
Authorization: Bearer <jwt_token_or_api_key>
```