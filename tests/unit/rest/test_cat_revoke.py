"""Tests for REST CAT endpoints - revoke CAT."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestRevokeCatEndpoint:
    """Test cases for DELETE /api/v1/cat/{key_id} endpoint."""

    def test_revoke_cat_success(self, client, app):
        """Test successful CAT token revocation."""
        pass

    def test_revoke_cat_not_found(self, client, app):
        """Test revoking non-existent CAT token."""
        pass

    def test_revoke_cat_other_users_token(self, client, app):
        """Test revoking another user's CAT token."""
        pass

    def test_revoke_cat_unauthorized(self, client):
        """Test revoking CAT without authentication."""
        pass
