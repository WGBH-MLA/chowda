"""Adds MediaFile <--> SonyCiAsset Links

Revision ID: 9c426736beb0
Revises: 
Create Date: 2023-07-31 15:34:04.018312

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9c426736beb0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('clams_apps',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('endpoint', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('collections',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('media_files',
    sa.Column('mmif_json', sa.JSON(), nullable=True),
    sa.Column('guid', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('guid')
    )
    op.create_index(op.f('ix_media_files_guid'), 'media_files', ['guid'], unique=False)
    op.create_table('pipelines',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sonyci_assets',
    sa.Column('size', sa.BIGINT(), nullable=True),
    sa.Column('type', sa.Enum('video', 'audio', name='mediatype'), nullable=True),
    sa.Column('thumbnails', postgresql.ARRAY(sa.JSON()), nullable=True),
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('format', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sonyci_assets_format'), 'sonyci_assets', ['format'], unique=False)
    op.create_index(op.f('ix_sonyci_assets_id'), 'sonyci_assets', ['id'], unique=False)
    op.create_index(op.f('ix_sonyci_assets_name'), 'sonyci_assets', ['name'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('first_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('last_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_first_name'), 'users', ['first_name'], unique=False)
    op.create_index(op.f('ix_users_last_name'), 'users', ['last_name'], unique=False)
    op.create_table('batches',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('pipeline_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('clamsapppipelinelink',
    sa.Column('clams_app_id', sa.Integer(), nullable=False),
    sa.Column('pipeline_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['clams_app_id'], ['clams_apps.id'], ),
    sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ),
    sa.PrimaryKeyConstraint('clams_app_id', 'pipeline_id')
    )
    op.create_table('mediafilecollectionlink',
    sa.Column('media_file_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('collection_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ),
    sa.ForeignKeyConstraint(['media_file_id'], ['media_files.guid'], ),
    sa.PrimaryKeyConstraint('media_file_id', 'collection_id')
    )
    op.create_table('mediafilesonyciassetlink',
    sa.Column('media_file_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('sonyci_asset_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['media_file_id'], ['media_files.guid'], ),
    sa.ForeignKeyConstraint(['sonyci_asset_id'], ['sonyci_assets.id'], ),
    sa.PrimaryKeyConstraint('media_file_id', 'sonyci_asset_id')
    )
    op.create_table('clams_events',
    sa.Column('response_json', sa.JSON(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('batch_id', sa.Integer(), nullable=True),
    sa.Column('clams_app_id', sa.Integer(), nullable=True),
    sa.Column('media_file_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ),
    sa.ForeignKeyConstraint(['clams_app_id'], ['clams_apps.id'], ),
    sa.ForeignKeyConstraint(['media_file_id'], ['media_files.guid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('mediafilebatchlink',
    sa.Column('media_file_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('batch_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ),
    sa.ForeignKeyConstraint(['media_file_id'], ['media_files.guid'], ),
    sa.PrimaryKeyConstraint('media_file_id', 'batch_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('mediafilebatchlink')
    op.drop_table('clams_events')
    op.drop_table('mediafilesonyciassetlink')
    op.drop_table('mediafilecollectionlink')
    op.drop_table('clamsapppipelinelink')
    op.drop_table('batches')
    op.drop_index(op.f('ix_users_last_name'), table_name='users')
    op.drop_index(op.f('ix_users_first_name'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_sonyci_assets_name'), table_name='sonyci_assets')
    op.drop_index(op.f('ix_sonyci_assets_id'), table_name='sonyci_assets')
    op.drop_index(op.f('ix_sonyci_assets_format'), table_name='sonyci_assets')
    op.drop_table('sonyci_assets')
    op.drop_table('pipelines')
    op.drop_index(op.f('ix_media_files_guid'), table_name='media_files')
    op.drop_table('media_files')
    op.drop_table('collections')
    op.drop_table('clams_apps')
    # ### end Alembic commands ###