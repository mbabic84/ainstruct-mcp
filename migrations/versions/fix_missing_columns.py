"""add_expires_at_to_api_keys_and_pat_tokens

Revision ID: fix_missing_columns
Revises: add_collections_refactor
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'fix_missing_columns'
down_revision: Union[str, Sequence[str], None] = 'add_collections_refactor'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'api_keys' in existing_tables:
        api_keys_columns = [c['name'] for c in inspector.get_columns('api_keys')]
        if 'expires_at' not in api_keys_columns:
            op.add_column('api_keys', sa.Column('expires_at', sa.DateTime(), nullable=True))
    
    if 'pat_tokens' not in existing_tables:
        op.create_table('pat_tokens',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('token_hash', sa.String(length=64), nullable=False),
            sa.Column('label', sa.String(length=100), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=False),
            sa.Column('scopes', sa.String(length=100), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('last_used', sa.DateTime(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('pat_tokens', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_pat_tokens_token_hash'), ['token_hash'], unique=True)
            batch_op.create_index(batch_op.f('ix_pat_tokens_user_id'), ['user_id'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'pat_tokens' in inspector.get_table_names():
        op.drop_table('pat_tokens')
    
    if 'api_keys' in inspector.get_table_names():
        api_keys_columns = [c['name'] for c in inspector.get_columns('api_keys')]
        if 'expires_at' in api_keys_columns:
            with op.batch_alter_table('api_keys', schema=None) as batch_op:
                batch_op.drop_column('expires_at')
