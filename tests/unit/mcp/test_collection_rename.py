"""Tests for rename_collection MCP tool."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_server.tools.collection_tools import (
    RenameCollectionInput,
    rename_collection,
)
from mcp_server.tools.context import clear_pat_info, clear_user_info, set_user_info


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
