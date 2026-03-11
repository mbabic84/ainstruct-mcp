"""Tests for REST API usage middleware."""


class TestUsageMiddleware:
    """Test cases for usage tracking middleware."""

    def test_should_track_path_documents(self):
        """Test that only embedding-requiring document endpoints are tracked."""
        from rest_api.middleware.usage import should_track_path

        # POST /documents (store) - should track
        assert should_track_path("/api/v1/documents", "POST") is True
        # PATCH /documents/{id} (update) - should track
        assert should_track_path("/api/v1/documents/123", "PATCH") is True
        # POST /documents/search (search) - should track
        assert should_track_path("/api/v1/documents/search", "POST") is True

        # Other methods on /documents - should NOT track
        assert should_track_path("/api/v1/documents", "GET") is False
        assert should_track_path("/api/v1/documents/123", "GET") is False
        assert should_track_path("/api/v1/documents/123", "DELETE") is False
        assert should_track_path("/api/v1/documents/123", "PUT") is False

        # Collections endpoints - should NOT track (no embedding)
        assert should_track_path("/api/v1/collections", "POST") is False
        assert should_track_path("/api/v1/collections/123", "GET") is False
        assert should_track_path("/api/v1/collections/123", "PATCH") is False
        assert should_track_path("/api/v1/collections/123", "DELETE") is False

    def test_should_skip_path_health(self):
        """Test that health checks are skipped."""
        from rest_api.middleware.usage import should_track_path

        assert should_track_path("/health", "GET") is False
        assert should_track_path("/health", "POST") is False

    def test_should_skip_path_auth(self):
        """Test that auth endpoints are skipped."""
        from rest_api.middleware.usage import should_track_path

        assert should_track_path("/api/v1/auth/register", "POST") is False
        assert should_track_path("/api/v1/auth/login", "POST") is False
        assert should_track_path("/api/v1/auth/refresh", "POST") is False

    def test_should_skip_path_admin(self):
        """Test that admin endpoints are skipped."""
        from rest_api.middleware.usage import should_track_path

        assert should_track_path("/api/v1/admin/users", "GET") is False
        assert should_track_path("/api/v1/admin/users/123", "DELETE") is False

    def test_should_skip_path_pat(self):
        """Test that PAT endpoints are skipped."""
        from rest_api.middleware.usage import should_track_path

        assert should_track_path("/api/v1/pat", "POST") is False
        assert should_track_path("/api/v1/pat/123", "DELETE") is False
