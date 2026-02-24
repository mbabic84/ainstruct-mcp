"""
E2E tests for permission enforcement across tools.
"""
import os
import pytest

from tests.e2e.mcp_client_test import (
    MCPClient,
    generate_test_id,
    register_test_user,
    login_user,
)


# Production server URL
SERVER_URL = os.environ.get("MCP_SERVER_URL", "https://ainstruct.kralicinora.cz/mcp")
TRANSPORT = os.environ.get("MCP_TRANSPORT", "http")


class TestReadonlyPermissions:
    """Test read-only API key permissions."""
    
    @pytest.mark.asyncio
    async def test_readonly_key_denies_write(self):
        """Verify read-only key cannot perform write operations."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Setup
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )
            
            collection_id = None
            readonly_key = None
            
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"]) as auth_client:
                collections_result = await auth_client.call_tool("list_collections_tool", {})
                collection_id = collections_result["collections"][0]["id"]
                
                # Create read-only key
                key_result = await auth_client.call_tool("create_api_key_tool", {
                    "label": "Readonly Key",
                    "collection_id": collection_id,
                    "permission": "read",  # Read-only!
                })
                readonly_key = key_result["key"]
            
            # Test with read-only key
            async with MCPClient(SERVER_URL, auth_token=readonly_key) as ro_client:
                # Should be able to list documents
                list_result = await ro_client.call_tool("list_documents_tool", {})
                print(f"\nRead-only key can list documents: {list_result.get('total', 0)} documents")
                
                # Should NOT be able to store - error is returned as string response
                store_result = await ro_client.call_tool("store_document_tool", {
                    "title": "Should Fail",
                    "content": "This should not work",
                })
                
                # Error is returned as string, not raised as exception
                error_msg = str(store_result).lower()
                assert "permission" in error_msg or "insufficient" in error_msg, f"Expected permission error, got: {store_result}"
                print(f"\nRead-only key correctly denied write: {store_result}")
