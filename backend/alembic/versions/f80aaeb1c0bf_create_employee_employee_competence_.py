"""create employee employee-competence tables

Revision ID: f80aaeb1c0bf
Revises: f1ce219d8f59
Create Date: 2026-03-07 16:13:46.185488

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f80aaeb1c0bf"
down_revision: Union[str, Sequence[str], None] = "f1ce219d8f59"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
