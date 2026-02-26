# SQLite to PostgreSQL Migration - Tasks

## Phase 1: Dependencies

- [ ] **T1.1** Add `asyncpg>=0.31.0` to `pyproject.toml`

## Phase 2: Docker Configuration

- [ ] **T2.1** Add `postgres` service to `docker-compose.yml`
- [ ] **T2.2** Add healthcheck to `postgres` service
- [ ] **T2.3** Add `depends_on: postgres: condition: service_healthy` to `mcp_server`
- [ ] **T2.4** Add `depends_on: postgres: condition: service_healthy` to `rest_api`
- [ ] **T2.5** Add `depends_on: postgres: condition: service_healthy` to `test_runner`
- [ ] **T2.6** Update `mcp_server` DATABASE_URL
- [ ] **T2.7** Update `rest_api` DATABASE_URL
- [ ] **T2.8** Update `test_runner` DATABASE_URL

## Phase 3: Configuration

- [ ] **T3.1** Add `DATABASE_URL` to `src/app/config/__init__.py`
- [ ] **T3.2** Add pool settings (db_pool_size, db_max_overflow, etc.)

## Phase 4: Database Layer

- [ ] **T4.1** Update `src/app/db/models.py`:
  - [ ] Import `AsyncAttrs`, `create_async_engine`
  - [ ] Add `AsyncAttrs` to `Base` class
  - [ ] Update `get_db_engine()` to return async engine with `pool_pre_ping=True`
  - [ ] (Optional) Update models to use `Mapped` syntax

- [ ] **T4.2** Update `src/app/db/repository.py`:
  - [ ] Import `AsyncSession`, `async_sessionmaker`
  - [ ] Convert `DocumentRepository` to async with `async with` sessions
  - [ ] Convert `UserRepository` to async with `async with` sessions
  - [ ] Convert `CollectionRepository` to async with `async with` sessions
  - [ ] Convert `CatRepository` to async with `async with` sessions
  - [ ] Convert `PatTokenRepository` to async with `async with` sessions

- [ ] **T4.3** Update `src/app/db/qdrant.py`:
  - [ ] Import `AsyncQdrantClient`
  - [ ] Convert all methods to async

- [ ] **T4.4** Update `src/app/rest/deps.py`:
  - [ ] Create async session factory
  - [ ] Convert `get_db()` to async generator

## Phase 5: Tool Updates

- [ ] **T5.1** Update `src/app/tools/document_tools.py` - add `await` to repo/qdrant calls
- [ ] **T5.2** Update `src/app/tools/collection_tools.py` - add `await` to repo calls
- [ ] **T5.3** Update `src/app/tools/user_tools.py` - add `await` to repo calls
- [ ] **T5.4** Update `src/app/tools/cat_tools.py` - add `await` to repo calls
- [ ] **T5.5** Update `src/app/tools/pat_tools.py` - add `await` to repo calls
- [ ] **T5.6** Update `src/app/tools/admin_tools.py` - add `await` to repo calls

## Phase 6: Alembic

- [ ] **T6.1** Update `alembic.ini` with PostgreSQL URL
- [ ] **T6.2** Update `migrations/env.py` with async migration support (critical)
- [ ] **T6.3** Remove old migration files (or keep for rollback)
- [ ] **T6.4** Generate new initial migration
- [ ] **T6.5** Test migration runs successfully

## Phase 7: MCP Server

- [ ] **T7.1** Update `src/app/mcp/server.py`:
  - [ ] Update `db_migrations_lifespan` to use async engine

## Phase 8: Testing

- [ ] **T8.1** Run `docker compose up -d postgres`
- [ ] **T8.2** Run tests: `docker compose --profile test run test_runner`
- [ ] **T8.3** Verify all endpoints work
- [ ] **T8.4** Verify MCP tools work

## Phase 9: Cleanup

- [ ] **T9.1** Remove SQLite-related code (if any remains)
- [ ] **T9.2** Update documentation
- [ ] **T9.3** Run linting: `ruff check src/`
- [ ] **T9.4** Run type checking: `mypy src/`

---

## Estimated Time

| Phase | Tasks | Est. Time |
|-------|-------|-----------|
| 1 | 1 | 5 min |
| 2 | 8 | 20 min |
| 3 | 2 | 10 min |
| 4 | 4 | 60 min |
| 5 | 6 | 30 min |
| 6 | 5 | 25 min |
| 7 | 1 | 10 min |
| 8 | 4 | 30 min |
| 9 | 3 | 15 min |

**Total: ~3.5 hours**
