"""Tests for REST PAT endpoints - create PAT."""

import pytest
from fastapi.testclient import TestClient
from rest_api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestCreatePatEndpoint:
    """Test cases for POST /api/v1/pat endpoint."""

    def test_create_pat_success(self, client, app):
        """Test successful PAT token creation."""
        pass

    def test_create_pat_unauthorized(self, client):
        """Test creating PAT without authentication."""
        pass
