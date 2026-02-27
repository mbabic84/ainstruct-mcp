# Plan: Remove User, PAT, and Admin MCP Tools

**Date:** 2026-02-27
**Status:** Completed

---

## Overview

Remove MCP tools that have equivalent REST endpoints, keeping only tools related to documents, collections, and CATs.

---

## Tools to Remove (13 total)

| Category | MCP Tool | REST Equivalent |
|----------|----------|-----------------|
| **User** | `user_register_tool` | `POST /auth/register` |
| **User** | `user_login_tool` | `POST /auth/login` |
| **User** | `user_refresh_tool` | `POST /auth/refresh` |
| **User** | `user_profile_tool` | `GET /auth/profile` |
| **PAT** | `create_pat_token_tool` | `POST /auth/pat` |
| **PAT** | `list_pat_tokens_tool` | `GET /auth/pat` |
| **PAT** | `revoke_pat_token_tool` | `DELETE /auth/pat/{pat_id}` |
| **PAT** | `rotate_pat_token_tool` | `POST /auth/pat/{pat_id}/rotate` |
| **Admin** | `list_users_tool` | `GET /admin/users` |
| **Admin** | `search_users_tool` | `GET /admin/users/search` |
| **Admin** | `get_user_tool` | `GET /admin/users/{user_id}` |
| **Admin** | `update_user_tool` | `PATCH /admin/users/{user_id}` |
| **Admin** | `delete_user_tool` | `DELETE /admin/users/{user_id}` |

---

## Tools to Keep (16 total)

| Category | Tools |
|----------|-------|
| **Documents** | `store_document_tool`, `search_documents_tool`, `get_document_tool`, `list_documents_tool`, `delete_document_tool`, `update_document_tool`, `move_document_tool` |
| **Collections** | `create_collection_tool`, `list_collections_tool`, `get_collection_tool`, `rename_collection_tool`, `delete_collection_tool` |
| **CATs** | `create_collection_access_token_tool`, `list_collection_access_tokens_tool`, `revoke_collection_access_token_tool`, `rotate_collection_access_token_tool` |

---

## Files to Modify

### 1. `services/mcp-server/src/mcp_server/server.py`
- Remove imports from `user_tools.py`, `pat_tools.py`, `admin_tools.py`
- Remove 13 tool function definitions

### 2. `services/mcp-server/src/mcp_server/tools/auth.py`
- Remove from `PUBLIC_TOOLS`: `user_register_tool`, `user_login_tool`, `user_refresh_tool`
- Remove from `USER_TOOLS`: `user_profile_tool`
- Remove from `ADMIN_TOOLS`: `list_users_tool`, `search_users_tool`, `get_user_tool`, `update_user_tool`, `delete_user_tool`

### 3. Delete files
- `services/mcp-server/src/mcp_server/tools/user_tools.py`
- `services/mcp-server/src/mcp_server/tools/pat_tools.py`
- `services/mcp-server/src/mcp_server/tools/admin_tools.py`

### 4. Update tests
- `tests/unit/mcp/test_server.py` - Remove tests for removed tools

---

## Impact Assessment

| Impact | Details |
|--------|---------|
| Breaking change | Yes - clients using MCP for user/PAT/admin management must switch to REST API |
| Migration path | Use REST endpoints: `/auth/*`, `/auth/pat*`, `/admin/users*` |
| Auth middleware | Update to remove references to deleted tool auth sets |

---

## Execution Order

1. Modify `services/mcp-server/src/mcp_server/tools/auth.py`
2. Modify `services/mcp-server/src/mcp_server/server.py`
3. Delete `user_tools.py`, `pat_tools.py`, `admin_tools.py`
4. Update tests in `tests/unit/mcp/test_server.py`
5. Run lint and type checks
6. Run tests to verify no regressions
