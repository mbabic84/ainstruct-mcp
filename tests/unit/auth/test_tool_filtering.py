from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tools.auth import (
    ADMIN_TOOLS,
    DOCUMENT_TOOLS,
    KEY_PAT_TOOLS,
    PUBLIC_TOOLS,
    USER_COLLECTION_TOOLS,
    USER_TOOLS,
    AuthLevel,
    get_tool_auth_level,
)
from app.tools.context import clear_all_auth


# All tools registered in server.py - this must be updated when adding new tools
ALL_REGISTERED_TOOLS: set[str] = {
    # Public tools (no auth required)
    "user_register_tool",
    "user_login_tool",
    "user_refresh_tool",
    # User tools (JWT/PAT required)
    "user_profile_tool",
    # User collection tools (JWT/PAT required - user owns collections)
    "create_collection_tool",
    "list_collections_tool",
    "get_collection_tool",
    "delete_collection_tool",
    "rename_collection_tool",
    "move_document_tool",
    # Key/PAT tools (JWT/PAT required)
    "create_collection_access_token_tool",
    "list_collection_access_tokens_tool",
    "revoke_collection_access_token_tool",
    "rotate_collection_access_token_tool",
    "create_pat_token_tool",
    "list_pat_tokens_tool",
    "revoke_pat_token_tool",
    "rotate_pat_token_tool",
    # Document tools (API key or JWT/PAT - bound to single collection)
    "store_document_tool",
    "search_documents_tool",
    "get_document_tool",
    "list_documents_tool",
    "delete_document_tool",
    "update_document_tool",
    # Admin tools (admin scope required)
    "list_users_tool",
    "search_users_tool",
    "get_user_tool",
    "update_user_tool",
    "delete_user_tool",
}


class TestToolAuthLevels:
    """Test that tools are correctly categorized by auth level."""

    def test_public_tools(self):
        """Public tools should have NONE auth level."""
        for tool in PUBLIC_TOOLS:
            assert get_tool_auth_level(tool) == AuthLevel.NONE

    def test_user_tools(self):
        """User tools should have JWT_OR_PAT auth level."""
        for tool in USER_TOOLS:
            assert get_tool_auth_level(tool) == AuthLevel.JWT_OR_PAT

    def test_collection_tools(self):
        """Collection tools should have JWT_OR_PAT auth level."""
        for tool in USER_COLLECTION_TOOLS:
            assert get_tool_auth_level(tool) == AuthLevel.JWT_OR_PAT

    def test_key_pat_tools(self):
        """Key/PAT tools should have JWT_OR_PAT auth level."""
        for tool in KEY_PAT_TOOLS:
            assert get_tool_auth_level(tool) == AuthLevel.JWT_OR_PAT

    def test_document_tools(self):
        """Document tools should have API_KEY auth level."""
        for tool in DOCUMENT_TOOLS:
            assert get_tool_auth_level(tool) == AuthLevel.API_KEY

    def test_admin_tools(self):
        """Admin tools should have ADMIN auth level."""
        for tool in ADMIN_TOOLS:
            assert get_tool_auth_level(tool) == AuthLevel.ADMIN

    def test_unknown_tool_returns_admin(self):
        """Unknown tools should default to ADMIN for security (fail closed)."""
        assert get_tool_auth_level("unknown_tool") == AuthLevel.ADMIN
        assert get_tool_auth_level("") == AuthLevel.ADMIN

    def test_all_registered_tools_have_auth_level(self):
        """All registered tools must be covered by an auth set.
        
        This test ensures no tool is accidentally left without proper
        authorization configuration. If this test fails, the tool needs
        to be added to the appropriate auth set in auth.py.
        """
        all_auth_set_tools = (
            PUBLIC_TOOLS |
            USER_TOOLS |
            USER_COLLECTION_TOOLS |
            KEY_PAT_TOOLS |
            DOCUMENT_TOOLS |
            ADMIN_TOOLS
        )
        
        missing_tools = ALL_REGISTERED_TOOLS - all_auth_set_tools
        assert not missing_tools, (
            f"Tools not in any auth set (security risk): {missing_tools}. "
            f"Add them to the appropriate set in auth.py"
        )

    def test_auth_sets_match_registered_tools(self):
        """Auth sets should not contain tools that aren't registered.
        
        This catches typos or removed tools that are still in auth sets.
        """
        all_auth_set_tools = (
            PUBLIC_TOOLS |
            USER_TOOLS |
            USER_COLLECTION_TOOLS |
            KEY_PAT_TOOLS |
            DOCUMENT_TOOLS |
            ADMIN_TOOLS
        )
        
        extra_tools = all_auth_set_tools - ALL_REGISTERED_TOOLS
        assert not extra_tools, (
            f"Tools in auth sets but not registered in server.py: {extra_tools}"
        )


class TestOnListToolsFiltering:
    """Test the on_list_tools filtering logic."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.fixture
    def mock_tools(self):
        """Create mock tool objects with name attribute."""
        tools = []
        all_tool_names = (
            list(PUBLIC_TOOLS) +
            list(USER_TOOLS) +
            list(USER_COLLECTION_TOOLS) +
            list(KEY_PAT_TOOLS) +
            list(DOCUMENT_TOOLS) +
            list(ADMIN_TOOLS)
        )
        for name in all_tool_names:
            tool = MagicMock()
            tool.name = name
            tools.append(tool)
        return tools

    @pytest.mark.asyncio
    async def test_jwt_non_admin_returns_user_tools(self, mock_tools):
        """JWT non-admin should see public + document + user + collection + key/pat tools."""
        from fastmcp.server.middleware import MiddlewareContext

        from app.tools.auth import AuthMiddleware

        user_info = {
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "scopes": [],
        }

        with patch("app.tools.auth.get_http_headers") as mock_headers:
            mock_headers.return_value = {"authorization": "Bearer jwt_token"}

            with patch("app.tools.auth.is_pat_token", return_value=False):
                with patch("app.tools.auth.is_jwt_token", return_value=True):
                    with patch("app.tools.auth.verify_jwt_token", return_value=user_info):
                        middleware = AuthMiddleware()
                        call_next = AsyncMock(return_value=mock_tools)
                        context = MagicMock(spec=MiddlewareContext)
                        context.fastmcp_context = None

                        result = await middleware.on_list_tools(context, call_next)

                        result_names = {tool.name for tool in result}
                        expected = PUBLIC_TOOLS | DOCUMENT_TOOLS | USER_TOOLS | USER_COLLECTION_TOOLS | KEY_PAT_TOOLS
                        assert result_names == expected

    @pytest.mark.asyncio
    async def test_jwt_admin_returns_all_tools(self, mock_tools):
        """JWT admin should see all tools including admin tools."""
        from fastmcp.server.middleware import MiddlewareContext

        from app.tools.auth import AuthMiddleware

        admin_info = {
            "id": "admin-123",
            "username": "admin",
            "email": "admin@example.com",
            "is_superuser": True,
            "scopes": [],
        }

        with patch("app.tools.auth.get_http_headers") as mock_headers:
            mock_headers.return_value = {"authorization": "Bearer admin_jwt_token"}

            with patch("app.tools.auth.is_pat_token", return_value=False):
                with patch("app.tools.auth.is_jwt_token", return_value=True):
                    with patch("app.tools.auth.verify_jwt_token", return_value=admin_info):
                        middleware = AuthMiddleware()
                        call_next = AsyncMock(return_value=mock_tools)
                        context = MagicMock(spec=MiddlewareContext)
                        context.fastmcp_context = None

                        result = await middleware.on_list_tools(context, call_next)

                        result_names = {tool.name for tool in result}
                        expected = (
                            PUBLIC_TOOLS | DOCUMENT_TOOLS | USER_TOOLS |
                            USER_COLLECTION_TOOLS | KEY_PAT_TOOLS | ADMIN_TOOLS
                        )
                        assert result_names == expected

    @pytest.mark.asyncio
    async def test_pat_non_admin_returns_user_tools(self, mock_tools):
        """PAT non-admin should see public + document + user + collection + key/pat tools."""
        from fastmcp.server.middleware import MiddlewareContext

        from app.tools.auth import AuthMiddleware

        pat_info = {
            "id": "pat-123",
            "user_id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "scopes": [],
        }

        with patch("app.tools.auth.get_http_headers") as mock_headers:
            mock_headers.return_value = {"authorization": "Bearer pat_token_abc"}

            with patch("app.tools.auth.is_pat_token", return_value=True):
                with patch("app.tools.auth.verify_pat_token", return_value=pat_info):
                    middleware = AuthMiddleware()
                    call_next = AsyncMock(return_value=mock_tools)
                    context = MagicMock(spec=MiddlewareContext)
                    context.fastmcp_context = None

                    result = await middleware.on_list_tools(context, call_next)

                    result_names = {tool.name for tool in result}
                    expected = PUBLIC_TOOLS | DOCUMENT_TOOLS | USER_TOOLS | USER_COLLECTION_TOOLS | KEY_PAT_TOOLS
                    assert result_names == expected

    @pytest.mark.asyncio
    async def test_pat_admin_returns_all_tools(self, mock_tools):
        """PAT admin should see all tools including admin tools."""
        from fastmcp.server.middleware import MiddlewareContext

        from app.tools.auth import AuthMiddleware

        pat_admin_info = {
            "id": "pat-admin-123",
            "user_id": "admin-123",
            "username": "admin",
            "email": "admin@example.com",
            "is_superuser": True,
            "scopes": [],
        }

        with patch("app.tools.auth.get_http_headers") as mock_headers:
            mock_headers.return_value = {"authorization": "Bearer pat_token_admin"}

            with patch("app.tools.auth.is_pat_token", return_value=True):
                with patch("app.tools.auth.verify_pat_token", return_value=pat_admin_info):
                    middleware = AuthMiddleware()
                    call_next = AsyncMock(return_value=mock_tools)
                    context = MagicMock(spec=MiddlewareContext)
                    context.fastmcp_context = None

                    result = await middleware.on_list_tools(context, call_next)

                    result_names = {tool.name for tool in result}
                    expected = (
                        PUBLIC_TOOLS | DOCUMENT_TOOLS | USER_TOOLS |
                        USER_COLLECTION_TOOLS | KEY_PAT_TOOLS | ADMIN_TOOLS
                    )
                    assert result_names == expected

    @pytest.mark.asyncio
    async def test_api_key_returns_document_tools(self, mock_tools):
        """API key should see public + document tools."""
        from fastmcp.server.middleware import MiddlewareContext

        from app.tools.auth import AuthMiddleware

        api_key_info = {
            "id": "key-123",
            "label": "test-key",
            "collection_id": "col-123",
            "qdrant_collection": "docs_abc",
            "is_admin": False,
            "permission": "read_write",
        }

        with patch("app.tools.auth.get_http_headers") as mock_headers:
            mock_headers.return_value = {"authorization": "Bearer api_key_xyz"}

            with patch("app.tools.auth.is_pat_token", return_value=False):
                with patch("app.tools.auth.is_jwt_token", return_value=False):
                    with patch("app.tools.auth.verify_api_key", return_value=api_key_info):
                        middleware = AuthMiddleware()
                        call_next = AsyncMock(return_value=mock_tools)
                        context = MagicMock(spec=MiddlewareContext)
                        context.fastmcp_context = None

                        result = await middleware.on_list_tools(context, call_next)

                        result_names = {tool.name for tool in result}
                        expected = PUBLIC_TOOLS | DOCUMENT_TOOLS
                        assert result_names == expected

    @pytest.mark.asyncio
    async def test_list_tools_streamable_http_fallback(self, mock_tools):
        """Test auth header retrieval via context.fastmcp_context (Streamable HTTP fallback)."""
        from fastmcp.server.middleware import MiddlewareContext

        from app.tools.auth import AuthMiddleware

        user_info = {
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "scopes": [],
        }

        # Create mock request with auth header
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer jwt_token_via_context"}

        # Create mock request_context
        mock_request_context = MagicMock()
        mock_request_context.request = mock_request

        # Create mock fastmcp_context
        mock_fastmcp_context = MagicMock()
        mock_fastmcp_context.request_context = mock_request_context

        with patch("app.tools.auth.get_http_headers") as mock_headers:
            # get_http_headers raises exception (simulating Streamable HTTP)
            mock_headers.side_effect = Exception("Not available")

            with patch("app.tools.auth.is_pat_token", return_value=False):
                with patch("app.tools.auth.is_jwt_token", return_value=True):
                    with patch("app.tools.auth.verify_jwt_token", return_value=user_info):
                        middleware = AuthMiddleware()
                        call_next = AsyncMock(return_value=mock_tools)
                        context = MagicMock(spec=MiddlewareContext)
                        context.fastmcp_context = mock_fastmcp_context

                        result = await middleware.on_list_tools(context, call_next)

                        result_names = {tool.name for tool in result}
                        expected = PUBLIC_TOOLS | DOCUMENT_TOOLS | USER_TOOLS | USER_COLLECTION_TOOLS | KEY_PAT_TOOLS
                        assert result_names == expected

    @pytest.mark.asyncio
    async def test_non_list_result_passes_through(self):
        """Non-list results should pass through unchanged."""
        from fastmcp.server.middleware import MiddlewareContext

        from app.tools.auth import AuthMiddleware

        middleware = AuthMiddleware()
        call_next = AsyncMock(return_value="not a list")
        context = MagicMock(spec=MiddlewareContext)

        result = await middleware.on_list_tools(context, call_next)

        assert result == "not a list"
        call_next.assert_called_once()
