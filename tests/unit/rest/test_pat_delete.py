"""Tests for REST PAT endpoints - permanent delete PAT."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestDeletePatEndpoint:
    """Test cases for POST /api/v1/auth/pat/{key_id}/delete endpoint."""

    def test_delete_pat_success(self, client, app):
        """Test successful PAT token permanent deletion."""
        pass

    def test_delete_pat_not_found(self, client, app):
        """Test deleting non-existent PAT token."""
        pass

    def test_delete_pat_other_users_token(self, client, app):
        """Test deleting another user's PAT token."""
        pass

    def test_delete_pat_unauthorized(self, client):
        """Test deleting PAT without authentication."""
        pass
