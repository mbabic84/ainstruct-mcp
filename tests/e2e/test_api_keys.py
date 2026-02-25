"""
E2E tests for API key management tools.
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


class TestAPIKeys:
    """Test API key management."""
    
    @pytest.mark.asyncio
    async def test_create_and_list_api_keys(self):
        """Test creating and listing API keys."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Register and login
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )
            
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"]) as auth_client:
                # Get collections
                collections_result = await auth_client.call_tool("list_collections_tool", {})
                collection_id = collections_result["collections"][0]["id"]
                
                # Create API key
                key_result = await auth_client.call_tool("create_collection_access_token_tool", {
                    "label": "Test Key",
                    "collection_id": collection_id,
                    "permission": "read_write",
                })
                
                assert "key" in key_result
                assert key_result["key"].startswith("ak_live_")
                
                api_key = key_result["key"]
                print(f"\nCreated API key: {api_key[:30]}...")
                
                # List API keys
                keys_result = await auth_client.call_tool("list_collection_access_tokens_tool", {})
                
                keys = keys_result.get("keys", [])
                assert len(keys) >= 1
                
                # Find our key (key value is not returned in list)
                our_key = next(
                    (k for k in keys if k.get("label") == "Test Key"),
                    None
                )
                assert our_key is not None
                
                print(f"\nListed {len(keys)} API keys")
