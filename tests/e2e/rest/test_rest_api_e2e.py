import os
import pytest
import httpx


BASE_URL = os.getenv("MCP_SERVER_BASE_URL", "http://rest_api:8000")


@pytest.fixture(scope="module")
def rest_client():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        yield client


class TestHealthEndpoint:
    def test_health_check(self, rest_client):
        response = rest_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAuthEndpoints:
    def test_register_duplicate_username(self, rest_client):
        response = rest_client.post("/api/v1/auth/register", json={
            "email": "another@example.com",
            "username": "e2euser",
            "password": "password123",
        })
        assert response.status_code == 400
        assert "USERNAME_EXISTS" in response.json()["detail"]["code"]

    def test_login_invalid_credentials(self, rest_client):
        response = rest_client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpass",
        })
        assert response.status_code == 401
        assert "INVALID_CREDENTIALS" in response.json()["detail"]["code"]
