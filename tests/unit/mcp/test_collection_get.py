"""Tests for list_collections and get_collection MCP tools."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_server.tools.collection_tools import (
    GetCollectionInput,
    get_collection,
    list_collections,
)
from mcp_server.tools.context import clear_pat_info, clear_user_info, set_user_info


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
