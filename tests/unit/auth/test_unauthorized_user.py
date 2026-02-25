"""
Unit tests for unauthorized user behavior at the middleware level.
Tests that the AuthMiddleware properly handles unauthenticated requests.
"""
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
    AuthMiddleware,
    get_tool_auth_level,
)
from app.tools.context import clear_all_auth


class TestUnauthorizedUserMiddleware:
    """Test AuthMiddleware behavior for unauthorized users."""

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
    async def test_on_call_tool_public_tools_allowed(self):
        """Public tools should be callable without authentication."""
        from fastmcp.server.middleware import MiddlewareContext

        middleware = AuthMiddleware()
        call_next = AsyncMock(return_value={"result": "success"})
        context = MagicMock(spec=MiddlewareContext)

        for tool_name in PUBLIC_TOOLS:
            message = MagicMock()
            message.name = tool_name
            context.message = message
            context.fastmcp_context = None

            result = await middleware.on_call_tool(context, call_next)
            assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_on_call_tool_protected_tools_rejected_no_header(self, mock_tools):
        """Protected tools should be rejected without auth header."""
        from fastmcp.server.middleware import MiddlewareContext

        middleware = AuthMiddleware()
        call_next = AsyncMock(return_value={"result": "success"})
        context = MagicMock(spec=MiddlewareContext)
        context.fastmcp_context = None

        protected_tools = (
            USER_TOOLS | USER_COLLECTION_TOOLS | KEY_PAT_TOOLS | DOCUMENT_TOOLS | ADMIN_TOOLS
        )

        with patch("app.tools.auth.get_http_headers") as mock_headers:
            mock_headers.return_value = {}

            for tool_name in protected_tools:
                message = MagicMock()
                message.name = tool_name
                context.message = message

                with pytest.raises(ValueError, match="Missing or invalid Authorization header"):
                    await middleware.on_call_tool(context, call_next)

    @pytest.mark.asyncio
    async def test_on_call_tool_protected_tools_rejected_invalid_header(self, mock_tools):
        """Protected tools should be rejected with invalid auth header."""
        from fastmcp.server.middleware import MiddlewareContext

        middleware = AuthMiddleware()
        call_next = AsyncMock(return_value={"result": "success"})
        context = MagicMock(spec=MiddlewareContext)
        context.fastmcp_context = None

        protected_tools = (
            USER_TOOLS | USER_COLLECTION_TOOLS | KEY_PAT_TOOLS | DOCUMENT_TOOLS | ADMIN_TOOLS
        )

        with patch("app.tools.auth.get_http_headers") as mock_headers:
            mock_headers.return_value = {"authorization": "InvalidFormat"}

            for tool_name in protected_tools:
                message = MagicMock()
                message.name = tool_name
                context.message = message

                with pytest.raises(ValueError, match="Missing or invalid Authorization header"):
                    await middleware.on_call_tool(context, call_next)

    @pytest.mark.asyncio
    async def test_on_call_tool_empty_bearer_token_rejected(self, mock_tools):
        """Empty Bearer token should be rejected."""
        from fastmcp.server.middleware import MiddlewareContext

        middleware = AuthMiddleware()
        call_next = AsyncMock(return_value={"result": "success"})
        context = MagicMock(spec=MiddlewareContext)
        context.fastmcp_context = None

        message = MagicMock()
        message.name = "user_profile_tool"
        context.message = message

        with patch("app.tools.auth.get_http_headers") as mock_headers:
            mock_headers.return_value = {"authorization": "Bearer   "}

            with pytest.raises(ValueError, match="Missing token"):
                await middleware.on_call_tool(context, call_next)

    @pytest.mark.asyncio
    async def test_on_call_tool_invalid_jwt_rejected(self, mock_tools):
        """Invalid JWT token should be rejected."""
        from fastmcp.server.middleware import MiddlewareContext

        middleware = AuthMiddleware()
        call_next = AsyncMock(return_value={"result": "success"})
        context = MagicMock(spec=MiddlewareContext)
        context.fastmcp_context = None

        message = MagicMock()
        message.name = "user_profile_tool"
        context.message = message

        with patch("app.tools.auth.get_http_headers") as mock_headers:
            mock_headers.return_value = {"authorization": "Bearer invalid.jwt.token"}

            with patch("app.tools.auth.is_jwt_token", return_value=True):
                with patch("app.tools.auth.verify_jwt_token", return_value=None):
                    with pytest.raises(ValueError, match="Invalid or expired JWT token"):
                        await middleware.on_call_tool(context, call_next)

    @pytest.mark.asyncio
    async def test_on_call_tool_invalid_pat_rejected(self, mock_tools):
        """Invalid PAT token should be rejected."""
        from fastmcp.server.middleware import MiddlewareContext

        middleware = AuthMiddleware()
        call_next = AsyncMock(return_value={"result": "success"})
        context = MagicMock(spec=MiddlewareContext)
        context.fastmcp_context = None

        message = MagicMock()
        message.name = "user_profile_tool"
        context.message = message

        with patch("app.tools.auth.get_http_headers") as mock_headers:
            mock_headers.return_value = {"authorization": "Bearer pat_invalid"}

            with patch("app.tools.auth.is_pat_token", return_value=True):
                with patch("app.tools.auth.verify_pat_token", return_value=None):
                    with pytest.raises(ValueError, match="Invalid or expired PAT token"):
                        await middleware.on_call_tool(context, call_next)

    @pytest.mark.asyncio
    async def test_on_call_tool_invalid_api_key_rejected(self, mock_tools):
        """Invalid API key should be rejected."""
        from fastmcp.server.middleware import MiddlewareContext

        middleware = AuthMiddleware()
        call_next = AsyncMock(return_value={"result": "success"})
        context = MagicMock(spec=MiddlewareContext)
        context.fastmcp_context = None

        message = MagicMock()
        message.name = "store_document_tool"
        context.message = message

        with patch("app.tools.auth.get_http_headers") as mock_headers:
            mock_headers.return_value = {"authorization": "Bearer invalid_api_key"}

            with patch("app.tools.auth.is_pat_token", return_value=False):
                with patch("app.tools.auth.is_jwt_token", return_value=False):
                    with patch("app.tools.auth.verify_cat_token", return_value=None):
                        with pytest.raises(ValueError, match="Invalid API key"):
                            await middleware.on_call_tool(context, call_next)

    @pytest.mark.asyncio
    async def test_on_list_tools_no_auth_returns_only_public(self, mock_tools):
        """List tools without auth should return only public tools."""
        from fastmcp.server.middleware import MiddlewareContext

        middleware = AuthMiddleware()
        call_next = AsyncMock(return_value=mock_tools)
        context = MagicMock(spec=MiddlewareContext)
        context.fastmcp_context = None

        with patch("app.tools.auth.get_http_headers") as mock_headers:
            mock_headers.return_value = {}

            result = await middleware.on_list_tools(context, call_next)

            result_names = {tool.name for tool in result}
            assert result_names == PUBLIC_TOOLS

    @pytest.mark.asyncio
    async def test_on_list_tools_invalid_token_returns_only_public(self, mock_tools):
        """List tools with invalid token should return only public tools."""
        from fastmcp.server.middleware import MiddlewareContext

        middleware = AuthMiddleware()
        call_next = AsyncMock(return_value=mock_tools)
        context = MagicMock(spec=MiddlewareContext)
        context.fastmcp_context = None

        with patch("app.tools.auth.get_http_headers") as mock_headers:
            mock_headers.return_value = {"authorization": "Bearer invalid_token"}

            with patch("app.tools.auth.is_pat_token", return_value=False):
                with patch("app.tools.auth.is_jwt_token", return_value=True):
                    with patch("app.tools.auth.verify_jwt_token", return_value=None):
                        result = await middleware.on_list_tools(context, call_next)

                        result_names = {tool.name for tool in result}
                        assert result_names == PUBLIC_TOOLS

    @pytest.mark.asyncio
    async def test_on_list_tools_malformed_header_returns_only_public(self, mock_tools):
        """List tools with malformed auth header should return only public tools."""
        from fastmcp.server.middleware import MiddlewareContext

        middleware = AuthMiddleware()
        call_next = AsyncMock(return_value=mock_tools)
        context = MagicMock(spec=MiddlewareContext)
        context.fastmcp_context = None

        with patch("app.tools.auth.get_http_headers") as mock_headers:
            mock_headers.return_value = {"authorization": "NotBearer token"}

            result = await middleware.on_list_tools(context, call_next)

            result_names = {tool.name for tool in result}
            assert result_names == PUBLIC_TOOLS


class TestUnauthorizedUserToolAuthLevels:
    """Test auth level categorization for unauthorized access."""

    def test_public_tools_have_none_auth_level(self):
        """All public tools should have AuthLevel.NONE."""
        for tool in PUBLIC_TOOLS:
            assert get_tool_auth_level(tool) == AuthLevel.NONE, f"{tool} should be public"

    def test_document_tools_require_auth(self):
        """Document tools should require authentication (not public)."""
        for tool in DOCUMENT_TOOLS:
            assert get_tool_auth_level(tool) != AuthLevel.NONE, f"{tool} should require auth"

    def test_collection_tools_require_auth(self):
        """Collection tools should require authentication (not public)."""
        for tool in USER_COLLECTION_TOOLS:
            assert get_tool_auth_level(tool) != AuthLevel.NONE, f"{tool} should require auth"

    def test_admin_tools_require_admin(self):
        """Admin tools should require admin level."""
        for tool in ADMIN_TOOLS:
            assert get_tool_auth_level(tool) == AuthLevel.ADMIN, f"{tool} should require admin"

    def test_unknown_tool_defaults_to_admin(self):
        """Unknown tools should default to ADMIN level (fail closed)."""
        assert get_tool_auth_level("unknown_tool") == AuthLevel.ADMIN
        assert get_tool_auth_level("") == AuthLevel.ADMIN
        assert get_tool_auth_level("random_name") == AuthLevel.ADMIN


class TestUnauthorizedUserContext:
    """Test context behavior for unauthorized users."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    def test_get_user_info_returns_none(self):
        """get_user_info should return None when not authenticated."""
        from app.tools.context import get_user_info
        assert get_user_info() is None

    def test_get_cat_info_returns_none(self):
        """get_cat_info should return None when not authenticated."""
        from app.tools.context import get_cat_info
        assert get_cat_info() is None

    def test_get_pat_info_returns_none(self):
        """get_pat_info should return None when not authenticated."""
        from app.tools.context import get_pat_info
        assert get_pat_info() is None

    def test_get_current_user_id_returns_none(self):
        """get_current_user_id should return None when not authenticated."""
        from app.tools.context import get_current_user_id
        assert get_current_user_id() is None

    def test_is_authenticated_returns_false(self):
        """is_authenticated should return False when not authenticated."""
        from app.tools.context import is_authenticated
        assert is_authenticated() is False

    def test_has_write_permission_returns_false(self):
        """has_write_permission should return False when not authenticated."""
        from app.tools.context import has_write_permission
        assert has_write_permission() is False
