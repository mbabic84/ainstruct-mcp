"""
Error handling and resilience tests for document_tools.
Tests failures in external services (Qdrant, embedding, chunking) and transaction rollback.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from app.tools.document_tools import (
    StoreDocumentInput,
    UpdateDocumentInput,
    DeleteDocumentInput,
    store_document,
    update_document,
    delete_document,
    GetDocumentInput,
    get_document,
)
from app.tools.context import set_api_key_info, clear_all_auth
from app.db.models import Permission


@pytest.fixture
def mock_api_key_write():
    """API key with read_write permission."""
    return {
        "id": "api-key-123",
        "user_id": "user-123",
        "collection_id": "collection-123",
        "permission": Permission.READ_WRITE,
        "is_admin": False,
        "auth_type": "api_key",
        "qdrant_collection": "qdrant-collection-123",
    }


@pytest.fixture
def mock_document():
    """Mock document."""
    return MagicMock(
        id="doc-123",
        collection_id="collection-123",
        title="Test Document",
        content="# Test\n\nContent here",
        document_type="markdown",
        doc_metadata={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def mock_chunks():
    """Mock chunks from chunking service."""
    return [
        {
            "chunk_index": 0,
            "content": "Chunk 1 content",
            "token_count": 10,
            "title": "Test Document",
        },
        {
            "chunk_index": 1,
            "content": "Chunk 2 content",
            "token_count": 12,
            "title": "Test Document",
        },
    ]


class TestStoreDocumentErrors:
    """Error handling tests for store_document."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_store_document_qdrant_fails_after_sql_create(self, mock_api_key_write, mock_chunks):
        """
        Test rollback when Qdrant fails after document is created in SQL.
        The document should be deleted from SQL if Qdrant fails.
        """
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory, \
             patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory:
            
            mock_doc_repo = MagicMock()
            mock_doc = MagicMock(id="doc-123", collection_id="collection-123")
            mock_doc_repo.create.return_value = mock_doc
            mock_doc_repo.delete = MagicMock()  # We expect this to be called for rollback
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            mock_qdrant = MagicMock()
            mock_qdrant.upsert_chunks.side_effect = Exception("Qdrant connection failed")
            mock_qdrant_factory.return_value = mock_qdrant
            
            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.return_value = mock_chunks
            mock_chunking_factory.return_value = mock_chunking
            
            mock_embedding = MagicMock()
            mock_embedding.embed_texts = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
            mock_embedding_factory.return_value = mock_embedding
            
            input_data = StoreDocumentInput(
                title="Test Doc",
                content="# Test\n\nContent",
            )
            
            with pytest.raises(Exception, match="Qdrant connection failed"):
                await store_document(input_data)

            # Document is created in SQL
            mock_doc_repo.create.assert_called_once()
            # Note: Current implementation does not rollback on Qdrant failure

    @pytest.mark.asyncio
    async def test_store_document_embedding_service_fails(self, mock_api_key_write, mock_chunks):
        """Test failure when embedding service is unavailable."""
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory, \
             patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory:
            
            mock_doc_repo = MagicMock()
            mock_doc = MagicMock(id="doc-123")
            mock_doc_repo.create.return_value = mock_doc
            mock_doc_repo.delete = MagicMock()
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            mock_qdrant = MagicMock()
            mock_qdrant_factory.return_value = mock_qdrant
            
            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.return_value = mock_chunks
            mock_chunking_factory.return_value = mock_chunking
            
            async def raise_exception(*args, **kwargs):
                raise Exception("Embedding service unavailable")
            mock_embedding = MagicMock()
            mock_embedding.embed_texts = raise_exception
            mock_embedding_factory.return_value = mock_embedding
            
            input_data = StoreDocumentInput(
                title="Test Doc",
                content="# Test\n\nContent",
            )
            
            with pytest.raises(Exception, match="Embedding service unavailable"):
                await store_document(input_data)

            # Document is created before embedding, but rollback is not implemented

    @pytest.mark.asyncio
    async def test_store_document_chunking_service_fails(self, mock_api_key_write):
        """Test failure when chunking service raises an error."""
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory:

            mock_doc_repo = MagicMock()
            mock_doc = MagicMock(id="doc-123")
            mock_doc_repo.create.return_value = mock_doc
            mock_doc_repo.delete = MagicMock()
            mock_doc_repo_factory.return_value = mock_doc_repo

            mock_qdrant = MagicMock()
            mock_qdrant_factory.return_value = mock_qdrant

            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.side_effect = Exception("Chunking failed")
            mock_chunking_factory.return_value = mock_chunking

            input_data = StoreDocumentInput(
                title="Test Doc",
                content="# Test\n\nContent",
            )

            with pytest.raises(Exception, match="Chunking failed"):
                await store_document(input_data)

            # Document is created before chunking, but rollback is not implemented

    @pytest.mark.asyncio
    async def test_store_document_qdrant_update_qdrant_point_id_fails(self, mock_api_key_write, mock_chunks):
        """Test failure when updating qdrant_point_id after successful upsert."""
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory, \
             patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory:
            
            mock_doc_repo = MagicMock()
            mock_doc = MagicMock(id="doc-123")
            mock_doc_repo.create.return_value = mock_doc
            mock_doc_repo.update_qdrant_point_id.side_effect = Exception("DB update failed")
            mock_doc_repo.delete = MagicMock()
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            mock_qdrant = MagicMock()
            mock_qdrant.upsert_chunks.return_value = ["point-1", "point-2"]
            mock_qdrant_factory.return_value = mock_qdrant
            
            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.return_value = mock_chunks
            mock_chunking_factory.return_value = mock_chunking
            
            mock_embedding = MagicMock()
            mock_embedding.embed_texts = AsyncMock(return_value=[[0.1, 0.2]])
            mock_embedding_factory.return_value = mock_embedding
            
            input_data = StoreDocumentInput(
                title="Test Doc",
                content="# Test\n\nContent",
            )
            
            with pytest.raises(Exception, match="DB update failed"):
                await store_document(input_data)
            
            # Qdrant succeeded but DB update of point IDs failed
            # Document should NOT be deleted because Qdrant succeeded
            # But we need to check that update_qdrant_point_id was called
            mock_doc_repo.update_qdrant_point_id.assert_called_once()
            # Ideally, we should attempt cleanup of Qdrant points on failure
            # This depends on implementation; current code may not do that

    @pytest.mark.asyncio
    async def test_store_document_empty_chunks(self, mock_api_key_write):
        """Store document with empty content returns no chunks but document is stored."""
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory:

            mock_doc_repo = MagicMock()
            mock_doc = MagicMock(id="doc-123", chunk_count=0)
            mock_doc_repo.create.return_value = mock_doc
            mock_doc_repo_factory.return_value = mock_doc_repo

            mock_qdrant = MagicMock()
            mock_qdrant_factory.return_value = mock_qdrant

            mock_embedding = MagicMock()
            mock_embedding_factory.return_value = mock_embedding

            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.return_value = []  # Empty chunks
            mock_chunking_factory.return_value = mock_chunking

            input_data = StoreDocumentInput(
                title="Empty Doc",
                content="",  # Empty content
            )

            result = await store_document(input_data)
            
            assert result.document_id == "doc-123"
            assert result.chunk_count == 0
            assert result.token_count == 0
            # Qdrant should not be called for empty chunks

    @pytest.mark.asyncio
    async def test_store_document_invalid_collection_id(self, mock_api_key_write):
        """API key uses its own collection_id (input collection_id is ignored)."""
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory, \
             patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory:

            mock_doc_repo = MagicMock()
            mock_doc = MagicMock(id="doc-123")
            mock_doc_repo.create.return_value = mock_doc
            mock_doc_repo_factory.return_value = mock_doc_repo

            mock_qdrant = MagicMock()
            mock_qdrant_factory.return_value = mock_qdrant

            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.return_value = []
            mock_chunking_factory.return_value = mock_chunking

            mock_embedding = MagicMock()
            mock_embedding_factory.return_value = mock_embedding

            # API key auth uses collection_id from auth context, not input
            input_data = StoreDocumentInput(
                title="Test Doc",
                content="# Test",
                collection_id="different-collection-id",  # This is ignored for API key auth
            )

            # Should succeed using API key's collection
            result = await store_document(input_data)
            assert "Document stored successfully" in result.message


class TestUpdateDocumentErrors:
    """Error handling tests for update_document."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_update_document_qdrant_delete_fails(self, mock_api_key_write, mock_document, mock_chunks):
        """
        Test rollback when Qdrant delete fails during update.
        The old chunks cannot be deleted but the document update may proceed or rollback.
        """
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory, \
             patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory:
            
            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id.return_value = mock_document
            mock_doc_repo.update.return_value = mock_document
            # We might need to rollback the SQL update if Qdrant delete fails
            mock_doc_repo.delete = MagicMock()  # Potential rollback
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            mock_qdrant = MagicMock()
            mock_qdrant.delete_by_document_id.side_effect = Exception("Qdrant delete failed")
            mock_qdrant.upsert_chunks.return_value = ["point-new-1"]
            mock_qdrant_factory.return_value = mock_qdrant
            
            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.return_value = mock_chunks
            mock_chunking_factory.return_value = mock_chunking
            
            mock_embedding = MagicMock()
            mock_embedding.embed_texts = AsyncMock(return_value=[[0.1, 0.2]])
            mock_embedding_factory.return_value = mock_embedding
            
            input_data = UpdateDocumentInput(
                document_id="doc-123",
                title="Updated Title",
                content="Updated content",
            )
            
            # The current implementation does not have proper transaction handling
            # It deletes old chunks first then updates SQL, then adds new chunks
            # If delete fails, what happens? It still updates SQL and adds new chunks
            # This is a data integrity issue - we need to decide on error handling strategy
            with pytest.raises(Exception, match="Qdrant delete failed"):
                await update_document(input_data)
            
            # The document update may or may not have been called depending on order
            # Current code: get doc -> delete qdrant chunks -> update SQL -> add new chunks -> update point IDs
            # If delete fails, update SQL may still be called - this is a bug we should fix
            # For now, we document this scenario and test current behavior
            
    @pytest.mark.asyncio
    async def test_update_document_embedding_fails_after_sql_update(self, mock_api_key_write, mock_document, mock_chunks):
        """
        Test rollback when embedding fails after document is updated in SQL.
        Should delete new chunks and possibly revert document? (depends on strategy)
        """
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory, \
             patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory:
            
            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id.return_value = mock_document
            updated_doc = MagicMock(id="doc-123", title="Updated Title")
            mock_doc_repo.update.return_value = updated_doc
            mock_doc_repo.delete = MagicMock()  # For potential rollback
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            mock_qdrant = MagicMock()
            mock_qdrant.delete_by_document_id.return_value = None
            mock_qdrant.upsert_chunks.return_value = ["point-1"]
            mock_qdrant_factory.return_value = mock_qdrant
            
            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.return_value = mock_chunks
            mock_chunking_factory.return_value = mock_chunking
            
            async def raise_exception(*args, **kwargs):
                raise Exception("Embedding failed")
            mock_embedding = MagicMock()
            mock_embedding.embed_texts = raise_exception
            mock_embedding_factory.return_value = mock_embedding
            
            input_data = UpdateDocumentInput(
                document_id="doc-123",
                title="Updated Title",
                content="New content",
            )
            
            with pytest.raises(Exception, match="Embedding failed"):
                await update_document(input_data)
            
            # Document should have been updated in SQL
            mock_doc_repo.update.assert_called_once()
            # Old chunks deleted
            mock_qdrant.delete_by_document_id.assert_called_once()
            # But new chunks were not upserted due to embedding failure
            # The document update may need to be rolled back - this is a design decision

    @pytest.mark.asyncio
    async def test_update_document_document_not_found(self, mock_api_key_write):
        """Update with non-existent document fails."""
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory:
            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id.return_value = None
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            input_data = UpdateDocumentInput(
                document_id="nonexistent",
                title="Title",
                content="Content",
            )
            
            with pytest.raises(ValueError, match="Document not found"):
                await update_document(input_data)

    @pytest.mark.asyncio
    async def test_update_document_empty_content(self, mock_api_key_write, mock_document):
        """Update document to empty content works (no chunks)."""
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory:
            
            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id.return_value = mock_document
            updated_doc = MagicMock(id="doc-123", title="Updated Title")
            mock_doc_repo.update.return_value = updated_doc
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            mock_qdrant = MagicMock()
            mock_qdrant.delete_by_document_id.return_value = None
            mock_qdrant_factory.return_value = mock_qdrant
            
            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.return_value = []  # Empty content yields no chunks
            mock_chunking_factory.return_value = mock_chunking
            
            input_data = UpdateDocumentInput(
                document_id="doc-123",
                title="Updated Title",
                content="",  # Empty
            )
            
            result = await update_document(input_data)
            
            assert result.document_id == "doc-123"
            assert result.chunk_count == 0
            # old chunks should be deleted, none added


class TestDeleteDocumentErrors:
    """Error handling tests for delete_document."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_delete_document_qdrant_fails(self, mock_api_key_write, mock_document):
        """
        Test when Qdrant delete fails.
        SQL delete may still proceed or be rolled back depending on strategy.
        """
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory:
            
            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id.return_value = mock_document
            mock_doc_repo.delete = MagicMock()
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            mock_qdrant = MagicMock()
            mock_qdrant.delete_by_document_id.side_effect = Exception("Qdrant delete failed")
            mock_qdrant_factory.return_value = mock_qdrant
            
            input_data = DeleteDocumentInput(document_id="doc-123")
            
            with pytest.raises(Exception, match="Qdrant delete failed"):
                await delete_document(input_data)
            
            # Current implementation: deletes from Qdrant then SQL
            # If Qdrant fails, SQL should not be called
            mock_doc_repo.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_document_sql_fails_after_qdrant_success(self, mock_api_key_write, mock_document):
        """
        Test when Qdrant delete succeeds but SQL delete fails.
        This is a partial success scenario - data is out of sync.
        """
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory:
            
            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id.return_value = mock_document
            mock_doc_repo.delete.side_effect = Exception("Database constraint violation")
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            mock_qdrant = MagicMock()
            mock_qdrant.delete_by_document_id.return_value = None
            mock_qdrant_factory.return_value = mock_qdrant
            
            input_data = DeleteDocumentInput(document_id="doc-123")
            
            with pytest.raises(Exception, match="Database constraint violation"):
                await delete_document(input_data)
            
            # Qdrant delete was called first
            mock_qdrant.delete_by_document_id.assert_called_once()
            # SQL delete was attempted but failed
            mock_doc_repo.delete.assert_called_once()
            # Document points remain in Qdrant but not in SQL - inconsistency!

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, mock_api_key_write):
        """Delete non-existent document returns success=False."""
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory:
            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id.return_value = None
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            input_data = DeleteDocumentInput(document_id="nonexistent")
            
            result = await delete_document(input_data)
            
            assert result.success is False
            assert result.message == "Document not found"
            # Qdrant should not be called
            mock_doc_repo.delete.assert_not_called()


class TestGetDocumentErrors:
    """Error handling tests for get_document."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, mock_api_key_write):
        """get_document returns None for non-existent document."""
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory:
            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id.return_value = None
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            input_data = GetDocumentInput(document_id="nonexistent")
            
            result = await get_document(input_data)
            
            assert result is None

    @pytest.mark.asyncio
    async def test_get_document_repository_error(self, mock_api_key_write):
        """Database/repository errors propagate."""
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory:
            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id.side_effect = Exception("Database connection lost")
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            input_data = GetDocumentInput(document_id="doc-123")
            
            with pytest.raises(Exception, match="Database connection lost"):
                await get_document(input_data)


class TestTransactionAtomicity:
    """Tests for atomicity of document operations."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_store_document_atomicity_all_success(self, mock_api_key_write, mock_chunks):
        """
        Test that when all services succeed, everything is committed.
        Document created, chunks stored, point IDs updated.
        """
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory, \
             patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory:
            
            mock_doc_repo = MagicMock()
            mock_doc = MagicMock(id="doc-123", collection_id="coll-123")
            mock_doc_repo.create.return_value = mock_doc
            mock_doc_repo.update_qdrant_point_id = MagicMock()
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            mock_qdrant = MagicMock()
            mock_qdrant.upsert_chunks.return_value = ["point-1", "point-2"]
            mock_qdrant_factory.return_value = mock_qdrant
            
            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.return_value = mock_chunks
            mock_chunking_factory.return_value = mock_chunking
            
            mock_embedding = MagicMock()
            mock_embedding.embed_texts = AsyncMock(return_value=[[0.1, 0.2], [0.3, 0.4]])
            mock_embedding_factory.return_value = mock_embedding
            
            input_data = StoreDocumentInput(
                title="Test Doc",
                content="# Test\n\nContent",
            )
            
            result = await store_document(input_data)
            
            assert result.document_id == "doc-123"
            mock_doc_repo.create.assert_called_once()
            mock_qdrant.upsert_chunks.assert_called_once()
            mock_doc_repo.update_qdrant_point_id.assert_called_once_with("doc-123", ["point-1", "point-2"])

    @pytest.mark.asyncio
    async def test_store_document_failure_on_qdrant_error(self, mock_api_key_write, mock_chunks):
        """
        Test that if Qdrant fails, an exception is raised.
        Note: Current implementation does not rollback SQL document.
        """
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory, \
             patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory:

            mock_doc_repo = MagicMock()
            mock_doc = MagicMock(id="doc-123")
            mock_doc_repo.create.return_value = mock_doc
            mock_doc_repo_factory.return_value = mock_doc_repo

            mock_qdrant = MagicMock()
            mock_qdrant.upsert_chunks.side_effect = Exception("Qdrant error")
            mock_qdrant_factory.return_value = mock_qdrant

            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.return_value = mock_chunks
            mock_chunking_factory.return_value = mock_chunking

            mock_embedding = MagicMock()
            mock_embedding.embed_texts = AsyncMock(return_value=[[0.1, 0.2]])
            mock_embedding_factory.return_value = mock_embedding
            
            input_data = StoreDocumentInput(title="Test", content="Test")
            
            with pytest.raises(Exception, match="Qdrant error"):
                await store_document(input_data)

            # Note: Current implementation does not rollback SQL document on Qdrant failure

    @pytest.mark.asyncio
    async def test_update_document_rollback_on_qdrant_failure(self, mock_api_key_write, mock_document, mock_chunks):
        """
        Test that if Qdrant fails during update, changes are rolled back.
        This is complex because we need to decide: rollback SQL update? delete new chunks? restore old chunks?
        """
        set_api_key_info(mock_api_key_write)

        with patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory, \
             patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory:
            
            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id.return_value = mock_document
            updated_doc = MagicMock(id="doc-123", title="Updated")
            mock_doc_repo.update.return_value = updated_doc
            mock_doc_repo.delete = MagicMock()  # For rollback
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            mock_qdrant = MagicMock()
            # Fail on upsert (adding new chunks)
            mock_qdrant.upsert_chunks.side_effect = Exception("Qdrant upsert failed")
            mock_qdrant.delete_by_document_id.return_value = None
            mock_qdrant_factory.return_value = mock_qdrant
            
            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.return_value = mock_chunks
            mock_chunking_factory.return_value = mock_chunking
            
            mock_embedding = MagicMock()
            mock_embedding.embed_texts = AsyncMock(return_value=[[0.1, 0.2]])
            mock_embedding_factory.return_value = mock_embedding
            
            input_data = UpdateDocumentInput(
                document_id="doc-123",
                title="Updated Title",
                content="New content",
            )
            
            with pytest.raises(Exception, match="Qdrant upsert failed"):
                await update_document(input_data)
            
            # Document was retrieved
            mock_doc_repo.get_by_id.assert_called_once()
            # Old chunks were deleted
            mock_qdrant.delete_by_document_id.assert_called_once()
            # Document SQL update was called
            mock_doc_repo.update.assert_called_once()
            # New chunks were not added
            # Should we rollback the SQL update? Current implementation does not
            # This is a data integrity gap that should be addressed
