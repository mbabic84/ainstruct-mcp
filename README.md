# AI Document Memory MCP Server

Remote MCP server for storing and searching markdown documents with semantic embeddings. Features user authentication with JWT tokens, CAT (Collection Access Token) management with permissions, and collection-based data organization.

## Architecture

The system consists of two services:

| Service | Default Port | Purpose |
|---------|--------------|---------|
| MCP Server | 8000 | MCP protocol for AI agents |
| REST API | 8001 | REST API for authentication and management |

Both share the same database (PostgreSQL) and vector store (Qdrant).

### Changing Ports

To change the default ports, set the `PORT` environment variable:

**MCP Server:**
```bash
docker run -e SERVICE=mcp-server -e PORT=9000 ...
```

**REST API:**
```bash
docker run -e SERVICE=rest-api -e PORT=9001 ...
```

Or in docker-compose, modify the `ports` mapping:
```yaml
mcp_server:
  ports:
    - "9000:9000"  # host:container

rest_api:
  environment:
    - PORT=9001
  ports:
    - "9001:9001"

## Quick Start

1. Copy environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your credentials:
- `POSTGRES_PASSWORD` - Required for PostgreSQL
- `OPENROUTER_API_KEY` - Get from https://openrouter.ai
- `API_KEYS` - Comma-separated list of allowed API keys
- `ADMIN_API_KEY` - Admin authentication key

3. Start the server:
```bash
docker-compose up -d
```

4. The MCP server is available at `http://localhost:8000/mcp`
5. The REST API is available at `http://localhost:8001/api/v1`

## New User Onboarding

User management (registration, login, token management) is available via the REST API only.

### Step 1: Register Account

**REST API**:
```bash
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "alice", "password": "secure123"}'
```

A "default" collection is automatically created for new users.

### Step 2: Login

**REST API**:
```bash
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secure123"}'
```

Save the returned `access_token` and `refresh_token`.

### Step 3: Create Authentication Credential

You have two options for authentication:

#### Option A: CAT (Collection Access Token)

**REST API**:
```bash
curl -X POST http://localhost:8001/api/v1/auth/cat \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"label": "My Client", "collection_id": "<uuid>", "permission": "read_write"}'
```

Provide a label, collection ID (from `/collections`), permission, and optional expiry. Save the returned token.

**Use this if**: You only need access to a single collection for document operations.

#### Option B: PAT Token (User-Level)

**REST API**:
```bash
curl -X POST http://localhost:8001/api/v1/auth/pat \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"label": "My Client"}'
```

Provide a label and optional expiry. Save the returned token.

**Use this if**: You need access to all your collections or want to perform management operations (create collections, manage CATs, etc.).

### Step 4: Configure Client
Update your MCP client config:
```json
{
  "mcp": {
    "ainstruct": {
      "type": "remote",
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY_OR_PAT_TOKEN_HERE"
      },
      "enabled": true
    }
  }
}
```

## Admin Users

Admin users (`is_superuser=True`) have full access to all admin REST API endpoints.

### Promote to Admin

```bash
curl -X POST http://localhost:8001/api/v1/admin/users/<user_id>/promote \
  -H "X-Admin-API-Key: <your-admin-api-key>"
```

- Requires valid `X-Admin-API-Key` header
- Works regardless of existing admin users

## Key Features

- **Document Management**: Store, retrieve, update, and delete markdown documents with automatic chunking
- **Semantic Search**: Search documents using embeddings (OpenRouter models)
- **Collections**: Organize documents into user-owned collections with granular permissions
- **CATs (Collection Access Tokens)**: Create, revoke, and rotate tokens with read/write permissions
- **User Authentication**: JWT-based login with refresh tokens
- **Admin Tools**: Manage users and view all collections (admin only)
- **REST API**: Separate REST API service on port 8001

## MCP Tools

### Document Tools
- `store_document_tool` - Store documents with embeddings
- `search_documents_tool` - Semantic search
- `get_document_tool` - Retrieve by ID
- `list_documents_tool` - List documents
- `update_document_tool` - Update documents
- `delete_document_tool` - Delete documents
- `move_document_tool` - Move document between collections

### Collection Access Token (CAT) Tools
- `create_collection_access_token_tool` - Create CATs (collection-specific tokens)
- `list_collection_access_tokens_tool` - List CATs
- `revoke_collection_access_token_tool` - Revoke CATs
- `rotate_collection_access_token_tool` - Rotate CATs

### Collection Tools
- `create_collection_tool` - Create collections
- `list_collections_tool` - List collections
- `get_collection_tool` - Get collection details
- `delete_collection_tool` - Delete collections
- `rename_collection_tool` - Rename collections

## Authentication

The system uses two APIs with different authentication methods:

| API | Purpose | Auth Method |
|-----|---------|-------------|
| REST API | Interactive auth + operations | JWT (short-lived) |
| MCP API | AI agent operations | PAT or CAT (long-lived) |

### JWT Tokens
- Obtained via REST API `/api/v1/auth/login`
- Used for REST API operations and token management
- Expire after 30 minutes (refreshable via `/api/v1/auth/refresh`)
- **Not recommended for MCP** - use PAT or CAT instead

### Collection Access Tokens (CATs)
- Created via REST API `/api/v1/auth/cat`
- **Collection-specific**: Assigned to a single collection
- Permissions: `read` (search/get) or `read_write` (full access)
- Optional expiration dates
- **Use case**: Document operations (store, search, update, delete)
- **Prefix**: `cat_live_`

### Personal Access Tokens (PAT)
- Created via REST API `/api/v1/auth/pat`
- **User-level**: Bound to a user account, not a specific collection
- **Inherits user scopes**: Read, write, and admin permissions from the user
- Optional expiration dates (max configurable via `PAT_MAX_EXPIRY_DAYS`)
- **Use case**: Full API access - document operations (all collections), user/collection management, CAT management
- **Prefix**: `pat_live_`

### Comparison: CAT vs PAT Token

| Feature | CAT | PAT Token |
|---------|-----|-----------|
| Scope | Single collection | All user's collections |
| Permissions | read or read_write | Inherits user's scopes (read, write, admin) |
| Use Case | Document operations | Full API access (documents + management) |
| Creation | Requires JWT/PAT | Requires JWT |
| Collection Binding | Yes (one collection) | No (all user collections) |
| User Binding | No (bound to collection) | Yes (bound to user) |
| Prefix | `cat_live_` | `pat_live_`

## Collection-Based Data Model

Documents are organized into user-owned collections:
- Each user gets a "default" collection on registration
- Collections can have multiple CATs with different permissions
- Data is isolated per collection
- Lost tokens can be replaced without data loss

## Environment Variables

All environment variables are used by both the MCP Server and REST API unless otherwise noted. The `SERVICE` variable determines which service runs.

### Service Selection

| Variable | Required | Description |
|----------|----------|-------------|
| `SERVICE` | Yes | Which service to run: `mcp-server` (default port 8000) or `rest-api` (default port 8001) |

### Database

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DATABASE_URL` | - | Yes | PostgreSQL connection string (e.g., `postgresql+asyncpg://user:pass@host:5432/db`) |
| `POSTGRES_PASSWORD` | - | Yes | PostgreSQL password (used in docker-compose) |

### Vector Store

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `QDRANT_URL` | `http://localhost:6333` | No | Qdrant server URL |
| `QDRANT_API_KEY` | - | No | Qdrant API key (optional) |
| `OPENROUTER_API_KEY` | - | Yes | OpenRouter API key for embeddings |
| `EMBEDDING_MODEL` | `Qwen/Qwen3-Embedding-8B` | No | Embedding model |
| `EMBEDDING_DIMENSIONS` | `4096` | No | Embedding dimensions |
| `USE_MOCK_EMBEDDINGS` | `false` | No | Use deterministic hash-based vectors for testing |

### Authentication

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `API_KEYS` | - | Yes | Comma-separated list of allowed API keys (for MCP client auth) |
| `ADMIN_API_KEY` | - | Yes | Admin authentication key |
| `JWT_SECRET_KEY` | `change-this-secret-in-production` | Yes | Secret key for JWT token signing |
| `JWT_ALGORITHM` | `HS256` | No | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | No | Access token expiry time |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | No | Refresh token expiry time |

### PAT Token Settings

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `PAT_DEFAULT_EXPIRY_DAYS` | `90` | No | Default expiry for new PAT tokens |
| `PAT_MAX_EXPIRY_DAYS` | `365` | No | Maximum allowed expiry for PAT tokens |

### Server Configuration

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `HOST` | `0.0.0.0` | No | Server host |
| `PORT` | `8000` (MCP), `8001` (REST) | No | Server port. MCP defaults to 8000, REST API defaults to 8001 |

### Document Processing

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `CHUNK_MAX_TOKENS` | `400` | No | Maximum tokens per document chunk |
| `CHUNK_OVERLAP_TOKENS` | `50` | No | Overlap between chunks |
| `SEARCH_MAX_RESULTS` | `5` | No | Maximum search results |
| `SEARCH_MAX_TOKENS` | `2000` | No | Maximum tokens in search results |

## MCP Configuration

For any MCP-compatible client, use the following configuration:

1. MCP server URL: `http://localhost:8000/mcp` (or custom PORT if changed)
2. Authentication: Pass your PAT or CAT token via the `Authorization` header:
   ```
   Authorization: Bearer YOUR_PAT_OR_CAT_TOKEN
   ```

Consult your MCP client's documentation for specific configuration file formats and locations.

## REST API Configuration

The REST API is available at `http://localhost:8001/api/v1` with the following endpoints:

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login and get JWT tokens |
| POST | `/auth/refresh` | Refresh JWT token |
| GET | `/auth/profile` | Get user profile |

### PAT Tokens

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/pat` | Create PAT token |
| GET | `/auth/pat` | List PAT tokens |
| DELETE | `/auth/pat/{pat_id}` | Revoke PAT token |
| POST | `/auth/pat/{pat_id}/rotate` | Rotate PAT token |

### CAT Tokens

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/cat` | Create CAT token |
| GET | `/auth/cat` | List CAT tokens |
| DELETE | `/auth/cat/{cat_id}` | Revoke CAT token |
| POST | `/auth/cat/{cat_id}/rotate` | Rotate CAT token |

### Collections

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/collections` | Create collection |
| GET | `/collections` | List collections |
| GET | `/collections/{collection_id}` | Get collection |
| PATCH | `/collections/{collection_id}` | Rename collection |
| DELETE | `/collections/{collection_id}` | Delete collection |

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/documents` | Store document |
| GET | `/documents` | List documents |
| GET | `/documents/{document_id}` | Get document |
| PATCH | `/documents/{document_id}` | Update document |
| DELETE | `/documents/{document_id}` | Delete document |
| POST | `/documents/search` | Semantic search |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/users` | List users |
| GET | `/admin/users/search` | Search users |
| GET | `/admin/users/{user_id}` | Get user details |
| PATCH | `/admin/users/{user_id}` | Update user |
| DELETE | `/admin/users/{user_id}` | Delete user |
| POST | `/admin/users/{user_id}/promote` | Promote to admin |

Authentication uses JWT Bearer tokens:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

## Development

### Testing
```bash
./scripts/test.sh
```
Runs linting, type checking, and tests using uv.

For more details, see [Testing Guide](./docs/TESTING.md).

### Database Migrations
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

For more details, see [Testing Guide](./docs/TESTING.md).

## License

MIT
