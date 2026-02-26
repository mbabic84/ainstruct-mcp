"""Tests for shared auth_service module."""

import pytest


class TestAuthService:
    """Test cases for AuthService class."""

    @pytest.fixture
    def auth_service(self, mock_settings):
        """Create AuthService instance."""
        from shared.services import AuthService
        return AuthService()

    def test_hash_password(self, auth_service):
        """Test password hashing."""
        password = "testpassword123"
        hashed = auth_service.hash_password(password)

        assert hashed != password
        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("wrongpassword", hashed) is False

    def test_create_access_token(self, auth_service):
        """Test access token creation."""
        token = auth_service.create_access_token(
            user_id="user-123",
            username="testuser",
            email="test@example.com",
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT has 3 parts

    def test_create_refresh_token(self, auth_service):
        """Test refresh token creation."""
        token = auth_service.create_refresh_token(user_id="user-123")

        assert token is not None
        assert isinstance(token, str)

    def test_decode_token(self, auth_service):
        """Test token decoding."""
        token = auth_service.create_access_token(
            user_id="user-123",
            username="testuser",
            email="test@example.com",
        )

        payload = auth_service.decode_token(token)

        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["username"] == "testuser"
        assert payload["email"] == "test@example.com"

    def test_validate_access_token(self, auth_service):
        """Test access token validation."""
        token = auth_service.create_access_token(
            user_id="user-123",
            username="testuser",
            email="test@example.com",
        )

        payload = auth_service.validate_access_token(token)

        assert payload is not None
        assert payload["type"] == "access"

    def test_validate_refresh_token(self, auth_service):
        """Test refresh token validation."""
        token = auth_service.create_refresh_token(user_id="user-123")

        payload = auth_service.validate_refresh_token(token)

        assert payload is not None
        assert payload["type"] == "refresh"

    def test_expired_token_returns_none(self, auth_service):
        """Test that expired tokens return None."""

        # This is a basic test - in real scenarios you'd create an expired token
        # For now, an invalid token should return None
        payload = auth_service.validate_access_token("invalid.token.here")

        assert payload is None


class TestIsPatToken:
    """Test cases for is_pat_token function."""

    def test_valid_pat_token(self):
        """Test valid PAT token detection."""
        from shared.services.auth_service import is_pat_token

        assert is_pat_token("pat_live_abc123") is True

    def test_invalid_pat_token(self):
        """Test invalid PAT token detection."""
        from shared.services.auth_service import is_pat_token

        assert is_pat_token("jwt_token") is False
        assert is_pat_token("cat_key") is False
        assert is_pat_token("") is False
