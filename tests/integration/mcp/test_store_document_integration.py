"""Integration tests for store_document_tool with CAT and PAT tokens."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_server.tools.context import (
    clear_cat_info,
    clear_pat_info,
    set_cat_info,
    set_pat_collections,
    set_pat_info,
)
from mcp_server.tools.document_tools import StoreDocumentInput, store_document


class TestStoreDocumentWithRealServices:
    """Test store_document with real service mocking."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        clear_cat_info()
        clear_pat_info()
        yield
        clear_cat_info()
        clear_pat_info()

    @pytest.fixture
    def mock_pat_info(self):
        """Mock PAT token info for testing."""
        return {
            "id": "test-pat",
            "user_id": "368e3dcf-1aac-4cfc-9a3c-990f9e80d3d8",
            "collection_ids": ["647a8ef8-6c09-4653-9fd1-eec82cef5775"],
            "qdrant_collections": ["43dc7b04-5aaf-4420-baa9-dc9cf41b35f4"],
            "scopes": ["read", "write"],
            "is_admin": False,
            "auth_type": "pat",
        }

    @pytest.fixture
    def mock_cat_info(self):
        """Mock CAT token info for testing."""
        return {
            "id": "test-cat",
            "user_id": "368e3dcf-1aac-4cfc-9a3c-990f9e80d3d8",
            "collection_id": "647a8ef8-6c09-4653-9fd1-eec82cef5775",
            "collection_name": "Test Collection",
            "qdrant_collection": "43dc7b04-5aaf-4420-baa9-dc9cf41b35f4",
            "permission": "read_write",
            "is_admin": False,
        }

    @pytest.mark.asyncio
    async def test_store_document_with_pat_token(self, mock_pat_info):
        """Test that store_document works with PAT token authentication."""
        set_pat_info(mock_pat_info)
        set_pat_collections(
            [
                {
                    "id": "647a8ef8-6c09-4653-9fd1-eec82cef5775",
                    "qdrant_collection": "43dc7b04-5aaf-4420-baa9-dc9cf41b35f4",
                }
            ]
        )

        mock_doc_repo = MagicMock()
        mock_doc_repo.create = AsyncMock(
            return_value=MagicMock(
                id="doc-new-123",
                collection_id=mock_pat_info["collection_ids"][0],
            )
        )
        mock_doc_repo.update_qdrant_point_ids = AsyncMock()

        mock_qdrant = MagicMock()
        mock_qdrant.collection_name = mock_pat_info["qdrant_collections"][0]
        mock_qdrant.upsert_chunks = AsyncMock(return_value=["point-1"])

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_texts = AsyncMock(return_value=[[0.1] * 4096])

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

            assert result.document_id == "doc-new-123"
            mock_qdrant.upsert_chunks.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_document_with_cat_token(self, mock_cat_info):
        """Test that store_document works with CAT token authentication."""
        set_cat_info(mock_cat_info)

        mock_doc_repo = MagicMock()
        mock_doc_repo.create = AsyncMock(
            return_value=MagicMock(
                id="doc-new-456",
                collection_id=mock_cat_info["collection_id"],
            )
        )
        mock_doc_repo.update_qdrant_point_ids = AsyncMock()

        mock_qdrant = MagicMock()
        mock_qdrant.collection_name = mock_cat_info["qdrant_collection"]
        mock_qdrant.upsert_chunks = AsyncMock(return_value=["point-1"])

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_texts = AsyncMock(return_value=[[0.1] * 4096])

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
                    title="Test Doc CAT",
                    content="# Test Content CAT\n\nThis is test content via CAT.",
                )
            )

            assert result.document_id == "doc-new-456"
            mock_qdrant.upsert_chunks.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_document_with_pat_specifies_collection(self, mock_pat_info):
        """Test that store_document uses specified collection_id with PAT."""
        set_pat_info(mock_pat_info)
        set_pat_collections(
            [
                {
                    "id": "specific-collection",
                    "qdrant_collection": "43dc7b04-5aaf-4420-baa9-dc9cf41b35f4",
                }
            ]
        )

        mock_doc_repo = MagicMock()
        mock_doc_repo.create = AsyncMock(
            return_value=MagicMock(id="doc-col-789", collection_id="specific-collection")
        )
        mock_doc_repo.update_qdrant_point_ids = AsyncMock()

        mock_qdrant = MagicMock()
        mock_qdrant.upsert_chunks = AsyncMock(return_value=["point-1"])

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_texts = AsyncMock(return_value=[[0.1] * 4096])

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

        captured_collection_name = None

        def capture_qdrant(collection_name, is_admin=False):
            nonlocal captured_collection_name
            captured_collection_name = collection_name
            return mock_qdrant

        with (
            patch(
                "mcp_server.tools.document_tools.get_document_repository",
                return_value=mock_doc_repo,
            ),
            patch(
                "mcp_server.tools.document_tools.get_qdrant_service",
                side_effect=capture_qdrant,
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
                    collection_id="specific-collection",
                )
            )

            assert captured_collection_name == "43dc7b04-5aaf-4420-baa9-dc9cf41b35f4"
