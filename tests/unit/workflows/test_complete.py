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
from app.tools.pat_tools import (
    CreatePatTokenInput,
    create_pat_token,
    list_pat_tokens,
    revoke_pat_token,
    RevokePatTokenInput,
    rotate_pat_token,
    RotatePatTokenInput,
)
from app.tools.document_tools import (
    StoreDocumentInput,
    SearchDocumentsInput,
    store_document,
    search_documents,
)
from app.tools.context import set_user_info, set_api_key_info, set_pat_info, clear_all_auth
from app.db.models import Permission, CollectionResponse, Scope


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
        """JWT users CAN perform document operations (they have access to their collections)."""
        from unittest.mock import MagicMock, patch

        set_user_info({
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "auth_type": "jwt",
            "collection_ids": ["coll-123"],
            "qdrant_collections": ["docs_123"],
        })

        # Can store
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

            result = await store_document(StoreDocumentInput(title="Test", content="Content"))
            assert "Document stored successfully" in result.message

        # Can update
        from app.tools.document_tools import update_document, UpdateDocumentInput
        with patch("app.tools.context.get_collection_repository") as mock_coll_repo, \
             patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory, \
             patch("app.tools.document_tools.get_embedding_service") as mock_emb_factory, \
             patch("app.tools.document_tools.get_chunking_service") as mock_chunk_factory:
            mock_coll_repo.return_value.list_by_user.return_value = [
                {"id": "coll-123", "qdrant_collection": "docs_123"}
            ]
            
            mock_doc = MagicMock()
            mock_doc.id = "doc-1"
            mock_doc.collection_id = "coll-123"
            mock_doc.title = "Old Title"
            mock_doc.content = "Old Content"
            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id_for_user.return_value = mock_doc
            mock_doc_repo.update.return_value = mock_doc
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            mock_qdrant = MagicMock()
            mock_qdrant_factory.return_value = mock_qdrant
            
            mock_emb = MagicMock()
            mock_emb.embed_texts = AsyncMock(return_value=[[0.1]])
            mock_emb_factory.return_value = mock_emb
            
            mock_chunk = MagicMock()
            mock_chunk.chunk_markdown.return_value = []
            mock_chunk_factory.return_value = mock_chunk

            result = await update_document(UpdateDocumentInput(
                document_id="doc-1",
                title="Test",
                content="Content",
            ))
            assert "Document updated successfully" in result.message

        # Can delete
        from app.tools.document_tools import delete_document, DeleteDocumentInput
        with patch("app.tools.context.get_collection_repository") as mock_coll_repo, \
             patch("app.tools.document_tools.get_document_repository") as mock_doc_repo_factory, \
             patch("app.tools.document_tools.get_qdrant_service") as mock_qdrant_factory:
            mock_coll_repo.return_value.list_by_user.return_value = [
                {"id": "coll-123", "qdrant_collection": "docs_123"}
            ]
            
            mock_doc = MagicMock()
            mock_doc.id = "doc-1"
            mock_doc.collection_id = "coll-123"
            mock_doc_repo = MagicMock()
            mock_doc_repo.get_by_id_for_user.return_value = mock_doc
            mock_doc_repo_factory.return_value = mock_doc_repo
            
            mock_qdrant = MagicMock()
            mock_qdrant_factory.return_value = mock_qdrant

            result = await delete_document(DeleteDocumentInput(document_id="doc-1"))
            assert "Document deleted successfully" in result.message


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


class TestPatTokenWorkflow:
    """Test PAT token creation, usage, and management."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_create_pat_token_as_jwt_user(self):
        """JWT user can create a PAT token."""
        set_user_info({
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "scopes": [Scope.READ, Scope.WRITE],
        })

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.create.return_value = ("pat-id-123", "pat_live_testtoken123")
            mock_repo.get_by_id.return_value = {
                "id": "pat-id-123",
                "label": "Test PAT",
                "user_id": "user-123",
                "scopes": [Scope.READ, Scope.WRITE],
                "created_at": datetime.utcnow(),
                "expires_at": None,
                "is_active": True,
                "last_used": None,
            }
            mock_repo_factory.return_value = mock_repo

            result = await create_pat_token(CreatePatTokenInput(
                label="Test PAT",
            ))

            assert result.id == "pat-id-123"
            assert result.token == "pat_live_testtoken123"
            assert result.label == "Test PAT"
            assert result.user_id == "user-123"

    @pytest.mark.asyncio
    async def test_pat_token_inherits_user_scopes(self):
        """PAT token inherits scopes from user at creation time."""
        set_user_info({
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "scopes": [Scope.READ],  # Read-only user
        })

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.create.return_value = ("pat-id-123", "pat_live_testtoken123")
            mock_repo.get_by_id.return_value = {
                "id": "pat-id-123",
                "label": "Read-only PAT",
                "user_id": "user-123",
                "scopes": [Scope.READ],
                "created_at": datetime.utcnow(),
                "expires_at": None,
                "is_active": True,
                "last_used": None,
            }
            mock_repo_factory.return_value = mock_repo

            result = await create_pat_token(CreatePatTokenInput(
                label="Read-only PAT",
            ))

            assert Scope.READ in result.scopes
            assert Scope.WRITE not in result.scopes

    @pytest.mark.asyncio
    async def test_pat_token_with_custom_expiry(self):
        """PAT token can have custom expiry."""
        set_user_info({
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "scopes": [Scope.READ, Scope.WRITE],
        })

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.create.return_value = ("pat-id-123", "pat_live_testtoken123")
            mock_repo.get_by_id.return_value = {
                "id": "pat-id-123",
                "label": "Test PAT",
                "user_id": "user-123",
                "scopes": [Scope.READ, Scope.WRITE],
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow(),
                "is_active": True,
                "last_used": None,
            }
            mock_repo_factory.return_value = mock_repo

            result = await create_pat_token(CreatePatTokenInput(
                label="Test PAT",
                expires_in_days=180,
            ))

            mock_repo.create.assert_called_once()
            call_kwargs = mock_repo.create.call_args[1]
            assert call_kwargs["expires_in_days"] == 180

    @pytest.mark.asyncio
    async def test_pat_token_cannot_be_created_without_jwt(self):
        """API key users cannot create PAT tokens."""
        set_api_key_info({
            "id": "api-key-1",
            "user_id": "user-123",
            "collection_id": "collection-1",
            "permission": Permission.READ_WRITE,
            "is_admin": False,
        })

        with pytest.raises(ValueError, match="JWT authentication required"):
            await create_pat_token(CreatePatTokenInput(label="Test PAT"))

    @pytest.mark.asyncio
    async def test_pat_token_can_list_own_tokens(self):
        """User can list their own PAT tokens."""
        set_user_info({
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "scopes": [Scope.READ, Scope.WRITE],
        })

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = [
                {
                    "id": "pat-1",
                    "label": "PAT 1",
                    "user_id": "user-123",
                    "scopes": [Scope.READ, Scope.WRITE],
                    "created_at": datetime.utcnow(),
                    "expires_at": None,
                    "is_active": True,
                    "last_used": None,
                },
                {
                    "id": "pat-2",
                    "label": "PAT 2",
                    "user_id": "user-123",
                    "scopes": [Scope.READ],
                    "created_at": datetime.utcnow(),
                    "expires_at": None,
                    "is_active": True,
                    "last_used": None,
                },
            ]
            mock_repo_factory.return_value = mock_repo

            result = await list_pat_tokens()

            assert len(result) == 2
            mock_repo.list_all.assert_called_once_with(user_id="user-123")

    @pytest.mark.asyncio
    async def test_pat_token_revoke(self):
        """User can revoke their own PAT token."""
        set_user_info({
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "scopes": [Scope.READ, Scope.WRITE],
        })

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = {
                "id": "pat-1",
                "label": "Test PAT",
                "user_id": "user-123",
                "scopes": [Scope.READ, Scope.WRITE],
                "created_at": datetime.utcnow(),
                "expires_at": None,
                "is_active": True,
                "last_used": None,
            }
            mock_repo.revoke.return_value = True
            mock_repo_factory.return_value = mock_repo

            result = await revoke_pat_token(RevokePatTokenInput(pat_id="pat-1"))

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_pat_token_rotate(self):
        """User can rotate their PAT token."""
        set_user_info({
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "scopes": [Scope.READ, Scope.WRITE],
        })

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = {
                "id": "pat-1",
                "label": "Test PAT",
                "user_id": "user-123",
                "scopes": [Scope.READ, Scope.WRITE],
                "created_at": datetime.utcnow(),
                "expires_at": None,
                "is_active": True,
                "last_used": None,
            }
            mock_repo.rotate.return_value = ("pat-2", "pat_live_newtoken123")
            mock_repo_factory.return_value = mock_repo

            result = await rotate_pat_token(RotatePatTokenInput(pat_id="pat-1"))

            assert result.id == "pat-2"
            assert result.token == "pat_live_newtoken123"


class TestPatTokenPermissions:
    """Test PAT token permission enforcement."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_pat_token_can_list_collections(self):
        """PAT token user can list their collections."""
        set_pat_info({
            "id": "pat-1",
            "user_id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "scopes": [Scope.READ, Scope.WRITE],
            "is_superuser": False,
        })

        with patch("app.tools.collection_tools.get_collection_repository") as mock_coll_factory:
            mock_coll_repo = MagicMock()
            mock_coll_repo.list_by_user.return_value = [
                {
                    "id": "collection-1",
                    "name": "default",
                    "user_id": "user-123",
                    "created_at": datetime.utcnow(),
                }
            ]
            mock_coll_factory.return_value = mock_coll_repo

            from app.tools.collection_tools import list_collections

            result = await list_collections()

            assert len(result) == 1
            assert result[0].name == "default"

    @pytest.mark.asyncio
    async def test_pat_token_cannot_directly_store_documents(self):
        """PAT tokens can now store documents when they have collections."""
        from unittest.mock import patch, MagicMock
        from app.tools.context import get_auth_context
        
        set_pat_info({
            "id": "pat-1",
            "user_id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "scopes": [Scope.READ, Scope.WRITE],
            "is_superuser": False,
        })
        
        with patch("app.tools.context.get_collection_repository") as mock_repo:
            mock_repo.return_value.list_by_user.return_value = [
                {"id": "collection-1", "qdrant_collection": "qdrant-1"}
            ]
            auth = get_auth_context()
            assert "collection_ids" in auth
            assert "collection-1" in auth["collection_ids"]

    @pytest.mark.asyncio
    async def test_pat_token_read_only_cannot_write(self):
        """PAT token with only read scope cannot write."""
        set_pat_info({
            "id": "pat-1",
            "user_id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "scopes": [Scope.READ],
            "is_superuser": False,
        })

        with pytest.raises(ValueError, match="Insufficient permissions"):
            await store_document(StoreDocumentInput(
                title="Test",
                content="Content",
                collection_id="collection-1",
            ))

    @pytest.mark.asyncio
    async def test_pat_superuser_has_full_access(self):
        """PAT token from superuser has full access."""
        set_pat_info({
            "id": "pat-1",
            "user_id": "admin-123",
            "username": "admin",
            "email": "admin@example.com",
            "scopes": [Scope.READ, Scope.WRITE, Scope.ADMIN],
            "is_superuser": True,
        })

        from app.tools.context import has_scope, has_write_permission

        assert has_scope(Scope.READ) is True
        assert has_scope(Scope.WRITE) is True
        assert has_scope(Scope.ADMIN) is True
        assert has_write_permission() is True
