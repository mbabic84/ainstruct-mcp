"""Shared pytest configuration and fixtures for the workspace."""
import sys
from pathlib import Path
from typing import Any

import pytest

workspace_root = Path(__file__).parent.parent

sys.path.insert(0, str(workspace_root / "packages" / "shared" / "src"))
sys.path.insert(0, str(workspace_root / "services" / "mcp-server" / "src"))
sys.path.insert(0, str(workspace_root / "services" / "rest-api" / "src"))


@pytest.fixture
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock settings for testing."""
    monkeypatch.setenv("USE_MOCK_EMBEDDINGS", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")


@pytest.fixture
def mock_qdrant(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock Qdrant for testing."""
    monkeypatch.setenv("USE_MOCK_EMBEDDINGS", "true")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
    }


@pytest.fixture
def sample_collection_data() -> dict[str, Any]:
    """Sample collection data for testing."""
    return {
        "name": "Test Collection",
    }


@pytest.fixture
def sample_document_data() -> dict[str, Any]:
    """Sample document data for testing."""
    return {
        "title": "Test Document",
        "content": "# Test Content\n\nThis is test content.",
        "document_type": "markdown",
    }


@pytest.fixture
def sample_chunk_data() -> dict[str, Any]:
    """Sample chunk data for testing."""
    return {
        "content": "# Test Content\n\nThis is test content.",
        "token_count": 10,
        "title": "Test Document",
        "chunk_index": 0,
    }
