"""
Comprehensive tests for collection management tools.
Tests create, list, get, delete, rename operations with various auth contexts.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.tools.collection_tools import (
    CreateCollectionInput,
    GetCollectionInput,
    DeleteCollectionInput,
    RenameCollectionInput,
    create_collection,
    list_collections,
    get_collection,
    delete_collection,
    rename_collection,
)
from app.tools.context import set_user_info, set_api_key_info, clear_all_auth
from app.db.models import CollectionResponse, CollectionListResponse, Permission


@pytest.fixture
def mock_user_info():
    """Regular user with JWT auth."""
    return {
        "id": "user-123",
        "username": "testuser",
        "email": "test@example.com",
        "is_superuser": False,
    }


@pytest.fixture
def mock_admin_info():
    """Admin user with JWT auth."""
    return {
        "id": "admin-123",
        "username": "admin",
        "email": "admin@example.com",
        "is_superuser": True,
    }


@pytest.fixture
def mock_api_key_info():
    """API key auth (cannot manage collections)."""
    return {
        "id": "api-key-123",
        "user_id": "user-123",
        "collection_id": "collection-123",
        "permission": Permission.READ_WRITE,
        "is_admin": False,
        "auth_type": "api_key",
    }


@pytest.fixture
def mock_collection():
    """Mock collection data."""
    return {
        "id": "collection-123",
        "name": "default",
        "qdrant_collection": "qdrant-uuid-123",
        "user_id": "user-123",
        "document_count": 5,
        "api_key_count": 2,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def mock_collection_list():
    """Mock list of collections."""
    return [
        {
            "id": "collection-1",
            "name": "default",
            "qdrant_collection": "qdrant-1",
            "user_id": "user-123",
            "created_at": datetime.utcnow(),
        },
        {
            "id": "collection-2",
            "name": "work",
            "qdrant_collection": "qdrant-2",
            "user_id": "user-123",
            "created_at": datetime.utcnow(),
        },
    ]


class TestCreateCollection:
    """Tests for create_collection tool."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_create_collection_with_jwt(self, mock_user_info):
        """JWT user can create collections."""
        set_user_info(mock_user_info)

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.create.return_value = CollectionResponse(
                id="new-collection-id",
                name="personal",
                document_count=0,
                api_key_count=0,
                created_at=datetime.utcnow(),
            )
            mock_repo_factory.return_value = mock_repo

            result = await create_collection(CreateCollectionInput(name="personal"))

            assert result.id == "new-collection-id"
            assert result.name == "personal"
            mock_repo.create.assert_called_once_with(
                user_id=mock_user_info["id"],
                name="personal",
            )

    @pytest.mark.asyncio
    async def test_create_collection_with_api_key(self, mock_api_key_info):
        """API key auth cannot create collections directly (uses user_id from key)."""
        set_api_key_info(mock_api_key_info)

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.create.return_value = CollectionResponse(
                id="new-collection-id",
                name="new-collection",
                document_count=0,
                api_key_count=0,
                created_at=datetime.utcnow(),
            )
            mock_repo_factory.return_value = mock_repo

            result = await create_collection(CreateCollectionInput(name="new-collection"))

            # Should use user_id from API key context
            mock_repo.create.assert_called_once_with(
                user_id=mock_api_key_info["user_id"],
                name="new-collection",
            )


class TestListCollections:
    """Tests for list_collections tool."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_list_collections_with_jwt(self, mock_user_info, mock_collection_list):
        """JWT user can list their collections."""
        set_user_info(mock_user_info)

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_by_user.return_value = mock_collection_list
            mock_repo_factory.return_value = mock_repo

            result = await list_collections()

            assert len(result) == 2
            assert all(isinstance(c, CollectionListResponse) for c in result)
            assert result[0].name == "default"
            assert result[1].name == "work"
            mock_repo.list_by_user.assert_called_once_with(mock_user_info["id"])

    @pytest.mark.asyncio
    async def test_list_collections_with_api_key_denied(self, mock_api_key_info):
        """API key auth cannot list collections (requires JWT)."""
        set_api_key_info(mock_api_key_info)

        with pytest.raises(ValueError, match="JWT authentication required"):
            await list_collections()

    @pytest.mark.asyncio
    async def test_list_collections_not_authenticated(self):
        """Unauthenticated request denied."""
        with pytest.raises(ValueError, match="JWT authentication required"):
            await list_collections()


class TestGetCollection:
    """Tests for get_collection tool."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_get_collection_owner(self, mock_user_info, mock_collection):
        """Collection owner can get collection details."""
        set_user_info(mock_user_info)

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_collection
            mock_repo_factory.return_value = mock_repo

            result = await get_collection(GetCollectionInput(collection_id="collection-123"))

            assert result.id == "collection-123"
            assert result.name == "default"
            assert result.document_count == 5
            assert result.api_key_count == 2

    @pytest.mark.asyncio
    async def test_get_collection_not_owner_denied(self, mock_user_info, mock_collection):
        """Non-owner cannot get collection details."""
        set_user_info(mock_user_info)
        mock_collection["user_id"] = "different-user-id"

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_collection
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="Collection not found"):
                await get_collection(GetCollectionInput(collection_id="collection-123"))

    @pytest.mark.asyncio
    async def test_get_collection_admin_can_access_others(self, mock_admin_info, mock_collection):
        """Admin can get any collection's details."""
        set_user_info(mock_admin_info)
        mock_collection["user_id"] = "different-user-id"

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_collection
            mock_repo_factory.return_value = mock_repo

            result = await get_collection(GetCollectionInput(collection_id="collection-123"))

            assert result.id == "collection-123"

    @pytest.mark.asyncio
    async def test_get_collection_not_found(self, mock_user_info):
        """Non-existent collection returns error."""
        set_user_info(mock_user_info)

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="Collection not found"):
                await get_collection(GetCollectionInput(collection_id="nonexistent"))


class TestDeleteCollection:
    """Tests for delete_collection tool."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_delete_collection_no_api_keys(self, mock_user_info, mock_collection):
        """Can delete collection with no active API keys."""
        set_user_info(mock_user_info)
        mock_collection["api_key_count"] = 0

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_collection
            mock_repo.delete.return_value = True
            mock_repo_factory.return_value = mock_repo

            result = await delete_collection(DeleteCollectionInput(collection_id="collection-123"))

            assert result["success"] is True
            mock_repo.delete.assert_called_once_with("collection-123")

    @pytest.mark.asyncio
    async def test_delete_collection_with_api_keys_denied(self, mock_user_info, mock_collection):
        """Cannot delete collection with active API keys."""
        set_user_info(mock_user_info)
        mock_collection["api_key_count"] = 3

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_collection
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="Cannot delete collection with active API keys"):
                await delete_collection(DeleteCollectionInput(collection_id="collection-123"))

            mock_repo.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_collection_not_owner_denied(self, mock_user_info, mock_collection):
        """Non-owner cannot delete collection."""
        set_user_info(mock_user_info)
        mock_collection["user_id"] = "different-user-id"
        mock_collection["api_key_count"] = 0

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_collection
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="Collection not found"):
                await delete_collection(DeleteCollectionInput(collection_id="collection-123"))

    @pytest.mark.asyncio
    async def test_delete_collection_admin_can_delete_others(self, mock_admin_info, mock_collection):
        """Admin can delete any collection."""
        set_user_info(mock_admin_info)
        mock_collection["user_id"] = "different-user-id"
        mock_collection["api_key_count"] = 0

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_collection
            mock_repo.delete.return_value = True
            mock_repo_factory.return_value = mock_repo

            result = await delete_collection(DeleteCollectionInput(collection_id="collection-123"))

            assert result["success"] is True


class TestRenameCollection:
    """Tests for rename_collection tool."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_rename_collection_owner(self, mock_user_info, mock_collection):
        """Collection owner can rename."""
        set_user_info(mock_user_info)

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_collection
            mock_repo.rename.return_value = CollectionResponse(
                id="collection-123",
                name="renamed",
                document_count=5,
                api_key_count=2,
                created_at=datetime.utcnow(),
            )
            mock_repo_factory.return_value = mock_repo

            result = await rename_collection(RenameCollectionInput(
                collection_id="collection-123",
                name="renamed",
            ))

            assert result.name == "renamed"
            mock_repo.rename.assert_called_once_with("collection-123", "renamed")

    @pytest.mark.asyncio
    async def test_rename_collection_not_owner_denied(self, mock_user_info, mock_collection):
        """Non-owner cannot rename collection."""
        set_user_info(mock_user_info)
        mock_collection["user_id"] = "different-user-id"

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_collection
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="Collection not found"):
                await rename_collection(RenameCollectionInput(
                    collection_id="collection-123",
                    name="renamed",
                ))

    @pytest.mark.asyncio
    async def test_rename_collection_not_found(self, mock_user_info):
        """Non-existent collection returns error."""
        set_user_info(mock_user_info)

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="Collection not found"):
                await rename_collection(RenameCollectionInput(
                    collection_id="nonexistent",
                    name="renamed",
                ))


class TestCollectionOwnership:
    """Tests for collection ownership and access control."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_user_can_only_see_own_collections(self, mock_user_info):
        """User can only list their own collections."""
        set_user_info(mock_user_info)

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_by_user.return_value = []
            mock_repo_factory.return_value = mock_repo

            await list_collections()

            mock_repo.list_by_user.assert_called_once_with(mock_user_info["id"])

    @pytest.mark.asyncio
    async def test_user_cannot_access_other_user_collection(self, mock_user_info, mock_collection):
        """User cannot access another user's collection."""
        set_user_info({
            "id": "different-user-id",
            "username": "other",
            "email": "other@example.com",
            "is_superuser": False,
        })

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_collection
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="Collection not found"):
                await get_collection(GetCollectionInput(collection_id="collection-123"))
