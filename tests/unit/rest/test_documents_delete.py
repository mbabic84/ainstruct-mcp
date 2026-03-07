"""Tests for REST documents endpoints - delete_document."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestDeleteDocumentEndpoint:
    """Test cases for DELETE /api/v1/documents/{document_id} endpoint."""

    def test_delete_document_success(self, client, app):
        """Test successful document deletion."""
        pass

    def test_delete_document_not_found(self, client, app):
        """Test deleting non-existent document."""
        pass

    def test_delete_document_unauthorized(self, client):
        """Test deleting document without authentication."""
        pass
