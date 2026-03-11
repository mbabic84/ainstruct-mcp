"""Remove is_active from cats and pat_tokens tables

Revision ID: remove_token_is_active
Revises: add_usage_records
Create Date: 2026-03-11 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "remove_token_is_active"
down_revision: Union[str, Sequence[str], None] = "add_usage_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop is_active columns from cats and pat_tokens tables."""
    op.drop_column("cats", "is_active")
    op.drop_column("pat_tokens", "is_active")


def downgrade() -> None:
    """Add is_active columns back to cats and pat_tokens tables."""
    op.add_column("cats", sa.Column("is_active", sa.Boolean(), default=True, nullable=True))
    op.add_column("pat_tokens", sa.Column("is_active", sa.Boolean(), default=True, nullable=True))
