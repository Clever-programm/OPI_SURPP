"""create order order-item tables

Revision ID: 7562c482c2d3
Revises: af6836bc5324
Create Date: 2026-03-07 17:00:16.185612

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "7562c482c2d3"
down_revision: Union[str, Sequence[str], None] = "af6836bc5324"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
