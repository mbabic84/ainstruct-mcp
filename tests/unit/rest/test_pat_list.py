"""Tests for REST PAT endpoints - list PATs."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestListPatEndpoint:
    """Test cases for GET /api/v1/pat endpoint."""

    def test_list_pat_success(self, client, app):
        """Test successful PAT token listing."""
        pass

    def test_list_pat_empty(self, client, app):
        """Test listing with no PAT tokens."""
        pass

    def test_list_pat_unauthorized(self, client):
        """Test listing PATs without authentication."""
        pass
