"""Добавлен столбец place_id в таблицу tickets

Revision ID: 7f5dc1e0120b
Revises: a8a257a4dc9a
Create Date: 2025-03-15 18:31:55.540841

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f5dc1e0120b'
down_revision: Union[str, None] = 'a8a257a4dc9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
