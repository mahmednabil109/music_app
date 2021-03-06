"""empty message

Revision ID: bd943ad1b225
Revises: 64efe8baec06
Create Date: 2020-11-23 12:30:18.784691

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bd943ad1b225'
down_revision = '64efe8baec06'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Artist', 'address')
    op.add_column('Venue', sa.Column('geners', sa.String(length=120), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Venue', 'geners')
    op.add_column('Artist', sa.Column('address', sa.VARCHAR(length=120), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
