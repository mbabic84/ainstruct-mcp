"""Tests for REST API module."""


class TestRestApi:
    """Test cases for REST API module."""

    def test_rest_api_imports(self):
        """Test that REST API module imports correctly."""
        from rest_api import main
        assert main is not None

    def test_create_app(self):
        """Test that create_app works."""
        from rest_api.app import create_app

        app = create_app()
        assert app is not None
        assert app.title == "ainstruct API"

    def test_app_has_routes(self):
        """Test that app has routes registered."""
        from rest_api.app import create_app

        app = create_app()

        # Check routes exist
        routes = [r.path for r in app.routes]

        assert any("/health" in r for r in routes)
        assert any("/auth/register" in r for r in routes)
        assert any("/auth/login" in r for r in routes)

    def test_health_endpoint(self):
        """Test health endpoint."""
        from fastapi.testclient import TestClient
        from rest_api.app import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestRestApiDeps:
    """Test cases for REST API dependencies."""

    def test_security_imports(self):
        """Test that security imports work."""
        from rest_api.deps import security
        assert security is not None

    def test_current_user_class(self):
        """Test CurrentUser class."""
        from rest_api.deps import CurrentUser
        from shared.db.models import Scope

        user = CurrentUser(
            user_id="user-123",
            username="testuser",
            email="test@example.com",
            is_superuser=False,
            scopes=[Scope.READ, Scope.WRITE],
        )

        assert user.user_id == "user-123"
        assert user.username == "testuser"
        assert user.is_superuser is False
        assert Scope.WRITE in user.scopes
