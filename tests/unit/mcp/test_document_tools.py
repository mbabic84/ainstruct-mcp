"""Tests for document tools with CAT token authentication."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_server.tools.context import (
    clear_all_auth,
    clear_cat_info,
    set_cat_info,
    set_user_collections,
    set_user_info,
)
from mcp_server.tools.document_tools import (
    DeleteDocumentInput,
    GetDocumentInput,
    ListDocumentsInput,
    MoveDocumentInput,
    StoreDocumentInput,
    delete_document,
    get_document,
    list_documents,
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
                document_id="doc-123",
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
                    return {
                        "collection_id": "source-collection-id",
                        "qdrant_collection": "docs_source123",
                        "user_id": "user-456",
                    }
                elif collection_id == "target-collection-id":
                    return {
                        "collection_id": "target-collection-id",
                        "qdrant_collection": "docs_target456",
                        "user_id": "user-456",
                    }
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
                document_id="doc-123",
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


class TestListDocuments:
    """Test cases for list_documents function."""

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
    async def test_list_documents_returns_document_id(self, mock_cat_info):
        """Test that list_documents returns document_id field, not id."""
        set_cat_info(mock_cat_info)

        mock_doc_repo = MagicMock()
        mock_doc_repo.list_all = AsyncMock(
            return_value=[
                MagicMock(
                    document_id="doc-123",
                    collection_id="27241155-eaae-4678-a69f-c8003512f1fe",
                    title="Test Doc 1",
                    content="Content 1",
                    document_type="markdown",
                    created_at=datetime(2024, 1, 1, 0, 0, 0),
                    updated_at=datetime(2024, 1, 1, 0, 0, 0),
                    doc_metadata={},
                ),
                MagicMock(
                    document_id="doc-456",
                    collection_id="27241155-eaae-4678-a69f-c8003512f1fe",
                    title="Test Doc 2",
                    content="Content 2",
                    document_type="markdown",
                    created_at=datetime(2024, 1, 2, 0, 0, 0),
                    updated_at=datetime(2024, 1, 2, 0, 0, 0),
                    doc_metadata={},
                ),
            ]
        )
        mock_doc_repo.count_by_collection = AsyncMock(return_value=2)

        with patch(
            "mcp_server.tools.document_tools.get_document_repository",
            return_value=mock_doc_repo,
        ):
            result = await list_documents(ListDocumentsInput(limit=50, offset=0))

            assert result.total == 2
            assert result.documents[0].document_id == "doc-123"
            assert result.documents[1].document_id == "doc-456"

    @pytest.mark.asyncio
    async def test_list_documents_excludes_content(self, mock_cat_info):
        """Test that list_documents does NOT return document content."""
        set_cat_info(mock_cat_info)

        mock_doc_repo = MagicMock()
        mock_doc_repo.list_all = AsyncMock(
            return_value=[
                MagicMock(
                    document_id="doc-123",
                    collection_id="27241155-eaae-4678-a69f-c8003512f1fe",
                    title="Test Doc 1",
                    content="This content should NOT be returned",
                    document_type="markdown",
                    created_at=datetime(2024, 1, 1, 0, 0, 0),
                    updated_at=datetime(2024, 1, 1, 0, 0, 0),
                    doc_metadata={},
                ),
            ]
        )
        mock_doc_repo.count_by_collection = AsyncMock(return_value=1)

        with patch(
            "mcp_server.tools.document_tools.get_document_repository",
            return_value=mock_doc_repo,
        ):
            result = await list_documents(ListDocumentsInput(limit=50, offset=0))

            assert len(result.documents) == 1
            doc = result.documents[0]
            assert doc.document_id == "doc-123"
            assert doc.title == "Test Doc 1"
            # Verify content field is NOT present on DocumentListItem
            assert not hasattr(doc, "content")

    @pytest.mark.asyncio
    async def test_list_documents_uses_count_query_not_len(self, mock_cat_info):
        """Test that total count comes from count_by_collection, not len(documents)."""
        set_cat_info(mock_cat_info)

        mock_doc_repo = MagicMock()
        # Simulate pagination: only 2 docs returned but 10 total in collection
        mock_doc_repo.list_all = AsyncMock(
            return_value=[
                MagicMock(
                    document_id=f"doc-{i}",
                    collection_id="27241155-eaae-4678-a69f-c8003512f1fe",
                    title=f"Test Doc {i}",
                    content=f"Content {i}",
                    document_type="markdown",
                    created_at=datetime(2024, 1, i, 0, 0, 0),
                    updated_at=datetime(2024, 1, i, 0, 0, 0),
                    doc_metadata={},
                )
                for i in range(1, 3)  # Only 2 docs
            ]
        )
        mock_doc_repo.count_by_collection = AsyncMock(return_value=10)

        with patch(
            "mcp_server.tools.document_tools.get_document_repository",
            return_value=mock_doc_repo,
        ):
            result = await list_documents(ListDocumentsInput(limit=2, offset=0))

            # Should return actual total (10), not length of returned docs (2)
            assert result.total == 10
            assert len(result.documents) == 2
            mock_doc_repo.count_by_collection.assert_called_once_with(
                "27241155-eaae-4678-a69f-c8003512f1fe"
            )

    @pytest.mark.asyncio
    async def test_list_documents_admin_uses_count_all(self):
        """Test that admin listing uses count_all() for total."""
        clear_cat_info()
        clear_all_auth()
        # Admin user: is_superuser flag in user_info makes is_admin=True in auth context
        set_user_info(
            {
                "user_id": "admin-123",
                "username": "admin",
                "email": "admin@test.com",
                "is_superuser": True,
                "scopes": [],
            }
        )
        # Need to set collections (even if empty) for auth context to build properly
        set_user_collections([])

        mock_doc_repo = MagicMock()
        mock_doc_repo.list_all = AsyncMock(
            return_value=[
                MagicMock(
                    document_id="doc-1",
                    collection_id="col-1",
                    title="Doc 1",
                    content="Content 1",
                    document_type="markdown",
                    created_at=datetime(2024, 1, 1),
                    updated_at=datetime(2024, 1, 1),
                    doc_metadata={},
                ),
            ]
        )
        mock_doc_repo.count_all = AsyncMock(return_value=100)

        with patch(
            "mcp_server.tools.document_tools.get_document_repository",
            return_value=mock_doc_repo,
        ):
            result = await list_documents(ListDocumentsInput(limit=1, offset=0))

            assert result.total == 100
            assert len(result.documents) == 1
            mock_doc_repo.count_all.assert_called_once()
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_list_documents_pat_user_uses_count_by_user(self):
        """Test that PAT/JWT user listing uses count_by_user() for total."""
        clear_cat_info()
        clear_all_auth()
        set_user_info(
            {
                "user_id": "user-789",
                "username": "user",
                "email": "user@test.com",
                "is_superuser": False,
                "scopes": ["read"],
            }
        )
        set_user_collections(
            [
                {"collection_id": "col-1", "qdrant_collection": "qdrant-1"},
            ]
        )

        mock_doc_repo = MagicMock()
        mock_doc_repo.list_all_for_user = AsyncMock(
            return_value=[
                MagicMock(
                    document_id="doc-1",
                    collection_id="col-1",
                    title="Doc 1",
                    content="Content 1",
                    document_type="markdown",
                    created_at=datetime(2024, 1, 1),
                    updated_at=datetime(2024, 1, 1),
                    doc_metadata={},
                ),
            ]
        )
        mock_doc_repo.count_by_user = AsyncMock(return_value=50)

        with patch(
            "mcp_server.tools.document_tools.get_document_repository",
            return_value=mock_doc_repo,
        ):
            result = await list_documents(ListDocumentsInput(limit=1, offset=0))

            assert result.total == 50
            assert len(result.documents) == 1
            mock_doc_repo.count_by_user.assert_called_once_with("user-789")
        clear_all_auth()


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
