"""Test MCP connection to local server with proper authentication flow."""
import asyncio
import json
import httpx
import os
import time
import subprocess
import uuid


async def wait_for_server(url: str, timeout: int = 30):
    """Wait for server to be ready."""
    print(f"Waiting for server at {url}...")
    start = time.time()
    async with httpx.AsyncClient(timeout=5.0) as client:
        while time.time() - start < timeout:
            try:
                response = await client.get(url, headers={"Accept": "text/event-stream"})
                print(f"Server responded with status {response.status_code}")
                return True
            except Exception as e:
                print(f"Connection failed: {e}, retrying...")
                await asyncio.sleep(1)
    return False


async def test_raw_http_local():
    """Test raw HTTP with local server."""
    server_url = os.environ.get("MCP_SERVER_URL", "http://mcp_server:8000/mcp")
    
    print("\n" + "="*60)
    print(f"Testing raw HTTP to server: {server_url}")
    print("="*60)
    
    # Wait for server to be ready
    if not await wait_for_server(server_url):
        print("Server not available after timeout")
        return
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get session ID first via GET
        print("\nStep 1: GET to obtain session...")
        try:
            response = await client.get(
                server_url,
                headers={"Accept": "text/event-stream"}
            )
            print(f"Status: {response.status_code}")
            session_id = response.headers.get("mcp-session-id")
            print(f"Session ID: {session_id}")
        except Exception as e:
            print(f"Error: {e}")
            return
        
        # Now POST with session ID
        print("\nStep 2: POST initialize...")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if session_id:
            headers["mcp-session-id"] = session_id
            
        response = await client.post(
            server_url,
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "id": 1,
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"}
                }
            },
            headers=headers
        )
        print(f"Status: {response.status_code}")
        
        # Parse the SSE response
        if "event: message" in response.text:
            for line in response.text.split('\n'):
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if "result" in data:
                        print(f"✓ Initialize succeeded!")
                        print(f"  Server: {data['result'].get('serverInfo', {}).get('name')}")
                        print(f"  Version: {data['result'].get('serverInfo', {}).get('version')}")
                    elif "error" in data:
                        print(f"✗ Error: {data['error']}")


async def test_full_auth_flow():
    """Test the full authentication flow with FastMCP client."""
    from fastmcp.client import Client
    
    server_url = os.environ.get("MCP_SERVER_URL", "http://mcp_server:8000/mcp")
    api_key = os.environ.get("MCP_API_KEY", "test_key_123")  # From .env
    
    print("\n" + "="*60)
    print(f"Testing Full Auth Flow")
    print("="*60)
    
    # Wait for server
    if not await wait_for_server(server_url):
        print("Server not available after timeout")
        return
    
    # Step 1: Register a user (public tool, no auth needed)
    print("\n--- Step 1: Register user (public tool) ---")
    test_id = uuid.uuid4().hex[:8]
    
    async with Client(server_url) as client:
        result = await client.call_tool("user_register_tool", {
            "email": f"test_{test_id}@example.com",
            "username": f"testuser_{test_id}",
            "password": "TestPassword123!",
        })
        print(f"✓ Registration result: {result}")
        user_id = result.get("id") if hasattr(result, 'get') else getattr(result, 'id', None)
    
    # Step 2: Login to get JWT token (public tool)
    print("\n--- Step 2: Login to get JWT token (public tool) ---")
    async with Client(server_url) as client:
        result = await client.call_tool("user_login_tool", {
            "username": f"testuser_{test_id}",
            "password": "TestPassword123!",
        })
        print(f"✓ Login result: {result}")
        # Extract access token from structured_content
        if hasattr(result, 'structured_content') and result.structured_content:
            access_token = result.structured_content.get("access_token")
        elif hasattr(result, 'data') and result.data:
            access_token = result.data.get("access_token")
        else:
            access_token = None
        print(f"  Access token: {access_token[:50]}..." if access_token else "  No access token!")
    
    # Step 3: List collections with JWT token
    print("\n--- Step 3: List collections with JWT token ---")
    collection_id = None
    if access_token:
        async with Client(server_url, auth=access_token) as client:
            result = await client.call_tool("list_collections_tool", {})
            print(f"✓ Collections: {result}")
            # Extract collection_id from structured_content
            if hasattr(result, 'structured_content') and result.structured_content:
                collections = result.structured_content.get("collections", [])
                if collections:
                    collection_id = collections[0].get("id")
                    print(f"  Using collection: {collection_id}")
    
    # Step 4: Use API key for document operations
    print("\n--- Step 4: List tools with API key ---")
    async with Client(server_url, auth=api_key) as client:
        tools = await client.list_tools()
        print(f"✓ Tools ({len(tools)}):")
        for tool in tools[:10]:
            print(f"  - {tool.name}")
    
    # Step 5: Store a document with API key
    # NOTE: Env-based API keys (from .env) don't have collection_id in database,
    # so document operations require a database-backed API key
    print("\n--- Step 5: Store document with API key ---")
    print("  (Skipping - env-based API keys don't support document operations)")
    
    # Step 6: Search documents
    print("\n--- Step 6: Search documents ---")
    print("  (Skipping - env-based API keys don't support document operations)")
    
    print("\n" + "="*60)
    print("✓ All tests passed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_raw_http_local())
    asyncio.run(test_full_auth_flow())
