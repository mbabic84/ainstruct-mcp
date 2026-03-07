"""Tests for delete_document MCP tool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_server.tools.context import clear_cat_info, set_cat_info
from mcp_server.tools.document_tools import (
    DeleteDocumentInput,
    delete_document,
)


class TestDeleteDocument:
    """Test cases for delete_document function."""

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
    async def test_delete_document_uses_document_id(self, mock_cat_info):
        """Test that delete_document uses document_id for lookups."""
        set_cat_info(mock_cat_info)

        mock_doc_repo = MagicMock()
        mock_doc_repo.get_by_id = AsyncMock(
            return_value=MagicMock(
                document_id="doc-123",
                collection_id="27241155-eaae-4678-a69f-c8003512f1fe",
            )
        )
        mock_doc_repo.delete = AsyncMock()

        mock_qdrant = MagicMock()
        mock_qdrant.delete_by_document_id = AsyncMock()

        with (
            patch(
                "mcp_server.tools.document_tools.get_document_repository",
                return_value=mock_doc_repo,
            ),
            patch(
                "mcp_server.tools.document_tools.get_qdrant_service",
                return_value=mock_qdrant,
            ),
        ):
            result = await delete_document(DeleteDocumentInput(document_id="doc-123"))

            assert result.success is True
            mock_qdrant.delete_by_document_id.assert_called_once_with("doc-123")
            mock_doc_repo.delete.assert_called_once_with("doc-123")
