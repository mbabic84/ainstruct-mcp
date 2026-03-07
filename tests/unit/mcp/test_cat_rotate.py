"""Tests for rotate_cat MCP tool."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_server.tools.cat_tools import RotateCatInput, rotate_cat
from mcp_server.tools.context import clear_pat_info, clear_user_info, set_user_info
from shared.db.models import Permission


class TestRotateCat:
    """Test cases for rotate_cat function."""

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
    async def test_rotate_cat_success(self, mock_user_info):
        """Test successful CAT token rotation."""
        set_user_info(mock_user_info)

        mock_cat_repo = MagicMock()
        mock_cat_repo.get_by_id = AsyncMock(
            return_value={
                "cat_id": "cat-123",
                "user_id": "user-123",
                "label": "Test CAT",
                "collection_id": "coll-123",
                "permission": Permission.READ_WRITE,
            }
        )
        mock_cat_repo.rotate = AsyncMock(return_value=("new-cat-123", "new-key-value"))
        mock_cat_repo.get_by_id = AsyncMock(
            side_effect=[
                {
                    "cat_id": "cat-123",
                    "user_id": "user-123",
                    "label": "Test CAT",
                    "collection_id": "coll-123",
                    "permission": Permission.READ_WRITE,
                },
                {
                    "cat_id": "new-cat-123",
                    "label": "Test CAT",
                    "collection_id": "coll-123",
                    "user_id": "user-123",
                    "permission": Permission.READ_WRITE,
                    "created_at": datetime(2024, 1, 2),
                    "expires_at": None,
                    "is_active": True,
                    "last_used": None,
                },
            ]
        )

        with patch(
            "mcp_server.tools.cat_tools.get_cat_repository",
            return_value=mock_cat_repo,
        ):
            result = await rotate_cat(RotateCatInput(key_id="cat-123"))

            assert result.cat_id == "new-cat-123"
            assert result.key == "new-key-value"

    @pytest.mark.asyncio
    async def test_rotate_cat_not_found(self, mock_user_info):
        """Test that rotating non-existent CAT token fails."""
        set_user_info(mock_user_info)

        mock_cat_repo = MagicMock()
        mock_cat_repo.get_by_id = AsyncMock(return_value=None)

        with patch(
            "mcp_server.tools.cat_tools.get_cat_repository",
            return_value=mock_cat_repo,
        ):
            with pytest.raises(ValueError, match="CAT token not found"):
                await rotate_cat(RotateCatInput(key_id="non-existent"))

    @pytest.mark.asyncio
    async def test_rotate_cat_other_users_token_fails(self, mock_user_info):
        """Test that rotating another user's CAT token fails."""
        set_user_info(mock_user_info)

        mock_cat_repo = MagicMock()
        mock_cat_repo.get_by_id = AsyncMock(
            return_value={
                "cat_id": "cat-123",
                "user_id": "different-user",
                "label": "Other User CAT",
            }
        )

        with patch(
            "mcp_server.tools.cat_tools.get_cat_repository",
            return_value=mock_cat_repo,
        ):
            with pytest.raises(ValueError, match="You can only rotate your own CAT tokens"):
                await rotate_cat(RotateCatInput(key_id="cat-123"))

    @pytest.mark.asyncio
    async def test_rotate_cat_superuser_can_rotate_any(self):
        """Test that superuser can rotate any CAT token."""
        set_user_info({"user_id": "admin-123", "is_superuser": True})

        mock_cat_repo = MagicMock()
        mock_cat_repo.get_by_id = AsyncMock(
            side_effect=[
                {
                    "cat_id": "cat-123",
                    "user_id": "different-user",
                    "label": "Other User CAT",
                    "collection_id": "coll-123",
                    "permission": Permission.READ_WRITE,
                },
                {
                    "cat_id": "new-cat-123",
                    "label": "Other User CAT",
                    "collection_id": "coll-123",
                    "user_id": "different-user",
                    "permission": Permission.READ_WRITE,
                    "created_at": datetime(2024, 1, 2),
                    "expires_at": None,
                    "is_active": True,
                    "last_used": None,
                },
            ]
        )
        mock_cat_repo.rotate = AsyncMock(return_value=("new-cat-123", "new-key-value"))

        with patch(
            "mcp_server.tools.cat_tools.get_cat_repository",
            return_value=mock_cat_repo,
        ):
            result = await rotate_cat(RotateCatInput(key_id="cat-123"))

            assert result.cat_id == "new-cat-123"

    @pytest.mark.asyncio
    async def test_rotate_cat_failure(self, mock_user_info):
        """Test that failed rotation raises error."""
        set_user_info(mock_user_info)

        mock_cat_repo = MagicMock()
        mock_cat_repo.get_by_id = AsyncMock(
            return_value={
                "cat_id": "cat-123",
                "user_id": "user-123",
                "label": "Test CAT",
            }
        )
        mock_cat_repo.rotate = AsyncMock(return_value=None)

        with patch(
            "mcp_server.tools.cat_tools.get_cat_repository",
            return_value=mock_cat_repo,
        ):
            with pytest.raises(ValueError, match="Failed to rotate CAT token"):
                await rotate_cat(RotateCatInput(key_id="cat-123"))
