"""Tests for document tools with CAT token authentication."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_server.tools.context import clear_cat_info, set_cat_info
from mcp_server.tools.document_tools import (
    MoveDocumentInput,
    StoreDocumentInput,
    move_document,
    store_document,
)


class TestStoreDocumentWithCatToken:
    """Test cases for store_document with CAT token authentication."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        # Clear CAT info before and after each test
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
        # Set up CAT auth context
        set_cat_info(mock_cat_info)

        # Mock dependencies - all need AsyncMock for async methods
        mock_doc_repo = MagicMock()
        mock_doc_repo.create = AsyncMock(
            return_value=MagicMock(
                id="doc-123",
                collection_id=mock_cat_info["collection_id"],
            )
        )
        mock_doc_repo.update_qdrant_point_ids = AsyncMock()

        # Create async mock for qdrant service
        mock_qdrant = MagicMock()
        mock_qdrant.collection_name = mock_cat_info["qdrant_collection"]
        mock_qdrant.upsert_chunks = AsyncMock(return_value=["point-1"])

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_texts = AsyncMock(
            return_value=[[0.1] * 384]  # Mock embeddings
        )

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

            # Verify the document was created
            assert result.document_id == "doc-123"

    @pytest.mark.asyncio
    async def test_store_document_cat_token_uses_correct_collection_name(
        self, mock_cat_info, monkeypatch
    ):
        """Test that CAT token's qdrant_collection (not collection_id) is passed to Qdrant."""
        set_cat_info(mock_cat_info)

        # Track what collection name is passed to get_qdrant_service
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
                id="doc-123",
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

            # The key assertion: qdrant_collection name (e.g., "docs_abc123def456")
            # should be passed, NOT the collection_id UUID
            assert captured_collection_name == "docs_abc123def456"
            assert captured_collection_name != mock_cat_info["collection_id"]


class TestMoveDocumentWithCatToken:
    """Test cases for move_document - verifies the fix for using qdrant_collection names."""

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
            "collection_id": "source-collection-id",
            "collection_name": "Source Collection",
            "qdrant_collection": "docs_source123",
            "permission": "read_write",
            "is_admin": False,
        }

    @pytest.mark.asyncio
    async def test_move_document_uses_qdrant_collection_name_not_id(
        self, mock_cat_info, monkeypatch
    ):
        """Test that move_document uses qdrant_collection names, not collection_id UUIDs."""
        set_cat_info(mock_cat_info)

        # Track calls to get_collection_repository
        collection_lookups = []

        def mock_get_collection_repository():
            # Create a mock that tracks lookups
            mock_repo = MagicMock()

            async def mock_get_by_id(collection_id):
                collection_lookups.append(collection_id)
                if collection_id == "source-collection-id":
                    return {"id": "source-collection-id", "qdrant_collection": "docs_source123"}
                elif collection_id == "target-collection-id":
                    return {"id": "target-collection-id", "qdrant_collection": "docs_target456"}
                return None

            mock_repo.get_by_id = mock_get_by_id
            return mock_repo

        captured_collections = []

        def capture_qdrant_service(collection_name, is_admin=False):
            captured_collections.append(collection_name)
            mock_qdrant = MagicMock()
            mock_qdrant.delete_by_document_id = AsyncMock()
            mock_qdrant.upsert_chunks = AsyncMock(return_value=["point-1"])
            return mock_qdrant

        # Mock document repository
        mock_doc_repo = MagicMock()
        mock_doc_repo.get_by_id = AsyncMock(
            return_value=MagicMock(
                id="doc-123",
                collection_id="source-collection-id",
                title="Test Doc",
                content="# Test Content",
            )
        )
        mock_doc_repo.update_collection_id = AsyncMock()
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
                "mcp_server.tools.document_tools.get_collection_repository",
                mock_get_collection_repository,
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
            await move_document(
                MoveDocumentInput(
                    document_id="doc-123",
                    target_collection_id="target-collection-id",
                )
            )

            # Verify the lookups happened in correct order
            assert collection_lookups[0] == "target-collection-id"
            assert collection_lookups[1] == "source-collection-id"

            # Verify that qdrant_collection names were used, not collection_id UUIDs
            # First qdrant call is for source (delete), second is for target (upsert)
            assert captured_collections[0] == "docs_source123"  # Source (delete)
            assert captured_collections[0] != "source-collection-id"

            assert captured_collections[1] == "docs_target456"  # Target (upsert)
            assert captured_collections[1] != "target-collection-id"
