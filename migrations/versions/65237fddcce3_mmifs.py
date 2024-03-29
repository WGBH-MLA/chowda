"""MMIFs

Revision ID: 65237fddcce3
Revises: 42a163f0faec
Create Date: 2023-10-13 14:58:07.011114

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '65237fddcce3'
down_revision = '42a163f0faec'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('mmifs',
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('mmif_json', sa.JSON(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('media_file_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('metaflow_run_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('batch_output_id', sa.Integer(), nullable=True),
    sa.Column('mmif_location', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.ForeignKeyConstraint(['batch_output_id'], ['batches.id'], ),
    sa.ForeignKeyConstraint(['media_file_id'], ['media_files.guid'], ),
    sa.ForeignKeyConstraint(['metaflow_run_id'], ['metaflow_runs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mmifs_id'), 'mmifs', ['id'], unique=False)
    op.create_index(op.f('ix_mmifs_media_file_id'), 'mmifs', ['media_file_id'], unique=False)
    op.create_table('mmifbatchinputlink',
    sa.Column('mmif_id', sa.Integer(), nullable=False),
    sa.Column('batch_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ),
    sa.ForeignKeyConstraint(['mmif_id'], ['mmifs.id'], ),
    sa.PrimaryKeyConstraint('mmif_id', 'batch_id')
    )
    op.create_index(op.f('ix_mmifbatchinputlink_batch_id'), 'mmifbatchinputlink', ['batch_id'], unique=False)
    op.create_index(op.f('ix_mmifbatchinputlink_mmif_id'), 'mmifbatchinputlink', ['mmif_id'], unique=False)
    op.drop_table('mediafilesonyciassetlink')
    op.create_index(op.f('ix_clamsapppipelinelink_clams_app_id'), 'clamsapppipelinelink', ['clams_app_id'], unique=False)
    op.create_index(op.f('ix_clamsapppipelinelink_pipeline_id'), 'clamsapppipelinelink', ['pipeline_id'], unique=False)
    op.create_index(op.f('ix_mediafilebatchlink_batch_id'), 'mediafilebatchlink', ['batch_id'], unique=False)
    op.create_index(op.f('ix_mediafilebatchlink_media_file_id'), 'mediafilebatchlink', ['media_file_id'], unique=False)
    op.create_index(op.f('ix_mediafilecollectionlink_collection_id'), 'mediafilecollectionlink', ['collection_id'], unique=False)
    op.create_index(op.f('ix_mediafilecollectionlink_media_file_id'), 'mediafilecollectionlink', ['media_file_id'], unique=False)
    op.alter_column('metaflow_runs', 'finished_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)
    op.create_index(op.f('ix_metaflow_runs_batch_id'), 'metaflow_runs', ['batch_id'], unique=False)
    op.create_index(op.f('ix_metaflow_runs_id'), 'metaflow_runs', ['id'], unique=False)
    op.create_index(op.f('ix_metaflow_runs_media_file_id'), 'metaflow_runs', ['media_file_id'], unique=False)
    op.create_index(op.f('ix_pipelines_id'), 'pipelines', ['id'], unique=False)
    op.add_column('sonyci_assets', sa.Column('media_file_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.create_index(op.f('ix_sonyci_assets_media_file_id'), 'sonyci_assets', ['media_file_id'], unique=False)
    op.create_foreign_key(None, 'sonyci_assets', 'media_files', ['media_file_id'], ['guid'])
    # ### end Alembic commands ###

    op.execute("ALTER TYPE mediatype RENAME VALUE 'video' TO 'Video';")
    op.execute("ALTER TYPE mediatype RENAME VALUE 'audio' TO 'Audio';")

def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # op.drop_constraint(None, 'sonyci_assets', type_='foreignkey')
    op.drop_index(op.f('ix_sonyci_assets_media_file_id'), table_name='sonyci_assets')
    op.drop_column('sonyci_assets', 'media_file_id')
    op.drop_index(op.f('ix_pipelines_id'), table_name='pipelines')
    op.drop_index(op.f('ix_metaflow_runs_media_file_id'), table_name='metaflow_runs')
    op.drop_index(op.f('ix_metaflow_runs_id'), table_name='metaflow_runs')
    op.drop_index(op.f('ix_metaflow_runs_batch_id'), table_name='metaflow_runs')
    op.alter_column('metaflow_runs', 'finished_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True)
    op.drop_index(op.f('ix_mediafilecollectionlink_media_file_id'), table_name='mediafilecollectionlink')
    op.drop_index(op.f('ix_mediafilecollectionlink_collection_id'), table_name='mediafilecollectionlink')
    op.drop_index(op.f('ix_mediafilebatchlink_media_file_id'), table_name='mediafilebatchlink')
    op.drop_index(op.f('ix_mediafilebatchlink_batch_id'), table_name='mediafilebatchlink')
    op.drop_index(op.f('ix_clamsapppipelinelink_pipeline_id'), table_name='clamsapppipelinelink')
    op.drop_index(op.f('ix_clamsapppipelinelink_clams_app_id'), table_name='clamsapppipelinelink')
    op.create_table('mediafilesonyciassetlink',
    sa.Column('media_file_id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('sonyci_asset_id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['media_file_id'], ['media_files.guid'], name='mediafilesonyciassetlink_media_file_id_fkey'),
    sa.ForeignKeyConstraint(['sonyci_asset_id'], ['sonyci_assets.id'], name='mediafilesonyciassetlink_sonyci_asset_id_fkey'),
    sa.PrimaryKeyConstraint('media_file_id', 'sonyci_asset_id', name='mediafilesonyciassetlink_pkey')
    )
    op.drop_index(op.f('ix_mmifbatchinputlink_mmif_id'), table_name='mmifbatchinputlink')
    op.drop_index(op.f('ix_mmifbatchinputlink_batch_id'), table_name='mmifbatchinputlink')
    op.drop_table('mmifbatchinputlink')
    op.drop_index(op.f('ix_mmifs_media_file_id'), table_name='mmifs')
    op.drop_index(op.f('ix_mmifs_id'), table_name='mmifs')
    op.drop_table('mmifs')
    # ### end Alembic commands ###

    op.execute("ALTER TYPE mediatype RENAME VALUE 'Video' TO 'video';")
    op.execute("ALTER TYPE mediatype RENAME VALUE 'Audio' TO 'audio';")