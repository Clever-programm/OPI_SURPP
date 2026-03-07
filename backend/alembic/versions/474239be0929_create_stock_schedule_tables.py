"""create stock schedule tables

Revision ID: 474239be0929
Revises: 7562c482c2d3
Create Date: 2026-03-07 17:10:58.795470

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "474239be0929"
down_revision: Union[str, Sequence[str], None] = "7562c482c2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
