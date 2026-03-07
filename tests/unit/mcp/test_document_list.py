"""Tests for list_documents MCP tool."""

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
    ListDocumentsInput,
    list_documents,
)


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
            assert not hasattr(doc, "content")

    @pytest.mark.asyncio
    async def test_list_documents_uses_count_query_not_len(self, mock_cat_info):
        """Test that total count comes from count_by_collection, not len(documents)."""
        set_cat_info(mock_cat_info)

        mock_doc_repo = MagicMock()
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
                for i in range(1, 3)
            ]
        )
        mock_doc_repo.count_by_collection = AsyncMock(return_value=10)

        with patch(
            "mcp_server.tools.document_tools.get_document_repository",
            return_value=mock_doc_repo,
        ):
            result = await list_documents(ListDocumentsInput(limit=2, offset=0))

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
        set_user_info(
            {
                "user_id": "admin-123",
                "username": "admin",
                "email": "admin@test.com",
                "is_superuser": True,
                "scopes": [],
            }
        )
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

    @pytest.mark.asyncio
    async def test_list_documents_with_collection_id_filter(self):
        """Test that list_documents with collection_id filters by collection."""
        clear_cat_info()
        clear_all_auth()
        set_user_info(
            {
                "user_id": "user-456",
                "username": "user",
                "email": "user@test.com",
                "is_superuser": False,
                "scopes": ["read"],
            }
        )
        set_user_collections(
            [
                {"collection_id": "col-1", "qdrant_collection": "qdrant-1"},
                {"collection_id": "col-2", "qdrant_collection": "qdrant-2"},
            ]
        )

        mock_collection_repo = MagicMock()
        mock_collection_repo.get_by_id = AsyncMock(
            return_value={
                "collection_id": "col-1",
                "user_id": "user-456",
                "name": "Collection 1",
            }
        )

        mock_doc_repo = MagicMock()
        mock_doc_repo.list_by_collection = AsyncMock(
            return_value=[
                MagicMock(
                    document_id="doc-1",
                    collection_id="col-1",
                    title="Doc in Collection 1",
                    content="Content",
                    document_type="markdown",
                    created_at=datetime(2024, 1, 1),
                    updated_at=datetime(2024, 1, 1),
                    doc_metadata={},
                ),
            ]
        )
        mock_doc_repo.count_by_collection = AsyncMock(return_value=1)

        with (
            patch(
                "mcp_server.tools.document_tools.get_collection_repository",
                return_value=mock_collection_repo,
            ),
            patch(
                "mcp_server.tools.document_tools.get_document_repository",
                return_value=mock_doc_repo,
            ),
        ):
            result = await list_documents(
                ListDocumentsInput(limit=50, offset=0, collection_id="col-1")
            )

            assert result.total == 1
            assert len(result.documents) == 1
            assert result.documents[0].document_id == "doc-1"
            mock_doc_repo.list_by_collection.assert_called_once_with(
                "user-456", "col-1", limit=50, offset=0
            )
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_list_documents_with_collection_id_not_owned(self):
        """Test that list_documents raises error when accessing another user's collection."""
        clear_cat_info()
        clear_all_auth()
        set_user_info(
            {
                "user_id": "user-456",
                "username": "user",
                "email": "user@test.com",
                "is_superuser": False,
                "scopes": ["read"],
            }
        )
        set_user_collections([])

        mock_collection_repo = MagicMock()
        mock_collection_repo.get_by_id = AsyncMock(
            return_value={
                "collection_id": "col-1",
                "user_id": "other-user",
                "name": "Other User Collection",
            }
        )

        with patch(
            "mcp_server.tools.document_tools.get_collection_repository",
            return_value=mock_collection_repo,
        ):
            with pytest.raises(ValueError, match="Collection not found or access denied"):
                await list_documents(ListDocumentsInput(limit=50, offset=0, collection_id="col-1"))
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_list_documents_with_collection_id_not_found(self):
        """Test that list_documents raises error for non-existent collection."""
        clear_cat_info()
        clear_all_auth()
        set_user_info(
            {
                "user_id": "user-456",
                "username": "user",
                "email": "user@test.com",
                "is_superuser": False,
                "scopes": ["read"],
            }
        )
        set_user_collections([])

        mock_collection_repo = MagicMock()
        mock_collection_repo.get_by_id = AsyncMock(return_value=None)

        with patch(
            "mcp_server.tools.document_tools.get_collection_repository",
            return_value=mock_collection_repo,
        ):
            with pytest.raises(ValueError, match="Collection not found or access denied"):
                await list_documents(
                    ListDocumentsInput(limit=50, offset=0, collection_id="non-existent")
                )
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_list_documents_without_collection_id(self):
        """Test that list_documents without collection_id returns all user documents."""
        clear_cat_info()
        clear_all_auth()
        set_user_info(
            {
                "user_id": "user-456",
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
                    content="Content",
                    document_type="markdown",
                    created_at=datetime(2024, 1, 1),
                    updated_at=datetime(2024, 1, 1),
                    doc_metadata={},
                ),
                MagicMock(
                    document_id="doc-2",
                    collection_id="col-2",
                    title="Doc 2",
                    content="Content",
                    document_type="markdown",
                    created_at=datetime(2024, 1, 2),
                    updated_at=datetime(2024, 1, 2),
                    doc_metadata={},
                ),
            ]
        )
        mock_doc_repo.count_by_user = AsyncMock(return_value=2)

        with patch(
            "mcp_server.tools.document_tools.get_document_repository",
            return_value=mock_doc_repo,
        ):
            result = await list_documents(ListDocumentsInput(limit=50, offset=0))

            assert result.total == 2
            assert len(result.documents) == 2
            mock_doc_repo.list_all_for_user.assert_called_once_with("user-456", limit=50, offset=0)
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_list_documents_with_collection_id_pagination(self):
        """Test that pagination works with collection_id filter."""
        clear_cat_info()
        clear_all_auth()
        set_user_info(
            {
                "user_id": "user-456",
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

        mock_collection_repo = MagicMock()
        mock_collection_repo.get_by_id = AsyncMock(
            return_value={
                "collection_id": "col-1",
                "user_id": "user-456",
                "name": "Collection 1",
            }
        )

        mock_doc_repo = MagicMock()
        mock_doc_repo.list_by_collection = AsyncMock(
            return_value=[
                MagicMock(
                    document_id="doc-2",
                    collection_id="col-1",
                    title="Doc 2",
                    content="Content",
                    document_type="markdown",
                    created_at=datetime(2024, 1, 2),
                    updated_at=datetime(2024, 1, 2),
                    doc_metadata={},
                ),
            ]
        )
        mock_doc_repo.count_by_collection = AsyncMock(return_value=10)

        with (
            patch(
                "mcp_server.tools.document_tools.get_collection_repository",
                return_value=mock_collection_repo,
            ),
            patch(
                "mcp_server.tools.document_tools.get_document_repository",
                return_value=mock_doc_repo,
            ),
        ):
            result = await list_documents(
                ListDocumentsInput(limit=1, offset=1, collection_id="col-1")
            )

            assert result.total == 10
            assert len(result.documents) == 1
            assert result.documents[0].document_id == "doc-2"
            mock_doc_repo.list_by_collection.assert_called_once_with(
                "user-456", "col-1", limit=1, offset=1
            )
        clear_all_auth()
