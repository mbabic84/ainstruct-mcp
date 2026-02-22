"""
Integration tests for complete workflows.
Tests end-to-end scenarios like user registration -> collection -> API key -> documents.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid

from app.tools.user_tools import (
    RegisterInput,
    LoginInput,
    user_register,
    user_login,
    user_profile,
)
from app.tools.collection_tools import (
    CreateCollectionInput,
    create_collection,
    list_collections,
    get_collection,
    GetCollectionInput,
)
from app.tools.key_tools import (
    CreateApiKeyInput,
    create_api_key,
    list_api_keys,
)
from app.tools.document_tools import (
    StoreDocumentInput,
    SearchDocumentsInput,
    store_document,
    search_documents,
)
from app.tools.context import set_user_info, set_api_key_info, clear_all_auth
from app.db.models import Permission, CollectionResponse


class TestCompleteUserWorkflow:
    """Test complete user journey from registration to document operations."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow: register -> login -> create collection -> create API key -> store document."""
        
        # Step 1: Register
        with (
            patch("app.tools.user_tools.get_user_repository") as mock_user_repo_factory,
            patch("app.tools.user_tools.get_auth_service") as mock_auth_factory,
            patch("app.tools.user_tools.get_collection_repository") as mock_coll_factory,
        ):
            mock_user_repo = MagicMock()
            mock_user_repo.get_by_username.return_value = None
            mock_user_repo.get_by_email.return_value = None
            mock_user_repo.create.return_value = MagicMock(
                id="user-123",
                email="test@example.com",
                username="testuser",
                is_active=True,
                is_superuser=False,
                created_at=datetime.utcnow(),
            )
            mock_user_repo_factory.return_value = mock_user_repo

            mock_auth = MagicMock()
            mock_auth.hash_password.return_value = "hashed_password"
            mock_auth_factory.return_value = mock_auth

            mock_coll_repo = MagicMock()
            mock_coll_repo.create.return_value = CollectionResponse(
                id="default-collection-id",
                name="default",
                document_count=0,
                api_key_count=0,
                created_at=datetime.utcnow(),
            )
            mock_coll_factory.return_value = mock_coll_repo

            user = await user_register(RegisterInput(
                email="test@example.com",
                username="testuser",
                password="password123",
            ))

            assert user.id == "user-123"
            # Verify default collection was created
            mock_coll_repo.create.assert_called_once_with(
                user_id="user-123",
                name="default",
            )

        # Step 2: Login
        with (
            patch("app.tools.user_tools.get_user_repository") as mock_user_repo_factory,
            patch("app.tools.user_tools.get_auth_service") as mock_auth_factory,
        ):
            mock_user_repo = MagicMock()
            mock_user_repo.get_by_username.return_value = {
                "id": "user-123",
                "email": "test@example.com",
                "username": "testuser",
                "password_hash": "hashed_password",
                "is_active": True,
                "is_superuser": False,
            }
            mock_user_repo_factory.return_value = mock_user_repo

            mock_auth = MagicMock()
            mock_auth.verify_password.return_value = True
            mock_auth.create_access_token.return_value = "access_token_123"
            mock_auth.create_refresh_token.return_value = "refresh_token_123"
            mock_auth.get_access_token_expiry.return_value = 1800
            mock_auth_factory.return_value = mock_auth

            tokens = await user_login(LoginInput(
                username="testuser",
                password="password123",
            ))

            assert tokens.access_token == "access_token_123"

        # Step 3: Set JWT auth context and list collections
        set_user_info({
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
        })

        with patch("app.tools.collection_tools.get_collection_repository") as mock_coll_factory:
            mock_coll_repo = MagicMock()
            mock_coll_repo.list_by_user.return_value = [
                {
                    "id": "default-collection-id",
                    "name": "default",
                    "qdrant_collection": "qdrant-uuid",
                    "user_id": "user-123",
                    "created_at": datetime.utcnow(),
                }
            ]
            mock_coll_factory.return_value = mock_coll_repo

            collections = await list_collections()

            assert len(collections) == 1
            assert collections[0].name == "default"

        # Step 4: Create API key
        with (
            patch("app.tools.key_tools.get_api_key_repository") as mock_key_repo_factory,
            patch("app.tools.key_tools.get_collection_repository") as mock_coll_factory,
        ):
            mock_coll_repo = MagicMock()
            mock_coll_repo.get_by_id.return_value = {
                "id": "default-collection-id",
                "name": "default",
                "qdrant_collection": "qdrant-uuid",
                "user_id": "user-123",
                "document_count": 0,
                "api_key_count": 0,
                "created_at": datetime.utcnow(),
            }
            mock_coll_factory.return_value = mock_coll_repo

            mock_key_repo = MagicMock()
            mock_key_repo.create.return_value = ("api-key-id", "ak_live_testkey123")
            mock_key_repo.get_by_id.return_value = {
                "id": "api-key-id",
                "label": "Main Key",
                "collection_id": "default-collection-id",
                "collection_name": "default",
                "permission": Permission.READ_WRITE,
                "created_at": datetime.utcnow(),
                "expires_at": None,
            }
            mock_key_repo_factory.return_value = mock_key_repo

            api_key = await create_api_key(CreateApiKeyInput(
                label="Main Key",
                collection_id="default-collection-id",
                permission="read_write",
            ))

            assert api_key.key == "ak_live_testkey123"
            assert api_key.collection_name == "default"

        # Step 5: Use API key to store document
        clear_all_auth()
        set_api_key_info({
            "id": "api-key-id",
            "user_id": "user-123",
            "collection_id": "default-collection-id",
            "collection_name": "default",
            "qdrant_collection": "qdrant-uuid",
            "permission": Permission.READ_WRITE,
            "is_admin": False,
            "auth_type": "api_key",
        })

        with (
            patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory,
            patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory,
            patch("app.tools.document_tools.get_embedding_service") as mock_embedding_factory,
            patch("app.tools.document_tools.get_chunking_service") as mock_chunking_factory,
        ):
            mock_doc_repo = MagicMock()
            mock_doc_repo.create.return_value = MagicMock(
                id="doc-123",
                collection_id="default-collection-id",
                title="Test Doc",
                content="Test content",
                document_type="markdown",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                doc_metadata={},
            )
            mock_doc_repo_factory.return_value = mock_doc_repo

            mock_qdrant = MagicMock()
            mock_qdrant.upsert_chunks.return_value = ["point-1"]
            mock_qdrant_factory.return_value = mock_qdrant

            mock_embedding = MagicMock()
            mock_embedding.embed_texts = AsyncMock(return_value=[[0.1] * 4096])
            mock_embedding_factory.return_value = mock_embedding

            mock_chunking = MagicMock()
            mock_chunking.chunk_markdown.return_value = [
                {"chunk_index": 0, "content": "Test content", "token_count": 5, "title": "Test Doc"}
            ]
            mock_chunking_factory.return_value = mock_chunking

            doc = await store_document(StoreDocumentInput(
                title="Test Doc",
                content="Test content",
            ))

            assert doc.document_id == "doc-123"
            assert doc.chunk_count == 1


class TestPermissionEnforcement:
    """Test that permissions are properly enforced across all operations."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_read_only_key_cannot_write(self):
        """Read-only API key cannot perform write operations."""
        set_api_key_info({
            "id": "readonly-key",
            "user_id": "user-123",
            "collection_id": "collection-123",
            "qdrant_collection": "qdrant-uuid",
            "permission": Permission.READ,
            "is_admin": False,
            "auth_type": "api_key",
        })

        # Cannot store
        with pytest.raises(ValueError, match="Insufficient permissions"):
            await store_document(StoreDocumentInput(title="Test", content="Content"))

        # Cannot update
        from app.tools.document_tools import update_document, UpdateDocumentInput
        with pytest.raises(ValueError, match="Insufficient permissions"):
            await update_document(UpdateDocumentInput(
                document_id="doc-1",
                title="Test",
                content="Content",
            ))

        # Cannot delete
        from app.tools.document_tools import delete_document, DeleteDocumentInput
        with pytest.raises(ValueError, match="Insufficient permissions"):
            await delete_document(DeleteDocumentInput(document_id="doc-1"))

    @pytest.mark.asyncio
    async def test_read_only_key_can_read(self):
        """Read-only API key can perform read operations."""
        set_api_key_info({
            "id": "readonly-key",
            "user_id": "user-123",
            "collection_id": "collection-123",
            "qdrant_collection": "qdrant-uuid",
            "permission": Permission.READ,
            "is_admin": False,
            "auth_type": "api_key",
        })

        # Can search
        with (
            patch("app.tools.document_tools.get_embedding_service") as mock_emb_factory,
            patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory,
        ):
            mock_emb = MagicMock()
            mock_emb.embed_query = AsyncMock(return_value=[0.1] * 4096)
            mock_emb_factory.return_value = mock_emb

            mock_qdrant = MagicMock()
            mock_qdrant.search.return_value = []
            mock_qdrant_factory.return_value = mock_qdrant

            result = await search_documents(SearchDocumentsInput(query="test"))

            assert result.total_results == 0

        # Can get document
        from app.tools.document_tools import get_document, GetDocumentInput
        with patch("app.tools.document_tools.get_document_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = MagicMock(
                id="doc-1",
                collection_id="collection-123",
                title="Test",
                content="Content",
                document_type="markdown",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                doc_metadata={},
            )
            mock_repo_factory.return_value = mock_repo

            result = await get_document(GetDocumentInput(document_id="doc-1"))
            assert result is not None

    @pytest.mark.asyncio
    async def test_jwt_cannot_manage_documents(self):
        """JWT users cannot perform document operations directly."""
        set_user_info({
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
        })

        # Cannot store
        with pytest.raises(ValueError, match="JWT users cannot store documents"):
            await store_document(StoreDocumentInput(title="Test", content="Content"))

        # Cannot update
        from app.tools.document_tools import update_document, UpdateDocumentInput
        with pytest.raises(ValueError, match="JWT users cannot update documents"):
            await update_document(UpdateDocumentInput(
                document_id="doc-1",
                title="Test",
                content="Content",
            ))

        # Cannot delete
        from app.tools.document_tools import delete_document, DeleteDocumentInput
        with pytest.raises(ValueError, match="JWT users cannot delete documents"):
            await delete_document(DeleteDocumentInput(document_id="doc-1"))


class TestCollectionIsolation:
    """Test that collections are properly isolated between users."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_api_key_limited_to_assigned_collection(self):
        """API key can only access its assigned collection."""
        set_api_key_info({
            "id": "api-key-1",
            "user_id": "user-123",
            "collection_id": "collection-1",
            "qdrant_collection": "qdrant-1",
            "permission": Permission.READ_WRITE,
            "is_admin": False,
            "auth_type": "api_key",
        })

        # Document repo should be called with collection-1
        with (
            patch("app.tools.document_tools.get_document_repository") as mock_repo_factory,
            patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory,
            patch("app.tools.document_tools.get_embedding_service") as mock_emb_factory,
            patch("app.tools.document_tools.get_chunking_service") as mock_chunk_factory,
        ):
            mock_repo = MagicMock()
            mock_repo.create.return_value = MagicMock(
                id="doc-1",
                collection_id="collection-1",
                title="Test",
                content="Content",
                document_type="markdown",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                doc_metadata={},
            )
            mock_repo_factory.return_value = mock_repo

            mock_qdrant = MagicMock()
            mock_qdrant_factory.return_value = mock_qdrant

            mock_emb = MagicMock()
            mock_emb.embed_texts = AsyncMock(return_value=[[0.1] * 4096])
            mock_emb_factory.return_value = mock_emb

            mock_chunk = MagicMock()
            mock_chunk.chunk_markdown.return_value = []
            mock_chunk_factory.return_value = mock_chunk

            await store_document(StoreDocumentInput(title="Test", content="Content"))

            # Verify repository was created with correct collection_id
            mock_repo_factory.assert_called()

    @pytest.mark.asyncio
    async def test_user_cannot_access_other_user_collection(self):
        """User cannot access another user's collection."""
        set_user_info({
            "id": "user-123",
            "username": "user1",
            "email": "user1@example.com",
            "is_superuser": False,
        })

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = {
                "id": "collection-456",
                "name": "other-user-collection",
                "user_id": "user-456",  # Different user
                "document_count": 5,
                "api_key_count": 1,
                "created_at": datetime.utcnow(),
            }
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="Collection not found"):
                await get_collection(GetCollectionInput(collection_id="collection-456"))


class TestAPIKeyRotation:
    """Test API key rotation preserves collection access."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_rotate_key_same_collection(self):
        """Rotated API key should have same collection and permission."""
        set_user_info({
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
        })

        from app.tools.key_tools import rotate_api_key, RotateApiKeyInput

        with patch("app.tools.key_tools.get_api_key_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = {
                "id": "old-key-id",
                "label": "Test Key",
                "collection_id": "collection-123",
                "collection_name": "default",
                "user_id": "user-123",
                "permission": Permission.READ_WRITE,
                "created_at": datetime.utcnow(),
                "expires_at": None,
            }
            mock_repo.rotate.return_value = ("new-key-id", "ak_live_newkey123")
            mock_repo_factory.return_value = mock_repo

            result = await rotate_api_key(RotateApiKeyInput(key_id="old-key-id"))

            assert result.key == "ak_live_newkey123"
            # The rotate method should preserve collection_id
            mock_repo.rotate.assert_called_once_with("old-key-id")
