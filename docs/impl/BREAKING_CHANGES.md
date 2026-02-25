# Breaking Changes & Migration Guide

This document describes breaking changes for existing users and provides migration instructions.

---

## Summary of Changes

| Change | Impact | Action Required |
|--------|--------|-----------------|
| API Key → CAT rename | Token prefix change | Regenerate tokens |
| Auth tools removed from MCP | Cannot register/login via MCP | Use REST API |
| PAT management removed from MCP | Cannot create PAT via MCP | Use REST API |
| JWT rejected for MCP | JWT tokens don't work for MCP | Use PAT instead |

---

## Change 1: API Key Renamed to CAT

### What Changed

| Before | After |
|--------|-------|
| "API Key" terminology | "CAT" (Collection Access Token) |
| `ak_live_xxx` prefix | `cat_live_xxx` prefix |
| `create_api_key_tool` | `create_cat_tool` |
| `list_api_keys_tool` | `list_cats_tool` |
| `revoke_api_key_tool` | `revoke_cat_tool` |
| `rotate_api_key_tool` | `rotate_cat_tool` |

### Impact

- **All existing `ak_live_` tokens are invalidated**
- You must create new `cat_live_` tokens
- No data is lost — documents and collections remain intact

### Migration Steps

1. **Update MCP configuration** with new CAT prefix awareness
2. **Create new CAT** via REST API or MCP tools:
   ```
   # Via MCP (with PAT)
   create_cat_tool({
     label: "My Client",
     collection_id: "your-collection-uuid",
     permission: "read_write"
   })
   ```
3. **Update any stored tokens** in your applications
4. **Delete old `ak_live_` tokens** (they won't work anyway)

---

## Change 2: Auth Tools Removed from MCP

### What Changed

The following tools are **no longer available via MCP API**:

| Removed MCP Tool | New REST Endpoint |
|------------------|-------------------|
| `user_register_tool` | `POST /auth/register` |
| `user_login_tool` | `POST /auth/login` |
| `user_refresh_tool` | `POST /auth/refresh` |

### Impact

- Cannot register new users via MCP
- Cannot login via MCP
- Cannot refresh JWT tokens via MCP

### Migration Steps

**For user registration:**

```bash
# Before (MCP)
user_register_tool({email, username, password})

# After (REST API)
curl -X POST https://ainstruct.example.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "alice", "password": "secret"}'
```

**For user login:**

```bash
# Before (MCP)
user_login_tool({username, password})

# After (REST API)
curl -X POST https://ainstruct.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret"}'
```

---

## Change 3: PAT Management Removed from MCP

### What Changed

The following PAT tools are **no longer available via MCP API**:

| Removed MCP Tool | New REST Endpoint |
|------------------|-------------------|
| `create_pat_token_tool` | `POST /auth/pat` |
| `list_pat_tokens_tool` | `GET /auth/pat` |
| `revoke_pat_token_tool` | `DELETE /auth/pat/:id` |
| `rotate_pat_token_tool` | `POST /auth/pat/:id/rotate` |

### Impact

- Cannot create PAT tokens via MCP
- Cannot list/revoke/rotate PAT tokens via MCP

### Migration Steps

**Create a PAT:**

```bash
# Login first to get JWT
TOKEN=$(curl -s -X POST https://ainstruct.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret"}' | jq -r '.access_token')

# Create PAT with JWT
curl -X POST https://ainstruct.example.com/api/v1/auth/pat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"label": "My MCP Client", "expires_in_days": 365}'
```

**List PATs:**

```bash
curl -X GET https://ainstruct.example.com/api/v1/auth/pat \
  -H "Authorization: Bearer $TOKEN"
```

**Revoke a PAT:**

```bash
curl -X DELETE https://ainstruct.example.com/api/v1/auth/pat/{pat_id} \
  -H "Authorization: Bearer $TOKEN"
```

---

## Change 4: JWT Rejected for MCP

### What Changed

- MCP API **no longer accepts JWT tokens**
- MCP API only accepts PAT or CAT tokens
- JWT tokens are strictly for REST API

### Impact

- Existing JWT-based MCP configurations will fail
- Error: `"JWT tokens not accepted for MCP. Use PAT instead."`

### Migration Steps

1. **Create a PAT** via REST API (see above)
2. **Update MCP configuration**:

```json
// Before (JWT - will not work)
{
  "mcp": {
    "ainstruct": {
      "headers": {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIs..."
      }
    }
  }
}

// After (PAT - correct)
{
  "mcp": {
    "ainstruct": {
      "headers": {
        "Authorization": "Bearer pat_live_xxx"
      }
    }
  }
}
```

---

## Complete Migration Checklist

### Step 1: Create PAT (Required for MCP Access)

```bash
# 1. Login to get JWT
curl -X POST https://ainstruct.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# 2. Create PAT with JWT from step 1
curl -X POST https://ainstruct.example.com/api/v1/auth/pat \
  -H "Authorization: Bearer <jwt_from_step_1>" \
  -H "Content-Type: application/json" \
  -d '{"label": "MCP Client", "expires_in_days": 365}'

# 3. Save the PAT token (shown only once)
```

### Step 2: Create New CATs

```bash
# With your PAT
curl -X POST https://ainstruct.example.com/api/v1/auth/cat \
  -H "Authorization: Bearer pat_live_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "My App",
    "collection_id": "your-collection-uuid",
    "permission": "read_write"
  }'
```

### Step 3: Update All Configurations

- [ ] Update MCP client configurations (Claude, Cursor, etc.)
- [ ] Update environment variables
- [ ] Update CI/CD secrets
- [ ] Update application code using old tokens
- [ ] Delete old `ak_live_` tokens from password managers

### Step 4: Verify

- [ ] MCP tools work with new PAT
- [ ] Document operations work with new CAT
- [ ] Old `ak_live_` tokens are rejected
- [ ] Old JWT tokens don't work for MCP

---

## Quick Reference: Old vs New

| Action | Before | After |
|--------|--------|-------|
| Register user | MCP: `user_register_tool` | REST: `POST /auth/register` |
| Login | MCP: `user_login_tool` | REST: `POST /auth/login` |
| Create PAT | MCP: `create_pat_token_tool` | REST: `POST /auth/pat` |
| Create CAT | MCP: `create_api_key_tool` | MCP: `create_cat_tool` (or REST) |
| MCP auth | JWT or PAT or CAT | PAT or CAT only |
| Token prefix | `ak_live_` | `cat_live_` |

---

## No Data Loss

Your data is safe:

- ✅ All documents remain intact
- ✅ All collections remain intact
- ✅ User accounts unchanged
- ✅ Only tokens need to be regenerated

---

## Support

If you encounter issues during migration:

1. Check that you're using the correct token type for each API
2. Verify token format (`pat_live_` or `cat_live_` prefix)
3. Ensure JWT is only used for REST API
4. Create new tokens via REST API if old ones fail

---

## Timeline

| Phase | Date | Action |
|-------|------|--------|
| Announcement | T-7 days | Notify users of upcoming changes |
| Deployment | T-0 | Deploy new architecture |
| Grace Period | T+7 days | Support for migration issues |
| Cleanup | T+30 days | Remove any temporary compatibility |

---

## FAQ

### Q: Will I lose my documents?

**A**: No. Only tokens are invalidated. All your documents and collections remain intact.

### Q: Can I keep using my old tokens temporarily?

**A**: No. The change is a clean break. Old `ak_live_` tokens will not work after deployment.

### Q: Do I need to recreate my collections?

**A**: No. Collections are preserved. You just need new CATs to access them.

### Q: Why was this change made?

**A**: To provide a cleaner architecture with proper separation between interactive auth (REST/JWT) and automated access (MCP/PAT/CAT).

### Q: What's the difference between PAT and CAT?

**A**: 
- **PAT**: User-level token, accesses all your collections
- **CAT**: Collection-level token, accesses one specific collection