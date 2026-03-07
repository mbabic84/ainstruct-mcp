"""Tests for REST CAT endpoints - create CAT."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestCreateCatEndpoint:
    """Test cases for POST /api/v1/cat endpoint."""

    def test_create_cat_success(self, client, app):
        """Test successful CAT token creation."""
        pass

    def test_create_cat_collection_not_found(self, client, app):
        """Test creating CAT for non-existent collection."""
        pass

    def test_create_cat_unauthorized(self, client):
        """Test creating CAT without authentication."""
        pass
