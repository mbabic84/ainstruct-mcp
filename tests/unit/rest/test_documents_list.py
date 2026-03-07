"""Tests for REST documents endpoints - list_documents."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestListDocumentsEndpoint:
    """Test cases for GET /api/v1/documents endpoint."""

    def test_list_documents_success(self, client, app):
        """Test successful document listing."""
        pass

    def test_list_documents_with_pagination(self, client, app):
        """Test document listing with pagination."""
        pass

    def test_list_documents_filter_by_collection(self, client, app):
        """Test listing documents filtered by collection."""
        pass

    def test_list_documents_unauthorized(self, client):
        """Test listing documents without authentication."""
        pass
