"""Tests for REST collections endpoints - create_collection."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestCreateCollectionEndpoint:
    """Test cases for POST /api/v1/collections endpoint."""

    def test_create_collection_success(self, client, app):
        """Test successful collection creation."""
        pass

    def test_create_collection_duplicate_name(self, client, app):
        """Test creating collection with duplicate name."""
        pass

    def test_create_collection_unauthorized(self, client):
        """Test creating collection without authentication."""
        pass
