import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from app.tools.document_tools import (
    UpdateDocumentInput,
    UpdateDocumentOutput,
    update_document,
)
from app.tools.context import set_api_key_info, clear_api_key_info


@pytest.fixture
def mock_api_key_info():
    return {
        "id": "test-api-key-id",
        "label": "Test Key",
        "qdrant_collection": "test-collection",
        "is_admin": False,
    }


@pytest.fixture
def mock_document():
    doc = MagicMock()
    doc.id = str(uuid.uuid4())
    doc.api_key_id = "test-api-key-id"
    doc.title = "Old Title"
    doc.content = "Old content"
    doc.document_type = "markdown"
    doc.doc_metadata = {}
    return doc


@pytest.fixture
def mock_updated_document():
    doc = MagicMock()
    doc.id = str(uuid.uuid4())
    doc.api_key_id = "test-api-key-id"
    doc.title = "New Title"
    doc.content = "New content for the document"
    doc.document_type = "markdown"
    return doc


@pytest.fixture
def mock_chunks():
    return [
        {
            "chunk_index": 0,
            "content": "New content for the document",
            "token_count": 10,
            "title": "New Title",
        }
    ]


@pytest.fixture
def mock_embeddings():
    return [[0.1, 0.2, 0.3] * 512]


class TestUpdateDocument:
    def setup_method(self):
        clear_api_key_info()

    def teardown_method(self):
        clear_api_key_info()

    @pytest.mark.asyncio
    async def test_update_document_success(
        self, mock_api_key_info, mock_document, mock_updated_document, mock_chunks, mock_embeddings
    ):
        set_api_key_info(mock_api_key_info)

        with patch("app.tools.document_tools.get_document_repository") as mock_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory:

            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_document
            mock_repo.update.return_value = mock_updated_document
            mock_repo_factory.return_value = mock_repo

            mock_qdrant = MagicMock()
            mock_qdrant.delete_by_document_id.return_value = None
            mock_qdrant.upsert_chunks.return_value = ["point-1", "point-2"]
            mock_qdrant_factory.return_value = mock_qdrant

            mock_embedding = MagicMock()
            mock_embedding.embed_texts = AsyncMock(return_value=mock_embeddings)
            mock_embedding_factory.return_value = mock_embedding

            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.return_value = mock_chunks
            mock_chunking_factory.return_value = mock_chunking

            input_data = UpdateDocumentInput(
                document_id=mock_document.id,
                title="New Title",
                content="New content for the document",
                document_type="markdown",
                doc_metadata={"key": "value"},
            )

            result = await update_document(input_data)

            assert isinstance(result, UpdateDocumentOutput)
            assert result.document_id == mock_updated_document.id
            assert result.chunk_count == 1
            assert result.token_count == 10
            assert "successfully" in result.message.lower()

            mock_repo.get_by_id.assert_called_once_with(mock_document.id)
            mock_qdrant.delete_by_document_id.assert_called_once_with(mock_document.id)
            mock_repo.update.assert_called_once_with(
                doc_id=mock_document.id,
                title="New Title",
                content="New content for the document",
                document_type="markdown",
                doc_metadata={"key": "value"},
            )
            mock_chunking.chunk_markdown.assert_called_once_with(
                "New content for the document", "New Title"
            )
            mock_embedding.embed_texts.assert_called_once()
            mock_qdrant.upsert_chunks.assert_called_once()
            mock_repo.update_qdrant_point_id.assert_called_once_with(
                mock_updated_document.id, ["point-1", "point-2"]
            )

    @pytest.mark.asyncio
    async def test_update_document_not_found(self, mock_api_key_info):
        set_api_key_info(mock_api_key_info)

        with patch("app.tools.document_tools.get_document_repository") as mock_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory:

            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_factory.return_value = mock_repo

            mock_qdrant = MagicMock()
            mock_qdrant_factory.return_value = mock_qdrant

            input_data = UpdateDocumentInput(
                document_id="non-existent-id",
                title="New Title",
                content="New content",
            )

            with pytest.raises(ValueError, match="Document not found"):
                await update_document(input_data)

    @pytest.mark.asyncio
    async def test_update_document_not_authenticated(self):
        clear_api_key_info()

        input_data = UpdateDocumentInput(
            document_id="some-id",
            title="New Title",
            content="New content",
        )

        with pytest.raises(ValueError, match="API key not authenticated"):
            await update_document(input_data)

    @pytest.mark.asyncio
    async def test_update_document_admin_rejected(self):
        set_api_key_info({
            "id": "admin-id",
            "is_admin": True,
        })

        input_data = UpdateDocumentInput(
            document_id="some-id",
            title="New Title",
            content="New content",
        )

        with pytest.raises(ValueError, match="Admin cannot update documents"):
            await update_document(input_data)

    @pytest.mark.asyncio
    async def test_update_document_empty_content(
        self, mock_api_key_info, mock_document, mock_updated_document
    ):
        set_api_key_info(mock_api_key_info)

        mock_updated_document.id = mock_document.id

        with patch("app.tools.document_tools.get_document_repository") as mock_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory:

            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_document
            mock_repo.update.return_value = mock_updated_document
            mock_repo_factory.return_value = mock_repo

            mock_qdrant = MagicMock()
            mock_qdrant_factory.return_value = mock_qdrant

            mock_embedding = MagicMock()
            mock_embedding_factory.return_value = mock_embedding

            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.return_value = []
            mock_chunking_factory.return_value = mock_chunking

            input_data = UpdateDocumentInput(
                document_id=mock_document.id,
                title="New Title",
                content="",
            )

            result = await update_document(input_data)

            assert result.chunk_count == 0
            assert result.token_count == 0
            mock_qdrant.upsert_chunks.assert_not_called()
            mock_embedding.embed_texts.assert_not_called()
