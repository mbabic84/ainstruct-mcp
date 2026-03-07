"""Tests for create_cat MCP tool."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_server.tools.cat_tools import CreateCatInput, create_cat
from mcp_server.tools.context import clear_pat_info, clear_user_info, set_user_info
from shared.db.models import Permission


class TestCreateCat:
    """Test cases for create_cat function."""

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
    async def test_create_cat_success(self, mock_user_info):
        """Test successful CAT token creation."""
        set_user_info(mock_user_info)

        mock_collection_repo = MagicMock()
        mock_collection_repo.get_by_id = AsyncMock(
            return_value={
                "collection_id": "coll-123",
                "name": "Test Collection",
                "user_id": "user-123",
            }
        )

        mock_cat_repo = MagicMock()
        mock_cat_repo.create = AsyncMock(return_value=("cat-123", "test-key-value"))
        mock_cat_repo.get_by_id = AsyncMock(
            return_value={
                "cat_id": "cat-123",
                "label": "Test CAT",
                "collection_id": "coll-123",
                "user_id": "user-123",
                "permission": Permission.READ_WRITE,
                "created_at": datetime(2024, 1, 1),
                "expires_at": None,
                "is_active": True,
                "last_used": None,
            }
        )

        with (
            patch(
                "mcp_server.tools.cat_tools.get_collection_repository",
                return_value=mock_collection_repo,
            ),
            patch(
                "mcp_server.tools.cat_tools.get_cat_repository",
                return_value=mock_cat_repo,
            ),
        ):
            result = await create_cat(
                CreateCatInput(
                    label="Test CAT",
                    collection_id="coll-123",
                    permission="read_write",
                )
            )

            assert result.cat_id == "cat-123"
            assert result.label == "Test CAT"
            assert result.key == "test-key-value"
            assert result.collection_id == "coll-123"

    @pytest.mark.asyncio
    async def test_create_cat_collection_not_found(self, mock_user_info):
        """Test that creating CAT for non-existent collection fails."""
        set_user_info(mock_user_info)

        mock_collection_repo = MagicMock()
        mock_collection_repo.get_by_id = AsyncMock(return_value=None)

        with patch(
            "mcp_server.tools.cat_tools.get_collection_repository",
            return_value=mock_collection_repo,
        ):
            with pytest.raises(ValueError, match="Collection not found"):
                await create_cat(
                    CreateCatInput(
                        label="Test CAT",
                        collection_id="non-existent",
                        permission="read_write",
                    )
                )

    @pytest.mark.asyncio
    async def test_create_cat_invalid_permission(self, mock_user_info):
        """Test that creating CAT with invalid permission fails."""
        set_user_info(mock_user_info)

        mock_collection_repo = MagicMock()
        mock_collection_repo.get_by_id = AsyncMock(
            return_value={
                "collection_id": "coll-123",
                "name": "Test Collection",
                "user_id": "user-123",
            }
        )

        with patch(
            "mcp_server.tools.cat_tools.get_collection_repository",
            return_value=mock_collection_repo,
        ):
            with pytest.raises(ValueError, match="Invalid permission"):
                await create_cat(
                    CreateCatInput(
                        label="Test CAT",
                        collection_id="coll-123",
                        permission="invalid_permission",
                    )
                )

    @pytest.mark.asyncio
    async def test_create_cat_not_authenticated(self):
        """Test that creating CAT without authentication fails."""
        with pytest.raises(ValueError, match="Not authenticated"):
            await create_cat(
                CreateCatInput(
                    label="Test CAT",
                    collection_id="coll-123",
                    permission="read_write",
                )
            )

    @pytest.mark.asyncio
    async def test_create_cat_with_expiry(self, mock_user_info):
        """Test CAT token creation with expiration date."""
        set_user_info(mock_user_info)

        mock_collection_repo = MagicMock()
        mock_collection_repo.get_by_id = AsyncMock(
            return_value={
                "collection_id": "coll-123",
                "name": "Test Collection",
                "user_id": "user-123",
            }
        )

        mock_cat_repo = MagicMock()
        mock_cat_repo.create = AsyncMock(return_value=("cat-123", "test-key-value"))
        mock_cat_repo.get_by_id = AsyncMock(
            return_value={
                "cat_id": "cat-123",
                "label": "Test CAT",
                "collection_id": "coll-123",
                "user_id": "user-123",
                "permission": Permission.READ_WRITE,
                "created_at": datetime(2024, 1, 1),
                "expires_at": datetime(2024, 12, 31),
                "is_active": True,
                "last_used": None,
            }
        )

        with (
            patch(
                "mcp_server.tools.cat_tools.get_collection_repository",
                return_value=mock_collection_repo,
            ),
            patch(
                "mcp_server.tools.cat_tools.get_cat_repository",
                return_value=mock_cat_repo,
            ),
        ):
            result = await create_cat(
                CreateCatInput(
                    label="Test CAT",
                    collection_id="coll-123",
                    permission="read",
                    expires_in_days=30,
                )
            )

            assert result.cat_id == "cat-123"
            assert result.expires_at is not None
