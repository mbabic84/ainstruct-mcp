import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.tools.cat_tools import (
    CreateCatInput,
    RevokeCatInput,
    RotateCatInput,
    create_cat,
    list_cats,
    revoke_cat,
    rotate_cat,
)
from app.tools.context import set_user_info, set_cat_info, clear_all_auth
from app.db.models import Permission


@pytest.fixture
def mock_user_info():
    return {
        "id": "test-user-id",
        "username": "testuser",
        "email": "test@example.com",
        "is_superuser": False,
    }


@pytest.fixture
def mock_admin_info():
    return {
        "id": "admin-user-id",
        "username": "admin",
        "email": "admin@example.com",
        "is_superuser": True,
    }


@pytest.fixture
def mock_collection():
    return {
        "id": "collection-id-123",
        "name": "default",
        "qdrant_collection": "qdrant-uuid",
        "user_id": "test-user-id",
        "document_count": 0,
        "cat_count": 0,
        "created_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def mock_cat():
    return {
        "id": "key-id-123",
        "label": "Test CAT",
        "collection_id": "collection-id-123",
        "collection_name": "default",
        "qdrant_collection": "qdrant-uuid",
        "created_at": datetime.now(timezone.utc),
        "last_used": None,
        "is_active": True,
        "user_id": "test-user-id",
        "permission": Permission.READ_WRITE,
        "expires_at": None,
    }


class TestCreateCat:
    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_create_cat_success(self, mock_user_info, mock_cat, mock_collection):
        set_user_info(mock_user_info)

        with (
            patch("app.tools.cat_tools.get_cat_repository") as mock_repo_factory,
            patch("app.tools.cat_tools.get_collection_repository") as mock_coll_factory,
        ):
            mock_repo = MagicMock()
            mock_repo.create.return_value = ("key-id-123", "cat_live_testkey123")
            mock_repo.get_by_id.return_value = mock_cat
            mock_repo_factory.return_value = mock_repo

            mock_coll_repo = MagicMock()
            mock_coll_repo.get_by_id.return_value = mock_collection
            mock_coll_factory.return_value = mock_coll_repo

            result = await create_cat(CreateCatInput(
                label="My CAT",
                collection_id="collection-id-123",
                permission="read_write",
            ))

            assert result.id == "key-id-123"
            assert result.key == "cat_live_testkey123"
            assert result.label == "My CAT"
            assert result.permission == Permission.READ_WRITE
            assert result.collection_id == "collection-id-123"
            assert result.collection_name == "default"

    @pytest.mark.asyncio
    async def test_create_cat_invalid_permission(self, mock_user_info, mock_collection):
        set_user_info(mock_user_info)

        with (
            patch("app.tools.cat_tools.get_cat_repository") as mock_repo_factory,
            patch("app.tools.cat_tools.get_collection_repository") as mock_coll_factory,
        ):
            mock_coll_repo = MagicMock()
            mock_coll_repo.get_by_id.return_value = mock_collection
            mock_coll_factory.return_value = mock_coll_repo

            with pytest.raises(ValueError, match="Invalid permission"):
                await create_cat(CreateCatInput(
                    label="My CAT",
                    collection_id="collection-id-123",
                    permission="invalid_permission",
                ))

    @pytest.mark.asyncio
    async def test_create_cat_collection_not_found(self, mock_user_info):
        set_user_info(mock_user_info)

        with patch("app.tools.cat_tools.get_collection_repository") as mock_coll_factory:
            mock_coll_repo = MagicMock()
            mock_coll_repo.get_by_id.return_value = None
            mock_coll_factory.return_value = mock_coll_repo

            with pytest.raises(ValueError, match="Collection not found"):
                await create_cat(CreateCatInput(
                    label="My CAT",
                    collection_id="nonexistent-collection",
                    permission="read_write",
                ))

    @pytest.mark.asyncio
    async def test_create_cat_with_expiry(self, mock_user_info, mock_cat, mock_collection):
        set_user_info(mock_user_info)

        with (
            patch("app.tools.cat_tools.get_cat_repository") as mock_repo_factory,
            patch("app.tools.cat_tools.get_collection_repository") as mock_coll_factory,
        ):
            mock_repo = MagicMock()
            mock_repo.create.return_value = ("key-id-123", "cat_live_testkey123")
            mock_repo.get_by_id.return_value = mock_cat
            mock_repo_factory.return_value = mock_repo

            mock_coll_repo = MagicMock()
            mock_coll_repo.get_by_id.return_value = mock_collection
            mock_coll_factory.return_value = mock_coll_repo

            result = await create_cat(CreateCatInput(
                label="My CAT",
                collection_id="collection-id-123",
                permission="read",
                expires_in_days=30,
            ))

            mock_repo.create.assert_called_once()
            call_kwargs = mock_repo.create.call_args[1]
            assert call_kwargs["expires_in_days"] == 30
            assert call_kwargs["permission"] == Permission.READ


class TestListCats:
    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_list_cats_as_user(self, mock_user_info, mock_cat):
        set_user_info(mock_user_info)

        with patch("app.tools.cat_tools.get_cat_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = [mock_cat]
            mock_repo_factory.return_value = mock_repo

            result = await list_cats()

            assert len(result) == 1
            mock_repo.list_all.assert_called_once_with(user_id=mock_user_info["id"])

    @pytest.mark.asyncio
    async def test_list_cats_as_admin(self, mock_admin_info, mock_cat):
        set_user_info(mock_admin_info)

        with patch("app.tools.cat_tools.get_cat_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = [mock_cat]
            mock_repo_factory.return_value = mock_repo

            result = await list_cats()

            assert len(result) == 1
            mock_repo.list_all.assert_called_once_with(user_id=None)


class TestRevokeCat:
    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_revoke_own_cat(self, mock_user_info, mock_cat):
        set_user_info(mock_user_info)

        with patch("app.tools.cat_tools.get_cat_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_cat
            mock_repo.revoke.return_value = True
            mock_repo_factory.return_value = mock_repo

            result = await revoke_cat(RevokeCatInput(key_id="key-id-123"))

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_revoke_other_user_cat_forbidden(self, mock_user_info, mock_cat):
        set_user_info(mock_user_info)
        mock_cat["user_id"] = "different-user-id"

        with patch("app.tools.cat_tools.get_cat_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_cat
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="You can only revoke your own CAT tokens"):
                await revoke_cat(RevokeCatInput(key_id="key-id-123"))

    @pytest.mark.asyncio
    async def test_revoke_other_user_cat_as_admin(self, mock_admin_info, mock_cat):
        set_user_info(mock_admin_info)
        mock_cat["user_id"] = "different-user-id"

        with patch("app.tools.cat_tools.get_cat_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_cat
            mock_repo.revoke.return_value = True
            mock_repo_factory.return_value = mock_repo

            result = await revoke_cat(RevokeCatInput(key_id="key-id-123"))

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_cat(self, mock_user_info):
        set_user_info(mock_user_info)

        with patch("app.tools.cat_tools.get_cat_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="CAT token not found"):
                await revoke_cat(RevokeCatInput(key_id="nonexistent"))


class TestRotateCat:
    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_rotate_own_cat(self, mock_user_info, mock_cat):
        set_user_info(mock_user_info)

        with patch("app.tools.cat_tools.get_cat_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_cat
            mock_repo.rotate.return_value = ("new-key-id", "cat_live_newkey123")
            mock_repo_factory.return_value = mock_repo

            result = await rotate_cat(RotateCatInput(key_id="key-id-123"))

            assert result.id == "new-key-id"
            assert result.key == "cat_live_newkey123"

    @pytest.mark.asyncio
    async def test_rotate_other_user_cat_forbidden(self, mock_user_info, mock_cat):
        set_user_info(mock_user_info)
        mock_cat["user_id"] = "different-user-id"

        with patch("app.tools.cat_tools.get_cat_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_cat
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="You can only rotate your own CAT tokens"):
                await rotate_cat(RotateCatInput(key_id="key-id-123"))

    @pytest.mark.asyncio
    async def test_rotate_nonexistent_cat(self, mock_user_info):
        set_user_info(mock_user_info)

        with patch("app.tools.cat_tools.get_cat_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="CAT token not found"):
                await rotate_cat(RotateCatInput(key_id="nonexistent"))
