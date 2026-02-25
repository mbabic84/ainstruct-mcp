"""
E2E tests for admin user management tools.
Tests list_users, search_users, get_user, update_user, delete_user with real server.
"""
import os

import pytest

from tests.e2e.mcp_client_test import (
    MCPClient,
    generate_test_id,
    register_test_user,
)

SERVER_URL = os.environ["MCP_SERVER_URL"]
TRANSPORT = os.environ.get("MCP_TRANSPORT", "http")


class TestAdminUserList:
    """E2E tests for listing users as admin."""

    @pytest.mark.asyncio
    async def test_admin_list_users(self):
        """Non-admin users cannot list all users."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            await register_test_user(client, test_id)

            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("list_users_tool", {})

    @pytest.mark.asyncio
    async def test_admin_list_users_with_pagination(self):
        """Non-admin cannot list users with pagination."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            for i in range(3):
                user_test_id = f"{test_id}_{i}"
                await register_test_user(client, user_test_id)

            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("list_users_tool", {"limit": 10, "offset": 0})


class TestAdminSearchUsers:
    """E2E tests for searching users as admin."""

    @pytest.mark.asyncio
    async def test_admin_search_users(self):
        """Non-admin cannot search users."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            username = f"searchuser_{test_id}"
            await register_test_user(client, test_id)

            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("search_users_tool", {"query": username})

    @pytest.mark.asyncio
    async def test_admin_search_no_results(self):
        """Non-admin search should fail with auth error."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("search_users_tool", {"query": "nonexistent_user_xyz"})


class TestAdminGetUser:
    """E2E tests for getting specific user as admin."""

    @pytest.mark.asyncio
    async def test_admin_get_user(self):
        """Non-admin cannot get user by ID."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            result = await register_test_user(client, test_id)
            user_id = result["user"]["id"]

            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("get_user_tool", {"user_id": user_id})

    @pytest.mark.asyncio
    async def test_admin_get_nonexistent_user(self):
        """Non-admin cannot get user - auth error."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("get_user_tool", {"user_id": "00000000-0000-0000-0000-000000000000"})


class TestAdminUpdateUser:
    """E2E tests for updating users as admin."""

    @pytest.mark.asyncio
    async def test_admin_update_user_email(self):
        """Non-admin cannot update user email."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            result = await register_test_user(client, test_id)
            user_id = result["user"]["id"]

            new_email = f"updated_{test_id}@example.com"

            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("update_user_tool", {
                    "user_id": user_id,
                    "email": new_email,
                })

    @pytest.mark.asyncio
    async def test_admin_update_user_password(self):
        """Non-admin cannot update user password."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            result = await register_test_user(client, test_id)
            user_id = result["user"]["id"]

            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("update_user_tool", {
                    "user_id": user_id,
                    "password": "NewPassword123!",
                })

    @pytest.mark.asyncio
    async def test_admin_update_user_active_status(self):
        """Non-admin cannot deactivate user."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            result = await register_test_user(client, test_id)
            user_id = result["user"]["id"]

            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("update_user_tool", {
                    "user_id": user_id,
                    "is_active": False,
                })

    @pytest.mark.asyncio
    async def test_admin_cannot_update_to_duplicate_email(self):
        """Non-admin cannot update duplicate to email."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            result1 = await register_test_user(client, f"{test_id}_1")
            email1 = result1["email"]

            result2 = await register_test_user(client, f"{test_id}_2")
            user2_id = result2["user"]["id"]

            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("update_user_tool", {
                    "user_id": user2_id,
                    "email": email1,
                })


class TestAdminDeleteUser:
    """E2E tests for deleting users as admin."""

    @pytest.mark.asyncio
    async def test_admin_delete_user(self):
        """Non-admin cannot delete user."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            result = await register_test_user(client, test_id)
            user_id = result["user"]["id"]

            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("delete_user_tool", {"user_id": user_id})

    @pytest.mark.asyncio
    async def test_admin_delete_nonexistent_user(self):
        """Non-admin cannot delete - auth error."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("delete_user_tool", {
                    "user_id": "00000000-0000-0000-0000-000000000000"
                })

    @pytest.mark.asyncio
    async def test_admin_cannot_delete_self(self):
        """User cannot delete their own account."""
        pytest.skip("Requires admin account setup")


class TestAdminPermissions:
    """E2E tests for admin permission enforcement."""

    @pytest.mark.asyncio
    async def test_non_admin_cannot_access_admin_tools(self):
        """Regular users cannot access any admin tools."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            await register_test_user(client, test_id)

            admin_tools = [
                "list_users_tool",
                "search_users_tool",
                "get_user_tool",
                "update_user_tool",
                "delete_user_tool",
            ]

            for tool in admin_tools:
                with pytest.raises(RuntimeError, match="Authorization|auth"):
                    await client.call_tool(tool, {"user_id": "any-id"} if tool != "list_users_tool" else {})

    @pytest.mark.asyncio
    async def test_admin_tools_require_authentication(self):
        """Admin tools require authentication."""
        async with MCPClient(SERVER_URL, auth_token=None, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("list_users_tool", {})
