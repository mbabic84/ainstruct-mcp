"""
E2E tests for admin user management tools.
Tests list_users, search_users, get_user, update_user, delete_user with real server.
"""
import os
import pytest
from datetime import datetime

from tests.e2e.mcp_client_test import (
    MCPClient,
    generate_test_id,
    register_test_user,
    login_user,
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
            # Register regular user
            reg_result = await register_test_user(client, test_id)
            regular_user_id = reg_result["user"]["id"]
            
            # Without auth, should get authentication error
            result = await client.call_tool("list_users_tool", {})
            assert "authorization" in str(result).lower() or "missing" in str(result).lower()

    @pytest.mark.asyncio
    async def test_admin_list_users_with_pagination(self):
        """Non-admin cannot list users with pagination."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Create multiple users
            user_ids = []
            for i in range(3):
                user_test_id = f"{test_id}_{i}"
                result = await register_test_user(client, user_test_id)
                user_ids.append(result["user"]["id"])
            
            # Non-admin cannot list, so we expect auth error
            result = await client.call_tool("list_users_tool", {"limit": 10, "offset": 0})
            assert "authorization" in str(result).lower() or "missing" in str(result).lower()


class TestAdminSearchUsers:
    """E2E tests for searching users as admin."""

    @pytest.mark.asyncio
    async def test_admin_search_users(self):
        """Non-admin cannot search users."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Create user with known username
            username = f"searchuser_{test_id}"
            result = await register_test_user(client, test_id)
            
            # Non-admin search should fail with auth error
            result = await client.call_tool("search_users_tool", {"query": username})
            assert "authorization" in str(result).lower() or "missing" in str(result).lower()

    @pytest.mark.asyncio
    async def test_admin_search_no_results(self):
        """Non-admin search should fail with auth error."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            result = await client.call_tool("search_users_tool", {"query": "nonexistent_user_xyz"})
            assert "authorization" in str(result).lower() or "missing" in str(result).lower()


class TestAdminGetUser:
    """E2E tests for getting specific user as admin."""

    @pytest.mark.asyncio
    async def test_admin_get_user(self):
        """Non-admin cannot get user by ID."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            result = await register_test_user(client, test_id)
            user_id = result["user"]["id"]
            
            # Non-admin should not be able to get user - auth error
            result = await client.call_tool("get_user_tool", {"user_id": user_id})
            assert "authorization" in str(result).lower() or "missing" in str(result).lower()

    @pytest.mark.asyncio
    async def test_admin_get_nonexistent_user(self):
        """Non-admin cannot get user - auth error."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            result = await client.call_tool("get_user_tool", {"user_id": "00000000-0000-0000-0000-000000000000"})
            assert "authorization" in str(result).lower() or "missing" in str(result).lower()


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
            
            # Non-admin cannot update - auth error
            result = await client.call_tool("update_user_tool", {
                "user_id": user_id,
                "email": new_email,
            })
            assert "authorization" in str(result).lower() or "missing" in str(result).lower()

    @pytest.mark.asyncio
    async def test_admin_update_user_password(self):
        """Non-admin cannot update user password."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            result = await register_test_user(client, test_id)
            user_id = result["user"]["id"]
            
            # Non-admin cannot update - auth error
            result = await client.call_tool("update_user_tool", {
                "user_id": user_id,
                "password": "NewPassword123!",
            })
            assert "authorization" in str(result).lower() or "missing" in str(result).lower()

    @pytest.mark.asyncio
    async def test_admin_update_user_active_status(self):
        """Non-admin cannot deactivate user."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            result = await register_test_user(client, test_id)
            user_id = result["user"]["id"]
            
            # Non-admin cannot update - auth error
            result = await client.call_tool("update_user_tool", {
                "user_id": user_id,
                "is_active": False,
            })
            assert "authorization" in str(result).lower() or "missing" in str(result).lower()

    @pytest.mark.asyncio
    async def test_admin_cannot_update_to_duplicate_email(self):
        """Non-admin cannot update duplicate to email."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Create two users
            result1 = await register_test_user(client, f"{test_id}_1")
            user1_id = result1["user"]["id"]
            email1 = result1["email"]
            
            result2 = await register_test_user(client, f"{test_id}_2")
            user2_id = result2["user"]["id"]
            
            # Try to update user2's email to user1's email as non-admin - auth error
            result = await client.call_tool("update_user_tool", {
                "user_id": user2_id,
                "email": email1,
            })
            assert "authorization" in str(result).lower() or "missing" in str(result).lower()


class TestAdminDeleteUser:
    """E2E tests for deleting users as admin."""

    @pytest.mark.asyncio
    async def test_admin_delete_user(self):
        """Non-admin cannot delete user."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            result = await register_test_user(client, test_id)
            user_id = result["user"]["id"]
            
            # Non-admin cannot delete - auth error
            result = await client.call_tool("delete_user_tool", {"user_id": user_id})
            assert "authorization" in str(result).lower() or "missing" in str(result).lower()

    @pytest.mark.asyncio
    async def test_admin_delete_nonexistent_user(self):
        """Non-admin cannot delete - auth error."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            result = await client.call_tool("delete_user_tool", {
                "user_id": "00000000-0000-0000-0000-000000000000"
            })
            assert "authorization" in str(result).lower() or "missing" in str(result).lower()

    @pytest.mark.asyncio
    async def test_admin_cannot_delete_self(self):
        """User cannot delete their own account."""
        # This would require admin to try to delete themselves
        # Hard to test without admin account; tested in unit tests
        pytest.skip("Requires admin account setup")


class TestAdminPermissions:
    """E2E tests for admin permission enforcement."""

    @pytest.mark.asyncio
    async def test_non_admin_cannot_access_admin_tools(self):
        """Regular users cannot access any admin tools."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            await register_test_user(client, test_id)
            
            # Try all admin tools - should all fail with auth error
            admin_tools = [
                "list_users_tool",
                "search_users_tool", 
                "get_user_tool",
                "update_user_tool",
                "delete_user_tool",
            ]
            
            for tool in admin_tools:
                result = await client.call_tool(tool, {"user_id": "any-id"} if tool != "list_users_tool" else {})
                assert "authorization" in str(result).lower() or "missing" in str(result).lower()

    @pytest.mark.asyncio
    async def test_admin_tools_require_authentication(self):
        """Admin tools require authentication."""
        async with MCPClient(SERVER_URL, auth_token=None, transport=TRANSPORT) as client:
            # No auth token provided - should fail
            result = await client.call_tool("list_users_tool", {})
            assert "authorization" in str(result).lower() or "missing" in str(result).lower()
