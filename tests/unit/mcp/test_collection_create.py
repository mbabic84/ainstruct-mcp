"""Tests for create_collection MCP tool."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_server.tools.collection_tools import (
    CreateCollectionInput,
    create_collection,
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
