"""relabel sonyci status enums to values

Revision ID: 808cace84505
Revises: d0dbc16a01b4
Create Date: 2026-08-04 11:43:35.824372

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '808cace84505'
down_revision = 'd0dbc16a01b4'
branch_labels = None
depends_on = None


# (enum type name, member name, member value); only labels where name != value.
ENUM_RELABELS = [
    ('sonyciassetstatus', 'ExecutableDetected', 'Executable Detected'),
    ('sonyciassetstatus', 'VirusDetected', 'Virus Detected'),
    ('sonyciarchivestatus', 'NotArchived', 'Not archived'),
    ('sonyciarchivestatus', 'ArchiveInProgress', 'Archive in progress'),
    ('sonyciarchivestatus', 'RestoreInProgress', 'Restore in progress'),
    ('sonycirestorestatus', 'NotRestored', 'Not restored'),
    ('sonycirestorestatus', 'RestoreInProgress', 'Restore in progress'),
    ('sonycirestorestatus', 'RestoreFailed', 'Restore failed'),
]


def upgrade() -> None:
    for type_name, name, value in ENUM_RELABELS:
        op.execute(
            f"ALTER TYPE {type_name} RENAME VALUE '{name}' TO '{value}'"
        )


def downgrade() -> None:
    for type_name, name, value in ENUM_RELABELS:
        op.execute(
            f"ALTER TYPE {type_name} RENAME VALUE '{value}' TO '{name}'"
        )

