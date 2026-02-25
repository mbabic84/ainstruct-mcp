"""
E2E tests for JWT-authenticated user capabilities.
Tests what JWT users CAN do: profile, collections, API keys, PAT tokens.
Note: Document operations with JWT are tested in test_pat_tokens.py (same mechanism).
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


class TestJWTUserProfile:
    """Test JWT user profile operations."""

    @pytest.mark.asyncio
    async def test_jwt_can_get_profile(self):
        """JWT user can get their own profile."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                profile = await auth_client.call_tool("user_profile_tool", {})

                assert profile.get("id") is not None
                assert profile.get("username") == reg_result["username"]
                assert profile.get("email") == reg_result["email"]
                assert profile.get("is_active") is True


class TestJWTCollectionOperations:
    """Test JWT user collection operations."""

    @pytest.mark.asyncio
    async def test_jwt_can_list_collections(self):
        """JWT user can list their collections."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                result = await auth_client.call_tool("list_collections_tool", {})

                collections = result.get("collections", [])
                assert len(collections) >= 1

                default_coll = next(
                    (c for c in collections if c.get("name") == "default"),
                    None
                )
                assert default_coll is not None

    @pytest.mark.asyncio
    async def test_jwt_can_create_collection(self):
        """JWT user can create a new collection."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                result = await auth_client.call_tool("create_collection_tool", {
                    "name": f"Test Collection {test_id}",
                })

                assert result.get("id") is not None
                assert result.get("name") == f"Test Collection {test_id}"

    @pytest.mark.asyncio
    async def test_jwt_can_get_collection(self):
        """JWT user can get collection details."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                collections_result = await auth_client.call_tool("list_collections_tool", {})
                collection_id = collections_result["collections"][0]["id"]

                result = await auth_client.call_tool("get_collection_tool", {
                    "collection_id": collection_id,
                })

                assert result.get("id") == collection_id
                assert result.get("name") is not None

    @pytest.mark.asyncio
    async def test_jwt_can_rename_collection(self):
        """JWT user can rename a collection."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                create_result = await auth_client.call_tool("create_collection_tool", {
                    "name": f"Original {test_id}",
                })
                collection_id = create_result["id"]

                rename_result = await auth_client.call_tool("rename_collection_tool", {
                    "collection_id": collection_id,
                    "name": f"Renamed {test_id}",
                })

                assert rename_result.get("name") == f"Renamed {test_id}"

    @pytest.mark.asyncio
    async def test_jwt_can_delete_collection(self):
        """JWT user can delete a collection."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                create_result = await auth_client.call_tool("create_collection_tool", {
                    "name": f"To Delete {test_id}",
                })
                collection_id = create_result["id"]

                delete_result = await auth_client.call_tool("delete_collection_tool", {
                    "collection_id": collection_id,
                })

                assert delete_result.get("success") is True


class TestJWTAPIKeyManagement:
    """Test JWT user API key management."""

    @pytest.mark.asyncio
    async def test_jwt_can_create_api_key(self):
        """JWT user can create API keys for their collections."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                collections_result = await auth_client.call_tool("list_collections_tool", {})
                collection_id = collections_result["collections"][0]["id"]

                result = await auth_client.call_tool("create_collection_access_token_tool", {
                    "label": f"Test Key {test_id}",
                    "collection_id": collection_id,
                    "permission": "read_write",
                })

                assert result.get("key") is not None
                assert result["key"].startswith("ak_live_")

    @pytest.mark.asyncio
    async def test_jwt_can_list_api_keys(self):
        """JWT user can list their API keys."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                collections_result = await auth_client.call_tool("list_collections_tool", {})
                collection_id = collections_result["collections"][0]["id"]

                await auth_client.call_tool("create_collection_access_token_tool", {
                    "label": "List Test Key",
                    "collection_id": collection_id,
                    "permission": "read_write",
                })

                result = await auth_client.call_tool("list_collection_access_tokens_tool", {})

                keys = result.get("keys", [])
                assert len(keys) >= 1

                test_key = next((k for k in keys if k.get("label") == "List Test Key"), None)
                assert test_key is not None

    @pytest.mark.asyncio
    async def test_jwt_can_revoke_api_key(self):
        """JWT user can revoke their API keys."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                collections_result = await auth_client.call_tool("list_collections_tool", {})
                collection_id = collections_result["collections"][0]["id"]

                create_result = await auth_client.call_tool("create_collection_access_token_tool", {
                    "label": "Revoke Test Key",
                    "collection_id": collection_id,
                    "permission": "read_write",
                })
                key_id = create_result["id"]

                revoke_result = await auth_client.call_tool("revoke_collection_access_token_tool", {
                    "key_id": key_id,
                })

                assert revoke_result.get("success") is True

    @pytest.mark.asyncio
    async def test_jwt_can_rotate_api_key(self):
        """JWT user can rotate their API keys."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                collections_result = await auth_client.call_tool("list_collections_tool", {})
                collection_id = collections_result["collections"][0]["id"]

                create_result = await auth_client.call_tool("create_collection_access_token_tool", {
                    "label": "Rotate Test Key",
                    "collection_id": collection_id,
                    "permission": "read_write",
                })
                key_id = create_result["id"]
                old_key = create_result["key"]

                rotate_result = await auth_client.call_tool("rotate_collection_access_token_tool", {
                    "key_id": key_id,
                })

                assert rotate_result.get("key") is not None
                assert rotate_result["key"] != old_key


class TestJWTPATManagement:
    """Test JWT user PAT token management."""

    @pytest.mark.asyncio
    async def test_jwt_can_create_pat_token(self):
        """JWT user can create PAT tokens."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": f"Test PAT {test_id}",
                })

                assert result.get("token") is not None
                assert result["token"].startswith("pat_live_")

    @pytest.mark.asyncio
    async def test_jwt_can_list_pat_tokens(self):
        """JWT user can list their PAT tokens."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                await auth_client.call_tool("create_pat_token_tool", {
                    "label": "List Test PAT",
                })

                result = await auth_client.call_tool("list_pat_tokens_tool", {})

                tokens = result.get("tokens", [])
                assert len(tokens) >= 1

                test_token = next((t for t in tokens if t.get("label") == "List Test PAT"), None)
                assert test_token is not None

    @pytest.mark.asyncio
    async def test_jwt_can_revoke_pat_token(self):
        """JWT user can revoke their PAT tokens."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                create_result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": "Revoke Test PAT",
                })
                pat_id = create_result["id"]

                revoke_result = await auth_client.call_tool("revoke_pat_token_tool", {
                    "pat_id": pat_id,
                })

                assert revoke_result.get("success") is True

    @pytest.mark.asyncio
    async def test_jwt_can_rotate_pat_token(self):
        """JWT user can rotate their PAT tokens."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                create_result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": "Rotate Test PAT",
                })
                pat_id = create_result["id"]
                old_token = create_result["token"]

                rotate_result = await auth_client.call_tool("rotate_pat_token_tool", {
                    "pat_id": pat_id,
                })

                assert rotate_result.get("token") is not None
                assert rotate_result["token"] != old_token


class TestJWTToolListing:
    """Test JWT user tool listing."""

    @pytest.mark.asyncio
    async def test_jwt_sees_user_tools(self):
        """JWT user sees all user-level tools but not admin tools."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                tools = await auth_client.list_tools()
                tool_names = {t["name"] for t in tools}

                assert "user_profile_tool" in tool_names
                assert "create_collection_tool" in tool_names
                assert "store_document_tool" in tool_names
                assert "create_collection_access_token_tool" in tool_names
                assert "create_pat_token_tool" in tool_names

                admin_tools = {
                    "list_users_tool",
                    "search_users_tool",
                    "get_user_tool",
                    "update_user_tool",
                    "delete_user_tool",
                }
                assert admin_tools.isdisjoint(tool_names)
