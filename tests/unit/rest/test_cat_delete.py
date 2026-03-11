"""Tests for REST CAT endpoints - permanent delete CAT."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestDeleteCatEndpoint:
    """Test cases for POST /api/v1/auth/cat/{key_id}/delete endpoint."""

    def test_delete_cat_success(self, client, app):
        """Test successful CAT token permanent deletion."""
        pass

    def test_delete_cat_not_found(self, client, app):
        """Test deleting non-existent CAT token."""
        pass

    def test_delete_cat_other_users_token(self, client, app):
        """Test deleting another user's CAT token."""
        pass

    def test_delete_cat_unauthorized(self, client):
        """Test deleting CAT without authentication."""
        pass
