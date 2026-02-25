# AI Document Memory MCP Server

Remote MCP server for storing and searching markdown documents with semantic embeddings. Features user authentication with JWT tokens, API key management with permissions, and collection-based data organization.

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

## New User Onboarding

### Step 1: Register Account
```
/user_register_tool
```
Provide email, username, and password. A "default" collection is automatically created.

### Step 2: Login
```
/user_login_tool
```
Save the returned `access_token` and `refresh_token`.

### Step 3: Create Authentication Credential

You have two options for authentication:

#### Option A: API Key (Collection-Specific)
```
/create_api_key_tool
```
Provide a label, collection ID (from `/list_collections_tool`), permission, and optional expiry. Save the returned key.

**Use this if**: You only need access to a single collection for document operations.

#### Option B: PAT Token (User-Level)
```
/create_pat_token_tool
```
Provide a label and optional expiry. Save the returned token.

**Use this if**: You need access to all your collections or want to perform management operations (create collections, manage API keys, etc.).

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

Admin users (`is_superuser=True`) have full access to all admin tools (user management) and all scopes implicitly.

### Promote to Admin
```
/promote_to_admin_tool
```
- First promotion: No admin API key needed
- Subsequent promotions: Requires `ADMIN_API_KEY` environment variable

## Key Features

- **Document Management**: Store, retrieve, update, and delete markdown documents with automatic chunking
- **Semantic Search**: Search documents using embeddings (OpenRouter models)
- **Collections**: Organize documents into user-owned collections with granular permissions
- **API Keys**: Create, revoke, and rotate API keys with read/write permissions
- **User Authentication**: JWT-based login with refresh tokens
- **Admin Tools**: Manage users and view all collections (admin only)

## MCP Tools

### Document Tools
- `store_document_tool` - Store documents with embeddings
- `search_documents_tool` - Semantic search
- `get_document_tool` - Retrieve by ID
- `list_documents_tool` - List documents
- `update_document_tool` - Update documents
- `delete_document_tool` - Delete documents

### User Tools
- `user_register_tool` - Register new accounts (public)
- `user_login_tool` - Authenticate and get tokens
- `user_profile_tool` - Get profile info
- `user_refresh_tool` - Refresh access tokens
- `promote_to_admin_tool` - Promote users to admin

### API Key Tools
- `create_api_key_tool` - Create API keys (collection-specific)
- `list_api_keys_tool` - List keys
- `revoke_api_key_tool` - Revoke keys
- `rotate_api_key_tool` - Rotate keys

### PAT Token Tools
- `create_pat_token_tool` - Create Personal Access Tokens (user-level)
- `list_pat_tokens_tool` - List PAT tokens
- `revoke_pat_token_tool` - Revoke PAT tokens
- `rotate_pat_token_tool` - Rotate PAT tokens

### Collection Tools
- `create_collection_tool` - Create collections
- `list_collections_tool` - List collections
- `get_collection_tool` - Get collection details
- `delete_collection_tool` - Delete collections
- `rename_collection_tool` - Rename collections

### Admin Tools
- `list_users_tool` - List all users
- `get_user_tool` - Get user details
- `update_user_tool` - Update users
- `delete_user_tool` - Delete users

## Authentication

### JWT Tokens
- Obtained via `/user_login_tool`
- Used for user and collection management
- Expire after 30 minutes (refreshable)

### API Keys
- Created via `/create_api_key_tool`
- **Collection-specific**: Assigned to a single collection
- Permissions: `read` (search/get) or `read_write` (full access)
- Optional expiration dates
- **Use case**: Document operations (store, search, update, delete)

### Personal Access Tokens (PAT)
- Created via `/create_pat_token_tool`
- **User-level**: Bound to a user account, not a specific collection
- **Inherits user scopes**: Read, write, and admin permissions from the user
- Optional expiration dates (max configurable via `PAT_MAX_EXPIRY_DAYS`)
- **Use case**: Full API access - document operations (all collections), user/collection management, API key management
- **Prefix**: `pat_live_`

### Comparison: API Key vs PAT Token

| Feature | API Key | PAT Token |
|---------|---------|-----------|
| Scope | Single collection | All user's collections |
| Permissions | read or read_write | Inherits user's scopes (read, write, admin) |
| Use Case | Document operations | Full API access (documents + management) |
| Creation | Requires JWT/PAT | Requires JWT |
| Collection Binding | Yes (one collection) | No (all user collections) |
| User Binding | No (bound to collection) | Yes (bound to user) |
| Prefix | `ak_live_` | `pat_live_`

## Collection-Based Data Model

Documents are organized into user-owned collections:
- Each user gets a "default" collection on registration
- Collections can have multiple API keys with different permissions
- Data is isolated per collection
- Lost keys can be replaced without data loss

## Environment Variables

Essential variables:
| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | - | **Required** - OpenRouter API key |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `JWT_SECRET_KEY` | `change-this-secret-in-production` | Secret key for JWT token signing |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |

PAT Token settings:
| Variable | Default | Description |
|----------|---------|-------------|
| `PAT_DEFAULT_EXPIRY_DAYS` | `90` | Default expiry for new PAT tokens |
| `PAT_MAX_EXPIRY_DAYS` | `365` | Maximum allowed expiry for PAT tokens |

For a full list, see `docker-compose.yml` and `.env.example`.

## MCP Configuration

For any MCP-compatible client, use the following configuration:

1. MCP server URL: `http://localhost:8000/mcp`
2. Authentication: Pass your API key or JWT token via the `Authorization` header:
   ```
   Authorization: Bearer YOUR_API_KEY_OR_JWT_TOKEN
   ```

Consult your MCP client's documentation for specific configuration file formats and locations.

## Development

### Testing
```bash
./run_tests.sh
```
Runs linting, type checking, and tests.

### Database Migrations
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

For more details, see [Testing Guide](./docs/TESTING.md) and [Development Guide](./docs/DEVELOPMENT.md).

## License

MIT
