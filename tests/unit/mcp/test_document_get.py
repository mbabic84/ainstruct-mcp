"""Tests for get_document MCP tool."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_server.tools.context import clear_cat_info, set_cat_info
from mcp_server.tools.document_tools import (
    GetDocumentInput,
    get_document,
)


class TestGetDocument:
    """Test cases for get_document function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        clear_cat_info()
        yield
        clear_cat_info()

    @pytest.fixture
    def mock_cat_info(self):
        return {
            "id": "cat-123",
            "user_id": "user-456",
            "collection_id": "27241155-eaae-4678-a69f-c8003512f1fe",
            "collection_name": "My Collection",
            "qdrant_collection": "docs_abc123def456",
            "permission": "read_write",
            "is_admin": False,
        }

    @pytest.mark.asyncio
    async def test_get_document_returns_document_id(self, mock_cat_info):
        """Test that get_document returns document_id field, not id."""
        set_cat_info(mock_cat_info)

        mock_doc_repo = MagicMock()
        mock_doc_repo.get_by_id = AsyncMock(
            return_value=MagicMock(
                document_id="doc-123",
                collection_id="27241155-eaae-4678-a69f-c8003512f1fe",
                title="Test Doc",
                content="Test content",
                document_type="markdown",
                created_at=datetime(2024, 1, 1, 0, 0, 0),
                updated_at=datetime(2024, 1, 1, 0, 0, 0),
                doc_metadata={},
            )
        )

        with patch(
            "mcp_server.tools.document_tools.get_document_repository",
            return_value=mock_doc_repo,
        ):
            result = await get_document(GetDocumentInput(document_id="doc-123"))

            assert result is not None
            assert result.document_id == "doc-123"
