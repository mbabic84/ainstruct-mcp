"""
E2E tests for tool listing and server health.
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


class TestMCPServerHealth:
    """Test basic server health and tool listing."""
    
    @pytest.mark.asyncio
    async def test_server_is_reachable(self):
        """Verify the MCP server is reachable and responds to initialize."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            assert client.session is not None
    
    @pytest.mark.asyncio
    async def test_list_tools_public(self):
        """List tools without authentication returns only public tools."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            tools = await client.list_tools()

            tool_names = {t["name"] for t in tools}

            # Without auth, only public tools should be visible
            public_tools = {
                "user_register_tool",
                "user_login_tool",
                "user_refresh_tool",
            }
            assert tool_names == public_tools, f"Expected only public tools, got: {tool_names}"

            print(f"\nFound {len(tools)} public tools (no auth)")

    @pytest.mark.asyncio
    async def test_list_tools_authenticated(self):
        """List tools with JWT authentication returns all non-admin tools."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Register and login to get JWT token
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            # List tools with JWT auth
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                tools = await auth_client.list_tools()
                tool_names = {t["name"] for t in tools}

                # With JWT, should see public + user + collections + keys/PATs + documents
                assert "user_register_tool" in tool_names
                assert "user_login_tool" in tool_names
                assert "user_profile_tool" in tool_names

                # Collection tools
                assert "create_collection_tool" in tool_names
                assert "list_collections_tool" in tool_names

                # Collection access token tools
                assert "create_collection_access_token_tool" in tool_names
                assert "list_collection_access_tokens_tool" in tool_names

                # Document tools
                assert "store_document_tool" in tool_names
                assert "search_documents_tool" in tool_names

                # Admin tools should NOT be visible to non-admin users
                admin_tools = {
                    "list_users_tool",
                    "get_user_tool",
                    "update_user_tool",
                    "delete_user_tool",
                }
                assert admin_tools.isdisjoint(tool_names), f"Non-admin user should not see admin tools: {tool_names & admin_tools}"

                print(f"\nFound {len(tools)} tools with JWT auth")

    @pytest.mark.asyncio
    async def test_list_tools_non_admin_cannot_see_admin_tools(self):
        """Non-admin users should NOT see admin tools."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Register and login to get JWT token
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            # List tools with JWT auth
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                tools = await auth_client.list_tools()
                tool_names = {t["name"] for t in tools}

                # Admin tools should NOT be visible
                admin_tools = {
                    "list_users_tool",
                    "get_user_tool",
                    "update_user_tool",
                    "delete_user_tool",
                }
                for admin_tool in admin_tools:
                    assert admin_tool not in tool_names, f"Non-admin user should not see {admin_tool}"

                print(f"\nNon-admin user has {len(tool_names)} tools, no admin tools visible")

    @pytest.mark.asyncio
    async def test_list_tools_api_key_only_sees_document_tools(self):
        """API key users should only see public + document tools."""
        # Use the pre-configured env API key from .env
        api_key = "test_key_123"

        # List tools with API key auth
        async with MCPClient(SERVER_URL, auth_token=api_key, transport=TRANSPORT) as key_client:
            tools = await key_client.list_tools()
            tool_names = {t["name"] for t in tools}

            # Should see public + document tools
            public_tools = {"user_register_tool", "user_login_tool", "user_refresh_tool"}
            document_tools = {
                "store_document_tool",
                "search_documents_tool",
                "get_document_tool",
                "list_documents_tool",
                "delete_document_tool",
                "update_document_tool",
            }

            expected = public_tools | document_tools
            assert tool_names == expected, f"Expected {expected}, got {tool_names}"

            # Should NOT see user, collection, or admin tools
            forbidden_tools = {
                "user_profile_tool",
                "create_collection_tool",
                "list_collections_tool",
                "get_collection_tool",
                "delete_collection_tool",
                "rename_collection_tool",
                "create_collection_access_token_tool",
                "list_collection_access_tokens_tool",
                "revoke_collection_access_token_tool",
                "rotate_collection_access_token_tool",
                "create_pat_token_tool",
                "list_pat_tokens_tool",
                "revoke_pat_token_tool",
                "rotate_pat_token_tool",
                "list_users_tool",
                "get_user_tool",
                "update_user_tool",
                "delete_user_tool",
            }
            assert forbidden_tools.isdisjoint(tool_names), f"API key should not see: {tool_names & forbidden_tools}"

            print(f"\nAPI key user has {len(tool_names)} tools: {tool_names}")
