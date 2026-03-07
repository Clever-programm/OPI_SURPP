"""create ingredients equipment competence tables

Revision ID: 2e5df22cbd9b
Revises: fe29b0566cb0
Create Date: 2026-03-07 13:57:08.561817

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "2e5df22cbd9b"
down_revision: Union[str, Sequence[str], None] = "fe29b0566cb0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
