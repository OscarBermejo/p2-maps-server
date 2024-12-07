"""add_city_column_to_restaurants

Revision ID: 4559b6eacc3e
Revises: 
Create Date: 2024-12-06 15:26:38.287533

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4559b6eacc3e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('restaurants', 
        sa.Column('city', sa.String(255), nullable=False, server_default='')
    )


def downgrade() -> None:
    op.drop_column('restaurants', 'city')
