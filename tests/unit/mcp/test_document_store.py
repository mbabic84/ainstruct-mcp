"""Tests for store_document MCP tool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_server.tools.context import clear_cat_info, set_cat_info
from mcp_server.tools.document_tools import (
    StoreDocumentInput,
    store_document,
)
from shared.constants import DocumentType


class TestStoreDocumentWithCatToken:
    """Test cases for store_document with CAT token authentication."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        clear_cat_info()
        yield
        clear_cat_info()

    @pytest.fixture
    def mock_cat_info(self):
        """Mock CAT token info for testing."""
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
    async def test_store_document_with_cat_token(self, mock_cat_info, monkeypatch):
        """Test that store_document correctly uses qdrant_collection for CAT tokens."""
        set_cat_info(mock_cat_info)

        mock_doc_repo = MagicMock()
        mock_doc_repo.create = AsyncMock(
            return_value=MagicMock(
                document_id="doc-123",
                collection_id=mock_cat_info["collection_id"],
            )
        )
        mock_doc_repo.update_qdrant_point_ids = AsyncMock()

        mock_qdrant = MagicMock()
        mock_qdrant.collection_name = mock_cat_info["qdrant_collection"]
        mock_qdrant.upsert_chunks = AsyncMock(return_value=["point-1"])

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_texts = AsyncMock(return_value=[[0.1] * 384])

        mock_chunking_service = MagicMock()
        mock_chunking_service.chunk_markdown = MagicMock(
            return_value=[
                {
                    "content": "Test content",
                    "chunk_index": 0,
                    "token_count": 10,
                    "title": "Test Doc",
                }
            ]
        )

        with (
            patch(
                "mcp_server.tools.document_tools.get_document_repository",
                return_value=mock_doc_repo,
            ),
            patch(
                "mcp_server.tools.document_tools.get_qdrant_service",
                return_value=mock_qdrant,
            ),
            patch(
                "mcp_server.tools.document_tools.get_embedding_service",
                return_value=mock_embedding_service,
            ),
            patch(
                "mcp_server.tools.document_tools.get_chunking_service",
                return_value=mock_chunking_service,
            ),
        ):
            result = await store_document(
                StoreDocumentInput(
                    title="Test Doc",
                    content="# Test Content\n\nThis is test content.",
                )
            )

            assert result.document_id == "doc-123"

    @pytest.mark.asyncio
    async def test_store_document_cat_token_uses_correct_collection_name(
        self, mock_cat_info, monkeypatch
    ):
        """Test that CAT token's qdrant_collection (not collection_id) is passed to Qdrant."""
        set_cat_info(mock_cat_info)

        captured_collection_name = None

        def capture_qdrant_service(collection_name, is_admin=False):
            nonlocal captured_collection_name
            captured_collection_name = collection_name
            mock_qdrant = MagicMock()
            mock_qdrant.collection_name = collection_name
            mock_qdrant.upsert_chunks = AsyncMock(return_value=["point-1"])
            return mock_qdrant

        mock_doc_repo = MagicMock()
        mock_doc_repo.create = AsyncMock(
            return_value=MagicMock(
                document_id="doc-123",
                collection_id=mock_cat_info["collection_id"],
            )
        )
        mock_doc_repo.update_qdrant_point_ids = AsyncMock()

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_texts = AsyncMock(return_value=[[0.1] * 384])

        mock_chunking_service = MagicMock()
        mock_chunking_service.chunk_markdown = MagicMock(
            return_value=[
                {
                    "content": "Test content",
                    "chunk_index": 0,
                    "token_count": 10,
                    "title": "Test Doc",
                }
            ]
        )

        with (
            patch(
                "mcp_server.tools.document_tools.get_document_repository",
                return_value=mock_doc_repo,
            ),
            patch(
                "mcp_server.tools.document_tools.get_qdrant_service",
                side_effect=capture_qdrant_service,
            ),
            patch(
                "mcp_server.tools.document_tools.get_embedding_service",
                return_value=mock_embedding_service,
            ),
            patch(
                "mcp_server.tools.document_tools.get_chunking_service",
                return_value=mock_chunking_service,
            ),
        ):
            await store_document(
                StoreDocumentInput(
                    title="Test Doc",
                    content="# Test Content",
                )
            )

            assert captured_collection_name == "docs_abc123def456"
            assert captured_collection_name != mock_cat_info["collection_id"]


class TestDocumentTypeValidation:
    """Test cases for document_type validation in StoreDocumentInput."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        clear_cat_info()
        yield
        clear_cat_info()

    def test_store_document_input_valid_types(self):
        """Test that StoreDocumentInput accepts all valid document types."""
        valid_types = DocumentType.get_codemirror_types()

        for doc_type in valid_types:
            input_data = StoreDocumentInput(
                title="Test",
                content="Test content",
                document_type=doc_type,
            )
            assert input_data.document_type == doc_type

    def test_store_document_input_default_is_markdown(self):
        """Test that StoreDocumentInput defaults to markdown."""
        input_data = StoreDocumentInput(
            title="Test",
            content="Test content",
        )
        assert input_data.document_type == "markdown"

    def test_store_document_input_invalid_type_raises_error(self):
        """Test that StoreDocumentInput raises error for invalid document types."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            StoreDocumentInput(
                title="Test",
                content="Test content",
                document_type="pdf",
            )

        assert "Invalid document_type" in str(exc_info.value)
