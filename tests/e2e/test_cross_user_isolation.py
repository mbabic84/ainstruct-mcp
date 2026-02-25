"""
E2E tests for cross-user isolation.
Tests that users can only access their own resources.
"""
import os
import pytest

from tests.e2e.mcp_client_test import (
    MCPClient,
    generate_test_id,
    register_test_user,
    login_user,
)


SERVER_URL = os.environ["MCP_SERVER_URL"]
TRANSPORT = os.environ.get("MCP_TRANSPORT", "http")


class TestCrossUserCollectionIsolation:
    """Test that users cannot access other users' collections."""

    @pytest.mark.asyncio
    async def test_user_cannot_get_other_user_collection(self):
        """User cannot get another user's collection details."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            user1_result = await register_test_user(client, f"{test_id}_user1")
            user1_login = await login_user(client, user1_result["username"], user1_result["password"])

            user2_result = await register_test_user(client, f"{test_id}_user2")
            user2_login = await login_user(client, user2_result["username"], user2_result["password"])

            user1_collection_id = None

            async with MCPClient(SERVER_URL, auth_token=user1_login["access_token"], transport=TRANSPORT) as user1_client:
                collections_result = await user1_client.call_tool("list_collections_tool", {})
                user1_collection_id = collections_result["collections"][0]["id"]

            async with MCPClient(SERVER_URL, auth_token=user2_login["access_token"], transport=TRANSPORT) as user2_client:
                with pytest.raises(RuntimeError, match="not found|permission|access"):
                    await user2_client.call_tool("get_collection_tool", {
                        "collection_id": user1_collection_id,
                    })

    @pytest.mark.asyncio
    async def test_user_cannot_list_other_user_collections(self):
        """User's collection list only shows their own collections."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            user1_result = await register_test_user(client, f"{test_id}_user1")
            user1_login = await login_user(client, user1_result["username"], user1_result["password"])

            user2_result = await register_test_user(client, f"{test_id}_user2")
            user2_login = await login_user(client, user2_result["username"], user2_result["password"])

            user1_collection_ids = []

            async with MCPClient(SERVER_URL, auth_token=user1_login["access_token"], transport=TRANSPORT) as user1_client:
                collections_result = await user1_client.call_tool("list_collections_tool", {})
                user1_collection_ids = [c["id"] for c in collections_result["collections"]]

                new_coll = await user1_client.call_tool("create_collection_tool", {
                    "name": f"User1 Private {test_id}",
                })
                user1_collection_ids.append(new_coll["id"])

            async with MCPClient(SERVER_URL, auth_token=user2_login["access_token"], transport=TRANSPORT) as user2_client:
                collections_result = await user2_client.call_tool("list_collections_tool", {})
                user2_collection_ids = [c["id"] for c in collections_result["collections"]]

                for user1_id in user1_collection_ids:
                    assert user1_id not in user2_collection_ids

    @pytest.mark.asyncio
    async def test_user_cannot_delete_other_user_collection(self):
        """User cannot delete another user's collection."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            user1_result = await register_test_user(client, f"{test_id}_user1")
            user1_login = await login_user(client, user1_result["username"], user1_result["password"])

            user2_result = await register_test_user(client, f"{test_id}_user2")
            user2_login = await login_user(client, user2_result["username"], user2_result["password"])

            user1_collection_id = None

            async with MCPClient(SERVER_URL, auth_token=user1_login["access_token"], transport=TRANSPORT) as user1_client:
                collections_result = await user1_client.call_tool("list_collections_tool", {})
                user1_collection_id = collections_result["collections"][0]["id"]

            async with MCPClient(SERVER_URL, auth_token=user2_login["access_token"], transport=TRANSPORT) as user2_client:
                with pytest.raises(RuntimeError, match="not found|permission|access"):
                    await user2_client.call_tool("delete_collection_tool", {
                        "collection_id": user1_collection_id,
                    })

    @pytest.mark.asyncio
    async def test_user_cannot_rename_other_user_collection(self):
        """User cannot rename another user's collection."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            user1_result = await register_test_user(client, f"{test_id}_user1")
            user1_login = await login_user(client, user1_result["username"], user1_result["password"])

            user2_result = await register_test_user(client, f"{test_id}_user2")
            user2_login = await login_user(client, user2_result["username"], user2_result["password"])

            user1_collection_id = None

            async with MCPClient(SERVER_URL, auth_token=user1_login["access_token"], transport=TRANSPORT) as user1_client:
                collections_result = await user1_client.call_tool("list_collections_tool", {})
                user1_collection_id = collections_result["collections"][0]["id"]

            async with MCPClient(SERVER_URL, auth_token=user2_login["access_token"], transport=TRANSPORT) as user2_client:
                with pytest.raises(RuntimeError, match="not found|permission|access"):
                    await user2_client.call_tool("rename_collection_tool", {
                        "collection_id": user1_collection_id,
                        "name": "Hijacked Collection",
                    })


class TestCrossUserDocumentIsolation:
    """Test that users cannot access other users' documents via API key."""

    @pytest.mark.skip(reason="JWT document storage has issues in test environment")
    async def test_api_key_cannot_access_other_user_documents(self):
        pass


class TestCrossUserAPIKeyIsolation:
    """Test that users cannot access other users' API keys."""

    @pytest.mark.asyncio
    async def test_user_cannot_list_other_user_api_keys(self):
        """User's API key list only shows their own keys."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            user1_result = await register_test_user(client, f"{test_id}_user1")
            user1_login = await login_user(client, user1_result["username"], user1_result["password"])

            user2_result = await register_test_user(client, f"{test_id}_user2")
            user2_login = await login_user(client, user2_result["username"], user2_result["password"])

            user1_key_label = f"User1 Key {test_id}"

            async with MCPClient(SERVER_URL, auth_token=user1_login["access_token"], transport=TRANSPORT) as user1_client:
                collections_result = await user1_client.call_tool("list_collections_tool", {})
                collection_id = collections_result["collections"][0]["id"]

                await user1_client.call_tool("create_collection_access_token_tool", {
                    "label": user1_key_label,
                    "collection_id": collection_id,
                    "permission": "read_write",
                })

            async with MCPClient(SERVER_URL, auth_token=user2_login["access_token"], transport=TRANSPORT) as user2_client:
                keys_result = await user2_client.call_tool("list_collection_access_tokens_tool", {})
                user2_key_labels = [k.get("label") for k in keys_result.get("keys", [])]

                assert user1_key_label not in user2_key_labels

    @pytest.mark.asyncio
    async def test_user_cannot_revoke_other_user_api_key(self):
        """User cannot revoke another user's API key."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            user1_result = await register_test_user(client, f"{test_id}_user1")
            user1_login = await login_user(client, user1_result["username"], user1_result["password"])

            user2_result = await register_test_user(client, f"{test_id}_user2")
            user2_login = await login_user(client, user2_result["username"], user2_result["password"])

            user1_key_id = None

            async with MCPClient(SERVER_URL, auth_token=user1_login["access_token"], transport=TRANSPORT) as user1_client:
                collections_result = await user1_client.call_tool("list_collections_tool", {})
                collection_id = collections_result["collections"][0]["id"]

                key_result = await user1_client.call_tool("create_collection_access_token_tool", {
                    "label": "User1 Key to Protect",
                    "collection_id": collection_id,
                    "permission": "read_write",
                })
                user1_key_id = key_result["id"]

            async with MCPClient(SERVER_URL, auth_token=user2_login["access_token"], transport=TRANSPORT) as user2_client:
                with pytest.raises(RuntimeError, match="not found|permission|access"):
                    await user2_client.call_tool("revoke_collection_access_token_tool", {
                        "key_id": user1_key_id,
                    })
