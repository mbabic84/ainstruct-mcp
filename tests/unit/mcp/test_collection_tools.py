"""Tests for MCP collection tools."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_server.tools.collection_tools import (
    CreateCollectionInput,
    DeleteCollectionInput,
    GetCollectionInput,
    RenameCollectionInput,
    create_collection,
    delete_collection,
    get_collection,
    list_collections,
    rename_collection,
)
from mcp_server.tools.context import clear_pat_info, clear_user_info, set_user_info


class TestCreateCollection:
    """Test cases for create_collection function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        clear_user_info()
        clear_pat_info()
        yield
        clear_user_info()
        clear_pat_info()

    @pytest.fixture
    def mock_user_info(self):
        return {
            "user_id": "user-123",
            "is_superuser": False,
        }

    @pytest.mark.asyncio
    async def test_create_collection_returns_collection_id(self, mock_user_info):
        """Test that create_collection returns collection_id field, not id."""
        set_user_info(mock_user_info)

        mock_repo = MagicMock()
        mock_repo.get_by_name_for_user = AsyncMock(return_value=None)

        mock_response = MagicMock()
        mock_response.collection_id = "coll-123"
        mock_response.name = "Test Collection"
        mock_response.document_count = 0
        mock_response.cat_count = 0
        mock_response.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_response.updated_at = None
        mock_repo.create = AsyncMock(return_value=mock_response)

        with patch(
            "mcp_server.tools.collection_tools.get_collection_repository",
            return_value=mock_repo,
        ):
            result = await create_collection(CreateCollectionInput(name="Test Collection"))

            assert result.collection_id == "coll-123"
            assert result.name == "Test Collection"

    @pytest.mark.asyncio
    async def test_create_collection_duplicate_name_fails(self, mock_user_info):
        """Test that creating a collection with duplicate name fails."""
        set_user_info(mock_user_info)

        mock_repo = MagicMock()
        mock_repo.get_by_name_for_user = AsyncMock(
            return_value={"collection_id": "existing-coll", "name": "Test Collection"}
        )

        with patch(
            "mcp_server.tools.collection_tools.get_collection_repository",
            return_value=mock_repo,
        ):
            with pytest.raises(ValueError, match="Collection with this name already exists"):
                await create_collection(CreateCollectionInput(name="Test Collection"))


class TestListCollections:
    """Test cases for list_collections function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        clear_user_info()
        clear_pat_info()
        yield
        clear_user_info()
        clear_pat_info()

    @pytest.fixture
    def mock_user_info(self):
        return {
            "user_id": "user-123",
            "is_superuser": False,
        }

    @pytest.mark.asyncio
    async def test_list_collections_returns_collection_id(self, mock_user_info):
        """Test that list_collections returns collection_id field, not id."""
        set_user_info(mock_user_info)

        mock_repo = MagicMock()
        mock_repo.list_by_user = AsyncMock(
            return_value=[
                {
                    "collection_id": "coll-123",
                    "name": "Collection 1",
                    "created_at": datetime(2024, 1, 1, 0, 0, 0),
                },
                {
                    "collection_id": "coll-456",
                    "name": "Collection 2",
                    "created_at": datetime(2024, 1, 2, 0, 0, 0),
                },
            ]
        )

        with patch(
            "mcp_server.tools.collection_tools.get_collection_repository",
            return_value=mock_repo,
        ):
            result = await list_collections()

            assert len(result) == 2
            assert result[0].collection_id == "coll-123"
            assert result[1].collection_id == "coll-456"


class TestGetCollection:
    """Test cases for get_collection function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        clear_user_info()
        clear_pat_info()
        yield
        clear_user_info()
        clear_pat_info()

    @pytest.fixture
    def mock_user_info(self):
        return {
            "user_id": "user-123",
            "is_superuser": False,
        }

    @pytest.mark.asyncio
    async def test_get_collection_returns_collection_id(self, mock_user_info):
        """Test that get_collection returns collection_id field, not id."""
        set_user_info(mock_user_info)

        mock_repo = MagicMock()
        mock_repo.get_by_id = AsyncMock(
            return_value={
                "collection_id": "coll-123",
                "name": "Test Collection",
                "user_id": "user-123",
                "document_count": 5,
                "cat_count": 2,
                "created_at": datetime(2024, 1, 1, 0, 0, 0),
                "updated_at": None,
            }
        )

        with patch(
            "mcp_server.tools.collection_tools.get_collection_repository",
            return_value=mock_repo,
        ):
            result = await get_collection(GetCollectionInput(collection_id="coll-123"))

            assert result.collection_id == "coll-123"
            assert result.document_count == 5
            assert result.cat_count == 2


class TestDeleteCollection:
    """Test cases for delete_collection function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        clear_user_info()
        clear_pat_info()
        yield
        clear_user_info()
        clear_pat_info()

    @pytest.fixture
    def mock_user_info(self):
        return {
            "user_id": "user-123",
            "is_superuser": False,
        }

    @pytest.mark.asyncio
    async def test_delete_collection_with_cats_fails(self, mock_user_info):
        """Test that deleting a collection with active CATs fails."""
        set_user_info(mock_user_info)

        mock_repo = MagicMock()
        mock_repo.get_by_id = AsyncMock(
            return_value={
                "collection_id": "coll-123",
                "name": "Test Collection",
                "user_id": "user-123",
                "cat_count": 1,
                "qdrant_collection": "docs_test123",
            }
        )

        with patch(
            "mcp_server.tools.collection_tools.get_collection_repository",
            return_value=mock_repo,
        ):
            with pytest.raises(ValueError, match="Cannot delete collection with active CAT tokens"):
                await delete_collection(DeleteCollectionInput(collection_id="coll-123"))


class TestRenameCollection:
    """Test cases for rename_collection function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        clear_user_info()
        clear_pat_info()
        yield
        clear_user_info()
        clear_pat_info()

    @pytest.fixture
    def mock_user_info(self):
        return {
            "user_id": "user-123",
            "is_superuser": False,
        }

    @pytest.mark.asyncio
    async def test_rename_collection_returns_collection_id(self, mock_user_info):
        """Test that rename_collection returns collection_id field, not id."""
        set_user_info(mock_user_info)

        mock_repo = MagicMock()
        mock_repo.get_by_id = AsyncMock(
            return_value={
                "collection_id": "coll-123",
                "name": "Old Name",
                "user_id": "user-123",
            }
        )
        mock_repo.get_by_name_for_user = AsyncMock(return_value=None)

        mock_response = MagicMock()
        mock_response.collection_id = "coll-123"
        mock_response.name = "New Name"
        mock_response.document_count = 5
        mock_response.cat_count = 2
        mock_response.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_response.updated_at = datetime(2024, 1, 2, 0, 0, 0)
        mock_repo.rename = AsyncMock(return_value=mock_response)

        with patch(
            "mcp_server.tools.collection_tools.get_collection_repository",
            return_value=mock_repo,
        ):
            result = await rename_collection(
                RenameCollectionInput(collection_id="coll-123", name="New Name")
            )

            assert result.collection_id == "coll-123"
            assert result.name == "New Name"
