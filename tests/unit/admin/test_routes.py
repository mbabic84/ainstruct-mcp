"""Tests for admin routes."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app
from rest_api.deps import CurrentUser, get_current_user
from shared.db.models import Scope


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def admin_user():
    return CurrentUser(
        user_id="admin-123",
        username="admin",
        email="admin@example.com",
        is_superuser=True,
        scopes=[Scope.ADMIN],
    )


@pytest.fixture
def regular_user():
    return CurrentUser(
        user_id="user-123",
        username="testuser",
        email="test@example.com",
        is_superuser=False,
        scopes=[Scope.READ, Scope.WRITE],
    )


class TestSearchUsers:
    """Test cases for search_users endpoint."""

    def test_search_users_success_username(self, client, app, admin_user):
        """Test successful search by username."""
        mock_user = type(
            "User",
            (),
            {
                "id": "user-123",
                "email": "test@example.com",
                "username": "testuser",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2024-01-01T00:00:00",
            },
        )()

        app.dependency_overrides[get_current_user] = lambda: admin_user

        with patch("rest_api.routes.admin.get_user_repository") as mock_repo:
            mock_repository = AsyncMock()
            mock_repository.search = AsyncMock(return_value=[mock_user])
            mock_repo.return_value = mock_repository

            response = client.get(
                "/api/v1/admin/users/search?query=testuser",
            )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) == 1
        assert data["users"][0]["username"] == "testuser"

        app.dependency_overrides.clear()

    def test_search_users_success_email(self, client, app, admin_user):
        """Test successful search by email."""
        mock_user = type(
            "User",
            (),
            {
                "id": "user-456",
                "email": "search@example.com",
                "username": "searchuser",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2024-01-01T00:00:00",
            },
        )()

        app.dependency_overrides[get_current_user] = lambda: admin_user

        with patch("rest_api.routes.admin.get_user_repository") as mock_repo:
            mock_repository = AsyncMock()
            mock_repository.search = AsyncMock(return_value=[mock_user])
            mock_repo.return_value = mock_repository

            response = client.get(
                "/api/v1/admin/users/search?query=example.com",
            )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) == 1
        assert data["users"][0]["email"] == "search@example.com"

        app.dependency_overrides.clear()

    def test_search_users_empty_results(self, client, app, admin_user):
        """Test empty results for non-matching query."""
        app.dependency_overrides[get_current_user] = lambda: admin_user

        with patch("rest_api.routes.admin.get_user_repository") as mock_repo:
            mock_repository = AsyncMock()
            mock_repository.search = AsyncMock(return_value=[])
            mock_repo.return_value = mock_repository

            response = client.get(
                "/api/v1/admin/users/search?query=nonexistent",
            )

        assert response.status_code == 200
        data = response.json()
        assert data["users"] == []
        assert data["total"] == 0

        app.dependency_overrides.clear()

    def test_search_users_unauthorized(self, client, app, regular_user):
        """Test unauthorized access returns 403."""
        app.dependency_overrides[get_current_user] = lambda: regular_user

        response = client.get(
            "/api/v1/admin/users/search?query=test",
        )

        assert response.status_code == 403
        app.dependency_overrides.clear()

    def test_search_users_missing_query(self, client, app, admin_user):
        """Test missing query parameter returns 422."""
        app.dependency_overrides[get_current_user] = lambda: admin_user

        response = client.get(
            "/api/v1/admin/users/search",
        )

        assert response.status_code == 422
        app.dependency_overrides.clear()


class TestPromoteUser:
    """Test cases for promote_user endpoint."""

    def test_promote_user_success(self, app, client):
        """Test successful user promotion."""
        mock_user = type(
            "User",
            (),
            {
                "id": "user-123",
                "email": "test@example.com",
                "username": "testuser",
                "is_active": True,
                "is_superuser": True,
                "created_at": "2024-01-01T00:00:00",
            },
        )()

        with patch("rest_api.routes.admin.get_user_repository") as mock_repo:
            mock_repository = AsyncMock()
            mock_repository.count_superusers = AsyncMock(return_value=0)
            mock_repository.get_by_id = AsyncMock(return_value=mock_user)
            mock_repository.update = AsyncMock(return_value=True)
            mock_repo.return_value = mock_repository

            with patch("rest_api.deps.settings") as mock_settings:
                mock_settings.admin_api_key = "test-admin-key"

                response = client.post(
                    "/api/v1/admin/users/user-123/promote",
                    headers={"X-Admin-API-Key": "test-admin-key"},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["is_superuser"] is True

    def test_promote_user_invalid_api_key(self, app, client):
        """Test invalid admin API key returns 401."""
        with patch("rest_api.routes.admin.get_user_repository"):
            with patch("rest_api.deps.settings") as mock_settings:
                mock_settings.admin_api_key = "test-admin-key"

                response = client.post(
                    "/api/v1/admin/users/user-123/promote",
                    headers={"X-Admin-API-Key": "wrong-key"},
                )

        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "INVALID_ADMIN_API_KEY"

    def test_promote_user_missing_api_key(self, app, client):
        """Test missing admin API key header returns 422."""
        response = client.post(
            "/api/v1/admin/users/user-123/promote",
        )

        assert response.status_code == 422

    def test_promote_user_not_found(self, app, client):
        """Test non-existent user returns 404."""
        with patch("rest_api.routes.admin.get_user_repository") as mock_repo:
            mock_repository = AsyncMock()
            mock_repository.count_superusers = AsyncMock(return_value=0)
            mock_repository.get_by_id = AsyncMock(return_value=None)
            mock_repo.return_value = mock_repository

            with patch("rest_api.deps.settings") as mock_settings:
                mock_settings.admin_api_key = "test-admin-key"

                response = client.post(
                    "/api/v1/admin/users/nonexistent/promote",
                    headers={"X-Admin-API-Key": "test-admin-key"},
                )

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "USER_NOT_FOUND"

    def test_promote_user_api_key_not_configured(self, app, client):
        """Test admin API key not configured returns 503."""
        with patch("rest_api.routes.admin.get_user_repository"):
            with patch("rest_api.deps.settings") as mock_settings:
                mock_settings.admin_api_key = ""

                response = client.post(
                    "/api/v1/admin/users/user-123/promote",
                    headers={"X-Admin-API-Key": "any-key"},
                )

        assert response.status_code == 503
        assert response.json()["detail"]["code"] == "ADMIN_API_KEY_NOT_CONFIGURED"

    def test_promote_user_admin_already_exists(self, app, client):
        """Test promote fails when admin already exists."""
        with patch("rest_api.routes.admin.get_user_repository") as mock_repo:
            mock_repository = AsyncMock()
            mock_repository.count_superusers = AsyncMock(return_value=1)
            mock_repo.return_value = mock_repository

            with patch("rest_api.deps.settings") as mock_settings:
                mock_settings.admin_api_key = "test-admin-key"

                response = client.post(
                    "/api/v1/admin/users/user-123/promote",
                    headers={"X-Admin-API-Key": "test-admin-key"},
                )

        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "ADMIN_EXISTS"
