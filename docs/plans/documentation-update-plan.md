# Documentation Update Plan

## Overview

Update documentation to reflect the current state of available MCP tools and REST API endpoints. The existing documentation references tools and endpoints that no longer exist or have been renamed.

## Current Issues

### MCP Tools Documentation (README.md lines 175-216)

| Documentation Says | Actual Tool | Action |
|-------------------|-------------|--------|
| `user_register_tool` | Does not exist (REST only) | Remove |
| `user_login_tool` | Does not exist (REST only) | Remove |
| `user_profile_tool` | Does not exist (REST only) | Remove |
| `user_refresh_tool` | Does not exist (REST only) | Remove |
| `promote_to_admin_tool` | Does not exist (REST only) | Remove |
| `create_cat_tool` | `create_collection_access_token_tool` | Rename |
| `list_cats_tool` | `list_collection_access_tokens_tool` | Rename |
| `revoke_cat_tool` | `revoke_collection_access_token_tool` | Rename |
| `rotate_cat_tool` | `rotate_collection_access_token_tool` | Rename |
| `create_pat_token_tool` | Does not exist (REST only) | Remove |
| `list_pat_tokens_tool` | Does not exist (REST only) | Remove |
| `revoke_pat_token_tool` | Does not exist (REST only) | Remove |
| `rotate_pat_token_tool` | Does not exist (REST only) | Remove |
| `list_users_tool` | Does not exist (REST only) | Remove |
| `get_user_tool` | Does not exist (REST only) | Remove |
| `update_user_tool` | Does not exist (REST only) | Remove |
| `delete_user_tool` | Does not exist (REST only) | Remove |
| *(missing)* | `move_document_tool` | Add |

### REST API Documentation

| Documentation | Actual Endpoint | Action |
|--------------|-----------------|--------|
| Missing | `GET /admin/users/search` | Add |
| Missing | `POST /admin/users/{user_id}/promote` | Add |

## Changes Required

### 1. MCP Tools Section (lines 175-216)

Replace entire MCP Tools section with:

```markdown
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
```

### 2. New User Onboarding Section (lines 63-152)

- Remove all MCP tool references for user management (lines 76-80, 91-95, 111-115, 129-133)
- Keep only REST API examples for registration, login, and credential creation
- Note: User authentication is REST API only

### 3. Admin Users Section (lines 154-163)

Replace `/promote_to_admin_tool` reference with:
- `POST /api/v1/admin/users/{user_id}/promote` (REST API)

### 4. REST API Section (lines 342-357)

Expand to show all available endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Register new user |
| `/auth/login` | POST | Login and get JWT tokens |
| `/auth/refresh` | POST | Refresh JWT token |
| `/auth/profile` | GET | Get user profile |
| `/auth/pat` | POST | Create PAT token |
| `/auth/pat` | GET | List PAT tokens |
| `/auth/pat/{pat_id}` | DELETE | Revoke PAT token |
| `/auth/pat/{pat_id}/rotate` | POST | Rotate PAT token |
| `/auth/cat` | POST | Create CAT token |
| `/auth/cat` | GET | List CAT tokens |
| `/auth/cat/{cat_id}` | DELETE | Revoke CAT token |
| `/auth/cat/{cat_id}/rotate` | POST | Rotate CAT token |
| `/collections` | POST | Create collection |
| `/collections` | GET | List collections |
| `/collections/{collection_id}` | GET | Get collection |
| `/collections/{collection_id}` | PATCH | Rename collection |
| `/collections/{collection_id}` | DELETE | Delete collection |
| `/documents` | POST | Store document |
| `/documents` | GET | List documents |
| `/documents/{document_id}` | GET | Get document |
| `/documents/{document_id}` | PATCH | Update document |
| `/documents/{document_id}` | DELETE | Delete document |
| `/documents/search` | POST | Semantic search |
| `/admin/users` | GET | List users |
| `/admin/users/search` | GET | Search users |
| `/admin/users/{user_id}` | GET | Get user details |
| `/admin/users/{user_id}` | PATCH | Update user |
| `/admin/users/{user_id}` | DELETE | Delete user |
| `/admin/users/{user_id}/promote` | POST | Promote to admin |

## Notes

- User management tools (register, login, profile, refresh) are only available via REST API
- PAT and CAT token management is only available via REST API
- Admin operations are only available via REST API
- MCP tools are focused on document and collection operations only
- Authentication for MCP uses PAT or CAT tokens (not JWT)

## Files to Modify

1. `README.md` - Main documentation updates
