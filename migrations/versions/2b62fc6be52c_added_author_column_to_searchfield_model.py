"""Added author column to SearchField model

Revision ID: 2b62fc6be52c
Revises: 5488b1d394df
Create Date: 2020-02-20 23:02:03.434688

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2b62fc6be52c'
down_revision = '5488b1d394df'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('nba-ws-search_field', sa.Column('author', sa.String(), nullable=True))
    op.create_unique_constraint(None, 'nba-ws-search_field', ['author'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'nba-ws-search_field', type_='unique')
    op.drop_column('nba-ws-search_field', 'author')
    # ### end Alembic commands ###