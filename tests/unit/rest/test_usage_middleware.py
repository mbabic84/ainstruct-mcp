"""Tests for REST API usage middleware."""



class TestUsageMiddleware:
    """Test cases for usage tracking middleware."""

    def test_should_track_path_documents(self):
        """Test that document paths are tracked."""
        from rest_api.middleware.usage import should_track_path

        assert should_track_path("/api/v1/documents") is True
        assert should_track_path("/api/v1/documents/123") is True
        assert should_track_path("/api/v1/collections") is True
        assert should_track_path("/api/v1/collections/123") is True

    def test_should_skip_path_health(self):
        """Test that health checks are skipped."""
        from rest_api.middleware.usage import should_track_path

        assert should_track_path("/health") is False

    def test_should_skip_path_auth(self):
        """Test that auth endpoints are skipped."""
        from rest_api.middleware.usage import should_track_path

        assert should_track_path("/api/v1/auth/register") is False
        assert should_track_path("/api/v1/auth/login") is False
        assert should_track_path("/api/v1/auth/refresh") is False

    def test_should_skip_path_admin(self):
        """Test that admin endpoints are skipped."""
        from rest_api.middleware.usage import should_track_path

        assert should_track_path("/api/v1/admin/users") is False

    def test_should_skip_path_pat(self):
        """Test that PAT endpoints are skipped."""
        from rest_api.middleware.usage import should_track_path

        assert should_track_path("/api/v1/pat") is False
