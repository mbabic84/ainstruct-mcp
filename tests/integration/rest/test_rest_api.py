import pytest
from fastapi.testclient import TestClient

from app.rest.app import create_app
from app.rest.deps import get_current_user, CurrentUser
from app.db.models import Scope


@pytest.fixture
def mock_user():
    return CurrentUser(
        user_id="test-user-id",
        username="testuser",
        email="test@example.com",
        is_superuser=False,
        scopes=[Scope.READ, Scope.WRITE],
    )


@pytest.fixture
def mock_admin():
    return CurrentUser(
        user_id="admin-user-id",
        username="admin",
        email="admin@example.com",
        is_superuser=True,
        scopes=[Scope.READ, Scope.WRITE, Scope.ADMIN],
    )


@pytest.fixture
def client(mock_user):
    app = create_app()
    
    def override_get_current_user():
        return mock_user
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(mock_admin):
    app = create_app()
    
    def override_get_current_user():
        return mock_admin
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()


class TestAuthEndpoints:
    def test_get_profile(self, client):
        response = client.get("/api/v1/auth/profile")
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"


class TestAdminEndpoints:
    def test_list_users_as_non_admin(self, client):
        response = client.get("/api/v1/admin/users")
        
        assert response.status_code == 403


class TestHealthEndpoint:
    def test_health_check(self):
        app = create_app()
        with TestClient(app) as client:
            response = client.get("/health")
            
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
