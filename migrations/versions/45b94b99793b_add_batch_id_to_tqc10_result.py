"""add batch_id to tqc10_result

Revision ID: 45b94b99793b
Revises: 0f1a2b3c4d5e
Create Date: 2026-06-10 16:36:00.533990

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '45b94b99793b'
down_revision = '0f1a2b3c4d5e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tqc10_result', sa.Column('batch_id', sa.String(12), nullable=True, comment='批次号'))
    op.create_index('idx_qc_batch_id', 'tqc10_result', ['batch_id'])


def downgrade():
    op.drop_index('idx_qc_batch_id', 'tqc10_result')
    op.drop_column('tqc10_result', 'batch_id')
