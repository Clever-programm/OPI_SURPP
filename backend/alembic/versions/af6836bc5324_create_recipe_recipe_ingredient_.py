"""create recipe recipe-ingredient operation tables

Revision ID: af6836bc5324
Revises: f80aaeb1c0bf
Create Date: 2026-03-07 16:41:09.561382

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "af6836bc5324"
down_revision: Union[str, Sequence[str], None] = "f80aaeb1c0bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
