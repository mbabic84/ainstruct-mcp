"""
E2E tests for permission enforcement across tools.
"""
import os

import pytest

from tests.e2e.mcp_client_test import (
    MCPClient,
    generate_test_id,
    login_user,
    register_test_user,
)

SERVER_URL = os.environ["MCP_SERVER_URL"]
TRANSPORT = os.environ.get("MCP_TRANSPORT", "http")


class TestReadonlyPermissions:
    """Test read-only API key permissions."""

    @pytest.mark.asyncio
    async def test_readonly_key_denies_write(self):
        """Verify read-only key cannot perform write operations."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
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

                key_result = await auth_client.call_tool("create_collection_access_token_tool", {
                    "label": "Readonly Key",
                    "collection_id": collection_id,
                    "permission": "read",
                })
                readonly_key = key_result["key"]

            async with MCPClient(SERVER_URL, auth_token=readonly_key) as ro_client:
                list_result = await ro_client.call_tool("list_documents_tool", {})
                print(f"\nRead-only key can list documents: {list_result.get('total', 0)} documents")

                with pytest.raises(RuntimeError, match="permission|Insufficient|write"):
                    await ro_client.call_tool("store_document_tool", {
                        "title": "Should Fail",
                        "content": "This should not work",
                    })
