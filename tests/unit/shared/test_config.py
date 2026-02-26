"""Tests for shared config module."""


class TestSettings:
    """Test cases for Settings class."""

    def test_settings_object_exists(self):
        """Test that settings object can be imported."""
        from shared.config import settings
        assert settings is not None

    def test_qdrant_url(self):
        """Test qdrant_url setting."""
        from shared.config import settings
        assert settings.qdrant_url is not None

    def test_embedding_dimensions(self):
        """Test embedding_dimensions setting."""
        from shared.config import settings
        assert settings.embedding_dimensions > 0

    def test_host_setting(self):
        """Test host setting."""
        from shared.config import settings
        assert settings.host is not None

    def test_port_setting(self):
        """Test port setting."""
        from shared.config import settings
        assert settings.port > 0

    def test_jwt_algorithm(self):
        """Test JWT algorithm setting."""
        from shared.config import settings
        assert settings.jwt_algorithm == "HS256"

    def test_jwt_token_expiry(self):
        """Test JWT token expiry settings."""
        from shared.config import settings
        assert settings.jwt_access_token_expire_minutes > 0
        assert settings.jwt_refresh_token_expire_days > 0

    def test_chunk_settings(self):
        """Test chunk settings."""
        from shared.config import settings
        assert settings.chunk_max_tokens > 0
        assert settings.chunk_overlap_tokens >= 0
