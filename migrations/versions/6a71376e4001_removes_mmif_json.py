"""Removes mmif_json

Revision ID: 6a71376e4001
Revises: 65237fddcce3
Create Date: 2023-10-16 15:26:35.973058

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6a71376e4001'
down_revision = '65237fddcce3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('media_files', 'mmif_json')
    op.add_column('mediafilebatchlink', sa.Column('source_mmif_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_mediafilebatchlink_source_mmif_id'), 'mediafilebatchlink', ['source_mmif_id'], unique=False)
    op.create_foreign_key(None, 'mediafilebatchlink', 'mmifs', ['source_mmif_id'], ['id'])
    op.drop_column('mmifs', 'mmif_json')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('mmifs', sa.Column('mmif_json', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'mediafilebatchlink', type_='foreignkey')
    op.drop_index(op.f('ix_mediafilebatchlink_source_mmif_id'), table_name='mediafilebatchlink')
    op.drop_column('mediafilebatchlink', 'source_mmif_id')
    op.add_column('media_files', sa.Column('mmif_json', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
