"""create ingredients equipment competence tables

Revision ID: f1ce219d8f59
Revises: 2e5df22cbd9b
Create Date: 2026-03-07 14:05:03.279284

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f1ce219d8f59"
down_revision: Union[str, Sequence[str], None] = "2e5df22cbd9b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
