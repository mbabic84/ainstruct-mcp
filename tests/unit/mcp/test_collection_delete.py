"""Tests for delete_collection MCP tool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_server.tools.collection_tools import (
    DeleteCollectionInput,
    delete_collection,
)
from mcp_server.tools.context import clear_pat_info, clear_user_info, set_user_info


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
