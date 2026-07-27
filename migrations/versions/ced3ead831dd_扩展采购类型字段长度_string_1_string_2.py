"""扩展采购类型字段长度 String(1)→String(2)

Revision ID: ced3ead831dd
Revises: 1d1bbdf210a6
Create Date: 2026-05-23 09:37:55.018025

"""
from alembic import op
import sqlalchemy as sa


revision = 'ced3ead831dd'
down_revision = '1d1bbdf210a6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tpc01_pcplan', schema=None) as batch_op:
        batch_op.alter_column('pctyp',
               existing_type=sa.VARCHAR(length=1),
               type_=sa.String(length=2),
               existing_comment='采购类型',
               existing_nullable=True)

    with op.batch_alter_table('tmm12_items', schema=None) as batch_op:
        batch_op.alter_column('purchasetyp',
               existing_type=sa.VARCHAR(length=1),
               type_=sa.String(length=2),
               existing_comment='采购类型',
               existing_nullable=True)


def downgrade():
    with op.batch_alter_table('tpc01_pcplan', schema=None) as batch_op:
        batch_op.alter_column('pctyp',
               existing_type=sa.String(length=2),
               type_=sa.VARCHAR(length=1),
               existing_comment='采购类型',
               existing_nullable=True)

    with op.batch_alter_table('tmm12_items', schema=None) as batch_op:
        batch_op.alter_column('purchasetyp',
               existing_type=sa.String(length=2),
               type_=sa.VARCHAR(length=1),
               existing_comment='采购类型',
               existing_nullable=True)
