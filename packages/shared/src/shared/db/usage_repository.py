import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.config import settings
from shared.db.models import UsageRecordModel


class UsageRepository:
    def __init__(self, async_session_factory):
        self.async_session = async_session_factory

    @staticmethod
    def _get_current_year_month() -> str:
        return datetime.utcnow().strftime("%Y-%m")

    async def increment(self, user_id: str, source: str) -> None:
        year_month = self._get_current_year_month()
        async with self.async_session() as session:
            stmt = pg_insert(UsageRecordModel).values(
                id=str(uuid.uuid4()),
                user_id=user_id,
                year_month=year_month,
                source=source,
                request_count=1,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id", "year_month", "source"],
                set_={
                    "request_count": UsageRecordModel.request_count + 1,
                    "updated_at": datetime.utcnow(),
                },
            )
            await session.execute(stmt)
            await session.commit()

    async def get_monthly_usage(
        self, user_id: str, year_month: str | None = None
    ) -> dict[str, Any]:
        if year_month is None:
            year_month = self._get_current_year_month()

        async with self.async_session() as session:
            query = select(UsageRecordModel).where(
                UsageRecordModel.user_id == user_id,
                UsageRecordModel.year_month == year_month,
            )
            result = await session.execute(query)
            records = result.scalars().all()

            api_requests = 0
            mcp_requests = 0

            for record in records:
                if record.source == "api":
                    api_requests = record.request_count
                elif record.source == "mcp":
                    mcp_requests = record.request_count

            return {
                "year_month": year_month,
                "api_requests": api_requests,
                "mcp_requests": mcp_requests,
                "total_requests": api_requests + mcp_requests,
            }

    async def get_usage_history(self, user_id: str, months: int = 6) -> list[dict[str, Any]]:
        async with self.async_session() as session:
            query = (
                select(UsageRecordModel)
                .where(UsageRecordModel.user_id == user_id)
                .order_by(UsageRecordModel.year_month.desc())
                .limit(months)
            )
            result = await session.execute(query)
            records = result.scalars().all()

            history_map: dict[str, dict[str, Any]] = {}

            for record in records:
                if record.year_month not in history_map:
                    history_map[record.year_month] = {
                        "year_month": record.year_month,
                        "api_requests": 0,
                        "mcp_requests": 0,
                        "total": 0,
                    }

                if record.source == "api":
                    history_map[record.year_month]["api_requests"] = record.request_count
                elif record.source == "mcp":
                    history_map[record.year_month]["mcp_requests"] = record.request_count

                history_map[record.year_month]["total"] = (
                    history_map[record.year_month]["api_requests"]
                    + history_map[record.year_month]["mcp_requests"]
                )

            return list(history_map.values())


_engine = None
_async_session_factory = None


def get_async_session_factory():
    global _engine, _async_session_factory
    if _engine is None:
        from shared.db.models import get_db_engine

        _engine = get_db_engine(settings.database_url)
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_factory


def get_usage_repository() -> UsageRepository:
    async_session = get_async_session_factory()
    return UsageRepository(async_session)
