"""Add provider_token and access_token_plain to session_tokens."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f0f1e2d3c4b5"
down_revision: str | Sequence[str] | None = "d4e6f7a8b9c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("session_tokens", sa.Column("provider_token", sa.String(), nullable=True))
    op.add_column("session_tokens", sa.Column("access_token_plain", sa.String(), nullable=True))
    op.create_index(op.f("ix_session_tokens_provider_token"), "session_tokens", ["provider_token"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_session_tokens_provider_token"), table_name="session_tokens")
    op.drop_column("session_tokens", "access_token_plain")
    op.drop_column("session_tokens", "provider_token")
