"""Change qdrant_point_id to qdrant_point_ids as UUID array

Revision ID: fix_qdrant_point_ids_array
Revises: e0bfb8ff04f0
Create Date: 2026-03-02 12:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fix_qdrant_point_ids_array"
down_revision: Union[str, Sequence[str], None] = "e0bfb8ff04f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add qdrant_point_ids column as UUID array if not exists."""
    # Check if qdrant_point_ids column exists
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'documents' AND column_name = 'qdrant_point_ids'
        """)
    )
    existing = result.fetchone()

    if not existing:
        # Add new column with ARRAY type
        op.add_column(
            "documents", sa.Column("qdrant_point_ids", sa.ARRAY(sa.String), nullable=True)
        )

        # Copy data from old column if it exists
        result = conn.execute(
            sa.text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'qdrant_point_id'
            """)
        )
        old_exists = result.fetchone()

        if old_exists:
            # Copy data from old column to new column
            conn.execute(
                sa.text("""
                UPDATE documents 
                SET qdrant_point_ids = CASE 
                    WHEN qdrant_point_id IS NOT NULL AND qdrant_point_id != '' 
                    THEN string_to_array(qdrant_point_id, ',')
                    ELSE NULL
                END
            """)
            )
            # Drop old column
            op.drop_column("documents", "qdrant_point_id")
    else:
        # Column already exists (already migrated), check if old column needs to be dropped
        result = conn.execute(
            sa.text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'qdrant_point_id'
            """)
        )
        old_exists = result.fetchone()
        if old_exists:
            # Copy data and drop old column
            conn.execute(
                sa.text("""
                UPDATE documents 
                SET qdrant_point_ids = CASE 
                    WHEN qdrant_point_id IS NOT NULL AND qdrant_point_id != '' 
                    THEN string_to_array(qdrant_point_id, ',')
                    ELSE NULL
                END
                WHERE qdrant_point_ids IS NULL AND qdrant_point_id IS NOT NULL AND qdrant_point_id != ''
            """)
            )
            op.drop_column("documents", "qdrant_point_id")


def downgrade() -> None:
    """Revert: change qdrant_point_ids back to qdrant_point_id as VARCHAR."""
    # Add old column back as VARCHAR
    op.add_column("documents", sa.Column("qdrant_point_id", sa.String(length=36), nullable=True))

    # Copy data back (array to comma-separated string)
    conn = op.get_bind()
    conn.execute(
        sa.text("""
        UPDATE documents 
        SET qdrant_point_id = CASE 
            WHEN qdrant_point_ids IS NOT NULL 
            THEN array_to_string(qdrant_point_ids, ',')
            ELSE NULL
        END
    """)
    )

    # Drop new column
    op.drop_column("documents", "qdrant_point_ids")
