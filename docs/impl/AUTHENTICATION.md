# Authentication Guide

This document explains the authentication model and token types for the ainstruct system.

---

## Authentication Overview

The system uses **two separate APIs** with different authentication requirements:

| API | Purpose | Auth Method | Use Case |
|-----|---------|-------------|----------|
| **REST API** | Interactive auth + operations | JWT (short-lived) | Web UI, CLI tools, token management |
| **MCP API** | AI agent operations | PAT or CAT (long-lived) | AI agents, automation, integrations |

---

## Token Types

### JWT Token (JSON Web Token)

**Use**: REST API only

**Format**: Three parts separated by dots
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOi... .signature
```

**Characteristics**:
| Property | Value |
|----------|-------|
| Lifetime | Access: 30 minutes, Refresh: 7 days |
| Storage | Stateless (not in database) |
| Revocation | Cannot revoke (until expired) |
| Creation | REST API login |
| API | REST only |

**JWT Payload**:
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

**When to use**:
- User registration
- User login
- Creating PAT tokens
- Managing PAT/CAT tokens
- Admin operations
- Web UI sessions
- CLI tools with interactive auth

---

### PAT (Personal Access Token)

**Use**: MCP API (primary) and REST API

**Format**: Prefix + 32 urlsafe characters
```
pat_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
└──────┘ └────────────────────────────────────┘
prefix   32 urlsafe characters
```

**Characteristics**:
| Property | Value |
|----------|-------|
| Lifetime | Configurable (days/months) |
| Storage | Database (hashed with SHA256) |
| Revocation | Can revoke/rotate |
| Creation | REST API (requires JWT) |
| API | MCP (primary), REST |
| Scope | Inherits user's scopes |

**When to use**:
- MCP client authentication (Claude, Cursor, etc.)
- Long-running integrations
- Automation scripts
- Any MCP API operations

---

### CAT (Collection Access Token)

**Use**: MCP API only

**Format**: Prefix + 32 urlsafe characters
```
cat_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
└──────┘ └────────────────────────────────────┘
prefix   32 urlsafe characters
```

**Characteristics**:
| Property | Value |
|----------|-------|
| Lifetime | Configurable (days/months) |
| Storage | Database (hashed with SHA256) |
| Revocation | Can revoke/rotate |
| Creation | REST API (JWT) or MCP API (PAT) |
| API | MCP only |
| Scope | Single collection, `read` or `read_write` |

**When to use**:
- Sharing collection access with others
- Limited-scope API access
- Third-party integrations (single collection)

---

## Token Comparison

| Property | JWT | PAT | CAT |
|----------|-----|-----|-----|
| **Format** | 3 parts (dots) | `pat_live_` + 32 chars | `cat_live_` + 32 chars |
| **Lifetime** | 30 min / 7 days | Configurable | Configurable |
| **Storage** | Stateless | DB (hashed) | DB (hashed) |
| **Revocable** | No | Yes | Yes |
| **Creation** | REST login | REST (JWT) | REST (JWT) or MCP (PAT) |
| **Scope** | User's scopes | User's scopes | Single collection |
| **REST API** | ✅ | ✅ | ❌ |
| **MCP API** | ❌ | ✅ | ✅ |

---

## Authentication Flows

### Flow 1: New User Onboarding

```
┌──────────────────────────────────────────────────────────────────┐
│ Step 1: Register Account (REST API)                               │
│                                                                   │
│ POST /auth/register                                               │
│ {email, username, password}                                       │
│                                                                   │
│ Result: User created + "default" collection auto-created          │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 2: Login (REST API)                                          │
│                                                                   │
│ POST /auth/login                                                  │
│ {username, password}                                              │
│                                                                   │
│ Result: {access_token: "jwt...", refresh_token: "jwt..."}         │
│ ⚠️ JWT expires in 30 minutes - NOT for MCP use                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 3: Create PAT (REST API, requires JWT)                       │
│                                                                   │
│ POST /auth/pat                                                    │
│ Authorization: Bearer <jwt_access_token>                          │
│ {label: "My MCP Client"}                                          │
│                                                                   │
│ Result: {token: "pat_live_xxx"}                                   │
│ ⚠️ Save this token - shown only once!                            │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 4: Configure MCP Client                                      │
│                                                                   │
│ In MCP config file (Claude Desktop, Cursor, etc.):                │
│                                                                   │
│ {                                                                 │
│   "mcp": {                                                        │
│     "ainstruct": {                                                │
│       "headers": {                                                │
│         "Authorization": "Bearer pat_live_xxx"                    │
│       }                                                           │
│     }                                                             │
│   }                                                               │
│ }                                                                 │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 5: Use MCP Tools                                             │
│                                                                   │
│ Available with PAT:                                               │
│ • store_document_tool - Store documents                           │
│ • search_documents_tool - Semantic search                         │
│ • get_document_tool - Retrieve by ID                              │
│ • create_collection_tool - Create collections                     │
│ • create_cat_tool - Create CATs for sharing                       │
│ • etc.                                                            │
└──────────────────────────────────────────────────────────────────┘
```

---

### Flow 2: Sharing Collection Access

```
┌──────────────────────────────────────────────────────────────────┐
│ Step 1: Create CAT (MCP with PAT or REST with JWT)                │
│                                                                   │
│ # Option A: Via MCP (with PAT)                                    │
│ create_cat_tool({                                                 │
│   label: "Colleague's Access",                                    │
│   collection_id: "uuid",                                          │
│   permission: "read"                                              │
│ })                                                                │
│                                                                   │
│ # Option B: Via REST (with JWT)                                   │
│ POST /auth/cat                                                    │
│ {label, collection_id, permission}                                │
│                                                                   │
│ Result: {token: "cat_live_xxx"}                                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 2: Share CAT with Recipient                                  │
│                                                                   │
│ Send: cat_live_xxx                                                │
│                                                                   │
│ ⚠️ Be careful who you share with!                                │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 3: Recipient Uses CAT                                        │
│                                                                   │
│ Configure MCP client with CAT:                                    │
│                                                                   │
│ {                                                                 │
│   "mcp": {                                                        │
│     "ainstruct": {                                                │
│       "headers": {                                                │
│         "Authorization": "Bearer cat_live_xxx"                    │
│       }                                                           │
│     }                                                             │
│   }                                                               │
│ }                                                                 │
│                                                                   │
│ Recipient can now access that specific collection.                │
└──────────────────────────────────────────────────────────────────┘
```

---

### Flow 3: JWT Refresh

```
┌──────────────────────────────────────────────────────────────────┐
│ JWT Token Lifecycle                                               │
│                                                                   │
│ Access Token ──30 min──> Expired                                  │
│        │                                                          │
│        └──Use refresh token──> New access + refresh tokens        │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

POST /auth/refresh
{refresh_token: "jwt..."}

Result: {access_token, refresh_token, expires_in}
```

---

## Why JWT is NOT for MCP

```
MCP Client Lifecycle:
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Load Config    │────▶│  Connect Once   │────▶│  Session Active │
│  (static)       │     │  (PAT/CAT)      │     │  (hours/days)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘

JWT Lifecycle:
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Login          │────▶│  Access Token   │────▶│  Expired        │
│  (interactive)  │     │  (30 minutes)   │     │  (need refresh) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Problem**:
- MCP clients load configuration once at startup
- JWT expires in 30 minutes
- No mechanism to auto-refresh in static MCP config
- User would need to manually update config every 30 minutes

**Solution**: Use PAT for MCP clients
- Long-lived (days/months)
- No refresh needed
- Can be revoked if compromised

---

## Token Security

### Storage

| Token Type | Where Stored | Security Notes |
|------------|--------------|----------------|
| JWT | Client-side (memory/localStorage) | Short-lived, auto-expires |
| PAT | DB (hashed) | Only hash stored, cannot recover |
| CAT | DB (hashed) | Only hash stored, cannot recover |

### Token Hashing

PAT and CAT tokens are hashed before storage:

```python
import hashlib

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

# Only the hash is stored in database
# Original token shown only once during creation
```

### Best Practices

1. **Never commit tokens to version control**
2. **Use environment variables for tokens**
3. **Rotate tokens periodically**
4. **Use minimal permissions (read vs read_write)**
5. **Set expiry dates on tokens**
6. **Revoke tokens immediately if compromised**

---

## Error Handling

### Common Auth Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `"Missing or invalid Authorization header"` | No auth provided | Add `Authorization: Bearer <token>` |
| `"Invalid or expired JWT token"` | JWT expired or invalid | Refresh token or re-login |
| `"Invalid PAT token"` | PAT invalid or revoked | Create new PAT via REST API |
| `"Invalid CAT"` | CAT invalid or revoked | Create new CAT |
| `"JWT tokens not accepted for MCP"` | Using JWT for MCP API | Create PAT via REST API first |
| `"Insufficient permissions"` | Missing required scope | Use token with appropriate permissions |

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Invalid or expired token",
    "details": {
      "token_type": "PAT",
      "reason": "revoked"
    }
  }
}
```

---

## Quick Reference

### When to Use Which Token

| Scenario | Token | API |
|----------|-------|-----|
| User registration | None (public) | REST |
| User login | None (public) | REST |
| Create PAT | JWT | REST |
| Create CAT | JWT or PAT | REST or MCP |
| MCP client operations | PAT | MCP |
| Share collection access | CAT | MCP (recipient) |
| Admin user management | JWT (ADMIN) | REST |
| CLI tools (interactive) | JWT | REST |
| CLI tools (automation) | PAT | REST or MCP |

### HTTP Header Format

```
Authorization: Bearer <token>
```

Example:
```
Authorization: Bearer pat_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```