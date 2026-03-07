"""Tests for REST collections endpoints - get and list collections."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestGetCollectionEndpoint:
    """Test cases for GET /api/v1/collections/{collection_id} endpoint."""

    def test_get_collection_success(self, client, app):
        """Test successful collection retrieval."""
        pass

    def test_get_collection_not_found(self, client, app):
        """Test getting non-existent collection."""
        pass

    def test_get_collection_unauthorized(self, client):
        """Test getting collection without authentication."""
        pass


class TestListCollectionsEndpoint:
    """Test cases for GET /api/v1/collections endpoint."""

    def test_list_collections_success(self, client, app):
        """Test successful collection listing."""
        pass

    def test_list_collections_empty(self, client, app):
        """Test listing with no collections."""
        pass

    def test_list_collections_unauthorized(self, client):
        """Test listing collections without authentication."""
        pass
