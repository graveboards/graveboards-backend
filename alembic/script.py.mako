"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, Sequence[str], None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """Upgrade schema.

    Base.metadata.create_all runs before migrations on every app startup (see
    app/lifespan.py) and will have already created any table/column that's
    also declared on a current SQLAlchemy model - including ones this
    migration is meant to introduce. Write every CREATE/ADD here as
    IF NOT EXISTS (and every DROP as IF EXISTS) so this migration is a no-op
    in that case instead of failing with "already exists".
    """
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Downgrade schema."""
    ${downgrades if downgrades else "pass"}
