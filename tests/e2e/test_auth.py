"""
E2E tests for authentication tools (user registration, login, refresh).
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
# Use HTTP transport (streamable HTTP, modern MCP protocol)
TRANSPORT = os.environ.get("MCP_TRANSPORT", "http")


class TestUserRegistration:
    """Test user registration flow."""
    
    @pytest.mark.asyncio
    async def test_register_new_user(self):
        """Register a new user account."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            result = await register_test_user(client, test_id)
            
            assert "user" in result
            user = result["user"]

            # Check user was created
            assert user.get("id") is not None
            assert user.get("email") == result["email"]
            assert user.get("username") == result["username"]
            assert user.get("is_active") is True
            assert user.get("is_superuser") is False

            print(f"\nRegistered user: {user.get('username')} (id: {user.get('id')})")


class TestUserLogin:
    """Test user login and token management."""
    
    @pytest.mark.asyncio
    async def test_login_flow(self):
        """Test complete login flow: register -> login -> profile."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Register
            reg_result = await register_test_user(client, test_id)

            # Login
            login_result = await login_user(
                client, 
                reg_result["username"], 
                reg_result["password"]
            )

            assert "access_token" in login_result
            assert "refresh_token" in login_result
            assert login_result.get("token_type") == "bearer"
            assert login_result.get("expires_in") > 0

            access_token = login_result["access_token"]
            refresh_token = login_result["refresh_token"]

            print(f"\nLogged in, got access token: {access_token[:50]}...")

            # Test profile with JWT token
            async with MCPClient(SERVER_URL, auth_token=access_token, transport=TRANSPORT) as auth_client:
                profile = await auth_client.call_tool("user_profile_tool", {})

                assert profile.get("username") == reg_result["username"]
                assert profile.get("email") == reg_result["email"]

                print(f"\nGot profile: {profile.get('username')}")
            
            # Test token refresh
            refresh_result = await client.call_tool("user_refresh_tool", {
                "refresh_token": refresh_token,
            })

            assert "access_token" in refresh_result
            assert refresh_result["access_token"] != access_token

            print("\nRefreshed token successfully")
