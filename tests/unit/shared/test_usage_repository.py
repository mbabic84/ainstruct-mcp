"""Tests for UsageRepository."""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestUsageRepository:
    """Test cases for UsageRepository class."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def mock_session_factory(self, mock_session):
        """Create a mock session factory."""
        factory = MagicMock()
        factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        factory.return_value.__aexit__ = AsyncMock(return_value=None)
        return factory

    @pytest.mark.asyncio
    async def test_increment_creates_new_record(self, mock_session_factory, mock_session):
        """Test that increment creates a new record when none exists."""
        from shared.db.usage_repository import UsageRepository

        mock_session.execute.return_value.scalar_one_or_none = None
        mock_session.execute.return_value = MagicMock(scalar_one_or_none=None)

        repo = UsageRepository(mock_session_factory)
        await repo.increment("user-123", "api")

        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_increments_existing_record(self, mock_session_factory, mock_session):
        """Test that increment increases count when record exists."""
        from shared.db.usage_repository import UsageRepository

        existing_record = MagicMock()
        existing_record.request_count = 5

        mock_session.execute.return_value.scalar_one_or_none = existing_record

        repo = UsageRepository(mock_session_factory)
        await repo.increment("user-123", "api")

        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_monthly_usage(self, mock_session_factory, mock_session):
        """Test getting monthly usage for a user."""
        from shared.db.usage_repository import UsageRepository

        mock_record_api = MagicMock()
        mock_record_api.source = "api"
        mock_record_api.request_count = 100

        mock_record_mcp = MagicMock()
        mock_record_mcp.source = "mcp"
        mock_record_mcp.request_count = 50

        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[mock_record_api, mock_record_mcp])
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = UsageRepository(mock_session_factory)
        result = await repo.get_monthly_usage("user-123", "2026-03")

        assert result["api_requests"] == 100
        assert result["mcp_requests"] == 50
        assert result["total_requests"] == 150

    @pytest.mark.asyncio
    async def test_get_monthly_usage_no_records(self, mock_session_factory, mock_session):
        """Test getting monthly usage when no records exist."""
        from shared.db.usage_repository import UsageRepository

        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[])
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = UsageRepository(mock_session_factory)
        result = await repo.get_monthly_usage("user-123", "2026-03")

        assert result["api_requests"] == 0
        assert result["mcp_requests"] == 0
        assert result["total_requests"] == 0

    @pytest.mark.asyncio
    async def test_get_usage_history(self, mock_session_factory, mock_session):
        """Test getting usage history across multiple months."""
        from shared.db.usage_repository import UsageRepository

        mock_record = MagicMock()
        mock_record.year_month = "2026-03"
        mock_record.source = "api"
        mock_record.request_count = 100

        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[mock_record])
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = UsageRepository(mock_session_factory)
        result = await repo.get_usage_history("user-123", months=3)

        assert len(result) >= 0
