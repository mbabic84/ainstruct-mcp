# SQLite to PostgreSQL Migration Plan

**Date:** 2026-02-26  
**Status:** In Progress  
**Current Phase:** Phase 7 - MCP Server & REST Routes Complete  
**Migration Type:** Full Async Migration

---

## Overview

This document outlines the migration from SQLite to PostgreSQL with full async support for improved concurrency and performance.

### Key Decisions

| Decision | Value |
|----------|-------|
| Database | PostgreSQL only (no SQLite fallback) |
| Data | Fresh start (no migration) |
| Migrations | Fresh Alembic migrations (regenerate) |
| Storage | No Docker volumes (ephemeral for testing) |
| Pattern | Full async throughout |
| PostgreSQL | postgres:18-alpine (latest stable) |

### Why Full Async?

The current codebase has an anti-pattern: async tool functions calling synchronous database operations, which blocks the event loop. Going fully async will:

- Enable true concurrent request handling
- Improve throughput under load
- Follow 2026 best practices for Python async applications

---

## Dependencies

### Required Changes

**File:** `pyproject.toml`

```toml
dependencies = [
    # ... existing dependencies ...
    "asyncpg>=0.31.0",  # ADD: Async PostgreSQL driver (latest)
]
```

**Rationale:**
- `asyncpg` is the fastest async PostgreSQL driver for Python
- Outperforms psycopg in async scenarios
- Well-maintained, regularly updated
- Version 0.31.0 is the latest (as of 2026-02)

---

## Docker Configuration

### Changes Required

**File:** `docker-compose.yml`

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ainstruct
      POSTGRES_USER: ainstruct
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-devpassword}
    # No volumes - data is ephemeral during testing
    tmpfs:
      - /var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ainstruct"]
      interval: 5s
      timeout: 5s
      retries: 5
    ports:
      - "5432:5432"

  mcp_server:
    environment:
      - DATABASE_URL=postgresql+asyncpg://ainstruct:${POSTGRES_PASSWORD:-devpassword}@postgres:5432/ainstruct
    depends_on:
      postgres:
        condition: service_healthy

  rest_api:
    environment:
      - DATABASE_URL=postgresql+asyncpg://ainstruct:${POSTGRES_PASSWORD:-devpassword}@postgres:5432/ainstruct
    depends_on:
      postgres:
        condition: service_healthy

  test_runner:
    environment:
      - DATABASE_URL=postgresql+asyncpg://ainstruct:${POSTGRES_PASSWORD:-devpassword}@postgres:5432/ainstruct
    depends_on:
      postgres:
        condition: service_healthy
```

### Key Points

- `tmpfs` provides ephemeral in-memory storage (clean on restart)
- All services connect to PostgreSQL via `DATABASE_URL`
- Healthcheck ensures PostgreSQL is ready before other services start

---

## Configuration

### Changes Required

**File:** `src/app/config/__init__.py`

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ... existing settings ...
    
    # Database configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/ainstruct"
    
    # Connection pool settings
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800
    
    # Legacy support (deprecated)
    db_path: str = "./data/documents.db"  # Deprecated, use DATABASE_URL

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

## Database Layer

### 1. Models - Async Engine

**File:** `src/app/db/models.py`

```python
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models with async support."""
    pass


# Example model with modern syntax
class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)


def get_db_engine(database_url: str, pool_size: int = 5, max_overflow: int = 10):
    """Create async database engine with connection pooling."""
    return create_async_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,  # Verify connection is alive before use (critical for async)
        echo=False,
    )
```

### 2. Repository - Async Methods

**File:** `src/app/db/repository.py`

```python
from typing import Optional
from datetime import datetime

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..config import settings
from .models import (
    Base,
    CatModel,
    CollectionModel,
    DocumentCreate,
    DocumentModel,
    PatTokenModel,
    UserModel,
    # ... response models
)


class DocumentRepository:
    def __init__(self, engine, collection_id: str | None = None):
        self.async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,  # 2026 best practice
        )
        self.collection_id = collection_id

    async def create(self, doc: DocumentCreate) -> DocumentResponse:
        async with self.async_session() as session:
            # Check for existing document
            result = await session.execute(
                select(DocumentModel).where(
                    DocumentModel.content_hash == compute_content_hash(doc.content),
                    DocumentModel.collection_id == doc.collection_id,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                return DocumentResponse(
                    id=existing.id,
                    collection_id=existing.collection_id,
                    title=existing.title,
                    content=existing.content,
                    document_type=existing.document_type,
                    created_at=existing.created_at,
                    updated_at=existing.updated_at,
                    doc_metadata=existing.doc_metadata or {},
                )

            # Create new document
            db_doc = DocumentModel(
                collection_id=doc.collection_id,
                title=doc.title,
                content=doc.content,
                content_hash=compute_content_hash(doc.content),
                document_type=doc.document_type,
                doc_metadata=doc.doc_metadata,
            )
            session.add(db_doc)
            await session.commit()
            await session.refresh(db_doc)

            return DocumentResponse(
                id=db_doc.id,
                collection_id=db_doc.collection_id,
                title=db_doc.title,
                content=db_doc.content,
                document_type=db_doc.document_type,
                created_at=db_doc.created_at,
                updated_at=db_doc.updated_at,
                doc_metadata=db_doc.doc_metadata or {},
            )

    async def get_by_id(self, doc_id: str) -> Optional[DocumentResponse]:
        async with self.async_session() as session:
            query = select(DocumentModel).where(DocumentModel.id == doc_id)
            if self.collection_id:
                query = query.where(DocumentModel.collection_id == self.collection_id)

            result = await session.execute(query)
            db_doc = result.scalar_one_or_none()
            
            if not db_doc:
                return None
                
            return DocumentResponse(
                id=db_doc.id,
                collection_id=db_doc.collection_id,
                title=db_doc.title,
                content=db_doc.content,
                document_type=db_doc.document_type,
                created_at=db_doc.created_at,
                updated_at=db_doc.updated_at,
                doc_metadata=db_doc.doc_metadata or {},
            )

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[DocumentResponse]:
        async with self.async_session() as session:
            query = select(DocumentModel).order_by(DocumentModel.created_at.desc())
            if self.collection_id:
                query = query.where(DocumentModel.collection_id == self.collection_id)

            result = await session.execute(query.limit(limit).offset(offset))
            docs = result.scalars().all()

            return [
                DocumentResponse(
                    id=d.id,
                    collection_id=d.collection_id,
                    title=d.title,
                    content=d.content,
                    document_type=d.document_type,
                    created_at=d.created_at,
                    updated_at=d.updated_at,
                    doc_metadata=d.doc_metadata or {},
                )
                for d in docs
            ]

    async def delete(self, doc_id: str) -> bool:
        async with self.async_session() as session:
            query = select(DocumentModel).where(DocumentModel.id == doc_id)
            if self.collection_id:
                query = query.where(DocumentModel.collection_id == self.collection_id)

            result = await session.execute(query)
            db_doc = result.scalar_one_or_none()
            
            if not db_doc:
                return False
                
            await session.delete(db_doc)
            await session.commit()
            return True
```

### 3. Qdrant - Async Client

**File:** `src/app/db/qdrant.py`

```python
from typing import Optional
import logging

from qdrant_client import AsyncQdrantClient, models

from ..config import settings
from .repository import CollectionRepository

log = logging.getLogger(__name__)


class QdrantService:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )

    async def upsert_chunks(
        self,
        chunks: list[dict],
        vectors: list[list[float]],
    ) -> None:
        points = [
            models.PointStruct(
                id=chunk["id"],
                vector=vector,
                payload=chunk,
            )
            for chunk, vector in zip(chunks, vectors)
        ]

        await self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    async def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        query_filter: Optional[models.Filter] = None,
    ) -> list[dict]:
        results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter,
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results
        ]

    async def delete_points(self, point_ids: list[str]) -> None:
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(points=point_ids),
        )

    async def collection_exists(self) -> bool:
        try:
            await self.client.get_collection(collection_name=self.collection_name)
            return True
        except Exception:
            return False

    async def create_collection(self, vector_size: int = 1536) -> None:
        await self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )
```

---

## REST API Dependencies

### Changes Required

**File:** `src/app/rest/deps.py`

```python
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..config import settings
from ..db.models import get_db_engine


# Global engine (initialized once)
_engine = None
_async_session_factory = None


def get_engine():
    """Get or create the global database engine."""
    global _engine
    if _engine is None:
        _engine = get_db_engine(settings.DATABASE_URL)
    return _engine


def get_async_session_factory():
    """Get or create the async session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session for each request."""
    async_session = get_async_session_factory()
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

---

## Tool Updates

### Pattern: Add await to Repository Calls

All tool functions in `src/app/tools/*.py` need to add `await` to repository and service calls:

```python
# Before
def store_document(input_data: StoreDocumentInput) -> StoreDocumentOutput:
    doc = doc_repo.create(DocumentCreate(...))
    qdrant.upsert_chunks(...)
    return DocumentResponse(...)

# After
async def store_document(input_data: StoreDocumentInput) -> StoreDocumentOutput:
    doc = await doc_repo.create(DocumentCreate(...))
    await qdrant.upsert_chunks(...)
    return DocumentResponse(...)
```

### Files to Update

| File | Changes |
|------|---------|
| `document_tools.py` | Add `await` to all repo/qdrant calls |
| `collection_tools.py` | Add `await` to all repo calls |
| `user_tools.py` | Add `await` to all repo calls |
| `cat_tools.py` | Add `await` to all repo calls |
| `pat_tools.py` | Add `await` to all repo calls |
| `admin_tools.py` | Add `await` to all repo calls |

---

## Alembic Configuration

### Changes Required

**File:** `alembic.ini`

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os

# Change from SQLite to PostgreSQL
sqlalchemy.url = postgresql+asyncpg://ainstruct:password@localhost:5432/ainstruct
```

**File:** `migrations/env.py` (Critical - Async Migration Support)

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine import Connection

from alembic import context

from src.app.config import settings
from src.app.db.models import Base

config = context.config

# Set the database URL from settings
if settings.DATABASE_URL:
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations within a connection context."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using async engine."""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async support."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Rationale:**
- Async migrations require `run_sync()` to execute sync migration code
- Must use `asyncio.run()` for the async migration runner
- Connection pooling disabled for migrations (`NullPool`)

### Generate Fresh Migrations

```bash
# Remove old migrations
rm -rf migrations/versions/*

# Create initial migration
alembic revision --autogenerate -m "initial postgresql migration"

# Apply migration
alembic upgrade head
```

---

## MCP Server

### Changes Required

**File:** `src/app/mcp/server.py`

The MCP server tools are already async. Key change is the database migration lifespan:

```python
@lifespan
async def db_migrations_lifespan(server):
    log.info("Running database migrations...")
    try:
        # Convert to async Alembic execution
        from sqlalchemy.ext.asyncio import create_async_engine
        
        engine = create_async_engine(settings.DATABASE_URL)
        
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        
        await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
        log.info("Migrations applied successfully!")
    except Exception as e:
        log.error(f"Migration failed: {e}")
        raise
    yield {}
```

---

## Files Summary

### Modify (12 files)

| Priority | File | Change |
|----------|------|--------|
| P1 | `pyproject.toml` | Add `asyncpg>=0.31.0` |
| P1 | `docker-compose.yml` | Add PostgreSQL service with healthcheck dependencies |
| P1 | `src/app/config/__init__.py` | Add DATABASE_URL |
| P1 | `src/app/db/models.py` | Async engine, AsyncAttrs |
| P1 | `src/app/db/repository.py` | Convert to async methods |
| P1 | `src/app/db/qdrant.py` | AsyncQdrantClient |
| P1 | `src/app/rest/deps.py` | Async session dependency |
| P1 | `migrations/env.py` | Async migration support (critical) |
| P2 | `src/app/tools/document_tools.py` | Add `await` |
| P2 | `src/app/tools/collection_tools.py` | Add `await` |
| P2 | `src/app/tools/user_tools.py` | Add `await` |
| P2 | `alembic.ini` | PostgreSQL URL |

### Tool Files (4 files)

| File | Changes |
|------|---------|
| `src/app/tools/cat_tools.py` | Add `await` |
| `src/app/tools/pat_tools.py` | Add `await` |
| `src/app/tools/admin_tools.py` | Add `await` |

---

## Testing Strategy

### Test Database

With ephemeral PostgreSQL:
- Each `docker compose down` → clean database
- Each `docker compose up` → fresh database with migrations
- No data persistence between test runs

### Running Tests

```bash
# Start PostgreSQL
docker compose up -d postgres

# Wait for PostgreSQL to be ready
docker compose run test_runner --help  # Or check health

# Run tests
docker compose --profile test run test_runner
```

### Manual Testing Checklist

- [ ] PostgreSQL connects successfully
- [ ] Tables created via Alembic
- [ ] User registration/login works
- [ ] Collection CRUD operations
- [ ] Document store/search works
- [ ] CAT/PAT token operations
- [ ] MCP tools work correctly

---

## Rollback Plan

If issues arise:

1. **Revert DATABASE_URL** in docker-compose.yml:
   ```yaml
   DATABASE_URL: sqlite:////tmp/mcp_server.db
   ```

2. **Revert alembic.ini** to SQLite:
   ```ini
   sqlalchemy.url = sqlite:///./data/documents.db
   ```

3. **Keep old migration files** in `migrations/versions/`

---

## Performance Expectations

### Before (SQLite + Sync)

- Concurrent requests: Limited by thread count
- Memory usage: High (thread per request)
- Throughput: ~100-500 req/s

### After (PostgreSQL + Async)

- Concurrent requests: Limited by connection pool
- Memory usage: Low (async event loop)
- Throughput: ~1000-5000 req/s

---

## References

- [SQLAlchemy 2.1 Async Documentation](https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [Qdrant Async Client](https://qdrant.tech/documentation/tutorials-develop/async-api/)
- [FastAPI Async Database Best Practices (2026)](https://oneuptime.com/blog/post/2026-02-02-fastapi-async-database/view)

---

## Validation Notes (2026-02-26)

This plan was validated against:

- SQLAlchemy 2.1 async documentation
- asyncpg 0.31.0 (latest as of 2026-02)
- qdrant-client async API

### Key Corrections Applied

1. **asyncpg version**: Updated from `>=0.30.0` to `>=0.31.0`
2. **Docker dependencies**: Added `depends_on: condition: service_healthy` for proper startup ordering
3. **Alembic env.py**: Added complete async migration support pattern (critical missing piece)
4. **pool_pre_ping**: Emphasized as critical for async connection validation
