"""rename_api_keys_to_cats

Revision ID: 001_rename_api_keys_to_cats
Revises: 339e4a4a595a
Create Date: 2026-02-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = '001_rename_api_keys_to_cats'
down_revision: Union[str, Sequence[str], None] = 'fix_missing_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table('api_keys', 'cats')


def downgrade() -> None:
    op.rename_table('cats', 'api_keys')
