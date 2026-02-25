"""
E2E tests for unauthorized (unauthenticated) user behavior.
Tests that unauthorized users can only access public tools and are properly blocked from protected operations.
"""
import os

import pytest

from tests.e2e.mcp_client_test import MCPClient

SERVER_URL = os.environ["MCP_SERVER_URL"]
TRANSPORT = os.environ.get("MCP_TRANSPORT", "http")


class TestUnauthorizedUserToolListing:
    """Test that unauthorized users see only public tools."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_only_public_tools(self):
        """Unauthorized users should only see the 3 public tools."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            tools = await client.list_tools()
            tool_names = {t["name"] for t in tools}

            expected_public = {
                "user_register_tool",
                "user_login_tool",
                "user_refresh_tool",
            }
            assert tool_names == expected_public, f"Expected {expected_public}, got {tool_names}"

    @pytest.mark.asyncio
    async def test_list_tools_count(self):
        """Unauthorized users should see exactly 3 tools."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            tools = await client.list_tools()
            assert len(tools) == 3, f"Expected 3 tools, got {len(tools)}"


class TestUnauthorizedUserPublicTools:
    """Test that unauthorized users CAN use public tools."""

    @pytest.mark.asyncio
    async def test_can_register_user(self):
        """Unauthorized users should be able to register."""
        import uuid
        test_id = uuid.uuid4().hex[:8]

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            result = await client.call_tool("user_register_tool", {
                "email": f"unauth_{test_id}@example.com",
                "username": f"unauth_{test_id}",
                "password": "TestPassword123!",
            })

            assert result.get("id") is not None
            assert result.get("is_active") is True

    @pytest.mark.asyncio
    async def test_can_login_after_register(self):
        """Unauthorized users should be able to login after registering."""
        import uuid
        test_id = uuid.uuid4().hex[:8]
        username = f"unauth_login_{test_id}"
        password = "TestPassword123!"

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            await client.call_tool("user_register_tool", {
                "email": f"{username}@example.com",
                "username": username,
                "password": password,
            })

            result = await client.call_tool("user_login_tool", {
                "username": username,
                "password": password,
            })

            assert "access_token" in result
            assert "refresh_token" in result

    @pytest.mark.asyncio
    async def test_can_refresh_token(self):
        """Unauthorized users should be able to refresh tokens."""
        import uuid
        test_id = uuid.uuid4().hex[:8]
        username = f"unauth_refresh_{test_id}"
        password = "TestPassword123!"

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            await client.call_tool("user_register_tool", {
                "email": f"{username}@example.com",
                "username": username,
                "password": password,
            })

            login_result = await client.call_tool("user_login_tool", {
                "username": username,
                "password": password,
            })

            refresh_result = await client.call_tool("user_refresh_tool", {
                "refresh_token": login_result["refresh_token"],
            })

            assert "access_token" in refresh_result
            assert refresh_result["access_token"] != login_result["access_token"]


class TestUnauthorizedUserDocumentTools:
    """Test that unauthorized users CANNOT use document tools."""

    @pytest.mark.asyncio
    async def test_cannot_store_document(self):
        """Unauthorized users should NOT be able to store documents."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("store_document_tool", {
                    "title": "Test Document",
                    "content": "# Test Content",
                })

    @pytest.mark.asyncio
    async def test_cannot_search_documents(self):
        """Unauthorized users should NOT be able to search documents."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("search_documents_tool", {
                    "query": "test query",
                })

    @pytest.mark.asyncio
    async def test_cannot_get_document(self):
        """Unauthorized users should NOT be able to get documents."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("get_document_tool", {
                    "document_id": "some-doc-id",
                })

    @pytest.mark.asyncio
    async def test_cannot_list_documents(self):
        """Unauthorized users should NOT be able to list documents."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("list_documents_tool", {})

    @pytest.mark.asyncio
    async def test_cannot_delete_document(self):
        """Unauthorized users should NOT be able to delete documents."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("delete_document_tool", {
                    "document_id": "some-doc-id",
                })

    @pytest.mark.asyncio
    async def test_cannot_update_document(self):
        """Unauthorized users should NOT be able to update documents."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("update_document_tool", {
                    "document_id": "some-doc-id",
                    "title": "Updated Title",
                    "content": "Updated content",
                })


class TestUnauthorizedUserCollectionTools:
    """Test that unauthorized users CANNOT use collection tools."""

    @pytest.mark.asyncio
    async def test_cannot_create_collection(self):
        """Unauthorized users should NOT be able to create collections."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("create_collection_tool", {
                    "name": "Test Collection",
                })

    @pytest.mark.asyncio
    async def test_cannot_list_collections(self):
        """Unauthorized users should NOT be able to list collections."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("list_collections_tool", {})

    @pytest.mark.asyncio
    async def test_cannot_get_collection(self):
        """Unauthorized users should NOT be able to get collection details."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("get_collection_tool", {
                    "collection_id": "some-collection-id",
                })

    @pytest.mark.asyncio
    async def test_cannot_delete_collection(self):
        """Unauthorized users should NOT be able to delete collections."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("delete_collection_tool", {
                    "collection_id": "some-collection-id",
                })

    @pytest.mark.asyncio
    async def test_cannot_rename_collection(self):
        """Unauthorized users should NOT be able to rename collections."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("rename_collection_tool", {
                    "collection_id": "some-collection-id",
                    "name": "New Name",
                })


class TestUnauthorizedUserProfileTools:
    """Test that unauthorized users CANNOT use profile tools."""

    @pytest.mark.asyncio
    async def test_cannot_get_profile(self):
        """Unauthorized users should NOT be able to get their profile."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("user_profile_tool", {})


class TestUnauthorizedUserTokenManagement:
    """Test that unauthorized users CANNOT manage API keys and PAT tokens."""

    @pytest.mark.asyncio
    async def test_cannot_create_api_key(self):
        """Unauthorized users should NOT be able to create API keys."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("create_collection_access_token_tool", {
                    "label": "Test Key",
                    "collection_id": "some-collection-id",
                })

    @pytest.mark.asyncio
    async def test_cannot_list_api_keys(self):
        """Unauthorized users should NOT be able to list API keys."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("list_collection_access_tokens_tool", {})

    @pytest.mark.asyncio
    async def test_cannot_create_pat_token(self):
        """Unauthorized users should NOT be able to create PAT tokens."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("create_pat_token_tool", {
                    "label": "Test PAT",
                })

    @pytest.mark.asyncio
    async def test_cannot_list_pat_tokens(self):
        """Unauthorized users should NOT be able to list PAT tokens."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("list_pat_tokens_tool", {})


class TestUnauthorizedUserAdminTools:
    """Test that unauthorized users CANNOT use admin tools."""

    @pytest.mark.asyncio
    async def test_cannot_list_users(self):
        """Unauthorized users should NOT be able to list users."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("list_users_tool", {})

    @pytest.mark.asyncio
    async def test_cannot_search_users(self):
        """Unauthorized users should NOT be able to search users."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("search_users_tool", {
                    "query": "test",
                })

    @pytest.mark.asyncio
    async def test_cannot_get_user(self):
        """Unauthorized users should NOT be able to get user details."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("get_user_tool", {
                    "user_id": "some-user-id",
                })

    @pytest.mark.asyncio
    async def test_cannot_update_user(self):
        """Unauthorized users should NOT be able to update users."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("update_user_tool", {
                    "user_id": "some-user-id",
                    "email": "new@example.com",
                })

    @pytest.mark.asyncio
    async def test_cannot_delete_user(self):
        """Unauthorized users should NOT be able to delete users."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("delete_user_tool", {
                    "user_id": "some-user-id",
                })


class TestUnauthorizedUserInvalidTokens:
    """Test that invalid/malformed tokens are treated as unauthorized."""

    @pytest.mark.asyncio
    async def test_invalid_jwt_token_rejected(self):
        """Invalid JWT token should be rejected."""
        async with MCPClient(SERVER_URL, auth_token="invalid.jwt.token", transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Invalid|JWT|auth"):
                await client.call_tool("user_profile_tool", {})

    @pytest.mark.asyncio
    async def test_invalid_api_key_rejected(self):
        """Invalid API key should be rejected."""
        async with MCPClient(SERVER_URL, auth_token="invalid_api_key_12345", transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Invalid|API key|auth"):
                await client.call_tool("store_document_tool", {
                    "title": "Test",
                    "content": "Content",
                })

    @pytest.mark.asyncio
    async def test_empty_token_rejected(self):
        """Empty token should be rejected."""
        async with MCPClient(SERVER_URL, auth_token="", transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Authorization|auth"):
                await client.call_tool("user_profile_tool", {})

    @pytest.mark.asyncio
    async def test_malformed_token_rejected(self):
        """Token that's not JWT/PAT/API key format should be rejected."""
        async with MCPClient(SERVER_URL, auth_token="not_a_valid_token_format", transport=TRANSPORT) as client:
            with pytest.raises(RuntimeError, match="Invalid|API key|auth"):
                await client.call_tool("user_profile_tool", {})

    @pytest.mark.asyncio
    async def test_invalid_token_list_tools_returns_public(self):
        """Invalid token should result in only public tools being listed."""
        async with MCPClient(SERVER_URL, auth_token="invalid_token_xyz", transport=TRANSPORT) as client:
            tools = await client.list_tools()
            tool_names = {t["name"] for t in tools}

            expected_public = {
                "user_register_tool",
                "user_login_tool",
                "user_refresh_tool",
            }
            assert tool_names == expected_public
