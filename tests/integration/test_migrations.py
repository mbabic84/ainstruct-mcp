"""
Integration tests for Alembic migrations.
Tests migration upgrade/downgrade paths and handles legacy schema scenarios.
"""
import os
import sys
import importlib
import pytest
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text, inspect


def get_alembic_config(db_path: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", "migrations")
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


@pytest.fixture(autouse=True)
def setup_python_path():
    app_dir = Path(__file__).parent.parent
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Create a temp database path and set env var for settings."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    
    if "src.app.config" in sys.modules:
        import src.app.config as config_module
        importlib.reload(config_module)
    
    yield str(db_path)


class TestMigrationsFreshDatabase:
    """Test migrations against a fresh database."""

    def test_upgrade_from_empty_database(self, temp_db):
        """Migrations should run successfully on an empty database."""
        cfg = get_alembic_config(temp_db)
        
        command.upgrade(cfg, "head")
        
        engine = create_engine(f"sqlite:///{temp_db}")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        assert "users" in tables
        assert "api_keys" in tables
        assert "collections" in tables
        assert "documents" in tables

    def test_upgrade_creates_correct_schema(self, temp_db):
        """Verify schema after migration matches expected structure."""
        cfg = get_alembic_config(temp_db)
        
        command.upgrade(cfg, "head")
        
        engine = create_engine(f"sqlite:///{temp_db}")
        inspector = inspect(engine)
        
        api_keys_columns = {c["name"] for c in inspector.get_columns("api_keys")}
        assert "collection_id" in api_keys_columns
        assert "permission" in api_keys_columns
        assert "qdrant_collection" not in api_keys_columns
        assert "scopes" not in api_keys_columns
        
        documents_columns = {c["name"] for c in inspector.get_columns("documents")}
        assert "collection_id" in documents_columns
        assert "api_key_id" not in documents_columns

    def test_downgrade_to_base(self, temp_db):
        """Downgrade should revert to base state."""
        cfg = get_alembic_config(temp_db)
        
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "base")
        
        engine = create_engine(f"sqlite:///{temp_db}")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        assert "users" not in tables
        assert "api_keys" not in tables
        assert "collections" not in tables
        assert "documents" not in tables


class TestMigrationsLegacySchema:
    """Test migrations handle legacy schema scenarios correctly."""

    def test_upgrade_with_existing_data_no_scopes_column(self, temp_db):
        """
        Test migration with pre-existing api_keys table that lacks 'scopes' column.
        This simulates the original bug: 'no such column: scopes'.
        """
        engine = create_engine(f"sqlite:///{temp_db}")
        
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    is_superuser INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """))
            conn.execute(text("""
                CREATE TABLE api_keys (
                    id TEXT PRIMARY KEY,
                    key_hash TEXT NOT NULL UNIQUE,
                    label TEXT NOT NULL,
                    qdrant_collection TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used TEXT,
                    is_active INTEGER DEFAULT 1,
                    user_id TEXT,
                    expires_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE documents (
                    id TEXT PRIMARY KEY,
                    api_key_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    doc_metadata TEXT NOT NULL,
                    qdrant_point_id TEXT
                )
            """))
            conn.execute(text("CREATE INDEX ix_documents_api_key_id ON documents (api_key_id)"))
            conn.execute(text("""
                INSERT INTO users (id, email, username, password_hash, is_active, is_superuser, created_at, updated_at)
                VALUES ('user-1', 'test@example.com', 'testuser', 'hash', 1, 0, datetime('now'), datetime('now'))
            """))
            conn.execute(text("""
                INSERT INTO api_keys (id, key_hash, label, qdrant_collection, created_at, is_active, user_id)
                VALUES ('key-1', 'hash123', 'Test Key', 'qdrant-uuid-1', datetime('now'), 1, 'user-1')
            """))
        
        cfg = get_alembic_config(temp_db)
        command.stamp(cfg, "339e4a4a595a")
        command.upgrade(cfg, "head")
        
        engine = create_engine(f"sqlite:///{temp_db}")
        inspector = inspect(engine)
        
        api_keys_columns = {c["name"] for c in inspector.get_columns("api_keys")}
        assert "collection_id" in api_keys_columns
        assert "permission" in api_keys_columns
        
        tables = inspector.get_table_names()
        assert "collections" in tables

    def test_upgrade_with_existing_data_with_scopes_column(self, temp_db):
        """
        Test migration with api_keys that has 'scopes' and 'qdrant_collection' columns.
        Should migrate data correctly.
        """
        engine = create_engine(f"sqlite:///{temp_db}")
        
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    is_superuser INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """))
            conn.execute(text("""
                CREATE TABLE api_keys (
                    id TEXT PRIMARY KEY,
                    key_hash TEXT NOT NULL UNIQUE,
                    label TEXT NOT NULL,
                    qdrant_collection TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used TEXT,
                    is_active INTEGER DEFAULT 1,
                    user_id TEXT,
                    scopes TEXT NOT NULL DEFAULT 'read,write',
                    expires_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE documents (
                    id TEXT PRIMARY KEY,
                    api_key_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    doc_metadata TEXT NOT NULL,
                    qdrant_point_id TEXT
                )
            """))
            conn.execute(text("CREATE INDEX ix_documents_api_key_id ON documents (api_key_id)"))
            conn.execute(text("""
                INSERT INTO users (id, email, username, password_hash, is_active, is_superuser, created_at, updated_at)
                VALUES ('user-1', 'test@example.com', 'testuser', 'hash', 1, 0, datetime('now'), datetime('now'))
            """))
            conn.execute(text("""
                INSERT INTO api_keys (id, key_hash, label, qdrant_collection, created_at, is_active, user_id, scopes)
                VALUES ('key-1', 'hash123', 'Test Key', 'qdrant-uuid-1', datetime('now'), 1, 'user-1', 'read,write')
            """))
        
        cfg = get_alembic_config(temp_db)
        command.stamp(cfg, "339e4a4a595a")
        command.upgrade(cfg, "head")
        
        engine = create_engine(f"sqlite:///{temp_db}")
        
        with engine.begin() as conn:
            result = conn.execute(text("SELECT collection_id, permission FROM api_keys WHERE id = 'key-1'"))
            row = result.fetchone()
            assert row is not None
            assert row[0] is not None
            assert row[1] in ("read", "read_write")

    def test_upgrade_with_read_only_scopes(self, temp_db):
        """Test that read-only scopes are correctly migrated to 'read' permission."""
        engine = create_engine(f"sqlite:///{temp_db}")
        
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    is_superuser INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """))
            conn.execute(text("""
                CREATE TABLE api_keys (
                    id TEXT PRIMARY KEY,
                    key_hash TEXT NOT NULL UNIQUE,
                    label TEXT NOT NULL,
                    qdrant_collection TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used TEXT,
                    is_active INTEGER DEFAULT 1,
                    user_id TEXT,
                    scopes TEXT NOT NULL DEFAULT 'read,write',
                    expires_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE documents (
                    id TEXT PRIMARY KEY,
                    api_key_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    doc_metadata TEXT NOT NULL,
                    qdrant_point_id TEXT
                )
            """))
            conn.execute(text("CREATE INDEX ix_documents_api_key_id ON documents (api_key_id)"))
            conn.execute(text("""
                INSERT INTO users (id, email, username, password_hash, is_active, is_superuser, created_at, updated_at)
                VALUES ('user-1', 'test@example.com', 'testuser', 'hash', 1, 0, datetime('now'), datetime('now'))
            """))
            conn.execute(text("""
                INSERT INTO api_keys (id, key_hash, label, qdrant_collection, created_at, is_active, user_id, scopes)
                VALUES ('key-1', 'hash123', 'Test Key', 'qdrant-uuid-1', datetime('now'), 1, 'user-1', 'read')
            """))
        
        cfg = get_alembic_config(temp_db)
        command.stamp(cfg, "339e4a4a595a")
        command.upgrade(cfg, "head")
        
        engine = create_engine(f"sqlite:///{temp_db}")
        
        with engine.begin() as conn:
            result = conn.execute(text("SELECT permission FROM api_keys WHERE id = 'key-1'"))
            row = result.fetchone()
            assert row is not None
            assert row[0] == "read"


class TestMigrationIdempotency:
    """Test that migrations are safe to run multiple times."""

    def test_upgrade_head_twice(self, temp_db):
        """Running upgrade to head twice should not cause errors."""
        cfg = get_alembic_config(temp_db)
        
        command.upgrade(cfg, "head")
        command.upgrade(cfg, "head")
        
        engine = create_engine(f"sqlite:///{temp_db}")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        assert "users" in tables
        assert "api_keys" in tables
        assert "collections" in tables


class TestMigrationDowngrade:
    """Test migration downgrade restores previous state."""

    def test_downgrade_restores_legacy_schema(self, temp_db):
        """Downgrading should restore scopes and qdrant_collection columns."""
        cfg = get_alembic_config(temp_db)
        
        command.upgrade(cfg, "head")
        
        engine = create_engine(f"sqlite:///{temp_db}")
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO users (id, email, username, password_hash, is_active, is_superuser, created_at, updated_at)
                VALUES ('user-1', 'test@example.com', 'testuser', 'hash', 1, 0, datetime('now'), datetime('now'))
            """))
            conn.execute(text("""
                INSERT INTO collections (id, name, qdrant_collection, user_id, created_at, updated_at)
                VALUES ('coll-1', 'default', 'qdrant-uuid-1', 'user-1', datetime('now'), datetime('now'))
            """))
            conn.execute(text("""
                INSERT INTO api_keys (id, key_hash, label, collection_id, permission, created_at, is_active, user_id)
                VALUES ('key-1', 'hash123', 'Test Key', 'coll-1', 'read_write', datetime('now'), 1, 'user-1')
            """))
        
        command.downgrade(cfg, "339e4a4a595a")
        
        inspector = inspect(engine)
        api_keys_columns = {c["name"] for c in inspector.get_columns("api_keys")}
        
        assert "qdrant_collection" in api_keys_columns
        assert "scopes" in api_keys_columns
        assert "collection_id" not in api_keys_columns
        assert "permission" not in api_keys_columns


class TestMigrationForeignKeys:
    """Test that foreign key constraints are properly created."""

    def test_foreign_keys_after_migration(self, temp_db):
        """Verify foreign keys exist after migration."""
        cfg = get_alembic_config(temp_db)
        
        command.upgrade(cfg, "head")
        
        engine = create_engine(f"sqlite:///{temp_db}")
        inspector = inspect(engine)
        
        doc_fks = inspector.get_foreign_keys("documents")
        doc_fk_cols = {fk["constrained_columns"][0] for fk in doc_fks}
        assert "collection_id" in doc_fk_cols
        
        api_key_fks = inspector.get_foreign_keys("api_keys")
        api_key_fk_cols = {fk["constrained_columns"][0] for fk in api_key_fks}
        assert "collection_id" in api_key_fk_cols


class TestMigrationLegacySchemaNoUserId:
    """Test migration handles api_keys without user_id column (pre-users schema)."""

    def test_upgrade_api_keys_without_user_id_column(self, temp_db):
        """
        Test migration with api_keys table that lacks user_id column.
        This simulates a legacy database where api_keys existed before users table
        was linked to it. This is the bug scenario: 'no such column: user_id'.
        """
        engine = create_engine(f"sqlite:///{temp_db}")
        
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    is_superuser INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """))
            conn.execute(text("""
                CREATE TABLE api_keys (
                    id TEXT PRIMARY KEY,
                    key_hash TEXT NOT NULL UNIQUE,
                    label TEXT NOT NULL,
                    qdrant_collection TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used TEXT,
                    is_active INTEGER DEFAULT 1,
                    user_id TEXT,
                    expires_at TEXT
                )
            """))
            conn.execute(text("""
                CREATE TABLE documents (
                    id TEXT PRIMARY KEY,
                    api_key_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    doc_metadata TEXT NOT NULL,
                    qdrant_point_id TEXT
                )
            """))
            conn.execute(text("CREATE INDEX ix_documents_api_key_id ON documents (api_key_id)"))
            conn.execute(text("""
                INSERT INTO users (id, email, username, password_hash, is_active, is_superuser, created_at, updated_at)
                VALUES ('user-1', 'test@example.com', 'testuser', 'hash', 1, 0, datetime('now'), datetime('now'))
            """))
            conn.execute(text("""
                INSERT INTO api_keys (id, key_hash, label, qdrant_collection, created_at, is_active, user_id)
                VALUES ('key-1', 'hash123', 'Test Key', 'qdrant-uuid-1', datetime('now'), 1, 'user-1')
            """))
        
        cfg = get_alembic_config(temp_db)
        command.stamp(cfg, "339e4a4a595a")
        command.upgrade(cfg, "head")
        
        engine = create_engine(f"sqlite:///{temp_db}")
        inspector = inspect(engine)
        
        api_keys_columns = {c["name"] for c in inspector.get_columns("api_keys")}
        assert "collection_id" in api_keys_columns
        assert "permission" in api_keys_columns
        
        tables = inspector.get_table_names()
        assert "collections" in tables


class TestFixMissingColumnsMigration:
    """Test fix_missing_columns migration handles missing columns correctly."""

    def test_add_expires_at_to_api_keys(self, temp_db):
        """Test migration adds expires_at column to api_keys if missing."""
        engine = create_engine(f"sqlite:///{temp_db}")
        
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    is_superuser INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """))
            conn.execute(text("""
                CREATE TABLE api_keys (
                    id TEXT PRIMARY KEY,
                    key_hash TEXT NOT NULL UNIQUE,
                    label TEXT NOT NULL,
                    collection_id TEXT NOT NULL,
                    permission TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used TEXT,
                    is_active INTEGER DEFAULT 1,
                    user_id TEXT
                )
            """))
            conn.execute(text("""
                CREATE TABLE collections (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    qdrant_collection TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """))
            conn.execute(text("""
                CREATE TABLE documents (
                    id TEXT PRIMARY KEY,
                    collection_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    doc_metadata TEXT NOT NULL,
                    qdrant_point_id TEXT
                )
            """))
        
        cfg = get_alembic_config(temp_db)
        command.stamp(cfg, "add_collections_refactor")
        command.upgrade(cfg, "head")
        
        inspector = inspect(engine)
        api_keys_columns = {c['name'] for c in inspector.get_columns("api_keys")}
        assert "expires_at" in api_keys_columns

    def test_add_pat_tokens_table(self, temp_db):
        """Test migration creates pat_tokens table if missing."""
        cfg = get_alembic_config(temp_db)
        
        command.upgrade(cfg, "add_collections_refactor")
        
        engine = create_engine(f"sqlite:///{temp_db}")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "pat_tokens" not in tables
        
        command.upgrade(cfg, "head")
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "pat_tokens" in tables
        
        pat_tokens_columns = {c['name'] for c in inspector.get_columns("pat_tokens")}
        assert "id" in pat_tokens_columns
        assert "token_hash" in pat_tokens_columns
        assert "label" in pat_tokens_columns
        assert "user_id" in pat_tokens_columns
        assert "scopes" in pat_tokens_columns
        assert "expires_at" in pat_tokens_columns
        assert "is_active" in pat_tokens_columns

    def test_migration_idempotent(self, temp_db):
        """Running migration twice should not cause errors."""
        cfg = get_alembic_config(temp_db)
        
        command.upgrade(cfg, "head")
        command.upgrade(cfg, "head")
        
        engine = create_engine(f"sqlite:///{temp_db}")
        inspector = inspect(engine)
        api_keys_columns = {c['name'] for c in inspector.get_columns("api_keys")}
        assert "expires_at" in api_keys_columns
        
        tables = inspector.get_table_names()
        assert "pat_tokens" in tables
