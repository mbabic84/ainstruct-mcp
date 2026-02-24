# AI Document Memory MCP Server

Remote MCP server for storing and searching markdown documents with semantic embeddings. Features user authentication with JWT tokens, API key management with permissions, and collection-based data organization.

## New User Onboarding

If you're a new user wanting to use ainstruct with Kilo CLI or another MCP client:

### Step 1: Create Initial Config

Create a minimal config file with a placeholder token. For Kilo CLI (`opencode.json`):

```json
{
  "mcp": {
    "ainstruct": {
      "type": "remote",
      "url": "https://ainstruct.kralicinora.cz/mcp",
      "headers": {
        "Authorization": "Bearer placeholder"
      },
      "enabled": true
    }
  }
}
```

### Step 2: Register Your Account

In Kilo CLI, call the registration tool (public, no auth needed):

```
/user_register_tool
```

Provide:
- `email` - Your email address
- `username` - Your desired username
- `password` - Your password

**A "default" collection is automatically created for you.**

### Step 3: Login

```
/user_login_tool
```

Provide:
- `username` - Your username
- `password` - Your password

**Save the returned `access_token` and `refresh_token`.**

### Step 4: (Optional) List Your Collections

```
/list_collections_tool
```

This shows your collections. You'll have one named "default".

### Step 5: Create an API Key

Using your access token, create a long-lived API key:

```
/create_api_key_tool
```

Provide:
- `label` - A name for this key (e.g., "Kilo CLI")
- `collection_id` - The collection to grant access to (from step 4)
- `permission` - `"read"` for read-only, `"read_write"` for full access
- `expires_in_days` - Optional expiry (leave empty for no expiry)

**Save the returned `key` - it's shown only once!**

### Step 6: Update Your Config

Replace the placeholder with your new API key:

```json
{
  "mcp": {
    "ainstruct": {
      "type": "remote",
      "url": "https://ainstruct.kralicinora.cz/mcp",
      "headers": {
        "Authorization": "Bearer ak_live_YOUR_KEY_HERE"
      },
      "enabled": true
    }
  }
}
```

### Step 7: Use the Tools

You can now use all document tools:
- `store_document_tool` - Store documents
- `search_documents_tool` - Semantic search
- `get_document_tool` - Retrieve by ID
- `list_documents_tool` - List your documents
- `update_document_tool` - Update documents
- `delete_document_tool` - Delete documents

---

## Admin Users

### How Admin Accounts Work

Admin users (`is_superuser=True`) have:
- **Full access** to all admin tools (user management)
- **All scopes** implicitly (read, write, admin)
- Can manage other users via `list_users_tool`, `get_user_tool`, `update_user_tool`, `delete_user_tool`

### Creating Admin Users

Admin rights are granted to **existing users** via promotion:

#### Step 1: User Registers Normally

```
/user_register_tool
```
User creates their account with email, username, password.

#### Step 2: Promote to Admin

```
/promote_to_admin_tool
```

**For the FIRST admin** (no admins exist yet):
- `user_id` - The user to promote
- `admin_api_key` - Leave empty (auto-allowed)

**For SUBSEQUENT admins** (admin already exists):
- `user_id` - The user to promote
- `admin_api_key` - The value from `ADMIN_API_KEY` env var

### Setup Flow Example

```bash
# 1. First user registers
/user_register_tool
# → email: alice@example.com
# → username: alice
# → password: ****

# 2. First user is promoted to admin (no key needed)
/promote_to_admin_tool
# → user_id: alice's user ID
# → admin_api_key: (leave empty)

# 3. Configure ADMIN_API_KEY in .env
echo "ADMIN_API_KEY=secret_key_123" >> .env

# 4. Second user registers
/user_register_tool
# → email: bob@example.com
# → username: bob
# → password: ****

# 5. Admin promotes second user (key required now)
/promote_to_admin_tool
# → user_id: bob's user ID
# → admin_api_key: secret_key_123
```

### Admin API Key vs Admin User

| Feature | Admin User | Admin API Key |
|---------|------------|---------------|
| Created via | `user_register_tool` + `promote_to_admin_tool` | Environment variable |
| Authentication | JWT tokens | API key |
| User management | ✅ Yes | ✅ Yes |
| All scopes | ✅ Yes | ✅ Yes |
| Data isolation | ✅ Own collection | ❌ Access to ALL collections |
| Recommended for | Human admins | Service accounts, CI/CD |

### Alternative: Admin Updates User

An existing admin can also promote users via:

```
/update_user_tool
```

Provide:
- `user_id` - The user to promote
- `is_superuser` - `true`

---

## Quick Start

1. Copy environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your credentials:
- `OPENROUTER_API_KEY` - Get from https://openrouter.ai
- `QDRANT_URL` - Point to your existing Qdrant instance (or use local via docker-compose)

3. Start the server:
```bash
docker-compose up -d
```

4. The MCP server is available at `http://localhost:8000/mcp`

## Testing

For local development and running tests, see [Testing Guide](./docs/TESTING.md).

## Transport Protocol

This server uses `streamable-http` transport (recommended over SSE-based `http`).

### Endpoint
- `http://host:port/mcp` - Streamable HTTP transport

### Shutdown Behavior
The server is configured with a 10-second graceful shutdown timeout to match Docker's stop timeout. Active connections will be given time to complete before the server terminates.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `QDRANT_API_KEY` | - | Qdrant API key (if required) |
| `OPENROUTER_API_KEY` | - | **Required** - OpenRouter API key |
| `EMBEDDING_MODEL` | `Qwen/Qwen3-Embedding-8B` | Embedding model |
| `EMBEDDING_DIMENSIONS` | `4096` | Embedding vector dimensions (4096 for Qwen3-Embedding-8B) |
| `API_KEYS` | - | Comma-separated API keys (legacy, each key gets isolated Qdrant collection) |
| `ADMIN_API_KEY` | - | Admin API key with full access to all collections |
| `DB_PATH` | `./data/documents.db` | SQLite database path |
| `CHUNK_MAX_TOKENS` | `400` | Max tokens per chunk |
| `CHUNK_OVERLAP_TOKENS` | `50` | Token overlap between chunks |
| `SEARCH_MAX_RESULTS` | `5` | Default max search results |
| `SEARCH_MAX_TOKENS` | `2000` | Default token budget for responses |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `JWT_SECRET_KEY` | `change-this-secret-in-production` | **Important** - Secret key for JWT token signing |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token expiry time |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token expiry time |
| `API_KEY_DEFAULT_EXPIRY_DAYS` | - | Default expiry for new API keys (None = no expiry) |

## MCP Tools

### Document Tools

#### store_document_tool
Store a markdown document with automatic chunking and embedding generation.

**Parameters:**
- `title` (string) - Document title
- `content` (string) - Markdown content
- `document_type` (string) - Type: markdown, pdf, docx, html, text, json
- `metadata` (object) - Optional custom metadata

**Returns:** `document_id`, `chunk_count`, `token_count`

---

#### search_documents_tool
Semantic search across all documents using embeddings.

**Parameters:**
- `query` (string) - Search query
- `max_results` (int) - Max results (default: 5)
- `max_tokens` (int) - Token budget (default: 2000)

**Returns:** List of relevant chunks with source info, formatted as markdown

---

#### get_document_tool
Retrieve full document by ID.

**Parameters:**
- `document_id` (string) - Document UUID

**Returns:** Full document content with metadata

---

#### list_documents_tool
List all documents with pagination.

**Parameters:**
- `limit` (int) - Number of documents (default: 50)
- `offset` (int) - Pagination offset (default: 0)

**Returns:** List of documents

---

#### update_document_tool
Update an existing document, replacing its content and re-generating embeddings.

**Parameters:**
- `document_id` (string) - Document UUID
- `title` (string) - New document title
- `content` (string) - New markdown content
- `document_type` (string) - Type: markdown, pdf, docx, html, text, json
- `doc_metadata` (object) - Optional custom metadata

**Returns:** `document_id`, `chunk_count`, `token_count`

---

#### delete_document_tool
Delete a document and all its chunks.

**Parameters:**
- `document_id` (string) - Document UUID

**Returns:** Success confirmation

---

### User Authentication Tools

#### user_register_tool
Register a new user account. **This tool is public and does not require authentication.**

**Parameters:**
- `email` (string) - User email address
- `username` (string) - Unique username
- `password` (string) - User password

**Returns:** Created user information

---

#### promote_to_admin_tool
Promote an existing user to admin. **Public tool - first promotion is automatic, subsequent require ADMIN_API_KEY.**

**Parameters:**
- `user_id` (string) - UUID of the user to promote
- `admin_api_key` (string, optional) - Required if an admin already exists

**Returns:** Updated user information with admin rights

---

#### user_login_tool
Authenticate a user and receive access and refresh tokens.

**Parameters:**
- `username` (string) - User username
- `password` (string) - User password

**Returns:** `access_token`, `refresh_token`, `token_type`, `expires_in`

---

#### user_profile_tool
Get the current authenticated user's profile information.

**Parameters:** None (uses JWT authentication)

**Returns:** Current user profile

---

#### user_refresh_tool
Refresh an access token using a valid refresh token.

**Parameters:**
- `refresh_token` (string) - Valid refresh token

**Returns:** New `access_token`, `refresh_token`, `token_type`, `expires_in`

---

### API Key Management Tools

#### create_api_key_tool
Create a new API key for a specific collection.

**Parameters:**
- `label` (string) - Descriptive label for the API key
- `collection_id` (string) - UUID of the collection to grant access to
- `permission` (string) - `"read"` or `"read_write"`. Default: `"read_write"`
- `expires_in_days` (int, optional) - Expiry in days

**Returns:** Created API key (only shown once), with collection info

---

#### list_api_keys_tool
List all API keys for the current user. Admins see all keys.

**Parameters:** None

**Returns:** List of API keys with collection name and permission (without actual key values)

---

#### revoke_api_key_tool
Revoke (deactivate) an API key.

**Parameters:**
- `key_id` (string) - ID of the API key to revoke

**Returns:** Success confirmation

---

#### rotate_api_key_tool
Rotate an API key. The old key is revoked and a new one is created with the same collection and permission.

**Parameters:**
- `key_id` (string) - ID of the API key to rotate

**Returns:** New API key (only shown once)

---

### Collection Management Tools

#### create_collection_tool
Create a new collection owned by the authenticated user.

**Parameters:**
- `name` (string) - User-friendly name for the collection

**Returns:** Created collection with `id`, `name`, `document_count`, `api_key_count`

---

#### list_collections_tool
List all collections owned by the authenticated user. **Requires JWT authentication.**

**Parameters:** None

**Returns:** List of collections with `id`, `name`, `created_at`

---

#### get_collection_tool
Get details of a specific collection.

**Parameters:**
- `collection_id` (string) - UUID of the collection

**Returns:** Collection details with `id`, `name`, `document_count`, `api_key_count`, `created_at`

---

#### delete_collection_tool
Delete a collection and all its documents. **Fails if the collection has active API keys.**

**Parameters:**
- `collection_id` (string) - UUID of the collection to delete

**Returns:** Success confirmation

---

#### rename_collection_tool
Rename a collection.

**Parameters:**
- `collection_id` (string) - UUID of the collection to rename
- `name` (string) - New name for the collection

**Returns:** Updated collection information

---

### Admin Tools (require `admin` scope)

#### list_users_tool
List all users. Requires admin scope.

**Parameters:**
- `limit` (int) - Number of users (default: 50)
- `offset` (int) - Pagination offset (default: 0)

**Returns:** List of users

---

#### get_user_tool
Get a specific user by ID. Requires admin scope.

**Parameters:**
- `user_id` (string) - UUID of the user

**Returns:** User information

---

#### update_user_tool
Update a user. Requires admin scope.

**Parameters:**
- `user_id` (string) - UUID of the user to update
- `email` (string, optional) - New email address
- `username` (string, optional) - New username
- `password` (string, optional) - New password
- `is_active` (bool, optional) - Account active status
- `is_superuser` (bool, optional) - Superuser status

**Returns:** Updated user information

---

#### delete_user_tool
Delete a user. Requires admin scope.

**Parameters:**
- `user_id` (string) - UUID of the user to delete

**Returns:** Success confirmation

## Authentication

The server supports two authentication methods:

### 1. JWT Token Authentication
Users authenticate with username/password via `user_login_tool` to receive JWT tokens:

```
Authorization: Bearer <jwt_access_token>
```

JWT tokens contain:
- User ID, username, email
- Scopes (read, write, admin)
- Expiration time

**JWT users can:**
- Manage collections (create, list, get, delete, rename)
- Create and manage API keys
- View their profile

**JWT users cannot:**
- Store/update/delete documents directly (must use an API key)

### 2. API Key Authentication
API keys are created via `create_api_key_tool` and are assigned to a specific collection:

```
Authorization: Bearer <api_key>
```

API keys have:
- Associated collection (required)
- Permission level (`read` or `read_write`)
- Optional expiration date

**API keys with `read_write` can:**
- Store documents
- Update documents
- Delete documents
- Search and read documents

**API keys with `read` can only:**
- Search documents
- Get documents
- List documents

### Permission Model

| Permission | Read | Write | Description |
|------------|------|-------|-------------|
| `read` | ✅ | ❌ | Search, get, list documents |
| `read_write` | ✅ | ✅ | Full document operations |

---

## Collection-Based Data Model

Data is organized into **collections**, each owned by a user:

```
User "alice" (user_id: abc123):
├── Collection "default" → documents, embeddings
│   ├── API Key "work-laptop" → read_write
│   └── API Key "mobile" → read
├── Collection "personal" → documents, embeddings
│   └── API Key "personal-key" → read_write
└── Collection "work" → documents, embeddings
    └── API Key "readonly-colleague" → read
```

### Key Benefits

1. **Lost key recovery**: If you lose an API key, create a new key for the same collection - no data loss!
2. **Granular access**: Give read-only keys to colleagues, keep read_write for yourself
3. **Organization**: Separate documents into different collections by topic/project

### Collection Assignment

| Auth Type | Collection | Access |
|-----------|------------|--------|
| API Key | Assigned collection only | Based on permission |
| JWT User | Any owned collection | Management only (no document ops) |
| Admin API Key | All collections | Full access |
| Superuser | Any collection | Full access |

### Example Workflows

#### Personal Knowledge Base
```
1. Register account → "default" collection created
2. Create API key with read_write for "default"
3. Store and search documents
```

#### Team Collaboration (Read-Only)
```
1. Admin creates collection "team-docs"
2. Admin stores documents using read_write key
3. Admin creates read-only keys for team members
4. Team members can search but not modify
```

#### Multiple Projects
```
1. Create collections: "work", "personal", "side-project"
2. Create separate API keys for each
3. Use appropriate key for each context
```

---

## Legacy API Keys

**Two ways to configure API keys:**
1. **Environment variable** - Add to `API_KEYS` comma-separated list (legacy, no collection association)
2. **Database** - Create via `create_api_key_tool` (recommended, with collection and permission)

Legacy API keys (from environment) get `read_write` permission and their own isolated collection.

### Admin Access

The `ADMIN_API_KEY` environment variable defines a special key with:
- Access to all collections (no isolation)
- Full read_write access

## Database Migrations

This project uses Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## MCP Configuration for AI Agents

### Claude Desktop

Add to `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`, Linux: `~/.config/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ainstruct-mcp": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "--port", "8000"],
      "env": {
        "AINSTRUCT_URL": "http://localhost:8000/mcp",
        "AINSTRUCT_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Cursor

Add to Cursor settings (`.cursor/mcp.json` in project or global settings):

```json
{
  "mcpServers": {
    "ainstruct-mcp": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "--port", "8000"],
      "env": {
        "AINSTRUCT_URL": "http://localhost:8000/mcp",
        "AINSTRUCT_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Other MCP Clients

For other MCP-compatible clients, use the HTTP server URL:

```
http://localhost:8000/mcp
```

Pass the API key or JWT token via the `Authorization` header:
```
Authorization: Bearer your_api_key_or_jwt_token
```

## Docker Deployment

```yaml
services:
  mcp_server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - QDRANT_URL=${QDRANT_URL}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    volumes:
      - ./data:/app/data

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
```
