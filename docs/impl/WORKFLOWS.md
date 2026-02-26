# Workflows Documentation

This document provides an overview of user workflows. For detailed specifications, see the dedicated documents.

---

## Architecture Overview

The system is a **Remote MCP Server** for storing and searching markdown documents with semantic embeddings. It uses a **dual authentication model** with **collection-based data isolation**.

### Two APIs

| API | Auth Method | Use Case |
|-----|-------------|----------|
| **REST API** | JWT (short-lived) | Web UI, CLI, interactive sessions |
| **MCP API** | PAT or CAT (long-lived) | AI agents, automation, integrations |

### Data Layer

| Storage | Purpose |
|---------|---------|
| SQLite | Users, Collections, PATs, CATs, Document metadata |
| Qdrant | Document embeddings, Semantic search |

---

## Quick Reference

### Token Types

| Token | Prefix | API | Scope |
|-------|--------|-----|-------|
| JWT | 3 parts (dots) | REST | User's scopes |
| PAT | `pat_live_` | MCP | User-level (all collections) |
| CAT | `cat_live_` | MCP | Collection-specific |

### Operations by API

| Operation | REST API | MCP API |
|-----------|----------|---------|
| User Registration | ✅ | ❌ |
| User Login | ✅ | ❌ |
| PAT Management | ✅ | ❌ |
| CAT Management | ✅ | ✅ |
| Collection Management | ✅ | ✅ |
| Document Operations | ✅ | ✅ |
| Admin User Management | ✅ | ✅ |

---

## Common Workflows

### New User Onboarding

1. **Register** → REST API `POST /auth/register`
2. **Login** → REST API `POST /auth/login` → Get JWT
3. **Create PAT** → REST API `POST /auth/pat` with JWT → Get PAT
4. **Configure MCP** → Use PAT in MCP config
5. **Use MCP Tools** → Document and collection operations

### Sharing Collection Access

1. **Create CAT** → MCP `create_cat_tool` or REST `POST /auth/cat`
2. **Share CAT** → Send token to recipient
3. **Recipient uses CAT** → Configure MCP with CAT

### Admin Tasks

1. **Admin login** → REST API `POST /auth/login`
2. **User management** → REST API `/admin/*` endpoints

---

## Detailed Documentation

| Topic | Document |
|-------|----------|
| Implementation phases | `IMPLEMENTATION_PLAN.md` |
| REST API endpoints | `REST_API.md` |
| MCP API tools | `MCP_API.md` |
| Authentication flows | `AUTHENTICATION.md` |
| Database migration | `DATABASE_MIGRATION.md` |
| Breaking changes | `BREAKING_CHANGES.md` |
| User permissions | `USER_PERMISSIONS.md` |
| Testing | `TESTING.md` |

---

## Environment Variables

```bash
# Database
DB_PATH=./data/documents.db

# Qdrant
QDRANT_URL=http://localhost:6333

# Embeddings
OPENROUTER_API_KEY=your-key
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B
EMBEDDING_DIMENSIONS=4096

# JWT
JWT_SECRET_KEY=change-this-secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Admin
ADMIN_API_KEY=                    # Optional admin access
```

---

## Support

For implementation questions, refer to:
- `IMPLEMENTATION_PLAN.md` - Phase-by-phase implementation guide
- `REST_API.md` - Complete REST endpoint reference
- `MCP_API.md` - Complete MCP tool reference