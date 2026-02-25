"""
E2E tests for PAT-authenticated user capabilities.
Tests that PAT tokens have the same capabilities as JWT tokens.
Note: Document operations with PAT are tested in test_pat_tokens.py.
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


class TestPATProfile:
    """Test PAT user profile operations."""

    @pytest.mark.asyncio
    async def test_pat_can_get_profile(self):
        """PAT user can get their own profile."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            pat_token = None

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                pat_result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": "Profile Test PAT",
                })
                pat_token = pat_result["token"]

            async with MCPClient(SERVER_URL, auth_token=pat_token, transport=TRANSPORT) as pat_client:
                profile = await pat_client.call_tool("user_profile_tool", {})

                assert profile.get("id") is not None
                assert profile.get("username") == reg_result["username"]


class TestPATCollectionOperations:
    """Test PAT user collection operations."""

    @pytest.mark.asyncio
    async def test_pat_can_list_collections(self):
        """PAT user can list their collections."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            pat_token = None

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                pat_result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": "Collection Test PAT",
                })
                pat_token = pat_result["token"]

            async with MCPClient(SERVER_URL, auth_token=pat_token, transport=TRANSPORT) as pat_client:
                result = await pat_client.call_tool("list_collections_tool", {})

                collections = result.get("collections", [])
                assert len(collections) >= 1

    @pytest.mark.asyncio
    async def test_pat_can_create_collection(self):
        """PAT user can create a new collection."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            pat_token = None

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                pat_result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": "Create Collection PAT",
                })
                pat_token = pat_result["token"]

            async with MCPClient(SERVER_URL, auth_token=pat_token, transport=TRANSPORT) as pat_client:
                result = await pat_client.call_tool("create_collection_tool", {
                    "name": f"PAT Collection {test_id}",
                })

                assert result.get("id") is not None


class TestPATAPIKeyManagement:
    """Test PAT user API key management - Note: Some operations may require JWT."""

    @pytest.mark.skip(reason="PAT API key management requires JWT authentication")
    async def test_pat_can_create_api_key(self):
        pass

    @pytest.mark.skip(reason="PAT API key management requires JWT authentication")
    async def test_pat_can_list_api_keys(self):
        pass


class TestPATPATManagement:
    """Test PAT user can manage other PAT tokens."""

    @pytest.mark.skip(reason="PAT creation requires JWT authentication")
    async def test_pat_can_create_another_pat(self):
        pass

    @pytest.mark.asyncio
    async def test_pat_can_list_pat_tokens(self):
        """PAT user can list their PAT tokens."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            pat_token = None

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                pat_result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": "List PAT Token",
                })
                pat_token = pat_result["token"]

            async with MCPClient(SERVER_URL, auth_token=pat_token, transport=TRANSPORT) as pat_client:
                result = await pat_client.call_tool("list_pat_tokens_tool", {})

                tokens = result.get("tokens", [])
                assert len(tokens) >= 1


class TestPATToolListing:
    """Test PAT user tool listing."""

    @pytest.mark.asyncio
    async def test_pat_sees_user_tools(self):
        """PAT user sees all user-level tools but not admin tools."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            pat_token = None

            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                pat_result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": "Tool List PAT",
                })
                pat_token = pat_result["token"]

            async with MCPClient(SERVER_URL, auth_token=pat_token, transport=TRANSPORT) as pat_client:
                tools = await pat_client.list_tools()
                tool_names = {t["name"] for t in tools}

                assert "user_profile_tool" in tool_names
                assert "create_collection_tool" in tool_names
                assert "store_document_tool" in tool_names

                admin_tools = {
                    "list_users_tool",
                    "search_users_tool",
                    "get_user_tool",
                    "update_user_tool",
                    "delete_user_tool",
                }
                assert admin_tools.isdisjoint(tool_names)
