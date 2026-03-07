"""Tests for REST collections endpoints - rename_collection."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestRenameCollectionEndpoint:
    """Test cases for PUT /api/v1/collections/{collection_id} endpoint."""

    def test_rename_collection_success(self, client, app):
        """Test successful collection rename."""
        pass

    def test_rename_collection_duplicate_name(self, client, app):
        """Test renaming to existing collection name."""
        pass

    def test_rename_collection_not_found(self, client, app):
        """Test renaming non-existent collection."""
        pass

    def test_rename_collection_unauthorized(self, client):
        """Test renaming collection without authentication."""
        pass
