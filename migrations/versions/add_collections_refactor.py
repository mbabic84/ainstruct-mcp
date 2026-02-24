"""add_collections_table_and_refactor_permissions

Revision ID: add_collections_refactor
Revises: 339e4a4a595a
Create Date: 2026-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = 'add_collections_refactor'
down_revision: Union[str, Sequence[str], None] = '339e4a4a595a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'collections' not in existing_tables:
        op.create_table('collections',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('qdrant_collection', sa.String(length=100), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('collections', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_collections_user_id'), ['user_id'], unique=False)
    
    api_keys_columns = [c['name'] for c in inspector.get_columns('api_keys')] if 'api_keys' in existing_tables else []
    if 'collection_id' not in api_keys_columns:
        op.add_column('api_keys', sa.Column('collection_id', sa.String(length=36), nullable=True))
    if 'permission' not in api_keys_columns:
        op.add_column('api_keys', sa.Column('permission', sa.String(length=20), nullable=True))
    
    if 'collection_id' not in api_keys_columns:
        with op.batch_alter_table('api_keys', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_api_keys_collection_id'), ['collection_id'], unique=False)
    
    has_scopes_column = 'scopes' in api_keys_columns
    has_qdrant_collection_column = 'qdrant_collection' in api_keys_columns
    
    users = conn.execute(text("SELECT id FROM users")).fetchall()
    collection_mapping = {}
    for user in users:
        user_id = user[0]
        
        if has_scopes_column and has_qdrant_collection_column:
            existing_keys = conn.execute(
                text("SELECT id, qdrant_collection, scopes FROM api_keys WHERE user_id = :user_id"),
                {"user_id": user_id}
            ).fetchall()
        elif has_qdrant_collection_column:
            existing_keys = conn.execute(
                text("SELECT id, qdrant_collection FROM api_keys WHERE user_id = :user_id"),
                {"user_id": user_id}
            ).fetchall()
        else:
            existing_keys = conn.execute(
                text("SELECT id FROM api_keys WHERE user_id = :user_id"),
                {"user_id": user_id}
            ).fetchall()
        
        if existing_keys:
            if has_qdrant_collection_column:
                qdrant_collection = existing_keys[0][1]
            else:
                qdrant_collection = f"default_{user_id}"
            collection_name = "default"
            
            result = conn.execute(
                text("""
                    INSERT INTO collections (id, name, qdrant_collection, user_id, created_at, updated_at)
                    VALUES (lower(hex(randomblob(16))), :name, :qdrant, :user_id, datetime('now'), datetime('now'))
                    RETURNING id
                """),
                {"name": collection_name, "qdrant": qdrant_collection, "user_id": user_id}
            )
            collection_id = result.fetchone()[0]
            collection_mapping[user_id] = collection_id
            
            for key in existing_keys:
                key_id = key[0]
                if has_scopes_column:
                    scopes = key[2] or "read,write"
                    permission = "read_write" if "write" in scopes else "read"
                else:
                    permission = "read_write"
                
                conn.execute(
                    text("UPDATE api_keys SET collection_id = :cid, permission = :perm WHERE id = :kid"),
                    {"cid": collection_id, "perm": permission, "kid": key_id}
                )
    
    documents_columns = [c['name'] for c in inspector.get_columns('documents')] if 'documents' in existing_tables else []
    documents_indexes = [idx['name'] for idx in inspector.get_indexes('documents')] if 'documents' in existing_tables else []
    if 'collection_id' not in documents_columns:
        op.add_column('documents', sa.Column('collection_id', sa.String(length=36), nullable=True))
        
        with op.batch_alter_table('documents', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_documents_collection_id'), ['collection_id'], unique=False)
        
        for user_id, collection_id in collection_mapping.items():
            conn.execute(
                text("""
                    UPDATE documents SET collection_id = :cid
                    WHERE api_key_id IN (SELECT id FROM api_keys WHERE user_id = :uid)
                """),
                {"cid": collection_id, "uid": user_id}
            )
    
    if 'api_key_id' in documents_columns:
        with op.batch_alter_table('documents', schema=None) as batch_op:
            if 'ix_documents_api_key_id' in documents_indexes:
                batch_op.drop_index('ix_documents_api_key_id')
            batch_op.drop_column('api_key_id')
    
    with op.batch_alter_table('collections', schema=None) as batch_op:
        batch_op.alter_column('user_id', existing_nullable=False, nullable=False)
    
    with op.batch_alter_table('api_keys', schema=None) as batch_op:
        batch_op.alter_column('collection_id', existing_nullable=True, nullable=False)
        batch_op.alter_column('permission', existing_nullable=True, nullable=False)
        if 'qdrant_collection' in api_keys_columns:
            batch_op.drop_column('qdrant_collection')
        if 'scopes' in api_keys_columns:
            batch_op.drop_column('scopes')
    
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_documents_collection', 'collections', ['collection_id'], ['id'])
    
    with op.batch_alter_table('api_keys', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_api_keys_collection', 'collections', ['collection_id'], ['id'])


def downgrade() -> None:
    conn = op.get_bind()
    
    with op.batch_alter_table('api_keys', schema=None) as batch_op:
        batch_op.add_column(sa.Column('qdrant_collection', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('scopes', sa.String(length=255), nullable=True))
        batch_op.drop_constraint('fk_api_keys_collection', type_='foreignkey')
    
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('api_key_id', sa.String(length=36), nullable=True))
        batch_op.drop_constraint('fk_documents_collection', type_='foreignkey')
    
    collections = conn.execute(text("SELECT id, qdrant_collection, user_id FROM collections")).fetchall()
    for coll in collections:
        coll_id, qdrant_coll, user_id = coll
        conn.execute(
            text("UPDATE api_keys SET qdrant_collection = :qc WHERE collection_id = :cid"),
            {"qc": qdrant_coll, "cid": coll_id}
        )
        conn.execute(
            text("UPDATE api_keys SET scopes = 'read,write' WHERE collection_id = :cid AND permission = 'read_write'"),
            {"cid": coll_id}
        )
        conn.execute(
            text("UPDATE api_keys SET scopes = 'read' WHERE collection_id = :cid AND permission = 'read'"),
            {"cid": coll_id}
        )
    
    api_keys = conn.execute(text("SELECT id, collection_id FROM api_keys")).fetchall()
    for key in api_keys:
        key_id, coll_id = key
        conn.execute(
            text("UPDATE documents SET api_key_id = :kid WHERE collection_id = :cid"),
            {"kid": key_id, "cid": coll_id}
        )
    
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_documents_api_key_id'), ['api_key_id'], unique=False)
        batch_op.drop_index(batch_op.f('ix_documents_collection_id'))
        batch_op.drop_column('collection_id')
    
    with op.batch_alter_table('api_keys', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_api_keys_collection_id'))
        batch_op.drop_column('collection_id')
        batch_op.drop_column('permission')
    
    with op.batch_alter_table('collections', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_collections_user_id'))
    
    op.drop_table('collections')
