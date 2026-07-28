"""add_ref_eid_to_tmm43_eid

Revision ID: 6740347934e6
Revises: 01baab307ccd
Create Date: 2026-06-01 18:22:57.198006

变更:
  - TMM43_EID 新增 ref_eid 列，用于翻新设备溯源链（旧EID→新EID）
"""
from alembic import op
import sqlalchemy as sa

revision = '6740347934e6'
down_revision = '01baab307ccd'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'tmm43_eid',
        sa.Column('ref_eid', sa.String(13), nullable=True, comment='来源EID（翻新溯源链）'),
    )


def downgrade():
    op.drop_column('tmm43_eid', 'ref_eid')
