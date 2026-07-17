"""Add is_public to queue_rules

Revision ID: 8a1c4f6e2d93
Revises: 540b96c318fb
Create Date: 2026-07-17 15:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a1c4f6e2d93'
down_revision: Union[str, Sequence[str], None] = '540b96c318fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE queue_rules ADD COLUMN IF NOT EXISTS is_public BOOLEAN NOT NULL DEFAULT TRUE")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE queue_rules DROP COLUMN IF EXISTS is_public")
