"""Tests for REST CAT endpoints - list CATs."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestListCatsEndpoint:
    """Test cases for GET /api/v1/cat endpoint."""

    def test_list_cats_success(self, client, app):
        """Test successful CAT token listing."""
        pass

    def test_list_cats_empty(self, client, app):
        """Test listing with no CAT tokens."""
        pass

    def test_list_cats_unauthorized(self, client):
        """Test listing CATs without authentication."""
        pass
