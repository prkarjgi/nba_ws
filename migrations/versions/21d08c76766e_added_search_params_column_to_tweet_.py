"""Added search_params column to Tweet model

Revision ID: 21d08c76766e
Revises: b97ca8a73993
Create Date: 2020-02-17 17:14:59.162198

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '21d08c76766e'
down_revision = 'b97ca8a73993'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('nba-news-tweet', sa.Column('search_params', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('nba-news-tweet', 'search_params')
    # ### end Alembic commands ###