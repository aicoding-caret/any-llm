"""Add metadata column to session_tokens for device info.

Revision ID: 3f2f5d9d9b77
Revises: c3d7e2f1c6f0
Create Date: 2025-11-23 10:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3f2f5d9d9b77"
down_revision: str | Sequence[str] | None = "c3d7e2f1c6f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("session_tokens", sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")))
    op.alter_column("session_tokens", "metadata", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("session_tokens", "metadata")
