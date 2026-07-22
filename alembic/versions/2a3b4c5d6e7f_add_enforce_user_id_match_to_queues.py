"""Add enforce_user_id_match to queues

Revision ID: 2a3b4c5d6e7f
Revises: 7b3d5e9f2a18
Create Date: 2026-07-22 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a3b4c5d6e7f'
down_revision: Union[str, Sequence[str], None] = '7b3d5e9f2a18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'queues',
        sa.Column(
            'enforce_user_id_match',
            sa.Boolean(),
            nullable=False,
            server_default='true'
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('queues', 'enforce_user_id_match')
