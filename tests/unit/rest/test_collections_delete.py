"""Tests for REST collections endpoints - delete_collection."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestDeleteCollectionEndpoint:
    """Test cases for DELETE /api/v1/collections/{collection_id} endpoint."""

    def test_delete_collection_success(self, client, app):
        """Test successful collection deletion."""
        pass

    def test_delete_collection_with_cats_fails(self, client, app):
        """Test deleting collection with active CAT tokens."""
        pass

    def test_delete_collection_not_found(self, client, app):
        """Test deleting non-existent collection."""
        pass

    def test_delete_collection_unauthorized(self, client):
        """Test deleting collection without authentication."""
        pass
