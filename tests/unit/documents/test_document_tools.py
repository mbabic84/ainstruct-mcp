"""
Comprehensive tests for all document tools.
Tests store, search, get, list, update, delete operations.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid

from app.tools.document_tools import (
    StoreDocumentInput,
    StoreDocumentOutput,
    SearchDocumentsInput,
    SearchDocumentsOutput,
    GetDocumentInput,
    GetDocumentOutput,
    ListDocumentsInput,
    ListDocumentsOutput,
    DeleteDocumentInput,
    DeleteDocumentOutput,
    UpdateDocumentInput,
    UpdateDocumentOutput,
    store_document,
    search_documents,
    get_document,
    list_documents,
    delete_document,
    update_document,
)
from app.tools.context import set_cat_info, set_user_info, clear_all_auth
from app.db.models import Permission


@pytest.fixture
def mock_read_write_key():
    """API key with read_write permission."""
    return {
        "id": "api-key-rw",
        "user_id": "user-123",
        "collection_id": "collection-123",
        "collection_name": "test-collection",
        "qdrant_collection": "qdrant-uuid-123",
        "permission": Permission.READ_WRITE,
        "is_admin": False,
        "is_superuser": False,
        "auth_type": "api_key",
    }


@pytest.fixture
def mock_read_only_key():
    """API key with read-only permission."""
    return {
        "id": "api-key-ro",
        "user_id": "user-123",
        "collection_id": "collection-123",
        "collection_name": "test-collection",
        "qdrant_collection": "qdrant-uuid-123",
        "permission": Permission.READ,
        "is_admin": False,
        "is_superuser": False,
        "auth_type": "api_key",
    }


@pytest.fixture
def mock_jwt_user():
    """JWT authenticated user."""
    return {
        "id": "user-123",
        "user_id": "user-123",
        "username": "testuser",
        "email": "test@example.com",
        "is_superuser": False,
        "auth_type": "jwt",
        "collection_ids": ["coll-123"],
        "qdrant_collections": ["docs_123"],
    }


@pytest.fixture
def mock_admin_key():
    """Admin API key with full access."""
    return {
        "id": "admin-key",
        "is_admin": True,
        "is_superuser": False,
        "auth_type": "api_key",
    }


@pytest.fixture
def mock_document():
    """Mock document response."""
    return MagicMock(
        id=str(uuid.uuid4()),
        collection_id="collection-123",
        title="Test Document",
        content="This is test content for the document.",
        document_type="markdown",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        doc_metadata={"key": "value"},
    )


@pytest.fixture
def mock_chunks():
    """Mock chunked document."""
    return [
        {
            "chunk_index": 0,
            "content": "This is test content for the document.",
            "token_count": 10,
            "title": "Test Document",
        }
    ]


@pytest.fixture
def mock_embeddings():
    """Mock embedding vectors."""
    return [[0.1] * 4096]


class TestStoreDocument:
    """Tests for store_document tool."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_store_document_success(self, mock_read_write_key, mock_document, mock_chunks, mock_embeddings):
        """Successfully store a document with read_write key."""
        set_cat_info(mock_read_write_key)

        with (
            patch("app.tools.document_tools.get_document_repository") as mock_repo_factory,
            patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory,
            patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory,
            patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory,
        ):
            mock_repo = MagicMock()
            mock_repo.create.return_value = mock_document
            mock_repo_factory.return_value = mock_repo

            mock_qdrant = MagicMock()
            mock_qdrant.upsert_chunks.return_value = ["point-1"]
            mock_qdrant_factory.return_value = mock_qdrant

            mock_embedding = MagicMock()
            mock_embedding.embed_texts = AsyncMock(return_value=mock_embeddings)
            mock_embedding_factory.return_value = mock_embedding

            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.return_value = mock_chunks
            mock_chunking_factory.return_value = mock_chunking

            result = await store_document(StoreDocumentInput(
                title="Test Document",
                content="This is test content for the document.",
            ))

            assert isinstance(result, StoreDocumentOutput)
            assert result.chunk_count == 1
            assert result.token_count == 10
            mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_document_read_only_denied(self, mock_read_only_key):
        """Read-only key cannot store documents."""
        set_cat_info(mock_read_only_key)

        with pytest.raises(ValueError, match="Insufficient permissions"):
            await store_document(StoreDocumentInput(
                title="Test",
                content="Content",
            ))

    @pytest.mark.asyncio
    async def test_store_document_jwt_denied(self, mock_jwt_user):
        """JWT users CAN store documents (they have access to their collections)."""
        set_user_info(mock_jwt_user)

        with patch("app.tools.context.get_collection_repository") as mock_coll_repo, \
             patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_embedding_service") as mock_emb_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunk_factory:
            mock_coll_repo.return_value.list_by_user.return_value = [
                {"id": "coll-123", "qdrant_collection": "docs_123"}
            ]
            
            mock_doc = MagicMock()
            mock_doc.id = "doc-new"
            mock_doc.collection_id = "coll-123"
            mock_doc_repo = MagicMock()
            mock_doc_repo.create.return_value = mock_doc
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            mock_qdrant = MagicMock()
            mock_qdrant_factory.return_value = mock_qdrant
            
            mock_emb = MagicMock()
            mock_emb.embed_texts = AsyncMock(return_value=[[0.1]])
            mock_emb_factory.return_value = mock_emb
            
            mock_chunk = MagicMock()
            mock_chunk.chunk_markdown.return_value = []
            mock_chunk_factory.return_value = mock_chunk

            result = await store_document(StoreDocumentInput(
                title="Test",
                content="Content",
            ))

            assert "Document stored successfully" in result.message

    @pytest.mark.asyncio
    async def test_store_document_not_authenticated(self):
        """Unauthenticated users cannot store documents."""
        with pytest.raises(ValueError, match="Not authenticated"):
            await store_document(StoreDocumentInput(
                title="Test",
                content="Content",
            ))


class TestSearchDocuments:
    """Tests for search_documents tool."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_search_documents_with_api_key(self, mock_read_write_key):
        """Search documents with API key."""
        set_cat_info(mock_read_write_key)

        with (
            patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory,
            patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory,
        ):
            mock_embedding = MagicMock()
            mock_embedding.embed_query = AsyncMock(return_value=[0.1] * 4096)
            mock_embedding_factory.return_value = mock_embedding

            mock_qdrant = MagicMock()
            mock_qdrant.search.return_value = [
                {
                    "document_id": "doc-1",
                    "title": "Test Doc",
                    "chunk_index": 0,
                    "content": "Content",
                    "score": 0.95,
                    "token_count": 10,
                }
            ]
            mock_qdrant_factory.return_value = mock_qdrant

            result = await search_documents(SearchDocumentsInput(
                query="test query",
                max_results=5,
            ))

            assert isinstance(result, SearchDocumentsOutput)
            assert result.total_results == 1
            assert len(result.results) == 1

    @pytest.mark.asyncio
    async def test_search_documents_with_read_only_key(self, mock_read_only_key):
        """Read-only key can search documents."""
        set_cat_info(mock_read_only_key)

        with (
            patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory,
            patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory,
        ):
            mock_embedding = MagicMock()
            mock_embedding.embed_query = AsyncMock(return_value=[0.1] * 4096)
            mock_embedding_factory.return_value = mock_embedding

            mock_qdrant = MagicMock()
            mock_qdrant.search.return_value = []
            mock_qdrant_factory.return_value = mock_qdrant

            result = await search_documents(SearchDocumentsInput(query="test"))

            assert result.total_results == 0

    @pytest.mark.asyncio
    async def test_search_documents_with_admin_key(self, mock_admin_key):
        """Admin key can search all collections."""
        set_cat_info(mock_admin_key)

        with (
            patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory,
            patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory,
        ):
            mock_embedding = MagicMock()
            mock_embedding.embed_query = AsyncMock(return_value=[0.1] * 4096)
            mock_embedding_factory.return_value = mock_embedding

            mock_qdrant = MagicMock()
            mock_qdrant.search.return_value = []
            mock_qdrant_factory.return_value = mock_qdrant

            # Admin should pass is_admin=True to qdrant service
            await search_documents(SearchDocumentsInput(query="test"))
            mock_qdrant_factory.assert_called_once_with(None, is_admin=True)


class TestGetDocument:
    """Tests for get_document tool."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_get_document_success(self, mock_read_write_key, mock_document):
        """Successfully get a document."""
        set_cat_info(mock_read_write_key)

        with patch("app.tools.document_tools.get_document_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_document
            mock_repo_factory.return_value = mock_repo

            result = await get_document(GetDocumentInput(document_id=mock_document.id))

            assert result is not None
            assert result.id == mock_document.id
            assert result.title == "Test Document"

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, mock_read_write_key):
        """Document not found returns None."""
        set_cat_info(mock_read_write_key)

        with patch("app.tools.document_tools.get_document_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_factory.return_value = mock_repo

            result = await get_document(GetDocumentInput(document_id="nonexistent"))

            assert result is None

    @pytest.mark.asyncio
    async def test_get_document_different_collection_denied(self, mock_read_write_key, mock_document):
        """Cannot get document from different collection."""
        set_cat_info(mock_read_write_key)
        mock_document.collection_id = "different-collection"

        with patch("app.tools.document_tools.get_document_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None  # Filtered by collection_id
            mock_repo_factory.return_value = mock_repo

            result = await get_document(GetDocumentInput(document_id=mock_document.id))

            assert result is None


class TestListDocuments:
    """Tests for list_documents tool."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_list_documents_success(self, mock_read_write_key, mock_document):
        """Successfully list documents."""
        set_cat_info(mock_read_write_key)

        with patch("app.tools.document_tools.get_document_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = [mock_document]
            mock_repo_factory.return_value = mock_repo

            result = await list_documents(ListDocumentsInput(limit=50, offset=0))

            assert isinstance(result, ListDocumentsOutput)
            assert len(result.documents) == 1
            assert result.total == 1

    @pytest.mark.asyncio
    async def test_list_documents_pagination(self, mock_read_write_key):
        """List documents with pagination."""
        set_cat_info(mock_read_write_key)

        with patch("app.tools.document_tools.get_document_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = []
            mock_repo_factory.return_value = mock_repo

            await list_documents(ListDocumentsInput(limit=10, offset=20))

            mock_repo.list_all.assert_called_once_with(limit=10, offset=20)


class TestUpdateDocument:
    """Tests for update_document tool."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_update_document_success(self, mock_read_write_key, mock_document, mock_chunks, mock_embeddings):
        """Successfully update a document."""
        set_cat_info(mock_read_write_key)

        updated_doc = MagicMock(
            id=mock_document.id,
            collection_id="collection-123",
            title="Updated Title",
            content="Updated content",
            document_type="markdown",
        )

        with (
            patch("app.tools.document_tools.get_document_repository") as mock_repo_factory,
            patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory,
            patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory,
            patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory,
        ):
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_document
            mock_repo.update.return_value = updated_doc
            mock_repo_factory.return_value = mock_repo

            mock_qdrant = MagicMock()
            mock_qdrant_factory.return_value = mock_qdrant

            mock_embedding = MagicMock()
            mock_embedding.embed_texts = AsyncMock(return_value=mock_embeddings)
            mock_embedding_factory.return_value = mock_embedding

            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.return_value = mock_chunks
            mock_chunking_factory.return_value = mock_chunking

            result = await update_document(UpdateDocumentInput(
                document_id=mock_document.id,
                title="Updated Title",
                content="Updated content",
            ))

            assert result.document_id == mock_document.id
            assert result.chunk_count == 1
            mock_qdrant.delete_by_document_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_document_read_only_denied(self, mock_read_only_key):
        """Read-only key cannot update documents."""
        set_cat_info(mock_read_only_key)

        with pytest.raises(ValueError, match="Insufficient permissions"):
            await update_document(UpdateDocumentInput(
                document_id="doc-1",
                title="Test",
                content="Content",
            ))

    @pytest.mark.asyncio
    async def test_update_document_jwt_denied(self, mock_jwt_user):
        """JWT users CAN update documents (they have access to their collections)."""
        set_user_info(mock_jwt_user)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant, \
             patch("app.tools.document_tools.get_embedding_service") as mock_emb, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunk:
            mock_doc = MagicMock()
            mock_doc.id = "doc-1"
            mock_doc.collection_id = "coll-123"
            mock_doc.title = "Old Title"
            mock_doc.content = "Old Content"
            mock_doc_repo.return_value.get_by_id_for_user.return_value = mock_doc
            mock_doc_repo.return_value.update.return_value = MagicMock(id="doc-1")
            mock_qdrant.return_value = MagicMock()
            mock_emb.return_value = MagicMock(embed_texts=MagicMock(return_value=[[0.1]]))
            mock_chunk.return_value = MagicMock(chunk_markdown=MagicMock(return_value=[]))

            result = await update_document(UpdateDocumentInput(
                document_id="doc-1",
                title="Test",
                content="Content",
            ))

            assert "Document updated successfully" in result.message


class TestDeleteDocument:
    """Tests for delete_document tool."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_delete_document_success(self, mock_read_write_key, mock_document):
        """Successfully delete a document."""
        set_cat_info(mock_read_write_key)

        with (
            patch("app.tools.document_tools.get_document_repository") as mock_repo_factory,
            patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory,
        ):
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_document
            mock_repo.delete.return_value = True
            mock_repo_factory.return_value = mock_repo

            mock_qdrant = MagicMock()
            mock_qdrant_factory.return_value = mock_qdrant

            result = await delete_document(DeleteDocumentInput(document_id=mock_document.id))

            assert result.success is True
            mock_qdrant.delete_by_document_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, mock_read_write_key):
        """Document not found returns failure."""
        set_cat_info(mock_read_write_key)

        with (
            patch("app.tools.document_tools.get_document_repository") as mock_repo_factory,
            patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory,
        ):
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_factory.return_value = mock_repo

            mock_qdrant = MagicMock()
            mock_qdrant_factory.return_value = mock_qdrant

            result = await delete_document(DeleteDocumentInput(document_id="nonexistent"))

            assert result.success is False
            assert "not found" in result.message.lower()

    @pytest.mark.asyncio
    async def test_delete_document_read_only_denied(self, mock_read_only_key):
        """Read-only key cannot delete documents."""
        set_cat_info(mock_read_only_key)

        with pytest.raises(ValueError, match="Insufficient permissions"):
            await delete_document(DeleteDocumentInput(document_id="doc-1"))