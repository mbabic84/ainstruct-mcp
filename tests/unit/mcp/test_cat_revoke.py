"""Tests for revoke_cat MCP tool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_server.tools.cat_tools import RevokeCatInput, revoke_cat
from mcp_server.tools.context import clear_pat_info, clear_user_info, set_user_info


class TestRevokeCat:
    """Test cases for revoke_cat function."""

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
    async def test_revoke_cat_success(self, mock_user_info):
        """Test successful CAT token revocation."""
        set_user_info(mock_user_info)

        mock_cat_repo = MagicMock()
        mock_cat_repo.get_by_id = AsyncMock(
            return_value={
                "cat_id": "cat-123",
                "user_id": "user-123",
                "label": "Test CAT",
            }
        )
        mock_cat_repo.revoke = AsyncMock(return_value=True)

        with patch(
            "mcp_server.tools.cat_tools.get_cat_repository",
            return_value=mock_cat_repo,
        ):
            result = await revoke_cat(RevokeCatInput(key_id="cat-123"))

            assert result["success"] is True
            mock_cat_repo.revoke.assert_called_once_with("cat-123")

    @pytest.mark.asyncio
    async def test_revoke_cat_not_found(self, mock_user_info):
        """Test that revoking non-existent CAT token fails."""
        set_user_info(mock_user_info)

        mock_cat_repo = MagicMock()
        mock_cat_repo.get_by_id = AsyncMock(return_value=None)

        with patch(
            "mcp_server.tools.cat_tools.get_cat_repository",
            return_value=mock_cat_repo,
        ):
            with pytest.raises(ValueError, match="CAT token not found"):
                await revoke_cat(RevokeCatInput(key_id="non-existent"))

    @pytest.mark.asyncio
    async def test_revoke_cat_other_users_token_fails(self, mock_user_info):
        """Test that revoking another user's CAT token fails."""
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
            with pytest.raises(ValueError, match="You can only revoke your own CAT tokens"):
                await revoke_cat(RevokeCatInput(key_id="cat-123"))

    @pytest.mark.asyncio
    async def test_revoke_cat_superuser_can_revoke_any(self):
        """Test that superuser can revoke any CAT token."""
        set_user_info({"user_id": "admin-123", "is_superuser": True})

        mock_cat_repo = MagicMock()
        mock_cat_repo.get_by_id = AsyncMock(
            return_value={
                "cat_id": "cat-123",
                "user_id": "different-user",
                "label": "Other User CAT",
            }
        )
        mock_cat_repo.revoke = AsyncMock(return_value=True)

        with patch(
            "mcp_server.tools.cat_tools.get_cat_repository",
            return_value=mock_cat_repo,
        ):
            result = await revoke_cat(RevokeCatInput(key_id="cat-123"))

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_revoke_cat_failure(self, mock_user_info):
        """Test that failed revocation raises error."""
        set_user_info(mock_user_info)

        mock_cat_repo = MagicMock()
        mock_cat_repo.get_by_id = AsyncMock(
            return_value={
                "cat_id": "cat-123",
                "user_id": "user-123",
                "label": "Test CAT",
            }
        )
        mock_cat_repo.revoke = AsyncMock(return_value=False)

        with patch(
            "mcp_server.tools.cat_tools.get_cat_repository",
            return_value=mock_cat_repo,
        ):
            with pytest.raises(ValueError, match="Failed to revoke CAT token"):
                await revoke_cat(RevokeCatInput(key_id="cat-123"))
