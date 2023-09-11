"""MetaflowRun

Revision ID: fd7b62eab884
Revises: 3ae9e767f652
Create Date: 2023-09-06 12:51:23.899408

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'fd7b62eab884'
down_revision = '3ae9e767f652'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('metaflow_runs', sa.Column('finished', sa.Boolean(), nullable=False))
    op.add_column('metaflow_runs', sa.Column('finished_at', sa.DateTime(), nullable=True))
    op.add_column('metaflow_runs', sa.Column('duration', sa.Integer(), nullable=True))
    op.add_column('metaflow_runs', sa.Column('successful', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('metaflow_runs', 'successful')
    op.drop_column('metaflow_runs', 'duration')
    op.drop_column('metaflow_runs', 'finished_at')
    op.drop_column('metaflow_runs', 'finished')
    # ### end Alembic commands ###
