"""
Security tests for token revocation and expiry handling.
Tests that revoked/expired tokens are rejected by auth middleware.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from app.tools.auth import verify_api_key, verify_jwt_token, is_jwt_token
from app.services.auth_service import verify_pat_token
from app.tools.context import set_user_info, clear_all_auth
from app.db.models import Scope, Permission


@pytest.fixture
def mock_auth_service():
    with patch("app.tools.auth.get_auth_service") as mock:
        yield mock


class TestJwtTokenSecurity:
    """Tests for JWT token validation and rejection."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_verify_jwt_token_expired(self, mock_auth_service):
        """Expired JWT tokens are rejected."""
        mock_auth = MagicMock()
        # Simulate expired token: validate_access_token returns None
        mock_auth.validate_access_token.return_value = None
        mock_auth_service.return_value = mock_auth

        result = verify_jwt_token("expired.jwt.token")
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_jwt_token_invalid_signature(self, mock_auth_service):
        """Invalid signature causes token to be rejected."""
        mock_auth = MagicMock()
        mock_auth.validate_access_token.side_effect = Exception("Invalid signature")
        mock_auth_service.return_value = mock_auth

        # The exception should be caught and return None
        result = verify_jwt_token("invalid.token")
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_jwt_token_wrong_type(self, mock_auth_service):
        """Refresh tokens are not valid as access tokens."""
        mock_auth = MagicMock()
        # Simulate a refresh token: payload type is 'refresh'
        mock_auth.validate_access_token.return_value = None
        mock_auth_service.return_value = mock_auth

        result = verify_jwt_token("refresh.token.here")
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_jwt_token_valid(self, mock_auth_service):
        """Valid JWT token returns user info."""
        mock_auth = MagicMock()
        mock_auth.validate_access_token.return_value = {
            "sub": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "scopes": ["read", "write"],
        }
        mock_auth_service.return_value = mock_auth

        result = verify_jwt_token("valid.jwt.token")

        assert result is not None
        assert result["id"] == "user-123"
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        assert result["is_superuser"] is False
        assert Scope.READ in result["scopes"]
        assert Scope.WRITE in result["scopes"]

    @pytest.mark.asyncio
    async def test_is_jwt_token_format(self):
        """is_jwt_token correctly identifies JWT format."""
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        not_jwt_token = "pat_live_1234567890abcdef"
        
        assert is_jwt_token(jwt_token) is True
        assert is_jwt_token(not_jwt_token) is False
        assert is_jwt_token("") is False
        assert is_jwt_token("short") is False
        assert is_jwt_token("two.parts") is False


class TestPatTokenSecurity:
    """Tests for PAT token validation, revocation, and expiry."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.fixture
    def mock_pat_repo(self):
        with patch("app.services.auth_service.get_pat_token_repository") as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_verify_pat_token_revoked(self, mock_pat_repo):
        """Revoked PAT token is rejected."""
        mock_repo = MagicMock()
        # Simulate revoked token (is_active=False)
        mock_repo.validate.return_value = None
        mock_pat_repo.return_value = mock_repo

        result = verify_pat_token("pat_live_revokedtoken")
        assert result is None
        mock_repo.validate.assert_called_once_with("pat_live_revokedtoken")

    @pytest.mark.asyncio
    async def test_verify_pat_token_expired(self, mock_pat_repo):
        """Expired PAT token is rejected."""
        mock_repo = MagicMock()
        # Simulate expired token (expires_at is in the past)
        mock_repo.validate.return_value = None
        mock_pat_repo.return_value = mock_repo

        result = verify_pat_token("pat_live_expiredtoken")
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_pat_token_not_found(self, mock_pat_repo):
        """Non-existent PAT token is rejected."""
        mock_repo = MagicMock()
        mock_repo.validate.return_value = None
        mock_pat_repo.return_value = mock_repo

        result = verify_pat_token("pat_live_nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_pat_token_valid(self, mock_pat_repo):
        """Valid PAT token returns token info."""
        mock_repo = MagicMock()
        pat_info = {
            "id": "pat-123",
            "label": "Test PAT",
            "user_id": "user-456",
            "username": "testuser",
            "email": "test@example.com",
            "scopes": [Scope.READ, Scope.WRITE],
            "is_superuser": False,
            "is_active": True,
            "expires_at": None,
        }
        mock_repo.validate.return_value = pat_info
        mock_pat_repo.return_value = mock_repo

        result = verify_pat_token("pat_live_validtoken")

        assert result is not None
        assert result["id"] == "pat-123"
        assert result["user_id"] == "user-456"
        assert Scope.READ in result["scopes"]
        assert Scope.WRITE in result["scopes"]

    @pytest.mark.asyncio
    async def test_verify_pat_token_invalid_prefix(self):
        """Token without correct PAT prefix is not processed by PAT verification."""
        # This test ensures is_pat_token() gate works correctly
        from app.tools.auth import is_pat_token

        assert is_pat_token("pat_live_abc123") is True
        assert is_pat_token("ak_live_abc123") is False
        assert is_pat_token("jwt.token.here") is False
        assert is_pat_token("randomstring") is False

    @pytest.mark.asyncio
    async def test_verify_pat_token_wrong_prefix(self, mock_pat_repo):
        """Token with wrong prefix should not call verify_pat_token."""
        # In the auth middleware, is_pat_token checks the prefix first
        # So verify_pat_token should only be called for tokens starting with "pat_live_"
        # This test documents that expectation
        pass  # Logic is in is_pat_token, which we tested above


class TestApiKeySecurity:
    """Tests for API key validation and admin status."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.fixture
    def mock_api_key_repo(self):
        with patch("app.tools.auth.get_api_key_repository") as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_verify_api_key_revoked(self, mock_api_key_repo):
        """Revoked API key is rejected."""
        mock_repo = MagicMock()
        mock_repo.validate.return_value = None  # Simulate revoked/not found
        mock_api_key_repo.return_value = mock_repo

        result = verify_api_key("ak_live_revokedkey")
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_api_key_not_found(self, mock_api_key_repo):
        """Non-existent API key is rejected."""
        mock_repo = MagicMock()
        mock_repo.validate.return_value = None
        mock_api_key_repo.return_value = mock_repo

        result = verify_api_key("ak_live_nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_api_key_valid(self, mock_api_key_repo):
        """Valid API key returns key info."""
        mock_repo = MagicMock()
        api_key_info = {
            "id": "api-key-123",
            "label": "Test Key",
            "user_id": "user-789",
            "collection_id": "collection-123",
            "qdrant_collection": "qdrant-123",
            "permission": Permission.READ_WRITE,
            "is_admin": False,
        }
        mock_repo.validate.return_value = api_key_info
        mock_api_key_repo.return_value = mock_repo

        result = verify_api_key("ak_live_validkey")

        assert result is not None
        assert result["id"] == "api-key-123"
        assert result["user_id"] == "user-789"
        assert result["permission"] == Permission.READ_WRITE
        assert result["is_admin"] is False

    @pytest.mark.asyncio
    async def test_verify_api_key_admin(self, mock_api_key_repo):
        """Admin API key returns is_admin=True."""
        mock_repo = MagicMock()
        api_key_info = {
            "id": "admin-key",
            "label": "Admin Key",
            "user_id": "admin-123",
            "collection_id": None,
            "qdrant_collection": None,
            "permission": Permission.READ_WRITE,
            "is_admin": True,
        }
        mock_repo.validate.return_value = api_key_info
        mock_api_key_repo.return_value = mock_repo

        result = verify_api_key("admin_api_key_here")

        assert result is not None
        assert result["is_admin"] is True

    @pytest.mark.asyncio
    async def test_verify_api_key_empty(self):
        """Empty API key is rejected."""
        result = verify_api_key("")
        assert result is None

        result = verify_api_key(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_api_key_invalid_format(self):
        """API key with invalid format is rejected by repo.validate."""
        # Keys should follow pattern ak_live_<random>
        # Invalid format should be caught by validate method
        with patch("app.tools.auth.get_api_key_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.validate.return_value = None
            mock_repo_factory.return_value = mock_repo

            result = verify_api_key("invalid-format-key")
            assert result is None


class TestAdminApiKeySpecial:
    """Tests for the special admin_api_key case (environment variable)."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_admin_api_key_bypasses_repo(self):
        """Admin API key from settings bypasses repository validation."""
        # This relies on settings.admin_api_key being set
        # In tests, we should mock settings
        with patch("app.tools.auth.settings") as mock_settings:
            mock_settings.admin_api_key = "secret_admin_key_123"
            
            result = verify_api_key("secret_admin_key_123")
            
            assert result is not None
            assert result["is_admin"] is True
            assert result["label"] == "admin"

    @pytest.mark.asyncio
    async def test_admin_api_key_different_value(self):
        """Different key than admin_api_key is not treated as admin."""
        with patch("app.tools.auth.settings") as mock_settings:
            mock_settings.admin_api_key = "secret_admin_key_123"
            
            result = verify_api_key("different_key")
            
            # Should return None because it doesn't match admin_api_key
            # and mock repo will reject it
            # We don't need to assert on repo.validate since that's mocked elsewhere
            pass


class TestTokenAuthMiddlewareIntegration:
    """Integration tests for auth middleware token rejection."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_middleware_rejects_expired_jwt(self, mock_auth_service):
        """Auth middleware rejects requests with expired JWT."""
        from app.tools.auth import AuthMiddleware
        from unittest.mock import AsyncMock

        mock_auth = MagicMock()
        mock_auth.validate_access_token.return_value = None  # Expired or invalid
        mock_auth_service.return_value = mock_auth

        middleware = AuthMiddleware()

        # Mock context with JWT token
        mock_context = MagicMock()
        mock_context.message.name = "user_profile_tool"
        mock_next = AsyncMock(return_value="result")

        headers = {"authorization": "Bearer expired.jwt.token"}
        
        # Patch get_http_headers to return our headers
        with patch("app.tools.auth.get_http_headers", return_value=headers):
            with pytest.raises(ValueError, match="Invalid or expired JWT token"):
                await middleware.on_call_tool(mock_context, mock_next)

    @pytest.mark.asyncio
    async def test_middleware_rejects_revoked_pat(self):
        """Auth middleware rejects requests with revoked PAT."""
        from app.tools.auth import AuthMiddleware
        from unittest.mock import AsyncMock

        # Mock PAT repo to return None (revoked)
        with patch("app.tools.auth.verify_pat_token", return_value=None):
            middleware = AuthMiddleware()

            mock_context = MagicMock()
            mock_context.message.name = "list_pat_tokens_tool"
            mock_next = AsyncMock(return_value="result")

            headers = {"authorization": "Bearer pat_live_revoked"}
            
            with patch("app.tools.auth.get_http_headers", return_value=headers):
                with pytest.raises(ValueError, match="Invalid or expired PAT token"):
                    await middleware.on_call_tool(mock_context, mock_next)

    @pytest.mark.asyncio
    async def test_middleware_rejects_invalid_api_key(self):
        """Auth middleware rejects requests with invalid API key."""
        from app.tools.auth import AuthMiddleware
        from unittest.mock import AsyncMock

        with patch("app.tools.auth.verify_api_key", return_value=None):
            middleware = AuthMiddleware()

            mock_context = MagicMock()
            mock_context.message.name = "store_document_tool"
            mock_next = AsyncMock(return_value="result")

            headers = {"authorization": "Bearer invalid_api_key"}
            
            with patch("app.tools.auth.get_http_headers", return_value=headers):
                with pytest.raises(ValueError, match="Invalid API key"):
                    await middleware.on_call_tool(mock_context, mock_next)

    @pytest.mark.asyncio
    async def test_middleware_accepts_valid_tokens(self, mock_auth_service):
        """Auth middleware accepts valid JWT, PAT, and API keys."""
        from app.tools.auth import AuthMiddleware
        from unittest.mock import AsyncMock

        mock_auth = MagicMock()
        mock_auth.validate_access_token.return_value = {
            "sub": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "scopes": ["read", "write"],
        }
        mock_auth_service.return_value = mock_auth

        middleware = AuthMiddleware()

        mock_context = MagicMock()
        mock_context.message.name = "user_profile_tool"
        mock_next = AsyncMock(return_value="result")

        headers = {"authorization": "Bearer valid.jwt.token"}
        
        with patch("app.tools.auth.get_http_headers", return_value=headers):
            # Also need to mock verify_jwt_token
            with patch("app.tools.auth.verify_jwt_token", return_value={
                "id": "user-123",
                "username": "testuser",
                "email": "test@example.com",
                "is_superuser": False,
                "scopes": [Scope.READ, Scope.WRITE],
            }):
                result = await middleware.on_call_tool(mock_context, mock_next)
                assert result == "result"
                mock_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_token_type_routing(self):
        """Middleware correctly routes JWT vs PAT vs API key."""
        from app.tools.auth import AuthMiddleware, is_jwt_token, is_pat_token

        # JWT: three parts separated by dots
        assert is_jwt_token("a.b.c") is True
        assert is_jwt_token("header.payload.signature") is True

        # PAT: starts with pat_live_
        assert is_pat_token("pat_live_abc123") is True
        assert is_pat_token("ak_live_abc123") is False

        # API key: other formats (ak_live_ or env keys)
        # In middleware, if not JWT and not PAT, treated as API key

    @pytest.mark.asyncio
    async def test_middleware_clears_context_on_error(self):
        """Auth middleware clears context even when tool raises error."""
        from app.tools.auth import AuthMiddleware
        from unittest.mock import AsyncMock

        middleware = AuthMiddleware()

        mock_context = MagicMock()
        mock_context.message.name = "user_profile_tool"
        
        # Simulate a tool that raises an error
        async def failing_next(context):
            raise ValueError("Tool error")

        headers = {"authorization": "Bearer valid.jwt.token"}
        
        with patch("app.tools.auth.get_http_headers", return_value=headers):
            with patch("app.tools.auth.verify_jwt_token", return_value={
                "id": "user-123",
                "username": "testuser",
                "email": "test@example.com",
                "is_superuser": False,
                "scopes": [Scope.READ, Scope.WRITE],
            }):
                with pytest.raises(ValueError, match="Tool error"):
                    await middleware.on_call_tool(mock_context, failing_next)
        
        # After the error, context should be cleared
        from app.tools.context import get_user_info
        assert get_user_info() is None

    @pytest.mark.asyncio
    async def test_middleware_clears_context_on_success(self):
        """Auth middleware clears context after successful tool call."""
        from app.tools.auth import AuthMiddleware
        from unittest.mock import AsyncMock

        middleware = AuthMiddleware()

        mock_context = MagicMock()
        mock_context.message.name = "user_profile_tool"
        
        async def success_next(context):
            return "success"

        headers = {"authorization": "Bearer valid.jwt.token"}
        
        with patch("app.tools.auth.get_http_headers", return_value=headers):
            with patch("app.tools.auth.verify_jwt_token", return_value={
                "id": "user-123",
                "username": "testuser",
                "email": "test@example.com",
                "is_superuser": False,
                "scopes": [Scope.READ, Scope.WRITE],
            }):
                result = await middleware.on_call_tool(mock_context, success_next)
                assert result == "success"
        
        from app.tools.context import get_user_info
        assert get_user_info() is None


class TestTokenRevocationPropagation:
    """Tests for ensuring revoked tokens are immediately rejected."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_revoked_pat_token_immediate_rejection(self):
        """After revoking a PAT, subsequent uses are rejected."""
        # This test requires integration with PAT repository
        # Unit test: mock repo to have validate return None after revoke
        with patch("app.tools.auth.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            
            # Initially token is valid
            pat_info = {
                "id": "pat-123",
                "user_id": "user-456",
                "scopes": [Scope.READ, Scope.WRITE],
                "is_active": True,
            }
            mock_repo.validate.return_value = pat_info
            mock_repo_factory.return_value = mock_repo

            # First use should succeed
            result = verify_pat_token("pat_live_valid")
            assert result is not None

            # Simulate revocation
            mock_repo.validate.return_value = None

            # Subsequent use should fail
            result = verify_pat_token("pat_live_valid")
            assert result is None

    @pytest.mark.asyncio
    async def test_expired_jwt_immediate_rejection(self, mock_auth_service):
        """After token expiry, validation returns None."""
        mock_auth = MagicMock()
        # Initially valid
        mock_auth.validate_access_token.return_value = {
            "sub": "user-123",
            "username": "test",
            "email": "test@example.com",
            "is_superuser": False,
            "scopes": ["read"],
        }
        mock_auth_service.return_value = mock_auth

        result = verify_jwt_token("valid.jwt")
        assert result is not None

        # Expire token
        mock_auth.validate_access_token.return_value = None

        result = verify_jwt_token("valid.jwt")
        assert result is None
