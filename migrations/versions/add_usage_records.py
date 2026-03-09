"""Add usage_records table

Revision ID: add_usage_records
Revises: fix_qdrant_point_ids_array
Create Date: 2026-03-09 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_usage_records"
down_revision: Union[str, Sequence[str], None] = "fix_qdrant_point_ids_array"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create usage_records table."""
    op.create_table(
        "usage_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("year_month", sa.String(length=7), nullable=False),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.UniqueConstraint("user_id", "year_month", "source", name="uq_user_month_source"),
    )

    op.create_index("ix_usage_records_user_id", "usage_records", ["user_id"])


def downgrade() -> None:
    """Drop usage_records table."""
    op.drop_index("ix_usage_records_user_id", "usage_records")
    op.drop_table("usage_records")
