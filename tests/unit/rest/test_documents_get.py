"""Tests for REST documents endpoints - get_document."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestGetDocumentEndpoint:
    """Test cases for GET /api/v1/documents/{document_id} endpoint."""

    def test_get_document_success(self, client, app):
        """Test successful document retrieval."""
        pass

    def test_get_document_not_found(self, client, app):
        """Test getting non-existent document."""
        pass

    def test_get_document_unauthorized(self, client):
        """Test getting document without authentication."""
        pass
