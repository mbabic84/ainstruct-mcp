"""
Tests for PAT (Personal Access Token) document access.
Verifies that PAT can access documents across all user collections.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import uuid

from app.tools.document_tools import (
    GetDocumentInput,
    ListDocumentsInput,
    DeleteDocumentInput,
    UpdateDocumentInput,
    get_document,
    list_documents,
    delete_document,
    update_document,
    search_documents,
    SearchDocumentsInput,
)
from app.tools.context import set_pat_info, clear_all_auth


@pytest.fixture
def mock_pat_user():
    """PAT authenticated user with access to multiple collections."""
    return {
        "id": "pat-123",
        "user_id": "user-123",
        "username": "testuser",
        "email": "test@example.com",
        "scopes": ["read", "write"],
        "is_superuser": False,
        "auth_type": "pat",
    }


@pytest.fixture
def mock_pat_admin():
    """PAT with superuser access."""
    return {
        "id": "pat-admin",
        "user_id": "admin-user",
        "username": "admin",
        "email": "admin@example.com",
        "scopes": ["read", "write", "admin"],
        "is_superuser": True,
        "auth_type": "pat",
    }


@pytest.fixture
def mock_collections():
    """User's collections."""
    return [
        {
            "id": "collection-1",
            "name": "Collection 1",
            "qdrant_collection": "qdrant-coll-1",
            "user_id": "user-123",
        },
        {
            "id": "collection-2",
            "name": "Collection 2",
            "qdrant_collection": "qdrant-coll-2",
            "user_id": "user-123",
        },
    ]


@pytest.fixture
def mock_document():
    """Mock document response."""
    return MagicMock(
        id=str(uuid.uuid4()),
        collection_id="collection-1",
        title="Test Document",
        content="This is test content for the document.",
        document_type="markdown",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        doc_metadata={"key": "value"},
    )


@pytest.fixture
def mock_other_user_document():
    """Document belonging to a different user."""
    return MagicMock(
        id=str(uuid.uuid4()),
        collection_id="collection-other",
        title="Other User Document",
        content="This belongs to another user.",
        document_type="markdown",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        doc_metadata={},
    )


class TestPATDocumentAccess:
    """Tests for PAT document access."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_pat_auth_context_has_collections(self, mock_pat_user, mock_collections):
        """Verify PAT context includes collection_ids and qdrant_collections."""
        set_pat_info(mock_pat_user)

        with patch("app.tools.context.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_by_user.return_value = mock_collections
            mock_repo_factory.return_value = mock_repo

            from app.tools.context import get_auth_context
            auth = get_auth_context()

            assert auth["auth_type"] == "pat"
            assert auth["user_id"] == "user-123"
            assert "collection_ids" in auth
            assert "qdrant_collections" in auth
            assert len(auth["collection_ids"]) == 2
            assert auth["collection_ids"] == ["collection-1", "collection-2"]
            assert auth["qdrant_collections"] == ["qdrant-coll-1", "qdrant-coll-2"]

    @pytest.mark.asyncio
    async def test_pat_can_get_document_without_collection(self, mock_pat_user, mock_document, mock_collections):
        """PAT can get document by ID without specifying collection."""
        set_pat_info(mock_pat_user)

        with patch("app.tools.context.get_collection_repository") as mock_repo_factory, \
             patch("app.tools.document_tools.get_document_repository") as doc_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_by_user.return_value = mock_collections
            mock_repo_factory.return_value = mock_repo

            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id_for_user.return_value = mock_document
            doc_repo_factory.return_value = mock_doc_repo

            result = await get_document(GetDocumentInput(document_id=mock_document.id))

            assert result is not None
            assert result.id == mock_document.id
            mock_doc_repo.get_by_id_for_user.assert_called_once_with(mock_document.id, "user-123")

    @pytest.mark.asyncio
    async def test_pat_cannot_access_other_user_document(self, mock_pat_user, mock_other_user_document, mock_collections):
        """PAT cannot access documents from other users."""
        set_pat_info(mock_pat_user)

        with patch("app.tools.context.get_collection_repository") as mock_repo_factory, \
             patch("app.tools.document_tools.get_document_repository") as doc_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_by_user.return_value = mock_collections
            mock_repo_factory.return_value = mock_repo

            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id_for_user.return_value = None
            doc_repo_factory.return_value = mock_doc_repo

            result = await get_document(GetDocumentInput(document_id=mock_other_user_document.id))

            assert result is None

    @pytest.mark.asyncio
    async def test_pat_can_list_all_documents(self, mock_pat_user, mock_document, mock_collections):
        """PAT can list all documents across all user collections."""
        set_pat_info(mock_pat_user)

        with patch("app.tools.context.get_collection_repository") as mock_repo_factory, \
             patch("app.tools.document_tools.get_document_repository") as doc_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_by_user.return_value = mock_collections
            mock_repo_factory.return_value = mock_repo

            mock_doc_repo = MagicMock()
            mock_doc_repo.list_all_for_user.return_value = [mock_document]
            doc_repo_factory.return_value = mock_doc_repo

            result = await list_documents(ListDocumentsInput(limit=50, offset=0))

            assert len(result.documents) == 1
            mock_doc_repo.list_all_for_user.assert_called_once_with("user-123", limit=50, offset=0)

    @pytest.mark.asyncio
    async def test_pat_can_update_document_without_collection(self, mock_pat_user, mock_document, mock_collections, mock_chunks=None):
        """PAT can update document by ID without specifying collection."""
        set_pat_info(mock_pat_user)

        mock_chunks = [
            {
                "chunk_index": 0,
                "content": "Updated content",
                "token_count": 10,
                "title": "Updated Title",
            }
        ]
        mock_embeddings = [[0.1] * 4096]

        with patch("app.tools.context.get_collection_repository") as mock_repo_factory, \
             patch("app.tools.document_tools.get_document_repository") as doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory:
            mock_repo = MagicMock()
            mock_repo.list_by_user.return_value = mock_collections
            mock_repo_factory.return_value = mock_repo

            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id_for_user.return_value = mock_document
            mock_doc_repo.update.return_value = mock_document
            doc_repo_factory.return_value = mock_doc_repo

            mock_qdrant = MagicMock()
            mock_qdrant.upsert_chunks.return_value = ["point-1"]
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

    @pytest.mark.asyncio
    async def test_pat_can_delete_document_without_collection(self, mock_pat_user, mock_document, mock_collections):
        """PAT can delete document by ID without specifying collection."""
        set_pat_info(mock_pat_user)

        with patch("app.tools.context.get_collection_repository") as mock_repo_factory, \
             patch("app.tools.document_tools.get_document_repository") as doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory:
            mock_repo = MagicMock()
            mock_repo.list_by_user.return_value = mock_collections
            mock_repo_factory.return_value = mock_repo

            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id_for_user.return_value = mock_document
            mock_doc_repo.delete.return_value = True
            doc_repo_factory.return_value = mock_doc_repo

            mock_qdrant = MagicMock()
            mock_qdrant_factory.return_value = mock_qdrant

            result = await delete_document(DeleteDocumentInput(document_id=mock_document.id))

            assert result.success is True
            mock_doc_repo.get_by_id_for_user.assert_called_once_with(mock_document.id, "user-123")

    @pytest.mark.asyncio
    async def test_pat_searches_all_collections(self, mock_pat_user, mock_collections):
        """PAT search returns results from all user collections."""
        set_pat_info(mock_pat_user)

        with patch("app.tools.context.get_collection_repository") as mock_repo_factory, \
             patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory:
            mock_repo = MagicMock()
            mock_repo.list_by_user.return_value = mock_collections
            mock_repo_factory.return_value = mock_repo

            mock_embedding = MagicMock()
            mock_embedding.embed_query = AsyncMock(return_value=[0.1] * 4096)
            mock_embedding_factory.return_value = mock_embedding

            mock_qdrant = MagicMock()
            mock_qdrant.search_multi.return_value = [
                {
                    "document_id": "doc-1",
                    "title": "Doc 1",
                    "chunk_index": 0,
                    "content": "Content 1",
                    "score": 0.95,
                    "token_count": 10,
                    "collection": "qdrant-coll-1",
                },
                {
                    "document_id": "doc-2",
                    "title": "Doc 2",
                    "chunk_index": 0,
                    "content": "Content 2",
                    "score": 0.90,
                    "token_count": 10,
                    "collection": "qdrant-coll-2",
                },
            ]
            mock_qdrant_factory.return_value = mock_qdrant

            result = await search_documents(SearchDocumentsInput(query="test", max_results=5))

            assert result.total_results == 2
            mock_qdrant.search_multi.assert_called_once()
            call_args = mock_qdrant.search_multi.call_args
            assert call_args[1]["collection_names"] == ["qdrant-coll-1", "qdrant-coll-2"]


class TestJWTDocumentAccess:
    """Tests for JWT user document access."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_jwt_auth_context_has_collections(self, mock_collections):
        """Verify JWT context includes collection_ids and qdrant_collections."""
        from app.tools.context import set_user_info, get_auth_context
        from app.db.models import Scope

        mock_jwt_user = {
            "id": "user-123",
            "user_id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "scopes": [Scope.READ, Scope.WRITE],
            "is_superuser": False,
        }
        set_user_info(mock_jwt_user)

        with patch("app.tools.context.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_by_user.return_value = mock_collections
            mock_repo_factory.return_value = mock_repo

            auth = get_auth_context()

            assert auth["auth_type"] == "jwt"
            assert auth["user_id"] == "user-123"
            assert "collection_ids" in auth
            assert "qdrant_collections" in auth
            assert len(auth["collection_ids"]) == 2

    @pytest.mark.asyncio
    async def test_jwt_can_list_all_documents(self, mock_collections):
        """JWT can list all documents across all their collections."""
        from app.tools.context import set_user_info
        from app.db.models import Scope

        mock_jwt_user = {
            "id": "user-123",
            "user_id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "scopes": [Scope.READ, Scope.WRITE],
            "is_superuser": False,
        }
        set_user_info(mock_jwt_user)

        mock_doc = MagicMock(
            id="doc-1",
            collection_id="collection-1",
            title="Test Doc",
            content="Content",
            document_type="markdown",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            doc_metadata={},
        )

        with patch("app.tools.context.get_collection_repository") as mock_repo_factory, \
             patch("app.tools.document_tools.get_document_repository") as doc_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_by_user.return_value = mock_collections
            mock_repo_factory.return_value = mock_repo

            mock_doc_repo = MagicMock()
            mock_doc_repo.list_all_for_user.return_value = [mock_doc]
            doc_repo_factory.return_value = mock_doc_repo

            result = await list_documents(ListDocumentsInput(limit=50, offset=0))

            assert len(result.documents) == 1
            mock_doc_repo.list_all_for_user.assert_called_once_with("user-123", limit=50, offset=0)

    @pytest.mark.asyncio
    async def test_jwt_can_get_document_without_collection(self, mock_collections):
        """JWT can get document by ID without specifying collection."""
        from app.tools.context import set_user_info
        from app.db.models import Scope

        mock_jwt_user = {
            "id": "user-123",
            "user_id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "scopes": [Scope.READ, Scope.WRITE],
            "is_superuser": False,
        }
        set_user_info(mock_jwt_user)

        mock_doc = MagicMock(
            id="doc-1",
            collection_id="collection-1",
            title="Test Doc",
            content="Content",
            document_type="markdown",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            doc_metadata={},
        )

        with patch("app.tools.context.get_collection_repository") as mock_repo_factory, \
             patch("app.tools.document_tools.get_document_repository") as doc_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_by_user.return_value = mock_collections
            mock_repo_factory.return_value = mock_repo

            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id_for_user.return_value = mock_doc
            doc_repo_factory.return_value = mock_doc_repo

            result = await get_document(GetDocumentInput(document_id="doc-1"))

            assert result is not None
            assert result.id == "doc-1"
            mock_doc_repo.get_by_id_for_user.assert_called_once_with("doc-1", "user-123")
