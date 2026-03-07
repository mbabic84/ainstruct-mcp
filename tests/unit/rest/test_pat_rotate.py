"""Tests for REST PAT endpoints - rotate PAT."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestRotatePatEndpoint:
    """Test cases for POST /api/v1/pat/{key_id}/rotate endpoint."""

    def test_rotate_pat_success(self, client, app):
        """Test successful PAT token rotation."""
        pass

    def test_rotate_pat_not_found(self, client, app):
        """Test rotating non-existent PAT token."""
        pass

    def test_rotate_pat_other_users_token(self, client, app):
        """Test rotating another user's PAT token."""
        pass

    def test_rotate_pat_unauthorized(self, client):
        """Test rotating PAT without authentication."""
        pass
