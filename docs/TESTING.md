# Testing the AI Document Memory MCP Server

This guide explains how to test the MCP server using Docker Compose and a local client.

## Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)

## Quick Start

### 1. Clone and Configure

```bash
git clone <repository-url>
cd ainstruct-mcp

# Create .env file if it doesn't exist
cat > .env << EOF
API_KEYS=test_key_123
ADMIN_API_KEY=admin_secret_key
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
QDRANT_URL=http://qdrant:6333
DATABASE_URL=sqlite:///./data/mcp_server.db
EOF
```

### 2. Run Tests with Docker Compose

```bash
# Start all services and run tests
docker compose --profile test up --build

# Or run in detached mode and view logs
docker compose --profile test up -d --build
docker compose --profile test logs -f mcp_client_test
```

### 3. Stop Services

```bash
docker compose --profile test down
```

## Testing Methods

### Method 1: Docker Compose Test Container (Recommended)

The test container (`mcp_client_test`) runs automated tests against the server.

**Test files:**
- `tests/debug_connection.py` - Full authentication flow test
- `tests/mcp_live_test.py` - MCP protocol compliance test
- `tests/mcp_client_test.py` - Comprehensive test suite

**Run specific test:**

```bash
docker compose --profile test up -d mcp_server qdrant
docker compose --profile test run mcp_client_test python tests/debug_connection.py
```

### Method 2: Local Python Client

Run a test client locally against Docker services:

```bash
# Start server services only
docker compose up -d mcp_server qdrant

# Install client dependencies locally
pip install fastmcp>=3.0.0 httpx

# Run test script
export MCP_SERVER_URL=http://localhost:8000/mcp
export MCP_API_KEY=test_key_123
python tests/debug_connection.py
```

### Method 3: Interactive Python Session

```python
import asyncio
from fastmcp.client import Client

async def test():
    server_url = "http://localhost:8000/mcp"
    
    # Register a user (public tool - no auth needed)
    async with Client(server_url) as client:
        result = await client.call_tool("user_register_tool", {
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPassword123!",
        })
        print(f"Registered: {result.structured_content}")
    
    # Login to get JWT token
    async with Client(server_url) as client:
        result = await client.call_tool("user_login_tool", {
            "username": "testuser",
            "password": "TestPassword123!",
        })
        token = result.structured_content["access_token"]
        print(f"Token: {token[:50]}...")
    
    # Use authenticated endpoints
    async with Client(server_url, auth=token) as client:
        result = await client.call_tool("list_collections_tool", {})
        print(f"Collections: {result.structured_content}")

asyncio.run(test())
```

### Method 4: Raw HTTP Requests

Test the MCP protocol directly with HTTP requests:

```bash
# Get session ID
SESSION_ID=$(curl -s -I http://localhost:8000/mcp | grep -i mcp-session-id | cut -d' ' -f2 | tr -d '\r')

# Initialize
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "id": 1,
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test", "version": "1.0"}
    }
  }'

# List tools (requires auth)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "mcp-session-id: $SESSION_ID" \
  -H "Authorization: Bearer test_key_123" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 2
  }'
```

## Test Scenarios

### Scenario 1: Public Tool Access

Public tools can be called without authentication:

```python
async with Client(server_url) as client:
    # No auth needed for these tools:
    await client.call_tool("user_register_tool", {...})
    await client.call_tool("user_login_tool", {...})
    await client.call_tool("promote_to_admin_tool", {...})
```

### Scenario 2: JWT Authentication

User authentication flow:

```python
# 1. Register
async with Client(server_url) as client:
    await client.call_tool("user_register_tool", {
        "email": "user@example.com",
        "username": "user",
        "password": "password123",
    })

# 2. Login
async with Client(server_url) as client:
    result = await client.call_tool("user_login_tool", {
        "username": "user",
        "password": "password123",
    })
    token = result.structured_content["access_token"]

# 3. Use authenticated endpoints
async with Client(server_url, auth=token) as client:
    await client.call_tool("list_collections_tool", {})
    await client.call_tool("user_profile_tool", {})
```

### Scenario 3: API Key Authentication

API keys for service-to-service communication:

```python
# Use API key from environment
async with Client(server_url, auth="test_key_123") as client:
    tools = await client.list_tools()
    print(f"Available tools: {len(tools)}")
```

### Scenario 4: Document Operations

Document operations require a database-backed API key:

```python
# 1. Create an API key after logging in
async with Client(server_url, auth=jwt_token) as client:
    result = await client.call_tool("create_api_key_tool", {
        "label": "my-api-key",
        "permission": "read_write",
    })
    api_key = result.structured_content["key"]

# 2. Use the API key for document operations
async with Client(server_url, auth=api_key) as client:
    result = await client.call_tool("store_document_tool", {
        "title": "My Document",
        "content": "# Hello\n\nThis is a test document.",
        "document_type": "markdown",
    })
    print(f"Stored: {result.structured_content}")
```

## Troubleshooting

### Server Won't Start

```bash
# Check logs
docker compose logs mcp_server

# Common issues:
# - Port 8000 already in use: Change port in docker-compose.yml
# - Qdrant not ready: Wait a few seconds and retry
# - Missing .env: Create .env file with required variables
```

### Authentication Errors

```
Missing or invalid Authorization header
```

- Ensure you're passing `auth=token` to the Client
- For API keys, pass the key directly: `auth="test_key_123"`
- For JWT tokens, pass the access token: `auth=access_token`

### bcrypt Errors

```
bcrypt: no backends available
```

- Ensure bcrypt is installed: `pip install "bcrypt>=4.0.0,<5.0.0"`
- bcrypt 5.x is incompatible with passlib

### Connection Refused

```
Connection refused / All connection attempts failed
```

- Ensure server is running: `docker compose ps`
- Check server health: `curl http://localhost:8000/mcp`
- Verify network connectivity between containers

## Test Files Reference

| File | Purpose |
|------|---------|
| `tests/debug_connection.py` | Full auth flow test with detailed output |
| `tests/mcp_live_test.py` | MCP protocol compliance tests |
| `tests/mcp_client_test.py` | Comprehensive pytest test suite |
| `tests/test_integration.py` | Unit tests with mocks |
| `tests/test_auth.py` | Authentication unit tests |

## CI/CD Integration

For automated testing in CI pipelines:

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run tests
        run: docker compose --profile test up --build --abort-on-container-exit
      
      - name: Show results
        run: docker compose logs mcp_client_test
```

## See Also

- [API Reference](./API_REFERENCE.md) - Full API documentation
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment
- [Architecture](./ARCHITECTURE.md) - System architecture overview
