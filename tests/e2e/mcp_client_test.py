"""
MCP Client test utilities for testing the ainstruct-mcp server.
Provides helper functions for connecting to and testing MCP servers.
Supports both SSE and Streamable HTTP transports.
"""
import json
import uuid
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession

# Import both transport types
try:
    from mcp.client.sse import sse_client
    from mcp.client.streamable_http import streamablehttp_client
except ImportError:
    # Fallback for older MCP versions
    from mcp.client.sse import sse_client
    streamablehttp_client = None


@asynccontextmanager
async def mcp_client_session_http(server_url: str, auth_token: str | None = None):
    """Context manager for MCP client connections using Streamable HTTP transport."""
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    if streamablehttp_client is None:
        raise ImportError("streamablehttp_client not available - upgrade mcp package")

    async with streamablehttp_client(url=server_url.rstrip("/"), headers=headers) as (read_stream, write_stream, session_info):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


@asynccontextmanager
async def mcp_client_session_sse(server_url: str, auth_token: str | None = None):
    """Context manager for MCP client connections using SSE transport."""
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    async with sse_client(url=f"{server_url.rstrip('/')}/sse", headers=headers) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


class MCPClient:
    """MCP client for testing ainstruct-mcp server."""

    def __init__(self, server_url: str, auth_token: str | None = None, transport: str = "http"):
        """
        Initialize MCP client.
        
        Args:
            server_url: MCP server URL
            auth_token: Optional Bearer token for authentication
            transport: Transport type - "http" (streamable HTTP) or "sse" (legacy SSE)
        """
        self.server_url = server_url.rstrip("/")
        self.auth_token = auth_token
        self.transport = transport
        self._cm = None
        self.session: ClientSession | None = None

    async def connect(self) -> None:
        """Connect to the MCP server."""
        if self.transport == "http":
            self._cm = mcp_client_session_http(self.server_url, self.auth_token)
        else:
            self._cm = mcp_client_session_sse(self.server_url, self.auth_token)
        self.session = await self._cm.__aenter__()

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._cm:
            await self._cm.__aexit__(None, None, None)
            self._cm = None
            self.session = None

    async def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools."""
        if not self.session:
            raise RuntimeError("Not connected to server")
        result = await self.session.list_tools()
        return [{"name": t.name, "description": t.description, "inputSchema": t.inputSchema} for t in result.tools]

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Call a tool on the server.
        
        Raises:
            RuntimeError: If tool call returns an error (isError=True)
        """
        if not self.session:
            raise RuntimeError("Not connected to server")
        result = await self.session.call_tool(name, arguments or {})

        if hasattr(result, "isError") and result.isError:
            error_msg = "Unknown error"
            if hasattr(result, "content"):
                for content in result.content:
                    if hasattr(content, "text"):
                        error_msg = content.text
                        break
            raise RuntimeError(f"Tool error: {error_msg}")

        if hasattr(result, "content"):
            for content in result.content:
                if hasattr(content, "text"):
                    try:
                        return json.loads(content.text)
                    except json.JSONDecodeError:
                        return content.text
        return result

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()


@asynccontextmanager
async def mcp_client(server_url: str, auth_token: str | None = None, transport: str = "http"):
    """Context manager for MCP client connections."""
    client = MCPClient(server_url, auth_token, transport)
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()


async def register_test_user(client: MCPClient, test_id: str) -> dict:
    """Register a test user and return user info."""
    email = f"test_{test_id}@example.com"
    username = f"testuser_{test_id}"
    password = "TestPassword123!"

    result = await client.call_tool("user_register_tool", {
        "email": email,
        "username": username,
        "password": password,
    })

    return {
        "user": result,
        "email": email,
        "username": username,
        "password": password,
    }


async def login_user(client: MCPClient, username: str, password: str) -> dict:
    """Login and return tokens."""
    result = await client.call_tool("user_login_tool", {
        "username": username,
        "password": password,
    })
    return result


async def create_api_key(client: MCPClient, collection_id: str, label: str = "Test Key") -> str:
    """Create a Collection Access Token for a collection."""
    result = await client.call_tool("create_collection_access_token_tool", {
        "label": label,
        "collection_id": collection_id,
        "permission": "read_write",
    })
    return result.get("key")


def generate_test_id() -> str:
    """Generate a unique test ID."""
    return uuid.uuid4().hex[:8]
