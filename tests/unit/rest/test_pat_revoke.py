"""Tests for REST PAT endpoints - revoke PAT."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestRevokePatEndpoint:
    """Test cases for DELETE /api/v1/pat/{key_id} endpoint."""

    def test_revoke_pat_success(self, client, app):
        """Test successful PAT token revocation."""
        pass

    def test_revoke_pat_not_found(self, client, app):
        """Test revoking non-existent PAT token."""
        pass

    def test_revoke_pat_other_users_token(self, client, app):
        """Test revoking another user's PAT token."""
        pass

    def test_revoke_pat_unauthorized(self, client):
        """Test revoking PAT without authentication."""
        pass
