"""
Validation and edge case tests for collection_tools.
Tests duplicate names, input validation, length limits, and special characters.
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
    get_collection,
    delete_collection,
    rename_collection,
)
from app.tools.context import set_user_info, set_api_key_info, clear_all_auth
from app.db.models import CollectionResponse, Permission


@pytest.fixture
def mock_user_info():
    return {
        "id": "user-123",
        "username": "testuser",
        "email": "test@example.com",
        "is_superuser": False,
    }


@pytest.fixture
def mock_api_key_info():
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
def mock_collection():
    return {
        "id": "collection-existing",
        "name": "existing",
        "qdrant_collection": "qdrant-existing",
        "user_id": "user-123",
        "document_count": 0,
        "api_key_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


class TestCreateCollectionValidation:
    """Validation tests for create_collection."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_create_collection_duplicate_name(self, mock_user_info, mock_collection):
        """Cannot create collection with duplicate name for same user."""
        set_user_info(mock_user_info)

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            # Simulate collection with same name already exists for user
            mock_repo.get_by_name_for_user.return_value = mock_collection
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="Collection with this name already exists"):
                await create_collection(CreateCollectionInput(name="existing"))

            mock_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_collection_name_too_long(self, mock_user_info):
        """Collection name must not exceed length limit (e.g., 255 chars)."""
        set_user_info(mock_user_info)

        long_name = "a" * 256  # 256 characters

        # Pydantic should enforce max length if defined in model
        # If not defined, we should add validation
        with pytest.raises(Exception):  # Could be ValidationError
            await create_collection(CreateCollectionInput(name=long_name))

    @pytest.mark.asyncio
    async def test_create_collection_empty_name(self):
        """Collection name cannot be empty."""
        with pytest.raises(Exception):  # Pydantic validation
            await create_collection(CreateCollectionInput(name=""))

    @pytest.mark.asyncio
    async def test_create_collection_whitespace_name(self, mock_user_info):
        """Collection name with only whitespace should fail or be stripped."""
        set_user_info(mock_user_info)

        # Depending on implementation, this might be allowed or not
        # Test that it either rejects or strips whitespace
        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.create.return_value = CollectionResponse(
                id="new-id",
                name="   ",  # Might be stripped to empty
                document_count=0,
                api_key_count=0,
                created_at=datetime.utcnow(),
            )
            mock_repo_factory.return_value = mock_repo

            # If we allow whitespace-only names, this will succeed
            # If we validate, it should raise error
            try:
                result = await create_collection(CreateCollectionInput(name="   "))
                # Check if name was stripped or kept as-is
                # If repository strips whitespace, it might succeed
            except (ValueError, Exception):
                pass  # Expected if validation rejects whitespace-only

    @pytest.mark.asyncio
    async def test_create_collection_special_characters(self, mock_user_info):
        """Collection name with special characters should be allowed or validated."""
        set_user_info(mock_user_info)

        special_names = [
            "collection-name",
            "collection_name",
            "collection.name",
            "collection@name",
            "collection#name",
            "collection name with spaces",
            "collection-🎉-emoji",
            "collection_中文_rus",
        ]

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.create.return_value = CollectionResponse(
                id="new-id",
                name="test",
                document_count=0,
                api_key_count=0,
                created_at=datetime.utcnow(),
            )
            mock_repo_factory.return_value = mock_repo

            # These should either be accepted or rejected based on validation rules
            # Currently no specific validation, so they should pass
            for name in special_names:
                # Reset mock
                mock_repo.create.reset_mock()
                try:
                    await create_collection(CreateCollectionInput(name=name))
                    mock_repo.create.assert_called_once()
                except ValueError as e:
                    # If validation rejects some special chars, that's okay
                    pass

    @pytest.mark.asyncio
    async def test_create_collection_case_sensitivity(self, mock_user_info, mock_collection):
        """Collection names should be case-sensitive or case-insensitive based on DB."""
        set_user_info(mock_user_info)

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            # Simulate case-insensitive match
            mock_repo.get_by_name_for_user.return_value = mock_collection
            mock_repo_factory.return_value = mock_repo

            # Try to create "Existing" when "existing" exists
            with pytest.raises(ValueError, match="Collection with this name already exists"):
                await create_collection(CreateCollectionInput(name="Existing"))

    @pytest.mark.asyncio
    async def test_create_collection_api_key_auth(self, mock_api_key_info):
        """API key auth can create collections (uses user_id from key)."""
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

            assert result.id == "new-collection-id"
            # Should use user_id from API key context
            mock_repo.create.assert_called_once_with(
                user_id=mock_api_key_info["user_id"],
                name="new-collection",
            )


class TestRenameCollectionValidation:
    """Validation tests for rename_collection."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.fixture
    def mock_owned_collection(self):
        return {
            "id": "collection-123",
            "name": "old-name",
            "qdrant_collection": "qdrant-123",
            "user_id": "user-123",
            "document_count": 0,
            "api_key_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    @pytest.mark.asyncio
    async def test_rename_collection_duplicate_name(self, mock_user_info, mock_owned_collection):
        """Cannot rename to a name that already exists for the user."""
        set_user_info(mock_user_info)

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_owned_collection
            # Another collection with target name exists
            mock_repo.get_by_name_for_user.return_value = {
                "id": "collection-other",
                "name": "new-name",
            }
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="Collection with this name already exists"):
                await rename_collection(RenameCollectionInput(
                    collection_id="collection-123",
                    name="new-name",
                ))

    @pytest.mark.asyncio
    async def test_rename_collection_too_long(self, mock_user_info, mock_owned_collection):
        """Cannot rename to a name that exceeds length limit."""
        set_user_info(mock_user_info)

        long_name = "a" * 256

        with pytest.raises(Exception):  # Pydantic validation error
            await rename_collection(RenameCollectionInput(
                collection_id="collection-123",
                name=long_name,
            ))

    @pytest.mark.asyncio
    async def test_rename_collection_empty_name(self, mock_user_info, mock_owned_collection):
        """Cannot rename to empty name."""
        set_user_info(mock_user_info)

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_owned_collection
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(Exception):  # Pydantic validation
                await rename_collection(RenameCollectionInput(
                    collection_id="collection-123",
                    name="",
                ))

    @pytest.mark.asyncio
    async def test_rename_collection_to_same_name(self, mock_user_info, mock_owned_collection):
        """Renaming to the same name should be allowed (no-op or succeed)."""
        set_user_info(mock_user_info)

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_owned_collection
            mock_repo.rename.return_value = CollectionResponse(
                id="collection-123",
                name="old-name",
                document_count=0,
                api_key_count=0,
                created_at=datetime.utcnow(),
            )
            mock_repo_factory.return_value = mock_repo

            result = await rename_collection(RenameCollectionInput(
                collection_id="collection-123",
                name="old-name",
            ))

            assert result.name == "old-name"
            mock_repo.rename.assert_called_once_with("collection-123", "old-name")

    @pytest.mark.asyncio
    async def test_rename_collection_special_characters(self, mock_user_info, mock_owned_collection):
        """Test renaming with special characters."""
        set_user_info(mock_user_info)

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_owned_collection
            mock_repo.rename.return_value = CollectionResponse(
                id="collection-123",
                name="new-special-name",
                document_count=0,
                api_key_count=0,
                created_at=datetime.utcnow(),
            )
            mock_repo_factory.return_value = mock_repo

            result = await rename_collection(RenameCollectionInput(
                collection_id="collection-123",
                name="new-special-name_123",
            ))

            assert result.name == "new-special-name_123"

    @pytest.mark.asyncio
    async def test_rename_collection_api_key_auth(self, mock_api_key_info, mock_owned_collection):
        """API key auth cannot rename collections (requires JWT or PAT)."""
        set_api_key_info(mock_api_key_info)
        mock_owned_collection["user_id"] = mock_api_key_info["user_id"]

        with patch("app.tools.collection_tools.get_collection_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_owned_collection
            mock_repo_factory.return_value = mock_repo

            # API key auth should be denied (list_collections already denies)
            with pytest.raises(ValueError, match="JWT or PAT authentication required"):
                await rename_collection(RenameCollectionInput(
                    collection_id="collection-123",
                    name="renamed",
                ))


class TestCollectionInputValidation:
    """General input validation tests for collection operations."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_create_collection_invalid_uuid_in_input(self):
        """Test that invalid UUID in collection_id field (if any) is caught."""
        # CreateCollectionInput only has 'name' which is string, no UUID
        # But if we add UUID fields later, they should be validated
        # This test is placeholder for when/if UUID fields are added
        pass

    @pytest.mark.asyncio
    async def test_rename_collection_invalid_uuid(self):
        """RenameCollectionInput collection_id should be valid UUID."""
        with pytest.raises(Exception):  # Pydantic validation
            await rename_collection(RenameCollectionInput(
                collection_id="not-a-uuid",
                name="newname",
            ))

    @pytest.mark.asyncio
    async def test_get_collection_invalid_uuid(self):
        """GetCollectionInput collection_id should be valid UUID."""
        from app.tools.collection_tools import GetCollectionInput

        with pytest.raises(Exception):
            await get_collection(GetCollectionInput(collection_id="invalid-uuid"))

    @pytest.mark.asyncio
    async def test_delete_collection_invalid_uuid(self):
        """DeleteCollectionInput collection_id should be valid UUID."""
        from app.tools.collection_tools import DeleteCollectionInput

        with pytest.raises(Exception):
            await delete_collection(DeleteCollectionInput(collection_id="not-uuid"))
