"""Tests for REST auth endpoints - login."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestLoginEndpoint:
    """Test cases for POST /api/v1/auth/login endpoint."""

    def test_login_success(self, client, app):
        """Test successful login."""
        pass

    def test_login_invalid_credentials(self, client, app):
        """Test login with invalid credentials."""
        pass

    def test_login_disabled_user(self, client, app):
        """Test login with disabled user account."""
        pass
