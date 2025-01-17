"""initial

Revision ID: 9cf7cad9918f
Revises:
Create Date: 2025-01-14 18:31:39.932297

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9cf7cad9918f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'accounts',
        sa.Column('id', sa.Integer, nullable=False, primary_key=True),
        sa.Column('acc_addr', sa.String, nullable=False),
        sa.Column('bandwidth', sa.String),
        sa.Column('trx_balance', sa.String),
        sa.Column('energy', sa.String),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table('accounts')
